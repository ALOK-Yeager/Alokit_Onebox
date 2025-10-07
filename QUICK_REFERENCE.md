# 🚀 Onebox Aggregator - Quick Reference

## ⚡ Quick Start
```powershell
# Start all services
.\start-all-services.ps1

# Verify everything is working
.\verify-system.ps1
```

## 🌐 Access URLs
| Service | URL | Description |
|---------|-----|-------------|
| 🎨 **Streamlit UI** | http://localhost:8501 | Main interface |
| 🔌 **API Server** | http://localhost:3000 | Backend API |
| 📚 **API Docs** | http://localhost:3000/docs | Swagger docs |
| 🔍 **VectorDB** | http://localhost:8001 | Search service |
| 📖 **VectorDB Docs** | http://localhost:8001/docs | VectorDB API |

## 🛠️ Manual Commands

### Start Services (Separate Terminals)
```powershell
# Terminal 1: VectorDB Service
python vectordb_service.py

# Terminal 2: API Server
python api_server.py

# Terminal 3: Streamlit UI
python -m streamlit run streamlit_app.py
```

### Test VectorDB
```powershell
python vectordb_service.py test
```

### Test Hybrid Search
```powershell
python search_service.py
```

## 🧪 Quick Health Checks
```powershell
# Check VectorDB (Port 8001)
curl http://localhost:8001/health

# Check API Server (Port 3000)
curl http://localhost:3000/health

# Check Streamlit UI (Port 8501)
# Open in browser: http://localhost:8501
```

## 🔍 API Examples

### Search Emails (Hybrid)
```powershell
curl "http://localhost:3000/api/emails/search?q=invoice&type=hybrid"
```

### Search Emails (Semantic Only)
```powershell
curl "http://localhost:3000/api/emails/search?q=meeting&type=vector"
```

### Search Emails (Keyword Only)
```powershell
curl "http://localhost:3000/api/emails/search?q=urgent&type=keyword"
```

### Get System Stats
```powershell
curl http://localhost:3000/api/stats
```

### Get VectorDB Stats
```powershell
curl http://localhost:8001/stats
```

## ⚠️ Common Issues

### "Connection Refused" Error
❌ **Problem:** API server not running
✅ **Solution:** Start `python api_server.py` in Terminal 2

### "Streamlit command not found"
❌ **Problem:** Streamlit not in PATH
✅ **Solution:** Use `python -m streamlit run streamlit_app.py`

### CUDA/PyTorch Errors
❌ **Problem:** Wrong PyTorch version
✅ **Solution:** Reinstall CPU-only version:
```powershell
pip uninstall torch torchvision torchaudio
pip install torch==2.6.0+cpu torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Empty Search Results
ℹ️ **Note:** Normal if no emails indexed yet
✅ **Solution:** Run test mode: `python vectordb_service.py test`

## 📁 Key Files

| File | Purpose |
|------|---------|
| `api_server.py` | Main API server (Port 3000) |
| `vectordb_service.py` | VectorDB service (Port 8001) |
| `streamlit_app.py` | Web UI (Port 8501) |
| `search_service.py` | Hybrid search logic |
| `start-all-services.ps1` | Startup automation |
| `README.md` | Full documentation |
| `SETUP_GUIDE.md` | Setup instructions |

## 🎯 Search Tips

### In Streamlit UI
1. Select "API Mode (via Backend)" for full functionality
2. Choose "All Categories" or specific category
3. Enter natural language query
4. Click "Search"

### Query Examples
- **Semantic:** "emails about project deadlines"
- **Keyword:** "invoice payment urgent"
- **Mixed:** "meeting with John about budget"

## 🔧 Configuration

### Environment Variables (Optional)
Create `.env` file:
```bash
# Python/ML
FORCE_CPU=1
CUDA_VISIBLE_DEVICES=-1

# VectorDB
VECTORDB_PORT=8001
VECTORDB_COLLECTION=emails

# API Server
API_PORT=3000

# Streamlit
STREAMLIT_PORT=8501
```

## 💡 Pro Tips

1. **Use Startup Script:** Easiest way to run everything
2. **Keep Terminals Open:** Each service needs its own window
3. **Check Health First:** Always verify services are healthy
4. **Use API Docs:** Swagger UI has interactive testing
5. **Test Mode:** Use `python vectordb_service.py test` to add sample data

## 📊 System Requirements

- ✅ Python 3.8+
- ✅ PyTorch 2.6.0+cpu
- ✅ ~1GB RAM (VectorDB)
- ✅ ~2GB Disk (with embeddings)
- ❌ No GPU required!

## 🆘 Need Help?

1. Check `README.md` for full documentation
2. Check `SETUP_GUIDE.md` for detailed steps
3. Check `SYSTEM_OVERVIEW.md` for architecture
4. Check service logs in terminal windows

## 📝 Quick Debugging

### Service Won't Start
```powershell
# Check if port already in use
netstat -ano | findstr :8001  # VectorDB
netstat -ano | findstr :3000  # API Server
netstat -ano | findstr :8501  # Streamlit

# Kill process if needed
taskkill /PID <PID> /F
```

### Dependencies Issue
```powershell
# Reinstall all dependencies
pip install -r python-requirements.txt --force-reinstall
```

### Python Environment
```powershell
# Check Python version
python --version  # Should be 3.8+

# Check PyTorch
python -c "import torch; print(torch.__version__)"  # Should be 2.6.0+cpu

# Check if CUDA available (should be False)
python -c "import torch; print(torch.cuda.is_available())"
```

---

**🎉 Happy Searching! 🎉**
