"""Scheduled workflow tasks - standup reminders and other automated workflows."""

import logging
import os
from typing import Dict, List, Any

from .celery import celery_app
from .sync import get_workflow_settings, get_active_tenants, log_activity
from ..storage.tenant_db import TenantDatabase
from ..storage.encryption import decrypt_token

logger = logging.getLogger("jobs.scheduled_workflows")


def get_tenant_dev_users(tenant_id: str) -> List[Dict[str, Any]]:
    """Get all developer users for a tenant (users with dev view)."""
    db = TenantDatabase(tenant_id=tenant_id)

    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, email, full_name, default_view
                FROM users 
                WHERE tenant_id = %s
                AND default_view = 'dev'
                """,
                [tenant_id],
            )
            columns = ["id", "email", "full_name", "default_view"]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, email, full_name, default_view
                FROM users 
                WHERE tenant_id = ?
                AND default_view = 'dev'
                """,
                [tenant_id],
            )
            rows = cursor.fetchall()
            if rows and isinstance(rows[0], tuple):
                columns = ["id", "email", "full_name", "default_view"]
                return [dict(zip(columns, row)) for row in rows]
            return [dict(row) for row in rows]


@celery_app.task(bind=True, max_retries=2)
def send_standup_dm_for_user(self, tenant_id: str, user_email: str):
    """Send daily standup DM to a specific user."""
    try:
        db = TenantDatabase(tenant_id=tenant_id)

        # Check Slack connection
        slack_creds = db.get_oauth_credentials("slack")
        if not slack_creds:
            return {"status": "skipped", "reason": "Slack not connected"}

        # Check Linear connection
        linear_creds = db.get_oauth_credentials("linear")
        if not linear_creds:
            return {"status": "skipped", "reason": "Linear not connected"}

        # Set tenant context
        os.environ["CURRENT_TENANT_ID"] = tenant_id

        # Decrypt tokens
        slack_token = decrypt_token(slack_creds["access_token"])
        linear_token = decrypt_token(linear_creds["access_token"])

        # Get config for Linear team
        config = db.get_tenant_config()
        team_id = config.get("linear_team_id") if config else None

        # Import and send standup DM
        from .workflows.standup import send_standup_dm

        result = send_standup_dm(
            user_email=user_email,
            slack_token=slack_token,
            linear_api_key=linear_token,
            linear_team_id=team_id,
        )

        if result.get("status") == "success":
            # Log activity
            log_activity(
                tenant_id,
                "post",
                f"Sent morning reminder to {user_email}",
                {"user_email": user_email, "in_progress": result.get("in_progress", 0)},
            )

        logger.info(f"Standup DM sent to {user_email} for tenant {tenant_id}")
        return result

    except Exception as e:
        logger.exception(
            f"Failed to send standup DM to {user_email} for tenant {tenant_id}"
        )
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes


@celery_app.task(bind=True, max_retries=2)
def send_standups_for_tenant(self, tenant_id: str):
    """Send daily standups to all dev users in a tenant."""
    try:
        # Check workflow settings
        settings = get_workflow_settings(tenant_id)
        if not settings.get("daily_standup", False):
            logger.info(
                f"Skipping standups for tenant {tenant_id} - daily_standup disabled"
            )
            return {"status": "skipped", "reason": "daily_standup disabled"}

        # Get all dev users for this tenant
        dev_users = get_tenant_dev_users(tenant_id)

        if not dev_users:
            return {"status": "skipped", "reason": "No dev users found"}

        # Queue standup DM for each dev user
        scheduled = 0
        for user in dev_users:
            user_email = user.get("email")
            if user_email:
                send_standup_dm_for_user.delay(tenant_id, user_email)
                scheduled += 1

        logger.info(f"Scheduled standups for {scheduled} devs in tenant {tenant_id}")
        return {"status": "scheduled", "users": scheduled}

    except Exception as e:
        logger.exception(f"Failed to schedule standups for tenant {tenant_id}")
        raise self.retry(exc=e, countdown=300)


@celery_app.task
def send_morning_standups_for_all_tenants():
    """Send morning standup DMs for all active tenants with the feature enabled."""
    tenant_ids = get_active_tenants()

    scheduled = 0
    for tenant_id in tenant_ids:
        settings = get_workflow_settings(tenant_id)
        if settings.get("daily_standup", False):
            send_standups_for_tenant.delay(tenant_id)
            scheduled += 1

    logger.info(f"Morning standups scheduled for {scheduled} tenants")
    return {"status": "scheduled", "tenants": scheduled}


@celery_app.task(bind=True, max_retries=2)
def post_priorities_to_slack_for_tenant(self, tenant_id: str, channel_id: str = None):
    """Post developer priorities to Slack channel for a specific tenant."""
    try:
        db = TenantDatabase(tenant_id=tenant_id)

        # Check Slack connection
        slack_creds = db.get_oauth_credentials("slack")
        if not slack_creds:
            return {"status": "skipped", "reason": "Slack not connected"}

        # Check Linear connection
        linear_creds = db.get_oauth_credentials("linear")
        if not linear_creds:
            return {"status": "skipped", "reason": "Linear not connected"}

        # Set tenant context
        os.environ["CURRENT_TENANT_ID"] = tenant_id

        # Decrypt tokens
        slack_token = decrypt_token(slack_creds["access_token"])
        linear_token = decrypt_token(linear_creds["access_token"])

        # Get config
        config = db.get_tenant_config()
        team_id = config.get("linear_team_id") if config else None

        # Get target channel from config if not provided
        if not channel_id:
            target_channel_ids = (
                config.get("slack_target_channel_ids", []) if config else []
            )
            if isinstance(target_channel_ids, str):
                import json

                try:
                    target_channel_ids = json.loads(target_channel_ids)
                except json.JSONDecodeError:
                    target_channel_ids = []

            if not target_channel_ids:
                return {"status": "skipped", "reason": "No target channel configured"}
            # Use first channel if multiple
            channel_id = (
                target_channel_ids[0]
                if isinstance(target_channel_ids, list)
                else target_channel_ids
            )

        # Import and post priorities
        from .workflows.priorities_to_slack import post_priorities_to_slack

        result = post_priorities_to_slack(
            channel_id=channel_id,
            slack_token=slack_token,
            linear_api_key=linear_token,
            linear_team_id=team_id,
            assignee_only=False,  # Show all issues, not just assigned
        )

        if result.get("status") == "success":
            # Log activity
            log_activity(
                tenant_id,
                "post",
                f"Posted developer priorities to Slack channel",
                {
                    "channel_id": channel_id,
                    "total_issues": result.get("total_issues", 0),
                    "total_developers": result.get("total_developers", 0),
                },
            )

        logger.info(f"Priorities posted to Slack for tenant {tenant_id}")
        return result

    except Exception as e:
        logger.exception(f"Failed to post priorities to Slack for tenant {tenant_id}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes


@celery_app.task
def post_priorities_to_slack_for_all_tenants():
    """Post developer priorities to Slack for all active tenants."""
    tenant_ids = get_active_tenants()

    scheduled = 0
    for tenant_id in tenant_ids:
        settings = get_workflow_settings(tenant_id)
        # Check if priorities_to_slack is enabled (default to True if not set)
        if settings.get("priorities_to_slack", True):
            post_priorities_to_slack_for_tenant.delay(tenant_id)
            scheduled += 1

    logger.info(f"Priorities posting scheduled for {scheduled} tenants")
    return {"status": "scheduled", "tenants": scheduled}
