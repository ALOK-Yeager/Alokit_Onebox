# 📧 Onebox Aggregator - Setup & Run Guide

## ✅ Successfully Completed Setup

### 🔧 Environment Configuration

The application is now configured to run with **CPU-only PyTorch** to avoid CUDA-related errors.

#### Key Configuration Changes:
1. **PyTorch Version**: Downgraded to `2.6.0+cpu` (stable Windows CPU version)
2. **Environment Variables**: Set at the top of `vectordb_service.py`:
   ```python
   os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
   os.environ["FORCE_CPU"] = "1"
   os.environ["TOKENIZERS_PARALLELISM"] = "false"
   ```
3. **VectorDB Configuration**: Modified to explicitly use CPU device:
   ```python
   self._embedder = SentenceTransformer(self._embedding_model_name, device='cpu')
   ```

---

## 🚀 How to Run the Complete Application

### Prerequisites Check

Before running the application, ensure you have:
- ✅ Python 3.8+ installed
- ✅ PyTorch 2.6.0+cpu installed
- ✅ All Python dependencies installed (`pip install -r python-requirements.txt`)
- ✅ Node.js and npm installed (if using email sync)

---

## 🎯 Quick Start - All Services at Once

**Easiest way to start all services:**

```powershell
.\start-all-services.ps1
```

This PowerShell script will:
1. ✅ Check if Python is installed
2. ✅ Start VectorDB Service (Port 8001) in a new window
3. ✅ Start API Server (Port 3000) in a new window
4. ✅ Start Streamlit UI (Port 8501) in a new window
5. ✅ Display all access URLs

**Note:** If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then run the script again.

---

## 📋 Manual Start (Alternative)

---

### 1. Start the VectorDB Service (Semantic Search Backend)

**Terminal 1:**
```powershell
cd C:\Users\shash\Desktop\onebox_aggregator
python vectordb_service.py
```

**Expected Output:**
```
PyTorch is using: CPU
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Service Endpoints:**
- Health Check: `http://localhost:8001/health`
- API Docs: `http://localhost:8001/docs`
- Search: `GET http://localhost:8001/search?q=your_query`
- Add Email: `POST http://localhost:8001/add_email`

**Keep this terminal running!** ✅

---

### 2. Start the API Server (Main Backend API)

**Terminal 2:**
```powershell
cd C:\Users\shash\Desktop\onebox_aggregator
python api_server.py
```

**Expected Output:**
```
============================================================
🚀 Starting Onebox Aggregator API Server
============================================================
📍 API Base URL: http://localhost:3000
📚 API Documentation: http://localhost:3000/docs
🔍 Health Check: http://localhost:3000/health
============================================================

✅ HybridSearch service initialized successfully

INFO:     Uvicorn running on http://0.0.0.0:3000
```

**Service Endpoints:**
- API Root: `http://localhost:3000`
- Search: `GET http://localhost:3000/api/emails/search?q=query`
- Health: `GET http://localhost:3000/health`
- Docs: `http://localhost:3000/docs`

**Keep this terminal running!** ✅

**⚠️ CRITICAL:** This API server is **required** for Streamlit UI search functionality. If you skip this step, you'll get connection errors in the UI.

---

### 3. Start the Streamlit UI (Web Interface)

**Terminal 3:**
```powershell
cd C:\Users\shash\Desktop\onebox_aggregator
python -m streamlit run streamlit_app.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.1.5:8501
```

**Access the UI:**
- Open your browser and navigate to: **http://localhost:8501**

**Keep this terminal running!** ✅

---

### 4. (Optional) Start Email Sync Service

If you want to sync emails from IMAP:

**Terminal 4:**
```powershell
cd C:\Users\shash\Desktop\onebox_aggregator
npm run dev
```

This starts the Node.js backend for email synchronization.

---

## ✅ Verification & Testing

### Quick Health Checks (After Starting All Services)

**1. VectorDB Service (Port 8001):**
```powershell
curl http://localhost:8001/health
```
Expected: `{"status":"healthy","service":"vectordb","mode":"production"}`

**2. API Server (Port 3000):**
```powershell
curl http://localhost:3000/health
```
Expected: `{"status":"healthy","timestamp":"...","services":{...}}`

