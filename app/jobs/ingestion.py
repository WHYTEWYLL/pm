"""Background jobs for scheduled ingestion."""

from celery import Celery
import os
from ..storage.tenant_db import TenantDatabase
from ..storage.encryption import decrypt_token
from ..ingestion.slack import SlackService
from ..ingestion.linear import LinearClient

# Initialize Celery
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("pm_assistant", broker=redis_url, backend=redis_url)


@celery_app.task
def ingest_slack_for_tenant(tenant_id: str):
    """Ingest Slack messages for a specific tenant."""
    try:
        db = TenantDatabase(tenant_id=tenant_id)
        creds = db.get_oauth_credentials("slack")
        
        if not creds:
            return {"status": "error", "message": "Slack not connected"}
        
        config = db.get_tenant_config()
        target_channel_ids = config.get("slack_target_channel_ids", []) if config else []
        
        token = decrypt_token(creds["access_token"])
        service = SlackService(token=token)
        
        result = service.ingest(
            include_threads=True,
            target_channel_ids=target_channel_ids,
            force_last_24h=True,
        )
        
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@celery_app.task
def ingest_linear_for_tenant(tenant_id: str):
    """Ingest Linear issues for a specific tenant."""
    try:
        db = TenantDatabase(tenant_id=tenant_id)
        creds = db.get_oauth_credentials("linear")
        
        if not creds:
            return {"status": "error", "message": "Linear not connected"}
        
        token = decrypt_token(creds["access_token"])
        linear = LinearClient(token=token)
        
        result = linear.ingest()
        
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@celery_app.task
def daily_ingestion_for_all_tenants():
    """Run daily ingestion for all active tenants."""
    # Get all active tenants
    db = TenantDatabase(tenant_id=None)  # No tenant filter for admin query
    
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id FROM tenants 
                WHERE subscription_status IN ('active', 'trial')
                AND (trial_ends_at IS NULL OR trial_ends_at > CURRENT_TIMESTAMP)
                """
            )
            tenant_ids = [row[0] for row in cursor.fetchall()]
        else:
            cursor = conn.cursor()
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                """
                SELECT id FROM tenants 
                WHERE subscription_status IN ('active', 'trial')
                AND (trial_ends_at IS NULL OR trial_ends_at > ?)
                """,
                [now],
            )
            tenant_ids = [row[0] if isinstance(row, tuple) else row["id"] for row in cursor.fetchall()]
    
    # Schedule ingestion for each tenant
    for tenant_id in tenant_ids:
        ingest_slack_for_tenant.delay(tenant_id)
        ingest_linear_for_tenant.delay(tenant_id)
    
    return {"status": "scheduled", "tenants": len(tenant_ids)}


@celery_app.task
def expire_trials():
    """Expire trials that have passed their end date."""
    from datetime import datetime, timezone
    
    db = TenantDatabase(tenant_id=None)  # No tenant filter for admin query
    
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            # Find all tenants with expired trials
            cursor.execute(
                """
                SELECT id FROM tenants 
                WHERE subscription_status = 'trial'
                AND trial_ends_at IS NOT NULL
                AND trial_ends_at < %s
                """,
                [datetime.now(timezone.utc)],
            )
            expired_tenant_ids = [row[0] for row in cursor.fetchall()]
            
            # Update expired trials
            if expired_tenant_ids:
                for tenant_id in expired_tenant_ids:
                    cursor.execute(
                        """
                        UPDATE tenants 
                        SET subscription_status = 'expired',
                            subscription_tier = 'free'
                        WHERE id = %s
                        """,
                        [tenant_id],
                    )
        else:
            cursor = conn.cursor()
            # Find all tenants with expired trials
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                """
                SELECT id FROM tenants 
                WHERE subscription_status = 'trial'
                AND trial_ends_at IS NOT NULL
                AND trial_ends_at < ?
                """,
                [now],
            )
            expired_tenant_ids = [row[0] if isinstance(row, tuple) else row["id"] for row in cursor.fetchall()]
            
            # Update expired trials
            if expired_tenant_ids:
                placeholders = ",".join("?" * len(expired_tenant_ids))
                cursor.execute(
                    f"""
                    UPDATE tenants 
                    SET subscription_status = 'expired',
                        subscription_tier = 'free'
                    WHERE id IN ({placeholders})
                    """,
                    expired_tenant_ids,
                )
    
    return {"status": "success", "expired_count": len(expired_tenant_ids) if expired_tenant_ids else 0}


# Schedule daily ingestion (runs at 9 AM UTC)
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "daily-ingestion": {
        "task": "app.jobs.ingestion.daily_ingestion_for_all_tenants",
        "schedule": crontab(hour=9, minute=0),
    },
    "expire-trials": {
        "task": "app.jobs.ingestion.expire_trials",
        "schedule": crontab(hour=0, minute=0),  # Run daily at midnight UTC
    },
}

