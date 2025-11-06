# Deploy PM Assistant to Railway

## 🎯 Architecture Overview

**How it works:**
1. Users sign up → Create account
2. Users connect services → OAuth flows (Slack, Linear, GitHub)
3. Backend runs workflows → Automatically for all users
4. Scheduled ingestion → Daily for all active tenants

## 🚀 Quick Deploy (15 minutes)

### Option 1: Railway CLI (Recommended)

```bash
# 1. Install Railway CLI
brew install railway

# 2. Login
railway login

# 3. Initialize project
cd /Users/blanco/corta/pm
railway init

# 4. Add PostgreSQL
railway add postgresql

# 5. Add Redis (for background jobs)
railway add redis

# 6. Generate and set secrets
SECRET=$(openssl rand -hex 32)
ENCRYPT_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

railway variables set ENV=production
railway variables set SECRET_KEY="$SECRET"
railway variables set JWT_SECRET_KEY="$SECRET"
railway variables set ENCRYPTION_KEY="$ENCRYPT_KEY"

# 7. Set OAuth credentials (get from OAuth apps - see below)
railway variables set SLACK_CLIENT_ID=your-slack-client-id
railway variables set SLACK_CLIENT_SECRET=your-slack-secret
railway variables set LINEAR_CLIENT_ID=your-linear-client-id
railway variables set LINEAR_CLIENT_SECRET=your-linear-secret
railway variables set GITHUB_CLIENT_ID=your-github-client-id
railway variables set GITHUB_CLIENT_SECRET=your-github-secret

# 8. Set OpenAI
railway variables set OPENAI_API_KEY=your-openai-key

# 9. Deploy
railway up

# 10. Initialize database
railway run python3 -c "from app.storage.tenant_db import TenantDatabase; TenantDatabase(tenant_id=None)"

# 11. Get your URL
railway domain
```

### Option 2: GitHub Integration (Easiest)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/pm-assistant.git
   git push -u origin main
   ```

2. **Connect to Railway:**
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Python

3. **Add Services:**
   - Click "New" → "Database" → "PostgreSQL"
   - Click "New" → "Database" → "Redis"

4. **Set Environment Variables:**
   - Go to your service → "Variables" tab
   - Add all variables (see checklist below)

5. **Deploy:**
   - Railway auto-deploys on git push!

---

## 📋 OAuth Apps Setup (Required)

Before deploying, set up OAuth apps. Railway will give you a URL like `https://your-app.railway.app`

### Slack OAuth App

1. Go to https://api.slack.com/apps
2. Create New App → "From scratch"
3. Name: "PM Assistant"
4. **OAuth Redirect URL**: `https://your-app.railway.app/api/oauth/slack/callback`
5. Go to "OAuth & Permissions"
6. Add Bot Token Scopes:
   - `channels:read`
   - `groups:read`
   - `im:read`
   - `mpim:read`
   - `chat:read`
   - `users:read`
7. Install app to workspace
8. Copy **Client ID** and **Client Secret**

### Linear OAuth App

1. Linear Settings → API
2. Create OAuth Application
3. Name: "PM Assistant"
4. **Redirect URL**: `https://your-app.railway.app/api/oauth/linear/callback`
5. Scopes: `read`, `write`
6. Copy **Client ID** and **Client Secret**

### GitHub OAuth App

1. GitHub → Settings → Developer settings → OAuth Apps
2. New OAuth App
3. Name: "PM Assistant"
4. **Authorization callback URL**: `https://your-app.railway.app/api/oauth/github/callback`
5. Scopes: `repo`, `read:org`
6. Copy **Client ID** and generate **Client Secret**

---

## 🔧 Environment Variables Checklist

Set these in Railway dashboard (Variables tab):

