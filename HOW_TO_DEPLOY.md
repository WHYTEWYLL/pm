# How to Deploy PM Assistant to Railway

## 🚀 Complete Step-by-Step Guide

### Prerequisites
- Railway account (free at https://railway.app)
- OAuth app credentials (Slack, Linear, GitHub)
- OpenAI API key

---

## Step 1: Login to Railway (2 min)

```bash
railway login
```

This opens your browser. Authenticate with Railway.

**Verify login:**
```bash
railway whoami
```

---

## Step 2: Initialize Project (1 min)

```bash
cd /Users/blanco/corta/pm
railway init
```

Choose:
- **Create new project**
- **Name:** `pm-assistant` (or your choice)

This creates a Railway project and links it to your directory.

---

## Step 3: Add PostgreSQL Database (1 min)

```bash
railway add --database postgres
```

Railway automatically:
- Creates PostgreSQL database
- Sets `DATABASE_URL` environment variable
- Links it to your project

---

## Step 4: Add Redis Database (1 min)

```bash
railway add --database redis
```

Railway automatically:
- Creates Redis database
- Sets `REDIS_URL` environment variable
- Links it to your project

---

## Step 5: Generate Secrets (1 min)

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate ENCRYPTION_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Save these values!** You'll need them in the next step.

---

## Step 6: Set Environment Variables (5 min)

**Option A: Railway Dashboard (Easiest)**

1. Go to https://railway.app/dashboard
2. Click your project
3. Click your **service** (the main app)
4. Go to **"Variables"** tab
5. Click **"New Variable"** and add each:

```
ENV=production
SECRET_KEY=<paste from step 5>
JWT_SECRET_KEY=<same as SECRET_KEY>
ENCRYPTION_KEY=<paste from step 5>
OPENAI_API_KEY=sk-your-openai-key-here
SLACK_CLIENT_ID=your-slack-client-id
SLACK_CLIENT_SECRET=your-slack-client-secret
LINEAR_CLIENT_ID=your-linear-client-id
LINEAR_CLIENT_SECRET=your-linear-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

**Option B: Railway CLI (Interactive)**

```bash
railway variables
```

This opens interactive mode. Add each variable one by one.

---

## Step 7: Deploy (2 min)

```bash
railway up
```

Railway will:
- Build your application
- Deploy it
- Give you a URL

**Wait for deployment to complete!** You'll see build logs.

---

## Step 8: Get Your App URL (1 min)

```bash
railway domain
```

Or check in Railway dashboard. Your URL will be like:
`https://pm-assistant-production.up.railway.app`

**Save this URL!** You'll need it for OAuth apps.

---

## Step 9: Initialize Database (1 min)

```bash
railway run python3 -c "from app.storage.tenant_db import TenantDatabase; TenantDatabase(tenant_id=None)"
```

This creates all database tables.

---

## Step 10: Set Up OAuth Apps (15 min)

Now that you have your Railway URL, set up OAuth apps:

### Slack OAuth App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. **App Name:** PM Assistant
4. **Workspace:** Select your workspace
5. Click **"Create App"**
6. Go to **"OAuth & Permissions"** in left sidebar
7. Scroll to **"Redirect URLs"**
8. Add: `https://your-app.railway.app/api/oauth/slack/callback`
9. Scroll to **"Bot Token Scopes"** and add:
   - `channels:read`
   - `groups:read`
   - `im:read`
   - `mpim:read`
   - `chat:read`
   - `users:read`
10. Click **"Install App to Workspace"**
11. Copy **Client ID** and **Client Secret**
12. Add to Railway variables (if not done in Step 6)

### Linear OAuth App

1. Go to Linear Settings → API
2. Click **"Create OAuth Application"**
3. **Name:** PM Assistant
4. **Redirect URL:** `https://your-app.railway.app/api/oauth/linear/callback`
5. **Scopes:** Check `read` and `write`
6. Copy **Client ID** and **Client Secret**
7. Add to Railway variables

### GitHub OAuth App

1. Go to GitHub → Settings → Developer settings → OAuth Apps
2. Click **"New OAuth App"**
3. **Application name:** PM Assistant
4. **Homepage URL:** `https://your-app.railway.app`
5. **Authorization callback URL:** `https://your-app.railway.app/api/oauth/github/callback`
6. Click **"Register application"**
7. Copy **Client ID**
8. Click **"Generate a new client secret"**
9. Copy **Client Secret**
10. Add to Railway variables

---

## Step 11: Test Deployment (2 min)

```bash
# Get your URL
APP_URL=$(railway domain)

# Health check
curl $APP_URL/health

# Register a user
curl -X POST $APP_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123", "full_name": "Test User"}'

# Login
curl -X POST $APP_URL/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123"
```

---

## ✅ You're Live!

Your SaaS is now deployed and ready for users!

**What works:**
- ✅ User registration
- ✅ User login
- ✅ OAuth connections (Slack, Linear, GitHub)
- ✅ Workflow execution
- ✅ Scheduled daily ingestion (9 AM UTC)

---

## 🔄 Background Jobs (Optional)

To run background jobs (Celery worker and beat):

1. In Railway dashboard, add **new service** from same repo
2. Set start command: `celery -A app.jobs.ingestion.celery_app worker --loglevel=info`
3. Add another service for beat: `celery -A app.jobs.ingestion.celery_app beat --loglevel=info`

Or use Railway's service configuration to run multiple processes.

---

## 🆘 Troubleshooting

**Build fails:**
- Check logs: `railway logs`
- Verify `requirements.txt` is correct
- Check Python version in `runtime.txt`

**Database connection fails:**
- Verify `DATABASE_URL` is set (auto-set by Railway)
- Check PostgreSQL service is running
- Run database initialization again

**OAuth not working:**
- Verify redirect URLs match exactly
- Check Client IDs/Secrets are correct
- Verify environment variables are set

**App crashes:**
- Check logs: `railway logs`
- Verify all environment variables are set
- Check Procfile is correct

---

## 📚 Next Steps

1. ✅ Deploy to Railway
2. ✅ Set up OAuth apps
3. ✅ Test registration/login
4. ✅ Test OAuth connections
5. ✅ Share with users!

---

**Ready?** Start with `railway login`! 🚀

