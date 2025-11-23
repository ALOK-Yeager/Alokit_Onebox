# Railway Deployment Setup Guide

## Critical Steps to Fix Railway Deployment

### Step 1: Fix the Code Issues
✅ Already fixed:
- Mixed import/require syntax in `main.ts`
- Missing health check endpoint
- Frontend `.env.production` URL

### Step 2: Set Environment Variables in Railway

Go to your Railway project dashboard and add these variables:

#### **REQUIRED Variables (App won't start without these):**

```
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USER=your-email@gmail.com
IMAP_PASSWORD=your-app-password-here
IMAP_TLS=true
PORT=3000
NODE_ENV=production
```

#### **Optional but Recommended:**

```
# Elasticsearch (for search functionality)
ELASTICSEARCH_URL=https://your-elastic-cloud-url
ELASTICSEARCH_API_KEY=your-api-key

# Or use username/password
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=your-password

# Notifications (optional)
SLACK_API_TOKEN=xoxb-your-slack-token
WEBHOOK_URL=https://your-webhook-url

# Disable classifier if not using AI
ENABLE_CLASSIFIER=false
```

### Step 3: Update Railway Configuration

Your `railway.json` is minimal. Update it:

```json
{
    "$schema": "https://railway.app/railway.schema.json",
    "build": {
        "builder": "DOCKERFILE",
        "dockerfilePath": "Dockerfile"
    },
    "deploy": {
        "startCommand": "node dist/main.js",
        "restartPolicyType": "ON_FAILURE",
        "restartPolicyMaxRetries": 10,
        "healthcheckPath": "/health",
        "healthcheckTimeout": 30
    }
}
```

### Step 4: Rebuild and Deploy

1. **Commit the code fixes:**
   ```bash
   git add .
   git commit -m "Fix mixed module syntax and add health endpoint"
   git push origin main
   ```

2. **Railway will auto-deploy** or manually trigger:
   - Go to Railway dashboard
   - Click "Deploy" → "Trigger Deploy"

### Step 5: Verify Deployment

After deployment, check:

1. **Service Health:**
   ```bash
   curl https://your-service.up.railway.app/health
   ```
   Should return:
   ```json
   {
     "status": "healthy",
     "service": "onebox-backend",
     "timestamp": "2025-11-23T...",
     "uptime": 123.45
   }
   ```

2. **Check Logs:**
   - Railway Dashboard → Your Service → Logs
   - Look for "🚀 API server running on port 3000"
   - Should NOT see "Connection Refused" or module errors

### Common Issues After Fix

#### Issue: "Missing required environment variables"
**Solution:** Add IMAP_* variables in Railway dashboard

#### Issue: "ECONNREFUSED" errors in logs
**Solution:** 
- Check if IMAP credentials are correct
- For Gmail, use App Password, not regular password
- Generate at: https://myaccount.google.com/apppasswords

#### Issue: Elasticsearch errors
**Solution:** Either:
- Set ELASTICSEARCH_URL variable with valid Elastic Cloud URL
- OR the app will gracefully handle missing Elasticsearch

#### Issue: "Cannot find module" errors
**Solution:** 
- Railway is building with Dockerfile (correct)
- Check that `package.json` and `tsconfig.json` are in repo root
- Rebuild with "Clear Cache" option in Railway

### Step 6: Update Frontend Environment

Your frontend is on Vercel. Update environment variable:

1. Go to Vercel → Your Project → Settings → Environment Variables
2. Update `VITE_API_BASE_URL`:
   ```
   VITE_API_BASE_URL=https://your-railway-service.up.railway.app
   ```
   ⚠️ Make sure to include `https://` protocol!

3. Redeploy frontend:
   - Vercel → Deployments → Click "..." → Redeploy

### Expected Result

After all fixes:
- ✅ Railway backend deploys successfully
- ✅ Health check responds with 200 OK
- ✅ Vercel frontend can connect to Railway API
- ✅ Search functionality works
- ✅ No more "warming up" fallback messages

### Monitoring

Check these endpoints to ensure everything works:

```bash
# Backend health
curl https://your-railway-service.up.railway.app/health

# Search API (requires running app with indexed emails)
curl "https://your-railway-service.up.railway.app/api/emails/search?q=test"

# Frontend
open https://your-vercel-app.vercel.app
# Try searching - should hit Railway API, not demo data
```

---

## Architecture After Fix

```
┌─────────────────┐
│  Vercel         │
│  (Frontend)     │ ← User accesses here
└────────┬────────┘
         │ VITE_API_BASE_URL
         │ https://...railway.app
         ▼
┌─────────────────┐
│  Railway        │
│  (Backend)      │ ← Fixed main.ts, proper env vars
│  Port: 3000     │
│  /health ✓      │
└────────┬────────┘
         │
         ├─→ IMAP Server (Gmail/Outlook)
         ├─→ Elasticsearch (optional)
         └─→ Slack/Webhooks (optional)
```

---

## Quick Checklist

- [ ] Code fixes committed and pushed
- [ ] Environment variables set in Railway
- [ ] Railway redeployed successfully
- [ ] Health endpoint returns 200 OK
- [ ] Frontend `.env.production` updated with `https://`
- [ ] Vercel redeployed
- [ ] Frontend search connects to Railway API
- [ ] No more "warming up" messages

---

## Need Help?

Check logs in:
- **Railway:** Dashboard → Service → Logs tab
- **Vercel:** Dashboard → Deployment → Functions log

If issues persist, check:
1. `TROUBLESHOOTING.md` in repo
2. Ensure all environment variables are correctly set
3. Verify IMAP credentials work (test with email client)
4. Check Railway/Vercel service status pages
