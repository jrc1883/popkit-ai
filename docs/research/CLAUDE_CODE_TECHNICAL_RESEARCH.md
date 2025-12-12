# Claude Code v2.0.65+ Technical Integration Research

**Date:** December 11, 2025
**Status:** In-Depth Technical Analysis
**Audience:** PopKit Architecture Team

---

## Table of Contents

1. **Technical Architecture Overview**
2. **How PopKit Currently Works** (Foundation)
3. **Context Window Integration** (Technical Deep-Dive)
4. **Model Switching** (Technical Deep-Dive)
5. **Status Line Enhancement** (Technical Deep-Dive)
6. **Elegant Implementation Patterns** (The "How")
7. **Hook-Based Automation Strategy**
8. **Integration Points & Non-Breaking Changes**
9. **Recommended Architecture Decisions**

---

## Part 1: Technical Architecture Overview

### 1.1 PopKit's Current Three-Layer Architecture

PopKit uses a elegant three-layer pattern that's already proven:

```
┌──────────────────────────────────────────────────┐
│ Layer 3: Commands & Skills (User-Facing)         │
│ /popkit:dev, /popkit:power, /popkit:stats        │
└────────────────────┬─────────────────────────────┘
                     │ Invoke
┌────────────────────▼─────────────────────────────┐
│ Layer 2: Stateless Hook Chain (Orchestration)    │
│ PreToolUse → Validators → PostToolUse            │
└────────────────────┬─────────────────────────────┘
                     │ Triggered by
┌────────────────────▼─────────────────────────────┐
│ Layer 1: Utilities & State Management (Core)     │
│ context_carrier, message_builder, trackers       │
└──────────────────────────────────────────────────┘
```

**Key Principle:** All state is explicit, immutable, and passed through the chain. No hidden global state.

### 1.2 Hook Execution Flow (Current)

```json
Claude Code executes tool
    ↓
Pre-Tool-Use Hook Chain (hooks.json)
    ├→ pre-tool-use.py (safety, routing)
    ├→ agent-orchestrator.py (agent selection)
    └→ chain-validator.py (validation)
    ↓
Claude Code runs tool (Read, Bash, etc.)
    ↓
Post-Tool-Use Hook Chain (hooks.json)
    ├→ post-tool-use.py (tracking, analysis)
    ├→ agent-observability.py (metrics)
    ├→ context-monitor.py (token tracking) ← ALREADY EXISTS
    ├→ quality-gate.py (code quality)
    └→ doc-sync.py (documentation)
```

**Important:** Hooks receive JSON input via stdin, return JSON via stdout. No side effects allowed—pure functions.

### 1.3 Existing State Management Patterns

PopKit already has three state persistence patterns:

| Pattern | Location | Use Case | Status |
|---------|----------|----------|--------|
| **Session-based** | `.claude/session-tokens.json` | Per-session token tracking | ✓ Working |
| **Project-local** | `.claude/popkit/config.json` | User preferences | ✓ Working |
| **Global** | `~/.claude/popkit/` | Cross-project data | ✓ Working |

**Key:** All paths check project-local first, then fall back to global. This enables per-project customization.

---

## Part 2: How PopKit Currently Works (Foundation)

### 2.1 The Stateless Hook Pattern (Your Secret Weapon)

This is PopKit's most elegant pattern. Every hook follows this:

```python
# Input: Immutable context from stdin (JSON)
# Process: Pure function, no side effects
# Output: Updated context + action (JSON)

class HookImplementation(StatelessHook):
    def process(self, ctx: HookContext) -> HookContext:
        # Read immutable context
        tool_name = ctx.tool_name
        session_id = ctx.session_id

        # Do processing (pure function)
        result = analyze(ctx)

        # Return updated context (never mutate original)
        return self.update_context(ctx, tool_result=result)
```

**Why This Matters:** You can chain unlimited hooks without state corruption. Each hook is testable in isolation.

**Current Usage:**
- `context-monitor.py`: Reads `session-tokens.json`, updates token counts
- `efficiency_tracker.py`: Reads efficiency metrics, updates with new events
- `pre-tool-use.py`: Reads agent config, returns routing decision

### 2.2 Message Composition Pattern

PopKit uses pure functions to build conversation context:

```python
# Pure functions—no state modifications
build_user_message(text)          # → {"role": "user", "content": text}
build_tool_use_message(...)       # → {"role": "assistant", "content": [tool_use]}
build_tool_result_message(...)    # → {"role": "user", "content": [tool_result]}
merge_tool_uses([...])            # → Single message with multiple tools
compose_conversation([...])       # → Validated message array
```

