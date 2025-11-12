# Stripe Integration Setup Guide

## Overview

This guide will help you set up Stripe for subscription management in your PM Assistant platform.

## Step 1: Get Your Stripe API Keys

1. Go to [Stripe Dashboard > API Keys](https://dashboard.stripe.com/test/apikeys)
2. Copy your **Publishable Key** (starts with `pk_test_...`)
3. Copy your **Secret Key** (starts with `sk_test_...`)

⚠️ **Important**: 
- These are **test keys** for development. 
- For production, you'll need to get live keys from your Stripe dashboard (switch to "Live mode").
- **Never commit API keys to version control** - always use environment variables.

## Step 2: Create Products and Prices in Stripe

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/test/products)
2. Click "Add product"
3. Create two products:

### Starter Plan
- **Name**: Starter Plan
- **Description**: Perfect for seed-stage teams getting their PM workflows under control.
- **Pricing**: 
  - Type: Recurring
  - Price: $99.00 USD
  - Billing period: Monthly
- **Save** and copy the **Price ID** (starts with `price_...`)

### Scale Plan
- **Name**: Scale Plan
- **Description**: For product teams managing multiple squads with enterprise-grade guardrails.
- **Pricing**:
  - Type: Recurring
  - Price: $249.00 USD
  - Billing period: Monthly
- **Save** and copy the **Price ID** (starts with `price_...`)

## Step 3: Set Up Environment Variables

### Backend (.env or Railway variables)

```bash
# Stripe Configuration
# Get your secret key from: https://dashboard.stripe.com/test/apikeys
STRIPE_SECRET_KEY=sk_test_...  # Your Stripe secret key from dashboard

# Comma-separated list of Scale tier price IDs
# Example: STRIPE_SCALE_PRICE_IDS=price_abc123,price_def456
STRIPE_SCALE_PRICE_IDS=<your_scale_price_id>

# Webhook secret (you'll get this after setting up webhook)
STRIPE_WEBHOOK_SECRET=whsec_...

# App URL for redirects
APP_URL=http://localhost:3000  # or your production URL
```

### Frontend (.env.local)

Create `frontend/.env.local`:

```bash
# API URL
NEXT_PUBLIC_API_URL=http://localhost:8000  # or your production API URL

# Stripe Price IDs (from Step 2)
NEXT_PUBLIC_STRIPE_STARTER_PRICE_ID=<your_starter_price_id>
NEXT_PUBLIC_STRIPE_SCALE_PRICE_ID=<your_scale_price_id>
```

## Step 4: Set Up Stripe Webhook

### For Local Development (using Stripe CLI)

1. Install [Stripe CLI](https://stripe.com/docs/stripe-cli)
2. Login: `stripe login`
3. Forward webhooks to your local server:
   ```bash
   stripe listen --forward-to localhost:8000/stripe/webhook
   ```
4. Copy the webhook signing secret (starts with `whsec_...`) and add it to your `.env` as `STRIPE_WEBHOOK_SECRET`

### For Production

1. Go to [Stripe Dashboard > Webhooks](https://dashboard.stripe.com/test/webhooks)
2. Click "Add endpoint"
3. Set endpoint URL: `https://yourdomain.com/stripe/webhook`
4. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.deleted`
5. Copy the webhook signing secret and add it to your production environment variables

## Step 5: Install Frontend Dependencies

```bash
cd frontend
npm install
```

This will install `@stripe/stripe-js` which is already added to `package.json`.

## Step 6: Test the Integration

### 1. Test Registration (Creates Trial)
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123", "full_name": "Test User"}'
```

### 2. Test Subscription Status
```bash
curl -H "Authorization: Bearer <your_jwt_token>" \
  http://localhost:8000/stripe/subscription
```

### 3. Test Checkout Session Creation
```bash
curl -X POST "http://localhost:8000/stripe/create-checkout?price_id=<your_starter_price_id>" \
  -H "Authorization: Bearer <your_jwt_token>"
```

### 4. Test in Frontend
1. Start your frontend: `cd frontend && npm run dev`
2. Register a new account
3. Go to `/pricing` page
4. Click "Subscribe" on a plan
5. Complete the Stripe checkout (use test card: `4242 4242 4242 4242`)
6. Verify subscription status in dashboard

## Test Cards

Use these test cards in Stripe Checkout:

- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **Requires Authentication**: `4000 0025 0000 3155`

Use any future expiry date, any CVC, and any ZIP code.

## Production Checklist

Before going live:

- [ ] Switch to live Stripe keys (get from Stripe Dashboard)
- [ ] Create live products and prices in Stripe
- [ ] Set up production webhook endpoint
- [ ] Update `APP_URL` to production URL
- [ ] Update `NEXT_PUBLIC_API_URL` to production API URL
- [ ] Test complete subscription flow in production
- [ ] Set up monitoring for webhook failures
- [ ] Configure email notifications in Stripe for subscription events

## Troubleshooting

### Webhook Not Working
- Check webhook secret matches in environment variables
- Verify webhook endpoint is accessible
- Check Stripe dashboard for webhook delivery logs
- Use Stripe CLI to test webhooks locally

### Price ID Not Found
- Verify price IDs are correct in environment variables
- Check that prices are active in Stripe dashboard
- Ensure you're using test keys with test prices (or live keys with live prices)

### Checkout Redirect Issues
- Verify `APP_URL` is set correctly
- Check that success/cancel URLs are accessible
- Ensure CORS is configured for your frontend domain

## Support

For Stripe-specific issues, check:
- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Support](https://support.stripe.com/)

For application-specific issues, check:
- `SUBSCRIPTION_SYSTEM.md` for system architecture
- Backend logs for error messages
- Frontend browser console for client-side errors

