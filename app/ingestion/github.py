from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from github import Github
from github.GithubException import GithubException

from ..config import settings
from ..models import GitHubPullRequest, GitHubIssue


class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.github_token
        if not self.token:
            raise ValueError("Missing GITHUB_TOKEN")
        self.client = Github(self.token)
        self._user = None

    def get_user(self):
        """Get the authenticated user."""
        if self._user is None:
            self._user = self.client.get_user()
        return self._user

    def get_repositories(
        self, owner: Optional[str] = None, repo_names: Optional[List[str]] = None
    ) -> List[Any]:
        """
        Get repositories to fetch activity from.

        Args:
            owner: If provided, only fetch from this owner/org
            repo_names: If provided, only fetch these specific repos (format: "owner/repo")

        Returns:
            List of Repository objects
        """
        repos = []

        if repo_names:
            # Fetch specific repositories
            for repo_name in repo_names:
                try:
                    repo = self.client.get_repo(repo_name)
                    repos.append(repo)
                except GithubException as e:
                    print(f"⚠️  Could not fetch repo {repo_name}: {e}")
        elif owner:
            # Fetch all repos from an owner/org
            try:
                org = self.client.get_organization(owner)
                repos = list(org.get_repos())
            except GithubException:
                # If not an org, try as a user
                user = self.client.get_user(owner)
                repos = list(user.get_repos())
        else:
            # Fetch all repos the authenticated user has access to
            user = self.get_user()
            repos = list(user.get_repos())

        return repos

    def list_pull_requests(
        self,
        owner: Optional[str] = None,
        repo_names: Optional[List[str]] = None,
        state: str = "all",  # all, open, closed
        since: Optional[datetime] = None,
    ) -> List[GitHubPullRequest]:
        """
        List pull requests from specified repositories.

        Args:
            owner: If provided, only fetch from this owner/org
            repo_names: If provided, only fetch these specific repos
            state: Filter by state (all, open, closed)
            since: Only fetch PRs updated since this datetime

        Returns:
            List of GitHubPullRequest objects
        """
        repos = self.get_repositories(owner=owner, repo_names=repo_names)
        all_prs = []

        for repo in repos:
            try:
                prs = repo.get_pulls(state=state, sort="updated", direction="desc")

                for pr in prs:
                    # Filter by since if provided
                    if since and pr.updated_at < since:
                        continue

                    # Fetch detailed PR information
                    try:
                        # Collect all comments (issue comments + review comments)
                        comments_text = []
                        pr_body = pr.body or ""

                        # Get issue comments (general comments)
                        try:
                            issue_comments = pr.get_issue_comments()
                            for comment in issue_comments:
                                comment_author = (
                                    comment.user.login if comment.user else "Unknown"
                                )
                                comment_date = (
                                    comment.created_at.isoformat()
                                    if comment.created_at
                                    else ""
                                )
                                comments_text.append(
                                    f"\n\n---\n💬 Comment by {comment_author} on {comment_date}:\n{comment.body}"
                                )
                        except GithubException:
                            pass

                        # Get review comments (code review comments)
                        try:
                            review_comments = pr.get_review_comments()
                            for comment in review_comments:
                                comment_author = (
                                    comment.user.login if comment.user else "Unknown"
                                )
                                comment_date = (
                                    comment.created_at.isoformat()
                                    if comment.created_at
                                    else ""
                                )
                                file_info = (
                                    f" (File: {comment.path}, Line: {comment.line})"
                                    if comment.path
                                    else ""
                                )
                                comments_text.append(
                                    f"\n\n---\n🔍 Review comment by {comment_author} on {comment_date}{file_info}:\n{comment.body}"
                                )
                        except GithubException:
                            pass

                        # Combine PR body with all comments
                        full_description = pr_body + "".join(comments_text)

                        # Get files changed (limited to first 50 files for performance)
                        files_changed_list = []
                        try:
                            files = pr.get_files()
                            file_count = 0
                            for file in files:
                                file_count += 1
                                if file_count <= 50:  # Limit to avoid huge strings
                                    files_changed_list.append(file.filename)
                            changed_files_count = file_count
                            files_changed_str = ",".join(files_changed_list)
                            if file_count > 50:
                                files_changed_str += f",... (+{file_count - 50} more)"
                        except GithubException:
                            # If we can't get files, use the stats from the PR object
                            changed_files_count = pr.changed_files
                            files_changed_str = None

                        # Get reviewers and approvals
                        reviewers_list = []
                        approved_by_list = []
                        try:
                            reviews = pr.get_reviews()
                            seen_reviewers = set()
                            for review in reviews:
                                reviewer = review.user.login if review.user else None
                                if reviewer and reviewer not in seen_reviewers:
                                    reviewers_list.append(reviewer)
                                    seen_reviewers.add(reviewer)
                                    if review.state == "APPROVED":
                                        approved_by_list.append(reviewer)
                        except GithubException:
                            pass

                        # Get commits count
                        commits_count = None
                        try:
                            commits = pr.get_commits()
                            commits_count = commits.totalCount
                        except GithubException:
                            pass

                        # Get merge information
                        merge_commit_sha = None
                        merge_method = None
                        merged_by = None
                        if pr.merged:
                            try:
                                merge_commit_sha = pr.merge_commit_sha
                                # Try to get merge method from the merge commit
                                if merge_commit_sha:
                                    try:
                                        commit = repo.get_commit(merge_commit_sha)
                                        # Check parents count to infer merge method
                                        # 2 parents = merge commit, 1 parent = squash/rebase
                                        if commit.parents and len(commit.parents) > 1:
                                            merge_method = "merge"
                                        else:
                                            # Could be squash or rebase, but hard to distinguish
                                            merge_method = "squash_or_rebase"
                                    except GithubException:
                                        pass
                                # Get merged_by from the PR
                                if pr.merged_by:
                                    merged_by = pr.merged_by.login
                            except GithubException:
                                pass

                        github_pr = GitHubPullRequest(
                            id=pr.id,
                            number=pr.number,
                            title=pr.title,
                            body=full_description,  # Include all comments in body
                            state=pr.state,
                            is_merged=pr.merged,
                            url=pr.html_url,
                            repo_full_name=pr.base.repo.full_name,
                            author=pr.user.login if pr.user else None,
                            created_at=(
                                pr.created_at.isoformat() if pr.created_at else ""
                            ),
                            updated_at=(
                                pr.updated_at.isoformat() if pr.updated_at else ""
                            ),
                            closed_at=(
                                pr.closed_at.isoformat() if pr.closed_at else None
                            ),
                            merged_at=(
                                pr.merged_at.isoformat() if pr.merged_at else None
                            ),
                            base_branch=pr.base.ref if pr.base else None,
                            head_branch=pr.head.ref if pr.head else None,
                            # Merge information
                            merge_commit_sha=merge_commit_sha,
                            merge_method=merge_method,
                            merged_by=merged_by,
                            # Code changes
                            additions=pr.additions,
                            deletions=pr.deletions,
                            changed_files=changed_files_count,
                            files_changed=files_changed_str,
                            # Review information
                            review_comments=pr.review_comments,
                            comments_count=pr.comments,
                            commits_count=commits_count,
                            reviewers=(
                                ",".join(reviewers_list) if reviewers_list else None
                            ),
                            approved_by=(
                                ",".join(approved_by_list) if approved_by_list else None
                            ),
                            # Draft status
                            is_draft=pr.draft if hasattr(pr, "draft") else False,
                        )
                        all_prs.append(github_pr)
                    except GithubException as e:
                        print(
                            f"⚠️  Could not fetch detailed info for PR #{pr.number}: {e}"
                        )
                        # Fallback to basic PR info (try to get comments even in fallback)
                        comments_text = []
                        pr_body = pr.body or ""
                        try:
                            issue_comments = pr.get_issue_comments()
                            for comment in issue_comments:
                                comment_author = (
                                    comment.user.login if comment.user else "Unknown"
                                )
                                comment_date = (
                                    comment.created_at.isoformat()
                                    if comment.created_at
                                    else ""
                                )
                                comments_text.append(
                                    f"\n\n---\n💬 Comment by {comment_author} on {comment_date}:\n{comment.body}"
                                )
                        except GithubException:
                            pass

                        try:
                            review_comments = pr.get_review_comments()
                            for comment in review_comments:
                                comment_author = (
                                    comment.user.login if comment.user else "Unknown"
                                )
                                comment_date = (
                                    comment.created_at.isoformat()
                                    if comment.created_at
                                    else ""
                                )
                                file_info = (
                                    f" (File: {comment.path}, Line: {comment.line})"
                                    if comment.path
                                    else ""
                                )
                                comments_text.append(
                                    f"\n\n---\n🔍 Review comment by {comment_author} on {comment_date}{file_info}:\n{comment.body}"
                                )
                        except GithubException:
                            pass

                        full_description = pr_body + "".join(comments_text)

                        github_pr = GitHubPullRequest(
                            id=pr.id,
                            number=pr.number,
                            title=pr.title,
                            body=full_description,
                            state=pr.state,
                            is_merged=pr.merged,
                            url=pr.html_url,
                            repo_full_name=pr.base.repo.full_name,
                            author=pr.user.login if pr.user else None,
                            created_at=(
                                pr.created_at.isoformat() if pr.created_at else ""
                            ),
                            updated_at=(
                                pr.updated_at.isoformat() if pr.updated_at else ""
                            ),
                            closed_at=(
                                pr.closed_at.isoformat() if pr.closed_at else None
                            ),
                            merged_at=(
                                pr.merged_at.isoformat() if pr.merged_at else None
                            ),
                            base_branch=pr.base.ref if pr.base else None,
                            head_branch=pr.head.ref if pr.head else None,
                        )
                        all_prs.append(github_pr)

            except GithubException as e:
                print(f"⚠️  Could not fetch PRs from {repo.full_name}: {e}")

        return all_prs

    def list_issues(
        self,
        owner: Optional[str] = None,
        repo_names: Optional[List[str]] = None,
        state: str = "all",  # all, open, closed
        since: Optional[datetime] = None,
    ) -> List[GitHubIssue]:
        """
        List issues from specified repositories.

        Args:
            owner: If provided, only fetch from this owner/org
            repo_names: If provided, only fetch these specific repos
            state: Filter by state (all, open, closed)
            since: Only fetch issues updated since this datetime

        Returns:
            List of GitHubIssue objects
        """
        repos = self.get_repositories(owner=owner, repo_names=repo_names)
        all_issues = []

        for repo in repos:
            try:
                issues = repo.get_issues(state=state, sort="updated", direction="desc")

                for issue in issues:
                    # Skip pull requests (they're issues too)
                    if issue.pull_request:
                        continue

                    # Filter by since if provided
                    if since and issue.updated_at < since:
                        continue

                    assignees = (
                        [a.login for a in issue.assignees] if issue.assignees else []
                    )
                    labels = [l.name for l in issue.labels] if issue.labels else []

                    github_issue = GitHubIssue(
                        id=issue.id,
                        number=issue.number,
                        title=issue.title,
                        body=issue.body,
                        state=issue.state,
                        url=issue.html_url,
                        repo_full_name=repo.full_name,
                        author=issue.user.login if issue.user else None,
                        assignees=",".join(assignees) if assignees else None,
                        labels=",".join(labels) if labels else None,
                        created_at=(
                            issue.created_at.isoformat() if issue.created_at else ""
                        ),
                        updated_at=(
                            issue.updated_at.isoformat() if issue.updated_at else ""
                        ),
                        closed_at=(
                            issue.closed_at.isoformat() if issue.closed_at else None
                        ),
                    )
                    all_issues.append(github_issue)

            except GithubException as e:
                print(f"⚠️  Could not fetch issues from {repo.full_name}: {e}")

        return all_issues


