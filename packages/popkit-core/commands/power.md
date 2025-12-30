---
description: "start | stop | status | init | metrics | widgets | consensus [--consensus, --agents N]"
argument-hint: "<subcommand> [options]"
---

# /popkit:power - Power Mode Management

Multi-agent orchestration for complex tasks requiring parallel collaboration.

## Architecture: Native Async (Claude Code 2.0.64+)

**Zero setup** - uses Claude Code's native background Task tool for true parallel execution.

### How Native Async Works

```
User Request → Main Agent (Coordinator)
                    ↓
      ┌─────────────┼─────────────┐
      ↓             ↓             ↓
   Agent 1       Agent 2       Agent 3
   (Task bg)     (Task bg)     (Task bg)
      ↓             ↓             ↓
   Share via .claude/popkit/insights.json
      ↓             ↓             ↓
   TaskOutput    TaskOutput    TaskOutput
      ↓             ↓             ↓
      └─────────────┼─────────────┘
                    ↓
           Aggregated Results
```

**Key Benefits:**
- **No external dependencies** (no Docker, no Redis)
- **True parallelism** (agents run simultaneously)
- **Cross-platform** (works on Windows/macOS/Linux)
- **Reliable** (no service dependencies)

**Communication:**
- Shared file: `.claude/popkit/insights.json`
- Polling: `TaskOutput(block: false)` every 500ms
- Sync barriers between phases

**Tier Comparison:**

**Deep Dive:** See `docs/POWER_MODE_ASYNC.md` for complete documentation.

## Subcommands

| Subcommand | Description |
|------------|-------------|
| status | Check current status (default) |
| start | Start with objective |
| stop | Stop gracefully |
| init | Check mode availability and configuration |
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

Prerequisites: Claude Code 2.0.64+ for Native Async mode (recommended)

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

Power Mode automatically selects the best available mode:

1. **Native Async (Primary)**: Claude Code 2.0.64+, 5+ parallel agents, zero setup
2. **Upstash Redis (Optional)**: 10+ parallel agents, requires env vars, advanced coordination
3. **File-Based (Fallback)**: 2-3 sequential agents, automatic fallback if Native Async unavailable

---

## Auto-Activation

Triggers: Label epic/power-mode (+80% auto), complex/multi-phase (+30%), PopKit Guidance checkbox (+90%), 5+ files (+10-30%)

Decision Priority: Explicit flags → PopKit Guidance → Labels → Content → Default sequential if <60%

Thresholds: 0-59% sequential, 60-79% suggest, 80-100% auto-enable

---

## Architecture

**Core Components:**
- `native_coordinator.py` - Native Async mode orchestration (primary)
- `mode_selector.py` - Automatic mode detection and selection
- `upstash_adapter.py` - Optional Upstash Redis integration
- `statusline.py` - Visual status indicators
- `efficiency_tracker.py` - Performance metrics
- `config.json` - Power Mode configuration
- `insights.json` - Agent coordination patterns

**No Docker dependencies.** All local coordination uses file system or Claude Code Task tool.

## Related

- /popkit:issue work #N -p - Work with Power Mode
- /popkit:issue list --power - List Power Mode candidates
- /popkit:stats - Efficiency metrics
- /popkit:routine morning - Includes Redis health check

## Examples

See examples/ for: power-mode-walkthrough.md, consensus-scenarios.md, widget-customization.md, metrics-analysis.md.
