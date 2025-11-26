"""Standup workflow: send daily work reminders to developers via DM."""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ..storage.db import Database
from .ingestion.linear import LinearClient
from .ingestion.slack import SlackService


def generate_standup() -> Dict[str, Any]:
    """
    Generate daily standup data with issues and untracked conversations.

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


def format_morning_reminder_blocks(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format standup data as Slack blocks for a morning DM reminder."""
    today = datetime.now(timezone.utc).strftime("%A, %B %d")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"☀️ Good morning! Here's your focus for {today}",
                "emoji": True,
            },
        },
    ]

    # Currently working on
    if data["in_progress"]:
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔥 Continue working on ({len(data['in_progress'])})*",
                },
            }
        )
        for issue in data["in_progress"][:5]:
            state_name = issue.get("state", {}).get("name", "In Progress")
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• <{issue['url']}|{issue['identifier']}> {issue['title']}\n   _Status: {state_name}_",
                    },
                }
            )

    # Up next
    if data["todo"]:
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📋 Up next ({len(data['todo'])})*",
                },
            }
        )
        # Show top 3 todos
        for issue in data["todo"][:3]:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• <{issue['url']}|{issue['identifier']}> {issue['title']}",
                    },
                }
            )
        if len(data["todo"]) > 3:
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_+ {len(data['todo']) - 3} more in your queue_",
                        }
                    ],
                }
            )

    # No work assigned - encourage picking something
    if not data["in_progress"] and not data["todo"]:
        blocks.append({"type": "divider"})
        if data["backlog"]:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🎯 Nothing in progress!*\nHere are some tickets from your backlog to pick up:",
                    },
                }
            )
            for issue in data["backlog"][:3]:
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• <{issue['url']}|{issue['identifier']}> {issue['title']}",
                        },
                    }
                )
        else:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*✨ Your plate is clear!*\nNo tickets assigned. Time to pick up new work or help a teammate.",
                    },
                }
            )

    # Untracked conversations - things that might need tickets
    if data["untracked_messages"]:
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*💬 Untracked discussions ({len(data['untracked_messages'])})*",
                },
            }
        )
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "_These conversations might need tickets:_",
                    }
                ],
            }
        )
        for msg in data["untracked_messages"][:2]:
            text = msg.get("text", "")[:80].replace("\n", " ")
            channel = msg.get("channel_name", "unknown")
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• *#{channel}*: {text}...",
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
                    "text": "🤖 _Sent by Corta • Reply here if you need help_",
                }
            ],
        }
    )

    return blocks


def send_standup_dm(
    user_email: str,
    slack_token: Optional[str] = None,
    linear_api_key: Optional[str] = None,
    linear_team_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate and send a morning standup reminder to a user via Slack DM.

    Args:
        user_email: Email of the user to send the DM to
        slack_token: Slack bot token
        linear_api_key: Linear API key (optional, uses env if not provided)
        linear_team_id: Linear team ID (optional)

    Returns:
        Result of the message send operation
    """
    import os

    # Set Linear credentials if provided
    if linear_api_key:
        os.environ["LINEAR_API_KEY"] = linear_api_key
    if linear_team_id:
        os.environ["LINEAR_TEAM_ID"] = linear_team_id

    slack = SlackService(token=slack_token)

    # Find user by email
    user = slack.get_user_by_email(user_email)
    if not user:
        return {"status": "error", "message": f"User not found for email: {user_email}"}

    user_id = user.get("id")

    # Generate standup data
    data = generate_standup()

    # Format as blocks
    blocks = format_morning_reminder_blocks(data)

    # Send DM
    result = slack.send_dm(
        user_id=user_id,
        text="☀️ Here's your morning work reminder!",
        blocks=blocks,
    )

    return {
        "status": "success",
        "user_email": user_email,
        "user_id": user_id,
        "in_progress": len(data["in_progress"]),
        "todo": len(data["todo"]),
        "message_ts": result.get("ts"),
    }


def send_standup_dm_by_user_id(
    slack_user_id: str,
    slack_token: Optional[str] = None,
    standup_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send a morning standup reminder to a user by their Slack user ID.

    Args:
        slack_user_id: Slack user ID to send the DM to
        slack_token: Slack bot token
        standup_data: Pre-generated standup data (optional)

    Returns:
        Result of the message send operation
    """
    slack = SlackService(token=slack_token)

    # Generate standup data if not provided
    data = standup_data or generate_standup()

    # Format as blocks
    blocks = format_morning_reminder_blocks(data)

    # Send DM
    result = slack.send_dm(
        user_id=slack_user_id,
        text="☀️ Here's your morning work reminder!",
        blocks=blocks,
    )

    return {
        "status": "success",
        "user_id": slack_user_id,
        "in_progress": len(data["in_progress"]),
        "todo": len(data["todo"]),
        "message_ts": result.get("ts"),
    }


# Legacy function for backward compatibility
def publish_standup(
    channel_id: str, slack_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate and publish standup to a Slack channel.

    DEPRECATED: Use send_standup_dm for personalized dev reminders.

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