def run_ingestion(
    owner: Optional[str] = None,
    repo_names: Optional[List[str]] = None,
    state: str = "all",
    store_in_db: bool = True,
    include_prs: bool = True,
    include_issues: bool = True,
) -> Dict[str, Any]:
    """
    Main entry point for GitHub ingestion.

    Fetches GitHub PRs and issues and optionally stores them in the database.

    Args:
        owner: If provided, only fetch from this owner/org
        repo_names: If provided, only fetch these specific repos (format: "owner/repo")
        state: Filter by state (all, open, closed)
        store_in_db: Whether to store in the database
        include_prs: Whether to fetch pull requests
        include_issues: Whether to fetch issues

    Returns:
        Dict with PRs, issues, stats, and database info
    """
    from ..storage.db import Database

    client = GitHubClient()

    # Fetch PRs updated in the last 24 hours
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    prs = []
    issues = []

    if include_prs:
        print("🔄 Fetching GitHub pull requests (last 24h, open and closed)...")
        # Always fetch both open and closed for last 24h
        prs = client.list_pull_requests(
            owner=owner, repo_names=repo_names, state="all", since=since
        )
        print(f"   Found {len(prs)} pull requests")

    if include_issues:
        print("🔄 Fetching GitHub issues...")
        issues = client.list_issues(
            owner=owner, repo_names=repo_names, state=state, since=since
        )
        print(f"   Found {len(issues)} issues")

    # Store in database if requested
    stored_prs = 0
    stored_issues = 0
    db_stats = {}
    if store_in_db:
        db = Database()

        if prs:
            stored_prs = db.insert_github_prs(prs)

        if issues:
            stored_issues = db.insert_github_issues(issues)

        db_stats = db.get_github_stats()

    # Group by state
    prs_by_state = {}
    for pr in prs:
        state_key = "merged" if pr.is_merged else pr.state
        prs_by_state[state_key] = prs_by_state.get(state_key, 0) + 1

    issues_by_state = {}
    for issue in issues:
        issues_by_state[issue.state] = issues_by_state.get(issue.state, 0) + 1

    return {
        "prs": prs,
        "issues": issues,
        "prs_by_state": prs_by_state,
        "issues_by_state": issues_by_state,
        "total_prs": len(prs),
        "total_issues": len(issues),
        "stored_prs": stored_prs,
        "stored_issues": stored_issues,
        "db_stats": db_stats,
    }


