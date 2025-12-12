# Claude Code v2.0.65+ Research: Features & PopKit Integration

**Date:** December 11, 2025
**Research Focus:** 3 Major Claude Code Features (v2.0.60-2.0.65) and PopKit Integration Opportunities

---

## Executive Summary

Three Claude Code features in the latest releases (v2.0.60-2.0.65) present opportunities to enhance PopKit's user experience:

1. **Model Switcher (v2.0.65)**: Mid-conversation model switching via hotkey (Alt+P / Option+P)
2. **Context Window Info (v2.0.65)**: Real-time context window display in status line
3. **Status Lines & Background Agents (v2.0.60+)**: Enhanced status line system with background agent execution

**Status:** Research complete, integration recommendations ready for planning phase.

---

## 1. MODEL SWITCHER (v2.0.65)

### Feature Details

**What It Does:**
- Users can switch AI models mid-conversation using **Alt+P** (Linux/Windows) or **Option+P** (macOS)
- Hotkey brings up a model selector during conversation
- Model switch is seamless; context is preserved
- Reduces friction when specific tasks need different models

**Current Claude Code Behavior:**
```
User types with model → Alt+P → Model selector appears → Pick new model → Continue in conversation
```

### PopKit Integration Opportunities

#### 1A: Agent-Specific Model Selection
**Benefit:** Tier-1 agents could auto-select optimal models for their specialization

| Agent | Optimal Model | Use Case |
|-------|--------------|----------|
| `bug-whisperer` | Sonnet 4.5 | Deep reasoning for tricky bugs |
| `code-reviewer` | Opus (extended thinking) | Complex code reviews |
| `test-writer-fixer` | Haiku 4.5 | Quick test generation |
| `performance-optimizer` | Sonnet 4.5 | Analysis + optimization |
| `security-auditor` | Opus | Deep security analysis |

**Implementation:**
- Store preferred model in agent definition (agents/config.json)
- Hook detects agent selection → auto-switch model
- User can override with Alt+P if needed

#### 1B: Power Mode Model Rotation
**Benefit:** Different agents in parallel could use different models

**Example Multi-Agent Flow:**
1. Phase 1: code-explorer (Haiku, fast analysis)
2. Phase 2: code-architect (Sonnet, design + reasoning)
3. Phase 3: code-reviewer (Opus, comprehensive review)
4. Phase 4: security-auditor (Opus, deep security check)

**Implementation:**
- Power Mode coordinator tracks active agent
- Coordinator issues model-switch message before agent activation
- Agents stream results back (v2.0.60 background agents support this)

#### 1C: Cost-Aware Model Selection
**Benefit:** Optimize costs without sacrificing quality

**Strategy:**
- Simple tasks → Haiku (cost: 1x baseline)
- Medium tasks → Sonnet (cost: 3x baseline)
- Complex tasks → Opus (cost: 6x baseline)

**Implementation:**
- Task complexity estimator in hook layer
- Auto-select model based on complexity score
- `/popkit:stats` shows projected token costs

### Implementation Complexity: **Medium**

**Files to Modify:**
- `agents/config.json` - Add model preferences per agent
- `hooks/pre-tool-use.py` - Model switching logic
- `hooks/utils/` - New model_selector utility
- `power-mode/coordinator.py` - Multi-agent model orchestration

**Risks:**
- Model context differences (some models may not understand specific instructions)
- Token cost increase if Opus is over-selected
- User confusion if model switch is not visible

---

## 2. CONTEXT WINDOW INFO (v2.0.65)

### Feature Details

**What It Does:**
- Displays current context window usage in the Claude Code status line
- Shows format: `Context: 45K / 200K (22%)`
- Real-time updates as conversation grows
- Helps users understand token budget

**Current Behavior:**
```
Status line shows: [Claude Code] Context: 45K / 200K (22%) | Model: Sonnet
```

### PopKit Integration Opportunities

#### 2A: Multi-Agent Context Budgeting
**Benefit:** Track context usage across all parallel agents