**Why This Matters:** You can reconstruct conversations deterministically from history dicts. Enables logging, replay, debugging.

### 2.3 Hook Chain Execution (Already Working)

`hooks.json` defines matchers and hook sequences:

```json
{
  "PostToolUse": [
    {
      "matcher": "Bash|Read|Write|Edit|...",
      "hooks": [
        {
          "type": "command",
          "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/post-tool-use.py\"",
          "timeout": 5000
        },
        {
          "type": "command",
          "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/context-monitor.py\"",
          "timeout": 3000
        }
      ]
    }
  ]
}
```

**Key Pattern:** Each hook runs sequentially. Each has explicit timeout. Matcher controls which tools trigger it.

---

## Part 3: Context Window Integration (Technical Deep-Dive)

### 3.1 Current State: What PopKit Has

**Already Implemented:**
- `context-monitor.py` hook: Tracks input/output tokens from Claude Code
- `efficiency_tracker.py`: Calculates token savings
- `statusline.py`: Already has infrastructure for widgets
- `hooks.json`: Context monitor already hooked into PostToolUse

**Gap:** Context monitor only tracks single-session tokens. Doesn't aggregate across parallel agents in Power Mode.

### 3.2 The Problem We're Solving

**Scenario 1: Single-Session Context**
```
User: "Refactor this code"
│
├→ Tool: Read (5K tokens input)
├→ Tool: Bash (2K tokens input)
└→ Tool: Edit (3K tokens input)
    Total: 10K tokens consumed ✓ Works (context-monitor.py tracks this)
```

**Scenario 2: Multi-Agent Power Mode (The Gap)**
```
User: "Build feature #45"
│
├→ [Parallel] code-explorer: Read files, search (15K tokens)
├→ [Parallel] code-architect: Analyze patterns (20K tokens)
├→ [Parallel] code-reviewer: Examine existing code (18K tokens)
└→ [Parallel] security-auditor: Security scan (12K tokens)
    Total: 65K tokens consumed ✗ No unified tracking
```

**Why This Matters:**
- Each agent gets its own context window
- Claude Code doesn't know about the collective usage
- User might run out of context without warning
- Power Mode has no visibility into cost allocation

### 3.3 Technical Architecture: Elegant Context Aggregation

**Option A: Hook-Based Aggregation (Recommended)**

```
┌──────────────────────────────────────────────────────┐
│ Each Agent (in parallel)                             │
│  ├→ PreToolUse Hook: Record starting model/context   │
│  ├→ Run Claude Code tool                             │
│  └→ PostToolUse Hook: Record token usage             │
└──────────────┬───────────────────────────────────────┘
               │
               ↓ Each hook writes to Redis (atomic)
        ┌──────────────────────────────┐
        │ Redis Key: powermode:context  │
        │ {                             │
        │   "code-explorer": {...},     │
        │   "code-architect": {...},    │
        │   "timestamp": "2025-12-11..."│
        │ }                             │
        └──────────┬───────────────────┘
                   │
                   ↓ Coordinator polls
        ┌──────────────────────────────┐
        │ Power Mode Coordinator       │
        │ Aggregates context usage     │
        │ Checks thresholds            │
        │ Updates status line          │
        └──────────────────────────────┘
```

**Implementation Steps:**

1. **Extend ContextMonitor class** (context-monitor.py):
```python
class ContextMonitor:
    # NEW: Redis support
    def __init__(self):
        self.redis_available = try_import_redis()
        self.coordinator_id = os.environ.get('POPKIT_COORDINATOR_ID')

    # NEW: Report to coordinator
    def report_to_coordinator(self, usage_data):
        if self.redis_available and self.coordinator_id:
            # Atomically update Redis key
            redis.hset(
                f"powermode:{self.coordinator_id}:agents",
                self.coordinator_id,
                json.dumps(usage_data)
            )
```

2. **Update PreToolUse Hook** to set `POPKIT_COORDINATOR_ID`:
```python
def pre_tool_use_hook(input_data):
    # NEW: If in Power Mode, get coordinator ID
    coordinator_id = get_power_mode_coordinator_id()

    # Set environment for downstream hooks
    os.environ['POPKIT_COORDINATOR_ID'] = coordinator_id

    return ctx
```

