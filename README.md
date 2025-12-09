# Alokit_Onebox: Real-Time Email Synchronization Service


---

## ALL FUNCTIONAL REQUIREMENTS 

**📊 Implementation Progress:**
- ✅ **FR-1**: Real-Time Email Synchronization -
- ✅ **FR-2**: Searchable Storage with Elasticsearch - 
- ✅ **FR-3**: AI-Based Email Categorization - 
- ✅ **FR-4**: Dual-Indexing Service (Elasticsearch + VectorDB) - 
- ✅ **FR-5**:Hybrid Search (Semantic + Keyword) - 
- ✅ **FR-6**: React based frontend - 

**💻 Development Environment:**
- **Hardware**: Developed and optimized for **CPU-only systems**
- **No GPU Required**: All ML/AI operations run efficiently on CPU
- **PyTorch Version**: 2.6.0+cpu (stable Windows CPU build)
- **Cross-Platform**: Works on Windows, macOS, and Linux

---

## 📚 Documentation Quick Links

| Document | Description | When to Use |
|----------|-------------|-------------|
| 📖 **[README.md](README.md)** | Complete project documentation | First-time setup and overview |
| 🚀 **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Commands and URLs cheat sheet | 
| 🛠️ **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | Detailed setup instructions | Installation and configuration |
| 🔧 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Problem-solving guide | 
| 🏗️ **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** | Visual system architecture | Understanding data flow |
| 📊 **[SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)** | Architecture and achievements | Understanding the system |
| ✅ **[PROJECT_COMPLETION.md](PROJECT_COMPLETION.md)** | FR completion status | Progress tracking |
| 📝 **[SESSION_SUMMARY.md](SESSION_SUMMARY.md)** | Latest changes and fixes | Recent updates |

**💡 Pro Tips:** 
- Keep **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** open for easy access to commands and URLs!
- Check **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** first when encountering errors!
- Review **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** to understand system components and data flow!

---

## Overview

This project is a comprehensive backend service with a modern UI, designed to provide real-time, two-way synchronization with email accounts using the IMAP protocol. It features AI-powered email classification, semantic search capabilities, and hybrid search combining keyword and semantic search. The entire system is optimized to run on CPU-only hardware, making it accessible without expensive GPU infrastructure.

---

## FR-1: Real-Time Email Synchronization

This is the core feature of the application, enabling seamless integration with any IMAP-based email server like Gmail.

### Key Features

-   **Secure IMAP Connection**: Establishes a secure and stable connection to the user's email server using `node-imap`.
-   **Historical Email Sync**: On initial startup, the service fetches all emails from the last 30 days to build a complete inbox view.
-   **Real-Time Email Detection**: Utilizes the **IMAP IDLE** command to listen for new emails in real-time, ensuring the application is updated within seconds of an email's arrival.
-   **Robust Error Handling & Reconnection**: Includes an automatic reconnection manager that attempts to re-establish a connection in case of network failures or timeouts, ensuring high availability.
-   **Safe Configuration**: Manages sensitive credentials securely using a `.env` file, which is excluded from version control via `.gitignore`.

### Architecture & Data Flow

The following diagram illustrates the flow of data from the IMAP server to the service.

```mermaid
graph TD
    subgraph "Email Provider"
        A[IMAP Server e.g., Gmail]
    end

    subgraph "Onebox Aggregator Service"
        B[IMAP Service]
        C[Sync Manager]
        D[Idle Manager]
        E[Logger]
    end

    subgraph "Future Implementation"
        F[Elasticsearch]
    end

    A -- "Establishes Connection" --> B;
    B -- "Opens Mailbox" --> A;
    B -- "Initiates Historical Sync" --> C;
    C -- "Fetches Last 30 Days of Emails" --> A;
    C -- "Parses and Logs Emails" --> E;
    B -- "Enters IDLE Mode" --> D;
    D -- "Listens for New Mail Events" --> A;
    A -- "Pushes New Email Notification" --> D;
    D -- "Triggers New Email Fetch" --> C;

    
```

---

## Tech Stack

