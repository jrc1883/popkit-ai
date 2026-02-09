---
description: "check | list | research | synthesize | stats [options]"
argument-hint: "<subcommand> [options]"
---

# /popkit-core:upstream - Anthropic Update Tracking

Track Anthropic repository updates (Claude Code, official plugins, SDKs) with research state management - essentially a "dependabot for Claude Code."

## Problem

Manually tracking which Anthropic changelog items have been researched becomes "muddy and confusing":

- Unclear if already researched a specific item
- No historical tracking of what was investigated
- No linkage between Anthropic changes and PopKit issues/PRs

## Solution

Automated tracking with status lifecycle: **pending_research** → **researched** → **synthesized**

---

## Subcommands

| Subcommand | Description                               |
| ---------- | ----------------------------------------- |
| check      | Check monitored repos for new updates     |
| list       | List changelog items by status            |
| research   | Research a specific item with guided flow |
| synthesize | Mark item as integrated, link issues/PRs  |
| stats      | Show tracking statistics and velocity     |

---

## Monitored Repositories

1. **anthropics/claude-code** - Core CLI tool
2. **anthropics/claude-plugins-official** - Official plugin collection
3. **anthropics/anthropic-sdk-python** - Python SDK
4. **anthropics/anthropic-sdk-typescript** - TypeScript SDK

---

## check

Check all monitored repositories for new updates since last check.

### Process

1. Load tracking state from `.claude/popkit/upstream-tracking.json`
2. For each monitored repo:
   - Fetch releases via `gh api repos/{owner}/{repo}/releases`
   - Fetch recent commits via `gh api repos/{owner}/{repo}/commits` (main branch, since last check)
   - Compare with tracked items
   - Add new items with status `pending_research`
3. Save updated tracking state
4. Report summary

### Output

```
🔍 Checking Anthropic repositories for updates...

anthropics/claude-code
  ✓ Latest: v2.1.0 (released 2026-01-25)
  📋 1 new item found:
    - Enhanced hook system (2026-01-20)

anthropics/claude-plugins-official
  ✓ Up to date
  📋 2 new items found:
    - feature-dev: New template system (2026-01-29)
    - debugging: Added trace visualization (2026-01-27)

anthropics/anthropic-sdk-python
  ✓ Latest: v0.42.0 (released 2026-01-28)

anthropics/anthropic-sdk-typescript
  ✓ Latest: v0.42.0 (released 2026-01-28)

Summary: 3 new items need research
Last checked: 2026-01-31T10:30:00Z
```

### Options

| Flag      | Description                     |
| --------- | ------------------------------- |
| --brief   | One-line summary for routines   |
| --json    | Machine-readable JSON output    |
| --verbose | Show detailed discovery process |

### Brief Output (for morning routine)

```
🔍 Anthropic Updates: 3 items need research
```

---

## list

List tracked changelog items filtered by status.

### Usage

```bash
/popkit-core:upstream list               # All items
/popkit-core:upstream list pending       # Need research
/popkit-core:upstream list researched    # Researched
/popkit-core:upstream list synthesized   # Integrated
```

### Output

```
📋 Upstream Tracking Status

Pending Research (3 items):
  [claude-code-hooks] Enhanced hook system
    Discovered: 2026-01-20
    URL: https://github.com/anthropics/claude-code/commit/abc123

  [feature-dev-templates] New template system
    Discovered: 2026-01-29
    URL: https://github.com/anthropics/claude-plugins-official/commits/main

  [debugging-trace] Added trace visualization
    Discovered: 2026-01-27
    URL: https://github.com/anthropics/claude-plugins-official/commits/main

Researched (2 items):
  [claude-code-v2.1.0] Claude Code v2.1.0
    Impact: none - MCP improvements don't affect PopKit
    Research Date: 2026-01-26

  [code-review-confidence] code-review: Confidence scoring
    Impact: alignment - PopKit's 80+ threshold aligns well
    Research Date: 2026-01-28

Synthesized (1 item):
  [code-review-confidence] code-review: Confidence scoring
    Impact: alignment
    Related: Issue #213, PR #214
    Notes: Updated CLAUDE.md integration docs
```

### Options

| Flag   | Description             |
| ------ | ----------------------- |
| --json | Machine-readable output |
| --repo | Filter by repository    |

---

## research

Guided workflow to research a specific changelog item.

### Usage

```bash
/popkit-core:upstream research <item-id>
```

### Workflow

1. **Fetch Details**
   - Load item from tracking state
   - Display title, URL, discovery date
   - Show related context (release notes, commit messages)

2. **Research Prompts**
   - Open URLs in browser or fetch with WebFetch
   - Prompt user for research summary
   - Ask about PopKit impact assessment

3. **Impact Assessment**
   - critical - Breaking changes, security issues
   - high - New features for significant PopKit enhancement
   - medium - Improvements worth considering
   - low - Minor updates, unlikely to affect PopKit
   - none - No impact on PopKit
   - alignment - Confirms PopKit's approach is correct

4. **Action Decision**
   - Ask if issue/PR should be created
   - If yes, prompt for issue title and description
   - Create GitHub issue with `upstream-tracking` label

5. **Update Status**
   - Save research summary and impact to tracking state
   - Update status to `researched`
   - Link created issue if applicable

### Example Flow

