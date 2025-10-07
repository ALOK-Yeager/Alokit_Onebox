import os
# CRITICAL: Force CPU mode BEFORE importing torch
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["FORCE_CPU"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

"""
VectorDB FastAPI Service

Exposes the VectorDB class functionality via HTTP endpoints for integration
with TypeScript EmailIndexingService. Provides batch processing, health checks,
and comprehensive error handling.

Endpoints:
- POST /add_email: Add single email to vector store
- POST /add_emails: Add multiple emails in batch
- GET /search: Search for similar emails
- GET /health: Service health check
- GET /stats: Vector store statistics

Usage:
    uvicorn vectordb_service:app --host 0.0.0.0 --port 8001

Environment:
    VECTORDB_PATH: Path to persistent storage (default: ./vector_store)
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Now import torch (safe to do after env vars set)
import torch

# Verify it's using CPU
print(f"PyTorch is using: {'CUDA' if torch.cuda.is_available() else 'CPU'}")

def force_cpu_torch():
    """Ensure torch uses CPU even if CUDA is mistakenly detected"""
    if hasattr(torch, 'cuda'):
        torch.cuda.is_available = lambda: False
        torch.cuda.current_device = lambda: None
        torch.cuda.get_device_name = lambda *args: 'CPU'

# Call it right after importing torch
force_cpu_torch()

# Import our VectorDB class
from src.Services.search.VectorDB import VectorDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VectorDB Service",
    description="Email Vector Database API for semantic search",
    version="1.0.0"
)

# Add CORS middleware for TypeScript service
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global VectorDB instance
vector_db: Optional[VectorDB] = None
service_stats = {
    "start_time": datetime.now(),
    "requests_processed": 0,
    "emails_indexed": 0,
    "searches_performed": 0,
    "errors": 0,
    "last_activity": datetime.now()
}

# Pydantic models for request/response
class EmailData(BaseModel):
    email_id: str = Field(..., description="Unique email identifier")
    content: str = Field(..., min_length=1, description="Email content (subject + body)")

class BatchEmailData(BaseModel):
    emails: List[EmailData] = Field(..., description="List of emails to index")

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    n_results: int = Field(5, ge=1, le=100, description="Number of results to return")
    filter_metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata filters")

class EmailResponse(BaseModel):
    success: bool
    email_id: str
    processing_time_ms: float
    error: Optional[str] = None

class BatchResponse(BaseModel):
    success: bool
    processed: int
    successful: int
    failed: int
    total_processing_time_ms: float
    results: List[EmailResponse]
    errors: List[str] = []

class SearchResult(BaseModel):
    email_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = {}

class SearchResponse(BaseModel):
    success: bool
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time_ms: float

class HealthResponse(BaseModel):
    status: str
    vector_db_available: bool
    total_emails: int
    uptime_seconds: float
    memory_usage_mb: Optional[float] = None

class StatsResponse(BaseModel):
    start_time: str
    uptime_seconds: float
    requests_processed: int
    emails_indexed: int
    searches_performed: int
    errors: int
    last_activity: str
    total_emails: int
    vector_db_status: str

@app.on_event("startup")
async def startup_event():
    """Initialize VectorDB on service startup"""
    global vector_db
    try:
        vector_db_path = os.getenv('VECTORDB_PATH', './vector_store')
        logger.info(f"Initializing VectorDB at: {vector_db_path}")
        
        vector_db = VectorDB(persist_directory=vector_db_path)
        
        # Test the connection
        test_count = len(vector_db)
        logger.info(f"VectorDB initialized successfully. Current emails: {test_count}")
        
    except Exception as e:
        logger.error(f"Failed to initialize VectorDB: {e}")
        # Don't crash the service, but mark VectorDB as unavailable
        vector_db = None

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on service shutdown"""
    global vector_db
    if vector_db:
        logger.info("Shutting down VectorDB service")
        # VectorDB handles persistence automatically
        vector_db = None

def update_stats(request_type: str, success: bool = True):
    """Update service statistics"""
    service_stats["requests_processed"] += 1
    service_stats["last_activity"] = datetime.now()
    
    if request_type == "index":
        if success:
            service_stats["emails_indexed"] += 1
    elif request_type == "search":
        if success:
            service_stats["searches_performed"] += 1
    elif request_type == "delete":
        # Track deletions but don't increment emails_indexed counter
        pass
    
    if not success:
        service_stats["errors"] += 1

@app.post("/add_email", response_model=EmailResponse)
async def add_email(email_data: EmailData, background_tasks: BackgroundTasks):
    """
    Add a single email to the vector store
    
    Args:
        email_data: Email data containing ID and content
        
    Returns:
        EmailResponse with success status and processing time
    """
    start_time = time.time()
    
    if not vector_db:
        update_stats("index", False)
        raise HTTPException(status_code=503, detail="VectorDB service unavailable")
    
    try:
        logger.debug(f"Adding email to vector store: {email_data.email_id}")
        
        # Add email to vector store
        vector_db.add_email(email_data.email_id, email_data.content)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Update stats in background
        background_tasks.add_task(update_stats, "index", True)
        
        logger.info(f"Successfully added email {email_data.email_id} (took {processing_time_ms:.2f}ms)")
        
        return EmailResponse(
            success=True,
            email_id=email_data.email_id,
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        error_msg = f"Failed to add email {email_data.email_id}: {str(e)}"
        logger.error(error_msg)
        
        # Update stats in background
        background_tasks.add_task(update_stats, "index", False)
        
        return EmailResponse(
            success=False,
            email_id=email_data.email_id,
            processing_time_ms=processing_time_ms,
            error=error_msg
        )

@app.post("/add_emails", response_model=BatchResponse)
async def add_emails(batch_data: BatchEmailData, background_tasks: BackgroundTasks):
    """
    Add multiple emails to the vector store in a batch operation
    
    Args:
        batch_data: Batch of emails to index
        
    Returns:
        BatchResponse with detailed results for each email
    """
    start_time = time.time()
    
    if not vector_db:
        update_stats("index", False)
        raise HTTPException(status_code=503, detail="VectorDB service unavailable")
    
    if not batch_data.emails:
        raise HTTPException(status_code=400, detail="No emails provided in batch")
    
    logger.info(f"Starting batch indexing of {len(batch_data.emails)} emails")
    
    results = []
    successful = 0
    errors = []
    
    try:
        # Prepare data for batch operation
        email_ids = [email.email_id for email in batch_data.emails]
        contents = [email.content for email in batch_data.emails]
        
        # Use VectorDB batch method for efficiency
        batch_start = time.time()
        # Create an iterable of (email_id, content) tuples
        email_data = zip(email_ids, contents)
        vector_db.add_emails(email_data)
        batch_time = time.time() - batch_start
        
        # All succeeded in batch operation
        for email in batch_data.emails:
            results.append(EmailResponse(
                success=True,
                email_id=email.email_id,
                processing_time_ms=batch_time * 1000 / len(batch_data.emails)  # Average time per email
            ))
            successful += 1
        
        logger.info(f"Batch indexing completed: {successful}/{len(batch_data.emails)} successful")
        
    except Exception as e:
        # Fallback to individual processing if batch fails
        logger.warning(f"Batch operation failed, falling back to individual processing: {e}")
        errors.append(f"Batch operation failed: {str(e)}")
        
        for email in batch_data.emails:
            try:
                email_start = time.time()
                vector_db.add_email(email.email_id, email.content)
                processing_time = (time.time() - email_start) * 1000
                
                results.append(EmailResponse(
                    success=True,
                    email_id=email.email_id,
                    processing_time_ms=processing_time
                ))
                successful += 1
                
            except Exception as individual_error:
                error_msg = f"Failed to add email {email.email_id}: {str(individual_error)}"
                results.append(EmailResponse(
                    success=False,
                    email_id=email.email_id,
                    processing_time_ms=0,
                    error=error_msg
                ))
                errors.append(error_msg)
    
    total_processing_time_ms = (time.time() - start_time) * 1000
    failed = len(batch_data.emails) - successful
    
    # Update stats in background
    for _ in range(successful):
        background_tasks.add_task(update_stats, "index", True)
    for _ in range(failed):
        background_tasks.add_task(update_stats, "index", False)
    
    return BatchResponse(
        success=successful > 0,
        processed=len(batch_data.emails),
        successful=successful,
        failed=failed,
        total_processing_time_ms=total_processing_time_ms,
        results=results,
        errors=errors
    )

@app.get("/search", response_model=SearchResponse)
async def search_emails(
    q: str,
    background_tasks: BackgroundTasks,
    n_results: int = 5
):
    """
    Search for emails using semantic similarity
    
    Args:
        q: Search query
        n_results: Number of results to return (1-100)
        
    Returns:
        SearchResponse with matching emails and scores
    """
    start_time = time.time()
    
    if not vector_db:
        update_stats("search", False)
        raise HTTPException(status_code=503, detail="VectorDB service unavailable")
    
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    if not 1 <= n_results <= 100:
        raise HTTPException(status_code=400, detail="n_results must be between 1 and 100")
    
    try:
        logger.debug(f"Searching for: '{q}' (top {n_results})")
        
        # Perform semantic search
        raw_results = vector_db.search(q, n_results=n_results)
        
        # Convert to response format
        search_results = []
        for result in raw_results:
            search_results.append(SearchResult(
                email_id=result['ids'][0] if result.get('ids') else 'unknown',
                content=result['documents'][0] if result.get('documents') else '',
                score=result['distances'][0] if result.get('distances') else 0.0,
                metadata=result.get('metadatas', [{}])[0] if result.get('metadatas') else {}
            ))
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Update stats in background
        background_tasks.add_task(update_stats, "search", True)
        
        logger.info(f"Search completed: '{q}' returned {len(search_results)} results (took {processing_time_ms:.2f}ms)")
        
        return SearchResponse(
            success=True,
            query=q,
            results=search_results,
            total_results=len(search_results),
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        error_msg = f"Search failed for query '{q}': {str(e)}"
        logger.error(error_msg)
        
        # Update stats in background
        background_tasks.add_task(update_stats, "search", False)
        
        return SearchResponse(
            success=False,
            query=q,
            results=[],
            total_results=0,
            processing_time_ms=processing_time_ms
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check service health and VectorDB availability
    
    Returns:
        HealthResponse with service status and statistics
    """
    uptime = (datetime.now() - service_stats["start_time"]).total_seconds()
    
    try:
        total_emails = len(vector_db) if vector_db else 0
        vector_db_available = vector_db is not None
        status = "healthy" if vector_db_available else "degraded"
        
        # Get memory usage if available
        memory_usage_mb = None
        try:
            import psutil
            process = psutil.Process()
            memory_usage_mb = process.memory_info().rss / 1024 / 1024
        except ImportError:
            pass
        
        return HealthResponse(
            status=status,
            vector_db_available=vector_db_available,
            total_emails=total_emails,
            uptime_seconds=uptime,
            memory_usage_mb=memory_usage_mb
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            vector_db_available=False,
            total_emails=0,
            uptime_seconds=uptime
        )

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get detailed service statistics
    
    Returns:
        StatsResponse with comprehensive service metrics
    """
    uptime = (datetime.now() - service_stats["start_time"]).total_seconds()
    
    try:
        total_emails = len(vector_db) if vector_db else 0
        vector_db_status = "available" if vector_db else "unavailable"
        
        return StatsResponse(
            start_time=service_stats["start_time"].isoformat(),
            uptime_seconds=uptime,
            requests_processed=service_stats["requests_processed"],
            emails_indexed=service_stats["emails_indexed"],
            searches_performed=service_stats["searches_performed"],
            errors=service_stats["errors"],
            last_activity=service_stats["last_activity"].isoformat(),
            total_emails=total_emails,
            vector_db_status=vector_db_status
        )
        
    except Exception as e:
        logger.error(f"Stats request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/delete_email")
async def delete_email(request: dict, background_tasks: BackgroundTasks):
    """
    Delete a single email from the vector store (for rollback operations)
    
    Args:
        request: Dictionary containing email_id to delete
        
    Returns:
        Success status and processing information
    """
    start_time = time.time()
    
    if not vector_db:
        update_stats("delete", False)
        raise HTTPException(status_code=503, detail="VectorDB service unavailable")
    
    email_id = request.get("email_id")
    if not email_id:
        raise HTTPException(status_code=400, detail="email_id is required")
    
    try:
        logger.debug(f"Deleting email from vector store: {email_id}")
        
        # Delete email from vector store
        success = vector_db.delete_email(email_id)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Update stats in background
        background_tasks.add_task(update_stats, "delete", success)
        
        if success:
            logger.info(f"Successfully deleted email {email_id} (took {processing_time_ms:.2f}ms)")
        else:
            logger.warning(f"Email {email_id} not found for deletion")
        
        return {
            "success": success,
            "email_id": email_id,
            "processing_time_ms": processing_time_ms,
            "message": "Email deleted successfully" if success else "Email not found"
        }
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        error_msg = f"Failed to delete email {email_id}: {str(e)}"
        logger.error(error_msg)
        
        background_tasks.add_task(update_stats, "delete", False)
        
        return {
            "success": False,
            "email_id": email_id,
            "processing_time_ms": processing_time_ms,
            "error": error_msg
        }

@app.post("/delete_emails")
async def delete_emails(request: dict, background_tasks: BackgroundTasks):
    """
    Delete multiple emails from the vector store in batch (for rollback operations)
    
    Args:
        request: Dictionary containing email_ids list to delete
        
    Returns:
        Batch deletion results with success/failure counts
    """
    start_time = time.time()
    
    if not vector_db:
        update_stats("delete", False)
        raise HTTPException(status_code=503, detail="VectorDB service unavailable")
    
    email_ids = request.get("email_ids", [])
    if not email_ids:
        raise HTTPException(status_code=400, detail="email_ids list is required")
    
    logger.info(f"Starting batch deletion of {len(email_ids)} emails")
    
    try:
        # Perform batch deletion
        results = vector_db.delete_emails(email_ids)
        
        total_processing_time_ms = (time.time() - start_time) * 1000
        
        # Update stats in background
        for _ in range(results.get("successful", 0)):
            background_tasks.add_task(update_stats, "delete", True)
        for _ in range(results.get("failed", 0)):
            background_tasks.add_task(update_stats, "delete", False)
        
        logger.info(f"Batch deletion completed: {results}")
        
        return {
            "success": results.get("successful", 0) > 0,
            "processed": len(email_ids),
            "successful": results.get("successful", 0),
            "failed": results.get("failed", 0),
            "total_processing_time_ms": total_processing_time_ms,
            "errors": results.get("errors", [])
        }
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        error_msg = f"Batch deletion failed: {str(e)}"
        logger.error(error_msg)
        
        background_tasks.add_task(update_stats, "delete", False)
        
        return {
            "success": False,
            "processed": len(email_ids),
            "successful": 0,
            "failed": len(email_ids),
            "total_processing_time_ms": processing_time_ms,
            "errors": [error_msg]
        }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "VectorDB API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "add_email": "POST /add_email",
            "add_emails": "POST /add_emails", 
            "search": "GET /search?q=query&n_results=5",
            "health": "GET /health",
            "stats": "GET /stats"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    import sys
    
    # Check if we're in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("\n🔍 Testing VectorDB functionality...")
        try:
            # Initialize DB
            db = VectorDB()
            print("✓ VectorDB initialized successfully")
            
            # Test adding an email
            test_id = "test_123"
            test_content = "This is a sample email about project updates and deadlines"
            test_metadata = {"subject": "Project Updates", "from": "test@example.com"}
            db.add_email(test_id, test_content, metadata=test_metadata)
            print(f"✓ Added test email with ID: {test_id}")
            
            # Test search
            results = db.search("project updates")
            print("✓ Search completed successfully")
            print(f"Search results: {results}")
            
            print("\n✅ All tests passed! VectorDB is ready for integration.")
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        # Development server
        uvicorn.run(
            "vectordb_service:app",
            host="0.0.0.0",
            port=8001,
            log_level="info",
            reload=True
        )