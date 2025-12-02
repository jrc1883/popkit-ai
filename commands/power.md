---
description: Power Mode management - check status, stop orchestration, or start with custom objective
---

# /popkit:power - Power Mode Management

Shortened command for Power Mode status and control. Full functionality available via `/popkit:power-mode`.

## Usage

```
/popkit:power <subcommand> [options]
```

## Subcommands

### status

Check current Power Mode status:

```
/popkit:power status
```

Output when active:
```
[+] POWER MODE ACTIVE

Session: abc123
Issue: #11 - Unified orchestration system
Started: 15 minutes ago
Runtime: 15m 32s

Current State:
  Phase: implementation (3/5)
  Progress: 45%
  Agents: 2 active

Active Agents:
  - code-architect: Designing API structure [T:28 P:60%]
  - test-writer-fixer: Writing unit tests [T:15 P:30%]

Recent Check-ins:
  10:05:32 code-architect: "Found existing auth patterns in src/auth/"
  10:04:18 test-writer-fixer: "Using Jest with existing test setup"

Insights Shared: 8
Patterns Learned: 3

Commands:
  /popkit:power stop    Stop Power Mode
  /popkit:work #11      Continue current issue
```

Output when inactive:
```
[i] POWER MODE INACTIVE

No active Power Mode session.

To start Power Mode:
  /popkit:work #N -p     Work on issue with Power Mode
  /popkit:power "task"   Start with custom objective
  /popkit:issues --power List issues recommending Power Mode

Redis Status: localhost:16379 [OK]
```

### stop

Stop Power Mode gracefully:

```
/popkit:power stop
```

Output:
```
[+] STOPPING POWER MODE

Sending stop signal to coordinator...
Waiting for active agents to complete current tool call...
Saving session state...
Cleaning up Redis channels...

Power Mode deactivated.

Session Summary:
  Session: abc123
  Issue: #11
  Runtime: 25m 18s
  Phases completed: 3/5
  Insights shared: 12
  Patterns learned: 5

Session transcript saved to:
  ~/.claude/power-mode-sessions/abc123.json

Resume later with:
  /popkit:work #11
```

### Custom Objective (no issue)

Start Power Mode with a custom objective (not tied to GitHub issue):

```
/popkit:power "Build user authentication with OAuth"
/popkit:power "Refactor database layer" --phases design,implement,test
```

Output:
```
[+] POWER MODE ACTIVATED

Objective: Build user authentication with OAuth
Source: Custom (no GitHub issue)

Configuration:
  Phases: explore -> design -> implement -> test -> review
  Agents: Auto-selected based on objective
  Timeout: 30 minutes

Redis: localhost:16379 [OK]
Status line: [POP] Phase: explore (1/5) [----------] 0%

Starting Phase 1: Explore...
```

## Options for Custom Objective

| Option | Description |
|--------|-------------|
| `--phases` | Override phases: `--phases design,implement,test` |
| `--agents` | Specify agents: `--agents reviewer,tester` |
| `--timeout` | Max runtime: `--timeout 45` (minutes) |

## Examples

```bash
# Check status
/popkit:power status

# Stop Power Mode
/popkit:power stop

# Start with custom objective
/popkit:power "Add dark mode toggle"

# Custom objective with specific phases
/popkit:power "Optimize database queries" --phases analyze,implement,test

# Custom objective with specific agents
/popkit:power "Security audit" --agents security-auditor
```

## Relationship to Other Commands

| Command | Relationship |
|---------|--------------|
| `/popkit:power-mode` | Full alias - same functionality |
| `/popkit:work #N` | Start Power Mode from GitHub issue |
| `/popkit:issues` | List issues to find candidates |
| `/popkit:init` | Set up Power Mode (Redis) |

## Status Line Integration

When Power Mode is active, the status line shows:

```
[POP] #11 Phase: implement (3/5) [####------] 40% (/power status | stop)
```

Components:
- `[POP]` - Yellow bold indicator
- `#11` - Issue number (if from issue)
- `Phase: X (N/M)` - Current phase and progress
- Progress bar - Visual completion
- Commands hint - Quick reference

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Status Check | `power-mode/coordinator.py` |
| Stop Signal | Redis pub/sub or file-based |
| State File | `~/.claude/power-mode-state.json` |
| Session Log | `~/.claude/power-mode-sessions/` |
| Status Line | `power-mode/statusline.py` |
