---
description: "start | stop | status | init [redis|file] [--agents N]"
---

# /popkit:power - Power Mode Management

Manage multi-agent orchestration via Redis pub/sub for complex tasks requiring parallel agent collaboration.

## Usage

```
/popkit:power <subcommand> [options]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `status` | Check current Power Mode status (default) |
| `start` | Start Power Mode with objective |
| `stop` | Stop Power Mode gracefully |
| `init` | Initialize Redis infrastructure |

---

## Subcommand: status (default)

Check current Power Mode status.

```
/popkit:power
/popkit:power status
```

### Output When Active

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
  /popkit:issue work #11      Continue current issue
```

### Output When Inactive

```
[i] POWER MODE INACTIVE

No active Power Mode session.

To start Power Mode:
  /popkit:issue work #N -p     Work on issue with Power Mode
  /popkit:power start "task"   Start with custom objective
  /popkit:issue list --power   List issues recommending Power Mode

Redis Status: localhost:16379 [OK]
```

---

## Subcommand: start

Start Power Mode with an objective.

```
/popkit:power start "Build user authentication with tests"
/popkit:power start "Create REST API" --phases explore,design,implement,test
/popkit:power start "Refactor database layer" --agents reviewer,architect,tester
```

### Arguments

| Argument | Description |
|----------|-------------|
| `[objective]` | Task description (required) |
| `--phases` | Comma-separated phase names (default: explore,design,implement,test,review) |
| `--agents` | Comma-separated agent names to use |
| `--timeout` | Max runtime in minutes (default: 30) |

### Prerequisites

**Redis must be running:**
```bash
# Check Redis
/popkit:power init

# Start if needed
/popkit:power init start
```

### Process

1. **Check Prerequisites**: Verify Redis connection
2. **Parse Objective**: Extract description, success criteria, phases, boundaries
3. **Start Coordinator**: Enable power mode and start coordinator process
4. **Display Configuration**: Show phases, agents, boundaries
5. **Begin Orchestration**: Dispatch initial agents

### Output

```
POWER MODE ACTIVATED

Session: abc123
Objective: Build user authentication with tests

Phases:
1. explore   - Analyze codebase and requirements
2. design    - Plan implementation
3. implement - Build the feature
4. test      - Write and run tests
5. review    - Final review

Boundaries:
  Files: src/auth/**, tests/auth/**
  Protected: .env*, secrets/
  Human approval: deploy, push main

Check-ins: Every 5 tool calls
Timeout: 30 minutes

Redis: localhost:6379 [OK]
Channels: pop:broadcast, pop:insights, pop:heartbeat

Ready to orchestrate. Agents will check in periodically.
```

---

## Subcommand: stop

Stop Power Mode gracefully.

```
/popkit:power stop
```

### Process

1. Send stop signal to coordinator
2. Wait for active agents to complete current tool call
3. Save session state
4. Clean up Redis channels

### Output

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
  /popkit:issue work #11
```

---

## Subcommand: init

Initialize Redis infrastructure for Power Mode.

```
/popkit:power init              # Check status and setup if needed
/popkit:power init start        # Start Redis
/popkit:power init stop         # Stop Redis
/popkit:power init restart      # Restart Redis
/popkit:power init debug        # Start with Redis Commander (http://localhost:8081)
/popkit:power init test         # Test Redis connectivity
```

### Prerequisites

- Docker installed and running
- Docker Compose (V1 or V2)

If Docker is not installed:
- **macOS**: Install Docker Desktop from https://docs.docker.com/desktop/mac/install/
- **Windows**: Install Docker Desktop from https://docs.docker.com/desktop/windows/install/
- **Linux**: Install Docker Engine from https://docs.docker.com/engine/install/

### Init Subcommands

#### Default (status + auto-start)

```
/popkit:power init

Checking Docker availability...
Docker is installed and running
Starting Redis container...
Redis container started
Waiting for Redis to be healthy...
Redis is running and accessible

Ready for Power Mode!

Next steps:
1. Run /popkit:power start "objective" to activate
2. Run /popkit:power init debug to open Redis Commander
```

#### start

```bash
cd power-mode/
python setup-redis.py start
```

Pulls Redis 7 Alpine image, creates container, exposes port 6379, creates persistent volume.

#### stop

```bash
cd power-mode/
python setup-redis.py stop
```

Gracefully stops Redis container (data persists in volume).

#### debug

```
/popkit:power init debug

Starting Redis Commander at http://localhost:8081

Inspect:
- Active pub/sub subscriptions
- Agent heartbeats
- Message queues
- Insight pool
```

#### test

```
/popkit:power init test
```

Verifies Redis connectivity, pub/sub functionality, and all Power Mode channels.

### Redis Channels

| Channel | Purpose |
|---------|---------|
| pop:broadcast | Messages to all agents |
| pop:heartbeat | Agent health checks |
| pop:results | Task completion results |
| pop:insights | Shared discoveries between agents |
| pop:coordinator | Coordinator commands |
| pop:human | Requests for human decisions |

---

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

---

## Examples

```bash
# Check Power Mode status
/popkit:power
/popkit:power status

# Initialize Redis
/popkit:power init
/popkit:power init start

# Start with custom objective
/popkit:power start "Add dark mode toggle"

# Custom objective with specific phases
/popkit:power start "Optimize database queries" --phases analyze,implement,test

# Custom objective with specific agents
/popkit:power start "Security audit" --agents security-auditor

# Stop Power Mode
/popkit:power stop

# Debug Redis
/popkit:power init debug
```

---

## File-Based Fallback

Power Mode works without Redis using file-based coordination:
- Uses shared JSON file for coordination
- Good for 2-3 agents, development, learning
- Auto-activates when Redis unavailable
- Zero setup required

---

## Skill Reference

This command activates the `pop-power-mode` skill. For detailed documentation see: `skills/pop-power-mode/SKILL.md`

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| **Coordinator** | `power-mode/coordinator.py` |
| **Auto-Coordinator** | `power-mode/coordinator_auto.py` |
| **File Fallback** | `power-mode/file_fallback.py` |
| **Check-In Hook** | `power-mode/checkin-hook.py` |
| **Status Line** | `power-mode/statusline.py` |
| **Config** | `power-mode/config.json` |
| **Docker Setup** | `power-mode/docker-compose.yml` |
| **Setup Script** | `power-mode/setup-redis.py` |
| **State File** | `~/.claude/power-mode-state.json` |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:issue work #N -p` | Work on issue with Power Mode |
| `/popkit:issue list --power` | List issues recommending Power Mode |
| `/popkit:morning` | Includes Redis health check |
