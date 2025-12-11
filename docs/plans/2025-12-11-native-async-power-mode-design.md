# Native Async Power Mode Architecture Design

**Date:** December 11, 2025
**Issue:** #180
**Author:** Claude Code Analysis
**Status:** Design Phase

---

## Executive Summary

Redesign PopKit's Power Mode to leverage Claude Code 2.0.64+'s native async agent capabilities, eliminating the Redis dependency while maintaining full multi-agent orchestration power.

**Key Insight:** Claude Code now provides native background agents with async messaging (`run_in_background: true` + `TaskOutput`), making external orchestration infrastructure unnecessary.

---

## Current Architecture (Redis-Based)

```
┌─────────────────────────────────────────────────────────────────┐
│                     REDIS-BASED POWER MODE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │   Agent 1   │     │   Agent 2   │     │   Agent 3   │      │
│   │ (subagent)  │     │ (subagent)  │     │ (subagent)  │      │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘      │
│          │                   │                   │              │
│          └───────────────────┼───────────────────┘              │
│                              │                                  │
│                    ┌─────────▼─────────┐                       │
│                    │  Redis Pub/Sub    │                       │
│                    │  (Docker: 16379)  │                       │
│                    └─────────┬─────────┘                       │
│                              │                                  │
│                    ┌─────────▼─────────┐                       │
│                    │   coordinator.py  │                       │
│                    │  (Python process) │                       │
│                    └───────────────────┘                       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ Requirements:                                                    │
│ • Docker installed and running                                  │
│ • Redis container (popkit-redis) active                         │
│ • Python redis package                                          │
│ • coordinator.py background process                             │
│                                                                  │
│ Limitations:                                                     │
│ • High barrier to entry (Docker knowledge required)             │
│ • External dependency failures                                  │
│ • Port conflicts possible                                       │
│ • No Windows Docker Desktop = no Power Mode                     │
└─────────────────────────────────────────────────────────────────┘
```

### Current Flow

1. User runs `/popkit:power start "Build auth system"`
2. `coordinator.py` starts Redis container
3. Coordinator spawns subagents via Task tool
4. Agents check in via Redis pub/sub channels
5. Insights shared via `pop:insights` channel
6. Sync barriers wait for Redis acknowledgments
7. Results aggregated and returned to main agent

### Pain Points

- **Setup friction**: Users must install Docker, run containers
- **Platform issues**: Docker Desktop licensing, WSL2 complexity
- **Network dependency**: Redis latency, connection failures
- **Resource overhead**: Docker containers, Redis memory
- **Debugging difficulty**: External process logs, pub/sub visibility

---

## Proposed Architecture (Native Async)

```
┌─────────────────────────────────────────────────────────────────┐
│                   NATIVE ASYNC POWER MODE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                CLAUDE CODE RUNTIME                       │   │
│   │                                                          │   │
│   │  ┌───────────┐  ┌───────────┐  ┌───────────┐           │   │
│   │  │  Agent 1  │  │  Agent 2  │  │  Agent 3  │           │   │
│   │  │background │  │background │  │background │           │   │
│   │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘           │   │
│   │        │              │              │                  │   │
│   │        └──────────────┼──────────────┘                  │   │
│   │                       │                                 │   │
│   │               ┌───────▼───────┐                        │   │
│   │               │  TaskOutput   │                        │   │
│   │               │ (native API)  │                        │   │
│   │               └───────┬───────┘                        │   │
│   │                       │                                 │   │
│   │               ┌───────▼───────┐                        │   │
│   │               │ Main Agent    │                        │   │
│   │               │ (coordinator) │                        │   │
│   │               └───────────────┘                        │   │
│   │                                                          │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ Requirements:                                                    │
│ • Claude Code 2.0.64+ (no external deps)                        │
│                                                                  │
│ Benefits:                                                        │
│ • Zero setup, works out of box                                  │
│ • Native error handling                                         │
│ • Built-in concurrency limits                                   │
│ • Integrated with Claude Code UI                                │
└─────────────────────────────────────────────────────────────────┘
```

### Native Async Flow

1. User runs `/popkit:power start "Build auth system"`
2. Main agent parses objective, identifies phases and agents
3. Main agent spawns background agents via `Task(run_in_background: true)`
4. Each agent receives its task and works independently
5. Main agent polls `TaskOutput(block: false)` for progress
6. Agents complete → main agent aggregates results
7. Phase transition → spawn next batch of agents

---

## Key Design Decisions

