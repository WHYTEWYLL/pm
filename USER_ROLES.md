# User Roles & Views

> Two types of users, two different experiences. Same data, different focus.

---

## Sign-Up Flow

The person who signs up becomes the **Owner**. During onboarding, we ask:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  What's your role?                                                      │
│                                                                         │
│  ┌─────────────────────────┐    ┌─────────────────────────┐            │
│  │                         │    │                         │            │
│  │  👨‍💻 I'm a Developer      │    │  📊 I'm a Stakeholder   │            │
│  │                         │    │                         │            │
│  │  I'll set up the        │    │  I want visibility      │            │
│  │  integrations and       │    │  into what my team      │            │
│  │  configure workflows    │    │  is working on          │            │
│  │                         │    │                         │            │
│  └─────────────────────────┘    └─────────────────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

This sets their **default view**, but as Owner they can always switch.

---

## Permissions vs Views

**Important distinction:**

| Concept | What it means |
|---------|---------------|
| **Permission** (Owner/Admin/Member) | What you CAN do |
| **View** (Dev/Stakeholder) | What you SEE by default |

### Permissions

| Role | Billing | Invite | Configure Integrations | View Reports |
|------|---------|--------|------------------------|--------------|
| **Owner** | ✅ | ✅ | ✅ | ✅ |
| **Admin** | ❌ | ✅ | ✅ | ✅ |
| **Member** | ❌ | ❌ | Based on view | ✅ |

### Views

| View | See Integrations | Configure Workflows | See Activity Log | See Reports | Manage Team |
|------|------------------|---------------------|------------------|-------------|-------------|
| **Dev** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Stakeholder** | ❌ | ❌ | ❌ | ✅ | ✅ |

**Owner/Admin can switch between views.** Members are locked to their assigned view.

---

## The Two Views

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           TEAM (Tenant)                                 │
│                                                                         │
│   ┌─────────────────────┐           ┌─────────────────────┐            │
│   │     DEV VIEW        │           │  STAKEHOLDER VIEW   │            │
│   │                     │           │                     │            │
│   │  - Connect tools    │           │  - View reports     │            │
│   │  - Enable workflows │           │  - Track progress   │            │
│   │  - Activity log     │           │  - Weekly summaries │            │
│   │                     │           │  - Invite team      │            │
│   └─────────────────────┘           └─────────────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Dev View (Current)

**Who**: Engineers, technical PMs, the person setting things up

**Purpose**: Configure and monitor the automation

### What they see:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DEV                                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INTEGRATIONS                                                           │
│  [Slack ✅] [Linear ✅] [GitHub ○]                                      │
│                                                                         │
│  WORKFLOWS                                                              │
│  Auto-Sync                    [ON ]                                     │
│  Link Conversations           [ON ]                                     │
│  Ticket Status Updates        [OFF]                                     │
│  Daily Standup                [OFF]                                     │
│  Create Tickets               [OFF]                                     │
│                                                                         │
│  LAST 7 DAYS                                                            │
│  [142 Synced] [38 Linked] [12 Moved] [3 Created]                       │
│                                                                         │
│                    [View Activity Log →]                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Dev Workflows:

| Workflow | Description |
|----------|-------------|
| Auto-Sync | Pull messages & tickets hourly |
| Link Conversations | Match Slack messages to Linear tickets |
| Ticket Status Updates | Auto-move tickets based on context |
| Daily Standup | Post summary to Slack |
| Create Tickets | Auto-create from untracked conversations |

---

## 2. Stakeholder View (New)

**Who**: Product managers, team leads, executives, non-technical team members

**Purpose**: Get visibility without the noise

