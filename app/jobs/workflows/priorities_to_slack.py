"""Priorities to Slack workflow: ingest Linear data and post developer priorities to Slack channels."""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .ingestion.linear import LinearClient
from .ingestion.slack import SlackService


def get_developer_priorities(
    linear_api_key: Optional[str] = None,
    linear_team_id: Optional[str] = None,
    assignee_only: bool = False,
) -> Dict[str, Any]:
    """
    Fetch Linear issues and group by developer/assignee.

    Args:
        linear_api_key: Linear API key (optional, uses env if not provided)
        linear_team_id: Linear team ID (optional)
        assignee_only: If True, only fetch issues assigned to someone

    Returns:
        Dictionary with issues grouped by assignee
    """
    import os

    # Set Linear credentials if provided
    if linear_api_key:
        os.environ["LINEAR_API_KEY"] = linear_api_key
    if linear_team_id:
        os.environ["LINEAR_TEAM_ID"] = linear_team_id

    linear = LinearClient(api_key=linear_api_key, team_id=linear_team_id)

    # Fetch all open issues (or assignee-only if specified)
    issues = linear.list_open_issues(assignee_only=assignee_only)

    # Group issues by assignee
    by_assignee: Dict[str, List[Dict[str, Any]]] = {}
    unassigned: List[Dict[str, Any]] = []

    for issue in issues:
        assignee = issue.get("assignee")
        if assignee:
            assignee_name = assignee.get("name", "Unknown")
            if assignee_name not in by_assignee:
                by_assignee[assignee_name] = []
            by_assignee[assignee_name].append(issue)
        else:
            unassigned.append(issue)

    # Group each assignee's issues by state
    result: Dict[str, Dict[str, Any]] = {}
    for assignee_name, assignee_issues in by_assignee.items():
        in_progress = [
            i for i in assignee_issues if i.get("state", {}).get("type") == "started"
        ]
        todo = [
            i for i in assignee_issues if i.get("state", {}).get("type") == "unstarted"
        ]
        backlog = [
            i for i in assignee_issues if i.get("state", {}).get("type") == "backlog"
        ]

        result[assignee_name] = {
            "in_progress": in_progress,
            "todo": todo,
            "backlog": backlog,
            "total": len(assignee_issues),
        }

    return {
        "by_assignee": result,
        "unassigned": unassigned,
        "total_issues": len(issues),
        "total_developers": len(by_assignee),
    }


def format_priorities_blocks(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format developer priorities as Slack blocks for channel posting."""
    today = datetime.now(timezone.utc).strftime("%A, %B %d")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📋 Developer Priorities - {today}",
                "emoji": True,
            },
        },
        {"type": "divider"},
    ]

    by_assignee = data.get("by_assignee", {})
    unassigned = data.get("unassigned", [])

    # Sort developers by total issues (most active first)
    sorted_developers = sorted(
        by_assignee.items(),
        key=lambda x: x[1]["total"],
        reverse=True,
    )

    # Show each developer's priorities
    for assignee_name, dev_data in sorted_developers:
        in_progress = dev_data.get("in_progress", [])
        todo = dev_data.get("todo", [])
        backlog = dev_data.get("backlog", [])

        # Skip developers with no active work
        if not in_progress and not todo:
            continue

        # Developer header
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*👤 {assignee_name}*",
                },
            }
        )

        # In Progress
        if in_progress:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🔥 In Progress ({len(in_progress)})*",
                    },
                }
            )
            for issue in in_progress[:5]:  # Show top 5
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
            if len(in_progress) > 5:
                blocks.append(
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"_+ {len(in_progress) - 5} more in progress_",
                            }
                        ],
                    }
                )

        # Up Next
        if todo:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📋 Up Next ({len(todo)})*",
                    },
                }
            )
            for issue in todo[:3]:  # Show top 3
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• <{issue['url']}|{issue['identifier']}> {issue['title']}",
                        },
                    }
                )
            if len(todo) > 3:
                blocks.append(
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"_+ {len(todo) - 3} more in queue_",
                            }
                        ],
                    }
                )

        blocks.append({"type": "divider"})

    # Unassigned issues
    if unassigned:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚠️ Unassigned Issues ({len(unassigned)})*",
                },
            }
        )
        for issue in unassigned[:5]:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• <{issue['url']}|{issue['identifier']}> {issue['title']}",
                    },
                }
            )
        if len(unassigned) > 5:
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_+ {len(unassigned) - 5} more unassigned_",
                        }
                    ],
                }
            )
        blocks.append({"type": "divider"})

    # Footer
    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"🤖 _Sent by Corta • Total: {data.get('total_issues', 0)} issues across {data.get('total_developers', 0)} developers_",
                }
            ],
        }
    )

    return blocks


def post_priorities_to_slack(
    channel_id: str,
    slack_token: Optional[str] = None,
    linear_api_key: Optional[str] = None,
    linear_team_id: Optional[str] = None,
    assignee_only: bool = False,
) -> Dict[str, Any]:
    """
    Fetch Linear priorities and post to a Slack channel.

    Args:
        channel_id: Slack channel ID to post to
        slack_token: Slack bot token
        linear_api_key: Linear API key (optional, uses env if not provided)
        linear_team_id: Linear team ID (optional)
        assignee_only: If True, only show issues assigned to someone

    Returns:
        Result of the message send operation
    """
    # Fetch priorities from Linear
    priorities_data = get_developer_priorities(
        linear_api_key=linear_api_key,
        linear_team_id=linear_team_id,
        assignee_only=assignee_only,
    )

    # Format as Slack blocks
    blocks = format_priorities_blocks(priorities_data)

    # Post to Slack
    slack = SlackService(token=slack_token)
    result = slack.send_message(
        channel_id=channel_id,
        text="📋 Developer Priorities Update",
        blocks=blocks,
    )

    return {
        "status": "success",
        "channel_id": channel_id,
        "message_ts": result.get("ts"),
        "total_issues": priorities_data.get("total_issues", 0),
        "total_developers": priorities_data.get("total_developers", 0),
    }


if __name__ == "__main__":
    import sys
    import os

    # Allow running this file directly for testing
    channel_id = os.getenv("SLACK_CHANNEL_ID")
    if not channel_id:
        print("Error: SLACK_CHANNEL_ID environment variable required")
        sys.exit(1)

    print("📋 Fetching developer priorities from Linear...")
    priorities = get_developer_priorities()

    print(f"\n📊 Summary:")
    print(f"   Total issues: {priorities['total_issues']}")
    print(f"   Developers: {priorities['total_developers']}")
    print(f"   Unassigned: {len(priorities['unassigned'])}")

    print(f"\n👥 By Developer:")
    for assignee_name, dev_data in sorted(
        priorities["by_assignee"].items(),
        key=lambda x: x[1]["total"],
        reverse=True,
    ):
        in_progress = len(dev_data["in_progress"])
        todo = len(dev_data["todo"])
        print(f"   {assignee_name}: {in_progress} in progress, {todo} todo")

    if "--post" in sys.argv:
        print(f"\n📤 Posting to Slack channel {channel_id}...")
        result = post_priorities_to_slack(channel_id=channel_id)
        print(f"✅ Posted successfully! Message TS: {result.get('message_ts')}")
    else:
        print("\n💡 Add --post to actually post to Slack")
