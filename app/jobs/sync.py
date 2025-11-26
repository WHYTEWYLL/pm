"""Data sync tasks for Slack, Linear, and GitHub."""

import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

from .celery import celery_app
from ..storage.tenant_db import TenantDatabase
from ..storage.encryption import decrypt_token
from .workflows.ingestion.slack import SlackService
from .workflows.ingestion.linear import LinearClient
from .workflows.ingestion.github import GitHubClient
from ..storage.db import Database

logger = logging.getLogger("jobs.sync")


# --- Helper Functions ---


def get_workflow_settings(tenant_id: str) -> dict:
    """Get workflow settings for a tenant."""
    db = TenantDatabase(tenant_id=tenant_id)
    config = db.get_tenant_config()

    if not config:
        return {
            "auto_sync": True,
            "link_conversations": True,
            "ticket_status_updates": False,
            "daily_standup": False,
            "create_tickets": False,
        }

    raw_settings = config.get("workflow_settings")
    if not raw_settings:
        return {
            "auto_sync": True,
            "link_conversations": True,
            "ticket_status_updates": False,
            "daily_standup": False,
            "create_tickets": False,
        }

    if isinstance(raw_settings, str):
        try:
            return json.loads(raw_settings)
        except json.JSONDecodeError:
            return {"auto_sync": True}

    return raw_settings


def log_activity(
    tenant_id: str, activity_type: str, description: str, metadata: dict = None
):
    """Log an activity for a tenant."""
    db = TenantDatabase(tenant_id=tenant_id)

    # Ensure activity_log table exists
    with db._conn() as conn:
        cursor = conn.cursor()
        if db.use_postgres:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_log (
                    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    tenant_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_log (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

    # Insert activity
    activity_id = str(uuid.uuid4())
    with db._conn() as conn:
        cursor = conn.cursor()
        if db.use_postgres:
            cursor.execute(
                """
                INSERT INTO activity_log (id, tenant_id, type, description, metadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [
                    activity_id,
                    tenant_id,
                    activity_type,
                    description,
                    json.dumps(metadata or {}),
                ],
            )
        else:
            cursor.execute(
                """
                INSERT INTO activity_log (id, tenant_id, type, description, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    activity_id,
                    tenant_id,
                    activity_type,
                    description,
                    json.dumps(metadata or {}),
                ],
            )


def get_active_tenants() -> list:
    """Get all active tenants (active subscription or valid trial)."""
    db = TenantDatabase(tenant_id=None)

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
            return [row[0] for row in cursor.fetchall()]
        else:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                """
                SELECT id FROM tenants 
                WHERE subscription_status IN ('active', 'trial')
                AND (trial_ends_at IS NULL OR trial_ends_at > ?)
                """,
                [now],
            )
            return [
                row[0] if isinstance(row, tuple) else row["id"]
                for row in cursor.fetchall()
            ]


def get_tenant_tier(tenant_id: str) -> str:
    """Get subscription tier for a tenant."""
    db = TenantDatabase(tenant_id=tenant_id)

    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT subscription_tier FROM tenants WHERE id = %s", [tenant_id]
            )
            row = cursor.fetchone()
            return row[0] if row else "free"
        else:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT subscription_tier FROM tenants WHERE id = ?", [tenant_id]
            )
            row = cursor.fetchone()
            return (
                row[0]
                if isinstance(row, tuple)
                else row.get("subscription_tier", "free") if row else "free"
            )


# --- Sync Tasks ---