**3. Streamlit UI (Port 8501):**
- Open browser to `http://localhost:8501`
- You should see the Onebox Email Aggregator interface

---

### 🔍 Test Search Functionality

**Via API (Terminal):**
```powershell
curl "http://localhost:3000/api/emails/search?q=invoice&type=hybrid"
```

**Via UI (Browser):**
1. Go to `http://localhost:8501`
2. Ensure "API Mode (via Backend)" is selected
3. Enter a search query (e.g., "invoice", "meeting", "project")
4. Click "Search"
5. Results should appear (or "No emails found" if database is empty)

---

### 🧪 Unit Testing

**Test VectorDB Functionality:**
```powershell
python vectordb_service.py test
```

**Expected Output:**
```
🔍 Testing VectorDB functionality...
✓ VectorDB initialized successfully
✓ Added test email with ID: test_123
✓ Search completed successfully
✅ All tests passed! VectorDB is ready for integration.
```

**Test Hybrid Search Service:**
```powershell
python search_service.py
```

---

## ☁️ Using Elastic Cloud Instead of Local Elasticsearch

Prefer a managed cluster? Elastic Cloud works without code changes.

1. Install the official client (handy for the Python snippets below):
   ```powershell
   pip install elasticsearch
   ```
2. Connect with the API key from your Elastic dashboard. Example based on the credentials you shared:
   ```python
   from elasticsearch import Elasticsearch

   client = Elasticsearch(
       "https://009e4f399df8495e8d901e235391571e.us-central1.gcp.cloud.es.io:443",
       api_key="<paste-your-elastic-api-key>"
   )
   ```
3. (Optional) Create mappings or seed documents before wiring the app:
   ```python
   index_name = "onebox_elastic"
   mappings = {
       "properties": {
           "vector": {"type": "dense_vector", "dims": 3},
           "text": {"type": "text"}
       }
   }
   client.indices.put_mapping(index=index_name, body=mappings)
   ```
   ```python
   from elasticsearch import helpers

   docs = [
       {"vector": [0.5, 0.212, 0.291], "text": "Yellowstone National Park ..."},
       {"vector": [1.891, 2.821, 7.889], "text": "Yosemite National Park ..."},
       {"vector": [7.263, 0.142, 9.095], "text": "Rocky Mountain National Park ..."}
   ]
   helpers.bulk(client, docs, index=index_name)
   ```
4. Update your `.env` (or Render secrets) so every service hits the managed endpoint:
   ```dotenv
   ELASTICSEARCH_URL=https://009e4f399df8495e8d901e235391571e.us-central1.gcp.cloud.es.io:443
   ELASTICSEARCH_INDEX=onebox_elastic
   ELASTICSEARCH_API_KEY=<paste-your-elastic-api-key>
   ```
   Leave `ELASTICSEARCH_USERNAME` / `ELASTICSEARCH_PASSWORD` empty when using the API key.

Restart the backend processes after changing these variables; the dual-indexer and Python hybrid search will automatically pick up the new credentials.

---

### ⚠️ Troubleshooting Connection Issues

**If Streamlit shows "Connection Refused" error:**
- ❌ API server is not running on port 3000
- ✅ **Solution:** Make sure Terminal 2 is running `python api_server.py`

**If API returns empty results:**
- ℹ️ This is normal if you haven't indexed any emails yet
- ✅ Use VectorDB test mode: `python vectordb_service.py test`
- ✅ Or run the email sync service to import real emails

**If VectorDB search fails:**
- ❌ VectorDB service (port 8001) is not running
- ✅ **Solution:** Make sure Terminal 1 is running `python vectordb_service.py`

---

## 📁 Project Structure

```
onebox_aggregator/
├── vectordb_service.py          # VectorDB FastAPI service (Port 8001)
├── search_service.py             # Hybrid search combining VectorDB + Elasticsearch
├── streamlit_app.py              # Streamlit UI (Port 8501)
├── src/
│   └── Services/
│       └── search/
│           └── VectorDB.py      # Core VectorDB implementation
├── vector_store/                 # ChromaDB persistent storage
└── models/                       # ML models (email classifier)
```