### 1. Coordinator Model: Main Agent vs External Process

**Decision: Main Agent as Coordinator**

The main Claude Code agent acts as the coordinator, eliminating the separate Python process.

| Aspect | External Coordinator | Main Agent Coordinator |
|--------|---------------------|----------------------|
| Setup | Requires background process | None needed |
| Communication | Redis pub/sub | Native TaskOutput |
| Reliability | Process can crash | Claude Code managed |
| Debugging | External logs | Integrated output |
| State | External Redis | In-context |

**Trade-off:** Main agent uses context tokens for coordination overhead (~1-2k tokens per orchestration cycle).

### 2. Inter-Agent Communication: File vs Memory

**Decision: Hybrid Approach**

- **Progress Updates**: Via TaskOutput polling (in-memory)
- **Shared Insights**: Via JSON file (`.claude/popkit/insights.json`)
- **Final Results**: Via TaskOutput blocking call

This preserves the insight-sharing pattern while using native async for control flow.

### 3. Concurrency Model: Parallel vs Sequential Phases

**Decision: Parallel Within Phase, Sequential Across Phases**

```
Phase 1: explore
├── Agent A (background) ─┐
├── Agent B (background) ─┼─► Sync barrier
└── Agent C (background) ─┘
                          │
Phase 2: implement        ▼
├── Agent D (background) ─┐
└── Agent E (background) ─┴─► Sync barrier
                          │
Phase 3: review           ▼
└── Agent F (background) ──► Complete
```

