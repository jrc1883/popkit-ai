---
title: Morning/Nightly Routines
description: Day-bracketing workflows with health checks
---

# Morning/Nightly Routines

PopKit provides day-bracketing workflows that check project health at the start and end of each day. Routines are **programmatic workflows** with predictable, deterministic steps - not AI-generated guesses.

## The Routine Concept

Morning and nightly are two **built-in routines** (ID: `pk`). You can also create custom routines for your specific workflow needs.

| Type    | Built-in ID  | Purpose                    | Output              |
| ------- | ------------ | -------------------------- | ------------------- |
| Morning | `pk`         | Start-of-day health check  | Ready to Code Score |
| Nightly | `pk`         | End-of-day cleanup & save  | Sleep Score         |
| Custom  | `<prefix>-N` | Project-specific workflows | Custom score        |

---

## How Morning Routine Works

**Command**: `/popkit-dev:routine morning`

The morning routine executes a **5-step deterministic pipeline**:

### Step 1: Restore Session

**What it does**: Reads `STATUS.json` to restore previous context

**Programmatic**:

```python
# Reads STATUS.json from project root
status = json.load("STATUS.json")
session_data = {
    "last_nightly_score": status["last_nightly_routine"]["sleep_score"],
    "last_work_summary": status["git_status"]["action_required"],
    "previous_branch": status["git_status"]["current_branch"],
}
```

### Step 2: Collect State

**What it does**: Runs shell commands to gather current project state

**Programmatic**:

```bash
# Git state
git fetch --prune
git status --porcelain
git rev-list --count HEAD..origin/main
git stash list

# GitHub state (if gh CLI available)
gh pr list --state open --json number,title,reviewDecision
gh issue list --state open --json number,title,assignees,labels

# Service health (platform-specific)
pgrep -f node
pgrep -f redis-server
pgrep -f postgres
```

### Step 3: Calculate Score

**What it does**: Applies deterministic scoring formula

**Programmatic**:

| Check                   | Points | Criteria                    |
| ----------------------- | ------ | --------------------------- |
| Clean working directory | 25     | No uncommitted changes      |
| Tests passing           | 25     | All tests pass              |
| CI status               | 20     | Last run successful         |
| Dependencies            | 15     | No critical vulnerabilities |
| Documentation           | 15     | CLAUDE.md up to date        |

Score interpretation:

- **90-100**: Green - All systems go
- **70-89**: Yellow - Minor issues
- **< 70**: Red - Critical issues need attention

### Step 4: Generate Report

**What it does**: Formats collected data into readable output

Uses templates from `packages/popkit-dev/output-styles/morning-dashboard.md`

### Step 5: Capture State

**What it does**: Writes current state to `STATUS.json` for tomorrow

**Programmatic**:

```python
# Writes to STATUS.json
{
    "session_id": "morning-2024-01-15-083045",
    "timestamp": "2024-01-15T08:30:45Z",
    "last_morning_routine": {
        "executed_at": "2024-01-15T08:30:45Z",
        "ready_to_code_score": "87/100",
        "breakdown": {...}
    },
    "recommendations": {
        "before_coding": ["Sync with remote: git pull (3 commits behind)"],
        "todays_focus": ["Review 2 pending PRs"]
    }
}
```

---

## How Nightly Routine Works

**Command**: `/popkit-dev:routine nightly`

### Sleep Score Calculation

| Check                  | Points | Criteria                        |
| ---------------------- | ------ | ------------------------------- |
| Uncommitted work saved | 25     | No unsaved changes or committed |
| Branches cleaned       | 20     | No stale branches               |
| Issues updated         | 20     | Today's issues have status      |
| CI passing             | 15     | Last run successful             |
| Services stopped       | 10     | Dev services shut down          |
| Logs archived          | 10     | Session logs saved              |

---

## Routine Output Examples

### Morning Routine

```
☀️ Morning Routine Report

Ready to Code Score: 92/100 ✅

✅ Git Status: Clean working tree
✅ Dependencies: Up to date
✅ Tests: All passing
⚠️  Security: 2 low-severity vulnerabilities

📋 Today's Priorities:
1. Complete PR #123 (Code review feedback)
2. Work on Issue #456 (User authentication)
3. Update documentation for v2.0

🎯 Next Steps:
- Fix security vulnerabilities (low priority)
- Continue work on feat/auth branch
- Review open PRs
```

### Nightly Routine

```
🌙 Nightly Routine Report

Sleep Score: 88/100 ✅

📊 Today's Activity:
- 5 commits created
- 12 files modified
- +324 lines added, -87 lines removed

✅ State captured for tomorrow
✅ Branches cleaned up
⚠️  Uncommitted changes stashed

💤 Tomorrow's Context:
- Resume work on feat/auth branch
- Review PR feedback on #123
- Continue with Issue #456

🎯 Recommended Actions:
- Push feat/auth branch (recommended)
- Other
```

