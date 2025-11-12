"""Local development endpoints that use existing env vars (no OAuth needed)."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import os

from .tenant import get_tenant_db
from ..storage.tenant_db import TenantDatabase
from ..storage.encryption import encrypt_token
from ..config import settings

router = APIRouter(prefix="/local-dev", tags=["local-dev"])


@router.post("/setup-tenant")
async def setup_local_tenant(tenant_id: str = "local-dev-tenant"):
    """Setup local tenant with existing env vars (no OAuth)."""
    db = TenantDatabase(tenant_id=tenant_id)
    
    # Create tenant if doesn't exist
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tenants (id, email, subscription_status, subscription_tier)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                [tenant_id, "local@dev.com", "active", "scale"],
            )
        else:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO tenants (id, email, subscription_status, subscription_tier)
                VALUES (?, ?, ?, ?)
                """,
                [tenant_id, "local@dev.com", "active", "scale"],
            )
    
    # Store credentials from env vars (for local dev, store plaintext or use a simple encoding)
    # In production, these should be encrypted
    if settings.slack_token:
        # For local dev, store as-is (encryption will be handled by decrypt_token)
        token_to_store = encrypt_token(settings.slack_token) if os.getenv("ENCRYPTION_KEY") else settings.slack_token
        db.save_oauth_credentials(
            service="slack",
            access_token=token_to_store,
            refresh_token=None,
            workspace_id="local-slack",
            workspace_name="Local Slack Workspace",
            scopes="local-dev",
        )
    
    if settings.linear_api_key:
        token_to_store = encrypt_token(settings.linear_api_key) if os.getenv("ENCRYPTION_KEY") else settings.linear_api_key
        db.save_oauth_credentials(
            service="linear",
            access_token=token_to_store,
            refresh_token=None,
            workspace_id=settings.linear_team_id or "local-linear",
            workspace_name="Local Linear Team",
            scopes="local-dev",
        )
    
    if settings.github_token:
        token_to_store = encrypt_token(settings.github_token) if os.getenv("ENCRYPTION_KEY") else settings.github_token
        db.save_oauth_credentials(
            service="github",
            access_token=token_to_store,
            refresh_token=None,
            workspace_id="local-github",
            workspace_name="Local GitHub",
            scopes="local-dev",
        )
    
    # Setup config
    from ..workflows.dev.config import SLACK_TARGET_CHANNEL_IDS
    
    config = {
        "slack_target_channel_ids": SLACK_TARGET_CHANNEL_IDS,
        "linear_team_id": settings.linear_team_id,
        "github_orgs": [],
        "workflow_settings": {},
    }
    db.update_tenant_config(config)
    
    return {
        "status": "setup_complete",
        "tenant_id": tenant_id,
        "message": "Local tenant configured with existing env vars",
    }


@router.get("/tenant-id")
async def get_local_tenant_id():
    """Get the local dev tenant ID."""
    return {"tenant_id": "local-dev-tenant"}