**Current Gap:**
- PopKit has 6+ agents running in parallel (Power Mode)
- No unified view of total context usage
- Agents may not be aware of shared context constraints

**PopKit Enhancement:**
```
Status Line Display:
[PK] Context: 23K/200K (11%) | Power: #45 3/7 | Agents: code-explorer,code-architect
```

**Implementation:**
- Each agent reports context usage after streaming
- Power Mode coordinator sums across all agents
- `power-mode/metrics.py` tracks context utilization
- Status line widget displays aggregated context

#### 2B: Context Window Warnings
**Benefit:** Prevent out-of-context errors mid-workflow

**Thresholds:**
- 70%: Warning in status line (`⚠ Context 70%`)
- 85%: Hold new agents (prevent phase activation)
- 95%: Suggest session save/resume

**Implementation:**
- `hooks/utils/context_monitor.py` - Track usage
- Post-tool-use hook checks threshold
- AskUserQuestion prompts for action (save, switch model, continue)

#### 2C: Session-Based Context Recovery
**Benefit:** Resume work with fresh context window

**Feature:**
- `/popkit:session checkpoint` - Saves current progress to STATUS.json
- `/popkit:session resume NAME` - Resumes from checkpoint with fresh context
- Aligns with v2.0.64 named sessions feature

**Example Workflow:**
```
User: "Working on feature X, context at 90%"
PopKit: "⚠ Context window full. Use /popkit:session checkpoint to save?"
User: "Yes"
PopKit: "Saved to .claude/STATUS.json. Run /popkit:session resume to continue fresh."
[New session starts with full context]
```

**Implementation:**
- Extend STATUS.json format with checkpoints
- New skill: `pop-session-checkpoint`
- New command: `/popkit:session checkpoint/resume/list`

### Implementation Complexity: **Medium-High**

**Files to Modify:**
- `power-mode/metrics.py` - Add context tracking
- `hooks/utils/context_monitor.py` - NEW
- `power-mode/statusline.py` - Add context widget
- `skills/pop-session-checkpoint/` - NEW skill
- `commands/session.md` - NEW command

**Risks:**
- Over-aggressive context warnings could interrupt workflow
- Context calculation differences between Claude Code's display and agent's actual usage
- Session resume complexity (preserving conversation state)

---

## 3. STATUS LINES & BACKGROUND AGENTS (v2.0.60+)

### Feature Details

**What v2.0.60 Does:**
- Agents run in background while user continues coding
- Status line shows agent progress live
- No blocking on agent completion
- `/mcp enable [server]` / `/mcp disable [server]` toggles MCP servers

**What v2.0.65 Adds:**
- Context window display in status line
- Extended status line customization

### PopKit's Current Status Line

**Existing Implementation:** `packages/plugin/power-mode/statusline.py`

```
[PK] Power: #45 3/7 40% | ~2.4k saved | Agents: code-explorer+2
```

**Widgets Available:**
- `popkit` - Branding
- `efficiency` - Token savings
- `power_mode` - Phase progress
- `workflow` - Workflow state
- `health` - Build/test status

### PopKit Integration Opportunities

#### 3A: Context Window Widget
**Add to Status Line:**
```
[PK] Power: #45 3/7 40% | Context: 45K/200K | ~2.4k saved
```

**Implementation:**
```python
def widget_context(compact: bool = True) -> str:
    context = get_context_usage()  # From coordinator
    if context:
        percent = int(context['used'] / context['max'] * 100)
        if compact:
            return f"{Colors.YELLOW}{context['used']}K{Colors.RESET}"
        return f"Context: {context['used']}K/{context['max']}K ({percent}%)"
    return ""
```

#### 3B: Background Agent Activity Indicator
**Enhance Existing Widget:**

Current:
```
[PK] Power: #45 3/7 40% | Agents: code-explorer+2
```