### Backend Services
-   **Primary Backend**: Node.js with TypeScript
-   **AI/ML Services**: Python (FastAPI)
-   **IMAP Communication**: `node-imap`
-   **Environment Management**: `dotenv`
-   **Logging**: `winston`
-   **Development**: `nodemon`, `ts-node`

### Search & Storage
-   **Keyword Search**: Elasticsearch
-   **Semantic Search**: ChromaDB (Vector Database)
-   **Embeddings**: SentenceTransformers (`all-MiniLM-L6-v2`)

### AI & Machine Learning
-   **Framework**: PyTorch 2.6.0+cpu (CPU-optimized)
-   **Email Classification**: Fine-tuned Transformer model (ONNX format)
-   **Semantic Search**: Sentence-BERT embeddings
-   **Deployment**: FastAPI microservice

### User Interface
-   **Frontend**: Streamlit
-   **API Documentation**: Swagger/OpenAPI (FastAPI)
-   **Styling**: Custom CSS with responsive design

### Integrations
-   **Notifications**: Slack API, Webhooks
-   **Version Control**: Git with Git LFS (for model files)

---

## 🚀 Quick Start Guide

Get the complete email aggregator running in 3 easy steps!

### Prerequisites

-   Node.js (v18 or higher)
-   Python 3.8+ (for AI and semantic search features)
-   Elasticsearch (optional, for hybrid search)
-   npm and pip

### Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/ALOK-Yeager/Alokit_Onebox.git
cd onebox_aggregator

# Install Node.js dependencies
npm install

# Install Python dependencies (CPU-optimized)
pip install torch==2.6.0+cpu torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r python-requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# - IMAP settings (Gmail, Outlook, etc.)
# - Elasticsearch URL (optional)
# - Slack token (optional)
# - Webhook URL (optional)
# - Set ENABLE_VECTORDB=false to run in keyword-only mode when vector dependencies are unavailable
```

### Step 3: Run the Application

#### 🚀 Option A: Quick Start (Recommended for First Time)

**Run all services at once using the startup script:**

```powershell
.\start-all-services.ps1
```

This PowerShell script automatically starts all 3 required services in separate windows:
- ✅ VectorDB Service (Port 8001)
- ✅ API Server (Port 3000)
- ✅ Streamlit UI (Port 8501)

**Note:** If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

#### 📋 Option B: Manual Start (For Development/Debugging)

**Important:** You need to run 3 separate services for full functionality:

```bash
# Terminal 1: Start VectorDB Service (Semantic Search Backend)
python vectordb_service.py

# Terminal 2: Start API Server (Search & Email Management)
python api_server.py

# Terminal 3: Start Streamlit UI (Web Interface)
python -m streamlit run streamlit_app.py

# Optional Terminal 4: Start Node.js Backend (Email Sync - if needed)
npm run dev
```

---

#### ✅ Step 4: Verify System (Optional but Recommended)

**Run the verification script to ensure all services are working:**

```powershell
.\verify-system.ps1
```

This will:
- ✅ Test all service health endpoints
- ✅ Verify API connectivity
- ✅ Check search functionality
- ✅ Display comprehensive test results

**Expected Output:**
```
🎉 ALL TESTS PASSED! System is fully operational! 🎉

🌐 Access Points:
   • Streamlit UI:    http://localhost:8501
   • API Server:      http://localhost:3000
   • API Docs:        http://localhost:3000/docs
   • VectorDB API:    http://localhost:8001
```

---

**Access Points:**
- 🌐 **Streamlit UI**: http://localhost:8501 (Main User Interface)
- 📚 **API Server**: http://localhost:3000 (Search API)
- 📖 **API Documentation**: http://localhost:3000/docs (Interactive API docs)
- � **VectorDB API**: http://localhost:8001/docs (Vector search backend)

**⚠️ Critical Note:** The API server (port 3000) **must be running** for the Streamlit UI search functionality to work. If you see connection errors in Streamlit, make sure the API server is running.

---

## Setup and Installation

For detailed setup instructions, follow these steps:

### Prerequisites

-   Node.js (v18 or higher)
-   Python 3.8 or higher
-   npm and pip

### 1. Clone the Repository

```bash
git clone https://github.com/ALOK-Yeager/Alokit_Onebox.git
cd onebox_aggregator
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment Variables