3. **Power Mode Coordinator** aggregates:
```python
class PowerModeCoordinator:
    def aggregate_context_usage(self) -> Dict:
        """Get total context from all agents."""
        agent_usage = redis.hgetall(f"powermode:{self.session_id}:agents")

        total = 0
        breakdown = {}
        for agent_id, usage_json in agent_usage.items():
            usage = json.loads(usage_json)
            total += usage['input_tokens']
            breakdown[agent_id] = usage

        return {
            "total_tokens": total,
            "breakdown": breakdown,
            "percent": (total / self.context_limit) * 100
        }
```

**Why This Is Elegant:**
- ✓ Hooks remain pure functions (no direct Redis writes in hooks)
- ✓ Coordinator is single source of truth
- ✓ Fallback to file-based if Redis unavailable
- ✓ No breaking changes to existing hooks

### 3.4 Context Window Display Strategy

**Status Line Integration:**

Current PopKit status line:
```
[PK] Power: #45 3/7 40% | ~2.4k saved | Agents: code-explorer+2
```

Enhanced with context:
```
[PK] Power: #45 3/7 40% | Context: 65K/200K (33%) | ~2.4k saved | Agents: code-explorer+2
```

**Implementation:**

1. Add `widget_context()` to `statusline.py`:
```python
def widget_context(compact: bool = True) -> str:
    """Context window usage widget."""
    # Get aggregated context from coordinator
    context_data = load_aggregated_context()

    if not context_data:
        return ""

    percent = int(context_data['percent'])
    used = context_data['total_tokens'] // 1000
    limit = context_data['limit'] // 1000

    # Color changes at thresholds
    if percent >= 90:
        color = Colors.RED
        icon = "🔴"
    elif percent >= 70:
        color = Colors.YELLOW
        icon = "🟡"
    else:
        color = Colors.GREEN
        icon = "🟢"

    if compact:
        return f"{icon} {color}{used}K{Colors.RESET}"

    return f"Context: {color}{used}K/{limit}K ({percent}%){Colors.RESET}"
```

2. Add to config:
```json
{
  "statusline": {
    "widgets": ["popkit", "power_mode", "context", "efficiency"],
    "compact_mode": true
  }
}
```

### 3.5 Context Threshold Strategy (Automatic Warnings)

**Hook-Based Implementation:**

In `post-tool-use.py`:
```python
def check_context_threshold(coordinator_id: str) -> Optional[Decision]:
    """Check if context usage triggers warning."""
    aggregated = coordinator.aggregate_context_usage()
    percent = aggregated['percent']

    # Threshold: 70% warning, 85% critical, 95% danger
    if percent >= 95:
        # Block new agents from starting
        return Decision(action="block", reason="context_critical")

    elif percent >= 85:
        # Warn and ask user
        return Decision(
            action="approve_with_prompt",
            prompt=f"⚠️ Context at {percent}%. Continue?",
            options=["Continue", "/popkit:session checkpoint"]
        )

    elif percent >= 70:
        # Silent notification to status line
        update_status("Context 70%—consider checkpoint")

    return Decision(action="approve")
```

---

## Part 4: Model Switching (Technical Deep-Dive)

### 4.1 The Challenge with Model Switching

**Claude Code's Hotkey Behavior:**
- User presses Alt+P (or Option+P on Mac)
- Claude Code displays model selector
- User picks a model
- Conversation continues with that model
- **Gap:** PopKit has no programmatic way to trigger this

**Current Model Fields in PopKit:**
```yaml
# Agent definition (agents/tier-1-always-active/code-reviewer/AGENT.md)
model: inherit  # ← Can be "inherit", "claude-opus-4", "claude-sonnet-4", etc.
```

### 4.2 Elegant Architecture: Model Selection Without Hotkey Mashing

**The Insight:** Don't make hooks trigger hotkeys. Instead, inform the user's model decision automatically.

**Three-Tier Strategy:**

#### Tier 1: Agent-Defined Model Preferences

```yaml
# In agent definitions
---
name: bug-whisperer
model: claude-opus-4  # Deep reasoning for tricky bugs
tools: Read, Bash, Grep, Edit

---
name: test-writer-fixer
model: claude-haiku-4  # Fast pattern recognition
tools: Read, Write, Edit

---
name: code-reviewer
model: claude-opus-4-extended-thinking  # Complex analysis
tools: Read, Grep, Edit
```

#### Tier 2: Hook-Based Model Awareness