Enhanced:
```
[PK] Power: #45 3/7 40% | ⠙ Agents: code-explorer,code-architect | Context: 45K/200K
```

**Animated Spinner:** Braille characters cycle when agents actively running
- Still (no spinner): Agents waiting
- Animated: Agents streaming
- Complete: All agents finished

**Implementation:**
- Already in `statusline.py` as `format_streaming_indicator()`
- Enhance with agent activity tracking
- Update Power Mode coordinator to push activity events

#### 3C: Model Display Widget
**New Widget:**

```
[PK] Power: #45 3/7 40% | Model: Sonnet | Context: 45K/200K
```

**Benefits:**
- Users know which model(s) are active
- Multi-agent setups show per-agent models
- Helps with cost tracking

**Implementation:**
```python
def widget_model(compact: bool = True) -> str:
    models = get_active_models()  # From coordinator
    if compact:
        if len(set(models)) == 1:
            return f"Model: {models[0]}"
        return f"Models: {'+'.join(set(models))}"
    return f"Active Models: {', '.join(models)}"
```

#### 3D: "Ready to Code" Indicator
**Integration with Morning Routine:**

Current morning routine (v2.0.64 mentions `/stats`):
```
/popkit:routine morning → Health check → "Ready to Code" score (0-100)
```

**Proposal:** Display score in status line

```
[PK] Ready: 87/100 | Health: +++ | Power: #45 3/7 40%
```

**Widgets:**
```json
"statusline": {
  "widgets": ["popkit", "ready_score", "power_mode", "context"],
  "compact_mode": true
}
```

### Implementation Complexity: **Low**

**Files to Modify:**
- `power-mode/statusline.py` - Add context/model/ready widgets
- `power-mode/coordinator.py` - Push model + context info
- `hooks/utils/context_monitor.py` - NEW (tracks context)
- `.claude-plugin/plugin.json` - Update status line settings description

**Risks:**
- Status line crowding (users need to configure widgets)
- Real-time updates may cause flicker
- Model tracking complexity in parallel agents

---

## Integration Priority Matrix

| Feature | Effort | Impact | Priority | Notes |
|---------|--------|--------|----------|-------|
| **Model Switcher** | Medium | High | Phase Next | Requires hook layer changes, but high ROI for Power Mode |
| **Context Window Info** | Medium-High | High | Phase Next | Critical for preventing errors, enables session resumption |
| **Status Line Enhancement** | Low | Medium | Phase Now | Quick wins; can be done incrementally |
| **Background Agents** | Low | Low | Already Done | v2.0.60 feature already supported by PopKit |

---

## Recommended Implementation Roadmap

### Phase 1: Status Line Enhancements (Week 1)
**Goal:** Leverage existing Claude Code status line without major rework

**Tasks:**
1. Add `context` widget to `statusline.py`
2. Add `model` widget to `statusline.py`
3. Add `ready_score` widget from morning routine
4. Update Power Mode coordinator to track model + context
5. Test with `/popkit:power metrics`

**Deliverable:** Enhanced status line showing context, model, ready score

### Phase 2: Context Monitoring (Week 2)
**Goal:** Prevent out-of-context errors

**Tasks:**
1. Create `hooks/utils/context_monitor.py`
2. Add context threshold checks to `post-tool-use.py`
3. Implement AskUserQuestion prompts for context warnings
4. Create `/popkit:session checkpoint` skill
5. Add context data to STATUS.json format

**Deliverable:** Context warnings + session checkpoint capability

### Phase 3: Model Selection System (Week 3)
**Goal:** Optimize model usage across agents

**Tasks:**
1. Add `preferred_model` to agent definitions in config.json
2. Create `hooks/utils/model_selector.py`
3. Update `pre-tool-use.py` to trigger model switches
4. Implement agent-aware model switching
5. Add cost tracking to `/popkit:stats`

**Deliverable:** Agent-aware model selection + cost tracking

### Phase 4: Power Mode Model Orchestration (Week 4)
**Goal:** Different agents use different models in parallel

