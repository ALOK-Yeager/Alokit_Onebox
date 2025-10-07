# 🏗️ System Architecture Diagram

## Complete System Overview

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ONEBOX EMAIL AGGREGATOR                              ║
║                    3-Tier Architecture for Email Search                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│                            PRESENTATION LAYER                                │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      Streamlit Web UI                              │    │
│  │                      Port: 8501                                    │    │
│  │                                                                    │    │
│  │  Features:                                                         │    │
│  │  • Natural language search interface                              │    │
│  │  • Category filtering (Important, Marketing, etc.)                │    │
│  │  • Dual search modes (API Mode / Direct Mode)                     │    │
│  │  • Expandable email preview cards                                 │    │
│  │  • Real-time result display                                       │    │
│  │                                                                    │    │
│  │  Access: http://localhost:8501                                    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 │
                                 │ HTTP REST API Calls
                                 │ (JSON Request/Response)
                                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            APPLICATION LAYER                                 │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      API Server                                    │    │
│  │                      Port: 3000                                    │    │
│  │                      (FastAPI)                                     │    │
│  │                                                                    │    │
│  │  Endpoints:                                                        │    │
│  │  GET  /                    → Welcome message                      │    │
│  │  GET  /health              → Service status check                 │    │
│  │  GET  /api/emails/search   → Search emails                        │    │
│  │       ?q=query             → Query parameter                      │    │
│  │       &type=hybrid         → Search type (hybrid/vector/keyword)  │    │
│  │  GET  /api/emails/{id}     → Get specific email                   │    │
│  │  POST /api/emails/classify → Classify email                       │    │
│  │  GET  /api/stats           → System statistics                    │    │
│  │  GET  /docs                → Swagger documentation                │    │
│  │                                                                    │    │
│  │  Features:                                                         │    │
│  │  • Request validation (Pydantic models)                           │    │
│  │  • Error handling & logging                                       │    │
│  │  • CORS middleware                                                │    │
│  │  • Auto-generated OpenAPI docs                                    │    │
│  │                                                                    │    │
│  │  Access: http://localhost:3000                                    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 │
                                 │ Search Orchestration
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         BUSINESS LOGIC LAYER                                 │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                   Hybrid Search Service                            │    │
│  │                   (search_service.py)                              │    │
│  │                                                                    │    │
│  │  Algorithm:                                                        │    │
│  │  1. Query both VectorDB (semantic) and Elasticsearch (keyword)    │    │
│  │  2. Normalize scores from both sources (0-1 range)                │    │
│  │  3. Apply weighted combination:                                   │    │
│  │     • 70% weight for semantic relevance                           │    │
│  │     • 30% weight for keyword matching                             │    │
│  │  4. Merge and deduplicate results                                 │    │
│  │  5. Sort by combined relevance score                              │    │
│  │  6. Return top N results                                          │    │
│  │                                                                    │    │
│  │  Fallback: If Elasticsearch unavailable → VectorDB only (100%)    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────┬────────────────────────────────────────┬───────────────────┘
                  │                                        │
                  │ Semantic Search                        │ Keyword Search
                  │ (Natural Language)                     │ (Exact Matching)
                  ▼                                        ▼
┌──────────────────────────────────────┐    ┌──────────────────────────────────┐
│        DATA LAYER - SEMANTIC         │    │       DATA LAYER - KEYWORD       │
│                                      │    │                                  │
│  ┌────────────────────────────────┐  │    │  ┌────────────────────────────┐ │
│  │   VectorDB Service             │  │    │  │   Elasticsearch            │ │
│  │   Port: 8001                   │  │    │  │   (Optional)               │ │
│  │   (FastAPI)                    │  │    │  │                            │ │
│  │                                │  │    │  │  Full-text search engine   │ │
│  │  Technology Stack:             │  │    │  │  • Inverted index          │ │
│  │  • ChromaDB (Vector Store)     │  │    │  │  • Fast keyword matching   │ │
│  │  • SentenceTransformers        │  │    │  │  • Boolean queries         │ │
│  │  • all-MiniLM-L6-v2 model      │  │    │  │  • Field-specific search   │ │
│  │  • PyTorch 2.6.0+cpu           │  │    │  │                            │ │
│  │                                │  │    │  └────────────────────────────┘ │
│  │  Capabilities:                 │  │    │                                  │
│  │  • Semantic similarity search  │  │    └──────────────────────────────────┘
│  │  • Context-aware queries       │  │
│  │  • Email embeddings (384-dim)  │  │
│  │  • Persistent storage          │  │
│  │                                │  │
│  │  Endpoints:                    │  │
│  │  GET  /health                  │  │
│  │  GET  /search?q=query          │  │
│  │  POST /add_email               │  │
│  │  POST /add_emails_batch        │  │
│  │  GET  /stats                   │  │
│  │  GET  /docs                    │  │
│  │                                │  │
│  │  Storage:                      │  │
│  │  ./vector_store/               │  │
│  │  • ChromaDB SQLite database    │  │
│  │  • Embedding vectors           │  │
│  │  • Email metadata              │  │
│  │                                │  │
│  │  Access: localhost:8001        │  │
│  └────────────────────────────────┘  │
│                                      │
└──────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

                           CPU OPTIMIZATION STACK

