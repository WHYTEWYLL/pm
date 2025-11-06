# Deploy Now - Quick Steps

## ✅ You're Logged In!

**Logged in as:** juanmiblanco1@gmail.com

## 🚀 Next Steps

### Option 1: Create Project via Dashboard (Easiest)

1. **Go to Railway Dashboard:**
   https://railway.app/dashboard

2. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo" OR "Empty Project"
   - If GitHub: Select your repo
   - If Empty: We'll deploy via CLI

3. **Link to Your Project:**
   ```bash
   railway link
   ```
   Select your project from the list

4. **Add Databases:**
   ```bash
   railway add --database postgres
   railway add --database redis
   ```

5. **Set Environment Variables:**
   - Go to Railway dashboard
   - Click your project → service → "Variables" tab
   - Add all variables (see checklist below)

6. **Deploy:**
   ```bash
   railway up
   ```

### Option 2: Create Project via CLI

Since `railway init` needs interactive input, you can:

1. **Create project in dashboard first:**
   - Go to https://railway.app/dashboard
   - Click "New Project" → "Empty Project"
   - Name it "pm-assistant"

2. **Then link it:**
   ```bash
   railway link
   ```
   Select "pm-assistant" from the list

3. **Continue with steps 4-6 above**

---

## 📋 Environment Variables Checklist

**Generated Secrets (save these!):**
```
SECRET_KEY=c6cd64a1af3ee30054b40fd1670d70e17b7b2165a5692dd786203c7250db5bc0
JWT_SECRET_KEY=c6cd64a1af3ee30054b40fd1670d70e17b7b2165a5692dd786203c7250db5bc0
ENCRYPTION_KEY=F8EaCHwEyPveheimkm5z8UBj1B90LoYzoTyv931BNsM=
```

**Set in Railway Dashboard → Variables:**
- `ENV=production`
- `SECRET_KEY` (use generated value above)
- `JWT_SECRET_KEY` (same as SECRET_KEY)
- `ENCRYPTION_KEY` (use generated value above)
- `OPENAI_API_KEY=sk-your-key`
- `SLACK_CLIENT_ID=your-id` (get from OAuth app)
- `SLACK_CLIENT_SECRET=your-secret` (get from OAuth app)
- `LINEAR_CLIENT_ID=your-id` (get from OAuth app)
- `LINEAR_CLIENT_SECRET=your-secret` (get from OAuth app)
- `GITHUB_CLIENT_ID=your-id` (get from OAuth app)
- `GITHUB_CLIENT_SECRET=your-secret` (get from OAuth app)

**Auto-set by Railway:**
- `DATABASE_URL` (from PostgreSQL)
- `REDIS_URL` (from Redis)
- `PORT` (Railway sets this)

---

## 🎯 Recommended: Use Dashboard

**Easiest path:**
1. Go to https://railway.app/dashboard
2. Create new project
3. Add PostgreSQL and Redis services
4. Set environment variables
5. Deploy via GitHub or CLI

---

**Ready?** Go to Railway dashboard and create your project! 🚀