In `pre-tool-use.py`:
```python
def get_agent_model_preference(agent_name: str) -> Optional[str]:
    """Get model preference for an agent."""
    agent_def = load_agent_definition(agent_name)

    model = agent_def.get('model', 'inherit')

    if model != 'inherit':
        # Agent has explicit preference
        return model

    # Fall back to current model
    return os.environ.get('CLAUDE_CODE_MODEL', 'claude-sonnet-4')

def handle_agent_activation(agent_name: str) -> HookContext:
    """When an agent is being activated, suggest its preferred model."""
    preferred_model = get_agent_model_preference(agent_name)
    current_model = os.environ.get('CLAUDE_CODE_MODEL')

    if preferred_model and preferred_model != current_model:
        # Log suggestion to status line or stderr
        log_model_preference(agent_name, preferred_model, current_model)

        # Optional: Update environment for hooks to see preference
        os.environ['SUGGESTED_MODEL'] = preferred_model

    return ctx
```

#### Tier 3: Status Line Indicator

```python
def widget_model_suggestion(compact: bool = True) -> str:
    """Show current + suggested model."""
    current = os.environ.get('CLAUDE_CODE_MODEL', '?')
    suggested = os.environ.get('SUGGESTED_MODEL')

    if not suggested or suggested == current:
        return f"Model: {current}"

    if compact:
        return f"Model: {current} → {suggested}"

    return f"Model: {current} (suggested: {suggested}, press Alt+P to switch)"
```

### 4.3 Power Mode Model Orchestration Architecture

**For Multi-Agent Scenarios:**

```
Power Mode Coordinator activates agents sequentially:

Phase 1: code-explorer (Haiku — fast analysis)
├→ PreToolUse: Sets SUGGESTED_MODEL=claude-haiku-4
├→ Status line: "Model: sonnet → haiku (fast analysis)"
└→ User can press Alt+P if they want different model

Phase 2: code-architect (Sonnet — design)
├→ PreToolUse: Sets SUGGESTED_MODEL=claude-sonnet-4
├→ Status line: "Model: haiku → sonnet (architecture)"
└→ User can press Alt+P if they want different model

Phase 3: code-reviewer (Opus — deep analysis)
├→ PreToolUse: Sets SUGGESTED_MODEL=claude-opus-4
├→ Status line: "Model: sonnet → opus (review)"
└→ User can press Alt+P if they want different model
```

**Key Pattern:** PopKit *suggests* models, but users remain in control. This is elegant because:
- ✓ No programmatic hotkey manipulation (Claude Code controls UX)
- ✓ User sees why each model is suggested
- ✓ User can override anytime
- ✓ Works with single-agent and multi-agent scenarios
- ✓ Integrates with status line naturally

### 4.4 Cost-Aware Model Selection (Optional)

For teams tracking costs:

```python
class ModelSelector:
    """Strategic model selection based on task complexity."""

    COST_MULTIPLIER = {
        "claude-haiku-4": 1.0,           # Baseline
        "claude-sonnet-4": 3.0,          # 3x cost
        "claude-opus-4": 6.0,            # 6x cost
        "claude-opus-4-extended": 7.5    # 7.5x cost
    }

    @staticmethod
    def estimate_task_complexity(task_description: str) -> float:
        """0.0 = simple, 1.0 = complex."""
        # Simple heuristics
        if any(word in task_description.lower() for word in ['simple', 'quick', 'fast']):
            return 0.2
        elif any(word in task_description.lower() for word in ['security', 'audit', 'complex']):
            return 0.9
        else:
            return 0.5

    @staticmethod
    def select_model(complexity: float) -> str:
        """Pick model based on task complexity."""
        if complexity < 0.3:
            return "claude-haiku-4"  # Cost: 1x
        elif complexity < 0.7:
            return "claude-sonnet-4"  # Cost: 3x
        else:
            return "claude-opus-4"    # Cost: 6x
```

**Integration Point:**
```python
# In pre-tool-use.py
if feature_enabled("cost-aware-models"):
    complexity = estimate_task_complexity(task)
    suggested_model = select_model(complexity)
    # Update environment for widget
```

---

## Part 5: Status Line Enhancement (Technical Deep-Dive)

### 5.1 Current PopKit Status Line Architecture

**File:** `power-mode/statusline.py` (1200+ lines, already highly functional)

**Existing Widgets:**
- `widget_popkit()` — Branding [PK]
- `widget_efficiency()` — Token savings
- `widget_power_mode()` — Phase progress
- `widget_workflow()` — Current workflow
- `widget_health()` — Build/test/lint status

**Configuration:**
```json
{
  "statusline": {
    "widgets": ["popkit", "efficiency", "power_mode"],
    "compact_mode": true,
    "show_hints": true,
    "separator": " | "
  }
}
```

### 5.2 Integration Points (Non-Breaking)

