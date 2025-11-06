# Railway Quick Start - Deploy in 10 Minutes

## 🚀 Fastest Path to Production

### Step 1: Login (2 min)

```bash
railway login
```
Opens browser → Authenticate → Done

### Step 2: Initialize Project (1 min)

```bash
cd /Users/blanco/corta/pm
railway init
```

Choose:
- Create new project
- Name: `pm-assistant` (or your choice)

### Step 3: Add Databases via Dashboard (2 min)

1. Go to https://railway.app/dashboard
2. Click your project
3. Click **"New"** → **"Database"** → **"PostgreSQL"**
4. Click **"New"** → **"Database"** → **"Redis"**

Railway automatically sets `DATABASE_URL` and `REDIS_URL`

### Step 4: Set Environment Variables (3 min)

In Railway dashboard:
1. Click your **service** (the main app)
2. Go to **"Variables"** tab
3. Click **"New Variable"** and add:

**Core:**
```
ENV=production
SECRET_KEY=<generate: openssl rand -hex 32>
JWT_SECRET_KEY=<same as SECRET_KEY>
ENCRYPTION_KEY=<generate: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
OPENAI_API_KEY=sk-your-key
```

**OAuth (get from OAuth apps - see below):**
```
SLACK_CLIENT_ID=your-slack-id
SLACK_CLIENT_SECRET=your-slack-secret
LINEAR_CLIENT_ID=your-linear-id
LINEAR_CLIENT_SECRET=your-linear-secret
GITHUB_CLIENT_ID=your-github-id
GITHUB_CLIENT_SECRET=your-github-secret
```

### Step 5: Deploy (2 min)

```bash
railway up
```

Railway will:
- Build your app
- Deploy it
- Give you a URL

### Step 6: Initialize Database (1 min)

```bash
railway run python3 -c "from app.storage.tenant_db import TenantDatabase; TenantDatabase(tenant_id=None)"
```

### Step 7: Get Your URL

```bash
railway domain
```

Or check in dashboard.

---

## 📋 OAuth Apps Setup (Before Step 4)

You need OAuth credentials. Railway will give you a URL like `https://your-app.railway.app`

### Slack
1. https://api.slack.com/apps → Create App
2. OAuth Redirect: `https://your-app.railway.app/api/oauth/slack/callback`
3. Scopes: `channels:read`, `groups:read`, `im:read`, `mpim:read`, `chat:read`, `users:read`
4. Install → Copy Client ID & Secret

### Linear
1. Linear Settings → API → Create OAuth App
2. Redirect: `https://your-app.railway.app/api/oauth/linear/callback`
3. Scopes: `read`, `write`
4. Copy Client ID & Secret

### GitHub
1. GitHub Settings → Developer → OAuth Apps → New
2. Callback: `https://your-app.railway.app/api/oauth/github/callback`
3. Scopes: `repo`, `read:org`
4. Copy Client ID & Secret

---

## ✅ Test Deployment

```bash
# Get your URL
APP_URL=$(railway domain)

# Health check
curl $APP_URL/health

# Register user
curl -X POST $APP_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123", "full_name": "Test"}'
```

---

## 🎯 How It Works for Users

1. **User signs up** → `POST /api/auth/register`
2. **User logs in** → `POST /api/auth/login` → Gets JWT token
3. **User connects Slack** → OAuth flow → Token stored encrypted
4. **User connects Linear** → OAuth flow → Token stored encrypted
5. **Backend runs workflows** → Automatically daily at 9 AM UTC
6. **User can trigger manually** → `POST /api/workflows/ingest/slack`

---

## 🔄 Background Jobs Setup

Railway can run multiple services:

1. **Web Service** (main app)
   - Command: `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`
   - Handles API requests

2. **Worker Service** (optional - for background jobs)
   - Add new service from same repo
   - Command: `celery -A app.jobs.ingestion.celery_app worker --loglevel=info`
   - Shares same environment variables

3. **Beat Service** (optional - for scheduling)
   - Add new service from same repo
   - Command: `celery -A app.jobs.ingestion.celery_app beat --loglevel=info`
   - Runs daily ingestion at 9 AM UTC

**Or use Railway's service configuration:**
- In dashboard, add multiple services
- Each with different start command
- All share same env vars

---

## 🆘 Troubleshooting

**Build fails:**
- Check logs in Railway dashboard
- Verify `requirements.txt` is correct

**Database connection fails:**
- Verify `DATABASE_URL` is set (auto-set by Railway)
- Check PostgreSQL service is running

**OAuth not working:**
- Verify redirect URLs match exactly
- Check Client IDs/Secrets are correct

---

**That's it!** Your SaaS is live and ready for users! 🚀

