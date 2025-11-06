# Deploy to Railway - Step by Step

Railway is a modern platform that makes deployment easy - no credit card required!

## 🚀 Quick Deployment (15 minutes)

### Step 1: Install Railway CLI (Optional but Recommended)

```bash
# macOS
brew install railway

# Or download from https://railway.app/cli
```

### Step 2: Login to Railway

```bash
railway login
```

This will open your browser to authenticate.

### Step 3: Initialize Railway Project

```bash
cd /Users/blanco/corta/pm
railway init
```

This will:
- Create a new Railway project
- Link it to your current directory
- Set up deployment configuration

### Step 4: Add PostgreSQL Database

```bash
railway add postgresql
```

This automatically:
- Creates a PostgreSQL database
- Sets `DATABASE_URL` environment variable
- Links it to your project

### Step 5: Add Redis (Optional - for background jobs)

```bash
railway add redis
```

### Step 6: Set Environment Variables

```bash
# Generate secrets
SECRET=$(openssl rand -hex 32)
ENCRYPT_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Set basic config
railway variables set ENV=production
railway variables set SECRET_KEY="$SECRET"
railway variables set JWT_SECRET_KEY="$SECRET"
railway variables set ENCRYPTION_KEY="$ENCRYPT_KEY"

# Set OAuth credentials (get from OAuth apps)
railway variables set SLACK_CLIENT_ID=your-slack-client-id
railway variables set SLACK_CLIENT_SECRET=your-slack-client-secret
railway variables set LINEAR_CLIENT_ID=your-linear-client-id
railway variables set LINEAR_CLIENT_SECRET=your-linear-client-secret
railway variables set GITHUB_CLIENT_ID=your-github-client-id
railway variables set GITHUB_CLIENT_SECRET=your-github-client-secret

# Set OpenAI
railway variables set OPENAI_API_KEY=your-openai-key

# Set app URL (will be set automatically, but you can override)
# railway variables set APP_URL=https://your-app.railway.app
```

### Step 7: Deploy

```bash
railway up
```

This will:
- Build your application
- Deploy it to Railway
- Give you a public URL

### Step 8: Initialize Database

```bash
railway run python3 -c "from app.storage.tenant_db import TenantDatabase; TenantDatabase(tenant_id=None)"
```

### Step 9: Get Your App URL

```bash
railway domain
```

Or check in Railway dashboard: https://railway.app/dashboard

---

## 🌐 Alternative: Deploy via GitHub (Easiest)

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/pm-assistant.git
git push -u origin main
```

### Step 2: Connect to Railway

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect Python and deploy

### Step 3: Add Services

1. In Railway dashboard, click "New" → "Database" → "PostgreSQL"
2. Click "New" → "Database" → "Redis" (optional)

### Step 4: Set Environment Variables

In Railway dashboard:
1. Go to your service
2. Click "Variables" tab
3. Add all environment variables (same as Step 6 above)

### Step 5: Deploy

Railway will automatically deploy when you push to GitHub!

---

## 📋 Environment Variables Checklist

Set these in Railway dashboard or via CLI:

**Required:**
- `ENV=production`
- `SECRET_KEY` (generate with `openssl rand -hex 32`)
- `JWT_SECRET_KEY` (can be same as SECRET_KEY)
- `ENCRYPTION_KEY` (generate with Python Fernet)
- `OPENAI_API_KEY`

**OAuth (Required for workflows):**
- `SLACK_CLIENT_ID`
- `SLACK_CLIENT_SECRET`
- `LINEAR_CLIENT_ID`
- `LINEAR_CLIENT_SECRET`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`

**Optional:**
- `FRONTEND_URL` (if you have a frontend)
- `APP_URL` (auto-set by Railway, but can override)
- `SENDGRID_API_KEY` (for emails)
- `FROM_EMAIL` (for emails)

**Auto-set by Railway:**
- `DATABASE_URL` (from PostgreSQL service)
- `REDIS_URL` (from Redis service)
- `PORT` (Railway sets this)
- `RAILWAY_ENVIRONMENT` (auto-set)

---

## 🧪 Test Deployment

After deployment, Railway gives you a URL like: `https://your-app.railway.app`

```bash
# Health check
curl https://your-app.railway.app/health

# Register user
curl -X POST https://your-app.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123", "full_name": "Test"}'

# Login
curl -X POST https://your-app.railway.app/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123"
```

---

## 🔄 Update OAuth Redirect URLs

After deployment, update your OAuth apps with Railway URL:

- **Slack**: `https://your-app.railway.app/api/oauth/slack/callback`
- **Linear**: `https://your-app.railway.app/api/oauth/linear/callback`
- **GitHub**: `https://your-app.railway.app/api/oauth/github/callback`

---

## 📊 Railway Dashboard

Access your dashboard at: https://railway.app/dashboard

Features:
- View logs
- Monitor usage
- Manage environment variables
- View metrics
- Manage deployments

---

## 💰 Pricing

Railway has a generous free tier:
- $5 free credit per month
- Enough for small apps
- Pay-as-you-go after that

---

## 🆘 Troubleshooting

**Build fails:**
- Check logs in Railway dashboard
- Verify `requirements.txt` is correct
- Check Python version in `runtime.txt`

**Database connection fails:**
- Verify `DATABASE_URL` is set (auto-set by Railway)
- Check database service is running
- Run database initialization command

**App crashes:**
- Check logs: `railway logs`
- Verify all environment variables are set
- Check Procfile is correct

---

## 🎯 Next Steps

1. Deploy to Railway
2. Test registration/login
3. Connect OAuth services
4. Test workflows
5. Share with users!

---

**Ready?** Start with `railway login` and follow the steps above! 🚀

