"""Update tickets workflow: analyze Slack messages and update Linear tickets."""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import json

from ...storage.db import Database
from ...ingestion.linear import LinearClient
from ...ai.analyzer import AIAnalyzer


def get_todays_data() -> Dict[str, Any]:
    """
    Get today's Slack messages and Linear tickets.

    Returns:
        Dictionary with today's messages and tickets
    """
    db = Database()

    # Get today's date range
    today = datetime.now(timezone.utc).date()
    start_of_day = datetime.combine(today, datetime.min.time()).replace(
        tzinfo=timezone.utc
    )
    end_of_day = datetime.combine(today, datetime.max.time()).replace(
        tzinfo=timezone.utc
    )

    # Get today's Slack messages
    messages = db.get_messages_since(start_of_day)

    # Get today's Linear tickets (from our snapshot)
    linear_issues = db.get_linear_issues()

    # Filter to today's snapshot
    today_issues = [
        issue
        for issue in linear_issues
        if issue.get("snapshot_date") == today.strftime("%Y-%m-%d")
    ]

    return {
        "messages": messages,
        "tickets": today_issues,
        "date": today.strftime("%Y-%m-%d"),
        "total_messages": len(messages),
        "total_tickets": len(today_issues),
    }


def analyze_ticket_updates(
    messages: List[Dict[str, Any]], tickets: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Use AI to analyze messages and identify ticket updates.

    Args:
        messages: Today's Slack messages
        tickets: Today's Linear tickets

    Returns:
        Analysis results with potential updates
    """
    analyzer = AIAnalyzer()

    # Prepare context for AI analysis
    context = {
        "messages": messages,
        "tickets": tickets,
        "analysis_date": datetime.now(timezone.utc).isoformat(),
    }

    # Create analysis prompt
    prompt = f"""
    Analyze the following Slack messages and Linear tickets to identify any updates or completions.
    
    MESSAGES ({len(messages)} total):
    {json.dumps([{
        'channel': msg.get('channel_name'),
        'text': msg.get('text'),
        'user': msg.get('user'),
        'timestamp': msg.get('created_at')
    } for msg in messages], indent=2)}
    
    TICKETS ({len(tickets)} total):
    {json.dumps([{
        'identifier': ticket.get('identifier'),
        'title': ticket.get('title'),
        'state': ticket.get('state_name'),
        'assignee': ticket.get('assignee_name')
    } for ticket in tickets], indent=2)}
    
    Please identify:
    1. Any tickets that appear to be completed or have significant updates
    2. Any messages that indicate work progress or completion
    3. Recommendations for ticket status changes
    
    Return your analysis in JSON format with:
    - completed_tickets: List of ticket identifiers that appear completed
    - updated_tickets: List of tickets with updates
    - recommendations: List of suggested actions
    """

    try:
        analysis = analyzer.analyze(prompt, context)
        return json.loads(analysis) if isinstance(analysis, str) else analysis
    except Exception as e:
        print(f"AI analysis failed: {e}")
        return {
            "completed_tickets": [],
            "updated_tickets": [],
            "recommendations": [],
            "error": str(e),
        }


def update_ticket_status(ticket_identifier: str, new_status: str) -> bool:
    """
    Update a ticket's status in Linear.

    Args:
        ticket_identifier: Linear ticket identifier (e.g., "DATA-96")
        new_status: New status to set

    Returns:
        True if successful, False otherwise
    """
    try:
        linear = LinearClient()

        # Get the issue by identifier
        issue = linear.issue_by_key(ticket_identifier)
        if not issue:
            print(f"❌ Ticket {ticket_identifier} not found")
            return False

        # Transition the issue
        linear.transition_issue(issue["id"], new_status)
        print(f"✅ Updated {ticket_identifier} to {new_status}")
        return True

    except Exception as e:
        print(f"❌ Failed to update {ticket_identifier}: {e}")
        return False


def run_update_tickets() -> Dict[str, Any]:
    """
    Main workflow to update tickets based on today's activity.

    Returns:
        Dictionary with update results
    """
    print("🔄 Starting ticket update workflow...")

    # Get today's data
    data = get_todays_data()
    print(
        f"📊 Found {data['total_messages']} messages and {data['total_tickets']} tickets"
    )

    if data["total_messages"] == 0:
        print("⚠️ No messages found for today")
        return {"status": "no_messages", "updates": []}

    # Analyze for updates
    print("🤖 Analyzing messages for ticket updates...")
    analysis = analyze_ticket_updates(data["messages"], data["tickets"])

    updates_made = []
    errors = []

    # Process completed tickets
    for ticket_id in analysis.get("completed_tickets", []):
        print(f"🎯 Processing completed ticket: {ticket_id}")
        success = update_ticket_status(ticket_id, "Done")
        if success:
            updates_made.append(
                {"ticket": ticket_id, "action": "completed", "status": "Done"}
            )
        else:
            errors.append({"ticket": ticket_id, "error": "Failed to mark as Done"})

    # Process updated tickets
    for ticket_id in analysis.get("updated_tickets", []):
        print(f"📝 Processing updated ticket: {ticket_id}")
        # For now, just log the update - could implement specific status changes
        updates_made.append(
            {"ticket": ticket_id, "action": "updated", "status": "noted"}
        )

    return {
        "status": "completed",
        "date": data["date"],
        "messages_analyzed": data["total_messages"],
        "tickets_analyzed": data["total_tickets"],
        "updates_made": updates_made,
        "errors": errors,
        "analysis": analysis,
    }


if __name__ == "__main__":
    print(
        f"\n🎫 TICKET UPDATE WORKFLOW - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n"
    )

    result = run_update_tickets()

    print(f"\n📊 RESULTS:")
    print(f"   Status: {result['status']}")
    print(f"   Messages analyzed: {result['messages_analyzed']}")
    print(f"   Tickets analyzed: {result['tickets_analyzed']}")
    print(f"   Updates made: {len(result['updates_made'])}")

    if result["updates_made"]:
        print(f"\n✅ UPDATES MADE:")
        for update in result["updates_made"]:
            print(f"   • {update['ticket']}: {update['action']} -> {update['status']}")

    if result["errors"]:
        print(f"\n❌ ERRORS:")
        for error in result["errors"]:
            print(f"   • {error['ticket']}: {error['error']}")

    print("\n" + "=" * 60)
