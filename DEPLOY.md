# Deploy to Railway - Simple Guide

## 🎯 Architecture

**Multi-Tenant SaaS:**
- Users sign up → Get their own tenant
- Users connect services via OAuth
- Backend runs workflows automatically for all users
- Scheduled daily ingestion at 9 AM UTC

## 🚀 Deploy in 10 Minutes

### Step 1: Login

```bash
railway login
```
Opens browser → Authenticate

### Step 2: Initialize

```bash
railway init
```
Creates new Railway project

### Step 3: Add Databases

```bash
railway add --database postgres
railway add --database redis
```

### Step 4: Set Environment Variables

**Easiest: Use Railway Dashboard**
1. Go to https://railway.app/dashboard
2. Click your project → Click your service
3. Go to "Variables" tab
4. Add these variables:

```
ENV=production
SECRET_KEY=<generate: openssl rand -hex 32>
JWT_SECRET_KEY=<same as SECRET_KEY>
ENCRYPTION_KEY=<generate: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
OPENAI_API_KEY=sk-your-key
SLACK_CLIENT_ID=your-slack-id
SLACK_CLIENT_SECRET=your-slack-secret
LINEAR_CLIENT_ID=your-linear-id
LINEAR_CLIENT_SECRET=your-linear-secret
GITHUB_CLIENT_ID=your-github-id
GITHUB_CLIENT_SECRET=your-github-secret
```

### Step 5: Deploy

```bash
railway up
```

### Step 6: Initialize Database

```bash
railway run python3 -c "from app.storage.tenant_db import TenantDatabase; TenantDatabase(tenant_id=None)"
```

### Step 7: Get Your URL

```bash
railway domain
```

---

## 📋 OAuth Apps Setup

Before Step 4, set up OAuth apps. Your Railway URL will be like `https://your-app.railway.app`

**Slack:** https://api.slack.com/apps
- Redirect: `https://your-app.railway.app/api/oauth/slack/callback`
- Scopes: `channels:read`, `groups:read`, `im:read`, `mpim:read`, `chat:read`, `users:read`

**Linear:** Settings → API
- Redirect: `https://your-app.railway.app/api/oauth/linear/callback`
- Scopes: `read`, `write`

**GitHub:** Settings → Developer → OAuth Apps
- Callback: `https://your-app.railway.app/api/oauth/github/callback`
- Scopes: `repo`, `read:org`

---

## ✅ Test

```bash
APP_URL=$(railway domain)

# Register
curl -X POST $APP_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123", "full_name": "Test"}'
```

---

**That's it!** Your SaaS is live! 🚀

