"""AI-powered message analysis."""

from __future__ import annotations
from typing import List, Dict, Any
from openai import OpenAI

from ...config import settings


class AIAnalyzer:
    """General AI analyzer for various tasks."""

    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)
        self.model = "gpt-4o-mini"

    def analyze(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Analyze text using AI.

        Args:
            prompt: The prompt to send to the AI
            context: Optional context data

        Returns:
            AI response as string
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that analyzes project management data. Provide clear, actionable insights in JSON format when requested.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f'{{"error": "AI analysis failed: {str(e)}"}}'


class MessageAnalyzer:
    """Analyzes Slack messages using AI to match them to Linear issues."""

    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)
        self.model = "gpt-4o-mini"

    def analyze_messages(
        self,
        messages: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
        batch_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Analyze messages and determine which actions to take.

        Args:
            messages: List of message dicts from database
            issues: List of Linear issue dicts
            batch_size: Number of messages to analyze per batch

        Returns:
            Dict with 'comments' and 'new_issues' lists
        """
        issue_comments = []
        new_issues = []
        errors = []

        # Build context about existing issues
        issues_context = []
        for issue in issues:
            state_type = issue.get("state", {}).get("type", "unknown")
            desc = issue.get("description") or ""
            issues_context.append(
                {
                    "identifier": issue.get("identifier"),
                    "title": issue.get("title"),
                    "description": desc[:200] if desc else "",
                    "state": state_type,
                }
            )

        # Create issue map for quick lookup
        issue_map = {issue.get("identifier"): issue for issue in issues}

        # Process messages in batches
        for i in range(0, len(messages), batch_size):
            batch = messages[i : i + batch_size]

            # Format messages for LLM
            messages_text = []
            for idx, msg in enumerate(batch):
                text = msg.get("text", "")
                channel = msg.get("channel_name", "unknown")
                user = msg.get("user", "unknown")
                messages_text.append(f"[{idx}] #{channel} - {user}: {text}")

            prompt = f"""Analyze these Slack messages and determine which actions to take with Linear issues.

EXISTING ISSUES:
{chr(10).join([f"- {i['identifier']}: {i['title']} (state: {i['state']})" for i in issues_context])}

MESSAGES TO ANALYZE:
{chr(10).join(messages_text)}

For each message, determine:
1. Should it be linked to an existing issue? (consider semantic similarity, not just exact ID mentions)
2. Should a new issue be created?
3. What's the reasoning?

Output JSON array with this structure:
[
  {{
    "message_index": 0,
    "action": "comment|create|none",
    "issue_identifier": "DATA-XX" (if comment action),
    "new_issue_title": "title" (if create action),
    "reasoning": "why this action"
  }}
]

Rules:
- Only link to issues if the message contains substantive updates (progress, blockers, questions)
- Create new issues for requests, bugs, or new work mentioned
- Skip operational chatter (meeting links, "thanks", etc.)
- Be conservative: when in doubt, choose "none"
"""

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an assistant that analyzes Slack messages to determine which should be tracked in Linear. Output valid JSON only.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"},
                )

                import json

                result_text = response.choices[0].message.content.strip()
                # Try to parse as JSON
                if result_text.startswith("["):
                    actions = json.loads(result_text)
                else:
                    # Might be wrapped in a JSON object
                    parsed = json.loads(result_text)
                    actions = parsed.get("actions", parsed.get("results", []))

                # Process AI recommendations
                for action in actions:
                    msg_idx = action.get("message_index")
                    if msg_idx is None or msg_idx >= len(batch):
                        continue

                    msg = batch[msg_idx]
                    text = msg.get("text", "")
                    channel_name = msg.get("channel_name", "unknown")
                    user = msg.get("user", "unknown")

                    action_type = action.get("action")
                    reasoning = action.get("reasoning", "")

                    if action_type == "comment":
                        issue_id = action.get("issue_identifier")
                        if issue_id in issue_map:
                            issue = issue_map[issue_id]
                            comment_body = f"Slack update in #{channel_name} by {user}:\n\n{text}\n\n---\nAI Analysis: {reasoning}"

                            issue_comments.append(
                                {
                                    "issue_identifier": issue_id,
                                    "issue_title": issue.get("title", ""),
                                    "issue_id": issue.get("id"),
                                    "comment": comment_body,
                                    "channel": channel_name,
                                    "user": user,
                                    "message_preview": text[:150],
                                    "ai_reasoning": reasoning,
                                }
                            )

                    elif action_type == "create":
                        title = action.get("new_issue_title", "Follow up from Slack")
                        description = f"Created from Slack in #{channel_name} by {user}\n\nOriginal message:\n{text}\n\n---\nAI Analysis: {reasoning}"

                        new_issues.append(
                            {
                                "title": title,
                                "description": description,
                                "channel": channel_name,
                                "user": user,
                                "original_line": text[:100],
                                "ai_reasoning": reasoning,
                            }
                        )

            except Exception as e:
                errors.append(f"AI analysis failed for batch {i//batch_size + 1}: {e}")

        return {"comments": issue_comments, "new_issues": new_issues, "errors": errors}