**Strategy:** Add new widgets without modifying existing ones.

```python
# NEW: Add these to WIDGETS dict

def widget_context(compact: bool = True) -> str:
    """Context window usage widget."""
    # Reads from aggregated context (Part 3.4)
    pass

def widget_model(compact: bool = True) -> str:
    """Current + suggested model widget."""
    # Reads from environment variables
    pass

def widget_ready_score(compact: bool = True) -> str:
    """Ready-to-code health score from morning routine."""
    # Reads from .claude/popkit/health-state.json
    pass

def widget_agents_streaming(compact: bool = True) -> str:
    """Show which agents are currently streaming."""
    # Reads from Power Mode state
    # Enhanced animation (already has spinner)
    pass

# Then update WIDGETS registry
WIDGETS: Dict[str, Callable[[bool], str]] = {
    "popkit": widget_popkit,
    "efficiency": widget_efficiency,
    "power_mode": widget_power_mode,
    "workflow": widget_workflow,
    "health": widget_health,
    "context": widget_context,      # NEW
    "model": widget_model,          # NEW
    "ready_score": widget_ready_score,  # NEW
    "agents_streaming": widget_agents_streaming,  # NEW
}
```

### 5.3 Enhanced Status Line Examples

**Before:**
```
[PK] Power: #45 3/7 40% | ~2.4k saved | Agents: code-explorer+2
```

**After (All Widgets):**
```
[PK] Power: #45 3/7 40% | Context: 65K/200K (33%) | Model: sonnet→opus | ~2.4k saved | Ready: 85/100
```

**After (Compact):**
```
[PK] #45 3/7 40% | 65K | sonnet→opus | ~2.4k | Ready: 85/100
```

**User Can Configure:**
```json
{
  "statusline": {
    "widgets": ["popkit", "power_mode", "context", "model", "efficiency"],
    "compact_mode": true
  }
}
```

---

## Part 6: Elegant Implementation Patterns (The "How")

### 6.1 The "Zero Breaking Changes" Principle

Every enhancement must pass this test:

```
IF hook is disabled/removed:
  THEN popkit still works, just without new feature
  ✓ Graceful degradation
```

**Example: Context Widget**

Current:
```python
def widget_context(compact: bool = True) -> str:
    metrics = load_efficiency_metrics()
    if not metrics:
        return ""  # ← Gracefully returns empty string
```

**Result:** If context monitoring fails, status line still shows other widgets.

### 6.2 Pure Function Strategy (No State Mutations)

All new code follows the stateless hook pattern:

```python
# ❌ DON'T DO THIS:
def update_context_window():
    global context_data  # ← State mutation
    context_data['used'] += 100

# ✓ DO THIS INSTEAD:
def get_updated_context(old_context: ContextData) -> ContextData:
    return ContextData(
        used=old_context.used + 100,
        # All other fields unchanged
    )
```

**Benefits:**
- Testable in isolation
- Reproducible (same input → same output)
- No race conditions
- Easy to debug

### 6.3 Immutable Context Carrier Pattern

Extend `HookContext` dataclass with new fields:

```python
@dataclass(frozen=True)
class HookContext:
    # Existing fields
    session_id: str
    tool_name: str
    tool_input: Dict[str, Any]

    # NEW: Model context
    suggested_model: Optional[str] = None
    current_model: str = "claude-sonnet-4"

    # NEW: Context aggregation
    aggregated_context_tokens: Optional[int] = None
    context_threshold_level: Optional[str] = None  # "ok", "warning", "critical"

    # NEW: Power Mode coordination
    coordinator_id: Optional[str] = None
    is_in_power_mode: bool = False
```

**Update helper:**
```python
ctx = update_context(
    ctx,
    suggested_model="claude-opus-4",
    current_model="claude-sonnet-4"
)
```

### 6.4 JSON Protocol Convention (Inherit From Claude Code)

All hooks follow this protocol:

```json
// INPUT (from Claude Code)
{
  "session_id": "abc123",
  "tool_name": "Read",
  "tool_input": {"file_path": "/test.py"},
  "message_history": [...]
}

// OUTPUT (to Claude Code)
{
  "decision": "approve",  // or "block" or "ask_user"
  "context": {
    "session_id": "abc123",
    // ... updated context fields
  },
  "log": "Optional logging"
}
```

**Never Add:**
- ❌ Custom side effects
- ❌ API calls (except to internal services)
- ❌ File writes (use state management utilities instead)
- ❌ Global variables

### 6.5 Configuration-Driven Behavior (Users Control Everything)

