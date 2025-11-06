# PM Assistant - Multi-Tenant SaaS Platform

AI-powered project management assistant that integrates Slack, Linear, and GitHub to automate ticket management, conversation tracking, and daily standup generation.

## 🎯 How It Works

**Multi-Tenant SaaS Architecture:**
1. **Users sign up** → Create account, automatically get their own tenant
2. **Users connect services** → OAuth flows (Slack, Linear, GitHub)
3. **Backend runs workflows** → Automatically for all active tenants
4. **Scheduled ingestion** → Daily at 9 AM UTC for all users
5. **Tenant isolation** → Each user's data is completely separate

**User Flow:**
- Register → Login → Connect Services → Workflows run automatically

---

## 🚀 Quick Start (Local Development)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up .env file with your credentials
# SLACK_TOKEN=xoxp-...
# LINEAR_API_KEY=lin_api_...
# OPENAI_API_KEY=sk-...

# 3. Start the server
export ENV=development
python3 -m uvicorn app.api.main:app --reload --port 8000

# 4. Setup local tenant (uses your env vars)
curl -X POST "http://localhost:8000/local-dev/setup-tenant?tenant_id=local-dev-tenant"

# 5. Test registration
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123", "full_name": "Test"}'
```

---

## 🚀 Deploy to Production (Railway)

See **[RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)** for complete deployment guide.

**Quick deploy:**
```bash
railway login
railway init
railway add postgresql
railway add redis
railway variables set ENV=production ...
railway up
```

---

## 📦 Core Features

### Authentication
- User registration and login
- JWT token-based authentication
- Password reset flow
- Email verification (structure ready)

### OAuth Integration
- Slack OAuth flow
- Linear OAuth flow
- GitHub OAuth flow
- Encrypted token storage

### Workflows
- **Slack Ingestion**: Fetch messages from last 24h
- **Linear Ingestion**: Fetch issues with parent-child structure
- **Standup**: Daily status report with tickets and untracked conversations
- **Process Messages**: AI analyzes and matches conversations to tickets
- **Move Tickets**: Analyzes conversations to move tickets based on status

### Background Jobs
- Scheduled daily ingestion (9 AM UTC)
- Runs for all active tenants automatically
- Celery workers for async processing

---

## 🏗️ Architecture

```
app/
├── api/              # FastAPI REST API
│   ├── auth.py      # User authentication
│   ├── oauth.py     # OAuth flows
│   ├── workflows.py # Workflow endpoints
│   └── tenant.py    # Tenant management
│
├── ingestion/        # Data sources
│   ├── slack.py     # Slack API
│   ├── linear.py    # Linear API
│   └── github.py    # GitHub API
│
├── workflows/        # Business logic
│   ├── process.py   # AI-powered processing
│   └── dev/
│       ├── standup.py      # Standup generation
│       └── move_tickets.py # Ticket management
│
├── storage/          # Database layer
│   ├── tenant_db.py # Multi-tenant database
│   └── encryption.py # Token encryption
│
├── jobs/             # Background jobs
│   └── ingestion.py  # Scheduled tasks
│
└── ai/               # AI/LLM
    └── analyzer.py  # Message analysis
```

---

## 📚 Documentation

- **[STATUS.md](STATUS.md)** - Current project status and roadmap
- **[RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)** - Complete Railway deployment guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture
- **[SAAS_ARCHITECTURE.md](SAAS_ARCHITECTURE.md)** - SaaS platform architecture

---

## 🔗 API Endpoints

**Authentication:**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (returns JWT)
- `GET /api/auth/me` - Get current user

**OAuth:**
- `GET /api/oauth/{service}/authorize` - Start OAuth flow
- `GET /api/oauth/{service}/callback` - OAuth callback
- `GET /api/oauth/{service}/status` - Check connection

**Workflows:**
- `POST /api/workflows/ingest/slack` - Ingest Slack
- `POST /api/workflows/ingest/linear` - Ingest Linear
- `GET /api/workflows/standup` - Get standup
- `POST /api/workflows/process` - Process messages
- `POST /api/workflows/move-tickets` - Move tickets

---

## 🎯 Key Technologies

- **Backend**: Python 3.9+, FastAPI, SQLite/PostgreSQL
- **AI**: OpenAI GPT-4
- **APIs**: Slack API, Linear API, GitHub API
- **Background Jobs**: Celery, Redis
- **Authentication**: JWT, OAuth 2.0
- **Database**: Multi-tenant with tenant isolation

---

## 🔐 Security

- Multi-tenant architecture with complete data isolation
- OAuth tokens encrypted at rest
- JWT tokens with 30-day expiration
- Passwords hashed with bcrypt
- All workflows are tenant-scoped

---

**Ready to deploy?** See [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) 🚀
