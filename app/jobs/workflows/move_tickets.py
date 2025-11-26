"""Move tickets workflow: analyze conversations and move tickets between states."""

from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
import json

from ...storage.db import Database
from .ingestion.linear import LinearClient
from .ai.analyzer import AIAnalyzer


def find_related_messages(
    ticket_id: str, messages: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Find messages that mention the ticket ID."""
    text_lower = ticket_id.lower()
    return [
        msg
        for msg in messages
        if text_lower in msg.get("text", "").lower()
        or text_lower.replace("-", "") in msg.get("text", "").lower().replace("-", "")
    ]


def analyze_ticket(
    ticket: Dict[str, Any], messages: List[Dict[str, Any]], db: Database
) -> Dict[str, Any]:
    """Analyze if a ticket should change status based on conversations."""
    analyzer = AIAnalyzer()

    # Get sub-tickets
    all_tickets = db.get_linear_issues()
    subtickets = [t for t in all_tickets if t.get("parent_id") == ticket.get("id")]

    prompt = f"""
Analyze this Linear ticket and Slack conversations to determine if the status should change.

TICKET: {ticket.get('identifier')} - {ticket.get('title')}
Current State: {ticket.get('state_name')}

SUB-TICKETS:
{json.dumps([{'id': s.get('identifier'), 'title': s.get('title'), 'state': s.get('state_name')} for s in subtickets], indent=2) if subtickets else 'None'}

CONVERSATIONS ({len(messages)} messages):
{json.dumps([{'channel': m.get('channel_name'), 'text': m.get('text')[:200], 'user': m.get('user')} for m in messages], indent=2)}

Look for completion indicators: "done", "deployed", "live", "running", "completed", "finished"
Look for blockers: "blocked", "waiting", "stuck", "issue"

Available states: Backlog, Todo, In Progress, Blocked, Done

Return JSON:
{{
    "should_change": true/false,
    "recommended_status": "State name",
    "confidence": 0.0-1.0,
    "reasoning": "Why"
}}
"""

    try:
        result = analyzer.analyze(prompt, {})
        return json.loads(result) if isinstance(result, str) else result
    except Exception as e:
        return {
            "should_change": False,
            "recommended_status": ticket.get("state_name"),
            "confidence": 0,
            "reasoning": str(e),
        }


def move_ticket(ticket_id: str, new_status: str, ticket: Dict[str, Any]) -> bool:
    """Move a ticket to a new status in Linear."""
    try:
        linear = LinearClient()
        issue_id = ticket.get("id")
        if not issue_id:
            return False
        linear.transition_issue(issue_id, new_status)
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def process_ticket_status_changes(
    days_back: int = 7, min_confidence: float = 0.7
) -> Dict[str, Any]:
    """Main workflow: analyze tickets and move them based on Slack conversations."""
    print("🎫 TICKET STATUS CHANGE WORKFLOW")
    print("=" * 50)

    db = Database()
    start_date = datetime.now(timezone.utc) - timedelta(days=days_back)

    messages = db.get_messages_since(start_date)
    all_issues = db.get_linear_issues()

    # Get most recent snapshot
    if all_issues:
        most_recent = max(all_issues, key=lambda x: x.get("snapshot_date", ""))
        issues = [
            t
            for t in all_issues
            if t.get("snapshot_date") == most_recent.get("snapshot_date")
        ]
    else:
        issues = []

    print(f"📊 {len(messages)} messages, {len(issues)} tickets")

    if not messages or not issues:
        return {"status": "no_data", "changes": [], "errors": []}

    changes = []
    errors = []

    for ticket in issues:
        ticket_id = ticket.get("identifier")
        current_state = ticket.get("state_name")

        # Find related messages
        related = find_related_messages(ticket_id, messages)
        if not related:
            continue

        print(f"\n🎯 {ticket_id} ({current_state}) - {len(related)} messages")

        # Analyze
        analysis = analyze_ticket(ticket, related, db)
        recommended = analysis.get("recommended_status")
        confidence = analysis.get("confidence", 0)

        if not analysis.get("should_change") or recommended == current_state:
            continue

        if confidence < min_confidence:
            print(f"   ⚠️ Low confidence ({confidence:.2f})")
            continue

        # Make the change
        print(f"   🎯 Moving to {recommended} (confidence: {confidence:.2f})")
        if move_ticket(ticket_id, recommended, ticket):
            # Log the decision
            db.log_decision(
                workflow_name="move_tickets",
                action_type="move_ticket",
                action_taken=f"Moved {ticket_id} from {current_state} to {recommended}",
                reasoning=analysis.get("reasoning", ""),
                confidence=confidence,
                entity_type="linear_ticket",
                entity_id=ticket.get("id"),
                entity_identifier=ticket_id,
                input_data={
                    "ticket": ticket_id,
                    "current_state": current_state,
                    "recommended_state": recommended,
                    "related_messages": len(related),
                },
                output_data={
                    "from": current_state,
                    "to": recommended,
                    "confidence": confidence,
                },
            )
            changes.append(
                {
                    "ticket": ticket_id,
                    "from": current_state,
                    "to": recommended,
                    "confidence": confidence,
                    "reasoning": analysis.get("reasoning", ""),
                }
            )
        else:
            errors.append({"ticket": ticket_id, "error": "Failed to move"})

    return {
        "status": "completed",
        "changes": changes,
        "errors": errors,
        "processed": len(issues),
    }


if __name__ == "__main__":
    print(f"\n🎫 TICKET MOVER - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n")

    result = process_ticket_status_changes()

    print(f"\n📊 RESULTS:")
    print(f"   Processed: {result.get('processed', 0)}")
    print(f"   Changes: {len(result.get('changes', []))}")
    print(f"   Errors: {len(result.get('errors', []))}")

    if result.get("changes"):
        print(f"\n✅ CHANGES:")
        for c in result["changes"]:
            print(
                f"   • {c['ticket']}: {c['from']} → {c['to']} ({c['confidence']:.2f})"
            )

    print("\n" + "=" * 60)