╔══════════════════════════════════════════════════════════════════════════════╗
║                     NO GPU REQUIRED - 100% CPU OPTIMIZED                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│  Machine Learning Stack:                                                     │
│                                                                              │
│  PyTorch 2.6.0+cpu                                                          │
│  ├─ Installed from: https://download.pytorch.org/whl/cpu                   │
│  ├─ No CUDA dependencies                                                    │
│  └─ Windows/Linux/macOS compatible                                          │
│                                                                              │
│  SentenceTransformers                                                        │
│  ├─ Model: all-MiniLM-L6-v2                                                 │
│  ├─ Embedding dimension: 384                                                │
│  ├─ Device: CPU (explicitly set)                                            │
│  └─ Inference speed: ~100-200 emails/sec                                    │
│                                                                              │
│  Environment Variables:                                                      │
│  ├─ CUDA_VISIBLE_DEVICES=-1    (Disables GPU detection)                    │
│  ├─ FORCE_CPU=1                (Forces CPU mode)                            │
│  └─ Set at script startup before imports                                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

                              DATA FLOW DIAGRAM

┌─────────────┐
│    User     │
│   Browser   │
└──────┬──────┘
       │ 1. Search Query: "emails about invoices"
       │    GET request to Streamlit UI (8501)
       ▼
┌──────────────────┐
│  Streamlit UI    │
│  (Port 8501)     │
└──────┬───────────┘
       │ 2. API Call: GET /api/emails/search?q=emails about invoices&type=hybrid
       │    HTTP request to API Server
       ▼
┌──────────────────┐
│   API Server     │
│   (Port 3000)    │
└──────┬───────────┘
       │ 3. Invoke HybridSearch.search_detailed()
       │    Pass query and search parameters
       ▼
┌──────────────────┐
│  Hybrid Search   │
│    Service       │
└──────┬───────────┘
       │
       ├─────────────────────────────────────┐
       │ 4a. Semantic Search                 │ 4b. Keyword Search
       ▼                                     ▼
┌──────────────────┐              ┌──────────────────┐
│  VectorDB API    │              │  Elasticsearch   │
│  (Port 8001)     │              │   (Optional)     │
└──────┬───────────┘              └──────┬───────────┘
       │ 5a. Query ChromaDB               │ 5b. Query ES index
       │     with embeddings              │     with keywords
       ▼                                  ▼
┌──────────────────┐              ┌──────────────────┐
│  Vector Results  │              │ Keyword Results  │
│  [id, score]     │              │  [id, score]     │
└──────┬───────────┘              └──────┬───────────┘
       │                                 │
       └─────────────┬───────────────────┘
                     │ 6. Combine Results
                     │    • Normalize scores (0-1)
                     │    • Apply weights (70/30)
                     │    • Merge & deduplicate
                     │    • Sort by combined score
                     ▼
              ┌──────────────────┐
              │  Merged Results  │
              │  [id, combined]  │
              └──────┬───────────┘
                     │ 7. Return JSON response
                     ▼
              ┌──────────────────┐
              │   API Server     │
              │   (Port 3000)    │
              └──────┬───────────┘
                     │ 8. Format response
                     │    Add metadata
                     ▼
              ┌──────────────────┐
              │  Streamlit UI    │
              │  (Port 8501)     │
              └──────┬───────────┘
                     │ 9. Render results
                     │    Display email cards
                     ▼
              ┌──────────────────┐
              │      User        │
              │  Sees Results    │
              └──────────────────┘

