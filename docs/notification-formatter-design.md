# PopKit Notification Formatter Design

## Overview

This document defines the notification formatting system that auto-formats structured messages from PopKit's Power Mode into human-readable output across three categories: **Telemetry**, **Project Data**, and **Status**.

---

## Part 1: Message Type Mapping

### Category 1: TELEMETRY (Developer-Facing)

Messages that help you optimize PopKit and serve customers better. Safe to log/store (no sensitive data).

| Protocol Message | Insight Type | Formatter Output | Example |
|-----------------|--------------|-----------------|---------|
| `HEARTBEAT` | N/A | Agent state snapshot | `🔵 code-explorer active (3:45m, 12 files touched)` |
| `PROGRESS` | N/A | Progress with metrics | `📊 code-reviewer 65% complete (8,420 tokens used)` |
| `BOUNDARY_ALERT` | `WARNING` | Boundary violation notice | `⚠️ Agent approaching file limit (245 of 250 files)` |
| `DRIFT_ALERT` | `WARNING` | Agent off-track warning | `⚠️ Agent idle for 90s, check if blocked` |
| `SYNC_ACK` | N/A | Sync barrier acknowledgment | `✓ All 4 agents synchronized at barrier-1` |
| Metrics snapshot | N/A | Session metrics summary | `📈 Session: 12 min, 3 agents, 24,560 tokens, 85% quality` |

**Storage**: All Redis streams + local JSON (for all users)

---

### Category 2: PROJECT DATA (Inter-Agent Shared)

Structured context agents share with each other. Core to multi-agent coordination.

| Protocol Message | Insight Type | Formatter Output | Example |
|-----------------|--------------|-----------------|---------|
| `TASK` | N/A | Task assignment | `📋 code-architect assigned: Design OAuth 2.0 flow (src/auth/*.ts)` |
| `INSIGHT` | `DISCOVERY` | Finding shared | `🔍 Found existing OAuth setup in src/lib/auth.ts:1-45` |
| `INSIGHT` | `BLOCKER` | Obstacle blocking progress | `🚫 Cannot modify .env files (protected by guardrails)` |
| `INSIGHT` | `PATTERN` | Convention identified | `🎯 Project uses NextAuth.js pattern for auth` |
| `INSIGHT` | `QUESTION` | Clarification needed | `❓ Should OAuth providers override existing session logic?` |
| `INSIGHT` | `DOCS_NEEDED` | Documentation gap | `📝 auth.ts needs JSDoc comments explaining JWT flow` |
| `INSIGHT` | `DOCS_UPDATED` | Documentation completed | `✅ JSDoc comments added to src/lib/auth.ts` |
| `QUERY` | N/A | Agent asking for info | `❓ code-architect asks: What's the session expiry? (via insights)` |
| `RESPONSE` | N/A | Answer to query | `➜ code-explorer responds: JWT expires in 7 days (src/lib/auth.ts:23)` |
| `OBJECTIVE_UPDATE` | N/A | Goal clarification | `🎯 Objective refined: Add Google OAuth (keep existing session)` |
| `COURSE_CORRECT` | N/A | Redirect from coordinator | `↩️ Agent redirected: Focus on Google OAuth, skip Facebook` |
| `RESULT` | N/A | Handoff to next agent | `✅ code-explorer → code-architect: Ready for implementation (confidence: 85%)` |

**Storage**: Redis streams + local JSON (for all users)

**Format**: Maps to `agent-handoff.md` output style

---

### Category 3: STATUS (User-Visible)

What end-users see. Shown on statusline and workflow UI.

