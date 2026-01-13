---
description: "list | create | close | report | health [--json, --verbose]"
argument-hint: "<subcommand> [name] [options]"
---

# /popkit-dev:milestone - Milestone Management

Manage GitHub milestones with progress tracking, health checks, and release planning.

## Usage

```
/popkit-dev:milestone <subcommand> [options]
```

## Subcommands

| Subcommand | Description                                 |
| ---------- | ------------------------------------------- |
| `list`     | List all milestones with progress (default) |
| `create`   | Create a new milestone                      |
| `close`    | Close a milestone with summary              |
| `report`   | Generate detailed milestone report          |
| `health`   | Check milestone health metrics              |

---

## Subcommand: list (default)

List all milestones with progress indicators.

```
/popkit-dev:milestone                    # List open milestones
/popkit-dev:milestone list               # Same as above
/popkit-dev:milestone list --all         # Include closed milestones
/popkit-dev:milestone list --json        # JSON output for scripting
```

### Flags

| Flag     | Description               |
| -------- | ------------------------- |
| `--all`  | Include closed milestones |
| `--json` | Output as JSON            |

### Output Format

```
📊 Milestones

| Milestone | Progress | Due Date   | Open | Closed | Status |
|-----------|----------|------------|------|--------|--------|
| v1.0.0    | ████████ | 2024-12-09 | 0    | 45     | ✅ Done |
| v1.1.0    | ███░░░░░ | 2025-01-15 | 13   | 7      | 🔄 Active |
| v2.0.0    | ░░░░░░░░ | 2025-06-01 | 5    | 0      | 📋 Planning |

Legend:
  ✅ Done = 100% complete and closed
  🔄 Active = In progress
  ⚠️ At Risk = Behind schedule
  📋 Planning = Not started
```

### Process

1. Fetch milestones via `gh api repos/{owner}/{repo}/milestones`
2. Calculate progress percentage
3. Determine status (Done/Active/At Risk/Planning)
4. Format as table

**Execute:**

```bash
gh api repos/{owner}/{repo}/milestones --jq '.[] | {title, open_issues, closed_issues, due_on, state}'
```

---

## Subcommand: create

Create a new milestone with optional due date.

```
/popkit-dev:milestone create "v1.2.0"
/popkit-dev:milestone create "v1.2.0" --due 2025-03-01
/popkit-dev:milestone create "v1.2.0" --description "Feature release"
```

### Flags

| Flag            | Description                  |
| --------------- | ---------------------------- |
| `--due`         | Due date (YYYY-MM-DD format) |
| `--description` | Milestone description        |

### Interactive Flow

When called without sufficient args:

```
Use AskUserQuestion tool with:
- question: "What should this milestone be named?"
- header: "Name"
- options:
  1. label: "v1.2.0"
     description: "Next minor version"
  2. label: "v2.0.0"
     description: "Next major version"
  3. label: "Q1 2025"
     description: "Quarterly milestone"
- multiSelect: false
```

Then prompt for due date:

```
Use AskUserQuestion tool with:
- question: "When is this milestone due?"
- header: "Due Date"
- options:
  1. label: "2 weeks"
     description: "Sprint-length milestone"
  2. label: "1 month"
     description: "Monthly milestone"
  3. label: "3 months"
     description: "Quarterly milestone"
  4. label: "No due date"
     description: "Open-ended milestone"
- multiSelect: false
```

### Process

**Execute:**

```bash
gh api repos/{owner}/{repo}/milestones \
  --method POST \
  -f title="v1.2.0" \
  -f description="Feature release" \
  -f due_on="2025-03-01T00:00:00Z"
```

---

## Subcommand: close

Close a milestone with a summary report.

```
/popkit-dev:milestone close "v1.0.0"
/popkit-dev:milestone close "v1.0.0" --comment
```

### Flags

| Flag        | Description                                 |
| ----------- | ------------------------------------------- |
| `--comment` | Post summary as comment on milestone issues |

### Process

1. Fetch milestone details
2. Get all issues in milestone
3. Generate summary statistics
4. Close the milestone
5. Optionally post summary comments

### Output

```
📋 Closing Milestone: v1.0.0

Summary:
  Total Issues: 45
  Closed: 45 (100%)
  Open: 0

By Type:
  🐛 Bug fixes: 12
  ✨ Features: 28
  📚 Documentation: 5

Key Contributors:
  @jrc1883: 38 issues

Milestone closed successfully!
```

**Execute:**

```bash
gh api repos/{owner}/{repo}/milestones/{number} \
  --method PATCH \
  -f state="closed"
```

---

## Subcommand: report

Generate a detailed milestone report.