Create a `.env` file in the root of the project by copying the example file:

```bash
# For Windows (Command Prompt)
copy .env.example .env

# For Windows (PowerShell)
cp .env.example .env

# For macOS/Linux
cp .env.example .env
```

Now, open the `.env` file and fill in your IMAP server details.

```properties
# Your email provider's IMAP server (e.g., imap.gmail.com)
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993

# Your email address and password
# IMPORTANT: For Gmail, you must generate an "App Password".
# See: https://support.google.com/accounts/answer/185833
IMAP_USER=your-email@example.com
IMAP_PASSWORD=your-app-password

# Enable TLS (recommended)
IMAP_TLS=true
```

---

## FR-4: Notification System

This feature enhances the email processing pipeline by adding real-time notifications for important emails, particularly focusing on high-intent leads identified by our AI classification system.

### Key Features

#### Slack Integration
- Real-time notifications for high-intent leads (confidence > 70%)
- Rich message formatting with email details and AI confidence scores
- Optional integration enabled via environment variables
- Automatic error handling and retry logic

#### Webhook Integration
- HTTP webhooks for system integration
- Detailed JSON payload with email metadata and AI classification results
- Performance metrics included (classification latency)
- Configurable endpoints and authentication

### Example Webhook Payload
```json
{
    "category": "Interested",
    "emailId": "email_123",
    "confidence": 0.92,
    "metadata": {
        "subject": "Looking to discuss project",
        "from": "client@company.com",
        "timestamp": "2025-08-04T15:30:00Z",
        "classificationLatencyMs": 245
    }
}
```

### Configuration

Add the following to your `.env` file to enable notifications:

```bash
# Slack Integration
SLACK_API_TOKEN=xoxb-your-bot-token

# Webhook Integration
WEBHOOK_URL=https://your-webhook-endpoint.com/hook
```

## Running the Application

### Development Mode
```bash
npm run dev
```

### Build for Production
```bash
npm run build
```

The compiled output will be in the `dist/` directory.

### Running in Production
After building the project, you can run the compiled code directly with Node.js:

```bash
node dist/main.js
```

---

## FR-2: Searchable Storage with Elasticsearch

### Prerequisites for Elasticsearch Testing

1. **Elasticsearch Server**: Make sure Elasticsearch is running on your system.

```bash
# Using Docker (recommended)
docker run -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.11.0

# Or install locally and start the service
```

2. **Environment Setup**: Add Elasticsearch configuration to your `.env` file:

```bash
# Elasticsearch configuration
ELASTICSEARCH_NODE=http://localhost:9200
```

### Running Tests

#### 1. Check Setup
First, verify that all dependencies and Elasticsearch are properly configured:

```bash
npm run check-setup
```

This command will:
- ✅ Verify all required packages are installed
- 🔌 Test Elasticsearch connection
- 📝 Provide next steps based on the results

#### 2. Test Elasticsearch Integration
Run the comprehensive Elasticsearch test suite:

```bash
npm run test:elasticsearch
```

This test will:
- Initialize the Elasticsearch service
- Create a test email entry
- Index the email in Elasticsearch
- Test search functionality with various queries
- Verify filtered search capabilities

#### 3. Test API Endpoints
Test the Express.js API routes for email search:

```bash
npm run test:api
```

Then open your browser or use curl to test the API:

```bash
# Test search endpoint
curl "http://localhost:3001/api/emails/search?q=test&from=0&size=10"
```

### Expected Results

When tests pass successfully, you should see:
- ✅ Elasticsearch connection established
- ✅ Email indexing working
- ✅ Search queries returning results
- ✅ API endpoints responding correctly

### Troubleshooting

**Connection Failed**: 
- Ensure Elasticsearch is running on the specified port
- Check firewall settings
- Verify ELASTICSEARCH_NODE environment variable

**No Search Results**:
- Wait a few seconds for indexing to complete
- Check if test emails were properly indexed
- Verify index mapping in Elasticsearch

