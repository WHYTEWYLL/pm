"""Standup workflow: generate daily status report."""

from __future__ import annotations
from typing import Dict, Any, List

from ...storage.db import Database
from ...ingestion.linear import LinearClient


def generate_standup() -> Dict[str, Any]:
    """
    Generate daily standup report with issues and untracked conversations.

    Returns:
        Dictionary with standup data
    """
    # Get Linear issues
    linear = LinearClient()
    my_issues = linear.list_open_issues(assignee_only=True)

    # Group by state
    in_progress = [i for i in my_issues if i.get("state", {}).get("type") == "started"]
    todo = [i for i in my_issues if i.get("state", {}).get("type") == "unstarted"]
    backlog = [i for i in my_issues if i.get("state", {}).get("type") == "backlog"]

    # Get all issue identifiers for matching
    issue_identifiers = {issue.get("identifier") for issue in my_issues}

    # Check unprocessed messages
    db = Database()
    messages = db.get_unprocessed_messages()

    # Flag conversations without issue mentions
    untracked: List[Dict[str, Any]] = []
    has_issue: List[Dict[str, Any]] = []

    for msg in messages:
        text = msg.get("text", "")

        # Check if any issue is mentioned
        mentioned = any(iid in text for iid in issue_identifiers)

        if mentioned:
            has_issue.append(msg)
        else:
            # Skip short operational messages
            if len(text) > 50 and not text.startswith(("<@", "http")):
                untracked.append(msg)

    return {
        "in_progress": in_progress,
        "todo": todo,
        "backlog": backlog,
        "untracked_messages": untracked,
        "tracked_messages": has_issue,
        "total_messages": len(messages),
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    print(f"\n📊 DAILY STANDUP - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n")

    data = generate_standup()

    # In Progress
    print(f"🟢 IN PROGRESS ({len(data['in_progress'])}):")
    for i in data["in_progress"]:
        print(f"  • {i['identifier']}: {i['title']}")

    # TODO
    print(f"\n🟡 TODO ({len(data['todo'])}):")
    for i in data["todo"][:5]:
        print(f"  • {i['identifier']}: {i['title']}")

    # Backlog
    print(f"\n⚪ BACKLOG ({len(data['backlog'])}):")
    for i in data["backlog"][:3]:
        print(f"  • {i['identifier']}: {i['title']}")

    # Slack activity
    tracked = len(data["tracked_messages"])
    untracked = len(data["untracked_messages"])

    print(f"\n💬 SLACK ACTIVITY:")
    print(f"  ✅ {tracked} tracked messages")
    print(f"  ⚠️  {untracked} untracked messages")

    if untracked > 0:
        print(f"\n⚠️  Sample untracked conversations:")
        for msg in data["untracked_messages"][:3]:
            text = msg.get("text", "")[:80].replace("\n", " ")
            print(f"  • [{msg.get('channel_name')}] {text}...")

    print("\n" + "=" * 60)
