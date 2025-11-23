# 🚀 Quick Fix Guide - Railway & Vercel Deployment

## TL;DR - What Was Wrong?

1. **Railway Backend:** Mixed `require()` and `import` causing crashes ❌
2. **Vercel Frontend:** API URL missing `https://` protocol ❌
3. **Railway Config:** Missing required environment variables ❌

## ✅ What I Fixed

### Code Changes (Already Done)
- ✅ `src/main.ts` - Fixed module syntax
- ✅ `src/main.ts` - Added `/health` endpoint
- ✅ `frontend/.env.production` - Added `https://` to API URL
- ✅ `railway.json` - Updated Docker configuration

### What YOU Need to Do Now

#### 1️⃣ Add Environment Variables in Railway

**Go to Railway Dashboard → Your Project → Variables → Add these:**

```bash
# REQUIRED (app won't start without these)
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USER=your-email@gmail.com
IMAP_PASSWORD=your-gmail-app-password
IMAP_TLS=true
PORT=3000
NODE_ENV=production

# OPTIONAL (for search and notifications)
ELASTICSEARCH_URL=your-elastic-url
SLACK_API_TOKEN=your-slack-token
ENABLE_CLASSIFIER=false
```

**For Gmail Users:**
- Don't use regular password ❌
- Generate App Password at: https://myaccount.google.com/apppasswords ✅

#### 2️⃣ Commit and Push Changes

```powershell
cd c:\Users\shash\Desktop\onebox_aggregator
git add .
git commit -m "Fix deployment issues: module syntax and health checks"
git push origin main
```

#### 3️⃣ Verify Deployment

**After Railway redeploys (automatic after push):**

```bash
# Test health endpoint
curl https://your-app.railway.app/health

# Should return:
# {"status":"healthy","service":"onebox-backend",...}
```

**In browser:**
- Open your Vercel frontend URL
- Try searching for emails
- Should show "Live Elastic index" NOT "Demo dataset"

---

## 🎯 Quick Verification Checklist

- [ ] Environment variables added to Railway dashboard
- [ ] Code changes committed and pushed to GitHub
- [ ] Railway shows "Deployed" status (green)
- [ ] Health check URL works: `https://your-app.railway.app/health`
- [ ] Railway logs show: "🚀 API server running on port 3000"
- [ ] Frontend on Vercel loads without errors
- [ ] Frontend search connects to Railway API (not demo data)

---

## 🐛 Still Not Working?

### Railway backend crashes on startup?
→ Check environment variables are correctly set  
→ For Gmail, use App Password not regular password  
→ Check Railway logs for error messages  

### Frontend still shows "Demo dataset"?
→ Check browser console for CORS errors  
→ Verify `VITE_API_BASE_URL` in Vercel has `https://`  
→ Hard refresh browser (Ctrl+Shift+R)  

### "Connection Refused" errors?
→ Railway backend isn't running  
→ Missing IMAP environment variables  
→ Check Railway logs for startup errors  

---

## 📚 Detailed Documentation

For complete details, see:
- **DEPLOYMENT_FIXES_SUMMARY.md** - Full root cause analysis
- **RAILWAY_SETUP.md** - Step-by-step Railway setup
- **TROUBLESHOOTING.md** - Common error solutions

---

## 🎉 Success Looks Like

**Railway:**
```
✅ Status: Deployed
✅ Health Check: Passing
✅ Logs: "🚀 API server running on port 3000"
```

**Vercel:**
```
✅ Status: Ready
✅ Search: Connects to Railway
✅ Results: Shows "Live Elastic index"
```

---

**Last Updated:** November 23, 2025  
**Time to Fix:** ~10 minutes (mostly adding env vars)