**API Errors**:
- Check server logs for detailed error messages
- Ensure all TypeScript files compile without errors
- Verify all required dependencies are installed

---

## FR-5: Dual-Indexing Service (Elasticsearch + VectorDB)

This advanced feature implements a dual-indexing pipeline that stores emails in both Elasticsearch (for keyword search) and ChromaDB (for semantic search), providing the foundation for hybrid search capabilities.

### Key Features

✅ **Dual-Index Architecture**: Simultaneously indexes emails in Elasticsearch and VectorDB  
✅ **Transaction Safety**: Rollback mechanisms for failed operations  
✅ **Batch Processing**: Efficient bulk indexing with progress tracking  
✅ **Error Recovery**: Comprehensive error handling and retry logic  
✅ **Monitoring**: Health checks and statistics endpoints  

### Architecture

```mermaid
graph LR
    A[New Email] --> B[DualIndexingAdapter]
    B --> C[Elasticsearch Service]
    B --> D[VectorDB Service]
    C --> E[Keyword Index]
    D --> F[Semantic Vector Store]
    E --> G[Hybrid Search]
    F --> G
```

### Running the Dual-Indexing Service

The system uses a FastAPI-based VectorDB service that runs alongside your Node.js backend:

```bash
# Terminal 1: Start VectorDB Service
python vectordb_service.py

# Terminal 2: Start Node.js Backend
npm run dev

# Terminal 3: Start Streamlit UI (optional)
python -m streamlit run streamlit_app.py
```

### Testing Dual-Indexing

```bash
# Test VectorDB functionality
python vectordb_service.py test

# Test hybrid search service
python search_service.py
```

---

## FR-6: Hybrid Search System

Combines the best of both worlds: keyword-based search (Elasticsearch) and semantic search (VectorDB) to provide highly relevant search results.

### Features

✅ **Weighted Scoring**: 70% semantic, 30% keyword (configurable)  
✅ **Fallback Mode**: Works with VectorDB-only if Elasticsearch unavailable  
✅ **Natural Language Queries**: Understand intent, not just keywords  
✅ **Detailed Results**: Individual scores for semantic and keyword matches  

### Usage Example

```python
from search_service import HybridSearch

# Initialize hybrid search
searcher = HybridSearch(vector_weight=0.7, keyword_weight=0.3)

# Search with natural language
results = searcher.search("emails about project deadlines", n_results=10)

# Get detailed results with scores
detailed = searcher.search_detailed("meeting schedule", n_results=5)
for result in detailed:
    print(f"Email: {result['email_id']}")
    print(f"  Semantic Score: {result['vector_score']:.2f}")
    print(f"  Keyword Score: {result['keyword_score']:.2f}")
    print(f"  Combined Score: {result['combined_score']:.2f}")
```

---

## FR-7: Streamlit UI

A modern, responsive web interface for searching and viewing emails with hybrid search capabilities.

### Features

✅ **Two Search Modes**: API-based and Direct Hybrid Search  
✅ **Category Filtering**: Filter by AI-classified categories  
✅ **Natural Language Input**: Type queries as you would ask a person  
✅ **Expandable Previews**: View email content without leaving the search page  
✅ **Responsive Design**: Works on desktop, tablet, and mobile  

### Accessing the UI

```bash
# Start the Streamlit app
python -m streamlit run streamlit_app.py

# Access in browser
# Local: http://localhost:8501
# Network: http://YOUR_IP:8501
```

### UI Features

- **Search Bar**: Natural language query input
- **Filter Options**: Category-based filtering
- **Result Cards**: Clean, organized email previews
- **Relevance Indicators**: Visual feedback on match quality
- **Expandable Content**: View full email details inline

---

## 💻 CPU-Optimized Development

This project is specifically optimized to run on **CPU-only hardware**, making it accessible without requiring expensive GPU infrastructure.

### Why CPU-Only?

- **Accessibility**: Works on any modern laptop or desktop
- **Cost-Effective**: No need for GPU cloud instances
- **Energy Efficient**: Lower power consumption
- **Easier Development**: Simpler setup without CUDA dependencies

### Optimizations Implemented