**Tasks:**
1. Update Power Mode coordinator to manage model switches
2. Implement model switch messaging in pub/sub system
3. Create model-specific agent configurations
4. Test multi-model parallel execution
5. Add phase-specific model selection strategy

**Deliverable:** Multi-model Power Mode orchestration

---

## Code Examples

### Example 1: Model Switcher Hook
```python
# hooks/utils/model_selector.py
def get_optimal_model(agent_name: str) -> str:
    """Get optimal model for an agent."""
    model_preferences = {
        "bug-whisperer": "claude-3-5-sonnet-20251022",
        "code-reviewer": "claude-opus-4-1-20250805",  # Extended thinking
        "test-writer-fixer": "claude-3-5-haiku-20241022",
        "security-auditor": "claude-opus-4-1-20250805",
        "performance-optimizer": "claude-3-5-sonnet-20251022",
    }
    return model_preferences.get(agent_name, "claude-3-5-sonnet-20251022")

# Usage in pre-tool-use.py
if agent_uses_specific_model:
    model = get_optimal_model(agent_name)
    # Trigger model switch via hotkey signal
    trigger_model_switch(model)
```

### Example 2: Context Window Widget
```python
# In power-mode/statusline.py
def widget_context(compact: bool = True) -> str:
    """Context window usage widget."""
    metrics = load_efficiency_metrics()
    if not metrics:
        return ""

    context_used = metrics.get("context_used_tokens", 0)
    context_max = metrics.get("context_max_tokens", 200000)

    if context_used == 0:
        return ""

    percent = int(context_used / context_max * 100)

    if compact:
        return f"{Colors.YELLOW}{context_used//1000}K{Colors.RESET}"

    return f"Context: {context_used}K/{context_max}K ({percent}%)"
```

### Example 3: Context Threshold Check
```python
# In hooks/post-tool-use.py
def check_context_threshold(metrics: dict) -> Optional[str]:
    """Check if context usage exceeds safe threshold."""
    percent = (metrics['context_used'] / metrics['context_max']) * 100

    if percent >= 85:
        return "block"  # Prevent more agents
    elif percent >= 70:
        # Warn user
        return json.dumps({
            "decision": "approve",
            "reason": "context_warning",
            "message": f"⚠ Context window {int(percent)}% full. Consider /popkit:session checkpoint"
        })

    return None
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| **Model switching fails** | Medium | High | Fallback to current model, log error |
| **Context tracking inaccurate** | Medium | Medium | Periodically sync with Claude Code's reported usage |
| **Status line too crowded** | High | Low | Make all widgets optional in config |
| **Performance hit from monitoring** | Low | Medium | Use event-based updates, not polling |
| **Multi-model coordination complexity** | Medium | High | Start with Phase 1-2 only, defer Power Mode orchestration |

---

## Not Recommended: Android Support

**Note:** The user mentioned "Claude Code on Android" in their request, but **no Android features are documented in the Claude Code v2.0.60-2.0.65 changelog**. This may be:
- Coming in a future release
- Not yet announced
- Confused with a different product

**Recommendation:** Monitor future Claude Code releases for Android support. PopKit's plugin architecture should be inherently portable once Claude Code Android is released.

---

## Conclusion

The three Claude Code features (Model Switcher, Context Window Info, Status Lines) present meaningful opportunities to enhance PopKit's multi-agent orchestration system. The recommended phased approach prioritizes quick wins (status line enhancements) before tackling more complex features (model orchestration).

**Next Steps:**
1. Present Phase 1 implementation plan to team
2. Get alignment on Phase 2 context monitoring approach
3. Start implementation with status line widgets (lowest risk, highest immediate value)
4. Defer Phases 3-4 until core PopKit 1.0 is stable

---

**Research Completed By:** Claude Code
**Repository:** jrc1883/popkit (private monorepo)
**Branch:** claude/research-claude-code-features-01WpyQzGrNeGx7cSNqM91iqP
