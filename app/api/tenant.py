"""Tenant management and middleware."""

from typing import Optional
from fastapi import Depends, HTTPException, Header, Cookie
from fastapi.security import OAuth2PasswordBearer
from functools import lru_cache
import os
import jwt
from jose import JWTError, jwt as jose_jwt
from ..storage.tenant_db import TenantDatabase

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


JWT_SECRET = os.getenv("JWT_SECRET_KEY", os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")))
JWT_ALGORITHM = "HS256"


async def get_tenant_id(
    authorization: Optional[str] = Header(None),
    tenant_id_cookie: Optional[str] = Cookie(None, alias="tenant_id"),
    token: Optional[str] = Depends(oauth2_scheme),
) -> str:
    """
    Extract tenant_id from JWT token or cookie.
    This is a dependency that should be used in all protected routes.
    """
    # Try JWT token from Authorization header
    if authorization:
        try:
            token_str = authorization.split(" ")[1] if " " in authorization else authorization
            payload = jose_jwt.decode(token_str, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            tenant_id = payload.get("tenant_id") or payload.get("sub")
            if tenant_id:
                return tenant_id
        except (JWTError, IndexError, KeyError):
            pass
    
    # Try token from oauth2_scheme dependency
    if token:
        try:
            payload = jose_jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            tenant_id = payload.get("tenant_id") or payload.get("sub")
            if tenant_id:
                return tenant_id
        except (JWTError, KeyError):
            pass
    
    # Fallback to cookie (for development)
    if tenant_id_cookie:
        return tenant_id_cookie
    
    # For development, allow passing tenant_id as header directly
    dev_tenant_id = os.getenv("DEV_TENANT_ID")
    if dev_tenant_id and os.getenv("ENV") != "production":
        return dev_tenant_id
    
    # For local dev, default to local-dev-tenant
    if os.getenv("ENV") != "production":
        return "local-dev-tenant"
    
    raise HTTPException(status_code=401, detail="Missing or invalid authentication")


def get_tenant_db(tenant_id: str = Depends(get_tenant_id)) -> TenantDatabase:
    """
    Get database instance with tenant context.
    All queries should filter by tenant_id.
    """
    return TenantDatabase(tenant_id=tenant_id)


def check_subscription(tenant_id: str) -> bool:
    """Check if tenant has active subscription or valid trial."""
    from datetime import datetime, timezone
    
    db = TenantDatabase(tenant_id=tenant_id)
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT subscription_status, trial_ends_at FROM tenants WHERE id = %s",
                [tenant_id],
            )
            row = cursor.fetchone()
            if row:
                status = row[0]
                trial_ends_at = row[1]
                
                # If status is active, they have a paid subscription
                if status == "active":
                    return True
                
                # If status is trial, check if trial hasn't expired
                if status == "trial":
                    if trial_ends_at:
                        return datetime.now(timezone.utc) < trial_ends_at
                    # If no trial_ends_at set, assume expired (shouldn't happen)
                    return False
                
                return False
        else:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT subscription_status, trial_ends_at FROM tenants WHERE id = ?",
                [tenant_id],
            )
            row = cursor.fetchone()
            if row:
                status = row[0] if isinstance(row, tuple) else row["subscription_status"]
                trial_ends_at_str = row[1] if isinstance(row, tuple) else row.get("trial_ends_at")
                
                # If status is active, they have a paid subscription
                if status == "active":
                    return True
                
                # If status is trial, check if trial hasn't expired
                if status == "trial":
                    if trial_ends_at_str:
                        try:
                            trial_ends_at = datetime.fromisoformat(trial_ends_at_str.replace("Z", "+00:00"))
                            return datetime.now(timezone.utc) < trial_ends_at
                        except (ValueError, AttributeError):
                            return False
                    # If no trial_ends_at set, assume expired
                    return False
                
                return False
    
    # Default to True for development (allows local dev to work without subscription)
    if os.getenv("ENV") != "production":
        return True
    
    # In production, if tenant not found, deny access
    return False


def get_subscription_tier(tenant_id: str) -> str:
    """Get subscription tier for a tenant."""
    db = TenantDatabase(tenant_id=tenant_id)
    with db._conn() as conn:
        if db.use_postgres:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT subscription_tier FROM tenants WHERE id = %s",
                [tenant_id],
            )
            row = cursor.fetchone()
            if row:
                return row[0] or "free"
        else:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT subscription_tier FROM tenants WHERE id = ?",
                [tenant_id],
            )
            row = cursor.fetchone()
            if row:
                tier = row[0] if isinstance(row, tuple) else row.get("subscription_tier")
                return tier or "free"
    
    return "free"


def check_tier_access(tenant_id: str, required_tier: str = "scale") -> bool:
    """
    Check if tenant has access to a specific tier feature.
    Tiers: free < starter < scale
    """
    tier = get_subscription_tier(tenant_id)
    
    tier_hierarchy = {"free": 0, "starter": 1, "scale": 2}
    required_level = tier_hierarchy.get(required_tier.lower(), 0)
    current_level = tier_hierarchy.get(tier.lower(), 0)
    
    return current_level >= required_level


def create_jwt_token(tenant_id: str, email: str) -> str:
    """Create a JWT token for a tenant."""
    payload = {
        "tenant_id": tenant_id,
        "sub": tenant_id,
        "email": email,
    }
    return jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