1. **PyTorch CPU Build**: Uses `torch 2.6.0+cpu` (stable Windows CPU version)
2. **Environment Configuration**: Forces CPU mode to avoid CUDA errors:
   ```python
   os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
   os.environ["FORCE_CPU"] = "1"
   os.environ["TOKENIZERS_PARALLELISM"] = "false"
   ```
3. **Model Selection**: Uses efficient models optimized for CPU inference
4. **Batch Processing**: Optimized batch sizes for CPU throughput

### Performance on CPU

- **Email Classification**: ~100-500ms per email
- **Vector Embeddings**: ~50-200ms per email
- **Semantic Search**: ~100-300ms for 1000 emails
- **Memory Usage**: ~1-2GB RAM (typical)

### Installation for CPU

```bash
# Install CPU-optimized PyTorch
pip install torch==2.6.0+cpu torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
pip install -r python-requirements.txt
```

---

## FR-3: AI-Based Email Categorization

The application includes an AI-powered email classification system using a fine-tuned transformer model that automatically categorizes incoming emails into predefined categories.

### Supported Categories

The AI classifier can identify the following email types:
- **Interested**: Emails expressing interest in meetings, collaborations, or opportunities
- **Meeting Booked**: Confirmations and calendar invites for scheduled meetings
- **Not Interested**: Polite rejections or expressions of disinterest
- **Spam**: Unsolicited promotional emails and potential scams
- **Out of Office**: Automated out-of-office replies

### AI Integration Features

✅ **Real-time Classification**: Every incoming email is automatically classified during IMAP sync  
✅ **Confidence Scoring**: Each classification includes a confidence percentage  
✅ **Elasticsearch Integration**: Classifications are stored and searchable  
✅ **Fallback Handling**: Graceful degradation when AI service is unavailable  
✅ **API Endpoint**: Manual classification via REST API  

### Prerequisites for AI Classification

1. **Python Environment**: Python 3.8+ with required packages
   ```bash
   # Install Python dependencies
   pip install -r python-requirements.txt
   ```

2. **Model Files**: Your fine-tuned model should be in the `models/email_classifier/` directory
   ```
   models/
   └── email_classifier/
       ├── config.json
       ├── pytorch_model.bin
       ├── tokenizer_config.json
       ├── tokenizer.json
       └── vocab.txt
   ```

### Testing AI Classification

#### 1. Test the AI Service
Run the comprehensive AI classification test:

```bash
npm run test:ai
```

This test will:
- ✅ Verify the AI service is available
- 🧪 Test classification with sample emails
- 📊 Report accuracy and performance
- 💡 Provide troubleshooting guidance

#### 2. Test via API
Test the classification endpoint manually:

```bash
# Classify email text
curl -X POST http://localhost:3000/api/emails/classify \
  -H "Content-Type: application/json" \
  -d '{"text":"Meeting invitation for next week. Are you available Tuesday?"}'
```

#### 3. Search by Category
Search emails by AI-assigned categories:

```bash
# Find all "Interested" emails
curl "http://localhost:3000/api/emails/search?category=Interested"

# Find all "Meeting Booked" emails
curl "http://localhost:3000/api/emails/search?category=Meeting%20Booked"
```

### Integration Workflow

The AI classification is seamlessly integrated into the email processing pipeline:

```mermaid
graph TD
    A[New Email Received] --> B[IMAP Service]
    B --> C[Email Parser]
    C --> D[AI Classification Service]
    D --> E[Add Category & Confidence]
    E --> F[Index in Elasticsearch]
    F --> G[Available for Search]
    
    D --> H{AI Service Available?}
    H -->|Yes| I[Fine-tuned Model Classification]
    H -->|No| J[Set as 'Unclassified']
    I --> E
    J --> E
```

### Configuration

The AI service automatically:
- Checks for Python and required packages on startup
- Loads your fine-tuned model from the models directory
- Gracefully handles errors and missing dependencies
- Provides detailed logging for troubleshooting

### Performance

- **Classification Speed**: ~100-500ms per email (depending on hardware)
- **Accuracy**: Typically 85-95% with well-trained models
- **Memory Usage**: ~500MB-2GB (depending on model size)
- **CPU Usage**: Moderate during classification, idle otherwise

