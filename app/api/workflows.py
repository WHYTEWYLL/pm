"""Workflow API endpoints."""

import logging
from datetime import datetime, timezone, timedelta
import os
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from .tenant import get_tenant_id, get_tenant_db, check_subscription
from ..storage.tenant_db import TenantDatabase
from ..storage.encryption import decrypt_token
from ..ingestion.slack import SlackService
from ..ingestion.linear import LinearClient
from ..storage.db import Database

router = APIRouter(prefix="/api/workflows", tags=["workflows"])
logger = logging.getLogger("workflows")


@router.post("/ingest/slack")
async def ingest_slack(
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_tenant_id),
    include_threads: bool = True,
):
    """Trigger Slack ingestion for tenant."""
    if not check_subscription(tenant_id):
        raise HTTPException(status_code=403, detail="Subscription required")

    db = get_tenant_db(tenant_id)
    creds = db.get_oauth_credentials("slack")

    if not creds:
        raise HTTPException(status_code=400, detail="Slack not connected")

    # Get tenant config
    config = db.get_tenant_config()
    target_channel_ids = config.get("slack_target_channel_ids", []) if config else []

    # Decrypt token
    token = decrypt_token(creds["access_token"])

    # Get tenant config for target channels
    if isinstance(target_channel_ids, str):
        import json

        target_channel_ids = json.loads(target_channel_ids)

    # Run ingestion in background
    def run_ingestion():
        # Set tenant context for Database
        os.environ["CURRENT_TENANT_ID"] = tenant_id
        service = SlackService(token=token)
        result = service.ingest(
            include_threads=include_threads,
            target_channel_ids=target_channel_ids if target_channel_ids else None,
            force_last_24h=True,
        )
        return result

    background_tasks.add_task(run_ingestion)

    return {"status": "started", "message": "Ingestion started in background"}


@router.post("/ingest/linear")
async def ingest_linear(
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_tenant_id),
):
    """Trigger Linear ingestion for tenant."""
    if not check_subscription(tenant_id):
        raise HTTPException(status_code=403, detail="Subscription required")

    db = get_tenant_db(tenant_id)
    creds = db.get_oauth_credentials("linear")

    if not creds:
        raise HTTPException(status_code=400, detail="Linear not connected")

    token = decrypt_token(creds["access_token"])

    # Get team_id from config
    config = db.get_tenant_config()
    team_id = config.get("linear_team_id") if config else None
    if isinstance(team_id, str):
        cleaned = team_id.strip()
        if not cleaned or cleaned.lower() in {"none", "null"}:
            team_id = None
        else:
            team_id = cleaned

    def run_ingestion():
        # Set tenant context
        os.environ["CURRENT_TENANT_ID"] = tenant_id
        linear = LinearClient(api_key=token, team_id=team_id)
        logger.info("Triggering Linear ingestion for tenant %s", tenant_id)
        try:
            result = linear.ingest()
            logger.info(
                "Linear ingestion finished for tenant %s: fetched=%s stored=%s",
                tenant_id,
                result.get("total"),
                result.get("stored"),
            )
            return result
        except Exception:
            logger.exception("Linear ingestion failed for tenant %s", tenant_id)
            raise

    background_tasks.add_task(run_ingestion)

    return {"status": "started", "message": "Ingestion started in background"}


