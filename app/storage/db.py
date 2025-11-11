from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Iterable
from datetime import datetime, timezone
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_batch
    from psycopg2.pool import SimpleConnectionPool

    PSYCOPG2_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    psycopg2 = None  # type: ignore
    RealDictCursor = None  # type: ignore
    execute_batch = None  # type: ignore
    SimpleConnectionPool = None  # type: ignore
    PSYCOPG2_AVAILABLE = False

from ..config import settings
from ..models import SlackMessage, LinearIssue, GitHubPullRequest, GitHubIssue


class Database:
    def __init__(
        self,
        db_path: Optional[Path] = None,
        db_url: Optional[str] = None,
    ):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.use_postgres = bool(self.db_url and self.db_url.startswith("postgresql"))

        if self.use_postgres:
            if not PSYCOPG2_AVAILABLE:
                raise ImportError(
                    "psycopg2 is required for PostgreSQL support. "
                    "Install it or unset DATABASE_URL to use SQLite."
                )
            # create a small connection pool for ingestion workloads
            self.pool = SimpleConnectionPool(1, 5, self.db_url)  # type: ignore[arg-type]
        else:
            self.db_path = Path(db_path or settings.db_file_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_schema()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @contextmanager
    def _conn(self):
        """Context manager for database connections."""
        if self.use_postgres:
            conn = self.pool.getconn()  # type: ignore[attr-defined]
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                self.pool.putconn(conn)  # type: ignore[attr-defined]
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

    def _cursor(self, conn):
        if self.use_postgres:
            return conn.cursor(cursor_factory=RealDictCursor)
        return conn.cursor()

    @staticmethod
    def _dt_from_timestamp(ts: float) -> datetime:
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    def _normalize_row(self, row: Optional[Any]) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        data = dict(row)
        for key, value in list(data.items()):
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

    def _normalize_rows(self, rows: Iterable[Any]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for row in rows:
            record = self._normalize_row(row)
            if record is not None:
                normalized.append(record)
        return normalized

    def _init_schema(self) -> None:
        """Initialize database schema if it doesn't exist."""
        with self._conn() as conn:
            cursor = self._cursor(conn)

            if self.use_postgres:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        channel_id TEXT NOT NULL,
                        ts DOUBLE PRECISION NOT NULL,
                        channel_name TEXT NOT NULL,
                        "user" TEXT,
                        text TEXT,
                        is_dm BOOLEAN NOT NULL,
                        thread_ts TEXT,
                        is_thread_reply BOOLEAN NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL,
                        processed BOOLEAN DEFAULT FALSE,
                        PRIMARY KEY (channel_id, ts)
                    )
                    """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_processed ON messages(processed, created_at)"
                )

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS linear_issues (
                        id TEXT PRIMARY KEY,
                        identifier TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        state_name TEXT NOT NULL,
                        state_type TEXT NOT NULL,
                        url TEXT NOT NULL,
                        assignee_name TEXT,
                        parent_id TEXT,
                        parent_title TEXT,
                        original_created_at TEXT,
                        original_updated_at TEXT,
                        snapshot_date TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_linear_state ON linear_issues(state_name, state_type)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_linear_assignee ON linear_issues(assignee_name)"
                )

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS github_prs (
                        id BIGINT PRIMARY KEY,
                        number INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        body TEXT,
                        state TEXT NOT NULL,
                        is_merged BOOLEAN NOT NULL,
                        url TEXT NOT NULL,
                        repo_full_name TEXT NOT NULL,
                        author TEXT,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        closed_at TIMESTAMPTZ,
                        merged_at TIMESTAMPTZ,
                        base_branch TEXT,
                        head_branch TEXT,
                        merge_commit_sha TEXT,
                        merge_method TEXT,
                        merged_by TEXT,
                        additions INTEGER,
                        deletions INTEGER,
                        changed_files INTEGER,
                        files_changed TEXT,
                        review_comments INTEGER,
                        comments_count INTEGER,
                        commits_count INTEGER,
                        reviewers TEXT,
                        approved_by TEXT,
                        is_draft BOOLEAN NOT NULL DEFAULT FALSE,
                        snapshot_date TEXT NOT NULL,
                        stored_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_github_pr_repo_state ON github_prs(repo_full_name, state)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_github_pr_author ON github_prs(author)"
                )

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS github_issues (
                        id BIGINT PRIMARY KEY,
                        number INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        body TEXT,
                        state TEXT NOT NULL,
                        url TEXT NOT NULL,
                        repo_full_name TEXT NOT NULL,
                        author TEXT,
                        assignees TEXT,
                        labels TEXT,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        closed_at TIMESTAMPTZ,
                        snapshot_date TEXT NOT NULL,
                        stored_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_github_issue_repo_state ON github_issues(repo_full_name, state)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_github_issue_author ON github_issues(author)"
                )

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS decision_logs (
                        id BIGSERIAL PRIMARY KEY,
                        workflow_name TEXT NOT NULL,
                        action_type TEXT NOT NULL,
                        entity_type TEXT,
                        entity_id TEXT,
                        entity_identifier TEXT,
                        action_taken TEXT NOT NULL,
                        reasoning TEXT,
                        confidence DOUBLE PRECISION,
                        input_data TEXT,
                        output_data TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_decision_logs_workflow_date ON decision_logs(workflow_name, created_at)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_decision_logs_entity ON decision_logs(entity_type, entity_id)"
                )
            else:
                # SQLite schema (unchanged from previous implementation)
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        channel_id TEXT NOT NULL,
                        ts REAL NOT NULL,
                        channel_name TEXT NOT NULL,
                        user TEXT,
                        text TEXT,
                        is_dm INTEGER NOT NULL,
                        thread_ts TEXT,
                        is_thread_reply INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        processed INTEGER DEFAULT 0,
                        PRIMARY KEY (channel_id, ts)
                    )
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_created_at 
                    ON messages(created_at)
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_processed 
                    ON messages(processed, created_at)
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS linear_issues (
                        id TEXT PRIMARY KEY,
                        identifier TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        state_name TEXT NOT NULL,
                        state_type TEXT NOT NULL,
                        url TEXT NOT NULL,
                        assignee_name TEXT,
                        parent_id TEXT,
                        parent_title TEXT,
                        original_created_at TEXT,
                        original_updated_at TEXT,
                        snapshot_date TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_linear_state 
                    ON linear_issues(state_name, state_type)
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_linear_assignee 
                    ON linear_issues(assignee_name)
                """
                )
                try:
                    conn.execute(
                        "ALTER TABLE linear_issues ADD COLUMN original_created_at TEXT"
                    )
                except sqlite3.OperationalError:
                    pass
                try:
                    conn.execute(
                        "ALTER TABLE linear_issues ADD COLUMN original_updated_at TEXT"
                    )
                except sqlite3.OperationalError:
                    pass
                try:
                    conn.execute(
                        "ALTER TABLE linear_issues ADD COLUMN snapshot_date TEXT"
                    )
                except sqlite3.OperationalError:
                    pass

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS github_prs (
                        id INTEGER PRIMARY KEY,
                        number INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        body TEXT,
                        state TEXT NOT NULL,
                        is_merged INTEGER NOT NULL,
                        url TEXT NOT NULL,
                        repo_full_name TEXT NOT NULL,
                        author TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        closed_at TEXT,
                        merged_at TEXT,
                        base_branch TEXT,
                        head_branch TEXT,
                        merge_commit_sha TEXT,
                        merge_method TEXT,
                        merged_by TEXT,
                        additions INTEGER,
                        deletions INTEGER,
                        changed_files INTEGER,
                        files_changed TEXT,
                        review_comments INTEGER,
                        comments_count INTEGER,
                        commits_count INTEGER,
                        reviewers TEXT,
                        approved_by TEXT,
                        is_draft INTEGER NOT NULL DEFAULT 0,
                        snapshot_date TEXT NOT NULL,
                        stored_at TEXT NOT NULL
                    )
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_github_pr_repo_state 
                    ON github_prs(repo_full_name, state)
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_github_pr_author 
                    ON github_prs(author)
                """
                )
                new_pr_columns = [
                    ("merge_commit_sha", "TEXT"),
                    ("merge_method", "TEXT"),
                    ("merged_by", "TEXT"),
                    ("additions", "INTEGER"),
                    ("deletions", "INTEGER"),
                    ("changed_files", "INTEGER"),
                    ("files_changed", "TEXT"),
                    ("review_comments", "INTEGER"),
                    ("comments_count", "INTEGER"),
                    ("commits_count", "INTEGER"),
                    ("reviewers", "TEXT"),
                    ("approved_by", "TEXT"),
                    ("is_draft", "INTEGER"),
                ]
                for col_name, col_type in new_pr_columns:
                    try:
                        conn.execute(
                            f"ALTER TABLE github_prs ADD COLUMN {col_name} {col_type}"
                        )
                    except sqlite3.OperationalError:
                        pass

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS github_issues (
                        id INTEGER PRIMARY KEY,
                        number INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        body TEXT,
                        state TEXT NOT NULL,
                        url TEXT NOT NULL,
                        repo_full_name TEXT NOT NULL,
                        author TEXT,
                        assignees TEXT,
                        labels TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        closed_at TEXT,
                        snapshot_date TEXT NOT NULL,
                        stored_at TEXT NOT NULL
                    )
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_github_issue_repo_state 
                    ON github_issues(repo_full_name, state)
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_github_issue_author 
                    ON github_issues(author)
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS decision_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        workflow_name TEXT NOT NULL,
                        action_type TEXT NOT NULL,
                        entity_type TEXT,
                        entity_id TEXT,
                        entity_identifier TEXT,
                        action_taken TEXT NOT NULL,
                        reasoning TEXT,
                        confidence REAL,
                        input_data TEXT,
                        output_data TEXT,
                        created_at TEXT NOT NULL
                    )
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_decision_logs_workflow_date 
                    ON decision_logs(workflow_name, created_at)
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_decision_logs_entity 
                    ON decision_logs(entity_type, entity_id)
                """
                )

    def insert_messages(self, messages: List[SlackMessage]) -> int:
        """
        Insert messages into the database.
        Uses INSERT OR IGNORE to handle duplicates automatically.
        Returns the number of new messages inserted.
        """
        if not messages:
            return 0

        inserted = 0
        with self._conn() as conn:
            cursor = self._cursor(conn)
            for msg in messages:
                created_at_dt = self._dt_from_timestamp(msg.ts)
                if self.use_postgres:
                    cursor.execute(
                        """
                        INSERT INTO messages 
                        (channel_id, ts, channel_name, "user", text, is_dm, thread_ts, is_thread_reply, created_at, processed)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                        ON CONFLICT (channel_id, ts) DO NOTHING
                        """,
                        (
                            msg.channel_id,
                            msg.ts,
                            msg.channel_name,
                            msg.user,
                            msg.text,
                            bool(msg.is_dm),
                            msg.thread_ts,
                            bool(msg.is_thread_reply),
                            created_at_dt,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO messages 
                        (channel_id, ts, channel_name, user, text, is_dm, thread_ts, is_thread_reply, created_at, processed)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                        """,
                        (
                            msg.channel_id,
                            msg.ts,
                            msg.channel_name,
                            msg.user,
                            msg.text,
                            1 if msg.is_dm else 0,
                            msg.thread_ts,
                            1 if msg.is_thread_reply else 0,
                            created_at_dt.isoformat(),
                        ),
                    )
                if cursor.rowcount > 0:
                    inserted += 1

        return inserted

    def get_unprocessed_messages(
        self, limit: Optional[int] = None, since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all unprocessed messages, optionally filtered by time.
        Returns messages as dictionaries.
        """
        with self._conn() as conn:
            cursor = self._cursor(conn)
            if self.use_postgres:
                query = "SELECT * FROM messages WHERE processed = FALSE"
                params: List[Any] = []
                if since:
                    query += " AND created_at >= %s"
                    params.append(since)
                query += " ORDER BY ts ASC"
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                cursor.execute(query, params)
            else:
                query = "SELECT * FROM messages WHERE processed = 0"
                params = []
                if since:
                    query += " AND created_at >= ?"
                    params.append(since.isoformat())
                query += " ORDER BY ts ASC"
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                cursor.execute(query, params)
            rows = cursor.fetchall()
            return self._normalize_rows(rows)

    def get_messages_since(
        self, since: datetime, processed: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all messages since a given datetime.
        Optionally filter by processed status.
        """
        with self._conn() as conn:
            cursor = self._cursor(conn)
            if self.use_postgres:
                query = "SELECT * FROM messages WHERE created_at >= %s"
                params: List[Any] = [since]
                if processed is not None:
                    query += " AND processed = %s"
                    params.append(bool(processed))
                query += " ORDER BY ts ASC"
                cursor.execute(query, params)
            else:
                query = "SELECT * FROM messages WHERE created_at >= ?"
                params = [since.isoformat()]
                if processed is not None:
                    query += " AND processed = ?"
                    params.append(1 if processed else 0)
                query += " ORDER BY ts ASC"
                cursor.execute(query, params)
            rows = cursor.fetchall()
            return self._normalize_rows(rows)

    def mark_as_processed(self, channel_id: str, ts: float) -> None:
        """Mark a single message as processed."""
        with self._conn() as conn:
            cursor = self._cursor(conn)
            if self.use_postgres:
                cursor.execute(
                    """
                    UPDATE messages 
                    SET processed = TRUE
                    WHERE channel_id = %s AND ts = %s
                    """,
                    (channel_id, ts),
                )
            else:
                cursor.execute(
                    """
                    UPDATE messages 
                    SET processed = 1 
                    WHERE channel_id = ? AND ts = ?
                """,
                    (channel_id, ts),
                )

    def mark_batch_as_processed(self, messages: List[tuple[str, float]]) -> None:
        """Mark multiple messages as processed. Expects list of (channel_id, ts) tuples."""
        if not messages:
            return

        with self._conn() as conn:
            cursor = self._cursor(conn)
            if self.use_postgres:
                query = """
                    UPDATE messages 
                    SET processed = TRUE 
                    WHERE channel_id = %s AND ts = %s
                """
                if execute_batch:
                    execute_batch(cursor, query, messages)
                else:  # pragma: no cover - fallback
                    cursor.executemany(query, messages)
            else:
                cursor.executemany(
                    """
                    UPDATE messages 
                    SET processed = 1 
                    WHERE channel_id = ? AND ts = ?
                """,
                    messages,
                )

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self._conn() as conn:
            cursor = self._cursor(conn)
            if self.use_postgres:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN processed THEN 1 ELSE 0 END) as processed,
                        SUM(CASE WHEN NOT processed THEN 1 ELSE 0 END) as unprocessed,
                        MIN(created_at) as oldest,
                        MAX(created_at) as newest
                    FROM messages
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed,
                        SUM(CASE WHEN processed = 0 THEN 1 ELSE 0 END) as unprocessed,
                        MIN(created_at) as oldest,
                        MAX(created_at) as newest
                    FROM messages
                """
                )
            row = self._normalize_row(cursor.fetchone())
            if not row:
                return {
                    "total": 0,
                    "processed": 0,
                    "unprocessed": 0,
                    "oldest": None,
                    "newest": None,
                }
            return {
                "total": row.get("total", 0) or 0,
                "processed": row.get("processed", 0) or 0,
                "unprocessed": row.get("unprocessed", 0) or 0,
                "oldest": row.get("oldest"),
                "newest": row.get("newest"),
            }

    def insert_linear_issues(self, issues: List[LinearIssue]) -> int:
        """
        Insert Linear issues into the database.
        Uses INSERT OR REPLACE to handle updates.
        Returns the number of issues inserted/updated.
        """
        if not issues:
            return 0

        now_iso = datetime.now(timezone.utc).isoformat()
        now_dt = datetime.now(timezone.utc)
        snapshot_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        inserted = 0

        with self._conn() as conn:
            cursor = self._cursor(conn)
            for issue in issues:
                if self.use_postgres:
                    cursor.execute(
                        """
                        INSERT INTO linear_issues 
                        (id, identifier, title, description, state_name, state_type, url, 
                         assignee_name, parent_id, parent_title, original_created_at, original_updated_at,
                         snapshot_date, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            identifier = EXCLUDED.identifier,
                            title = EXCLUDED.title,
                            description = EXCLUDED.description,
                            state_name = EXCLUDED.state_name,
                            state_type = EXCLUDED.state_type,
                            url = EXCLUDED.url,
                            assignee_name = EXCLUDED.assignee_name,
                            parent_id = EXCLUDED.parent_id,
                            parent_title = EXCLUDED.parent_title,
                            original_created_at = EXCLUDED.original_created_at,
                            original_updated_at = EXCLUDED.original_updated_at,
                            snapshot_date = EXCLUDED.snapshot_date,
                            created_at = EXCLUDED.created_at,
                            updated_at = EXCLUDED.updated_at
                        """,
                        (
                            issue.id,
                            issue.identifier,
                            issue.title,
                            issue.description,
                            issue.state_name,
                            issue.state_type,
                            issue.url,
                            issue.assignee_name,
                            issue.parent_id,
                            issue.parent_title,
                            issue.original_created_at,
                            issue.original_updated_at,
                            snapshot_date,
                            now_dt,
                            now_dt,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO linear_issues 
                        (id, identifier, title, description, state_name, state_type, url, 
                         assignee_name, parent_id, parent_title, original_created_at, original_updated_at,
                         snapshot_date, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            issue.id,
                            issue.identifier,
                            issue.title,
                            issue.description,
                            issue.state_name,
                            issue.state_type,
                            issue.url,
                            issue.assignee_name,
                            issue.parent_id,
                            issue.parent_title,
                            issue.original_created_at,
                            issue.original_updated_at,
                            snapshot_date,
                            now_iso,
                            now_iso,
                        ),
                    )
                inserted += 1

        return inserted

    def get_linear_issues(
        self, assignee_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get Linear issues, optionally filtered by assignee."""
        with self._conn() as conn:
            cursor = self._cursor(conn)
            if assignee_name:
                if self.use_postgres:
                    cursor.execute(
                        "SELECT * FROM linear_issues WHERE assignee_name = %s ORDER BY updated_at DESC",
                        (assignee_name,),
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM linear_issues WHERE assignee_name = ? ORDER BY updated_at DESC",
                        (assignee_name,),
                    )
            else:
                cursor.execute("SELECT * FROM linear_issues ORDER BY updated_at DESC")
            return self._normalize_rows(cursor.fetchall())

    def get_linear_stats(self) -> Dict[str, Any]:
        """Get Linear issues statistics."""
        with self._conn() as conn:
            cursor = self._cursor(conn)
            if self.use_postgres:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN state_type = 'started' THEN 1 END) as in_progress,
                        COUNT(CASE WHEN state_type = 'unstarted' THEN 1 END) as todo,
                        COUNT(CASE WHEN state_type = 'backlog' THEN 1 END) as backlog,
                        COUNT(CASE WHEN assignee_name IS NOT NULL THEN 1 END) as assigned
                    FROM linear_issues
                """
                )
            else:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN state_type = 'started' THEN 1 END) as in_progress,
                        COUNT(CASE WHEN state_type = 'unstarted' THEN 1 END) as todo,
                        COUNT(CASE WHEN state_type = 'backlog' THEN 1 END) as backlog,
                        COUNT(CASE WHEN assignee_name IS NOT NULL THEN 1 END) as assigned
                    FROM linear_issues
                """
                )
            row = self._normalize_row(cursor.fetchone()) or {}
            return {
                "total": row.get("total", 0) or 0,
                "in_progress": row.get("in_progress", 0) or 0,
                "todo": row.get("todo", 0) or 0,
                "backlog": row.get("backlog", 0) or 0,
                "assigned": row.get("assigned", 0) or 0,
            }

    def insert_github_prs(self, prs: List[GitHubPullRequest]) -> int:
        """
        Insert GitHub pull requests into the database.
        Uses INSERT OR REPLACE to handle updates.
        Returns the number of PRs inserted/updated.
        """
        if not prs:
            return 0

        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        snapshot_date = now_dt.strftime("%Y-%m-%d")
        inserted = 0

        with self._conn() as conn:
            cursor = self._cursor(conn)
            for pr in prs:
                stored_at = now_dt if self.use_postgres else now_iso
                params = (
                    pr.id,
                    pr.number,
                    pr.title,
                    pr.body,
                    pr.state,
                    bool(pr.is_merged),
                    pr.url,
                    pr.repo_full_name,
                    pr.author,
                    pr.created_at,
                    pr.updated_at,
                    pr.closed_at,
                    pr.merged_at,
                    pr.base_branch,
                    pr.head_branch,
                    pr.merge_commit_sha,
                    pr.merge_method,
                    pr.merged_by,
                    pr.additions,
                    pr.deletions,
                    pr.changed_files,
                    pr.files_changed,
                    pr.review_comments,
                    pr.comments_count,
                    pr.commits_count,
                    pr.reviewers,
                    pr.approved_by,
                    bool(pr.is_draft),
                    snapshot_date,
                    stored_at,
                )
                if self.use_postgres:
                    cursor.execute(
                        """
                        INSERT INTO github_prs 
                        (id, number, title, body, state, is_merged, url, repo_full_name,
                         author, created_at, updated_at, closed_at, merged_at, base_branch,
                         head_branch, merge_commit_sha, merge_method, merged_by,
                         additions, deletions, changed_files, files_changed,
                         review_comments, comments_count, commits_count, reviewers, approved_by,
                         is_draft, snapshot_date, stored_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            number = EXCLUDED.number,
                            title = EXCLUDED.title,
                            body = EXCLUDED.body,
                            state = EXCLUDED.state,
                            is_merged = EXCLUDED.is_merged,
                            url = EXCLUDED.url,
                            repo_full_name = EXCLUDED.repo_full_name,
                            author = EXCLUDED.author,
                            created_at = EXCLUDED.created_at,
                            updated_at = EXCLUDED.updated_at,
                            closed_at = EXCLUDED.closed_at,
                            merged_at = EXCLUDED.merged_at,
                            base_branch = EXCLUDED.base_branch,
                            head_branch = EXCLUDED.head_branch,
                            merge_commit_sha = EXCLUDED.merge_commit_sha,
                            merge_method = EXCLUDED.merge_method,
                            merged_by = EXCLUDED.merged_by,
                            additions = EXCLUDED.additions,
                            deletions = EXCLUDED.deletions,
                            changed_files = EXCLUDED.changed_files,
                            files_changed = EXCLUDED.files_changed,
                            review_comments = EXCLUDED.review_comments,
                            comments_count = EXCLUDED.comments_count,
                            commits_count = EXCLUDED.commits_count,
                            reviewers = EXCLUDED.reviewers,
                            approved_by = EXCLUDED.approved_by,
                            is_draft = EXCLUDED.is_draft,
                            snapshot_date = EXCLUDED.snapshot_date,
                            stored_at = EXCLUDED.stored_at
                        """,
                        params,
                    )
                else:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO github_prs 
                        (id, number, title, body, state, is_merged, url, repo_full_name,
                         author, created_at, updated_at, closed_at, merged_at, base_branch,
                         head_branch, merge_commit_sha, merge_method, merged_by,
                         additions, deletions, changed_files, files_changed,
                         review_comments, comments_count, commits_count, reviewers, approved_by,
                         is_draft, snapshot_date, stored_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        params,
                    )
                inserted += 1

        return inserted

    def insert_github_issues(self, issues: List[GitHubIssue]) -> int:
        """
        Insert GitHub issues into the database.
        Uses INSERT OR REPLACE to handle updates.
        Returns the number of issues inserted/updated.
        """
        if not issues:
            return 0

        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        snapshot_date = now_dt.strftime("%Y-%m-%d")
        inserted = 0

        with self._conn() as conn:
            cursor = self._cursor(conn)
            for issue in issues:
                stored_at = now_dt if self.use_postgres else now_iso
                params = (
                    issue.id,
                    issue.number,
                    issue.title,
                    issue.body,
                    issue.state,
                    issue.url,
                    issue.repo_full_name,
                    issue.author,
                    issue.assignees,
                    issue.labels,
                    issue.created_at,
                    issue.updated_at,
                    issue.closed_at,
                    snapshot_date,
                    stored_at,
                )
                if self.use_postgres:
                    cursor.execute(
                        """
                        INSERT INTO github_issues 
                        (id, number, title, body, state, url, repo_full_name,
                         author, assignees, labels, created_at, updated_at, closed_at,
                         snapshot_date, stored_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            number = EXCLUDED.number,
                            title = EXCLUDED.title,
                            body = EXCLUDED.body,
                            state = EXCLUDED.state,
                            url = EXCLUDED.url,
                            repo_full_name = EXCLUDED.repo_full_name,
                            author = EXCLUDED.author,
                            assignees = EXCLUDED.assignees,
                            labels = EXCLUDED.labels,
                            created_at = EXCLUDED.created_at,
                            updated_at = EXCLUDED.updated_at,
                            closed_at = EXCLUDED.closed_at,
                            snapshot_date = EXCLUDED.snapshot_date,
                            stored_at = EXCLUDED.stored_at
                        """,
                        params,
                    )
                else:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO github_issues 
                        (id, number, title, body, state, url, repo_full_name,
                         author, assignees, labels, created_at, updated_at, closed_at,
                         snapshot_date, stored_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        params,
                    )
                inserted += 1

        return inserted

    def get_github_prs(
        self,
        repo_full_name: Optional[str] = None,
        state: Optional[str] = None,
        author: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get GitHub pull requests, optionally filtered."""
        with self._conn() as conn:
            cursor = self._cursor(conn)
            query = "SELECT * FROM github_prs WHERE 1=1"
            params: List[Any] = []

            if repo_full_name:
                query += (
                    " AND repo_full_name = %s"
                    if self.use_postgres
                    else " AND repo_full_name = ?"
                )
                params.append(repo_full_name)

            if state:
                query += " AND state = %s" if self.use_postgres else " AND state = ?"
                params.append(state)

            if author:
                query += " AND author = %s" if self.use_postgres else " AND author = ?"
                params.append(author)

            query += " ORDER BY updated_at DESC"

            cursor.execute(query, params)
            return self._normalize_rows(cursor.fetchall())

    def get_github_issues(
        self,
        repo_full_name: Optional[str] = None,
        state: Optional[str] = None,
        author: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get GitHub issues, optionally filtered."""
        with self._conn() as conn:
            cursor = self._cursor(conn)
            query = "SELECT * FROM github_issues WHERE 1=1"
            params: List[Any] = []

            if repo_full_name:
                query += (
                    " AND repo_full_name = %s"
                    if self.use_postgres
                    else " AND repo_full_name = ?"
                )
                params.append(repo_full_name)

            if state:
                query += " AND state = %s" if self.use_postgres else " AND state = ?"
                params.append(state)

            if author:
                query += " AND author = %s" if self.use_postgres else " AND author = ?"
                params.append(author)

            query += " ORDER BY updated_at DESC"

            cursor.execute(query, params)
            return self._normalize_rows(cursor.fetchall())

    def get_github_stats(self) -> Dict[str, Any]:
        """Get GitHub statistics."""
        with self._conn() as conn:
            cursor = self._cursor(conn)
            if self.use_postgres:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_prs,
                        COUNT(CASE WHEN state = 'open' THEN 1 END) as open_prs,
                        COUNT(CASE WHEN state = 'closed' AND is_merged THEN 1 END) as merged_prs,
                        COUNT(CASE WHEN state = 'closed' AND NOT is_merged THEN 1 END) as closed_prs
                    FROM github_prs
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_prs,
                        COUNT(CASE WHEN state = 'open' THEN 1 END) as open_prs,
                        COUNT(CASE WHEN state = 'closed' AND is_merged = 1 THEN 1 END) as merged_prs,
                        COUNT(CASE WHEN state = 'closed' AND is_merged = 0 THEN 1 END) as closed_prs
                    FROM github_prs
                """
                )
            pr_row = self._normalize_row(cursor.fetchone()) or {}

            if self.use_postgres:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_issues,
                        COUNT(CASE WHEN state = 'open' THEN 1 END) as open_issues,
                        COUNT(CASE WHEN state = 'closed' THEN 1 END) as closed_issues
                    FROM github_issues
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_issues,
                        COUNT(CASE WHEN state = 'open' THEN 1 END) as open_issues,
                        COUNT(CASE WHEN state = 'closed' THEN 1 END) as closed_issues
                    FROM github_issues
                """
                )
            issue_row = self._normalize_row(cursor.fetchone()) or {}

            return {
                "total_prs": pr_row.get("total_prs", 0) or 0,
                "open_prs": pr_row.get("open_prs", 0) or 0,
                "merged_prs": pr_row.get("merged_prs", 0) or 0,
                "closed_prs": pr_row.get("closed_prs", 0) or 0,
                "total_issues": issue_row.get("total_issues", 0) or 0,
                "open_issues": issue_row.get("open_issues", 0) or 0,
                "closed_issues": issue_row.get("closed_issues", 0) or 0,
            }

    def clear_all(self) -> None:
        """Clear all messages from the database. Use with caution!"""
        with self._conn() as conn:
            cursor = self._cursor(conn)
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM linear_issues")
            cursor.execute("DELETE FROM github_prs")
            cursor.execute("DELETE FROM github_issues")

    def log_decision(
        self,
        workflow_name: str,
        action_type: str,
        action_taken: str,
        reasoning: Optional[str] = None,
        confidence: Optional[float] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        entity_identifier: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Log an AI decision/action for audit purposes.

        Args:
            workflow_name: Name of the workflow (e.g., 'process', 'move_tickets')
            action_type: Type of action (e.g., 'create_ticket', 'update_ticket', 'move_ticket')
            action_taken: Description of what was done
            reasoning: AI reasoning for the decision
            confidence: Confidence level (0-1)
            entity_type: Type of entity (e.g., 'linear_ticket', 'slack_message')
            entity_id: Internal ID of the entity
            entity_identifier: Human-readable identifier (e.g., 'DATA-96')
            input_data: Input data used for the decision (will be JSON stringified)
            output_data: Output data from the decision (will be JSON stringified)

        Returns:
            ID of the logged decision
        """
        import json

        with self._conn() as conn:
            cursor = self._cursor(conn)
            created_at = datetime.now(timezone.utc)
            params = (
                workflow_name,
                action_type,
                entity_type,
                entity_id,
                entity_identifier,
                action_taken,
                reasoning,
                confidence,
                json.dumps(input_data) if input_data else None,
                json.dumps(output_data) if output_data else None,
                created_at if self.use_postgres else created_at.isoformat(),
            )
            if self.use_postgres:
                cursor.execute(
                    """
                    INSERT INTO decision_logs 
                    (workflow_name, action_type, entity_type, entity_id, entity_identifier,
                     action_taken, reasoning, confidence, input_data, output_data, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    params,
                )
                row = cursor.fetchone()
                return row["id"] if row else None
            else:
                cursor.execute(
                    """
                    INSERT INTO decision_logs 
                    (workflow_name, action_type, entity_type, entity_id, entity_identifier,
                     action_taken, reasoning, confidence, input_data, output_data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    params,
                )
                return cursor.lastrowid

    def get_decision_logs(
        self,
        workflow_name: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_identifier: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve decision logs with optional filtering.

        Args:
            workflow_name: Filter by workflow name
            entity_type: Filter by entity type
            entity_identifier: Filter by entity identifier (e.g., 'DATA-96')
            since: Only return logs since this datetime
            limit: Maximum number of logs to return

        Returns:
            List of decision log dictionaries
        """
        import json

        with self._conn() as conn:
            cursor = self._cursor(conn)
            query = "SELECT * FROM decision_logs WHERE 1=1"
            params: List[Any] = []

            if workflow_name:
                query += (
                    " AND workflow_name = %s"
                    if self.use_postgres
                    else " AND workflow_name = ?"
                )
                params.append(workflow_name)

            if entity_type:
                query += (
                    " AND entity_type = %s"
                    if self.use_postgres
                    else " AND entity_type = ?"
                )
                params.append(entity_type)

            if entity_identifier:
                query += (
                    " AND entity_identifier = %s"
                    if self.use_postgres
                    else " AND entity_identifier = ?"
                )
                params.append(entity_identifier)

            if since:
                query += (
                    " AND created_at >= %s"
                    if self.use_postgres
                    else " AND created_at >= ?"
                )
                params.append(since if self.use_postgres else since.isoformat())

            query += " ORDER BY created_at DESC"

            if limit:
                query += " LIMIT %s" if self.use_postgres else " LIMIT ?"
                params.append(limit)

            cursor.execute(query, params)
            logs = self._normalize_rows(cursor.fetchall())

            # Parse JSON fields
            for log in logs:
                if log.get("input_data"):
                    try:
                        log["input_data"] = json.loads(log["input_data"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                if log.get("output_data"):
                    try:
                        log["output_data"] = json.loads(log["output_data"])
                    except (json.JSONDecodeError, TypeError):
                        pass

            return logs
