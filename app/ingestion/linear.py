from __future__ import annotations

from typing import Optional, Dict, Any, List
import logging
import requests

from ..config import settings
from ..models import LinearIssue


class LinearClient:
    logger = logging.getLogger("linear_ingestion")

    def __init__(self, api_key: Optional[str] = None, team_id: Optional[str] = None):
        self.api_key = api_key or settings.linear_api_key

        raw_team_id = team_id if team_id is not None else settings.linear_team_id
        if isinstance(raw_team_id, str):
            cleaned = raw_team_id.strip()
            if not cleaned or cleaned.lower() in {"none", "null"}:
                raw_team_id = None
            else:
                raw_team_id = cleaned
        self.team_id = raw_team_id
        if not self.api_key:
            raise ValueError("Missing LINEAR_API_KEY")
        self.endpoint = "https://api.linear.app/graphql"
        self._resolved_team_id: Optional[str] = None

    def _post(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(
            self.endpoint,
            json={"query": query, "variables": variables or {}},
            headers=headers,
        )
        if resp.status_code != 200:
            print(f"   HTTP Error {resp.status_code}: {resp.text}")
            resp.raise_for_status()
        data = resp.json()
        snippet = " ".join(query.split())
        if len(snippet) > 200:
            snippet = f"{snippet[:200]}..."
        print(f">>> Linear ingestion: GraphQL query: {snippet}")
        if variables:
            print(f">>> Linear ingestion: variables: {variables}")
        print(f">>> Linear ingestion: GraphQL response: {data}")
        if "errors" in data:
            print(f"   GraphQL errors: {data['errors']}")
            raise RuntimeError(data["errors"])
        return data["data"]

    def _get_team_id(self) -> Optional[str]:
        """Resolve team ID from key if needed. Returns the actual team ID."""
        if self._resolved_team_id:
            return self._resolved_team_id

        if not self.team_id:
            return None

        # If it looks like a UUID, assume it's already an ID
        if len(self.team_id) > 30 and "-" in self.team_id:
            self._resolved_team_id = self.team_id
            return self._resolved_team_id

        # Otherwise, treat it as a key and look it up
        query = """
        query {
          teams {
            nodes { id key }
          }
        }
        """
        data = self._post(query)
        teams = data.get("teams", {}).get("nodes", [])

        for team in teams:
            if team.get("key") == self.team_id:
                self._resolved_team_id = team.get("id")
                return self._resolved_team_id

        # If not found by key, assume it's an ID
        self._resolved_team_id = self.team_id
        return self._resolved_team_id

    def get_viewer_id(self) -> str:
        """Get the current user's ID."""
        query = """
        query {
          viewer { id name email }
        }
        """
        data = self._post(query)
        return data["viewer"]["id"]

    def list_open_issues(
        self, assignee_only: bool = False, team_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        target_team_id = team_id if team_id is not None else self._get_team_id()

        # Build filter
        filter_parts = ['state: {name: {nin: ["Done", "Canceled", "Duplicate"]}}']

        if target_team_id:
            filter_parts.insert(0, f'team: {{id: {{eq: "{target_team_id}"}}}}')

        if assignee_only:
            viewer_id = self.get_viewer_id()
            filter_parts.append(f'assignee: {{id: {{eq: "{viewer_id}"}}}}')

        filter_str = ", ".join(filter_parts)

        # Filter for issues that are not Done, Canceled, or Duplicate
        # Note: Using hardcoded values in query because Linear API has issues with variables + nin operator
        query = f"""
        query {{
          issues(filter: {{{filter_str}}}, first: 100) {{
            nodes {{ 
              id 
              identifier 
              title 
              description
              state {{ name type }} 
              url 
              assignee {{ name }} 
              parent {{ id identifier title }}
              createdAt
              updatedAt
            }}
          }}
        }}
        """
        data = self._post(query)
        main_issues = data["issues"]["nodes"]

        # Also fetch sub-tickets of the main issues
        all_issues = main_issues.copy()
        for issue in main_issues:
            try:
                sub_query = f"""
                query {{
                  issues(filter: {{parent: {{id: {{eq: "{issue['id']}"}}}}}}, first: 50) {{
                    nodes {{ 
                      id 
                      identifier 
                      title 
                      description
                      state {{ name type }} 
                      url 
                      assignee {{ name }} 
                      parent {{ id identifier title }}
                      createdAt
                      updatedAt
                    }}
                  }}
                }}
                """
                sub_data = self._post(sub_query)
                sub_issues = sub_data["issues"]["nodes"]
                all_issues.extend(sub_issues)
                print(
                    f"📋 Found {len(sub_issues)} sub-tickets for {issue.get('identifier')}"
                )
            except Exception as e:
                print(
                    f"⚠️ Could not fetch sub-tickets for {issue.get('identifier')}: {e}"
                )

        return all_issues

    def issue_by_key(self, identifier: str) -> Optional[Dict[str, Any]]:
        query = """
        query($id: String!) { issue(identifier: $id) { id identifier title url state { name } } }
        """
        data = self._post(query, {"id": identifier})
        return data.get("issue")

    def add_comment(self, issue_id: str, body: str) -> None:
        mutation = """
        mutation($issueId: String!, $body: String!) {
          commentCreate(input: { issueId: $issueId, body: $body }) { success }
        }
        """
        self._post(mutation, {"issueId": issue_id, "body": body})

    def create_issue(self, title: str, description: str = "") -> Dict[str, Any]:
        team_id = self._get_team_id()
        mutation = """
        mutation($teamId: String!, $title: String!, $description: String) {
          issueCreate(input: { teamId: $teamId, title: $title, description: $description }) {
            issue { id identifier title url }
          }
        }
        """
        data = self._post(
            mutation,
            {"teamId": team_id, "title": title, "description": description},
        )
        return data["issueCreate"]["issue"]

    def transition_issue(self, issue_id: str, state_name: str) -> None:
        # Fetch team workflow states, then find by name
        team_id = self._get_team_id()
        states_query = """
        query($teamId: ID!) {
          workflowStates(filter: { team: { id: { eq: $teamId } } }) { nodes { id name } }
        }
        """
        states = self._post(states_query, {"teamId": team_id})["workflowStates"][
            "nodes"
        ]
        print(f"   Available states: {[s['name'] for s in states]}")
        print(f"   Looking for state: '{state_name}'")
        target = next(
            (s for s in states if s["name"].lower() == state_name.lower()), None
        )
        if not target:
            print(f"   ❌ State '{state_name}' not found in available states")
            return
        print(f"   ✅ Found state: {target['name']} (ID: {target['id']})")
        mutation = """
        mutation($issueId: String!, $stateId: String!) {
          issueUpdate(id: $issueId, input: { stateId: $stateId }) { success }
        }
        """
        result = self._post(mutation, {"issueId": issue_id, "stateId": target["id"]})
        print(f"   Linear API response: {result}")

    def ingest(
        self, assignee_only: bool = True, store_in_db: bool = True
    ) -> Dict[str, Any]:
        """Fetch Linear issues and optionally persist them."""
        self.logger.info(
            "Starting Linear ingestion (assignee_only=%s, store_in_db=%s)",
            assignee_only,
            store_in_db,
        )
        print(">>> Linear ingestion: starting fetch")

        team_id = self._get_team_id()
        print(f">>> Linear ingestion: team id: {team_id}")

        try:
            if team_id:
                issues = self.list_open_issues(assignee_only=assignee_only)
            else:
                self.logger.info(
                    "No team configured; fetching issues across all accessible teams"
                )
                teams_query = """
                query {
                  teams {
                    nodes { id key name }
                  }
                }
                """
                teams = self._post(teams_query)["teams"]["nodes"]
                print(
                    f">>> Linear ingestion: discovered {len(teams)} teams in workspace"
                )

                aggregated: Dict[str, Dict[str, Any]] = {}
                effective_assignee_only = assignee_only
                if assignee_only:
                    print(
                        ">>> Linear ingestion: overriding assignee_only=True → False to capture all team issues"
                    )
                    effective_assignee_only = False
                for entry in teams:
                    current_team_id = entry.get("id")
                    team_key = entry.get("key") or entry.get("name") or current_team_id
                    if not current_team_id:
                        continue
                    print(
                        f">>> Linear ingestion: fetching issues for team {team_key} ({current_team_id})"
                    )
                    team_issues = self.list_open_issues(
                        assignee_only=effective_assignee_only,
                        team_id=current_team_id,
                    )
                    print(
                        f">>> Linear ingestion: fetched {len(team_issues)} issues for team {team_key}"
                    )
                    for issue in team_issues:
                        aggregated[issue["id"]] = issue
                issues = list(aggregated.values())
                print(
                    f">>> Linear ingestion: aggregated {len(issues)} unique issues across all teams"
                )
            print(f">>> Linear ingestion: fetched {len(issues)} issues from API")
        except Exception as exc:
            self.logger.exception("Linear ingestion failed while fetching issues")
            print(f">>> Linear ingestion: fetch failed with error {exc!r}")
            raise

        linear_issues: List[LinearIssue] = []
        for issue in issues:
            linear_issue = LinearIssue(
                id=issue["id"],
                identifier=issue["identifier"],
                title=issue["title"],
                description=issue.get("description"),
                state_name=issue.get("state", {}).get("name", "Unknown"),
                state_type=issue.get("state", {}).get("type", "unknown"),
                url=issue["url"],
                assignee_name=(
                    issue.get("assignee", {}).get("name")
                    if issue.get("assignee")
                    else None
                ),
                parent_id=(
                    issue.get("parent", {}).get("id") if issue.get("parent") else None
                ),
                parent_title=(
                    issue.get("parent", {}).get("title")
                    if issue.get("parent")
                    else None
                ),
                original_created_at=issue.get("createdAt"),
                original_updated_at=issue.get("updatedAt"),
            )
            linear_issues.append(linear_issue)

        stored_count = 0
        db_stats: Dict[str, Any] = {}
        if store_in_db and linear_issues:
            from ..storage.db import Database

            db = Database()
            stored_count = db.insert_linear_issues(linear_issues)
            db_stats = db.get_linear_stats()
            print(
                f">>> Linear ingestion: stored {stored_count} issues (db stats: {db_stats})"
            )
        else:
            print(">>> Linear ingestion: skipping DB store (no issues or disabled)")

        by_state: Dict[str, List[Dict[str, Any]]] = {}
        for issue in issues:
            state_type = issue.get("state", {}).get("type", "unknown")
            if state_type not in by_state:
                by_state[state_type] = []
            by_state[state_type].append(issue)

        self.logger.info(
            "Linear ingestion completed: fetched=%s, stored=%s",
            len(issues),
            stored_count,
        )
        print(
            f">>> Linear ingestion: completed fetched={len(issues)} stored={stored_count}"
        )

        return {
            "issues": issues,
            "by_state": by_state,
            "total": len(issues),
            "stored": stored_count,
            "db_stats": db_stats,
        }


def run_ingestion(
    assignee_only: bool = True, store_in_db: bool = True
) -> Dict[str, Any]:
    """
    Main entry point for Linear ingestion.

    Fetches Linear issues and optionally stores them in the database.

    Args:
        assignee_only: Only fetch issues assigned to current user
        store_in_db: Whether to store issues in the database

    Returns:
        Dict with issues, stats, and database info
    """
    from ..storage.db import Database

    client = LinearClient()
    return client.ingest(assignee_only=assignee_only, store_in_db=store_in_db)


if __name__ == "__main__":
    # Allow running this file directly
    import sys

    all_issues = "--all" in sys.argv
    no_store = "--no-store" in sys.argv

    print("🔄 Fetching Linear issues...")
    result = run_ingestion(assignee_only=not all_issues, store_in_db=not no_store)

    scope = "All issues" if all_issues else "Your issues"
    print(f"\n📋 {scope}: {result['total']}")
    print(f"💾 Stored in DB: {result['stored']}")

    by_state = result["by_state"]
    if "started" in by_state:
        print(f"🟢 In Progress: {len(by_state['started'])}")
    if "unstarted" in by_state:
        print(f"🟡 TODO: {len(by_state['unstarted'])}")
    if "backlog" in by_state:
        print(f"⚪ Backlog: {len(by_state['backlog'])}")

    if result.get("db_stats"):
        stats = result["db_stats"]
        print(f"\n📊 Database stats:")
        print(f"   Total: {stats['total']}")
        print(f"   In Progress: {stats['in_progress']}")
        print(f"   TODO: {stats['todo']}")
        print(f"   Backlog: {stats['backlog']}")
        print(f"   Assigned: {stats['assigned']}")