```
/popkit-dev:milestone report "v1.1.0"
/popkit-dev:milestone report "v1.1.0" --format markdown
/popkit-dev:milestone report "v1.1.0" --verbose
```

### Flags

| Flag        | Description                                         |
| ----------- | --------------------------------------------------- |
| `--format`  | Output format: `text` (default), `markdown`, `json` |
| `--verbose` | Include issue-by-issue breakdown                    |

### Output (Markdown)

```markdown
# Milestone Report: v1.1.0

## Overview

| Metric               | Value            |
| -------------------- | ---------------- |
| Progress             | 35% (7/20)       |
| Due Date             | January 15, 2025 |
| Days Remaining       | 37               |
| Velocity             | 0.5 issues/day   |
| Projected Completion | February 3, 2025 |

## Status

⚠️ **At Risk**: At current velocity, milestone will miss due date by ~19 days.

## Breakdown

### Completed (7)

- ✅ #125: User Signup & Billing (Epic)
- ✅ #126: Premium Feature Gating (Epic)
- ✅ #127: Research Management System (Epic)
- ...

### In Progress (3)

- 🔄 #128: GitHub Workflow Refinement
- 🔄 #148: Milestone and Audit Commands
- 🔄 #149: GitHub Projects Integration

### Not Started (10)

- 📋 #111: Multi-Model Foundation
- 📋 #112: Universal MCP Server
- ...

## Recommendations

1. Consider moving #111, #112 to v2.0.0 (scope too large)
2. Add more resources to #128 (blocking other work)
3. Re-evaluate due date based on scope
```

---

## Subcommand: health

Check milestone health metrics and provide recommendations.

```
/popkit-dev:milestone health "v1.1.0"
/popkit-dev:milestone health --all
```

### Flags

| Flag    | Description               |
| ------- | ------------------------- |
| `--all` | Check all open milestones |

### Health Metrics

1. **Velocity** - Issues closed per day
2. **Scope Creep** - New issues added after start
3. **Blocker Count** - Issues with "blocked" label
4. **At-Risk Percentage** - Issues with P0/P1 not in progress

### Output

```
🏥 Milestone Health: v1.1.0

Overall Health: 🟡 Fair

| Metric | Value | Status |
|--------|-------|--------|
| Progress | 35% | 🟡 |
| Velocity | 0.5/day | 🔴 |
| Days to Due | 37 | 🟡 |
| Blockers | 2 | 🟡 |
| Scope Creep | +5 issues | 🟡 |

Diagnosis:
- Velocity is below target (need 0.8/day to hit deadline)
- 2 issues are blocked (#148, #150)
- 5 issues added after milestone start

Recommendations:
1. Unblock #148 (dependency on GitHub Pro)
2. Consider reducing scope or extending due date
3. Focus on P0/P1 issues first
```

### Health Score Calculation

```
Health Score = (Progress Score + Velocity Score + Risk Score) / 3

Progress Score:
  - 100 if on track (progress >= expected)
  - progress/expected * 100 otherwise

Velocity Score:
  - 100 if velocity >= required
  - velocity/required * 100 otherwise

Risk Score:
  - 100 - (blockers * 10) - (scope_creep * 5)
```

---

## Integration

### With /popkit-dev:issue

```
/popkit-dev:issue list --milestone "v1.1.0"   # Issues in milestone
/popkit-dev:issue edit 42 --milestone "v1.1.0"  # Add to milestone
```

### With /popkit-ops:audit

```
/popkit-ops:audit quarterly  # Includes milestone analysis
```

### With /popkit-dev:dev

```
/popkit-dev:dev work #148  # Shows milestone context
```

---

## Examples

```bash
# List all milestones
/popkit-dev:milestone

# Create new milestone
/popkit-dev:milestone create "v1.2.0" --due 2025-03-01

# Check health before release
/popkit-dev:milestone health "v1.1.0"

# Generate release report
/popkit-dev:milestone report "v1.0.0" --format markdown

# Close completed milestone
/popkit-dev:milestone close "v1.0.0"
```

---

## Architecture Integration

| Component         | Integration                              |
| ----------------- | ---------------------------------------- |
| GitHub API        | `gh api repos/{owner}/{repo}/milestones` |
| Issue Linking     | `gh issue list --milestone`              |
| Progress Tracking | Calculate from open/closed counts        |
| Velocity          | Track daily closes via commit timestamps |
| Reports           | Markdown formatting with tables          |

## Related Commands

| Command                   | Purpose                                 |
| ------------------------- | --------------------------------------- |
| `/popkit-dev:issue`       | Manage individual issues                |
| `/popkit-ops:audit`       | Periodic review with milestone analysis |
| `/popkit-dev:git release` | Create releases tied to milestones      |
