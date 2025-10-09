# Onebox Aggregator API Gateway Integration Guide

## Overview

The API Gateway (`api_gateway_onebox.py`) provides a single entry point for all Onebox Aggregator services. It routes requests to the appropriate backend services and provides unified error handling, health checks, and CORS support.

## Architecture

```
Frontend/Client
       ↓
API Gateway (Port 3001)
       ↓
┌─────────────────┬─────────────────┐
│   API Server    │  VectorDB       │
│   (Port 3000)   │  Service        │
│                 │  (Port 8001)    │
└─────────────────┴─────────────────┘
```

## Service Ports

| Service | Port | Status |
|---------|------|--------|
| **API Gateway** | 3001 | ✅ Integrated & Tested |
| API Server | 3000 | Routes to email/search endpoints |
| VectorDB Service | 8001 | Routes to vector search endpoints |
| Node.js Service | 3000 | (Optional, for IMAP functionality) |

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Ensure httpx is installed for the gateway
pip install httpx
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your actual configuration values
```

### 3. Start Services

**Option A: Use PowerShell Script (Recommended)**
```powershell
# Start all services with health monitoring
.\start-services.ps1

# Start only the gateway (if other services are running)
.\start-services.ps1 -StartGatewayOnly

# Skip dependency checks
.\start-services.ps1 -SkipDependencyCheck
```

**Option B: Use Batch File (Simple)**
```cmd
# Start all services in separate windows
start-services.bat
```

**Option C: Manual Start (Individual)**
```bash
# Terminal 1: Start VectorDB Service
python vectordb_service.py

# Terminal 2: Start API Server  
python api_server.py

# Terminal 3: Start API Gateway
python api_gateway_onebox.py
```

## API Gateway Endpoints

### Health & Status

```bash
# Gateway health check
GET http://localhost:3001/health

# Gateway information
GET http://localhost:3001/

# Service statistics
GET http://localhost:3001/api/stats
```

### Search Endpoints

```bash
# Hybrid search (via API Server)
GET http://localhost:3001/api/search?q=your-query&type=hybrid&n_results=10

# Vector search (via VectorDB Service)
GET http://localhost:3001/api/vector-search?q=your-query&n_results=5

# Email search with filters
GET http://localhost:3001/api/emails/search?q=query&category=Work
```

### Email Management

```bash
# Get email by ID
GET http://localhost:3001/api/emails/{email_id}

# Classify email content
POST http://localhost:3001/api/emails/classify
Content-Type: application/json
{
  "text": "Email content to classify"
}
```

### VectorDB Operations

```bash
# Add single email to vector store
POST http://localhost:3001/api/vectordb/add_email
Content-Type: application/json
{
  "email_id": "unique-id",
  "content": "Email subject and body"
}

# Add multiple emails (batch)
POST http://localhost:3001/api/vectordb/add_emails
Content-Type: application/json
{
  "emails": [
    {"email_id": "id1", "content": "content1"},
    {"email_id": "id2", "content": "content2"}
  ]
}
```

## Configuration

### Environment Variables

The gateway uses these environment variables (see `.env.example`):

```bash
# Gateway Configuration
API_SERVER_URL=http://localhost:3000
VECTORDB_SERVICE_URL=http://localhost:8001
GATEWAY_PORT=3001

# Service Endpoints
ELASTICSEARCH_URL=http://localhost:9200
VECTORDB_PATH=./vector_store
```

### Service Dependencies

| Gateway Feature | Requires |
|----------------|----------|
| Basic routing | ✅ Always available |
| Search endpoints | API Server running |
| Vector search | VectorDB Service running |
| Email classification | API Server + AI models |
| Full functionality | All services running |

## Testing the Integration

### 1. Health Check Test

```bash
# Test gateway health
curl http://localhost:3001/health

# Expected response:
{
  "status": "healthy|degraded",
  "services": {
    "api_server": true,
    "vectordb_service": true,
    "last_check": "2025-10-08T14:58:29.686Z"
  },
  "timestamp": "2025-10-08T14:58:29.686Z"
}
```

### 2. Search Test

```bash
# Test search routing
curl "http://localhost:3001/api/search?q=test&type=hybrid"