**New Config Section in .claude/popkit/config.json:**

```json
{
  "claude_code_integration": {
    "context_monitoring": {
      "enabled": true,
      "warning_threshold": 70,
      "critical_threshold": 85,
      "danger_threshold": 95
    },
    "model_suggestions": {
      "enabled": true,
      "show_in_status_line": true,
      "auto_switch": false  // Never auto-switch, just suggest
    },
    "status_line": {
      "widgets": ["popkit", "power_mode", "context", "model", "efficiency"],
      "compact_mode": true,
      "update_interval_ms": 1000
    }
  }
}
```

**Benefits:**
- ✓ Users opt-in to new features
- ✓ Easy to disable if problematic
- ✓ Policies can be enforced per-project
- ✓ No code changes needed to adjust behavior

---

## Part 7: Hook-Based Automation Strategy

### 7.1 PreToolUse Hook: Model Suggestion Logic

```python
# hooks/pre-tool-use.py (NEW SECTION)

def handle_model_preference(ctx: HookContext) -> HookContext:
    """Suggest preferred model based on context."""

    # Only in Power Mode
    if not is_in_power_mode(ctx):
        return ctx

    # Get active agent
    active_agent = get_power_mode_active_agent()
    if not active_agent:
        return ctx

    # Check if agent has model preference
    agent_def = load_agent_definition(active_agent)
    preferred = agent_def.get('model')

    if preferred and preferred != 'inherit':
        current = get_current_model()

        if preferred != current:
            # Store for status line widget
            return update_context(
                ctx,
                suggested_model=preferred,
                current_model=current
            )

    return ctx

# In main processing:
def process(input_json: str) -> str:
    ctx = json.loads(input_json)
    ctx = handle_model_preference(ctx)
    # ... other processing
    return json.dumps(ctx)
```

### 7.2 PostToolUse Hook: Context Aggregation

```python
# hooks/post-tool-use.py (NEW SECTION)

def aggregate_context_usage(ctx: HookContext) -> HookContext:
    """Update aggregated context usage in Redis."""

    if not is_in_power_mode(ctx):
        return ctx

    # Get token usage from current tool
    tokens_used = extract_tokens_from_response(ctx)

    if tokens_used > 0 and ctx.coordinator_id:
        # Update coordinator's context tracking
        try:
            redis_client = get_redis_client()
            coordinator_key = f"powermode:{ctx.coordinator_id}:context"

            # Atomically add to total
            redis_client.incrby(coordinator_key, tokens_used)
        except Exception:
            # Gracefully fall back if Redis unavailable
            pass

    return ctx

def check_context_threshold(ctx: HookContext) -> HookContext:
    """Check if we've hit context limits and warn."""

    if not is_in_power_mode(ctx):
        return ctx

    # Get aggregated context
    total_tokens = get_aggregated_tokens(ctx.coordinator_id)
    context_limit = get_context_limit(ctx.current_model)
    percent = (total_tokens / context_limit) * 100

    # Determine threshold level
    level = "ok"
    if percent >= 95:
        level = "danger"
    elif percent >= 85:
        level = "critical"
    elif percent >= 70:
        level = "warning"

    ctx = update_context(ctx, context_threshold_level=level)

    # Warn if needed
    if level in ["critical", "danger"]:
        print(f"⚠️  Context {percent:.0f}%—consider checkpoint", file=sys.stderr)

    return ctx

# In main processing:
def process(input_json: str) -> str:
    ctx = json.loads(input_json)
    ctx = aggregate_context_usage(ctx)
    ctx = check_context_threshold(ctx)
    # ... other processing
    return json.dumps(ctx)
```

### 7.3 Power Mode Coordinator: Central Aggregation

```python
# power-mode/coordinator.py (NEW METHOD)

class PowerModeCoordinator:
    def aggregate_context_usage(self) -> ContextUsageReport:
        """Get total context from all agents."""

        # Fetch all agent context updates from Redis
        agent_tokens = redis_client.hgetall(
            f"powermode:{self.session_id}:context"
        )

        total = sum(int(tokens) for tokens in agent_tokens.values())

        limit = self.get_context_limit()
        percent = (total / limit) * 100

        return ContextUsageReport(
            total_tokens=total,
            limit_tokens=limit,
            percent=percent,
            agent_breakdown=agent_tokens,
            level=self.determine_level(percent)
        )

    def determine_level(self, percent: float) -> str:
        """Determine warning level."""
        if percent >= 95:
            return "danger"
        elif percent >= 85:
            return "critical"
        elif percent >= 70:
            return "warning"
        else:
            return "ok"
```