**Core:**
- `ENV=production`
- `SECRET_KEY` (generate: `openssl rand -hex 32`)
- `JWT_SECRET_KEY` (can be same as SECRET_KEY)
- `ENCRYPTION_KEY` (generate: `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
- `OPENAI_API_KEY`

**OAuth:**
- `SLACK_CLIENT_ID`
- `SLACK_CLIENT_SECRET`
- `LINEAR_CLIENT_ID`
- `LINEAR_CLIENT_SECRET`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`

**Auto-set by Railway:**
- `DATABASE_URL` (from PostgreSQL)
- `REDIS_URL` (from Redis)
- `PORT` (Railway sets this)

**Optional:**
- `FRONTEND_URL` (if you have a frontend)
- `SENDGRID_API_KEY` (for email verification)
- `FROM_EMAIL`

---

## 🔄 How It Works for Users

### User Flow:

1. **User visits your app** → Registers account
   ```
   POST /api/auth/register
   {
     "email": "user@example.com",
     "password": "password123",
     "full_name": "John Doe"
   }
   ```

2. **User logs in** → Gets JWT token
   ```
   POST /api/auth/login
   Returns: { "access_token": "...", "tenant_id": "..." }
   ```

3. **User connects Slack** → OAuth flow
   ```
   GET /api/oauth/slack/authorize?redirect_uri=...
   → User authorizes in Slack
   → Callback stores encrypted token
   → Status: connected ✅
   ```

4. **User connects Linear** → OAuth flow
   ```
   GET /api/oauth/linear/authorize?redirect_uri=...
   → User authorizes in Linear
   → Callback stores encrypted token
   → Status: connected ✅
   ```

5. **Backend runs workflows automatically:**
   - Scheduled daily ingestion (9 AM UTC)
   - Processes messages for all active tenants
   - Updates tickets based on conversations
   - Generates standup data

6. **User can trigger workflows manually:**
   ```
   POST /api/workflows/ingest/slack
   GET /api/workflows/standup
   POST /api/workflows/process
   ```

---

## 📊 Background Jobs Setup

Railway will run:
- **Web service**: FastAPI app (handles API requests)
- **Worker service**: Celery worker (runs background jobs)
- **Beat service**: Celery beat (schedules daily ingestion)

To set up multiple services in Railway:

1. **Create Web Service:**
   - Uses `railway.json` or Procfile
   - Runs: `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`

2. **Create Worker Service:**
   - Same codebase
   - Command: `celery -A app.jobs.ingestion.celery_app worker --loglevel=info`
   - Shares same environment variables

3. **Create Beat Service:**
   - Same codebase
   - Command: `celery -A app.jobs.ingestion.celery_app beat --loglevel=info`
   - Shares same environment variables

**Or use Railway's service configuration:**

In Railway dashboard:
- Add multiple services from same repo
- Each service has different start command
- All share same environment variables

---

## 🧪 Test After Deployment

```bash
# Get your Railway URL (e.g., https://pm-assistant-production.up.railway.app)
APP_URL="https://your-app.railway.app"

# 1. Health check
curl $APP_URL/health

# 2. Register user
curl -X POST $APP_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123", "full_name": "Test User"}'

# 3. Login
curl -X POST $APP_URL/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123"

# 4. Test OAuth (after setting up OAuth apps)
# Get auth URL
curl "$APP_URL/api/oauth/slack/authorize?redirect_uri=https://your-frontend.com/callback" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔐 Security Notes

- Each user gets their own tenant
- OAuth tokens are encrypted at rest
- JWT tokens expire in 30 days
- Passwords hashed with bcrypt
- All workflows are tenant-isolated

---

## 📈 Scaling

Railway automatically:
- Scales based on traffic
- Handles multiple concurrent users
- Isolates each tenant's data
- Runs background jobs for all active tenants

---

## 🎯 Next Steps After Deployment

1. ✅ Deploy to Railway
2. ✅ Set up OAuth apps with Railway URL
3. ✅ Test registration/login
4. ✅ Test OAuth connections
5. ✅ Verify background jobs are running
6. ✅ Share with users!

---

**Ready to deploy?** Start with `railway login`! 🚀

