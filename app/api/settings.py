"""Settings and Activity Log API endpoints."""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .tenant import get_tenant_id, get_tenant_db
from ..storage.tenant_db import TenantDatabase

router = APIRouter(prefix="/api/settings", tags=["settings"])
logger = logging.getLogger("settings")


# --- Workflow Settings ---


class WorkflowSettings(BaseModel):
    auto_sync: bool = True
    link_conversations: bool = True
    ticket_status_updates: bool = False
    daily_standup: bool = False
    create_tickets: bool = False


DEFAULT_WORKFLOW_SETTINGS = WorkflowSettings()


@router.get("/workflows", response_model=WorkflowSettings)
async def get_workflow_settings(
    tenant_id: str = Depends(get_tenant_id),
):
    """Get workflow settings for tenant."""
    db = get_tenant_db(tenant_id)
    config = db.get_tenant_config()

    if not config or not config.get("workflow_settings"):
        return DEFAULT_WORKFLOW_SETTINGS

    raw_settings = config.get("workflow_settings")

    # Parse if string (SQLite stores as string)
    if isinstance(raw_settings, str):
        try:
            raw_settings = json.loads(raw_settings)
        except json.JSONDecodeError:
            return DEFAULT_WORKFLOW_SETTINGS

    # Merge with defaults
    return WorkflowSettings(
        **{**DEFAULT_WORKFLOW_SETTINGS.model_dump(), **raw_settings}
    )


@router.put("/workflows", response_model=WorkflowSettings)
async def update_workflow_settings(
    settings: WorkflowSettings,
    tenant_id: str = Depends(get_tenant_id),
):
    """Update workflow settings for tenant."""
    db = get_tenant_db(tenant_id)

    # Get existing config
    existing = db.get_tenant_config() or {}

    # Update workflow_settings
    db.update_tenant_config(
        {**existing, "workflow_settings": json.dumps(settings.model_dump())}
    )

    return settings


# --- Activity Log ---


class ActivityItem(BaseModel):
    id: str
    type: str  # sync, link, move, create, post
    description: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: str


class ActivityMetrics(BaseModel):
    synced: int = 0
    linked: int = 0
    moved: int = 0
    created: int = 0


class ActivityResponse(BaseModel):
    items: List[ActivityItem]
    metrics: ActivityMetrics
    has_more: bool


def _init_activity_log_table(db: TenantDatabase):
    """Ensure activity_log table exists."""
    with db._conn() as conn:
        cursor = conn.cursor()
        if db.use_postgres:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_log (
                    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_activity_log_tenant ON activity_log(tenant_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_activity_log_created ON activity_log(created_at DESC)"
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
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_activity_log_tenant ON activity_log(tenant_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_activity_log_created ON activity_log(created_at DESC)"
            )


def log_activity(
    tenant_id: str,
    activity_type: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Log an activity for a tenant."""
    import uuid

    db = TenantDatabase(tenant_id=tenant_id)
    _init_activity_log_table(db)

    with db._conn() as conn:
        cursor = conn.cursor()
        activity_id = str(uuid.uuid4())

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

    return activity_id


@router.get("/activity", response_model=ActivityResponse)
async def get_activity_log(
    tenant_id: str = Depends(get_tenant_id),
    days: int = 7,
    limit: int = 50,
    offset: int = 0,
):
    """Get activity log for tenant."""
    db = get_tenant_db(tenant_id)
    _init_activity_log_table(db)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    items = []
    metrics = ActivityMetrics()
    has_more = False

    with db._conn() as conn:
        cursor = conn.cursor()

        if db.use_postgres:
            # Get items
            cursor.execute(
                """
                SELECT id, type, description, metadata, created_at
                FROM activity_log
                WHERE tenant_id = %s AND created_at >= %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                [tenant_id, since, limit + 1, offset],
            )
            rows = cursor.fetchall()

            # Check if there are more
            if len(rows) > limit:
                has_more = True
                rows = rows[:limit]

            for row in rows:
                items.append(
                    ActivityItem(
                        id=row[0],
                        type=row[1],
                        description=row[2],
                        metadata=(
                            row[3]
                            if isinstance(row[3], dict)
                            else json.loads(row[3] or "{}")
                        ),
                        created_at=(
                            row[4].isoformat()
                            if hasattr(row[4], "isoformat")
                            else str(row[4])
                        ),
                    )
                )

            # Get metrics
            cursor.execute(
                """
                SELECT type, COUNT(*) as count
                FROM activity_log
                WHERE tenant_id = %s AND created_at >= %s
                GROUP BY type
                """,
                [tenant_id, since],
            )
            for row in cursor.fetchall():
                activity_type, count = row[0], row[1]
                if activity_type == "sync":
                    metrics.synced = count
                elif activity_type == "link":
                    metrics.linked = count
                elif activity_type == "move":
                    metrics.moved = count
                elif activity_type == "create":
                    metrics.created = count
        else:
            # SQLite
            since_str = since.isoformat()

            cursor.execute(
                """
                SELECT id, type, description, metadata, created_at
                FROM activity_log
                WHERE tenant_id = ? AND created_at >= ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                [tenant_id, since_str, limit + 1, offset],
            )
            rows = cursor.fetchall()

            if len(rows) > limit:
                has_more = True
                rows = rows[:limit]

            for row in rows:
                items.append(
                    ActivityItem(
                        id=row[0] if isinstance(row, tuple) else row["id"],
                        type=row[1] if isinstance(row, tuple) else row["type"],
                        description=(
                            row[2] if isinstance(row, tuple) else row["description"]
                        ),
                        metadata=json.loads(
                            row[3]
                            if isinstance(row, tuple)
                            else row["metadata"] or "{}"
                        ),
                        created_at=(
                            row[4] if isinstance(row, tuple) else row["created_at"]
                        ),
                    )
                )

            cursor.execute(
                """
                SELECT type, COUNT(*) as count
                FROM activity_log
                WHERE tenant_id = ? AND created_at >= ?
                GROUP BY type
                """,
                [tenant_id, since_str],
            )
            for row in cursor.fetchall():
                activity_type = row[0] if isinstance(row, tuple) else row["type"]
                count = row[1] if isinstance(row, tuple) else row["count"]
                if activity_type == "sync":
                    metrics.synced = count
                elif activity_type == "link":
                    metrics.linked = count
                elif activity_type == "move":
                    metrics.moved = count
                elif activity_type == "create":
                    metrics.created = count

    return ActivityResponse(items=items, metrics=metrics, has_more=has_more)


@router.get("/activity/metrics", response_model=ActivityMetrics)
async def get_activity_metrics(
    tenant_id: str = Depends(get_tenant_id),
    days: int = 7,
):
    """Get activity metrics for tenant."""
    response = await get_activity_log(tenant_id=tenant_id, days=days, limit=0)
    return response.metrics