# Test vector search routing
curl "http://localhost:3001/api/vector-search?q=test&n_results=5"
```

### 3. API Documentation

Visit these URLs to test the services:

- **Gateway Docs**: http://localhost:3001/docs
- **Gateway Redoc**: http://localhost:3001/redoc
- **Gateway Health**: http://localhost:3001/health

## Troubleshooting

### Common Issues

**1. Gateway starts but backend services are unavailable**
```bash
# Check individual services
curl http://localhost:3000/health  # API Server
curl http://localhost:8001/health  # VectorDB Service

# Start missing services manually
python api_server.py
python vectordb_service.py
```

**2. Port conflicts**
```bash
# Check what's running on ports
netstat -an | findstr "3000 3001 8001"

# Change ports in .env file if needed
GATEWAY_PORT=3002
API_SERVER_URL=http://localhost:3000
```

**3. CORS issues**
- The gateway has CORS enabled for all origins
- For production, update the `allow_origins` setting

**4. Service discovery issues**
- Ensure all services use correct URLs in configuration
- Check firewall/antivirus settings

### Logs and Monitoring

```bash
# Service logs (when using startup scripts)
.\logs\api_gateway.log     # Gateway logs
.\logs\api_server.log      # API Server logs  
.\logs\vectordb_service.log # VectorDB logs

# Real-time monitoring
tail -f logs\api_gateway.log
```

## Production Deployment

### Docker Support

The project includes a `Dockerfile` for the Node.js service. For the complete system:

```dockerfile
# Example docker-compose.yml structure
version: '3.8'
services:
  gateway:
    build: .
    ports:
      - "3001:3001"
    environment:
      - API_SERVER_URL=http://api-server:3000
      - VECTORDB_SERVICE_URL=http://vectordb:8001
    depends_on:
      - api-server
      - vectordb
      
  api-server:
    # API Server configuration
    
  vectordb:
    # VectorDB Service configuration
```

### Environment Configuration

```bash
# Production environment variables
NODE_ENV=production
API_SERVER_URL=http://api-server:3000
VECTORDB_SERVICE_URL=http://vectordb:8001
ELASTICSEARCH_URL=http://elasticsearch:9200
```

## API Client Examples

### JavaScript/TypeScript

```javascript
// Gateway client example
class OneboxAPIClient {
  constructor(baseURL = 'http://localhost:3001') {
    this.baseURL = baseURL;
  }

  async search(query, type = 'hybrid', nResults = 10) {
    const response = await fetch(
      `${this.baseURL}/api/search?q=${encodeURIComponent(query)}&type=${type}&n_results=${nResults}`
    );
    return response.json();
  }

  async vectorSearch(query, nResults = 5) {
    const response = await fetch(
      `${this.baseURL}/api/vector-search?q=${encodeURIComponent(query)}&n_results=${nResults}`
    );
    return response.json();
  }

  async getHealth() {
    const response = await fetch(`${this.baseURL}/health`);
    return response.json();
  }
}

// Usage
const client = new OneboxAPIClient();
const results = await client.search('project updates');
console.log(results);
```

### Python

```python
import requests

class OneboxAPIClient:
    def __init__(self, base_url="http://localhost:3001"):
        self.base_url = base_url

    def search(self, query, search_type="hybrid", n_results=10):
        response = requests.get(
            f"{self.base_url}/api/search",
            params={"q": query, "type": search_type, "n_results": n_results}
        )
        return response.json()

    def vector_search(self, query, n_results=5):
        response = requests.get(
            f"{self.base_url}/api/vector-search",
            params={"q": query, "n_results": n_results}
        )
        return response.json()

    def get_health(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Usage
client = OneboxAPIClient()
results = client.search("project updates")
print(results)
```

## Next Steps

1. **Configure your email provider** in the `.env` file
2. **Start all services** using one of the startup scripts
3. **Test the gateway** using the provided curl commands
4. **Integrate with your frontend** using the client examples
5. **Monitor logs** for any issues or errors
6. **Scale for production** using Docker or container orchestration

## Support

- **Logs**: Check the `logs/` directory for detailed service logs
- **Health checks**: Use `/health` endpoints to monitor service status
- **API Documentation**: Visit `/docs` for interactive API testing
- **Configuration**: Refer to `.env.example` for all available settings