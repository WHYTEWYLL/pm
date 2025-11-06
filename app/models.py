"""Data models for the PM assistant."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class SlackMessage:
    """Represents a Slack message."""

    channel_id: str
    channel_name: str
    ts: float
    user: Optional[str]
    text: str
    is_dm: bool
    thread_ts: Optional[str] = None
    is_thread_reply: bool = False


@dataclass
class LinearIssue:
    """Represents a Linear issue."""

    id: str
    identifier: str
    title: str
    description: Optional[str]
    state_name: str
    state_type: str
    url: str
    assignee_name: Optional[str]
    parent_id: Optional[str] = None
    parent_title: Optional[str] = None
    original_created_at: Optional[str] = None
    original_updated_at: Optional[str] = None


@dataclass
class GitHubPullRequest:
    """Represents a GitHub Pull Request with detailed information."""

    id: int
    number: int
    title: str
    body: Optional[str]
    state: str  # open, closed
    is_merged: bool
    url: str
    repo_full_name: str  # owner/repo
    author: Optional[str]
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    merged_at: Optional[str] = None
    base_branch: Optional[str] = None
    head_branch: Optional[str] = None
    # Merge information
    merge_commit_sha: Optional[str] = None
    merge_method: Optional[str] = None  # merge, squash, rebase
    merged_by: Optional[str] = None
    # Code changes
    additions: Optional[int] = None
    deletions: Optional[int] = None
    changed_files: Optional[int] = None
    files_changed: Optional[str] = None  # comma-separated list of file paths
    # Review information
    review_comments: Optional[int] = None
    comments_count: Optional[int] = None
    commits_count: Optional[int] = None
    reviewers: Optional[str] = None  # comma-separated list of reviewer usernames
    approved_by: Optional[str] = None  # comma-separated list of approvers
    # Draft status
    is_draft: bool = False


@dataclass
class GitHubIssue:
    """Represents a GitHub Issue."""

    id: int
    number: int
    title: str
    body: Optional[str]
    state: str  # open, closed
    url: str
    repo_full_name: str  # owner/repo
    author: Optional[str]
    created_at: str
    updated_at: str
    assignees: Optional[str] = None  # comma-separated
    labels: Optional[str] = None  # comma-separated
    closed_at: Optional[str] = None