### What they see:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  STAKEHOLDER                                                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  THIS WEEK                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  📊 12 tickets completed                                        │   │
│  │  🚀 3 tickets moved to review                                   │   │
│  │  💬 47 conversations tracked                                    │   │
│  │  ⚠️  5 blockers identified                                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  NOTIFICATIONS                                                          │
│  Weekly Email Summary           [ON ]                                   │
│  Slack Digest (#pm-updates)     [ON ]                                   │
│  Blocker Alerts                 [OFF]                                   │
│                                                                         │
│  TEAM                                                                   │
│  alice@company.com (Dev)        [Admin]                                 │
│  bob@company.com (Stakeholder)  [Member]                                │
│  + Invite team member                                                   │
│                                                                         │
│                    [View Full Report →]                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Stakeholder Workflows (Notifications):

| Workflow | Description |
|----------|-------------|
| Weekly Email Summary | Monday morning recap of last week |
| Slack Digest | Daily summary posted to a channel |
| Blocker Alerts | Instant notification when blockers detected |
| Progress Reports | Automated weekly/monthly reports |

---

## 3. Team & Invites

### How It Works

**Owner** (the person who signed up):
- Pays the bill
- Can do everything
- Can invite Admins or Members
- Can switch between Dev/Stakeholder views

**When inviting someone:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Invite Team Member                                                     │
│                                                                         │
│  Email: [bob@company.com                    ]                           │
│                                                                         │
│  Permission:  ○ Admin (can invite others, configure)                    │
│               ● Member (view only)                                      │
│                                                                         │
│  View:        ○ Dev (integrations, workflows, activity)                 │
│               ● Stakeholder (reports, summaries)                        │
│                                                                         │
│                                              [Send Invite]              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Invite Flow

```
Owner/Admin clicks "Invite"
       │
       ▼
Selects permission (Admin/Member) + view (Dev/Stakeholder)
       │
       ▼
Invitee receives email
       │
       ▼
Invitee creates account (or logs in if existing)
       │
       ▼
Invitee joins team with assigned permission + view
```

### Data Model

```
tenant
  ├── owner_user_id          (the person who pays)
  └── members[]
        ├── user_id
        ├── permission: 'admin' | 'member'
        ├── view: 'dev' | 'stakeholder'
        └── invited_by
        
user
  ├── id
  ├── email
  ├── teams[]                 (can belong to multiple teams)
  └── default_view: 'dev' | 'stakeholder'
```

---

## 4. Switching Views

Users can switch between views (if they have permission):

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Corta.ai                           [DEV ▼] Pricing Dashboard Log out   │
│                                      ├─────────┤                        │
│                                      │ Dev     │                        │
│                                      │ Stakeholder │                    │
│                                      └─────────┘                        │
└─────────────────────────────────────────────────────────────────────────┘
```

- **Devs** can switch to Stakeholder view (to see what stakeholders see)
- **Stakeholders** only see Stakeholder view
- **Admins** can see both + team management

---

## 5. URL Structure

```
/dashboard              → Redirects based on user's role/preference
/dashboard/dev          → Dev view (integrations, workflows, activity)
/dashboard/stakeholder  → Stakeholder view (reports, notifications, team)
/dashboard/team         → Team management (admin only)
/dashboard/activity     → Activity log (dev only)
/dashboard/reports      → Full reports (stakeholder)
```

---

## 6. What's Shared vs Separate

### Shared (same data, same tenant):
- Slack messages
- Linear tickets
- GitHub PRs/issues
- Activity log data

### Separate by view:
- **Dev**: Raw activity log, workflow toggles, integration status
- **Stakeholder**: Summarized reports, notification preferences, team invites

---

## Implementation Order

1. **Phase 1** (current): Dev view ✅
2. **Phase 2**: Add role to user, view switcher in header
3. **Phase 3**: Stakeholder dashboard with reports
4. **Phase 4**: Team invites & management
5. **Phase 5**: Stakeholder notification workflows

---

## Decisions Made

1. **Can one person be both Dev and Stakeholder?**
   - ✅ Owner/Admin can switch views
   - Members are locked to their assigned view

2. **Who creates the team?**
   - ✅ First user becomes Owner automatically
   - Owner can invite Admins or Members

3. **Who pays?**
   - ✅ Owner controls billing
   - Admins can manage team but not billing

4. **Should Stakeholders see the Activity Log?**
   - ✅ No - too noisy
   - They get summarized reports instead

---

## Open Questions

1. **Billing model**
   - Per-seat pricing?
   - Flat rate per team?
   - Different prices for Dev vs Stakeholder seats?
   - Free for Stakeholders, pay for Devs?

2. **Can a user belong to multiple teams?**
   - Probably yes (consultant scenario)
   - Each team is a separate tenant with separate billing

3. **What happens if Owner leaves?**
   - Must transfer ownership first
   - Or team gets frozen

