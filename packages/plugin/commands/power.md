---
description: "start | stop | status | init | metrics | widgets | consensus [--consensus, --agents N]"
argument-hint: "<subcommand> [options]"
---

# /popkit:power - Power Mode Management

Multi-agent orchestration for complex tasks requiring parallel collaboration.

## Architecture: Native Async (Claude Code 2.0.64+)

Zero setup - uses Claude Code background agents (no Docker/Redis).

**Tier Comparison:**

| Feature | Free | Premium (dollar 9/mo) | Pro (dollar 29/mo) |
|---------|------|-----------------|--------------|
| Mode | File-based | Native Async | Native Async |
| Max Agents | 2 | 5 | 10 |
| Parallel | Sequential | True parallel | True parallel |
| Sync Barriers | Basic | Phase-aware | Phase-aware |
| Redis Fallback | No | No | Optional |

Run /popkit:upgrade to unlock premium.

## Subcommands

| Subcommand | Description |
|------------|-------------|
| status | Check current status (default) |
| start | Start with objective |
| stop | Stop gracefully |
| init | Check mode availability / Setup Redis (Pro) |
| metrics | View session metrics |
| widgets | Manage status line widgets |
| consensus | Multi-agent decision-making |

---

## status (default)

Check current Power Mode status.

**Active Output:**
- Session ID, issue, started time
- Mode: Native Async, tier info
- Phase, progress percentage
- Active agents (running, pending)
- Insights, sync barriers completed

**Inactive Output:**
- Mode available (Native Async)
- Tier info (5 or 10 agents)
- Start commands
- No setup required

---

## start

Start Power Mode with objective.

Arguments: [objective] (required), --phases, --agents, --timeout, --consensus, --require-plans, --trust-agents

Prerequisites: Claude Code 2.0.64+ (Native Async), or /popkit:power init --redis (Pro)

Process: Detect mode → Parse objective → Spawn background agents → Coordinate via TaskOutput → Sync barriers

**Plan Mode (2.0.70+):** Agents present implementation plans for approval. Config-based (default), --require-plans (all), --trust-agents (none).

---

## stop

Stop Power Mode gracefully. Send stop → Wait for agents → Save state → Clean up. Outputs session summary and transcript location.

---

## metrics

View session metrics: Time (phase duration, task completion), Quality (first-pass success, review score, bugs), Coordination (insights, context reuses, sync wait), Resource (token efficiency, utilization, concurrent).

Flags: --session ID, --compare, --export, --history N

---

## init

Check mode availability or setup Redis (Pro).

Default: Shows native > redis > file selection, reports availability.

Redis (Pro): /popkit:power init --redis [start|stop|debug]

Statusline: /popkit:power init statusline (adds to .claude/settings.json)

---

## widgets

Manage status line widgets.

Available: popkit ([PK]), efficiency (~2.4k), power_mode (#45 3/7 40%), workflow (impl 70%), health (✓✓✓)

Commands: list, enable widget, disable widget, compact on/off, reset

Config: .claude/popkit/config.json (statusline.widgets, compact_mode)

---

## consensus

Multi-agent decision-making via democratic voting.

Protocol: Token Ring + 7-Phase State Machine (GATHERING → VOTING → COMMITTED/ABORTED)

Triggers: UserRequest, AgentRequest, Conflict, Threshold, Checkpoint, PhaseTransition

Rule Presets: default (67% quorum, 60% approval), quick (50/50), strict (80/75), critical (100/100)

Commands: status, enable, disable, rules [preset]

---

## Mode Selection

1. Native Async (Preferred): Claude Code 2.0.64+, Premium/Pro, 5-10 parallel
2. Redis (Legacy): Docker + Redis, Pro only, 6+ parallel
3. File-Based (Fallback): Nothing required, Free, 2 sequential

---

## Auto-Activation

Triggers: Label epic/power-mode (+80% auto), complex/multi-phase (+30%), PopKit Guidance checkbox (+90%), 5+ files (+10-30%)

Decision Priority: Explicit flags → PopKit Guidance → Labels → Content → Default sequential if <60%

Thresholds: 0-59% sequential, 60-79% suggest, 80-100% auto-enable

---

## Architecture

Native Async: power-mode/native_coordinator.py, mode_selector.py, config.json, insights.json
Redis (Pro): coordinator.py, docker-compose.yml, setup-redis.py
Shared: statusline.py, efficiency_tracker.py, widget config, metrics
Consensus: consensus/ (protocol, coordinator, triggers, monitor, agent_hook, config)

## Related

- /popkit:issue work #N -p - Work with Power Mode
- /popkit:issue list --power - List Power Mode candidates
- /popkit:stats - Efficiency metrics
- /popkit:routine morning - Includes Redis health check

## Examples

See examples/ for: power-mode-walkthrough.md, consensus-scenarios.md, widget-customization.md, metrics-analysis.md.
