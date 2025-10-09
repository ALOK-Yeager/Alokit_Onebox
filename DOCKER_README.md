# Docker Deployment for Onebox Aggregator Python Services

## Quick Start

### 1. Build and Run All Services
```bash
# Windows PowerShell
.\docker-deploy.ps1 start

# Linux/Mac
./docker-deploy.sh start
```

### 2. Build Individual Services
```bash
# Build API Server
.\docker-deploy.ps1 build api-server

# Build VectorDB Service  
.\docker-deploy.ps1 build vectordb

# Build API Gateway
.\docker-deploy.ps1 build api-gateway
```

### 3. Run Individual Services
```bash
# Run API Server only
.\docker-deploy.ps1 run api-server

# Run VectorDB Service only
.\docker-deploy.ps1 run vectordb

# Run API Gateway only
.\docker-deploy.ps1 run api-gateway
```

## Docker Files

| File | Purpose |
|------|---------|
| `Dockerfile.python` | Multi-service Python Dockerfile |
| `docker-compose.python.yml` | Orchestration for all services |
| `.dockerignore.python` | Excludes unnecessary files |
| `docker-deploy.ps1` | Windows PowerShell deployment script |
| `docker-deploy.sh` | Linux/Mac bash deployment script |

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| **API Gateway** | 3001 | Main entry point, routes to other services |
| API Server | 3000 | FastAPI server for email search and management |
| VectorDB Service | 8001 | Vector database for semantic search |
| Elasticsearch | 9200 | (Optional) Search engine |

## Environment Variables

Create a `.env` file with these variables:

```bash
# Core Configuration
VECTORDB_PATH=/app/vector_store
API_SERVER_URL=http://api-server:3000
VECTORDB_SERVICE_URL=http://vectordb:8001

# Performance Settings
CUDA_VISIBLE_DEVICES=-1
FORCE_CPU=1
TOKENIZERS_PARALLELISM=false

# External Services
ELASTICSEARCH_URL=http://elasticsearch:9200
GROQ_API_KEY=your_groq_api_key_here

# Email Configuration (if needed)
IMAP_SERVER=your.imap.server.com
IMAP_USER=your.email@example.com
IMAP_PASSWORD=your_password
```

## Usage Examples

### Build and Test
```bash
# Build all images
.\docker-deploy.ps1 build

# Start all services
.\docker-deploy.ps1 start

# Check health
.\docker-deploy.ps1 health

# View logs
.\docker-deploy.ps1 logs

# Stop everything
.\docker-deploy.ps1 stop
```

### Individual Service Management
```bash
# Run just the API Gateway
.\docker-deploy.ps1 run api-gateway

# View API Gateway logs
.\docker-deploy.ps1 logs api-gateway

# Check specific service health
curl http://localhost:3001/health
```

### Development Workflow
```bash
# Make code changes
# Rebuild and restart
.\docker-deploy.ps1 restart

# Or rebuild specific service
.\docker-deploy.ps1 build api-server
.\docker-deploy.ps1 run api-server
```

## Dockerfile Features

✅ **Multi-service support** - Single Dockerfile builds any service  
✅ **Optimized layers** - Efficient caching and build times  
✅ **Security** - Non-root user execution  
✅ **Health checks** - Built-in service monitoring  
✅ **Environment configuration** - Flexible configuration via env vars  
✅ **CPU optimization** - Forced CPU execution for ML models  

## Troubleshooting

### Service Won't Start
```bash
# Check logs
.\docker-deploy.ps1 logs [service-name]

# Check if Docker is running
docker info

# Rebuild with no cache
docker build --no-cache -f Dockerfile.python -t onebox-aggregator:api-server .
```

### Port Conflicts
```bash
# Check what's using ports
netstat -an | findstr "3000 3001 8001"

# Change ports in docker-compose.python.yml if needed
```

### Missing Dependencies
```bash
# Update requirements files
# Rebuild images
.\docker-deploy.ps1 build
```

### Clean Start
```bash
# Remove everything and start fresh
.\docker-deploy.ps1 clean
.\docker-deploy.ps1 start
```

## Production Deployment

For production, update `docker-compose.python.yml`:

```yaml
# Add resource limits
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'

# Use specific image tags
image: onebox-aggregator:api-server-v1.0.0

# Add restart policies
restart: always

# Use secrets for sensitive data
secrets:
  - source: groq_api_key
    target: /run/secrets/groq_api_key
```

## Monitoring

All services include health checks accessible at:
- http://localhost:3001/health (API Gateway)
- http://localhost:3000/health (API Server)
- http://localhost:8001/health (VectorDB Service)

Use these for monitoring and load balancer health checks.