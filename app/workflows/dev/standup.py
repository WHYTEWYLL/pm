"""Standup workflow: generate daily status report."""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ...storage.db import Database
from ...ingestion.linear import LinearClient
from ...ingestion.slack import SlackService


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


def publish_standup(
    channel_id: str, slack_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate and publish standup to Slack.

    Args:
        channel_id: Slack channel ID to post to
        slack_token: Optional Slack token (if not in env)
    """
    data = generate_standup()
    slack = SlackService(token=slack_token)

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 Daily Standup - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                "emoji": True,
            },
        },
        {"type": "divider"},
    ]

    # In Progress
    if data["in_progress"]:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🟢 In Progress ({len(data['in_progress'])})*",
                },
            }
        )
        for i in data["in_progress"]:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*<{i['url']}|{i['identifier']}>*: {i['title']}\n> State: {i['state']['name']}",
                    },
                }
            )

    # Todo
    if data["todo"]:
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🟡 Up Next ({len(data['todo'])})*",
                },
            }
        )
        # Show top 5
        for i in data["todo"][:5]:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<{i['url']}|{i['identifier']}>: {i['title']}",
                    },
                }
            )

    # Untracked Messages
    if data["untracked_messages"]:
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*⚠️ Untracked Conversations*"},
            }
        )
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "These discussions might need tickets:"}
                ],
            }
        )

        for msg in data["untracked_messages"][:3]:
            # Format link to message if we had workspace domain, for now just channel ref
            text = msg.get("text", "")[:100].replace("\n", " ") + "..."
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*#{msg.get('channel_name')}*: {text}",
                    },
                }
            )

    # Footer
    blocks.append({"type": "divider"})
    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Processed {data['total_messages']} messages today.",
                }
            ],
        }
    )

    return slack.send_message(channel_id, "Daily Standup Report", blocks=blocks)


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
