# Deploy via Railway Dashboard - Easiest Method

## 🚀 Step-by-Step

### Step 1: Create Project in Dashboard

1. **Go to Railway Dashboard:**
   https://railway.app/dashboard

2. **Create New Project:**
   - Click **"New Project"** button
   - Choose one:
     - **"Deploy from GitHub repo"** (if you have a GitHub repo)
     - **"Empty Project"** (if deploying via CLI)

3. **If GitHub:**
   - Select your repository
   - Railway auto-detects Python
   - Skip to Step 3

4. **If Empty Project:**
   - Name it: `pm-assistant`
   - Click **"Create"**

### Step 2: Add Services

In your project dashboard:

1. **Add PostgreSQL:**
   - Click **"New"** → **"Database"** → **"PostgreSQL"**
   - Railway automatically sets `DATABASE_URL`

2. **Add Redis:**
   - Click **"New"** → **"Database"** → **"Redis"**
   - Railway automatically sets `REDIS_URL`

### Step 3: Configure Main Service

1. **If using GitHub deployment:**
   - Railway auto-creates a service
   - Go to service → **"Settings"** tab
   - Set **Start Command:** `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`

2. **If using Empty Project:**
   - Click **"New"** → **"GitHub Repo"** (or **"Empty Service"**)
   - If GitHub: Select your repo
   - If Empty: We'll deploy via CLI later

### Step 4: Set Environment Variables

1. **Go to your service** (the main app)
2. Click **"Variables"** tab
3. Click **"New Variable"** and add:

```
ENV=production
SECRET_KEY=c6cd64a1af3ee30054b40fd1670d70e17b7b2165a5692dd786203c7250db5bc0
JWT_SECRET_KEY=c6cd64a1af3ee30054b40fd1670d70e17b7b2165a5692dd786203c7250db5bc0
ENCRYPTION_KEY=F8EaCHwEyPveheimkm5z8UBj1B90LoYzoTyv931BNsM=
OPENAI_API_KEY=sk-your-openai-key-here
SLACK_CLIENT_ID=your-slack-client-id
SLACK_CLIENT_SECRET=your-slack-client-secret
LINEAR_CLIENT_ID=your-linear-client-id
LINEAR_CLIENT_SECRET=your-linear-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

**Note:** You can set OAuth credentials later after you get your Railway URL.

### Step 5: Deploy

**If using GitHub:**
- Railway auto-deploys on git push
- Or click **"Deploy"** button

**If using Empty Project:**
- Link project: `railway link` (select your project)
- Deploy: `railway up`

### Step 6: Initialize Database

After deployment, in Railway dashboard:

1. Go to your service
2. Click **"Deployments"** tab
3. Click on latest deployment
4. Click **"Shell"** tab
5. Run:
   ```bash
   python3 -c "from app.storage.tenant_db import TenantDatabase; TenantDatabase(tenant_id=None)"
   ```

Or via CLI:
```bash
railway run python3 -c "from app.storage.tenant_db import TenantDatabase; TenantDatabase(tenant_id=None)"
```

### Step 7: Get Your URL

In Railway dashboard:
- Go to your service
- Click **"Settings"** tab
- Scroll to **"Domains"**
- Click **"Generate Domain"**
- Copy your URL (e.g., `https://pm-assistant-production.up.railway.app`)

### Step 8: Set Up OAuth Apps

Now that you have your Railway URL, set up OAuth apps:

**Slack:** https://api.slack.com/apps
- Redirect: `https://your-app.railway.app/api/oauth/slack/callback`

**Linear:** Settings → API
- Redirect: `https://your-app.railway.app/api/oauth/linear/callback`

**GitHub:** Settings → Developer → OAuth Apps
- Callback: `https://your-app.railway.app/api/oauth/github/callback`

Then add the OAuth credentials to Railway variables.

---

## ✅ You're Live!

Your SaaS is now deployed and ready for users!

---

## 🆘 Troubleshooting

**Service won't start:**
- Check **"Logs"** tab in Railway dashboard
- Verify start command is correct
- Check environment variables are set

**Database connection fails:**
- Verify `DATABASE_URL` is set (auto-set by Railway)
- Check PostgreSQL service is running

**Build fails:**
- Check **"Logs"** tab
- Verify `requirements.txt` is correct
- Check Python version in `runtime.txt`

---

**Ready?** Go to https://railway.app/dashboard and create your project! 🚀

