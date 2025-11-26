"""Workflow API endpoints."""

import json
import logging
from datetime import datetime, timezone, timedelta
import os
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from pydantic import BaseModel

from .tenant import get_tenant_id, get_tenant_db, check_subscription, check_tier_access
from ..storage.tenant_db import TenantDatabase
from ..storage.encryption import decrypt_token
from ..ingestion.slack import SlackService
from ..ingestion.linear import LinearClient
from ..ingestion.github import GitHubClient
from ..storage.db import Database

router = APIRouter(prefix="/api/workflows", tags=["workflows"])
logger = logging.getLogger("workflows")


class PublishStandupRequest(BaseModel):
    channel_id: str


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

    # Check if linear_team_id is in config, else we list all teams and we get the data for all teams

    # Get team_id from config
    config = db.get_tenant_config()
    raw_team_id = config.get("linear_team_id") if config else None

    team_ids: list[Optional[str]]
    if isinstance(raw_team_id, list):
        team_ids = [t for t in raw_team_id if t]
    elif isinstance(raw_team_id, str):
        cleaned = raw_team_id.strip()
        if not cleaned or cleaned.lower() in {"none", "null"}:
            team_ids = []
        else:
            # Try to parse JSON array, fallback to single value
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, list):
                    team_ids = [str(t) for t in parsed if t]
                else:
                    team_ids = [cleaned]
            except json.JSONDecodeError:
                team_ids = [cleaned]
    else:
        team_ids = []

    if not team_ids:
        # No specific team configured; ingest across all teams
        team_ids = [None]

    aggregated = {"total": 0, "stored": 0, "results": []}

    def run_ingestion():
        # Set tenant context
        os.environ["CURRENT_TENANT_ID"] = tenant_id
        for current_team in team_ids:
            linear = LinearClient(api_key=token, team_id=current_team)
            logger.info(
                "Triggering Linear ingestion for tenant %s (team=%s)",
                tenant_id,
                current_team,
            )
            try:
                result = linear.ingest()
                aggregated["total"] += result.get("total", 0) or 0
                aggregated["stored"] += result.get("stored", 0) or 0
                aggregated["results"].append(
                    {
                        "team": current_team,
                        "fetched": result.get("total", 0),
                        "stored": result.get("stored", 0),
                    }
                )
                logger.info(
                    "Linear ingestion finished for tenant %s (team=%s): fetched=%s stored=%s",
                    tenant_id,
                    current_team,
                    result.get("total"),
                    result.get("stored"),
                )
            except Exception:
                logger.exception(
                    "Linear ingestion failed for tenant %s (team=%s)",
                    tenant_id,
                    current_team,
                )
                raise
        return aggregated

    background_tasks.add_task(run_ingestion)

    return {
        "status": "started",
        "message": "Ingestion started in background",
        "teams": team_ids,
    }