═══════════════════════════════════════════════════════════════════════════════

                           DEPLOYMENT ARCHITECTURE

┌──────────────────────────────────────────────────────────────────────────────┐
│                       Windows PowerShell Terminals                           │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   Terminal 1    │  │   Terminal 2    │  │   Terminal 3    │            │
│  │                 │  │                 │  │                 │            │
│  │  python         │  │  python         │  │  python -m      │            │
│  │  vectordb_      │  │  api_server.py  │  │  streamlit run  │            │
│  │  service.py     │  │                 │  │  streamlit_     │            │
│  │                 │  │  Port: 3000     │  │  app.py         │            │
│  │  Port: 8001     │  │                 │  │                 │            │
│  │                 │  │  Status: ✅     │  │  Port: 8501     │            │
│  │  Status: ✅     │  │                 │  │                 │            │
│  │                 │  │                 │  │  Status: ✅     │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                              │
│  OR: Run startup script in one terminal:                                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PS C:\> .\start-all-services.ps1                                   │   │
│  │                                                                      │   │
│  │  ✅ Starting VectorDB Service (Port 8001)...                        │   │
│  │  ✅ Starting API Server (Port 3000)...                              │   │
│  │  ✅ Starting Streamlit UI (Port 8501)...                            │   │
│  │                                                                      │   │
│  │  All services started in separate windows!                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

                              PORT ALLOCATION

  Port 8001  →  VectorDB Service (FastAPI)
                • Semantic search engine
                • ChromaDB backend
                • Embedding generation
                • Health monitoring

  Port 3000  →  API Server (FastAPI)
                • Main REST API
                • Search orchestration
                • Email management
                • Swagger documentation

  Port 8501  →  Streamlit UI
                • Web interface
                • User interaction
                • Result visualization
                • Category filtering

═══════════════════════════════════════════════════════════════════════════════

                            TECHNOLOGY STACK

┌──────────────────────────────────────────────────────────────────────────────┐
│  Frontend:        Streamlit 1.28+                                            │
│                   • Python-based web framework                               │
│                   • Reactive UI components                                   │
│                   • Real-time updates                                        │
│                                                                              │
│  Backend:         FastAPI 0.104+                                             │
│                   • Async request handling                                   │
│                   • Auto-generated docs                                      │
│                   • Pydantic validation                                      │
│                                                                              │
│  Search:          ChromaDB + Elasticsearch                                   │
│                   • Vector similarity search                                 │
│                   • Full-text indexing                                       │
│                   • Hybrid result merging                                    │
│                                                                              │
│  ML/AI:           PyTorch 2.6.0+cpu                                          │
│                   SentenceTransformers                                       │
│                   • CPU-optimized inference                                  │
│                   • 384-dim embeddings                                       │
│                   • No GPU required                                          │
│                                                                              │
│  Language:        Python 3.8+                                                │
│                   TypeScript 4.9+ (for email sync)                           │
│                                                                              │
│  Platform:        Windows, macOS, Linux                                      │
│                   • Cross-platform compatible                                │
│                   • No special hardware requirements                         │
└──────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
```

## Key Architectural Decisions

### 1. **3-Tier Architecture**
- **Presentation:** Streamlit UI (user-facing)
- **Application:** FastAPI server (business logic)
- **Data:** VectorDB + Elasticsearch (storage & search)

**Why?** Separation of concerns, scalability, maintainability

### 2. **CPU-Only Optimization**
- PyTorch CPU build, no CUDA
- Environment variables force CPU mode
- Explicit device selection

**Why?** Wider accessibility, lower costs, no GPU required

### 3. **Hybrid Search**
- 70% semantic + 30% keyword weighting
- Score normalization before merging
- Fallback to VectorDB-only

**Why?** Best of both worlds, improved relevance

### 4. **Microservices Pattern**
- Each service runs independently
- Clear API boundaries
- Can scale services separately

**Why?** Flexibility, fault isolation, easier debugging

### 5. **FastAPI for All APIs**
- Async/await support
- Auto-generated OpenAPI docs
- Pydantic validation

**Why?** Modern, fast, well-documented, type-safe