---

## Part 8: Integration Points & Non-Breaking Changes

### 8.1 Adding Context Monitoring (Zero Breaking Changes)

**Step 1: Extend context-monitor.py**
- ✓ Existing hook remains active
- ✓ Add Redis support
- ✓ Falls back to file-based if Redis unavailable
- ✓ Existing callers still work

**Step 2: Update Power Mode coordinator**
- ✓ New method `aggregate_context_usage()`
- ✓ Doesn't affect existing orchestration
- ✓ Optional—works if Redis unavailable

**Step 3: Add status line widget**
- ✓ New `widget_context()` function
- ✓ Returns empty string if no data
- ✓ User opts-in via config
- ✓ Existing widgets unaffected

**Result:** If anything breaks, disable context monitoring and system still works.

### 8.2 Adding Model Suggestions (Zero Breaking Changes)

**Step 1: Add model fields to AGENT.md**
- ✓ New optional field `model: inherit`
- ✓ Existing agents continue to work with `model: inherit`
- ✓ No changes to agent routing logic

**Step 2: Update pre-tool-use.py**
- ✓ Add new function `handle_model_preference()`
- ✓ Existing safety checks unaffected
- ✓ Just logs suggestion to stderr/context
- ✓ Never makes actual model switch (user controls)

**Step 3: Add status line widget**
- ✓ New `widget_model()` function
- ✓ Returns empty string if no suggestion
- ✓ User opts-in via config

**Result:** Users who don't enable this feature see no change.

### 8.3 Updating Status Line (Fully Backward Compatible)

**Current Config Still Works:**
```json
{
  "statusline": {
    "widgets": ["popkit", "efficiency", "power_mode"]
  }
}
```

**Enhanced Config (Opt-In):**
```json
{
  "statusline": {
    "widgets": ["popkit", "power_mode", "context", "model", "efficiency"],
    "compact_mode": true
  }
}
```

**Implementation in statusline.py:**
```python
def format_widget_status_line(config: Optional[WidgetConfig] = None) -> str:
    if config is None:
        config = WidgetConfig.load()

    outputs = []
    for widget_name in config.widgets:
        output = get_widget_output(widget_name, config.compact_mode)
        if output:  # ← Skip if widget returns empty string
            outputs.append(output)

    return config.separator.join(outputs)
```

**Result:** Old configs still work. New widgets gracefully skip if data unavailable.

---

## Part 9: Recommended Architecture Decisions

### 9.1 Decision: Redis vs. File-Based Context Tracking

**Recommendation: Start with File-Based, Plan for Redis**

**Phase 1 (Immediate):** File-based aggregation
```python
# Write to .claude/popkit/aggregated-context.json
# Simple, zero dependencies
# Suitable for single-project scenarios
```

**Phase 2 (When Power Mode Scales):** Redis integration
```python
# Write to Redis if available
# Fall back to file-based automatically
# Zero breaking changes
```

**Why:**
- ✓ No Redis dependency for core functionality
- ✓ Works in all environments (CI, standalone, etc.)
- ✓ Easy upgrade path
- ✓ Matches PopKit's "prefer local, fallback to global" philosophy

### 9.2 Decision: Model Selection Strategy

**Recommendation: Suggest, Never Auto-Switch**

**Pattern:**
```python
# ✓ DO: Suggest in status line and environment
os.environ['SUGGESTED_MODEL'] = 'claude-opus-4'
# User presses Alt+P if interested

# ❌ DON'T: Programmatically trigger hotkey
# This is too invasive, Claude Code owns the UX
```

**Why:**
- ✓ Respects user agency
- ✓ No UX surprises
- ✓ User stays in control of model costs
- ✓ Compatible with Claude Code's design

### 9.3 Decision: Hook Execution Strategy

**Recommendation: Implement in Post-Tool-Use, Not Pre-Tool-Use**

**Why Post-Tool-Use?**
- ✓ We have actual token usage data
- ✓ Less performance impact (already done with work)
- ✓ Can batch updates
- ✓ Non-blocking

**Post-Tool-Use Hook Order (in hooks.json):**
1. `post-tool-use.py` — Routing, logging (fast)
2. `context-monitor.py` — Token tracking (fast, existing)
3. **NEW:** aggregation logic — Add to context-monitor.py
4. `agent-observability.py` — Metrics (fast)
5. `quality-gate.py` — Code quality (slow, can timeout)

### 9.4 Decision: Configuration Schema