| Protocol Message | Base | Formatter Output | Display |
|-----------------|------|-----------------|---------|
| Workflow start | TASK | `🚀 Starting code review for PR #42` | Statusline + notification |
| Agent transition | RESULT | `➜ Passing to security-auditor (checking OAuth)` | Statusline + notification |
| Human decision needed | `HUMAN_REQUIRED` | `🤔 Awaiting approval: Add Google OAuth provider?` | Notification + blocking |
| Workflow blocked | DRIFT_ALERT | `⏸ Waiting for your decision (60s timeout)` | Statusline + notification |
| Workflow complete | RESULT (final) | `✅ Code review complete: 3 issues found, 2 approved` | Notification + summary |
| Agent busy | PROGRESS | `🔄 code-reviewer analyzing (2:34m)` | Statusline (live) |
| Agent idle | HEARTBEAT | `⏱️ code-explorer idle, waiting for user input` | Statusline (live) |
| Task failed | TASK_ORPHANED | `❌ Task failed: code-reviewer crashed, reassigning` | Notification + alert |

**Storage**: Latest state only (for statusline), historical in Redis/JSON

**Format**: Emoji + short text, designed for 80-char terminal width

---

## Part 2: Message Format Specifications

### Telemetry Message Format

```json
{
  "type": "HEARTBEAT",
  "from_agent": "code-explorer",
  "category": "telemetry",
  "formatted_output": "🔵 code-explorer active (3:45m, 12 files touched)",
  "metadata": {
    "agent_state": "active",
    "duration_seconds": 225,
    "files_touched": 12,
    "tools_used": ["Bash", "Read", "Grep"],
    "tool_call_count": 8,
    "confidence": 0.85
  },
  "timestamp": "2025-12-15T10:30:45Z"
}
```

**Safe to display**: ✅ Yes (only metrics, no sensitive data)

---

### Project Data Message Format

```json
{
  "type": "INSIGHT",
  "insight_type": "DISCOVERY",
  "from_agent": "code-explorer",
  "to_agents": ["code-architect"],
  "category": "project_data",
  "formatted_output": "## Agent Handoff Report\n\n**From:** code-explorer\n**To:** code-architect\n**Status:** completed\n**Confidence:** 85\n\n### Summary\nFound existing NextAuth.js auth setup with JWT sessions...",
  "raw_insight": {
    "content": "Found existing NextAuth.js implementation in src/lib/auth.ts",
    "relevance_tags": ["auth", "nextauth", "oauth"],
    "confidence": 0.85,
    "consumed_by": []
  },
  "timestamp": "2025-12-15T10:30:45Z"
}
```

**Safe to display**: ✅ Yes (project code context, no secrets)

---

### Status Message Format

```json
{
  "type": "WORKFLOW_STATUS",
  "source_message": "RESULT",
  "category": "status",
  "formatted_output": "✅ code-review complete: 3 issues, 2 approved",
  "metadata": {
    "workflow_state": "complete",
    "severity": "info",
    "action_required": false,
    "display_duration_seconds": 5
  },
  "timestamp": "2025-12-15T10:30:45Z"
}
```

**Safe to display**: ✅ Yes (summary only)

---

## Part 3: Formatter Hook Architecture

### Hook Configuration (hooks.json)

```json
{
  "Notification": [
    {
      "description": "Format power mode messages for human display",
      "hooks": [
        {
          "type": "command",
          "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/notification.py",
          "timeout": 10,
          "retry": {
            "max_attempts": 2,
            "backoff_seconds": 1
          }
        }
      ]
    }
  ]
}
```

---

### Formatter Implementation Path

**File**: `packages/plugin/hooks/notification.py`

**Responsibilities**:
1. Read raw message from stdin (JSON)
2. Determine message category (telemetry/project_data/status)
3. Apply appropriate formatter based on message type
4. Filter sensitive data (API keys, user IDs, etc.)
5. Apply output-style template (agent-handoff.md, etc.)
6. Output formatted message to stdout (JSON)
7. Store metadata (for later retrieval)

**Key Functions**:
- `format_telemetry_message(message)` → Emoji + metrics
- `format_project_data_message(message)` → Markdown (agent-handoff style)
- `format_status_message(message)` → Emoji + short text
- `sanitize_context(data)` → Remove API keys, credentials
- `enrich_with_metadata(formatted, original)` → Add source info

---

### Formatter Features