if __name__ == "__main__":
    # Allow running this file directly
    import sys

    # Parse command line arguments
    owner = None
    repos = None
    state = "all"
    no_store = "--no-store" in sys.argv
    no_prs = "--no-prs" in sys.argv
    no_issues = "--no-issues" in sys.argv

    # Parse --owner flag
    if "--owner" in sys.argv:
        idx = sys.argv.index("--owner")
        if idx + 1 < len(sys.argv):
            owner = sys.argv[idx + 1]

    # Parse --repos flag (comma-separated)
    if "--repos" in sys.argv:
        idx = sys.argv.index("--repos")
        if idx + 1 < len(sys.argv):
            repos = [r.strip() for r in sys.argv[idx + 1].split(",")]

    # Parse --state flag
    if "--state" in sys.argv:
        idx = sys.argv.index("--state")
        if idx + 1 < len(sys.argv):
            state = sys.argv[idx + 1]

    print("🔄 Running GitHub ingestion...")
    result = run_ingestion(
        owner=owner,
        repo_names=repos,
        state=state,
        store_in_db=not no_store,
        include_prs=not no_prs,
        include_issues=not no_issues,
    )

    print(f"\n📋 Pull Requests: {result['total_prs']}")
    if result["prs_by_state"]:
        for state_key, count in result["prs_by_state"].items():
            print(f"   {state_key}: {count}")

    # Group PRs by repository
    prs_by_repo = {}
    for pr in result["prs"]:
        repo = pr.repo_full_name
        if repo not in prs_by_repo:
            prs_by_repo[repo] = []
        prs_by_repo[repo].append(pr)

    if prs_by_repo:
        print(f"\n📦 PRs by Repository:")
        for repo, prs in prs_by_repo.items():
            print(f"   {repo}: {len(prs)} PR(s)")

    # Show sample PR details if any were fetched
    if result["prs"] and len(result["prs"]) > 0:
        print(f"\n📝 PR details:")
        for pr in result["prs"]:  # Show all PRs
            print(f"\n   #{pr.number}: {pr.title}")
            print(f"      📦 Repo: {pr.repo_full_name}")
            print(f"      👤 Author: {pr.author}")
            if pr.is_merged:
                print(f"      ✅ Merged by {pr.merged_by} ({pr.merge_method})")
            elif pr.is_draft:
                print(f"      📝 Draft")
            if pr.additions and pr.deletions:
                print(
                    f"      📊 +{pr.additions}/-{pr.deletions} lines in {pr.changed_files} files"
                )
            if pr.commits_count:
                print(f"      🔀 {pr.commits_count} commits")
            if pr.approved_by:
                print(f"      ✅ Approved by: {pr.approved_by}")
            if pr.reviewers:
                print(f"      👥 Reviewers: {pr.reviewers}")
            # Show comment count if available
            if pr.body and "---\n💬" in pr.body:
                comment_count = pr.body.count("---\n💬") + pr.body.count("---\n🔍")
                print(f"      💬 {comment_count} comments included in description")

    print(f"\n📋 Issues: {result['total_issues']}")
    if result["issues_by_state"]:
        for state_key, count in result["issues_by_state"].items():
            print(f"   {state_key}: {count}")

    print(
        f"\n💾 Stored in DB: {result['stored_prs']} PRs, {result['stored_issues']} issues"
    )

    if result.get("db_stats"):
        stats = result["db_stats"]
        print(f"\n📊 Database stats:")
        print(f"   Total PRs: {stats.get('total_prs', 0)}")
        print(f"   Open PRs: {stats.get('open_prs', 0)}")
        print(f"   Merged PRs: {stats.get('merged_prs', 0)}")
        print(f"   Total Issues: {stats.get('total_issues', 0)}")