@celery_app.task(bind=True, max_retries=3)
def ingest_slack_for_tenant(self, tenant_id: str):
    """Ingest Slack messages for a specific tenant."""
    try:
        # Check workflow settings
        settings = get_workflow_settings(tenant_id)
        if not settings.get("auto_sync", True):
            logger.info(
                f"Skipping Slack sync for tenant {tenant_id} - auto_sync disabled"
            )
            return {"status": "skipped", "reason": "auto_sync disabled"}

        db = TenantDatabase(tenant_id=tenant_id)
        creds = db.get_oauth_credentials("slack")

        if not creds:
            return {"status": "skipped", "reason": "Slack not connected"}

        config = db.get_tenant_config()
        target_channel_ids = (
            config.get("slack_target_channel_ids", []) if config else []
        )

        if isinstance(target_channel_ids, str):
            try:
                target_channel_ids = json.loads(target_channel_ids)
            except json.JSONDecodeError:
                target_channel_ids = []

        # Set tenant context
        os.environ["CURRENT_TENANT_ID"] = tenant_id

        token = decrypt_token(creds["access_token"])
        service = SlackService(token=token)

        result = service.ingest(
            include_threads=True,
            target_channel_ids=target_channel_ids if target_channel_ids else None,
            force_last_24h=True,
        )

        # Log activity
        stored = result.get("stored", 0) if result else 0
        if stored > 0:
            log_activity(
                tenant_id,
                "sync",
                f"Synced {stored} new Slack messages",
                {"source": "slack", "count": stored},
            )

        logger.info(f"Slack ingestion completed for tenant {tenant_id}: {result}")
        return {"status": "success", "result": result}

    except Exception as e:
        logger.exception(f"Slack ingestion failed for tenant {tenant_id}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def ingest_linear_for_tenant(self, tenant_id: str):
    """Ingest Linear issues for a specific tenant."""
    try:
        # Check workflow settings
        settings = get_workflow_settings(tenant_id)
        if not settings.get("auto_sync", True):
            logger.info(
                f"Skipping Linear sync for tenant {tenant_id} - auto_sync disabled"
            )
            return {"status": "skipped", "reason": "auto_sync disabled"}

        db = TenantDatabase(tenant_id=tenant_id)
        creds = db.get_oauth_credentials("linear")

        if not creds:
            return {"status": "skipped", "reason": "Linear not connected"}

        # Set tenant context
        os.environ["CURRENT_TENANT_ID"] = tenant_id

        token = decrypt_token(creds["access_token"])

        # Get team_id from config
        config = db.get_tenant_config()
        team_id = config.get("linear_team_id") if config else None

        linear = LinearClient(api_key=token, team_id=team_id)
        result = linear.ingest()

        # Log activity
        stored = result.get("stored", 0) if result else 0
        if stored > 0:
            log_activity(
                tenant_id,
                "sync",
                f"Synced {stored} Linear tickets",
                {"source": "linear", "count": stored},
            )

        logger.info(f"Linear ingestion completed for tenant {tenant_id}: {result}")
        return {"status": "success", "result": result}

    except Exception as e:
        logger.exception(f"Linear ingestion failed for tenant {tenant_id}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def ingest_github_for_tenant(self, tenant_id: str):
    """Ingest GitHub PRs and issues for a specific tenant. Requires Scale tier."""
    try:
        # Check workflow settings
        settings = get_workflow_settings(tenant_id)
        if not settings.get("auto_sync", True):
            logger.info(
                f"Skipping GitHub sync for tenant {tenant_id} - auto_sync disabled"
            )
            return {"status": "skipped", "reason": "auto_sync disabled"}

        # Check tier
        tier = get_tenant_tier(tenant_id)
        if tier not in ("scale", "enterprise"):
            return {"status": "skipped", "reason": "GitHub requires Scale tier"}

        db = TenantDatabase(tenant_id=tenant_id)
        creds = db.get_oauth_credentials("github")

        if not creds:
            return {"status": "skipped", "reason": "GitHub not connected"}

        # Set tenant context
        os.environ["CURRENT_TENANT_ID"] = tenant_id

        token = decrypt_token(creds["access_token"])

        # Get config
        config = db.get_tenant_config()
        github_owner = config.get("github_owner") if config else None
        github_repos = config.get("github_repos") if config else None

        if isinstance(github_repos, str):
            try:
                github_repos = json.loads(github_repos)
            except json.JSONDecodeError:
                github_repos = [r.strip() for r in github_repos.split(",") if r.strip()]

        client = GitHubClient(token=token)

        # Fetch PRs and issues from last 24 hours
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        prs = client.list_pull_requests(
            owner=github_owner,
            repo_names=github_repos if github_repos else None,
            state="all",
            since=since,
        )

        issues = client.list_issues(
            owner=github_owner,
            repo_names=github_repos if github_repos else None,
            state="all",
            since=since,
        )

        # Store in database
        stored_prs = 0
        stored_issues = 0
        if prs or issues:
            db_storage = Database()
            if prs:
                stored_prs = db_storage.insert_github_prs(prs)
            if issues:
                stored_issues = db_storage.insert_github_issues(issues)

        # Log activity
        total_stored = stored_prs + stored_issues
        if total_stored > 0:
            log_activity(
                tenant_id,
                "sync",
                f"Synced {stored_prs} PRs and {stored_issues} issues from GitHub",
                {"source": "github", "prs": stored_prs, "issues": stored_issues},
            )

        logger.info(
            f"GitHub ingestion completed for tenant {tenant_id}: prs={len(prs)}, issues={len(issues)}"
        )
        return {
            "status": "success",
            "prs_fetched": len(prs),
            "issues_fetched": len(issues),
            "prs_stored": stored_prs,
            "issues_stored": stored_issues,
        }

    except Exception as e:
        logger.exception(f"GitHub ingestion failed for tenant {tenant_id}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))


# --- Scheduled Tasks ---


@celery_app.task
def hourly_sync_for_all_tenants():
    """Run hourly sync for all active tenants with auto_sync enabled."""
    tenant_ids = get_active_tenants()

    scheduled = 0
    for tenant_id in tenant_ids:
        # Queue ingestion tasks
        ingest_slack_for_tenant.delay(tenant_id)
        ingest_linear_for_tenant.delay(tenant_id)
        ingest_github_for_tenant.delay(tenant_id)
        scheduled += 1

    logger.info(f"Hourly sync scheduled for {scheduled} tenants")
    return {"status": "scheduled", "tenants": scheduled}


@celery_app.task
def daily_sync_for_all_tenants():
    """Run daily sync for all active tenants (full sync)."""
    tenant_ids = get_active_tenants()

    scheduled = 0
    for tenant_id in tenant_ids:
        # Queue ingestion tasks
        ingest_slack_for_tenant.delay(tenant_id)
        ingest_linear_for_tenant.delay(tenant_id)
        ingest_github_for_tenant.delay(tenant_id)
        scheduled += 1

    logger.info(f"Daily sync scheduled for {scheduled} tenants")
    return {"status": "scheduled", "tenants": scheduled}
