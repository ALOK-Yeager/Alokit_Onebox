"""
API Gateway for Onebox Aggregator Services

This FastAPI server acts as a gateway that routes requests to the appropriate
backend services (API Server and VectorDB Service). It provides a single
entry point for the frontend application.

Features:
- Routes /api/search to the API Server
- Routes /api/vector-search to the VectorDB Service
- Handles health checks for all services
- Manages CORS for frontend integration
- Provides unified error handling

Usage:
    python api_gateway.py
    
    Then access:
    - Gateway: http://localhost:3001
    - API Server: http://localhost:3000 (proxied)
    - VectorDB Service: http://localhost:8001 (proxied)
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Service URLs
API_SERVER_URL = os.getenv("API_SERVER_URL", "http://localhost:3002")
VECTORDB_SERVICE_URL = os.getenv("VECTORDB_SERVICE_URL", "http://localhost:8001")
NODE_BACKEND_URL = os.getenv("NODE_BACKEND_URL", "http://localhost:3000")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "3001"))

# Initialize FastAPI app
app = FastAPI(
    title="Onebox Aggregator API Gateway",
    description="Gateway service for Onebox Aggregator backend services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service health status
service_status = {
    "api_server": False,
    "vectordb_service": False,
    "last_check": None
}

async def check_service_health():
    """Check the health of all backend services"""
    global service_status
    
    # Check API Server
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_SERVER_URL}/health", timeout=5.0)
            service_status["api_server"] = response.status_code == 200
    except Exception as e:
        logger.error(f"API Server health check failed: {e}")
        service_status["api_server"] = False
    
    # Check VectorDB Service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{VECTORDB_SERVICE_URL}/health", timeout=5.0)
            service_status["vectordb_service"] = response.status_code == 200
    except Exception as e:
        logger.error(f"VectorDB Service health check failed: {e}")
        service_status["vectordb_service"] = False
    
    service_status["last_check"] = datetime.utcnow().isoformat()
    return service_status

async def proxy_request(request: Request, target_url: str):
    """Proxy a request to the target service"""
    # Prepare the request data
    url = f"{target_url}{request.url.path}"
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header to avoid conflicts
    
    # Get request body if present
    body = await request.body()
    
    # Make the request to the target service
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params
            )
            
            # Return the response from the target service
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.RequestError as e:
            logger.error(f"Request to {url} failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {str(e)}"
            )

@app.on_event("startup")
async def startup_event():
    """Check service health on startup"""
    await check_service_health()
    logger.info("API Gateway started")
    logger.info(f"API Server URL: {API_SERVER_URL}")
    logger.info(f"VectorDB Service URL: {VECTORDB_SERVICE_URL}")

@app.get("/")
async def root():
    """Root endpoint with gateway information"""
    return {
        "service": "Onebox Aggregator API Gateway",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "search": "GET /api/search?q=query",
            "vector_search": "GET /api/vector-search?q=query",
            "health": "GET /health",
            "docs": "GET /docs"
        },
        "services": {
            "api_server": API_SERVER_URL,
            "vectordb_service": VECTORDB_SERVICE_URL
        },
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    """Check the health of the gateway and all backend services"""
    await check_service_health()
    
    return {
        "status": "healthy" if all(service_status.values()) else "degraded",
        "services": service_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# Route /api/search to the API Server
@app.api_route("/api/search", methods=["GET", "POST"])
async def search_proxy(request: Request):
    """Proxy search requests to the API Server"""
    if not service_status["api_server"]:
        raise HTTPException(
            status_code=503,
            detail="API Server is currently unavailable"
        )
    
    # For GET requests, redirect to /api/emails/search on the API Server
    if request.method == "GET":
        target_url = f"{API_SERVER_URL}/api/emails/search"
    else:
        target_url = f"{API_SERVER_URL}/api/search"
    
    return await proxy_request(request, target_url)

# Route /api/vector-search to the VectorDB Service
@app.api_route("/api/vector-search", methods=["GET", "POST"])
async def vector_search_proxy(request: Request):
    """Proxy vector search requests to the VectorDB Service"""
    if not service_status["vectordb_service"]:
        raise HTTPException(
            status_code=503,
            detail="VectorDB Service is currently unavailable"
        )
    
    # For GET requests, redirect to /search on the VectorDB Service
    if request.method == "GET":
        target_url = f"{VECTORDB_SERVICE_URL}/search"
    else:
        target_url = f"{VECTORDB_SERVICE_URL}/vector-search"
    
    return await proxy_request(request, target_url)

# Route /api/emails/* to the API Server
@app.api_route("/api/emails/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def emails_proxy(request: Request, path: str):
    """Proxy email-related requests to the API Server"""
    if not service_status["api_server"]:
        raise HTTPException(
            status_code=503,
            detail="API Server is currently unavailable"
        )
    
    target_url = f"{API_SERVER_URL}/api/emails/{path}"
    return await proxy_request(request, target_url)

# Route /api/stats to the API Server
@app.get("/api/stats")
async def stats_proxy(request: Request):
    """Proxy stats requests to the API Server"""
    if not service_status["api_server"]:
        raise HTTPException(
            status_code=503,
            detail="API Server is currently unavailable"
        )
    
    target_url = f"{API_SERVER_URL}/api/stats"
    return await proxy_request(request, target_url)

# Route /api/vectordb/* to the VectorDB Service
@app.api_route("/api/vectordb/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def vectordb_proxy(request: Request, path: str):
    """Proxy VectorDB requests to the VectorDB Service"""
    if not service_status["vectordb_service"]:
        raise HTTPException(
            status_code=503,
            detail="VectorDB Service is currently unavailable"
        )
    
    target_url = f"{VECTORDB_SERVICE_URL}/{path}"
    return await proxy_request(request, target_url)

# Exception handler for HTTPExceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "status_code": exc.status_code},
    )

# Exception handler for other exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "status_code": 500},
    )

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting Onebox Aggregator API Gateway")
    print("="*60)
    print(f"📍 Gateway URL: http://localhost:{GATEWAY_PORT}")
    print(f"📚 Gateway Documentation: http://localhost:{GATEWAY_PORT}/docs")
    print(f"🔍 Health Check: http://localhost:{GATEWAY_PORT}/health")
    print("="*60)
    print(f"🔗 API Server: {API_SERVER_URL}")
    print(f"🔗 VectorDB Service: {VECTORDB_SERVICE_URL}")
    print("="*60)
    
    print("\n💡 To test the gateway, try:")
    print(f'   curl "http://localhost:{GATEWAY_PORT}/api/search?q=test"')
    print(f'   curl "http://localhost:{GATEWAY_PORT}/api/vector-search?q=test"')
    print("\nPress CTRL+C to stop the gateway\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=GATEWAY_PORT,
        log_level="info"
    )