# PM Assistant - Architecture

## 🏗️ Structure

The project is organized into clear, modular layers following separation of concerns:

```
pm/
├── app/
│   ├── ingestion/           # Data sources (fetch raw data)
│   │   ├── slack.py         # Slack API client
│   │   ├── linear.py        # Linear API client
│   │   └── github.py        # Future: GitHub API client
│   │
│   ├── workflows/           # Business logic orchestration
│   │   ├── sync.py          # Sync: fetch & store messages
│   │   ├── process.py       # Process: analyze & update Linear
│   │   └── standup.py       # Generate daily reports
│   │
│   ├── storage/             # Data persistence layer
│   │   └── db.py            # SQLite database operations
│   │
│   ├── ai/                  # Intelligence layer
│   │   └── analyzer.py      # AI-powered message analysis
│   │
│   ├── models.py            # Data models (SlackMessage, LinearIssue)
│   └── config.py            # Configuration management
│
└── data/                    # Local storage (DB, memory files)
```

---

## 📦 Layer Responsibilities

### **Ingestion Layer** (`app/jobs/workflows/ingestion/`)

**Purpose:** Fetch raw data from external sources

- `slack.py`: Slack API interactions

  - Fetch messages from channels
  - Handle threading and pagination
  - Filter relevant messages (mentions, DMs)

- `linear.py`: Linear API interactions
  - Fetch issues by team/assignee
  - Create issues and add comments
  - Manage issue states

**Key Principle:** These modules only fetch/push data—no business logic

---

### **Storage Layer** (`app/storage/`)

**Purpose:** Manage data persistence

- `db.py`: SQLite database operations
  - Store Slack messages with deduplication
  - Track processed status
  - Query messages by time/status
  - Provide database statistics

**Key Principle:** Pure CRUD operations—no knowledge of business rules

---

### **AI Layer** (`app/ai/`)

**Purpose:** Intelligent analysis and decision-making

- `analyzer.py`: AI-powered message analysis
  - Match messages to existing issues (semantic similarity)
  - Detect new work requests
  - Provide reasoning for suggestions
  - Batch processing for efficiency

**Key Principle:** Encapsulates all AI/LLM logic in one place

---

### **Workflows Layer** (`app/jobs/workflows/`)

**Purpose:** Orchestrate business logic by combining layers

- `sync.py`: **Sync Workflow**

  ```
  Slack API → Database → Return stats
  ```

  Fetches last 24h of messages and stores them

- `process.py`: **Process Workflow**

  ```
  Database → AI Analyzer → Linear API → Database (mark processed)
  ```

  Analyzes unprocessed messages and syncs with Linear

- `standup.py`: **Standup Workflow**
  ```
  Linear API + Database → Generate report data
  ```
  Aggregates issues and messages for daily standup

**Key Principle:** Workflows know about all layers and orchestrate them

---

## 🔄 Data Flow

### Typical Daily Flow:

1. **Morning Sync**

   ```
   cli.py sync → workflows/sync.py → ingestion/slack.py → storage/db.py
   ```

2. **Process Messages**

   ```
   cli.py process → workflows/process.py
   ├─→ storage/db.py (get unprocessed)
   ├─→ ingestion/linear.py (get issues)
   ├─→ ai/analyzer.py (match messages to issues)
   └─→ ingestion/linear.py (add comments, create issues)
   ```

3. **Daily Standup**
   ```
   cli.py standup → workflows/standup.py
   ├─→ ingestion/linear.py (get issues)
   └─→ storage/db.py (get messages)
   ```

---

## 🎯 Benefits of This Architecture

✅ **Separation of Concerns**

- Each layer has a single, clear responsibility
- Easy to understand what goes where

✅ **Testable**

- Can test each layer independently
- Mock external APIs for workflow testing

✅ **Extensible**

- Add GitHub ingestion without touching workflows
- Add new workflows without changing ingestion
- Swap AI providers without affecting workflows

✅ **Maintainable**

- Bug in Slack API? Check `ingestion/slack.py`
- Need to change AI logic? Check `ai/analyzer.py`
- Want new workflow? Add to `workflows/`

✅ **Reusable**

- Workflows can use same ingestion modules
- Multiple workflows can share AI analyzer
- CLI and future API can use same workflows

---

## 🚀 Adding New Features

### Add New Data Source (e.g., GitHub)

1. Create `app/jobs/workflows/ingestion/github.py`
2. Implement fetch methods
3. Use in existing or new workflows

### Add New Workflow

1. Create `app/jobs/workflows/my_workflow.py`
2. Import needed ingestion/storage/ai modules
3. Orchestrate the business logic
4. Add CLI command in `cli.py`

### Change AI Provider

1. Update `app/ai/analyzer.py`
2. All workflows automatically use new logic
3. No changes needed elsewhere

---

## 📝 Example: Adding GitHub Support

```python
# 1. Create app/jobs/workflows/ingestion/github.py
class GitHubClient:
    def fetch_pull_requests(self):
        # Fetch PRs from GitHub API
        pass

# 2. Use in workflow
from ..ingestion.github import GitHubClient

def sync_github():
    github = GitHubClient()
    prs = github.fetch_pull_requests()
    # Store in DB, analyze, etc.
```

No changes needed to existing code!
