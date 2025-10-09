"""
Onebox Aggregator API Server

This FastAPI server provides RESTful endpoints for email search and management.
It integrates with the hybrid search service and provides a clean API interface
for the Streamlit UI and other clients.

Endpoints:
- GET /api/emails/search: Search emails using hybrid or vector search
- GET /api/emails/{email_id}: Get email details by ID
- POST /api/emails/classify: Classify email text
- GET /health: Service health check
- GET /: Root endpoint with API information

Usage:
    python api_server.py
    
    Then access:
    - API: http://localhost:3000
    - Docs: http://localhost:3000/docs
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Try to import the search service
HybridSearchClass = None
try:
    from search_service import HybridSearch as _HybridSearch
    HYBRID_SEARCH_AVAILABLE = True
    HybridSearchClass = _HybridSearch
except ImportError as e:
    print(f"⚠️  Warning: Could not import HybridSearch: {e}")
    print("   Search functionality will be limited.")
    HYBRID_SEARCH_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Onebox Aggregator API",
    description="Email aggregation, search, and classification API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
hybrid_search = None
if HYBRID_SEARCH_AVAILABLE and HybridSearchClass is not None:
    try:
        hybrid_search = HybridSearchClass()
        logger.info("✅ HybridSearch service initialized successfully")
        if hasattr(hybrid_search, "vector_enabled") and not hybrid_search.vector_enabled:
            logger.info("🔕 Vector search disabled (ENABLE_VECTORDB=false or VectorDB unavailable)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize HybridSearch: {e}")

# Pydantic models
class SearchResponse(BaseModel):
    query: str
    type: str
    count: int
    results: List[Dict[str, Any]]
    processing_time_ms: Optional[float] = None

class ClassifyRequest(BaseModel):
    text: str

class ClassifyResponse(BaseModel):
    category: str
    confidence: float
    text: str

class HealthResponse(BaseModel):
    status: str
    services: Dict[str, bool]
    timestamp: str

# Routes
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Onebox Aggregator API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "search": "GET /api/emails/search?q=query&type=hybrid",
            "classify": "POST /api/emails/classify",
            "health": "GET /health",
            "docs": "GET /docs"
        },
        "documentation": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "api": True,
            "hybrid_search": hybrid_search is not None,
            "vector_db": bool(
                hybrid_search is not None
                and getattr(hybrid_search, "vector_enabled", False)
            )
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/emails/search", response_model=SearchResponse)
async def search_emails(
    q: str = Query(..., description="Search query string"),
    type: str = Query("hybrid", description="Search type: 'hybrid', 'vector', or 'keyword'"),
    n_results: int = Query(10, ge=1, le=100, description="Number of results to return"),
    category: Optional[str] = Query(None, description="Filter by email category")
):
    """
    Search emails using hybrid, vector, or keyword search.
    
    Parameters:
    - **q**: Search query string (required)
    - **type**: Search type - 'hybrid' (default), 'vector', or 'keyword'
    - **n_results**: Number of results to return (1-100, default: 10)
    - **category**: Optional category filter
    
    Returns:
    - Search results with email IDs and scores
    """
    if not hybrid_search:
        raise HTTPException(
            status_code=503,
            detail="Search service is not available. Ensure backend dependencies are installed."
        )
    
    start_time = datetime.utcnow()
    
    try:
        vector_enabled = getattr(hybrid_search, "vector_enabled", True)
        # Perform search based on type
        if type == "hybrid":
            results = hybrid_search.search(q, n_results=n_results)
            # Convert to detailed format
            formatted_results = [
                {
                    "id": email_id,
                    "score": 1.0,  # Placeholder score
                    "match_type": "hybrid" if vector_enabled else "keyword-only"
                }
                for email_id in results
            ]
        elif type == "vector":
            if not vector_enabled:
                raise HTTPException(
                    status_code=503,
                    detail="Vector search is disabled. Set ENABLE_VECTORDB=true and ensure VectorDB dependencies are installed."
                )
            vector_results = hybrid_search.search_vector(q, n_results=n_results)
            formatted_results = [
                {
                    "id": email_id,
                    "score": float(score),
                    "match_type": "semantic"
                }
                for email_id, score in vector_results
            ]
        elif type == "keyword":
            keyword_results = hybrid_search.search_keyword(q, n_results=n_results)
            formatted_results = [
                {
                    "id": email_id,
                    "score": float(score),
                    "match_type": "keyword"
                }
                for email_id, score in keyword_results
            ]
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid search type: {type}. Must be 'hybrid', 'vector', or 'keyword'"
            )
        
        # Apply category filter if provided
        if category:
            # This would require integration with Elasticsearch to filter by category
            # For now, we'll just pass through the results
            logger.info(f"Category filter '{category}' requested (not yet implemented)")
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return SearchResponse(
            query=q,
            type=type,
            count=len(formatted_results),
            results=formatted_results,
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

@app.get("/api/emails/{email_id}")
async def get_email(email_id: str):
    """
    Get email details by ID.
    
    Parameters:
    - **email_id**: Unique email identifier
    
    Returns:
    - Email details including subject, from, to, date, and content
    """
    # This would require integration with Elasticsearch or a database
    # For now, return a mock response
    
    # TODO: Implement actual email retrieval from Elasticsearch
    return {
        "id": email_id,
        "subject": "Email Subject",
        "from": "sender@example.com",
        "to": "recipient@example.com",
        "date": datetime.utcnow().isoformat(),
        "content": "Email content would be loaded from Elasticsearch",
        "category": "Unclassified",
        "note": "This is a mock response. Implement Elasticsearch integration for real data."
    }

@app.post("/api/emails/classify", response_model=ClassifyResponse)
async def classify_email(request: ClassifyRequest):
    """
    Classify email text using AI.
    
    Parameters:
    - **text**: Email text to classify
    
    Returns:
    - Category and confidence score
    """
    # This would require integration with the AI classification service
    # For now, return a mock response
    logger.info(f"Classifying text: {request.text[:50]}...")
    
    # TODO: Implement actual AI classification
    return ClassifyResponse(
        category="Interested",
        confidence=0.85,
        text=request.text
    )

@app.get("/api/stats")
async def get_statistics():
    """
    Get API and search statistics.
    
    Returns:
    - Service statistics and metrics
    """
    vector_enabled = bool(hybrid_search and getattr(hybrid_search, "vector_enabled", False))
    stats = {
        "api_version": "1.0.0",
        "uptime": "Active",
        "services": {
            "hybrid_search": hybrid_search is not None,
            "vector_search": vector_enabled,
        }
    }
    
    # Try to get VectorDB stats if available
    vector_db_client = getattr(hybrid_search, "vector_db", None) if vector_enabled else None
    if vector_db_client:
        try:
            collection = getattr(vector_db_client, "collection", None)
            if collection is not None and hasattr(collection, "count"):
                count = collection.count()  # type: ignore[call-arg]
            elif hasattr(vector_db_client, "get_email_count"):
                count = vector_db_client.get_email_count()
            else:
                count = len(vector_db_client) if hasattr(vector_db_client, "__len__") else 0

            stats["vector_store"] = {
                "email_count": int(count),
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Error getting VectorDB stats: {e}")
            stats["vector_store"] = {"status": "error", "message": str(e)}
    else:
        stats["vector_store"] = {"status": "disabled"}
    
    return stats


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting Onebox Aggregator API Server")
    print("="*60)
    print(f"📍 API Base URL: http://localhost:3000")
    print(f"📚 API Documentation: http://localhost:3000/docs")
    print(f"🔍 Health Check: http://localhost:3000/health")
    print("="*60)
    
    if not HYBRID_SEARCH_AVAILABLE:
        print("\n⚠️  WARNING: HybridSearch service is not available!")
        print("   Make sure VectorDB service is running:")
        print("   python vectordb_service.py")
        print()
    elif hybrid_search and not getattr(hybrid_search, "vector_enabled", False):
        print("\nℹ️  Vector search disabled. Running keyword-only mode.")
        print("   To enable, install vector dependencies and set ENABLE_VECTORDB=true.")
    
    print("\n💡 To test the API, try:")
    print('   curl "http://localhost:3000/api/emails/search?q=test&type=hybrid"')
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3000,
        log_level="info"
    )
