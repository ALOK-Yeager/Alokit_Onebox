# 🔧 Troubleshooting Guide

**Quick Navigation:**
- [Common Issues](#common-issues)
- [Service-Specific Problems](#service-specific-problems)
- [Connection Errors](#connection-errors)
- [Performance Issues](#performance-issues)
- [Installation Problems](#installation-problems)
- [Debug Mode](#debug-mode)

---

## Common Issues

### ❌ "Connection Refused" Error

**Symptom:**
```
HTTPConnectionPool(host='localhost', port=3000): Max retries exceeded
ConnectionRefusedError: [WinError 10061] No connection could be made
```

**Cause:** API server is not running on port 3000

**Solution:**
```powershell
# Option 1: Use the startup script
.\start-all-services.ps1

# Option 2: Start API server manually
python api_server.py
```

**Verification:**
```powershell
curl http://localhost:3000/health
# Should return: {"status":"healthy",...}
```

---

### ❌ "Module Not Found" Error

**Symptom:**
```
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'chromadb'
```

**Cause:** Python dependencies not installed

**Solution:**
```powershell
# Install all dependencies
pip install -r python-requirements.txt

# Verify installation
pip list | Select-String "fastapi|chromadb|streamlit"
```

---

### ❌ CUDA/PyTorch DLL Error

**Symptom:**
```
OSError: [WinError 126] The specified module could not be found
Error loading "...\torch\lib\torch_cuda.dll"
```

**Cause:** Wrong PyTorch version (trying to load CUDA on CPU-only system)

**Solution:**
```powershell
# Uninstall current PyTorch
pip uninstall torch torchvision torchaudio -y

# Install CPU-only version
pip install torch==2.6.0+cpu torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Verify
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}')"
# Should show: PyTorch: 2.6.0+cpu, CUDA Available: False
```

---

### ❌ "Streamlit Command Not Found"

**Symptom:**
```
'streamlit' is not recognized as an internal or external command
```

**Cause:** Streamlit not in PATH or not installed

**Solution:**
```powershell
# Use Python module syntax instead
python -m streamlit run streamlit_app.py

# Or add Streamlit to PATH
# Find Streamlit location:
python -c "import streamlit; print(streamlit.__file__)"
# Add the Scripts folder to your PATH
```

---

### ❌ Port Already in Use

**Symptom:**
```
Error: [Errno 10048] Only one usage of each socket address is normally permitted
```

**Cause:** Another process is using the required port

**Solution:**
```powershell
# Find which process is using the port
netstat -ano | findstr ":8001"  # VectorDB
netstat -ano | findstr ":3000"  # API Server
netstat -ano | findstr ":8501"  # Streamlit

# Kill the process (use PID from above)
taskkill /PID <PID> /F

# Example:
# netstat -ano | findstr ":3000"
# Output: TCP    0.0.0.0:3000    0.0.0.0:0    LISTENING    12345
# taskkill /PID 12345 /F
```

---

### ❌ Empty Search Results

**Symptom:**
- Search returns "No emails found"
- Stats show 0 emails

**Cause:** No emails indexed in VectorDB yet

**Solution:**
```powershell
# Option 1: Run test mode to add sample data
python vectordb_service.py test

# Option 2: Use the API to add emails
# See API documentation at http://localhost:3000/docs

# Verify
curl http://localhost:8001/stats
# Check "total_emails" field
```

---

## Service-Specific Problems

### VectorDB Service (Port 8001)

#### Issue: Service won't start

**Check Python version:**
```powershell
python --version
# Should be 3.8 or higher
```

**Check dependencies:**
```powershell
python -c "import chromadb; print('ChromaDB OK')"
python -c "import sentence_transformers; print('SentenceTransformers OK')"
```

**Check logs:**
```powershell
# Run in verbose mode
python vectordb_service.py
# Look for error messages
```

#### Issue: Slow embedding generation

**Cause:** CPU bottleneck with large batch sizes

**Solution:**
- Reduce batch size in vectordb_service.py
- Use smaller embedding model (already using all-MiniLM-L6-v2, which is optimal)
- Process emails in smaller chunks

#### Issue: ChromaDB database corruption

**Symptom:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solution:**
```powershell
# Backup current database
Move-Item .\vector_store .\vector_store_backup

# Start fresh
python vectordb_service.py
# VectorDB will create new database
```

---

### API Server (Port 3000)

#### Issue: HybridSearch not available

**Symptom:**
```
⚠️ Warning: HybridSearch service not available. Using VectorDB only.
```

**Cause:** search_service.py not found or import error

**Solution:**
```powershell
# Check if file exists
Test-Path .\search_service.py

# Test import
python -c "from search_service import HybridSearch; print('OK')"

# If import fails, check dependencies
pip install requests
```

#### Issue: API returns 500 errors

**Check API server logs in terminal**
Look for Python traceback errors

**Common causes:**
- VectorDB service not running (port 8001)
- Invalid request format
- Missing required fields

**Solution:**
```powershell
# Verify VectorDB is running
curl http://localhost:8001/health

# Test with valid request
curl "http://localhost:3000/api/emails/search?q=test&type=hybrid"
```

---

### Streamlit UI (Port 8501)

#### Issue: UI shows "Connecting..." forever

**Cause:** Streamlit service didn't start properly

**Solution:**
```powershell
# Stop any existing Streamlit processes
Get-Process python | Where-Object {$_.MainWindowTitle -like "*Streamlit*"} | Stop-Process

# Start Streamlit again
python -m streamlit run streamlit_app.py

# Check if port 8501 is open
Test-NetConnection -ComputerName localhost -Port 8501
```

#### Issue: Search not working in UI

**Check which mode is selected:**
- "API Mode (via Backend)" requires API server on port 3000
- "Direct Mode (VectorDB)" requires VectorDB on port 8001

**Verify services:**
```powershell
.\verify-system.ps1
```

#### Issue: UI is slow or unresponsive

**Possible causes:**
- Large number of results
- Slow search backend
- Network latency

**Solutions:**
- Limit result count in search
- Use pagination
- Check VectorDB performance

---

## Connection Errors

### Services can't communicate

#### Check Windows Firewall

```powershell
# Allow Python through firewall
New-NetFirewallRule -DisplayName "Python HTTP" -Direction Inbound -Program "C:\Python3X\python.exe" -Action Allow

# Or temporarily disable firewall (not recommended)
# Test if firewall is the issue
```

#### Check localhost resolution

```powershell
# Test if localhost resolves
ping localhost

# Check hosts file
notepad C:\Windows\System32\drivers\etc\hosts
# Should contain: 127.0.0.1 localhost
```

#### Check if services are listening

```powershell
# Show all listening ports
netstat -an | findstr "LISTENING"

# Should see:
# TCP    0.0.0.0:8001    (VectorDB)
# TCP    0.0.0.0:3000    (API Server)
# TCP    127.0.0.1:8501  (Streamlit)
```

---

## Performance Issues

### Slow search queries

**Measure performance:**
```powershell
# Time a search query
Measure-Command {
    curl "http://localhost:3000/api/emails/search?q=test&type=hybrid"
}
```

**Optimization tips:**

1. **Use hybrid search with appropriate weights:**
   - Default: 70% semantic + 30% keyword (good balance)
   - For speed: 100% keyword (type=keyword)
   - For accuracy: 100% semantic (type=vector)

2. **Limit result count:**
   - Add `&limit=10` to search query
   - Default is 50 results

3. **Index optimization:**
   - Ensure ChromaDB persistence is enabled
   - Don't rebuild index on every restart

4. **Hardware:**
   - Minimum 4GB RAM
   - SSD recommended for vector_store
   - Multi-core CPU helps

---

### High memory usage

**Check memory usage:**
```powershell
# Monitor Python processes
Get-Process python | Select-Object ProcessName, Id, WorkingSet
```

**Memory optimization:**

1. **VectorDB Service:**
   - Limit collection size
   - Use batch operations
   - Clear old embeddings

2. **API Server:**
   - Reduce concurrent requests
   - Implement caching

3. **Streamlit:**
   - Limit displayed results
   - Use pagination
   - Clear cache periodically

---

## Installation Problems

### pip install fails

#### SSL Certificate errors

```powershell
# Use --trusted-host
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r python-requirements.txt
```

#### Timeout errors

```powershell
# Increase timeout
pip install --timeout 1000 -r python-requirements.txt
```

#### Permission errors

```powershell
# Install for current user only
pip install --user -r python-requirements.txt

# Or run PowerShell as Administrator
```

---

### Python version issues

**Check Python version:**
```powershell
python --version
```

**If wrong version:**
```powershell
# Use py launcher to select version
py -3.10 -m pip install -r python-requirements.txt
py -3.10 vectordb_service.py
```

---

### Virtual environment issues

**Create clean virtual environment:**
```powershell
# Create venv
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r python-requirements.txt

# Run services
python vectordb_service.py
```

---

## Debug Mode

### Enable verbose logging

#### VectorDB Service

Edit `vectordb_service.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### API Server

Edit `api_server.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Streamlit

Run with verbose flag:
```powershell
python -m streamlit run streamlit_app.py --logger.level=debug
```

---

### Manual service testing

#### Test VectorDB directly

```powershell
python
```
```python
from src.Services.search.VectorDB import VectorDB

# Initialize
vdb = VectorDB()

# Add test email
vdb.add_email(
    email_id="test_123",
    subject="Test Email",
    body="This is a test",
    sender="test@example.com",
    date="2024-01-01",
    metadata={"category": "test"}
)

# Search
results = vdb.search("test", limit=5)
print(results)
```

#### Test HybridSearch directly

```powershell
python
```
```python
from search_service import HybridSearch

# Initialize
hs = HybridSearch()

# Search
results = hs.search_simple("test query")
print(results)
```

---

## Getting Help

### Collect system information

```powershell
# Create diagnostics report
@"
System Diagnostics Report
========================

Python Version:
$(python --version)

PyTorch Version:
$(python -c "import torch; print(torch.__version__)")

Installed Packages:
$(pip list | Select-String "fastapi|chromadb|streamlit|torch")

Listening Ports:
$(netstat -an | findstr "LISTENING" | findstr "8001 3000 8501")

"@ | Out-File diagnostics.txt

notepad diagnostics.txt
```

### Check documentation

1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Common commands
2. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Installation steps
3. **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** - System design

### Run verification script

```powershell
.\verify-system.ps1
```

This will test all services and show exactly what's working and what's not.

---

## Emergency Reset

If all else fails, complete system reset:

```powershell
# 1. Stop all services
Get-Process python | Stop-Process -Force

# 2. Clean virtual environment
Remove-Item -Recurse -Force .\venv

# 3. Clean vector database
Remove-Item -Recurse -Force .\vector_store

# 4. Reinstall Python dependencies
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r python-requirements.txt

# 5. Start fresh
.\start-all-services.ps1
```

---

## Still Having Issues?

1. **Check logs** in each terminal window for error messages
2. **Run verify-system.ps1** to identify failing components
3. **Review recent changes** in SESSION_SUMMARY.md
4. **Check system requirements** in README.md

**System Requirements:**
- ✅ Python 3.8+
- ✅ 4GB+ RAM
- ✅ ~2GB disk space
- ✅ Windows 10/11, macOS, or Linux
- ❌ No GPU required