### Git LFS Setup

This project uses Git Large File Storage (LFS) for managing the AI model files which can be several hundred megabytes. To work with the repository:

1. **Install Git LFS**:
   ```bash
   # Download from https://git-lfs.github.com/ and install, then:
   git lfs install
   ```

2. **LFS is already configured** for the following file patterns in `.gitattributes`:
   ```
   models/email_classifier/** filter=lfs diff=lfs merge=lfs -text
   *.onnx filter=lfs diff=lfs merge=lfs -text
   *.bin filter=lfs diff=lfs merge=lfs -text
   ```

3. **Clone the repository** with LFS:
   ```bash
   git lfs clone https://github.com/ALOK-Yeager/Alokit_Onebox.git
   ```

4. **Verify LFS files**:
   ```bash
   git lfs ls-files
   ```

Note: The model files are tracked by Git LFS and will be downloaded automatically when you clone or pull the repository.

### Troubleshooting

**Service Unavailable**:
- Ensure Python is installed and in PATH
- Install dependencies: `pip install -r python-requirements.txt`
- Verify model files are in `models/email_classifier/`

**Low Accuracy**:
- Check if the model was trained on similar email types
- Consider retraining with more diverse data
- Verify model files are complete and not corrupted

**Performance Issues**:
- ✅ System is already CPU-optimized (no GPU required)
- Reduce model size or use quantization for older CPUs
- Implement batching for high-volume scenarios
- Consider increasing batch size in VectorDB settings

**PyTorch CUDA Errors** (Common on Windows):
- ✅ **RESOLVED**: Use CPU-only PyTorch build
- Install with: `pip install torch==2.6.0+cpu --index-url https://download.pytorch.org/whl/cpu`
- Environment variables are pre-configured in `vectordb_service.py`
- System automatically forces CPU mode at startup

---

## 📋 Complete Feature List

### Core Email Management
- ✅ Real-time IMAP synchronization with IDLE support
- ✅ Historical email fetching (last 30 days)
- ✅ Automatic reconnection and error recovery
- ✅ Secure credential management

### Search Capabilities
- ✅ **Keyword Search**: Fast Elasticsearch-based text search
- ✅ **Semantic Search**: AI-powered meaning-based search
- ✅ **Hybrid Search**: Combined keyword + semantic (70/30 weighted)
- ✅ **Natural Language Queries**: Search as you speak
- ✅ **Category Filtering**: Filter by AI-classified categories

### AI & Machine Learning
- ✅ Automatic email classification (5 categories)
- ✅ Confidence scoring for classifications
- ✅ CPU-optimized inference (no GPU required)
- ✅ Fine-tuned transformer models
- ✅ Semantic embeddings for vector search

### Data Storage
- ✅ Dual-indexing (Elasticsearch + VectorDB)
- ✅ Transaction safety and rollback
- ✅ Batch processing for efficiency
- ✅ Persistent vector storage (ChromaDB)

### Integrations & APIs
- ✅ RESTful APIs with OpenAPI/Swagger docs
- ✅ Slack notifications for high-intent leads
- ✅ Webhook support for custom integrations
- ✅ Real-time notification system

### User Interface
- ✅ Modern Streamlit web UI
- ✅ Responsive design (mobile-friendly)
- ✅ Two search modes (API and Direct)
- ✅ Expandable email previews
- ✅ Visual relevance indicators

### Developer Experience
- ✅ Comprehensive TypeScript types
- ✅ Detailed logging with Winston
- ✅ Hot reload in development
- ✅ Git LFS for model management
- ✅ Complete test suites
- ✅ API documentation and examples

---

## 🔧 Environment Variables Reference

Create a `.env` file with the following variables:

