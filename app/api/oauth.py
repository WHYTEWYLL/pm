"""OAuth integration handlers for Slack, Linear, and GitHub."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
import secrets
import httpx
import os
from urllib.parse import urlencode
from datetime import datetime, timezone, timedelta

from .tenant import get_tenant_id
from ..storage.tenant_db import TenantDatabase
from ..storage.encryption import encrypt_token, decrypt_token

router = APIRouter(prefix="/oauth", tags=["oauth"])


def get_oauth_config():
    """Get OAuth configuration from environment variables."""
    return {
        "slack": {
            "client_id": os.getenv("SLACK_CLIENT_ID"),
            "client_secret": os.getenv("SLACK_CLIENT_SECRET"),
            "auth_url": "https://slack.com/oauth/v2/authorize",
            "token_url": "https://slack.com/api/oauth.v2.access",
            "scopes": [
                "channels:read",
                "groups:read",
                "im:read",
                "mpim:read",
                "chat:read",
                "users:read",
            ],
        },
        "linear": {
            "client_id": os.getenv("LINEAR_CLIENT_ID"),
            "client_secret": os.getenv("LINEAR_CLIENT_SECRET"),
            "auth_url": "https://linear.app/oauth/authorize",
            "token_url": "https://api.linear.app/oauth/token",
            "scopes": ["read", "write"],
        },
        "github": {
            "client_id": os.getenv("GITHUB_CLIENT_ID"),
            "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "scopes": ["repo", "read:org"],
        },
    }


# Simple in-memory state store (use Redis in production)
_oauth_states = {}


@router.get("/{service}/authorize")
async def authorize_oauth(
    service: str,
    redirect_uri: str = Query(...),
    tenant_id: str = Depends(get_tenant_id),
):
    """
    Initiate OAuth flow for a service.
    Returns authorization URL to redirect user to.
    """
    configs = get_oauth_config()
    if service not in configs:
        raise HTTPException(status_code=404, detail="Service not found")

    config = configs[service]
    if not config["client_id"]:
        raise HTTPException(
            status_code=500, detail=f"{service.title()} OAuth not configured"
        )

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        "tenant_id": tenant_id,
        "service": service,
        "redirect_uri": redirect_uri,
        "created_at": datetime.now(timezone.utc),
    }

    # Build authorization URL
    params = {
        "client_id": config["client_id"],
        "redirect_uri": redirect_uri,
        "state": state,
    }

    if service == "linear":
        params["response_type"] = "code"
        params["prompt"] = "consent"
        params["scope"] = " ".join(config["scopes"])
    elif service == "github":
        params["response_type"] = "code"
        params["scope"] = " ".join(config["scopes"])
    elif service == "slack":
        params["user_scope"] = ",".join(config["scopes"])

    auth_url = f"{config['auth_url']}?{urlencode(params)}"
    return {"auth_url": auth_url, "state": state}


@router.get("/{service}/callback")
async def oauth_callback(
    service: str,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
):
    """
    Handle OAuth callback and exchange code for tokens.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    # Verify state
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state")

    state_data = _oauth_states.pop(state)
    tenant_id = state_data["tenant_id"]

    # Check if state is not too old (5 minutes)
    if datetime.now(timezone.utc) - state_data["created_at"] > timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="State expired")

    configs = get_oauth_config()
    config = configs[service]

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        if service == "slack":
            response = await client.post(
                config["token_url"],
                data={
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "code": code,
                    "redirect_uri": state_data["redirect_uri"],
                },
            )
            data = response.json()
            if not data.get("ok"):
                raise HTTPException(status_code=400, detail=data.get("error", "Token exchange failed"))
            
            access_token = data["authed_user"]["access_token"]
            workspace_id = data["team"]["id"]
            workspace_name = data["team"]["name"]
            expires_at = None  # Slack tokens don't expire

        elif service == "linear":
            response = await client.post(
                config["token_url"],
                json={
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "code": code,
                    "redirect_uri": state_data["redirect_uri"],
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/json"},
            )
            data = response.json()
            if "error" in data:
                raise HTTPException(status_code=400, detail=data["error"])
            
            access_token = data["access_token"]
            refresh_token = data.get("refresh_token")
            expires_in = data.get("expires_in", 3600)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            # Get workspace info
            workspace_response = await client.get(
                "https://api.linear.app/graphql",
                headers={"Authorization": access_token},
                json={"query": "{ viewer { id } }"},
            )
            workspace_id = "linear_workspace"  # Linear uses user-based auth
            workspace_name = "Linear"

        elif service == "github":
            response = await client.post(
                config["token_url"],
                data={
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "code": code,
                    "redirect_uri": state_data["redirect_uri"],
                },
                headers={"Accept": "application/json"},
            )
            data = response.json()
            if "error" in data:
                raise HTTPException(status_code=400, detail=data["error"])
            
            access_token = data["access_token"]
            refresh_token = data.get("refresh_token")
            expires_at = None  # GitHub tokens are long-lived
            
            # Get user/org info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {access_token}"},
            )
            user_data = user_response.json()
            workspace_id = user_data.get("login")
            workspace_name = user_data.get("name") or workspace_id

    # Store encrypted tokens
    db = TenantDatabase(tenant_id=tenant_id)
    db.save_oauth_credentials(
        service=service,
        access_token=encrypt_token(access_token),
        refresh_token=encrypt_token(refresh_token) if refresh_token else None,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        scopes=",".join(config["scopes"]),
        expires_at=expires_at,
    )

    return {
        "status": "connected",
        "service": service,
        "workspace": workspace_name,
        "redirect_url": f"{state_data['redirect_uri']}?success=true",
    }


@router.get("/{service}/status")
async def get_oauth_status(
    service: str,
    tenant_id: str = Depends(get_tenant_id),
):
    """Check if a service is connected for this tenant."""
    db = TenantDatabase(tenant_id=tenant_id)
    creds = db.get_oauth_credentials(service)
    
    if not creds:
        return {"connected": False, "service": service}
    
    return {
        "connected": True,
        "service": service,
        "workspace": creds.get("workspace_name"),
        "connected_at": creds.get("created_at"),
    }


@router.delete("/{service}/disconnect")
async def disconnect_oauth(
    service: str,
    tenant_id: str = Depends(get_tenant_id),
):
    """Disconnect an OAuth service."""
    db = TenantDatabase(tenant_id=tenant_id)
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE oauth_credentials SET is_active = FALSE WHERE tenant_id = %s AND service = %s",
                [tenant_id, service],
            )
        else:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE oauth_credentials SET is_active = 0 WHERE tenant_id = ? AND service = ?",
                [tenant_id, service],
            )
    
    return {"status": "disconnected", "service": service}

