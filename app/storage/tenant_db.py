"""Multi-tenant database layer with tenant isolation."""

from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, ContextManager
from datetime import datetime, timezone
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2.pool import SimpleConnectionPool

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    RealDictCursor = None
    SimpleConnectionPool = None

from ..config import settings


class TenantDatabase:
    """Database class with tenant isolation support."""

    def __init__(self, tenant_id: Optional[str] = None, db_url: Optional[str] = None):
        """
        Initialize database with tenant context.

        Args:
            tenant_id: Current tenant ID for filtering queries
            db_url: PostgreSQL connection URL (if None, uses SQLite for local dev)
        """
        self.tenant_id = tenant_id
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.use_postgres = (
            self.db_url and self.db_url.startswith("postgresql") and PSYCOPG2_AVAILABLE
        )

        if self.use_postgres:
            if not PSYCOPG2_AVAILABLE:
                raise ImportError(
                    "psycopg2 is required for PostgreSQL. Install with: pip install psycopg2-binary"
                )
            # PostgreSQL connection pool
            self.pool = SimpleConnectionPool(1, 10, self.db_url)
        else:
            # SQLite for local development
            db_path = Path(os.getenv("DB_FILE_PATH", "./data/messages.db"))
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.db_path = db_path

        # Initialize schema
        self._init_schema()

    @contextmanager
    def _conn(self) -> ContextManager:
        """Get database connection with tenant context."""
        if self.use_postgres:
            conn = self.pool.getconn()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                self.pool.putconn(conn)
        else:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def _init_schema(self) -> None:
        """Initialize multi-tenant schema if it doesn't exist."""
        with self._conn() as conn:
            if self.use_postgres:
                # PostgreSQL schema
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tenants (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        subscription_tier TEXT DEFAULT 'free',
                        subscription_status TEXT DEFAULT 'active',
                        stripe_customer_id TEXT,
                        stripe_subscription_id TEXT,
                        trial_ends_at TIMESTAMP,
                        owner_user_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS oauth_credentials (
                        id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                        service TEXT NOT NULL,
                        access_token TEXT NOT NULL,
                        refresh_token TEXT,
                        token_expires_at TIMESTAMP,
                        workspace_id TEXT,
                        workspace_name TEXT,
                        scopes TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(tenant_id, service, workspace_id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tenant_configs (
                        tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
                        slack_target_channel_ids JSONB DEFAULT '[]'::jsonb,
                        linear_team_id TEXT,
                        github_orgs JSONB DEFAULT '[]'::jsonb,
                        workflow_settings JSONB DEFAULT '{}'::jsonb,
                        notification_settings JSONB DEFAULT '{}'::jsonb,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    email_verified BOOLEAN DEFAULT FALSE,
                    email_verification_token TEXT,
                    email_verification_expires TIMESTAMP,
                    password_reset_token TEXT,
                    password_reset_expires TIMESTAMP,
                    tenant_id TEXT REFERENCES tenants(id) ON DELETE SET NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_users_email_verification_token ON users(email_verification_token)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_users_password_reset_token ON users(password_reset_token)"
                )

                # Add owner_user_id to tenants if it doesn't exist
                try:
                    cursor.execute(
                        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS owner_user_id TEXT REFERENCES users(id) ON DELETE SET NULL"
                    )
                except Exception:
                    pass  # Column already exists or not supported
            else:
                # SQLite schema
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tenants (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        subscription_tier TEXT DEFAULT 'free',
                        subscription_status TEXT DEFAULT 'active',
                        stripe_customer_id TEXT,
                        stripe_subscription_id TEXT,
                        trial_ends_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS oauth_credentials (
                        id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        service TEXT NOT NULL,
                        access_token TEXT NOT NULL,
                        refresh_token TEXT,
                        token_expires_at TEXT,
                        workspace_id TEXT,
                        workspace_name TEXT,
                        scopes TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(tenant_id, service, workspace_id)
                    )
                """
                )
                cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS tenant_configs (
                    tenant_id TEXT PRIMARY KEY,
                    slack_target_channel_ids TEXT DEFAULT '[]',
                    linear_team_id TEXT,
                    github_orgs TEXT DEFAULT '[]',
                    workflow_settings TEXT DEFAULT '{}',
                    notification_settings TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
                )
                cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    email_verified INTEGER DEFAULT 0,
                    email_verification_token TEXT,
                    email_verification_expires TEXT,
                    password_reset_token TEXT,
                    password_reset_expires TEXT,
                    tenant_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_users_email_verification_token ON users(email_verification_token)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_users_password_reset_token ON users(password_reset_token)"
                )

                # Add owner_user_id to tenants if it doesn't exist
                try:
                    cursor.execute("ALTER TABLE tenants ADD COLUMN owner_user_id TEXT")
                except Exception:
                    pass  # Column already exists

                # Add trial_ends_at to tenants if it doesn't exist (for SQLite migration)
                try:
                    cursor.execute("ALTER TABLE tenants ADD COLUMN trial_ends_at TEXT")
                except Exception:
                    pass  # Column already exists

                # Handle existing tenants with trial status but no trial_ends_at (SQLite migration)
                from datetime import datetime, timezone, timedelta

                try:
                    # Get existing trial tenants without trial_ends_at
                    cursor.execute(
                        """
                        SELECT id, created_at FROM tenants 
                        WHERE subscription_status = 'trial' 
                        AND (trial_ends_at IS NULL OR trial_ends_at = '')
                        """
                    )
                    trial_tenants = cursor.fetchall()

                    for tenant_row in trial_tenants:
                        tenant_id = (
                            tenant_row[0]
                            if isinstance(tenant_row, tuple)
                            else tenant_row["id"]
                        )
                        created_at_str = (
                            tenant_row[1]
                            if isinstance(tenant_row, tuple)
                            else tenant_row.get("created_at")
                        )

                        if created_at_str:
                            try:
                                # Parse created_at and set trial_ends_at to 7 days from creation
                                if isinstance(created_at_str, str):
                                    created_at = datetime.fromisoformat(
                                        created_at_str.replace("Z", "+00:00")
                                    )
                                else:
                                    created_at = datetime.fromisoformat(created_at_str)

                                # If created more than 7 days ago, mark as expired
                                if datetime.now(timezone.utc) - created_at > timedelta(
                                    days=7
                                ):
                                    cursor.execute(
                                        """
                                        UPDATE tenants 
                                        SET subscription_status = 'expired',
                                            subscription_tier = 'free'
                                        WHERE id = ?
                                        """,
                                        [tenant_id],
                                    )
                                else:
                                    # Set trial_ends_at to 7 days from creation
                                    trial_ends_at = created_at + timedelta(days=7)
                                    cursor.execute(
                                        """
                                        UPDATE tenants 
                                        SET trial_ends_at = ?
                                        WHERE id = ?
                                        """,
                                        [trial_ends_at.isoformat(), tenant_id],
                                    )
                            except (ValueError, AttributeError, TypeError):
                                # If we can't parse the date, mark as expired to be safe
                                cursor.execute(
                                    """
                                    UPDATE tenants 
                                    SET subscription_status = 'expired',
                                        subscription_tier = 'free'
                                    WHERE id = ?
                                    """,
                                    [tenant_id],
                                )
                except Exception as e:
                    # Log but don't fail - migration should be resilient
                    import logging

                    logging.warning(f"Error during SQLite trial migration: {e}")
                    pass
            conn.commit()

    def _ensure_tenant_filter(
        self, query: str, params: List[Any]
    ) -> tuple[str, List[Any]]:
        """Add tenant_id filter to query if tenant_id is set."""
        if not self.tenant_id:
            return query, params

        if "WHERE" in query.upper():
            query += (
                f" AND tenant_id = ?"
                if not self.use_postgres
                else f" AND tenant_id = %s"
            )
        else:
            query += (
                f" WHERE tenant_id = ?"
                if not self.use_postgres
                else f" WHERE tenant_id = %s"
            )

        params.append(self.tenant_id)
        return query, params

    def get_oauth_credentials(
        self, service: str, workspace_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get OAuth credentials for a service."""
        with self._conn() as conn:
            if self.use_postgres:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                query = """
                    SELECT * FROM oauth_credentials 
                    WHERE tenant_id = %s AND service = %s AND is_active = TRUE
                """
                params = [self.tenant_id, service]
                if workspace_id:
                    query += " AND workspace_id = %s"
                    params.append(workspace_id)
                cursor.execute(query, params)
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                cursor = conn.cursor()
                query = """
                    SELECT * FROM oauth_credentials 
                    WHERE tenant_id = ? AND service = ? AND is_active = 1
                """
                params = [self.tenant_id, service]
                if workspace_id:
                    query += " AND workspace_id = ?"
                    params.append(workspace_id)
                cursor.execute(query, params)
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None

    def save_oauth_credentials(
        self,
        service: str,
        access_token: str,
        refresh_token: Optional[str],
        workspace_id: str,
        workspace_name: Optional[str] = None,
        scopes: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> str:
        """Save or update OAuth credentials."""
        with self._conn() as conn:
            if self.use_postgres:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO oauth_credentials 
                    (tenant_id, service, access_token, refresh_token, workspace_id, 
                     workspace_name, scopes, token_expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tenant_id, service, workspace_id)
                    DO UPDATE SET
                        access_token = EXCLUDED.access_token,
                        refresh_token = EXCLUDED.refresh_token,
                        workspace_name = EXCLUDED.workspace_name,
                        scopes = EXCLUDED.scopes,
                        token_expires_at = EXCLUDED.token_expires_at,
                        is_active = TRUE,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """,
                    (
                        self.tenant_id,
                        service,
                        access_token,
                        refresh_token,
                        workspace_id,
                        workspace_name,
                        scopes,
                        expires_at,
                    ),
                )
                return cursor.fetchone()[0]
            else:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO oauth_credentials 
                    (tenant_id, service, access_token, refresh_token, workspace_id, 
                     workspace_name, scopes, token_expires_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                    ON CONFLICT(tenant_id, service, workspace_id)
                    DO UPDATE SET
                        access_token = excluded.access_token,
                        refresh_token = excluded.refresh_token,
                        workspace_name = excluded.workspace_name,
                        scopes = excluded.scopes,
                        token_expires_at = excluded.token_expires_at,
                        is_active = 1,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    (
                        self.tenant_id,
                        service,
                        access_token,
                        refresh_token,
                        workspace_id,
                        workspace_name,
                        scopes,
                        expires_at.isoformat() if expires_at else None,
                    ),
                )
                return str(cursor.lastrowid)

    def get_tenant_config(self) -> Optional[Dict[str, Any]]:
        """Get tenant configuration."""
        with self._conn() as conn:
            if self.use_postgres:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(
                    "SELECT * FROM tenant_configs WHERE tenant_id = %s",
                    [self.tenant_id],
                )
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM tenant_configs WHERE tenant_id = ?", [self.tenant_id]
                )
                row = cursor.fetchone()
                return dict(row) if row else None

    def update_tenant_config(self, config: Dict[str, Any]) -> None:
        """Update tenant configuration."""
        with self._conn() as conn:
            if self.use_postgres:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO tenant_configs (tenant_id, slack_target_channel_ids, 
                        linear_team_id, github_orgs, workflow_settings)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (tenant_id)
                    DO UPDATE SET
                        slack_target_channel_ids = EXCLUDED.slack_target_channel_ids,
                        linear_team_id = EXCLUDED.linear_team_id,
                        github_orgs = EXCLUDED.github_orgs,
                        workflow_settings = EXCLUDED.workflow_settings,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    (
                        self.tenant_id,
                        config.get("slack_target_channel_ids"),
                        config.get("linear_team_id"),
                        config.get("github_orgs"),
                        config.get("workflow_settings"),
                    ),
                )
            else:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO tenant_configs 
                    (tenant_id, slack_target_channel_ids, linear_team_id, 
                     github_orgs, workflow_settings)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        self.tenant_id,
                        str(config.get("slack_target_channel_ids", "[]")),
                        config.get("linear_team_id"),
                        str(config.get("github_orgs", "[]")),
                        str(config.get("workflow_settings", "{}")),
                    ),
                )