---

## Profiles

Pre-configured flag combinations for common use cases:

| Profile    | Speed  | Flags Applied                                             |
| ---------- | ------ | --------------------------------------------------------- |
| `minimal`  | < 10s  | `--quick --skip-tests --skip-services --skip-deployments` |
| `standard` | ~20s   | (defaults)                                                |
| `thorough` | ~60s   | `--full --measure`                                        |
| `ci`       | varies | `--optimized --measure --simple --no-cache`               |

```bash
# Fast morning check
/popkit-dev:routine morning --profile minimal

# Deep analysis with metrics
/popkit-dev:routine morning --profile thorough
```

---

## All Flags

| Flag                 | Effect                                     |
| -------------------- | ------------------------------------------ |
| `--quick`            | One-line summary instead of full report    |
| `--measure`          | Track performance metrics                  |
| `--optimized`        | Use caching for efficiency                 |
| `--no-cache`         | Force fresh execution, bypass cache        |
| `--simple`           | Markdown tables instead of ASCII dashboard |
| `--skip-tests`       | Skip test execution                        |
| `--skip-services`    | Skip service health checks                 |
| `--skip-deployments` | Skip deployment status check               |
| `--full`             | Include all checks (slower)                |
| `--no-nightly`       | Skip "From Last Night" section             |
| `--no-upstream`      | Skip Anthropic upstream update check       |

### Smart Defaults

- `--measure` automatically enables `--simple` for parseable output
- `--full` overrides `--optimized` (thorough checks can't be cached)

---

## Custom Routines

Create project-specific routines beyond `pk`.

### Available Slots

Each project can have up to **5 custom routines** per type (morning/nightly).

IDs use your project prefix: `rc-1`, `rc-2`, `maa-1`, etc.

### Create a Custom Routine

```bash
/popkit-dev:routine generate
```

This creates:

```
.claude/popkit/routines/morning/<prefix>-1/
├── routine.md      # Routine definition with checks
├── config.json     # Score weights and settings
└── checks/         # Custom check scripts
```

### List Available Routines

```bash
/popkit-dev:routine list
```

Output:

```
Morning Routines

| ID    | Name                  | Default | Created    |
|-------|-----------------------|---------|------------|
| pk    | PopKit Standard       | yes     | (built-in) |
| rc-1  | Full Stack Check      |         | 2024-01-15 |

Slots available: 4 of 5
```

### Set Default Routine

```bash
/popkit-dev:routine set rc-1
```

### Run Specific Routine

```bash
/popkit-dev:routine morning run rc-1
```

---

## Configuration Files

### Main Config

Location: `.claude/popkit/config.json`

```json
{
  "project_name": "Reseller Central",
  "prefix": "rc",
  "defaults": {
    "morning": "pk",
    "nightly": "pk"
  },
  "routines": {
    "morning": [
      {
        "id": "rc-1",
        "name": "Full Stack Check",
        "description": "Includes database and Redis health",
        "created": "2024-01-15T08:00:00Z",
        "based_on": "pk"
      }
    ],
    "nightly": []
  }
}
```

### Session State

Location: `STATUS.json` (project root)

This file persists across sessions and enables context restoration.

See [Configuration Reference](/reference/configuration/) for complete schema documentation.

---

## Performance Measurement

Track routine efficiency with `--measure`:

```bash
/popkit-dev:routine morning --measure
```

View measurements:

```bash
/popkit-core:stats routine
/popkit-core:stats routine morning --all
```

Measurements include:

- Duration (ms)
- Tool calls
- Token usage (input/output)
- Cost estimate (USD)
- Per-check breakdown

---

## Best Practices

1. **Run Morning Routine First**: Start each day with health check
2. **Run Nightly Routine Last**: End each day with cleanup
3. **Address Red Scores**: Fix critical issues before coding
4. **Use Profiles**: Match routine depth to your time
5. **Create Custom Routines**: Tailor checks to your stack

---

## Troubleshooting

### Morning Routine Shows Red Score

**Symptom**: Low Ready to Code score

**Solutions**:

- Fix test failures
- Update dependencies
- Address security issues
- Clean git state

### Nightly Routine Shows Red Score

**Symptom**: Low Sleep score

**Solutions**:

- Commit or stash changes
- Push completed work
- Close or save work-in-progress
- Clean up temporary files

### Context Not Restored

**Symptom**: Morning routine doesn't restore previous work

**Solution**:

- Ensure nightly routine ran successfully
- Check `STATUS.json` exists in project root
- Manually run: `/popkit-core:project restore`

---

## Next Steps

- Review [Configuration Reference](/reference/configuration/)
- Learn about [Power Mode](/features/power-mode/)
- Explore [Feature Development](/features/feature-dev/)
- Review [Git Workflows](/features/git-workflows/)
