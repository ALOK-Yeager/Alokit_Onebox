"""FastAPI integration example for hybrid search.

This module demonstrates how to expose the hybrid search functionality
via a REST API endpoint.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
import logging

from src.Services.search.VectorDB import VectorDB
from src.Services.search.hybrid_search import hybrid_search, HybridSearchConfig

# Initialize FastAPI app
app = FastAPI(title="Email Hybrid Search API", version="1.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize VectorDB (singleton pattern)
vector_db = VectorDB(persist_directory="./vector_store")


# ==================== Request/Response Models ==================== #

class SearchRequest(BaseModel):
    """Request model for hybrid search."""
    query: str = Field(..., description="Search query string", min_length=1)
    account_id: Optional[str] = Field(None, description="Filter by account ID")
    folder: Optional[str] = Field(None, description="Filter by folder name")
    category: Optional[str] = Field(None, description="Filter by AI category")
    max_results: int = Field(20, ge=1, le=100, description="Maximum results to return")
    semantic_weight: float = Field(0.7, ge=0.0, le=1.0, description="Weight for semantic similarity")
    keyword_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for keyword matching")
    method: Literal['weighted', 'rrf'] = Field('weighted', description="Ranking method")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum score threshold")


class SearchResult(BaseModel):
    """Response model for a single search result."""
    id: str
    hybrid_score: float
    es_norm_score: float
    vector_norm_score: float
    subject: Optional[str] = None
    from_address: Optional[str] = Field(None, alias="from")
    to: Optional[List[str]] = None
    date: Optional[str] = None
    body: Optional[str] = None
    ai_category: Optional[str] = Field(None, alias="aiCategory")
    folder: Optional[str] = None
    in_es: bool
    in_vector: bool

    class Config:
        populate_by_name = True


class SearchResponse(BaseModel):
    """Response model for hybrid search."""
    query: str
    total_results: int
    method: str
    weights: Dict[str, float]
    results: List[Dict[str, Any]]  # Use Dict for flexibility


class IndexEmailRequest(BaseModel):
    """Request model for indexing an email."""
    email_id: str = Field(..., description="Unique email identifier")
    subject: str
    body: str
    from_address: str = Field(..., alias="from")
    to: List[str]
    date: str
    account_id: str
    folder: str = "INBOX"
    ai_category: Optional[str] = None


# ==================== API Endpoints ==================== #

@app.post("/api/search", response_model=SearchResponse)
async def search_emails(request: SearchRequest):
    """
    Perform hybrid search combining Elasticsearch and vector similarity.
    
    This endpoint:
    1. Queries Elasticsearch for keyword matches
    2. Queries VectorDB for semantic similarity
    3. Combines results using configurable weighting
    4. Returns ranked, deduplicated results
    
    Example:
        POST /api/search
        {
            "query": "invoice payment details",
            "account_id": "user@example.com",
            "max_results": 10,
            "semantic_weight": 0.7,
            "keyword_weight": 0.3
        }
    """
    try:
        logger.info(f"Search request: query='{request.query}', method={request.method}")
        
        # Validate weights sum to 1.0
        if abs((request.semantic_weight + request.keyword_weight) - 1.0) > 1e-6:
            raise HTTPException(
                status_code=400,
                detail="semantic_weight + keyword_weight must equal 1.0"
            )
        
        # 1. Get Elasticsearch results
        # NOTE: In production, this would call your TypeScript ElasticsearchService
        # via HTTP API or subprocess. For this example, we'll simulate it.
        es_results = await get_elasticsearch_results(
            query=request.query,
            account_id=request.account_id,
            folder=request.folder,
            category=request.category,
            size=50  # Get more candidates for better hybrid ranking
        )
        
        # 2. Get VectorDB results
        vector_where = {}
        if request.account_id:
            vector_where["accountId"] = request.account_id
        if request.folder:
            vector_where["folder"] = request.folder
        if request.category:
            vector_where["aiCategory"] = request.category
        
        vector_results = vector_db.search(
            query=request.query,
            n_results=50,
            where=vector_where if vector_where else None
        )
        
        # 3. Configure hybrid search
        config = HybridSearchConfig(
            semantic_weight=request.semantic_weight,
            keyword_weight=request.keyword_weight,
            method=request.method,
            max_results=request.max_results,
            min_score_threshold=request.min_score
        )
        
        # 4. Combine results
        combined_results = hybrid_search(
            query=request.query,
            es_results=es_results,
            vector_results=vector_results,
            config=config
        )
        
        # 5. Format response
        return SearchResponse(
            query=request.query,
            total_results=len(combined_results),
            method=request.method,
            weights={
                "semantic": request.semantic_weight,
                "keyword": request.keyword_weight
            },
            results=combined_results
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/index")
async def index_email(request: IndexEmailRequest):
    """
    Index an email to both Elasticsearch and VectorDB.
    
    This ensures the email is searchable via both keyword and semantic search.
    
    Example:
        POST /api/index
        {
            "email_id": "msg-12345",
            "subject": "Q4 Financial Report",
            "body": "Please find attached...",
            "from": "cfo@company.com",
            "to": ["manager@company.com"],
            "date": "2025-10-07T10:00:00Z",
            "account_id": "user@example.com",
            "folder": "INBOX"
        }
    """
    try:
        logger.info(f"Indexing email: {request.email_id}")
        
        # 1. Index to Elasticsearch
        # NOTE: In production, call your TypeScript ElasticsearchService
        await index_to_elasticsearch(request)
        
        # 2. Index to VectorDB
        content = f"Subject: {request.subject}\n\nFrom: {request.from_address}\n\n{request.body}"
        
        metadata = {
            "accountId": request.account_id,
            "folder": request.folder,
            "from": request.from_address,
            "to": request.to,
            "subject": request.subject,
            "date": request.date,
            "aiCategory": request.ai_category,
        }
        
        vector_db.add_email(
            email_id=request.email_id,
            content=content,
            metadata=metadata
        )
        
        return {
            "success": True,
            "email_id": request.email_id,
            "message": "Email indexed successfully to both systems"
        }
        
    except Exception as e:
        logger.error(f"Indexing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/index/batch")
async def batch_index_emails(emails: List[IndexEmailRequest]):
    """
    Batch index multiple emails for efficiency.
    
    This is much faster than indexing emails one-by-one.
    
    Example:
        POST /api/index/batch
        [
            { "email_id": "msg-1", "subject": "...", ... },
            { "email_id": "msg-2", "subject": "...", ... },
            ...
        ]
    """
    try:
        logger.info(f"Batch indexing {len(emails)} emails")
        
        # 1. Index to Elasticsearch (one by one, or batch if supported)
        for email in emails:
            await index_to_elasticsearch(email)
        
        # 2. Batch index to VectorDB
        email_tuples = [
            (
                email.email_id,
                f"Subject: {email.subject}\n\nFrom: {email.from_address}\n\n{email.body}"
            )
            for email in emails
        ]
        
        metadatas = [
            {
                "accountId": email.account_id,
                "folder": email.folder,
                "from": email.from_address,
                "to": email.to,
                "subject": email.subject,
                "date": email.date,
                "aiCategory": email.ai_category,
            }
            for email in emails
        ]
        
        count = vector_db.add_emails(email_tuples, metadatas=metadatas)
        
        return {
            "success": True,
            "indexed_count": count,
            "message": f"Successfully indexed {count} emails"
        }
        
    except Exception as e:
        logger.error(f"Batch indexing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """
    Get statistics about the search indexes.
    
    Returns counts and status information.
    """
    try:
        vector_count = len(vector_db)
        
        # In production, would also get ES count
        es_count = 0  # Placeholder
        
        return {
            "elasticsearch": {
                "indexed_count": es_count,
                "status": "active"
            },
            "vector_db": {
                "indexed_count": vector_count,
                "model": "all-MiniLM-L6-v2",
                "persist_directory": vector_db.persist_directory,
                "status": "active"
            }
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Helper Functions ==================== #

async def get_elasticsearch_results(
    query: str,
    account_id: Optional[str],
    folder: Optional[str],
    category: Optional[str],
    size: int = 50
) -> List[Dict[str, Any]]:
    """
    Get results from Elasticsearch.
    
    In production, this would make an HTTP call to your TypeScript service
    or use a subprocess to execute Node.js code.
    
    For this example, we return mock data.
    """
    # TODO: Implement actual Elasticsearch integration
    # This is a placeholder that would be replaced with actual ES calls
    
    logger.warning("Using mock Elasticsearch results - implement actual integration")
    
    return [
        {
            "id": "mock-es-1",
            "score": 15.2,
            "subject": f"Result for {query}",
            "from": "sender@example.com",
            "body": f"Email content matching {query}",
            "date": "2025-10-07T10:00:00Z",
            "folder": folder or "INBOX",
            "accountId": account_id or "user@example.com",
        }
    ]


async def index_to_elasticsearch(email: IndexEmailRequest) -> None:
    """
    Index an email to Elasticsearch.
    
    In production, this would call your TypeScript ElasticsearchService.
    """
    # TODO: Implement actual Elasticsearch integration
    logger.warning("Mock Elasticsearch indexing - implement actual integration")
    pass


# ==================== Startup/Shutdown Events ==================== #

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Email Hybrid Search API")
    logger.info(f"VectorDB initialized with {len(vector_db)} documents")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Email Hybrid Search API")


# ==================== Health Check ==================== #

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "email-hybrid-search",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
