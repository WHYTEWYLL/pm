# Subscription & Trial System

## Overview

The platform now includes a comprehensive subscription management system with:
- **7-day free trial** for all new users
- **Stripe-powered subscriptions** (Starter and Scale tiers)
- **Automatic trial expiration**
- **Tier-based feature access control**

## How It Works

### 1. Registration & Trial

When a user registers:
- A tenant is created with `subscription_status = "trial"`
- `trial_ends_at` is set to 7 days from registration
- `subscription_tier = "free"` (default)

### 2. Subscription Statuses

- **`trial`**: User is in their 7-day free trial period
- **`active`**: User has an active paid subscription via Stripe
- **`cancelled`**: User cancelled their subscription
- **`expired`**: Trial expired without subscription

### 3. Subscription Tiers

- **`free`**: No active subscription (trial expired or cancelled)
- **`starter`**: $99/month - Basic features
- **`scale`**: $249/month - All features including GitHub integration

### 4. Access Control

#### Subscription Check (`check_subscription()`)
- Returns `True` if:
  - Status is `active` (paid subscription)
  - Status is `trial` AND `trial_ends_at` hasn't passed
- Returns `False` otherwise

#### Tier-Based Access (`check_tier_access()`)
- Checks if tenant has access to tier-specific features
- Hierarchy: `free < starter < scale`
- Example: GitHub ingestion requires `scale` tier

### 5. Stripe Integration

#### Creating Checkout Session
- Endpoint: `POST /stripe/create-checkout`
- Requires `price_id` parameter
- Creates Stripe checkout session with tenant metadata

#### Webhook Events

**`checkout.session.completed`**:
- Retrieves subscription details from Stripe
- Maps `price_id` to tier (via `STRIPE_SCALE_PRICE_IDS` env var)
- Updates tenant:
  - `subscription_status = "active"`
  - `subscription_tier = "starter"` or `"scale"`
  - `stripe_customer_id` and `stripe_subscription_id`
  - `trial_ends_at = NULL`

**`customer.subscription.deleted`**:
- Updates tenant:
  - `subscription_status = "cancelled"`
  - `subscription_tier = "free"`

#### Subscription Status Endpoint
- Endpoint: `GET /stripe/subscription`
- Returns:
  - Current tier and status
  - Trial information (if applicable)
  - Days remaining in trial
  - Whether trial is active

### 6. Background Jobs

#### Data Sync (Hourly & Daily)
- Runs hourly and daily for all active tenants
- Syncs Slack messages, Linear tickets, and GitHub (Scale tier)
- Located in `app/jobs/sync.py`

#### Morning Standups
- Runs daily at 9 AM UTC
- Sends standup DMs to developers with `daily_standup` enabled
- Located in `app/jobs/scheduled_workflows.py`

#### Trial Expiration
- **No background job needed** - trial access is checked at runtime
- `check_subscription()` compares `trial_ends_at` timestamp against current time
- Expired trials are automatically denied access without needing status updates

#### Daily Ingestion
- Only runs for tenants with:
  - `subscription_status IN ('active', 'trial')`
  - `trial_ends_at` hasn't passed (if trial)

## Feature Access by Tier

### Starter Tier ($99/month)
- ✅ Slack + Linear integrations
- ✅ Daily standup and ticket hygiene workflows
- ✅ Decision logging & audit trails
- ❌ GitHub ingestion (Scale only)

### Scale Tier ($249/month)
- ✅ Everything in Starter
- ✅ GitHub ingestion and PR insights
- ✅ Weekly wins digest + incident retros
- ✅ Priority support & onboarding

## Environment Variables

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_SCALE_PRICE_IDS=price_xxx,price_yyy  # Comma-separated list of Scale tier price IDs
```

## Database Schema

### `tenants` table additions:
- `trial_ends_at TIMESTAMP` - When the trial expires
- `subscription_tier TEXT` - Current tier (free, starter, scale)
- `subscription_status TEXT` - Current status (trial, active, cancelled, expired)
- `stripe_customer_id TEXT` - Stripe customer ID
- `stripe_subscription_id TEXT` - Stripe subscription ID

## Migration

Run the migration to add `trial_ends_at` field:
```sql
-- See migrations/003_add_trial_support.sql
```

## API Endpoints

### Subscription Management
- `GET /stripe/subscription` - Get current subscription status
- `POST /stripe/create-checkout?price_id=...` - Create Stripe checkout
- `POST /stripe/webhook` - Stripe webhook handler

### Protected Endpoints
All workflow endpoints check subscription:
- `POST /api/workflows/ingest/slack` - Requires active subscription or trial
- `POST /api/workflows/ingest/linear` - Requires active subscription or trial
- `POST /api/workflows/ingest/github` - Requires Scale tier
- `GET /api/workflows/standup` - Requires active subscription or trial

## Frontend Integration

The pricing page (`/pricing`) now displays:
- Free trial notice
- Starter and Scale tier details
- Call-to-action for subscription

## Testing

1. **Test Trial Registration**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "testpass123", "full_name": "Test"}'
   ```

2. **Check Subscription Status**:
   ```bash
   curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/stripe/subscription
   ```

3. **Test Stripe Checkout**:
   ```bash
   curl -X POST "http://localhost:8000/stripe/create-checkout?price_id=price_xxx" \
     -H "Authorization: Bearer <token>"
   ```

## Next Steps

1. **Configure Stripe Prices**:
   - Create Starter tier price in Stripe dashboard
   - Create Scale tier price in Stripe dashboard
   - Set `STRIPE_SCALE_PRICE_IDS` env var with Scale price IDs

2. **Set Up Webhook**:
   - Configure Stripe webhook endpoint: `https://yourdomain.com/stripe/webhook`
   - Subscribe to events: `checkout.session.completed`, `customer.subscription.deleted`

3. **Update Frontend**:
   - Add subscription status display in dashboard
   - Add upgrade prompts for trial users
   - Add tier-based feature gating in UI