| Feature | Implementation |
|---------|----------------|
| **Output Style Alignment** | References `packages/plugin/output-styles/agent-handoff.md` for project data |
| **Emoji Support** | Consistent emoji set for agent states, actions, results |
| **Confidence Scores** | Displays 0-100 confidence from protocol.Insight |
| **File References** | Includes `file:line` references for code context |
| **Token Tracking** | Shows token usage per agent, phase, and total |
| **Time Formatting** | Human-readable duration (3:45m, 2h 15m, etc.) |
| **Sensitive Data Filtering** | Removes .env keys, API tokens, user emails |
| **Markdown Support** | Full markdown for long-form project data |
| **Storage Metadata** | Tracks original message ID, source, category |

---

## Part 4: Message Storage Architecture

### Upstash Redis Streams (Pro Tier)

```
Stream: pop:telemetry:metrics
  ├─ token-usage entries
  ├─ agent-state entries
  └─ boundary-alert entries

Stream: pop:project-data:insights
  ├─ discovery entries
  ├─ blocker entries
  └─ pattern entries

Stream: pop:status:workflow
  ├─ started
  ├─ handoff
  └─ complete
```

**Data Retention Policy**:
- **Free Tier**: 7 days (local JSON only)
- **Pro Tier**: 30 days (Redis streams)
- **Enterprise Tier**: 90 days + search capability

---

### Local JSON Fallback (Free Tier)

```
~/.popkit/messages/
├── sessions/
│   └── {session-id}.json          # Messages in session
├── telemetry/
│   └── {date}.json                # Daily telemetry logs
├── project-data/
│   └── {workflow-id}.json         # Workflow context
└── status/
    └── current.json               # Latest status
```

---

### Message Query API (Future)

```python
# Users should be able to query their own messages
api.popkit.com/v1/messages?
  session_id=sess_123
  category=telemetry
  start_date=2025-12-01
  end_date=2025-12-15
  agent_filter=code-reviewer
```

---

## Part 5: Pro Tier Storage Strategy

### Free Tier (Current)
- ✅ Local JSON storage (`.popkit/messages/`)
- ✅ 7-day retention (auto-cleanup)
- ✅ Session-based retrieval
- ❌ Cross-session search
- ❌ Cloud backup
- ❌ Shared team access

### Pro Tier (Proposed)
- ✅ Upstash Redis streams (30-day retention)
- ✅ Cross-session search
- ✅ API access to message history
- ✅ Team message sharing
- ✅ Telemetry analytics dashboard
- ✅ Workflow replay/debugging
- ❌ Vector search (requires additional setup)

### Enterprise Tier (Future)
- ✅ All Pro features
- ✅ 90-day retention
- ✅ Vector search (similarity queries on insights)
- ✅ Advanced analytics (ML pattern detection)
- ✅ Audit logging
- ✅ Custom retention policies
- ✅ Data export (CSV, JSON)

---

## Part 6: Implementation Timeline

| Phase | Components | Timeline |
|-------|-----------|----------|
| **Phase 1: Core Formatter** | notification.py, message mapping, basic templates | Week 1 |
| **Phase 2: Hook Integration** | hooks.json update, storage integration, testing | Week 2 |
| **Phase 3: Storage Layer** | Redis stream setup, local JSON fallback verification | Week 3 |
| **Phase 4: Pro Tier Infrastructure** | Stream queries, retention policies, API endpoints | Week 4 |
| **Phase 5: User-Facing Features** | Message history UI, analytics dashboard, exports | Week 5+ |

---

## Next Steps

1. ✅ Create message mapping (this document)
2. → Implement `notification.py` formatter
3. → Update `hooks.json` configuration
4. → Test with sample messages
5. → Document Upstash integration
6. → Plan Pro tier implementation

---

## Questions for Review

1. **Output Style**: Should each message category use a separate output-style template, or should we create a unified `message-formatter.md` template?

2. **Real-time vs Historical**: Should the formatter hook run on every message, or should we batch-format at intervals?

3. **Sensitive Data**: Beyond `.env` keys, what other data should we consider sensitive?

4. **Metadata Enrichment**: Should formatter automatically add git commit context, PR number, etc.?

5. **Emoji Consistency**: Should we create an `EMOJI_MAP` constant for consistency across the codebase?
