# Testing Priorities to Slack Workflow

This guide shows how to test the `priorities_to_slack` workflow that posts developer priorities from Linear to Slack.

## Prerequisites

1. **Environment Variables** (in `.env` or exported):
   ```bash
   SLACK_TOKEN=xoxb-your-slack-token
   LINEAR_API_KEY=lin_api_your-key
   LINEAR_TEAM_ID=your-team-id  # Optional
   SLACK_CHANNEL_ID=C1234567890  # For direct testing
   ```

2. **Local Tenant Setup** (if using API):
   ```bash
   curl -X POST "http://localhost:8000/local-dev/setup-tenant?tenant_id=local-dev-tenant"
   ```

## Testing Methods

### 1. Direct CLI Testing (Recommended for Quick Tests)

Test the workflow directly from command line:

```bash
# Just fetch and display priorities (no Slack posting)
python3 run.py priorities

# Fetch and post to Slack (requires SLACK_CHANNEL_ID env var)
export SLACK_CHANNEL_ID=C1234567890
python3 run.py priorities --post
```

Or run the module directly:

```bash
# View priorities only
python3 -m app.jobs.workflows.priorities_to_slack

# Post to Slack (requires SLACK_CHANNEL_ID)
export SLACK_CHANNEL_ID=C1234567890
python3 -m app.jobs.workflows.priorities_to_slack --post
```

### 2. API Endpoint Testing

Start the server:
```bash
export ENV=development
python3 -m uvicorn app.api.main:app --reload --port 8000
```

**Option A: Using local dev tenant (no auth needed)**
```bash
# First, setup local tenant
curl -X POST "http://localhost:8000/local-dev/setup-tenant?tenant_id=local-dev-tenant"

# Get tenant ID
TENANT_ID=$(curl -s http://localhost:8000/local-dev/tenant-id | jq -r '.tenant_id')

# Post priorities (uses channel from config)
curl -X POST "http://localhost:8000/api/workflows/priorities-to-slack" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{}'

# Or specify a channel
curl -X POST "http://localhost:8000/api/workflows/priorities-to-slack" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "C1234567890"}'
```

**Option B: With authentication**
```bash
# Register/login first
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}' \
  | jq -r '.access_token')

# Post priorities
curl -X POST "http://localhost:8000/api/workflows/priorities-to-slack" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "C1234567890"}'
```

### 3. Python Script Testing

Create a test script:

```python
# test_priorities.py
import os
from app.jobs.workflows.priorities_to_slack import (
    get_developer_priorities,
    post_priorities_to_slack,
)

# Fetch priorities
print("📋 Fetching priorities...")
priorities = get_developer_priorities()

print(f"Total issues: {priorities['total_issues']}")
print(f"Developers: {priorities['total_developers']}")

# Post to Slack
channel_id = os.getenv("SLACK_CHANNEL_ID")
if channel_id:
    print(f"\n📤 Posting to Slack...")
    result = post_priorities_to_slack(channel_id=channel_id)
    print(f"✅ Success! Message TS: {result.get('message_ts')}")
else:
    print("\n⚠️  Set SLACK_CHANNEL_ID to post to Slack")
```

Run it:
```bash
python3 test_priorities.py
```

### 4. Celery Task Testing

Test the background job:

```python
# test_celery_task.py
from app.jobs.scheduled_workflows import post_priorities_to_slack_for_tenant
import os

# Set tenant context
os.environ["CURRENT_TENANT_ID"] = "local-dev-tenant"

# Run the task (synchronously for testing)
result = post_priorities_to_slack_for_tenant("local-dev-tenant", channel_id="C1234567890")
print(result)
```

Or test async:
```python
from app.jobs.scheduled_workflows import post_priorities_to_slack_for_tenant

# Queue the task
task = post_priorities_to_slack_for_tenant.delay("local-dev-tenant", channel_id="C1234567890")
print(f"Task ID: {task.id}")
print(f"Result: {task.get(timeout=30)}")
```

## Expected Output

### Console Output (CLI)
```
📋 Fetching developer priorities from Linear...

📊 Summary:
   Total issues: 15
   Developers: 3
   Unassigned: 2

👥 By Developer:
   Alice Developer: 2 in progress, 3 todo, 1 backlog
   Bob Developer: 1 in progress, 2 todo, 0 backlog
   Charlie Developer: 0 in progress, 4 todo, 2 backlog

💡 Add --post to actually post to Slack
```

### Slack Message Format
The Slack message will show:
- Header: "📋 Developer Priorities - [Date]"
- For each developer:
  - Name
  - 🔥 In Progress section (up to 5 items)
  - 📋 Up Next section (up to 3 items)
- ⚠️ Unassigned Issues section (if any)
- Footer with total stats

## Troubleshooting

### "Slack not connected" error
- Make sure you've run the local dev setup: `curl -X POST "http://localhost:8000/local-dev/setup-tenant"`
- Or ensure OAuth credentials are stored in the tenant database

### "Linear not connected" error
- Check that `LINEAR_API_KEY` is set in environment
- Run local dev setup to store credentials

### "No target channel configured" error
- Either provide `channel_id` in the API request
- Or configure `slack_target_channel_ids` in tenant config

### No issues showing
- Check that Linear team has open issues
- Verify `LINEAR_TEAM_ID` is correct (or set to None to fetch all teams)
- Try with `assignee_only=False` to see all issues

## Testing Checklist

- [ ] Can fetch priorities from Linear (CLI)
- [ ] Can format priorities correctly (view output)
- [ ] Can post to Slack channel (with `--post`)
- [ ] API endpoint works (with auth)
- [ ] API endpoint works (local dev)
- [ ] Celery task executes successfully
- [ ] Handles missing credentials gracefully
- [ ] Handles missing channel gracefully
- [ ] Shows correct developer grouping
- [ ] Shows unassigned issues when present

