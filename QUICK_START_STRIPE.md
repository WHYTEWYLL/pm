# Quick Start: Stripe Integration

## 🚀 Quick Setup (5 minutes)

### 1. Set Backend Environment Variables

Add to your `.env` file or Railway variables:

```bash
# Get your Stripe API keys from: https://dashboard.stripe.com/test/apikeys
STRIPE_SECRET_KEY=sk_test_...  # Your Stripe secret key from dashboard
STRIPE_SCALE_PRICE_IDS=  # You'll set this after creating prices in Stripe
STRIPE_WEBHOOK_SECRET=   # You'll get this from Stripe CLI or dashboard
APP_URL=http://localhost:3000
```

### 2. Create Products in Stripe Dashboard

1. Go to https://dashboard.stripe.com/test/products
2. Create **Starter** product: $99/month recurring
3. Create **Scale** product: $249/month recurring
4. Copy the **Price IDs** (start with `price_...`)

### 3. Set Frontend Environment Variables

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_STARTER_PRICE_ID=<paste_starter_price_id>
NEXT_PUBLIC_STRIPE_SCALE_PRICE_ID=<paste_scale_price_id>
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 5. Set Up Webhook (Local Development)

```bash
# Install Stripe CLI: https://stripe.com/docs/stripe-cli
stripe login
stripe listen --forward-to localhost:8000/stripe/webhook
# Copy the webhook secret (whsec_...) and add to STRIPE_WEBHOOK_SECRET
```

### 6. Test It!

1. Start backend: `python -m uvicorn app.api.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Register a new account → Gets 7-day trial
4. Go to `/pricing` → Click "Subscribe"
5. Use test card: `4242 4242 4242 4242`

## ✅ What's Included

- ✅ Subscription buttons on pricing page
- ✅ Subscription status display in dashboard
- ✅ Trial countdown and upgrade prompts
- ✅ Stripe Checkout integration
- ✅ Webhook handling for subscription events
- ✅ Automatic tier assignment

## 📚 Full Documentation

See `STRIPE_SETUP.md` for detailed instructions and troubleshooting.

