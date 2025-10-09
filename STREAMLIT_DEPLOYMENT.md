# 📧 Onebox Aggregator - Streamlit Cloud Deployment

## 🚀 Quick Deploy to Streamlit Cloud

### Option 1: Direct Deploy (Recommended)
1. **Fork this repository** to your GitHub account
2. **Go to [share.streamlit.io](https://share.streamlit.io)**
3. **Click "New app"**
4. **Select your forked repository**
5. **Set main file path**: `streamlit_app.py`
6. **Click "Deploy"**

### Option 2: Demo Mode Deploy
1. **Use `app.py` as main file** (forces demo mode)
2. **Ensure `requirements-streamlit.txt` is used**

## 🎯 Demo Features

### ✅ What Works in Demo Mode
- **Full-text search** across 10 realistic sample emails
- **Smart categorization** (Interested, Not Interested, More Information)
- **Responsive UI** with modern design
- **Instant results** (no external dependencies)
- **Multiple search strategies** (keyword + semantic-like)

### 📧 Sample Email Types
- **Security Alerts**: Login attempts, account verification
- **Project Management**: Timeline updates, performance reviews
- **Business Communications**: Funding, contracts, renewals
- **Technical Updates**: Development environment, GitHub notifications

### 🔍 Try These Queries
```
"Show me security alerts"
"Project timeline updates"
"Funding announcement"
"Stripe verification"
"GitHub notifications"
"Contract renewal"
```

## 🛠 Technical Details

### Demo Mode Detection
The app automatically detects Streamlit Cloud environment:
```python
IS_DEMO = (
    "STREAMLIT_RUNTIME_RUNNING" in os.environ or
    "STREAMLIT_SERVER_PORT" in os.environ or
    Path("demo_mode").exists() or
    os.getenv("DEMO_MODE", "false").lower() == "true"
)
```

### Architecture (Demo Mode)
```
User Query → SQLite FTS → Demo Search Service → Formatted Results
```

### Local Development
To test demo mode locally:
```bash
# Method 1: Environment variable
export DEMO_MODE=true
streamlit run streamlit_app.py

# Method 2: Create marker file
touch demo_mode
streamlit run streamlit_app.py

# Method 3: Use demo entry point
streamlit run app.py
```

## 📁 Required Files for Deployment

### Core Files
- `streamlit_app.py` - Main application
- `demo_search.py` - Demo search service
- `requirements-streamlit.txt` - Minimal dependencies

### Configuration
- `.streamlit/config.toml` - Streamlit configuration
- `app.py` - Demo mode entry point (optional)

### Auto-Generated
- `demo_emails.db` - SQLite database (created automatically)
- `demo_emails.json` - Sample data (created automatically)

## 🎨 Customization

### Adding More Sample Emails
Edit the `_create_sample_emails()` method in `demo_search.py`:

```python
def _create_sample_emails(self) -> List[Dict[str, Any]]:
    emails = [
        {
            "id": "demo_011",
            "from": "your-sender@example.com",
            "subject": "Your Custom Subject",
            "body": "Your email content here...",
            "aiCategory": "Interested",
            # ... other fields
        }
    ]
    return emails
```

### Modifying UI
Update `streamlit_app.py` demo section:
- Change suggested queries
- Modify styling
- Add custom metrics

## 🐛 Troubleshooting

### Common Issues
1. **Import Error**: Ensure `demo_search.py` is in repository
2. **No Results**: Check sample email content matches queries
3. **Styling Issues**: Verify `.streamlit/config.toml` is present

### Debug Mode
Add to your forked repository:
```python
# Add to streamlit_app.py
if IS_DEMO:
    st.sidebar.write(f"Demo mode: {USE_DEMO_SEARCH}")
    st.sidebar.write(f"Service available: {demo_search_service is not None}")
```

## 🌟 Features Showcase

Perfect for demonstrating:
- **Email aggregation** and search capabilities
- **AI-powered categorization** 
- **Hybrid search** methodologies
- **Modern Streamlit** UI design
- **Zero-setup** user experience

## 📊 Performance
- **Load time**: < 3 seconds
- **Search time**: < 0.5 seconds
- **Memory usage**: < 100MB
- **Database size**: < 1MB

---

🎯 **Ready to deploy?** Click [here to deploy on Streamlit Cloud](https://share.streamlit.io) and showcase your email management solution!