@router.post("/ingest/github")
async def ingest_github(
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_tenant_id),
):
    """Trigger GitHub ingestion for tenant. Requires Scale tier."""
    if not check_subscription(tenant_id):
        raise HTTPException(status_code=403, detail="Subscription required")

    if not check_tier_access(tenant_id, required_tier="scale"):
        raise HTTPException(
            status_code=403,
            detail="GitHub ingestion requires Scale tier subscription. Upgrade to access this feature.",
        )

    db = get_tenant_db(tenant_id)
    creds = db.get_oauth_credentials("github")

    if not creds:
        raise HTTPException(status_code=400, detail="GitHub not connected")

    # Decrypt token
    token = decrypt_token(creds["access_token"])

    # Get tenant config for repo filtering
    config = db.get_tenant_config()
    github_owner = config.get("github_owner") if config else None
    github_repos = config.get("github_repos") if config else None

    # Parse repos if it's a string
    if isinstance(github_repos, str):
        try:
            github_repos = json.loads(github_repos)
        except json.JSONDecodeError:
            # If not JSON, treat as comma-separated
            github_repos = [r.strip() for r in github_repos.split(",") if r.strip()]

    # Run ingestion in background
    def run_ingestion():
        # Set tenant context for Database
        os.environ["CURRENT_TENANT_ID"] = tenant_id
        from datetime import datetime, timezone, timedelta

        # Use OAuth token instead of settings
        client = GitHubClient(token=token)

        # Fetch PRs and issues updated in the last 24 hours
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        prs = []
        issues = []

        print(">>> GitHub ingestion: starting fetch")
        print(
            f">>> GitHub ingestion: config - owner={github_owner}, repos={github_repos}"
        )
        try:
            # Check what repos we have access to
            repos = client.get_repositories(
                owner=github_owner,
                repo_names=github_repos if github_repos else None,
            )
            print(f">>> GitHub ingestion: found {len(repos)} repositories")
            if repos:
                repo_names = [repo.full_name for repo in repos[:5]]  # Show first 5
                print(f">>> GitHub ingestion: sample repos: {repo_names}")

            prs = client.list_pull_requests(
                owner=github_owner,
                repo_names=github_repos if github_repos else None,
                state="all",
                since=since,
            )
            print(f">>> GitHub ingestion: fetched {len(prs)} PRs from API (last 24h)")

            issues = client.list_issues(
                owner=github_owner,
                repo_names=github_repos if github_repos else None,
                state="all",
                since=since,
            )
            print(
                f">>> GitHub ingestion: fetched {len(issues)} issues from API (last 24h)"
            )
        except Exception as exc:
            logger.exception("GitHub ingestion failed while fetching")
            print(f">>> GitHub ingestion: fetch failed with error {exc!r}")
            raise

        # Store in database
        stored_prs = 0
        stored_issues = 0
        db_stats = {}
        if prs or issues:
            db = Database()
            if prs:
                stored_prs = db.insert_github_prs(prs)
            if issues:
                stored_issues = db.insert_github_issues(issues)
            db_stats = db.get_github_stats()
            print(
                f">>> GitHub ingestion: stored {stored_prs} PRs and {stored_issues} issues (db stats: {db_stats})"
            )
        else:
            print(">>> GitHub ingestion: skipping DB store (no PRs/issues)")

        logger.info(
            "GitHub ingestion finished for tenant %s: prs=%s issues=%s stored_prs=%s stored_issues=%s",
            tenant_id,
            len(prs),
            len(issues),
            stored_prs,
            stored_issues,
        )
        print(
            f">>> GitHub ingestion: completed prs={len(prs)} issues={len(issues)} stored_prs={stored_prs} stored_issues={stored_issues}"
        )

        return {
            "prs": prs,
            "issues": issues,
            "total_prs": len(prs),
            "total_issues": len(issues),
            "stored_prs": stored_prs,
            "stored_issues": stored_issues,
            "db_stats": db_stats,
        }

    background_tasks.add_task(run_ingestion)

    return {"status": "started", "message": "GitHub ingestion started in background"}


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


@router.post("/standup/publish")
async def publish_standup_endpoint(
    req: PublishStandupRequest,
    tenant_id: str = Depends(get_tenant_id),
):
    """Publish standup to Slack."""
    if not check_subscription(tenant_id):
        raise HTTPException(status_code=403, detail="Subscription required")

    db_tenant = get_tenant_db(tenant_id)

    # Linear Creds
    linear_creds = db_tenant.get_oauth_credentials("linear")
    if not linear_creds:
        raise HTTPException(status_code=400, detail="Linear not connected")

    # Slack Creds
    slack_creds = db_tenant.get_oauth_credentials("slack")
    if not slack_creds:
        raise HTTPException(status_code=400, detail="Slack not connected")

    linear_token = decrypt_token(linear_creds["access_token"])
    slack_token = decrypt_token(slack_creds["access_token"])

    config = db_tenant.get_tenant_config()
    team_id = config.get("linear_team_id") if config else None

    from ..workflows.dev.standup import publish_standup

    # Temporarily set credentials for the workflow
    original_linear_key = os.getenv("LINEAR_API_KEY")
    original_team_id = os.getenv("LINEAR_TEAM_ID")
    os.environ["LINEAR_API_KEY"] = linear_token
    if team_id:
        os.environ["LINEAR_TEAM_ID"] = team_id
    os.environ["CURRENT_TENANT_ID"] = tenant_id

    try:
        result = publish_standup(channel_id=req.channel_id, slack_token=slack_token)
        return {"status": "published", "result": result}
    except Exception as e:
        logger.exception("Failed to publish standup")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
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