**Rationale:** Phase ordering matters (can't implement before exploring), but within a phase, agents can work in parallel.

### 4. Fallback Strategy

**Decision: Graceful Degradation**

```
try:
  Native Async Mode (Claude Code 2.0.64+)
    └── 3-6 background agents, native TaskOutput
except:
  File-Based Mode (fallback)
    └── 2 sequential agents, JSON file coordination
```

Redis mode preserved for Pro/Team tier (high-volume scenarios).

---

## Implementation Architecture

### New File Structure

```
packages/plugin/power-mode/
├── coordinator.py           # Legacy Redis coordinator (keep for Pro tier)
├── native_coordinator.py    # NEW: Native async coordinator
├── config.json              # Configuration (add native mode settings)
├── protocol.py              # Shared message types (reuse)
├── stream_manager.py        # Streaming support (reuse)
├── file_coordinator.py      # Existing file-based fallback
└── mode_selector.py         # NEW: Auto-select best mode
```

### Native Coordinator Interface

```python
# native_coordinator.py

class NativeAsyncCoordinator:
    """
    Orchestrates multi-agent collaboration using Claude Code's
    native background agent support (2.0.64+).
    """

    def __init__(self, objective: str, config: Dict):
        self.objective = objective
        self.config = config
        self.agents: Dict[str, AgentStatus] = {}
        self.insights_file = Path(".claude/popkit/insights.json")
        self.phase = 0
        self.phases = []

    async def start(self) -> Dict:
        """
        Main orchestration loop.
        Returns final aggregated results.
        """
        # 1. Parse objective into phases
        self.phases = self._decompose_objective()

        # 2. Execute each phase
        for phase in self.phases:
            results = await self._execute_phase(phase)
            self._aggregate_phase_results(results)

        # 3. Return combined results
        return self._finalize()

    async def _execute_phase(self, phase: Phase) -> List[AgentResult]:
        """Execute a single phase with parallel agents."""
        # Spawn agents in background
        agent_ids = []
        for agent_config in phase.agents:
            agent_id = await self._spawn_background_agent(agent_config)
            agent_ids.append(agent_id)

        # Wait for all agents to complete (sync barrier)
        results = await self._wait_for_agents(agent_ids)
        return results

    async def _spawn_background_agent(self, config: AgentConfig) -> str:
        """
        Spawn a background agent using Task tool.

        Returns agent_id for later TaskOutput polling.
        """
        # This is pseudo-code for the Task tool invocation
        # In practice, the main agent does this via tool calls
        pass

    async def _wait_for_agents(self, agent_ids: List[str]) -> List[AgentResult]:
        """
        Wait for all background agents to complete.
        Uses TaskOutput with block=true.
        """
        results = []
        for agent_id in agent_ids:
            result = await self._get_agent_output(agent_id, block=True)
            results.append(result)
        return results
```

### Mode Selection Logic

```python
# mode_selector.py

def select_power_mode() -> str:
    """
    Auto-select the best Power Mode based on environment.

    Returns: "native" | "redis" | "file"
    """
    # 1. Check Claude Code version
    if claude_code_version() >= "2.0.64":
        # Native async available
        if is_premium_user():
            return "native"  # Premium gets native async
        else:
            return "file"    # Free tier gets file-based

    # 2. Fallback to Redis if configured
    if redis_available():
        return "redis"

    # 3. Final fallback to file-based
    return "file"
```

### Configuration Updates

```json
// config.json additions
{
  "native": {
    "enabled": true,
    "min_claude_code_version": "2.0.64",
    "max_parallel_agents": 5,
    "poll_interval_ms": 500,
    "sync_timeout_seconds": 120,
    "use_insights_file": true
  },

  "mode_priority": ["native", "redis", "file"],

  "tier_limits": {
    "free": {
      "mode": "file",
      "max_agents": 2
    },
    "premium": {
      "mode": "native",
      "max_agents": 5
    },
    "pro": {
      "mode": "native",
      "max_agents": 10,
      "redis_fallback": true
    }
  }
}
```

---

## Command Updates

### `/popkit:power start`

**Before:**
```bash
# Required Docker + Redis
/popkit:power start "Build auth system"
# → Error if Redis not running
```

**After:**
```bash
# Just works (native async)
/popkit:power start "Build auth system"
# → Auto-detects best mode, starts orchestration
```

### `/popkit:power status`

**Before:**
```
Power Mode: Redis
Redis: Connected (localhost:16379)
Agents: 3 active
```

**After:**
```
Power Mode: Native Async
Claude Code: 2.0.64 ✓
Agents: 3 background (2 running, 1 pending)
Insights: 5 shared
Phase: 2/4 (implement)
```

### `/popkit:power init`

**Before:**
```bash
# Required to set up Docker/Redis
/popkit:power init
```

**After:**
```bash
# Optional - only for Redis mode
/popkit:power init
# → "Native Async mode enabled. No setup required!"
# → "Run /popkit:power init --redis for Redis mode (optional)"
```

---

## Migration Strategy

### Phase 1: Add Native Coordinator (Non-Breaking)

1. Create `native_coordinator.py`
2. Add mode selection logic
3. Update config.json with native settings
4. Keep Redis mode as default initially

**Timeline:** 1-2 days

### Phase 2: Test and Validate

1. Test with 3 agents in parallel
2. Verify sync barriers work
3. Test insight sharing via file
4. Compare performance to Redis mode

**Timeline:** 1 day

### Phase 3: Switch Default

1. Make native mode default for Premium users
2. Update documentation
3. Deprecate Redis requirement (keep as option)

**Timeline:** 1 day

### Phase 4: Clean Up (Post-Launch)

1. Move Redis coordinator to `legacy/` or separate package
2. Update all references
3. Simplify Power Mode skill documentation

**Timeline:** Future

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| TaskOutput API changes | Low | High | Pin to Claude Code version |
| Concurrency limits | Medium | Medium | Tier-based limits, graceful degradation |
| Context window overflow | Medium | Medium | Efficient prompt templates |
| File coordination race conditions | Low | Low | File locking, atomic writes |
| Performance regression | Low | Medium | Benchmarking before release |

---

## Success Criteria

1. **Zero-config startup**: `/popkit:power start` works without Docker/Redis
2. **Equivalent functionality**: 3+ agents coordinate, insights shared, sync barriers work
3. **Performance parity**: No significant latency increase vs Redis mode
4. **Graceful degradation**: Falls back to file mode if native fails
5. **Documentation updated**: All Power Mode docs reflect native mode

---

## Acceptance Checklist

- [ ] `native_coordinator.py` implemented and tested
- [ ] Mode selection logic working
- [ ] 3+ agents coordinate successfully
- [ ] Insights shared via file work
- [ ] Sync barriers function correctly
- [ ] `/popkit:power` command updated
- [ ] `pop-power-mode` skill updated
- [ ] CLAUDE.md Power Mode section updated
- [ ] Benchmark: Native vs Redis latency comparison
- [ ] Free tier falls back to file mode

---

## References

- Issue #180: Native Async Power Mode
- Research: `docs/research/claude-code-2.0.60-integration.md`
- Current Implementation: `packages/plugin/power-mode/coordinator.py`
- Claude Code Changelog: Background agents (v2.0.60, v2.0.64)

---

**Next Steps:**
1. Review and approve this design
2. Create implementation branch
3. Build `native_coordinator.py`
4. Test with real workloads
5. Update documentation
