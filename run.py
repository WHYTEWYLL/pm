#!/usr/bin/env python3
"""Simple runner for daily PM tasks."""

import sys


def main():
    if len(sys.argv) < 2:
        print(
            """
PM Assistant - Run individual modules

Usage:
  python3 run.py sync       → Ingest Slack messages
  python3 run.py linear     → Fetch Linear issues  
  python3 run.py process    → AI analysis (add --execute to apply)
  python3 run.py standup    → Daily standup report
  python3 run.py priorities → Developer priorities (add --post to post to Slack)
  python3 run.py stats      → Database statistics

Or run modules directly:
  python3 -m app.jobs.workflows.ingestion.slack
  python3 -m app.jobs.workflows.ingestion.linear
  python3 -m app.jobs.workflows.process
  python3 -m app.jobs.workflows.standup
"""
        )
        return

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "sync":
        from app.jobs.workflows.ingestion.slack import run_ingestion

        result = run_ingestion(include_threads="--threads" in args)
        mode = "🔄 Incremental" if result["mode"] == "incremental" else "📥 Initial"
        print(f"\n{mode}")
        print(f"✓ Fetched: {result['fetched']}")
        print(f"✓ Stored: {result['stored']}")
        print(f"📊 Total: {result['db_stats']['total']}")

    elif command == "linear":
        from app.jobs.workflows.ingestion.linear import run_ingestion

        result = run_ingestion(assignee_only="--all" not in args)
        scope = "All" if "--all" in args else "Your"
        print(f"\n📋 {scope} issues: {result['total']}")
        by_state = result["by_state"]
        for state_type in ["started", "unstarted", "backlog"]:
            if state_type in by_state:
                emoji = (
                    "🟢"
                    if state_type == "started"
                    else "🟡" if state_type == "unstarted" else "⚪"
                )
                print(f"{emoji} {state_type.title()}: {len(by_state[state_type])}")

    elif command == "process":
        from app.jobs.workflows.process import process_messages

        execute = "--execute" in args
        print(f"{'⚡ EXECUTING' if execute else '🔍 DRY RUN'}\n")
        result = process_messages(dry_run=not execute, use_ai=True)
        print(f"📨 Scanned: {result['processed']} messages")

        comments = result.get("issue_comments", [])
        new_issues = result.get("new_issues", [])

        if comments:
            print(f"💬 {len(comments)} issue updates")
        if new_issues:
            print(f"📝 {len(new_issues)} new issues")
        if not execute:
            print("\n💡 Add --execute to apply")

    elif command == "standup":
        from app.jobs.workflows.standup import generate_standup
        from datetime import datetime, timezone

        data = generate_standup()
        print(f"\n📊 STANDUP - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n")
        print(f"🟢 In Progress: {len(data['in_progress'])}")
        print(f"🟡 TODO: {len(data['todo'])}")
        print(f"⚪ Backlog: {len(data['backlog'])}")
        print(
            f"💬 Slack: {len(data['tracked_messages'])} tracked, {len(data['untracked_messages'])} untracked"
        )

    elif command == "priorities":
        from app.jobs.workflows.priorities_to_slack import get_developer_priorities
        import os

        print("\n📋 Fetching developer priorities from Linear...")
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
            backlog = len(dev_data["backlog"])
            print(
                f"   {assignee_name}: {in_progress} in progress, {todo} todo, {backlog} backlog"
            )

        if "--post" in args:
            channel_id = os.getenv("SLACK_CHANNEL_ID")
            if not channel_id:
                print("\n❌ Error: SLACK_CHANNEL_ID environment variable required")
                print("   Set it with: export SLACK_CHANNEL_ID=C1234567890")
                return

            from app.jobs.workflows.priorities_to_slack import post_priorities_to_slack

            print(f"\n📤 Posting to Slack channel {channel_id}...")
            result = post_priorities_to_slack(channel_id=channel_id)
            print(f"✅ Posted successfully! Message TS: {result.get('message_ts')}")
        else:
            print(
                "\n💡 Add --post to actually post to Slack (requires SLACK_CHANNEL_ID env var)"
            )

    elif command == "stats":
        from app.storage.db import Database

        stats = Database().get_stats()
        print("\n📊 Database Stats")
        print(f"Total: {stats['total']}")
        print(f"Processed: {stats['processed']}")
        print(f"Unprocessed: {stats['unprocessed']}")

    else:
        print(f"Unknown command: {command}")
        print("Run 'python3 run.py' for usage")


if __name__ == "__main__":
    main()