```
📖 Researching: Enhanced hook system

ID: claude-code-hooks
Repository: anthropics/claude-code
Discovered: 2026-01-20T00:00:00Z
URL: https://github.com/anthropics/claude-code/commit/abc123

Opening URL in browser... (or fetching with WebFetch)

Research Summary:
> (User input) Claude Code v2.0.5 added new hook types for
> pre-tool and post-tool events. This could enhance PopKit's
> measurement and debugging capabilities.

PopKit Impact Assessment:
1. critical - Breaking changes
2. high - Significant enhancement
3. medium - Worth considering
4. low - Minor update
5. none - No impact
6. alignment - Confirms approach

Choose impact (1-6): 2

Should we create a GitHub issue to track this? (y/n): y

Issue Title: Explore new hook types in Claude Code v2.0.5

Issue Created: #219
URL: https://github.com/jrc1883/popkit-claude/issues/219

✅ Research Complete
Status: pending_research → researched
Impact: high
Related: Issue #219
```

---

## synthesize

Mark a researched item as synthesized and link to PopKit issues/PRs.

### Usage

```bash
/popkit-core:upstream synthesize <item-id> \
  --issues #213,#214 \
  --prs #215 \
  --notes "Updated CLAUDE.md integration docs"
```

### Process

1. Load item from tracking state
2. Verify status is `researched` (can't synthesize pending items)
3. Update item with:
   - related_issues
   - related_prs
   - notes
   - status = `synthesized`
4. Save tracking state

### Output

```
✅ Item Synthesized

[code-review-confidence] code-review: Confidence scoring

Status: researched → synthesized
Related Issues: #213, #214
Related PRs: #215
Notes: Updated CLAUDE.md integration docs

Thank you for completing the research cycle!
```

### Options

| Flag     | Description                   |
| -------- | ----------------------------- |
| --issues | Comma-separated issue numbers |
| --prs    | Comma-separated PR numbers    |
| --notes  | Integration notes             |

---

## stats

Show upstream tracking statistics and research velocity.

### Output

```
📊 Upstream Tracking Statistics

Total Items Tracked: 15
├─ Pending Research: 3 (20%)
├─ Researched: 8 (53%)
├─ Synthesized: 4 (27%)

Impact Distribution:
├─ Critical: 0
├─ High: 2
├─ Medium: 5
├─ Low: 3
└─ None: 5

Research Velocity:
├─ Average research time: 2.5 days
├─ Items researched this week: 3
├─ Items synthesized this month: 7

Last Repository Check: 2 hours ago
Next Scheduled Check: In 22 hours (daily)
```

### Options

| Flag   | Description                  |
| ------ | ---------------------------- |
| --json | Machine-readable JSON output |
| --repo | Filter by repository         |

---

## Data Model

**Storage**: `.claude/popkit/upstream-tracking.json`

```json
{
  "repositories": {
    "anthropics/claude-code": {
      "last_checked": "2026-01-31T10:30:00Z",
      "latest_release": "v2.1.0",
      "changelog_items": [
        {
          "id": "claude-code-v2.1.0",
          "type": "release",
          "title": "Claude Code v2.1.0",
          "url": "https://github.com/anthropics/claude-code/releases/tag/v2.1.0",
          "published_date": "2026-01-25T00:00:00Z",
          "discovered_date": "2026-01-31T10:30:00Z",
          "status": "researched",
          "research_summary": "Added new MCP features. No PopKit integration needed.",
          "research_date": "2026-01-26T00:00:00Z",
          "popkit_impact": "none",
          "related_issues": [],
          "related_prs": [],
          "notes": "MCP improvements don't affect PopKit's CLI-based approach"
        }
      ]
    }
  },
  "settings": {
    "check_frequency_hours": 24,
    "auto_check_in_morning_routine": true,
    "notification_threshold": "all"
  },
  "statistics": {
    "total_items_tracked": 15,
    "pending_research": 3,
    "researched": 8,
    "synthesized": 4,
    "avg_research_time_days": 2.5
  }
}
```

---

## Integration with Morning Routine

Add to `/popkit-dev:routine morning`:

```yaml
- id: check_upstream
  description: Check for Anthropic updates
  type: command
  command: /popkit-core:upstream check --brief
  optional: true
  settings_key: check_upstream_in_morning
```

User can disable with:

```bash
/popkit-dev:routine morning --no-upstream
```

---

## Architecture

| Component           | Location                              | Purpose             |
| ------------------- | ------------------------------------- | ------------------- |
| Command Definition  | commands/upstream.md                  | This file           |
| Tracking Utility    | hooks/utils/upstream_tracker.py       | Core tracking logic |
| Data Storage        | .claude/popkit/upstream-tracking.json | Persistent state    |
| Morning Integration | commands/routine.md                   | Auto-check support  |

**Related:**

- `/popkit-dev:routine morning` - Integrated auto-check
- `/popkit-core:stats` - Similar statistics pattern
- `/popkit-dev:issue` - Issue creation pattern

---

## Examples

### Daily Workflow

```bash
# Morning: Check for updates
/popkit-dev:routine morning
# Output includes: 🔍 Anthropic Updates: 3 items need research

# List pending items
/popkit-core:upstream list pending

# Research an item
/popkit-core:upstream research claude-code-hooks
# (Interactive guided workflow)

# After creating issue and implementing
/popkit-core:upstream synthesize claude-code-hooks \
  --issues #219 \
  --notes "Implemented new hook integration"
```

### Weekly Review

```bash
# See overall statistics
/popkit-core:upstream stats

# Review all researched items
/popkit-core:upstream list researched

# Export for reporting (JSON)
/popkit-core:upstream stats --json > upstream-report.json
```

---

## Future Enhancements

### Phase 3: Automation

- GitHub Actions daily check
- Auto-discovery of new Anthropic plugins
- LLM-powered impact assessment
- Slack/email notifications for critical updates
- Export to markdown reports

---

## Success Criteria

- [ ] All monitored repos tracked with last check timestamp
- [ ] Changelog items categorized by status and impact
- [ ] No duplicate research on same items
- [ ] Clear linkage between Anthropic updates and PopKit changes
- [ ] Morning routine shows upstream status
- [ ] Research velocity metrics available