---

## 🔍 Features Implemented

### 1. **VectorDB Service** (FastAPI)
- ✅ Semantic email search using SentenceTransformers
- ✅ Add single or batch emails
- ✅ Health monitoring and stats
- ✅ CPU-only operation (no GPU required)
- ✅ RESTful API with Swagger docs

### 2. **Hybrid Search Service**
- ✅ Combines VectorDB (semantic) + Elasticsearch (keyword)
- ✅ Weighted scoring (70% semantic, 30% keyword)
- ✅ Fallback to VectorDB-only if Elasticsearch unavailable
- ✅ Detailed search results with individual scores

### 3. **Streamlit UI**
- ✅ Modern, responsive design
- ✅ Two search modes:
  - **API Search**: Uses backend endpoints
  - **Direct Hybrid Search**: Uses local VectorDB
- ✅ Category filtering
- ✅ Natural language query support
- ✅ Email preview with expandable details

---

## 🛠️ Troubleshooting

### Issue: PyTorch CUDA DLL Error
**Solution:** ✅ **RESOLVED**
- Downgraded to PyTorch 2.6.0+cpu
- Set environment variables to force CPU mode
- Added helper function to disable CUDA detection

### Issue: ChromaDB Metadata Error
**Solution:** ✅ **RESOLVED**
- ChromaDB requires non-empty metadata dictionaries
- Updated test to include metadata: `{"subject": "...", "from": "..."}`

### Issue: Streamlit Command Not Found
**Solution:** ✅ **RESOLVED**
- Use `python -m streamlit run streamlit_app.py` instead of `streamlit run streamlit_app.py`

---

## 📊 API Usage Examples

### Add an Email
```python
import requests

response = requests.post(
    "http://localhost:8001/add_email",
    json={
        "id": "email_001",
        "content": "Meeting scheduled for tomorrow at 2 PM",
        "metadata": {
            "subject": "Team Meeting",
            "from": "manager@company.com",
            "category": "Interested"
        }
    }
)
print(response.json())
```

### Search Emails
```python
response = requests.get(
    "http://localhost:8001/search",
    params={"q": "meeting schedule", "n_results": 5}
)
results = response.json()["results"]
for email in results:
    print(f"{email['id']}: {email['metadata']['subject']}")
```

### Use Hybrid Search (Python)
```python
from search_service import HybridSearch

searcher = HybridSearch(vector_weight=0.7, keyword_weight=0.3)
results = searcher.search("project deadlines", n_results=10)
print(f"Found {len(results)} emails: {results}")
```

---

## 🌐 Accessing the Application

### Streamlit UI
**URL:** http://localhost:8501

**Features:**
- 🔍 Search your emails with natural language
- 📊 View search results with relevance scores
- 📧 Expandable email previews
- 🏷️ Category filtering
- 🎯 Two search modes (API vs Direct)

### VectorDB API
**URL:** http://localhost:8001

**Interactive Documentation:**
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## 📦 Dependencies

### Core Packages
```
torch==2.6.0+cpu
torchvision==0.21.0+cpu
torchaudio==2.6.0+cpu
sentence-transformers
fastapi<0.100
pydantic<2
uvicorn
chromadb
streamlit
```

### Installation Command
```powershell
pip install torch==2.6.0+cpu torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install fastapi<0.100 pydantic<2 uvicorn chromadb streamlit sentence-transformers
```

---

## ✨ Next Steps

1. **Add More Emails**: Use the API or UI to index your email database
2. **Connect Elasticsearch**: Set `ELASTICSEARCH_URL` environment variable for hybrid search
3. **Customize Search Weights**: Adjust `vector_weight` and `keyword_weight` in `HybridSearch`
4. **Deploy**: Use Docker or cloud platforms (Heroku, AWS, Azure)

---

## 🎉 Success!

Your Onebox Aggregator is now fully functional with:
- ✅ CPU-only PyTorch (no GPU required)
- ✅ VectorDB semantic search
- ✅ Hybrid search capabilities
- ✅ Modern Streamlit UI
- ✅ RESTful API with documentation

**Enjoy your email aggregator!** 📧🚀
