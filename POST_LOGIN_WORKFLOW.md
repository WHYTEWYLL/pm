# Post-Login Workflow

> **Philosophy**: Plug it in, set it up once, forget about it. Only come back when you want to check what happened.

---

## The Flow

```
Login → Connect Services → Enable Workflows → Done ✨
                                    │
                                    └── (optional) Check Activity Log
```

---

## Home View (After Login)

This is what users see when they log in:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  PM Assistant                                              [Logout]     │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INTEGRATIONS                                                           │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  ✅ Slack    │  │  ✅ Linear   │  │  ○ GitHub    │                  │
│  │  Connected   │  │  Connected   │  │  [Connect]   │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  WORKFLOWS                                                              │
│                                                                         │
│  Auto-Sync                    Pull messages & tickets hourly   [✓ ON ]  │
│  Link Conversations           Match messages to tickets        [✓ ON ]  │
│  Ticket Status Updates        Auto-move tickets by context     [  OFF]  │
│  Daily Standup                Post summary to Slack            [  OFF]  │
│  Create Tickets               Create from untracked msgs       [  OFF]  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAST 7 DAYS                                                            │
│                                                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                    │
│  │   142   │  │    38   │  │    12   │  │     3   │                    │
│  │ Synced  │  │ Linked  │  │  Moved  │  │ Created │                    │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘                    │
│                                                                         │
│                                        [ View Activity Log → ]          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Sections Breakdown

### 1. Integrations

Shows connected services with simple status:

| Service    | What it does                           |
| ---------- | -------------------------------------- |
| **Slack**  | Reads conversations from your channels |
| **Linear** | Reads/updates your tickets             |
| **GitHub** | Reads PRs and issues (Scale tier)      |

- ✅ = Connected
- ○ + [Connect] button = Not connected

### 2. Workflows

Toggle switches for each automation:

| Workflow                  | Description                                      | Default |
| ------------------------- | ------------------------------------------------ | ------- |
| **Auto-Sync**             | Pull new messages and tickets every hour         | ✅ On   |
| **Link Conversations**    | Match Slack messages to Linear tickets           | ✅ On   |
| **Ticket Status Updates** | Auto-move tickets based on conversation context  | ❌ Off  |
| **Daily Standup**         | Generate and post standup summary to Slack       | ❌ Off  |
| **Create Tickets**        | Auto-create tickets from untracked conversations | ❌ Off  |

### 3. Quick Metrics

Summary stats from activity log (last 7 days):

- **Synced** - Messages/tickets pulled from services
- **Linked** - Conversations matched to tickets
- **Moved** - Tickets auto-updated
- **Created** - New tickets generated

### 4. View Activity Log Button

Takes user to the full activity log dashboard.

---

## Activity Log (Dashboard)

Full history of what the system did:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ← Back                        Activity Log          [Last 7 days ▼]    │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  🔗  Linked message to PM-123 "Fix login bug"                  2h ago   │
│  📥  Synced 47 new Slack messages                              2h ago   │
│  📥  Synced 12 Linear tickets                                  2h ago   │
│  →   Moved PM-118 to "In Review"                               5h ago   │
│  🔗  Linked message to PM-120 "API redesign"                   5h ago   │
│  📝  Created ticket PM-125 "Mobile app crash"                  1d ago   │
│  📤  Posted standup to #engineering                            1d ago   │
│  📥  Synced 52 new Slack messages                              1d ago   │
│  🔗  Linked 3 messages to PM-119                               1d ago   │
│  ...                                                                    │
│                                                                         │
│                              [ Load More ]                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Activity Types:**

- 📥 **Sync** - Data pulled from services
- 🔗 **Link** - Message matched to ticket
- → **Move** - Ticket status changed
- 📝 **Create** - New ticket created
- 📤 **Post** - Message sent to Slack

---

## User Experience

### First Visit (Setup)

1. Login
2. Connect Slack + Linear
3. (Optional) Toggle workflows
4. Done - workflows run automatically

### Return Visit (Checking)

1. Login
2. Glance at metrics (142 synced, 38 linked...)
3. Maybe click "View Activity Log" for details
4. Leave

---

## That's It

No complex configuration. No daily check-ins required.

The home view gives you everything at a glance:

- Are my services connected? ✅
- Which workflows are running? ✅
- Is it actually doing stuff? ✅ (metrics)
- Want details? → Activity Log
