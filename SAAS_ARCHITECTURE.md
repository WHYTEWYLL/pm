# SaaS Architecture Plan

## Overview
Transform PM Assistant into a multi-tenant SaaS platform with OAuth integrations and subscription management.

## Architecture Components

### 1. Multi-Tenant Database Architecture

#### Option A: Shared Database with Tenant Isolation (Recommended)
- Single database with `tenant_id` on all tables
- Row-level security with tenant_id filtering
- Pros: Easier to manage, lower cost
- Cons: Need careful query filtering

#### Option B: Separate Database per Tenant
- Each tenant gets their own database
- Pros: Complete isolation, easier backups
- Cons: More complex, higher cost

**Recommendation**: Start with Option A, migrate to Option B for enterprise customers.

### 2. Authentication & OAuth Flow

#### User Authentication
- Use service like Auth0, Clerk, or Supabase Auth
- JWT tokens for API authentication
- Session management for web app

#### OAuth Integrations (Like Zapier)

**Slack OAuth:**
```
1. User clicks "Connect Slack"
2. Redirect to Slack OAuth URL with:
   - client_id
   - redirect_uri
   - scope: channels:read, chat:read, im:read, mpim:read
3. User authorizes
4. Slack redirects back with code
5. Exchange code for access_token + refresh_token
6. Store tokens encrypted in database (tenant-specific)
```

**Linear OAuth:**
```
1. User clicks "Connect Linear"
2. Redirect to Linear OAuth URL
3. User authorizes
4. Get access_token
5. Store encrypted (Linear tokens are long-lived)
```

**GitHub OAuth:**
```
1. User clicks "Connect GitHub"
2. Redirect to GitHub OAuth URL
3. User authorizes
4. Get access_token + refresh_token
5. Store encrypted
```

### 3. Data Storage Structure

```sql
-- Users/Tenants table
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    subscription_tier TEXT, -- free, pro, enterprise
    subscription_status TEXT, -- active, cancelled, expired
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- OAuth credentials (encrypted)
CREATE TABLE oauth_credentials (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    service TEXT NOT NULL, -- slack, linear, github
    access_token TEXT NOT NULL, -- encrypted
    refresh_token TEXT, -- encrypted
    token_expires_at TIMESTAMP,
    workspace_id TEXT, -- slack workspace, linear team, github org
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(tenant_id, service, workspace_id)
);

-- All existing tables need tenant_id
ALTER TABLE messages ADD COLUMN tenant_id UUID REFERENCES tenants(id);
ALTER TABLE linear_issues ADD COLUMN tenant_id UUID;
ALTER TABLE github_prs ADD COLUMN tenant_id UUID;
ALTER TABLE decision_logs ADD COLUMN tenant_id UUID;
```

### 4. API Architecture

#### REST API (FastAPI/Flask)
```
POST /api/v1/oauth/slack/authorize
POST /api/v1/oauth/slack/callback
GET  /api/v1/integrations/slack/status
POST /api/v1/ingestion/slack
POST /api/v1/workflows/standup
GET  /api/v1/decision-logs
```

#### Web Application
- React/Next.js frontend
- Dashboard for:
  - OAuth connections status
  - Workflow configuration
  - View decision logs
  - Subscription management

### 5. Subscription & Payment

#### Options:
1. **Stripe** (Recommended)
   - Subscription management
   - Webhooks for payment events
   - Multiple pricing tiers

2. **Paddle**
   - Alternative to Stripe
   - Handles taxes automatically

#### Pricing Tiers:
```python
PRICING_TIERS = {
    "free": {
        "price": 0,
        "features": ["1 integration", "100 messages/month", "Basic workflows"]
    },
    "pro": {
        "price": 29,  # per month
        "features": ["Unlimited integrations", "Unlimited messages", "All workflows", "Priority support"]
    },
    "enterprise": {
        "price": 99,
        "features": ["Everything in Pro", "Custom workflows", "Dedicated support", "SLA"]
    }
}
```

### 6. Deployment Architecture

#### Option A: Serverless (Recommended for MVP)
```
- Frontend: Vercel/Netlify
- API: AWS Lambda / Vercel Serverless Functions
- Database: Supabase / PlanetScale / Neon
- Queue: AWS SQS / Inngest for background jobs
- Storage: S3 for logs/backups
```

#### Option B: Containerized
```
- Frontend: Docker container on Vercel/Railway
- API: Docker containers on Railway/Render/Fly.io
- Database: Managed PostgreSQL (Supabase/Neon)
- Queue: Redis + Celery or Inngest
```

### 7. Background Jobs

#### Workflow Execution
- Use job queue (Inngest, Celery, or AWS EventBridge)
- Scheduled jobs for daily ingestion
- User-triggered workflows via API

```python
# Example with Inngest
@inngest.create_function(
    id="daily-ingestion",
    trigger=inngest.TriggerEvent(event="daily/ingestion"),
)
async def daily_ingestion(event: InngestEvent):
    tenant_id = event.data["tenant_id"]
    # Run ingestion for this tenant
    await ingest_all_sources(tenant_id)
```

### 8. Security Considerations

1. **Encryption at Rest**
   - Encrypt OAuth tokens (use AWS KMS, Hashicorp Vault, or libsodium)
   - Encrypt sensitive data in database

2. **Encryption in Transit**
   - HTTPS everywhere
   - API authentication with JWT

3. **Row-Level Security**
   - All queries must filter by tenant_id
   - Use middleware to inject tenant_id

4. **Rate Limiting**
   - Per-tenant rate limits
   - Protect against abuse

### 9. Configuration Management

#### Per-Tenant Configuration
```python
# Store in database
CREATE TABLE tenant_configs (
    tenant_id UUID PRIMARY KEY REFERENCES tenants(id),
    slack_channels JSONB, -- List of channel IDs
    linear_team_id TEXT,
    github_orgs JSONB,
    workflow_settings JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 10. Monitoring & Observability

- **Error Tracking**: Sentry
- **Logging**: Logtail / Datadog
- **Analytics**: PostHog / Mixpanel
- **Metrics**: Prometheus / DataDog

## Implementation Phases

### Phase 1: MVP (2-3 weeks)
1. Add tenant_id to all tables
2. Implement OAuth for Slack, Linear, GitHub
3. Basic multi-tenant API
4. Stripe subscription integration
5. Simple web dashboard

### Phase 2: Production Ready (4-6 weeks)
1. Encryption for OAuth tokens
2. Background job system
3. Email notifications
4. Admin dashboard
5. Error handling & monitoring

### Phase 3: Scale (Ongoing)
1. Performance optimization
2. Caching layer (Redis)
3. Advanced analytics
4. Enterprise features
5. Mobile app (optional)

## Tech Stack Recommendations

### Backend
- **FastAPI** - Modern Python API framework
- **SQLAlchemy** - ORM with multi-tenant support
- **Pydantic** - Data validation
- **Stripe** - Payments
- **Inngest** - Background jobs

### Frontend
- **Next.js** - React framework
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **React Query** - Data fetching

### Database
- **PostgreSQL** - Primary database (Supabase/Neon)
- **Redis** - Caching & sessions

### Authentication
- **Clerk** or **Supabase Auth** - User auth
- **Custom OAuth** - Service integrations

## Next Steps

1. Create database migration script for multi-tenant
2. Set up OAuth apps for Slack, Linear, GitHub
3. Implement tenant isolation middleware
4. Build basic web dashboard
5. Integrate Stripe
6. Set up deployment pipeline

