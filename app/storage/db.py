from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from contextlib import contextmanager

from ..config import settings
from ..models import SlackMessage, LinearIssue, GitHubPullRequest, GitHubIssue


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.db_file_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self):
        """Context manager for database connections."""
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
        """Initialize database schema if it doesn't exist."""
        with self._conn() as conn:
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

            # Index for fast 24h queries
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON messages(created_at)
            """
            )

            # Index for unprocessed messages
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_processed 
                ON messages(processed, created_at)
            """
            )

            # Linear issues table
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

            # Index for Linear issues by state
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_linear_state 
                ON linear_issues(state_name, state_type)
            """
            )

            # Index for Linear issues by assignee
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_linear_assignee 
                ON linear_issues(assignee_name)
            """
            )

            # Add new columns if they don't exist (for existing tables)
            try:
                conn.execute(
                    "ALTER TABLE linear_issues ADD COLUMN original_created_at TEXT"
                )
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute(
                    "ALTER TABLE linear_issues ADD COLUMN original_updated_at TEXT"
                )
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute("ALTER TABLE linear_issues ADD COLUMN snapshot_date TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            # GitHub pull requests table
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

            # Index for GitHub PRs by repo and state
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_github_pr_repo_state 
                ON github_prs(repo_full_name, state)
            """
            )

            # Index for GitHub PRs by author
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_github_pr_author 
                ON github_prs(author)
            """
            )

            # Add new columns if they don't exist (for existing tables)
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
                    pass  # Column already exists

            # GitHub issues table
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

            # Index for GitHub issues by repo and state
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_github_issue_repo_state 
                ON github_issues(repo_full_name, state)
            """
            )

            # Index for GitHub issues by author
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_github_issue_author 
                ON github_issues(author)
            """
            )

            # Decision/audit log table for tracking AI decisions
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

            # Index for decision logs by workflow and date
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_decision_logs_workflow_date 
                ON decision_logs(workflow_name, created_at)
            """
            )

            # Index for decision logs by entity
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

        with self._conn() as conn:
            cursor = conn.cursor()
            inserted = 0

            for msg in messages:
                created_at = datetime.fromtimestamp(msg.ts, tz=timezone.utc).isoformat()

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
                        created_at,
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
            query = "SELECT * FROM messages WHERE processed = 0"
            params = []

            if since:
                query += " AND created_at >= ?"
                params.append(since.isoformat())

            query += " ORDER BY ts ASC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def get_messages_since(
        self, since: datetime, processed: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all messages since a given datetime.
        Optionally filter by processed status.
        """
        with self._conn() as conn:
            query = "SELECT * FROM messages WHERE created_at >= ?"
            params = [since.isoformat()]

            if processed is not None:
                query += " AND processed = ?"
                params.append(1 if processed else 0)

            query += " ORDER BY ts ASC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def mark_as_processed(self, channel_id: str, ts: float) -> None:
        """Mark a single message as processed."""
        with self._conn() as conn:
            conn.execute(
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
            conn.executemany(
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
            cursor = conn.execute(
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
            row = cursor.fetchone()

            return {
                "total": row["total"],
                "processed": row["processed"],
                "unprocessed": row["unprocessed"],
                "oldest": row["oldest"],
                "newest": row["newest"],
            }

    def insert_linear_issues(self, issues: List[LinearIssue]) -> int:
        """
        Insert Linear issues into the database.
        Uses INSERT OR REPLACE to handle updates.
        Returns the number of issues inserted/updated.
        """
        if not issues:
            return 0

        now = datetime.now(timezone.utc).isoformat()
        snapshot_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        inserted = 0

        with self._conn() as conn:
            for issue in issues:
                conn.execute(
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
                        snapshot_date,  # snapshot_date (today's date)
                        now,  # created_at (when we stored it)
                        now,  # updated_at (when we stored it)
                    ),
                )
                inserted += 1

        return inserted

    def get_linear_issues(
        self, assignee_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get Linear issues, optionally filtered by assignee."""
        with self._conn() as conn:
            if assignee_name:
                cursor = conn.execute(
                    "SELECT * FROM linear_issues WHERE assignee_name = ? ORDER BY updated_at DESC",
                    (assignee_name,),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM linear_issues ORDER BY updated_at DESC"
                )

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_linear_stats(self) -> Dict[str, Any]:
        """Get Linear issues statistics."""
        with self._conn() as conn:
            cursor = conn.execute(
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
            row = cursor.fetchone()
            return {
                "total": row["total"],
                "in_progress": row["in_progress"],
                "todo": row["todo"],
                "backlog": row["backlog"],
                "assigned": row["assigned"],
            }

    def insert_github_prs(self, prs: List[GitHubPullRequest]) -> int:
        """
        Insert GitHub pull requests into the database.
        Uses INSERT OR REPLACE to handle updates.
        Returns the number of PRs inserted/updated.
        """
        if not prs:
            return 0

        now = datetime.now(timezone.utc).isoformat()
        snapshot_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        inserted = 0

        with self._conn() as conn:
            for pr in prs:
                conn.execute(
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
                    (
                        pr.id,
                        pr.number,
                        pr.title,
                        pr.body,
                        pr.state,
                        1 if pr.is_merged else 0,
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
                        1 if pr.is_draft else 0,
                        snapshot_date,
                        now,
                    ),
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

        now = datetime.now(timezone.utc).isoformat()
        snapshot_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        inserted = 0

        with self._conn() as conn:
            for issue in issues:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO github_issues 
                    (id, number, title, body, state, url, repo_full_name,
                     author, assignees, labels, created_at, updated_at, closed_at,
                     snapshot_date, stored_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
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
                        now,
                    ),
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
            query = "SELECT * FROM github_prs WHERE 1=1"
            params = []

            if repo_full_name:
                query += " AND repo_full_name = ?"
                params.append(repo_full_name)

            if state:
                query += " AND state = ?"
                params.append(state)

            if author:
                query += " AND author = ?"
                params.append(author)

            query += " ORDER BY updated_at DESC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_github_issues(
        self,
        repo_full_name: Optional[str] = None,
        state: Optional[str] = None,
        author: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get GitHub issues, optionally filtered."""
        with self._conn() as conn:
            query = "SELECT * FROM github_issues WHERE 1=1"
            params = []

            if repo_full_name:
                query += " AND repo_full_name = ?"
                params.append(repo_full_name)

            if state:
                query += " AND state = ?"
                params.append(state)

            if author:
                query += " AND author = ?"
                params.append(author)

            query += " ORDER BY updated_at DESC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_github_stats(self) -> Dict[str, Any]:
        """Get GitHub statistics."""
        with self._conn() as conn:
            # PR stats
            pr_cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_prs,
                    COUNT(CASE WHEN state = 'open' THEN 1 END) as open_prs,
                    COUNT(CASE WHEN state = 'closed' AND is_merged = 1 THEN 1 END) as merged_prs,
                    COUNT(CASE WHEN state = 'closed' AND is_merged = 0 THEN 1 END) as closed_prs
                FROM github_prs
            """
            )
            pr_row = pr_cursor.fetchone()

            # Issue stats
            issue_cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_issues,
                    COUNT(CASE WHEN state = 'open' THEN 1 END) as open_issues,
                    COUNT(CASE WHEN state = 'closed' THEN 1 END) as closed_issues
                FROM github_issues
            """
            )
            issue_row = issue_cursor.fetchone()

            return {
                "total_prs": pr_row["total_prs"] or 0,
                "open_prs": pr_row["open_prs"] or 0,
                "merged_prs": pr_row["merged_prs"] or 0,
                "closed_prs": pr_row["closed_prs"] or 0,
                "total_issues": issue_row["total_issues"] or 0,
                "open_issues": issue_row["open_issues"] or 0,
                "closed_issues": issue_row["closed_issues"] or 0,
            }

    def clear_all(self) -> None:
        """Clear all messages from the database. Use with caution!"""
        with self._conn() as conn:
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM linear_issues")
            conn.execute("DELETE FROM github_prs")
            conn.execute("DELETE FROM github_issues")

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
            cursor = conn.execute(
                """
                INSERT INTO decision_logs 
                (workflow_name, action_type, entity_type, entity_id, entity_identifier,
                 action_taken, reasoning, confidence, input_data, output_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
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
                    datetime.now(timezone.utc).isoformat(),
                ),
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
            query = "SELECT * FROM decision_logs WHERE 1=1"
            params = []

            if workflow_name:
                query += " AND workflow_name = ?"
                params.append(workflow_name)

            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type)

            if entity_identifier:
                query += " AND entity_identifier = ?"
                params.append(entity_identifier)

            if since:
                query += " AND created_at >= ?"
                params.append(since.isoformat())

            query += " ORDER BY created_at DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            logs = [dict(row) for row in rows]

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
