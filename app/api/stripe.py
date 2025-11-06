"""Stripe subscription management."""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
import os

try:
    import stripe

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

from .tenant import get_tenant_id, get_tenant_db, check_subscription
from ..storage.tenant_db import TenantDatabase

router = APIRouter(prefix="/stripe", tags=["stripe"])


@router.post("/create-checkout")
async def create_checkout_session(
    price_id: str,
    tenant_id: str = Depends(get_tenant_id),
):
    """
    Create Stripe checkout session for subscription.
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Stripe not available")
    try:
        db = get_tenant_db(tenant_id)

        # Get tenant email
        with db._conn() as conn:
            if db.use_postgres:
                cursor = conn.cursor()
                cursor.execute("SELECT email FROM tenants WHERE id = %s", [tenant_id])
                row = cursor.fetchone()
                email = row[0] if row else None
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT email FROM tenants WHERE id = ?", [tenant_id])
                row = cursor.fetchone()
                email = (
                    row[0] if isinstance(row, tuple) else row["email"] if row else None
                )

        checkout_session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=f"{os.getenv('APP_URL', 'http://localhost:3000')}/dashboard?success=true",
            cancel_url=f"{os.getenv('APP_URL', 'http://localhost:3000')}/dashboard?canceled=true",
            metadata={
                "tenant_id": tenant_id,
            },
        )

        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Stripe not available")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        tenant_id = session["metadata"].get("tenant_id")
        customer_id = session["customer"]
        subscription_id = session["subscription"]

        # Update tenant subscription
        db = TenantDatabase(tenant_id=tenant_id)
        with db._conn() as conn:
            if db.use_postgres:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE tenants 
                    SET subscription_status = 'active',
                        stripe_customer_id = %s,
                        stripe_subscription_id = %s
                    WHERE id = %s
                """,
                    [customer_id, subscription_id, tenant_id],
                )
            else:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE tenants 
                    SET subscription_status = 'active',
                        stripe_customer_id = ?,
                        stripe_subscription_id = ?
                    WHERE id = ?
                """,
                    [customer_id, subscription_id, tenant_id],
                )

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        # Find tenant by subscription_id and mark as cancelled
        # Implementation depends on your database structure

    return {"status": "success"}


@router.get("/subscription")
async def get_subscription(
    tenant_id: str = Depends(get_tenant_id),
):
    """Get current subscription status."""
    db = get_tenant_db(tenant_id)
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT subscription_tier, subscription_status, stripe_subscription_id FROM tenants WHERE id = %s",
                [tenant_id],
            )
            row = cursor.fetchone()
            if row:
                tier, status, sub_id = row
                return {
                    "tier": tier,
                    "status": status,
                    "subscription_id": sub_id,
                }
        else:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT subscription_tier, subscription_status, stripe_subscription_id FROM tenants WHERE id = ?",
                [tenant_id],
            )
            row = cursor.fetchone()
            if row:
                tier = row[0] if isinstance(row, tuple) else row["subscription_tier"]
                status = (
                    row[1] if isinstance(row, tuple) else row["subscription_status"]
                )
                sub_id = (
                    row[2]
                    if isinstance(row, tuple)
                    else row.get("stripe_subscription_id")
                )
                return {
                    "tier": tier,
                    "status": status,
                    "subscription_id": sub_id,
                }

    return {"tier": "free", "status": "active"}
