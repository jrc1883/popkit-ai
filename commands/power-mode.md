---
description: Activate Pop Power Mode for multi-agent Redis pub/sub orchestration
---

# /popkit:power-mode - Multi-Agent Orchestration

Activate Power Mode for complex tasks requiring parallel agent collaboration via Redis pub/sub.

## Usage

```
/popkit:power-mode "Build user authentication with tests"
/popkit:power-mode --phases explore,design,implement,test "Create REST API"
/popkit:power-mode --agents reviewer,architect,tester "Refactor database layer"
/popkit:power-mode status        # Check current status
/popkit:power-mode stop          # Deactivate power mode
```

## Arguments

| Argument | Description |
|----------|-------------|
| `[objective]` | The task description (required for start) |
| `--phases` | Comma-separated phase names (default: explore,design,implement,test,review) |
| `--agents` | Comma-separated agent names to use |
| `--timeout` | Max runtime in minutes (default: 30) |
| `status` | Show current power mode status |
| `stop` | Deactivate power mode |

## Prerequisites

**Redis must be running:**
```bash
# Docker
docker run -d -p 6379:6379 redis:alpine

# Or native
redis-server

# Verify
redis-cli ping  # Should return PONG
```

## Process

### Step 1: Check Prerequisites

```bash
# Check Redis connection
redis-cli ping
```

If Redis unavailable, show instructions and exit.

### Step 2: Parse Objective

Extract from user input:
- **Description**: Main task description
- **Success criteria**: Infer from description (or ask user)
- **Phases**: From `--phases` or default
- **Boundaries**: Infer file patterns from description

### Step 3: Start Coordinator

```bash
# Enable power mode
touch ~/.claude/power-mode-enabled

# Start coordinator process (background)
python power-mode/coordinator.py start \
  --objective "Build user authentication" \
  --phases explore design implement test review \
  --success-criteria "Login works" "Tests pass"
```

### Step 4: Display Configuration

Show user what was configured:

```
┌─────────────────────────────────────────────────────────────┐
│ ⚡ POP POWER MODE ACTIVATED                                  │
├─────────────────────────────────────────────────────────────┤
│ Session: abc123                                              │
│ Objective: Build user authentication with tests              │
├─────────────────────────────────────────────────────────────┤
│ Phases:                                                      │
│ 1. explore   - Analyze codebase and requirements            │
│ 2. design    - Plan implementation                          │
│ 3. implement - Build the feature                            │
│ 4. test      - Write and run tests                          │
│ 5. review    - Final review                                 │
├─────────────────────────────────────────────────────────────┤
│ Boundaries:                                                  │
│ • Files: src/auth/**, tests/auth/**                         │
│ • Protected: .env*, secrets/                                │
│ • Human approval: deploy, push main                         │
├─────────────────────────────────────────────────────────────┤
│ Check-ins: Every 5 tool calls                               │
│ Timeout: 30 minutes                                          │
├─────────────────────────────────────────────────────────────┤
│ Redis: localhost:6379 ✓                                      │
│ Channels: pop:broadcast, pop:insights, pop:heartbeat        │
└─────────────────────────────────────────────────────────────┘

Ready to orchestrate. Agents will check in periodically.
Use /popkit:power-mode status to monitor progress.
```

### Step 5: Begin Orchestration

Dispatch initial agents based on Phase 1:

```
Starting Phase 1: EXPLORE

Dispatching agents:
• code-explorer → Analyze codebase structure
• researcher → Research authentication patterns
• architect → Review existing architecture

Agents will check in every 5 tool calls.
Insights will be shared via Redis.
```

## Status Command

```
/popkit:power-mode status
```

Shows current orchestration status:

```
┌─────────────────────────────────────────────────────────────┐
│ ⚡ POWER MODE STATUS                                         │
├─────────────────────────────────────────────────────────────┤
│ Session: abc123 | Runtime: 5m 32s                           │
│ Phase: implement (3/5) | Progress: 45%                      │
├─────────────────────────────────────────────────────────────┤
│ Active Agents:                                               │
│ • rapid-prototyper  [████████░░] 80%  - Implementing login  │
│ • test-writer       [████░░░░░░] 40%  - Writing auth tests  │
│ • docs-maintainer   [██░░░░░░░░] 20%  - Updating API docs   │
├─────────────────────────────────────────────────────────────┤
│ Recent Check-ins:                                            │
│ 10:05:32 rapid-prototyper: "Created login endpoint"         │
│ 10:04:18 test-writer: "Found existing test patterns"        │
│ 10:03:45 docs-maintainer: "Using OpenAPI format"            │
├─────────────────────────────────────────────────────────────┤
│ Insights Shared: 8 | Patterns Learned: 3                    │
│ Sync Barriers: 2 completed | Human Pending: 0               │
└─────────────────────────────────────────────────────────────┘
```

## Stop Command

```
/popkit:power-mode stop
```

Gracefully stops power mode:

```
⚡ Stopping Power Mode...

• Sending stop signal to coordinator
• Waiting for active agents to complete current tool call
• Saving session state
• Cleaning up Redis channels

Power Mode deactivated.

Summary:
• Session: abc123
• Runtime: 12m 45s
• Phases completed: 3/5
• Insights shared: 15
• Patterns learned: 7

Session transcript saved to: ~/.claude/power-mode-sessions/abc123.json
```

## Examples

**Basic usage:**
```
/popkit:power-mode "Add dark mode toggle to settings"

⚡ POP POWER MODE ACTIVATED
Objective: Add dark mode toggle to settings
Phases: explore → design → implement → test → review

Starting Phase 1: EXPLORE
Dispatching code-explorer to analyze UI patterns...
```

**With custom phases:**
```
/popkit:power-mode --phases research,design,build "Create GraphQL API"

⚡ POP POWER MODE ACTIVATED
Objective: Create GraphQL API
Phases: research → design → build

Starting Phase 1: RESEARCH
Dispatching researcher and architect...
```

**Check status:**
```
/popkit:power-mode status

Phase: design (2/3) | 3 agents active | 12 insights shared
```

**Stop orchestration:**
```
/popkit:power-mode stop

Power Mode stopped. Session saved.
```

## Skill Reference

This command activates the `pop-power-mode` skill. For detailed documentation on:
- Check-in protocol
- Redis channels
- Guardrails
- Troubleshooting

See: `skills/pop-power-mode/SKILL.md`

## Output Style

Uses `output-styles/power-mode-checkin.md` for agent check-in formatting.

## Related Commands

- `/popkit:power-mode-status` - Alias for status
- `/popkit:power-mode-stop` - Alias for stop