**Recommendation: Extend agents/config.json, Not Create New File**

**Current:**
```json
{
  "tiers": {...},
  "routing": {...}
}
```

**Proposed Addition:**
```json
{
  "tiers": {...},
  "routing": {...},
  "claude_code_integration": {  // NEW SECTION
    "context_tracking": {
      "enabled": true,
      "aggregation_method": "redis_with_fallback",
      "thresholds": {
        "warning": 70,
        "critical": 85,
        "danger": 95
      }
    },
    "model_suggestions": {
      "enabled": true,
      "auto_suggest_in_status_line": true,
      "auto_switch": false
    },
    "status_line_widgets": {
      "defaults": ["popkit", "power_mode", "efficiency"],
      "optional": ["context", "model", "ready_score"]
    }
  }
}
```

**Benefits:**
- ✓ Single source of truth
- ✓ All settings discoverable
- ✓ Easy to document
- ✓ Matches PopKit's architecture

---

## Part 10: Implementation Roadmap (Technical)

### Phase 1: Foundation (Week 1)

**Goal:** Get context aggregation working

**Tasks:**

1. **Extend context-monitor.py**
   - Add `aggregate_context_usage()` method
   - Support file-based aggregation first
   - Keep existing functionality intact

2. **Update hooks.json**
   - Add environment variable setup in pre-tool-use.py
   - No new hooks, just extend existing ones

3. **Test**: Verify token tracking works in Power Mode

**Deliverable:** `/popkit:power metrics` shows aggregated context

### Phase 2: Status Line (Week 2)

**Goal:** Add context & model widgets to status line

**Tasks:**

1. **Add context widget to statusline.py**
   - Reads from aggregated-context.json
   - Colors based on thresholds
   - Gracefully returns "" if no data

2. **Add model widget to statusline.py**
   - Reads from environment variables
   - Shows current + suggested
   - Users can configure in .claude/popkit/config.json

3. **Update default config**
   - Add new widgets with sensible defaults
   - Make all optional

**Deliverable:** Enhanced status line showing context & model hints

### Phase 3: Model Suggestions (Week 3)

**Goal:** Agent-aware model recommendations

**Tasks:**

1. **Add model field to agent definitions**
   - Extend agent AGENT.md template
   - Update 5-10 key agents with preferences

2. **Update pre-tool-use.py**
   - Implement `handle_model_preference()` function
   - Store in environment for widgets

3. **Test**: Verify model suggestions show correctly

**Deliverable:** Status line shows "Model: sonnet → opus" for code-reviewer

### Phase 4: Redis Integration (Week 4)

**Goal:** Scalable context tracking for large Power Mode sessions

**Tasks:**

1. **Make context-monitor.py Redis-aware**
   - Try to connect to Redis on startup
   - Fall back to file-based if unavailable
   - No breaking changes

2. **Update Power Mode coordinator**
   - Implement Redis-based aggregation
   - Keep file-based as fallback

3. **Test**: Verify 6+ agents in parallel works

**Deliverable:** Power Mode scales without context tracking overhead

---

## Conclusion: Why This Architecture Works

### 1. Elegant (Not Overengineered)

- ✓ Extends existing patterns (hooks, widgets, context)
- ✓ No new complex systems
- ✓ Configuration-driven, not code-driven
- ✓ Users opt-in to features

### 2. Automatic (Users Don't Have to Think)

- ✓ Hooks run automatically with tools
- ✓ Context aggregation happens in background
- ✓ Status line updates in real-time
- ✓ Warnings surface when needed

### 3. Non-Breaking (Zero Risk)

- ✓ All new code is optional
- ✓ Existing functionality untouched
- ✓ Graceful degradation if features fail
- ✓ Easy to roll back

### 4. Scalable (Grows with Power Mode)

- ✓ File-based for simple cases
- ✓ Redis for complex orchestration
- ✓ No architectural changes between scales
- ✓ Coordinator remains single point of truth

### 5. Testable (Each Component Isolated)

- ✓ Pure functions, no side effects
- ✓ Immutable context passing
- ✓ Hooks testable independently
- ✓ Widget functions testable in isolation

---

## Next Steps for Team

1. **Review this architecture** with team
2. **Make decision** on Redis vs. file-based start
3. **Create technical spec** for Phase 1
4. **Assign implementation** to team members
5. **Start with context aggregation** (lowest risk, highest value)

---

**Research Completed:** December 11, 2025
**Status:** Ready for implementation planning
**Questions?** Refer to original CLAUDE_CODE_RESEARCH.md for feature-level details