```bash
# IMAP Configuration (Required)
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USER=your-email@example.com
IMAP_PASSWORD=your-app-password
IMAP_TLS=true

# Elasticsearch (Optional - for hybrid search)
ELASTICSEARCH_NODE=http://localhost:9200

# Slack Integration (Optional)
SLACK_API_TOKEN=xoxb-your-bot-token

# Webhook Integration (Optional)
WEBHOOK_URL=https://your-webhook-endpoint.com/hook

# VectorDB Service (Auto-configured)
VECTORDB_PATH=./vector_store
VECTORDB_PORT=8001

# Python/ML Environment (Auto-configured)
TF_CPP_MIN_LOG_LEVEL=3
TF_ENABLE_ONEDNN_OPTS=0
CUDA_VISIBLE_DEVICES=-1
FORCE_CPU=1
```

---

## 📊 System Architecture

### Complete Data Flow

```mermaid
graph TD
    subgraph "Email Providers"
        A[IMAP Server]
    end
    
    subgraph "Onebox Aggregator Core"
        B[IMAP Service]
        C[Email Parser]
        D[AI Classification]
        E[Dual Indexing]
    end
    
    subgraph "Storage Layer"
        F[Elasticsearch<br/>Keyword Search]
        G[ChromaDB<br/>Vector Store]
    end
    
    subgraph "Search Services"
        H[Hybrid Search<br/>70% Semantic + 30% Keyword]
    end
    
    subgraph "User Interfaces"
        I[Streamlit UI]
        J[REST API]
    end
    
    subgraph "Integrations"
        K[Slack Notifications]
        L[Webhooks]
    end
    
    A -->|Sync Emails| B
    B --> C
    C --> D
    D -->|Classify| E
    E --> F
    E --> G
    F --> H
    G --> H
    H --> I
    H --> J
    D -->|High Intent| K
    D -->|Events| L
```

---

## 📖 API Documentation

### VectorDB Service Endpoints

**Base URL**: `http://localhost:8001`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/stats` | GET | Vector store statistics |
| `/add_email` | POST | Add single email |
| `/add_emails` | POST | Batch add emails |
| `/search` | GET | Semantic search |
| `/docs` | GET | Interactive API docs |

### Node.js Backend Endpoints

**Base URL**: `http://localhost:3000`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/emails/search` | GET | Hybrid email search |
| `/api/emails/classify` | POST | Classify email text |
| `/api/emails/:id` | GET | Get email by ID |

### Example Requests

```bash
# Semantic search
curl "http://localhost:8001/search?q=project%20updates&n_results=5"

# Hybrid search
curl "http://localhost:3000/api/emails/search?q=meeting&category=Interested"

# Classify email
curl -X POST http://localhost:3000/api/emails/classify \
  -H "Content-Type: application/json" \
  -d '{"text":"I would like to schedule a meeting next week"}'
```

---

## 🧪 Testing Guide

### Test VectorDB Service

```bash
# Run VectorDB tests
python vectordb_service.py test
```

**Expected Output:**
```
✓ VectorDB initialized successfully
✓ Added test email with ID: test_123
✓ Search completed successfully
✅ All tests passed! VectorDB is ready for integration.
```

### Test Hybrid Search

```bash
# Run hybrid search tests
python search_service.py
```

### Test Node.js Backend

```bash
# Check setup
npm run check-setup

# Test Elasticsearch
npm run test:elasticsearch

# Test AI classification
npm run test:ai

# Test API endpoints
npm run test:api
```

---

## 📚 Documentation Files

- **SETUP_GUIDE.md**: Detailed setup and troubleshooting guide
- **architecture.md**: System architecture and design decisions
- **README.md**: This file - complete project documentation
- **.env.example**: Environment variable template

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👨‍💻 Author

**Alokit Mishra **  

- GitHub: [@ALOK-Yeager](https://github.com/ALOK-Yeager)

---

## 🙏 Acknowledgments

- **ReachInbox** for the opportunity and requirements
- **OpenAI** for language model technologies
- **Hugging Face** for transformer models and tools
- **Elasticsearch** for powerful search capabilities
- **ChromaDB** for vector database functionality
- **Streamlit** for rapid UI development

---

## 📞 Support

For issues, questions, or suggestions:
1. Check the **SETUP_GUIDE.md** for detailed troubleshooting
2. Review existing GitHub Issues
3. Create a new Issue with detailed information
4. Contact via GitHub discussions

---

**⭐ If you find this project helpful, please consider giving it a star on GitHub!**

---
