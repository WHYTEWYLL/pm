"""Process workflow: analyze messages and sync with Linear."""

from __future__ import annotations
import re
from typing import Dict, Any

from ..storage.db import Database
from ..ingestion.linear import LinearClient
from .ai.analyzer import MessageAnalyzer


ISSUE_KEY_RE = re.compile(r"\b([A-Z]{2,}-\d+)\b")


def process_messages(dry_run: bool = True, use_ai: bool = True) -> Dict[str, Any]:
    """
    Process unprocessed messages and sync with Linear.

    Args:
        dry_run: If True, only preview actions without executing them
        use_ai: If True, use LLM to intelligently match messages to tickets

    Returns:
        Dictionary with processing results
    """
    db = Database()

    # Get unprocessed messages
    messages = db.get_unprocessed_messages()

    if not messages:
        return {"processed": 0, "issue_comments": [], "new_issues": [], "errors": []}

    # Get assigned issues from Linear
    try:
        linear = LinearClient()
        my_issues = linear.list_open_issues(assignee_only=True)
    except Exception as e:
        return {
            "processed": 0,
            "issue_comments": [],
            "new_issues": [],
            "errors": [f"Failed to fetch Linear issues: {e}"],
        }

    # Create a map of issue identifiers for quick lookup
    issue_map = {issue.get("identifier"): issue for issue in my_issues}

    # Track actions
    issue_comments = []
    new_issues = []
    errors = []

    if use_ai:
        # Use AI to intelligently analyze messages
        try:
            analyzer = MessageAnalyzer()
            result = analyzer.analyze_messages(messages, my_issues)

            issue_comments = result["comments"]
            new_issues = result["new_issues"]
            errors.extend(result["errors"])

        except Exception as e:
            errors.append(f"AI analysis failed: {e}, falling back to regex")
            use_ai = False

    # Fallback to regex-based detection if AI is disabled or failed
    if not use_ai:
        for msg in messages:
            text = msg.get("text", "")
            channel_name = msg.get("channel_name", "unknown")
            user = msg.get("user", "unknown")

            # 1. Detect Linear issue mentions (e.g., DATA-89)
            for match in ISSUE_KEY_RE.findall(text):
                if match in issue_map:
                    issue = issue_map[match]
                    comment_body = (
                        f"Slack update in #{channel_name} by {user}:\n\n{text}"
                    )

                    issue_comments.append(
                        {
                            "issue_identifier": match,
                            "issue_title": issue.get("title", ""),
                            "issue_id": issue.get("id"),
                            "comment": comment_body,
                            "channel": channel_name,
                            "user": user,
                            "message_preview": text[:150],
                        }
                    )

            # 2. Detect TODO/ACTION items
            todo_lines = [
                line.strip()
                for line in text.split("\n")
                if line.lower().startswith(("todo:", "action:"))
            ]

            for todo_line in todo_lines:
                title = todo_line.split(":", 1)[-1].strip() or "Follow up from Slack"
                description = f"Created from Slack in #{channel_name} by {user}\n\nFull message:\n{text}"

                new_issues.append(
                    {
                        "title": title,
                        "description": description,
                        "channel": channel_name,
                        "user": user,
                        "original_line": todo_line,
                    }
                )

    # Mark as processed (only if not dry run)
    if not dry_run:
        for msg in messages:
            try:
                db.mark_as_processed(msg.get("channel_id"), msg.get("ts"))
            except Exception as e:
                errors.append(f"Failed to mark message as processed: {e}")

    # Execute Linear actions (only if not dry run)
    if not dry_run:
        for comment_action in issue_comments:
            try:
                linear.add_comment(
                    issue_id=comment_action["issue_id"], body=comment_action["comment"]
                )
                # Log the decision
                db.log_decision(
                    workflow_name="process",
                    action_type="add_comment",
                    action_taken=f"Added comment to {comment_action['issue_identifier']}",
                    reasoning=comment_action.get("ai_reasoning", "Matched message to issue"),
                    confidence=comment_action.get("confidence"),
                    entity_type="linear_ticket",
                    entity_id=comment_action["issue_id"],
                    entity_identifier=comment_action["issue_identifier"],
                    input_data={
                        "message": comment_action.get("message_preview", ""),
                        "channel": comment_action.get("channel", ""),
                        "user": comment_action.get("user", ""),
                    },
                    output_data={
                        "comment": comment_action["comment"][:200],
                    },
                )
            except Exception as e:
                errors.append(
                    f"Failed to add comment to {comment_action['issue_identifier']}: {e}"
                )

        for issue_action in new_issues:
            try:
                created = linear.create_issue(
                    title=issue_action["title"], description=issue_action["description"]
                )
                issue_action["created_identifier"] = created.get("identifier")
                issue_action["created_url"] = created.get("url")
                
                # Log the decision
                db.log_decision(
                    workflow_name="process",
                    action_type="create_ticket",
                    action_taken=f"Created ticket {created.get('identifier')}: {issue_action['title']}",
                    reasoning=issue_action.get("ai_reasoning", "Detected TODO/action item"),
                    confidence=issue_action.get("confidence"),
                    entity_type="linear_ticket",
                    entity_id=created.get("id"),
                    entity_identifier=created.get("identifier"),
                    input_data={
                        "original_message": issue_action.get("original_line", ""),
                        "channel": issue_action.get("channel", ""),
                        "user": issue_action.get("user", ""),
                    },
                    output_data={
                        "title": issue_action["title"],
                        "identifier": created.get("identifier"),
                        "url": created.get("url"),
                    },
                )
            except Exception as e:
                errors.append(f"Failed to create issue '{issue_action['title']}': {e}")

    return {
        "processed": len(messages),
        "issue_comments": issue_comments,
        "new_issues": new_issues,
        "errors": errors,
        "in_progress_issues": [
            {
                "identifier": issue.get("identifier"),
                "title": issue.get("title"),
                "state": issue.get("state", {}).get("name"),
            }
            for issue in my_issues
            if issue.get("state", {}).get("type") == "started"
        ],
    }


if __name__ == "__main__":
    import sys

    execute = "--execute" in sys.argv
    verbose = "--verbose" in sys.argv

    print("🤖 AI-Powered Message Processing\n")
    print("Mode:", "⚡ EXECUTE" if execute else "🔍 DRY RUN")
    print()

    result = process_messages(dry_run=not execute, use_ai=True)

    # Show results
    print(f"📨 Scanned: {result['processed']} messages")

    in_progress = result.get("in_progress_issues", [])
    if in_progress:
        print(f"\n🟢 In Progress ({len(in_progress)}):")
        for issue in in_progress:
            print(f"  • {issue['identifier']}: {issue['title']}")

    comments = result.get("issue_comments", [])
    if comments:
        print(f"\n💬 {len(comments)} issue updates:")
        for c in comments:
            print(f"  📌 {c['issue_identifier']}: {c['issue_title']}")
            print(f"     AI: {c['ai_reasoning']}")
            if verbose:
                print(f"     Message: {c['message_preview']}")

    new = result.get("new_issues", [])
    if new:
        print(f"\n📝 {len(new)} new issues:")
        for issue in new:
            print(f"  📋 {issue['title']}")
            print(f"     AI: {issue['ai_reasoning']}")

    if result.get("errors"):
        print(f"\n❌ {len(result['errors'])} errors")

    if not execute:
        print("\n💡 Add --execute to apply changes")
