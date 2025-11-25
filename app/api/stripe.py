"""Stripe subscription management."""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

try:
    import stripe

    stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
    if stripe_secret_key:
        stripe.api_key = stripe_secret_key
    STRIPE_AVAILABLE = True
    else:
        STRIPE_AVAILABLE = False
        logger.warning("STRIPE_SECRET_KEY not set - Stripe features disabled")
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("stripe package not installed - Stripe features disabled")

from .tenant import get_tenant_id, get_tenant_db, check_subscription
from datetime import datetime, timezone
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

        if not tenant_id:
            logger.error(
                "Stripe webhook: checkout.session.completed missing tenant_id in metadata"
            )
            return {"status": "error", "detail": "Missing tenant_id in metadata"}

        customer_id = session["customer"]
        subscription_id = session["subscription"]

        try:
            # Get subscription details to determine tier
            subscription = stripe.Subscription.retrieve(subscription_id)
            price_id = subscription["items"]["data"][0]["price"]["id"]

            # Map price_id to tier (you'll need to set these in Stripe dashboard)
            # For now, we'll use metadata or price lookup
            # You can store price_id -> tier mapping in env vars or database
            tier = "starter"  # Default to starter
            # Check if it's a scale tier price (you'll need to configure this)
            # You can use Stripe price metadata or compare price_id to known values
            scale_price_ids = [
                pid.strip()
                for pid in os.getenv("STRIPE_SCALE_PRICE_IDS", "").split(",")
                if pid.strip()
            ]
            if price_id in scale_price_ids:
                tier = "scale"

        # Update tenant subscription
        db = TenantDatabase(tenant_id=tenant_id)
        with db._conn() as conn:
            if db.use_postgres:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE tenants 
                    SET subscription_status = 'active',
                            subscription_tier = %s,
                        stripe_customer_id = %s,
                            stripe_subscription_id = %s,
                            trial_ends_at = NULL
                    WHERE id = %s
                """,
                        [tier, customer_id, subscription_id, tenant_id],
                )
            else:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE tenants 
                    SET subscription_status = 'active',
                            subscription_tier = ?,
                        stripe_customer_id = ?,
                            stripe_subscription_id = ?,
                            trial_ends_at = NULL
                    WHERE id = ?
                """,
                        [tier, customer_id, subscription_id, tenant_id],
                    )

            # Log successful subscription activation
            logger.info(
                f"Subscription activated for tenant {tenant_id}: tier={tier}, "
                f"customer={customer_id}, subscription={subscription_id}"
            )

        except Exception as e:
            logger.error(
                f"Error processing checkout.session.completed for tenant {tenant_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail=f"Error processing subscription: {str(e)}"
                )

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        subscription_id = subscription["id"]

        # Find tenant by subscription_id and mark as cancelled
        db = TenantDatabase(tenant_id=None)  # No tenant filter for admin query
        with db._conn() as conn:
            if db.use_postgres:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE tenants 
                    SET subscription_status = 'cancelled',
                        subscription_tier = 'free'
                    WHERE stripe_subscription_id = %s
                """,
                    [subscription_id],
                )
                rows_updated = cursor.rowcount
            else:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE tenants 
                    SET subscription_status = 'cancelled',
                        subscription_tier = 'free'
                    WHERE stripe_subscription_id = ?
                """,
                    [subscription_id],
                )
                rows_updated = cursor.rowcount

            # Log subscription cancellation
            if rows_updated > 0:
                logger.info(
                    f"Subscription cancelled: subscription_id={subscription_id}"
                )
            else:
                logger.warning(
                    f"Subscription cancellation webhook received but no tenant found: subscription_id={subscription_id}"
                )

    return {"status": "success"}


@router.get("/subscription")
async def get_subscription(
    tenant_id: str = Depends(get_tenant_id),
):
    """Get current subscription status with trial information."""
    db = get_tenant_db(tenant_id)
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT subscription_tier, subscription_status, stripe_subscription_id, trial_ends_at FROM tenants WHERE id = %s",
                [tenant_id],
            )
            row = cursor.fetchone()
            if row:
                tier, status, sub_id, trial_ends_at = row
                is_trial_active = False
                days_remaining = None

                if status == "trial" and trial_ends_at:
                    now = datetime.now(timezone.utc)
                    if now < trial_ends_at:
                        is_trial_active = True
                        days_remaining = (trial_ends_at - now).days

                return {
                    "tier": tier or "free",
                    "status": status or "active",
                    "subscription_id": sub_id,
                    "is_trial": status == "trial",
                    "trial_ends_at": (
                        trial_ends_at.isoformat() if trial_ends_at else None
                    ),
                    "is_trial_active": is_trial_active,
                    "trial_days_remaining": days_remaining,
                }
        else:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT subscription_tier, subscription_status, stripe_subscription_id, trial_ends_at FROM tenants WHERE id = ?",
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
                trial_ends_at_str = (
                    row[3] if isinstance(row, tuple) else row.get("trial_ends_at")
                )

                is_trial_active = False
                days_remaining = None

                if status == "trial" and trial_ends_at_str:
                    try:
                        trial_ends_at = datetime.fromisoformat(
                            trial_ends_at_str.replace("Z", "+00:00")
                        )
                        now = datetime.now(timezone.utc)
                        if now < trial_ends_at:
                            is_trial_active = True
                            days_remaining = (trial_ends_at - now).days
                    except (ValueError, AttributeError):
                        pass

                return {
                    "tier": tier or "free",
                    "status": status or "active",
                    "subscription_id": sub_id,
                    "is_trial": status == "trial",
                    "trial_ends_at": trial_ends_at_str,
                    "is_trial_active": is_trial_active,
                    "trial_days_remaining": days_remaining,
                }

    return {"tier": "free", "status": "active", "is_trial": False}