@router.get("/standup")
async def get_standup(
    tenant_id: str = Depends(get_tenant_id),
):
    """Get standup data for tenant."""
    if not check_subscription(tenant_id):
        raise HTTPException(status_code=403, detail="Subscription required")

    db_tenant = get_tenant_db(tenant_id)
    creds = db_tenant.get_oauth_credentials("linear")

    if not creds:
        raise HTTPException(status_code=400, detail="Linear not connected")

    token = decrypt_token(creds["access_token"])
    config = db_tenant.get_tenant_config()
    team_id = config.get("linear_team_id") if config else None

    # Import and call the actual standup workflow
    from ..workflows.dev.standup import generate_standup

    # Temporarily set credentials for the workflow
    original_linear_key = os.getenv("LINEAR_API_KEY")
    original_team_id = os.getenv("LINEAR_TEAM_ID")
    os.environ["LINEAR_API_KEY"] = token
    if team_id:
        os.environ["LINEAR_TEAM_ID"] = team_id

    try:
        result = generate_standup()
        # Convert to JSON-serializable format
        return {
            "in_progress": [
                {
                    "identifier": i.get("identifier"),
                    "title": i.get("title"),
                    "state": i.get("state", {}).get("name"),
                }
                for i in result.get("in_progress", [])
            ],
            "todo": [
                {
                    "identifier": i.get("identifier"),
                    "title": i.get("title"),
                    "state": i.get("state", {}).get("name"),
                }
                for i in result.get("todo", [])
            ],
            "backlog": [
                {
                    "identifier": i.get("identifier"),
                    "title": i.get("title"),
                    "state": i.get("state", {}).get("name"),
                }
                for i in result.get("backlog", [])
            ],
            "untracked_messages": [
                {
                    "channel": m.get("channel_name"),
                    "text": m.get("text", "")[:100],
                    "user": m.get("user"),
                }
                for m in result.get("untracked_messages", [])[:10]
            ],
            "tracked_messages": len(result.get("tracked_messages", [])),
            "total_messages": result.get("total_messages", 0),
        }
    finally:
        # Restore original env vars
        if original_linear_key:
            os.environ["LINEAR_API_KEY"] = original_linear_key
        if original_team_id:
            os.environ["LINEAR_TEAM_ID"] = original_team_id


@router.post("/process")
async def process_messages(
    execute: bool = False,
    tenant_id: str = Depends(get_tenant_id),
):
    """Process messages and create/update tickets."""
    if not check_subscription(tenant_id):
        raise HTTPException(status_code=403, detail="Subscription required")

    db_tenant = get_tenant_db(tenant_id)
    creds = db_tenant.get_oauth_credentials("linear")

    if not creds:
        raise HTTPException(status_code=400, detail="Linear not connected")

    token = decrypt_token(creds["access_token"])
    config = db_tenant.get_tenant_config()
    team_id = config.get("linear_team_id") if config else None

    # Import and call the actual process workflow
    from ..workflows.process import process_messages as process_workflow

    # Set credentials
    original_linear_key = os.getenv("LINEAR_API_KEY")
    original_team_id = os.getenv("LINEAR_TEAM_ID")
    os.environ["LINEAR_API_KEY"] = token
    if team_id:
        os.environ["LINEAR_TEAM_ID"] = team_id
    os.environ["CURRENT_TENANT_ID"] = tenant_id

    try:
        result = process_workflow(dry_run=not execute, use_ai=True)
        return {
            "status": "completed",
            "processed": result.get("processed", 0),
            "issue_comments": len(result.get("issue_comments", [])),
            "new_issues": len(result.get("new_issues", [])),
            "errors": result.get("errors", []),
        }
    finally:
        if original_linear_key:
            os.environ["LINEAR_API_KEY"] = original_linear_key
        if original_team_id:
            os.environ["LINEAR_TEAM_ID"] = original_team_id


@router.post("/move-tickets")
async def move_tickets(
    tenant_id: str = Depends(get_tenant_id),
):
    """Analyze and move tickets based on conversations."""
    if not check_subscription(tenant_id):
        raise HTTPException(status_code=403, detail="Subscription required")

    db_tenant = get_tenant_db(tenant_id)
    creds = db_tenant.get_oauth_credentials("linear")

    if not creds:
        raise HTTPException(status_code=400, detail="Linear not connected")

    token = decrypt_token(creds["access_token"])
    config = db_tenant.get_tenant_config()
    team_id = config.get("linear_team_id") if config else None

    # Import and call the actual move_tickets workflow
    from ..workflows.dev.move_tickets import process_ticket_status_changes

    # Set credentials
    original_linear_key = os.getenv("LINEAR_API_KEY")
    original_team_id = os.getenv("LINEAR_TEAM_ID")
    os.environ["LINEAR_API_KEY"] = token
    if team_id:
        os.environ["LINEAR_TEAM_ID"] = team_id
    os.environ["CURRENT_TENANT_ID"] = tenant_id

    try:
        result = process_ticket_status_changes(days_back=7, min_confidence=0.7)
        return {
            "status": result.get("status", "completed"),
            "processed": result.get("processed", 0),
            "changes": result.get("changes", []),
            "errors": result.get("errors", []),
        }
    finally:
        if original_linear_key:
            os.environ["LINEAR_API_KEY"] = original_linear_key
        if original_team_id:
            os.environ["LINEAR_TEAM_ID"] = original_team_id
