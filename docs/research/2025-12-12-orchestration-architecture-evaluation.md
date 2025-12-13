# Orchestration Architecture Evaluation: Beyond the Tiered Approach

**Date:** 2025-12-12
**Status:** Research Complete - Recommendations Ready
**Related Issues:** #205 (Programmatic Skill Orchestration)

---

## Executive Summary

This document evaluates PopKit's current tiered agent architecture and explores alternatives including a **single programmatic orchestrator**. After comprehensive research, the recommendation is to evolve from a tiered loading model to a **workflow-centric orchestration model** that:

1. **Retains tier structure** for Claude Code's native agent loading (it works well for this)
2. **Adds programmatic orchestration layer** for skill chaining and workflow execution
3. **Uses Upstash Workflow** for durable cross-session orchestration
4. **Implements semantic routing** via Upstash Vector for intelligent agent selection
5. **Supports file-based fallback** for zero-dependency local development

**Key Insight:** The tiered approach is NOT the problem. The problem is the lack of a programmatic orchestration layer that can chain skills, route responses, and manage workflows without requiring the LLM to manually coordinate each step.

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Architectural Limitations](#architectural-limitations)
3. [Alternative Approaches Evaluated](#alternative-approaches-evaluated)
4. [Recommended Architecture](#recommended-architecture)
5. [Implementation Plan](#implementation-plan)
6. [Migration Strategy](#migration-strategy)
7. [Risk Assessment](#risk-assessment)

---

## Current State Analysis

### Tiered Agent Architecture

```
packages/plugin/agents/
├── tier-1-always-active/     # 11 agents - loaded at session start
│   ├── bug-whisperer/
│   ├── code-reviewer/
│   ├── security-auditor/
│   └── ... (8 more)
├── tier-2-on-demand/         # 17 agents - loaded when triggered
│   ├── ai-engineer/
│   ├── meta-agent/
│   └── ... (15 more)
├── feature-workflow/         # 2 agents - for 7-phase development
│   ├── code-architect/
│   └── code-explorer/
└── assessors/               # 6 agents - for quality assessment
```

**How it works:**
- **Tier-1**: Loaded into Claude Code's context at session start
- **Tier-2**: Loaded dynamically via keyword/file/error pattern triggers
- **Routing**: `agents/config.json` defines routing rules (keywords, patterns, confidence)

**What it does well:**
- Context window efficiency (progressive disclosure)
- Universal agents available immediately
- Specialized agents loaded only when needed
- Clear separation of concerns

**What it doesn't do:**
- Programmatic skill chaining (skills can't call other skills directly)
- Response-driven routing (AskUserQuestion responses don't trigger workflows)
- Background workflow execution (no async agent spawning from skills)
- Cross-session workflow continuity (state lost on restart)

### Native Coordinator (Power Mode)

```python
# packages/plugin/power-mode/native_coordinator.py
class NativeAsyncCoordinator:
    """
    Orchestrates multi-agent collaboration using Claude Code's
    native background agent support (Task with run_in_background=true).
    """
    def decompose_objective(self) -> List[Phase]
    def register_agent(self, agent_id, name, task, phase) -> BackgroundAgent
    def share_insight(self, source_agent, type, content, tags) -> Insight
    def check_phase_complete(self) -> bool
    def advance_to_next_phase(self) -> Optional[Phase]
```

**Capabilities:**
- Phase-based workflow execution
- Agent registration and status tracking
- Insight sharing between agents
- File-based state persistence

**Limitations:**
- Requires manual activation (`/popkit:power start`)
- State lost on Claude Code session restart
- No cross-session workflow resumption
- No integration with skill system

### Skill State Tracker

```python
# packages/plugin/hooks/utils/skill_state.py
class SkillStateTracker:
    """Tracks active skill and enforces required decisions."""
    def start_skill(self, skill_name, workflow_id) -> None
    def end_skill(self, status, output) -> None
    def record_decision(self, decision_id) -> None
    def get_pending_completion_decisions() -> List[dict]
    def _publish_activity(self, event_type, data) -> Optional[str]
```

**Capabilities:**
- Track which skill is currently active
- Enforce AskUserQuestion decisions (Issue #159)
- Publish skill lifecycle events to activity ledger
- Record errors and tool usage

**Limitations:**
- Cannot invoke other skills programmatically
- Cannot route based on AskUserQuestion responses
- Activity ledger is informational only, not actionable

### Context Storage Backends

```python
# packages/plugin/hooks/utils/context_storage.py
class BaseContextStorage(ABC):
    """Abstract base for context storage backends."""
    def publish_activity(self, skill_name, event_type, data, workflow_id) -> str
    def get_activity_stream(self, workflow_id, since) -> List[Dict]
    def store_context(self, workflow_id, context) -> None
    def get_context(self, workflow_id) -> Optional[Dict]

# Implementations:
# - FileContextStorage (free tier)
# - UpstashContextStorage (Pro tier)
# - CloudAPIContextStorage (future Team tier)
```

**Capabilities:**
- Activity ledger with timestamps
- Context persistence across skills
- Multi-backend support (file, Upstash, cloud)

**Limitations:**
- Read-only from hooks (cannot trigger actions)
- No message queue functionality
- No workflow state machine

### Hook Capabilities Matrix

| Capability | Pre-Tool Hook | Post-Tool Hook | Notes |
|------------|---------------|----------------|-------|
| Block tool execution | ✅ | ❌ | Return `{"decision": "block"}` |
| Modify tool input | ✅ | ❌ | Transform parameters |
| Read tool output | ❌ | ✅ | Analyze results |
| Invoke tools | ❌ | ❌ | **IMPOSSIBLE** - architectural limitation |
| Chain skills | ❌ | ❌ | **IMPOSSIBLE** - requires tool invocation |
| Update state | ✅ | ✅ | File/DB writes allowed |
| Publish events | ✅ | ✅ | Activity ledger, etc. |

**Critical Limitation:** Hooks are **reactive only**. They cannot initiate tool calls, spawn agents, or chain skills. They can only observe, block, or modify within their scope.

---

## Architectural Limitations

### Why Tiered Loading Isn't the Problem

The tiered loading approach is **correct for Claude Code's architecture**. It ensures:
1. Context window efficiency (PD-001: max 15 Tier-1 agents)
2. Fast session startup (only essential agents loaded)
3. Trigger-based specialization (right agent for right task)

**The problem is not tier loading. The problem is the lack of an orchestration layer.**

### The Missing Orchestration Layer

Currently, when a skill needs to:
1. Ask a user question → get response → branch to different skill
2. Spawn background agents → wait for completion → aggregate results
3. Execute a multi-step workflow → handle errors → retry or escalate

...it has to rely on the **LLM to manually orchestrate** each step. This is:
- **Slow**: LLM round-trips for each decision
- **Unreliable**: LLM might skip steps or misunderstand context
- **Expensive**: Token cost for coordination overhead
- **Non-resumable**: Can't continue a workflow across sessions

### What We Need: Programmatic Orchestration

```
User Request
    ↓
Orchestrator (NEW)
    ↓
    ├── Semantic Routing (Upstash Vector)
    │   └── Select best skill/agent based on intent
    ├── Workflow Engine (Upstash Workflow)
    │   └── Execute multi-step durable workflows
    ├── Response Router
    │   └── Route AskUserQuestion responses to workflows
    └── Background Agents
        └── Spawn and monitor async agents

Current Flow:          Future Flow:
┌─────────┐            ┌─────────┐
│   LLM   │            │   LLM   │
│(manual) │            │(assisted)│
└────┬────┘            └────┬────┘
     │                      │
     ▼                      ▼
┌─────────┐            ┌─────────────┐
│  Skill  │            │ Orchestrator│
└────┬────┘            │ (automatic) │
     │                 └──────┬──────┘
     ▼                        │
┌─────────┐            ┌──────▼──────┐
│  Skill  │ (manual)   │    Skill    │
└────┬────┘            └──────┬──────┘
     │                        │
     ▼                        ▼
┌─────────┐            ┌──────────────┐
│  Skill  │ (manual)   │    Skill     │ (automatic)
└─────────┘            └──────────────┘
```

---

## Alternative Approaches Evaluated

### Approach 1: Single Global Orchestrator (Full Replacement)

**Concept:** Replace the tiered structure with a single orchestrator that routes ALL requests.

```typescript
// Theoretical single orchestrator
class PopKitOrchestrator {
  async route(request: UserRequest): Promise<Skill> {
    // Semantic search for best agent/skill
    const match = await vectorSearch(request.intent);
    return this.skills[match.id];
  }

  async execute(skill: Skill, context: Context): Promise<Result> {
    // Execute skill with automatic chaining
    const result = await skill.execute(context);
    if (result.nextSkill) {
      return this.execute(result.nextSkill, result.context);
    }
    return result;
  }
}
```

**Pros:**
- Simple mental model (one entry point)
- Full control over routing
- Can implement any orchestration pattern

**Cons:**
- Loses Claude Code's native agent benefits
- Requires reimplementing agent selection
- Doesn't integrate with existing skill/hook system
- Heavy lift for minimal benefit

**Verdict:** ❌ **Not recommended** - throws away working infrastructure

### Approach 2: Upstash Workflow as Orchestration Layer (Complement)

**Concept:** Keep tiered agents but add Upstash Workflow for durable orchestration.

```typescript
// Workflow-based orchestration
export const { POST } = serve(async (context) => {
  // Phase 1: Initial skill execution
  const phase1 = await context.run("exploration", async () => {
    return await invokeSkill("pop-project-analyze");
  });

  // Phase 2: Wait for user decision
  const { eventData: decision } = await context.waitForEvent(
    "user-decision",
    `decision-${context.workflowRunId}`
  );

  // Phase 3: Route based on decision
  if (decision.choice === "implement") {
    return await context.run("implementation", async () => {
      return await invokeSkill("pop-feature-dev");
    });
  } else if (decision.choice === "research") {
    return await context.run("research", async () => {
      return await invokeSkill("pop-research-deep");
    });
  }
});
```

**Pros:**
- Durable workflows (survive restarts)
- Native `waitForEvent` for user decisions
- Automatic retries and dead letter queues
- Integrates with existing skill system
- Purpose-built for multi-agent coordination

**Cons:**
- Requires cloud backend (PopKit Cloud)
- Learning curve for Workflow API
- May add latency (HTTP round-trips)

**Verdict:** ✅ **Recommended for Pro/Team tiers**

### Approach 3: File-Based Workflow Engine (Local Fallback)

**Concept:** Local file-based workflow engine for free tier users.

```python
# File-based workflow state machine
class LocalWorkflowEngine:
    """Simple workflow engine using file-based state."""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.state_file = Path(f".claude/popkit/workflows/{workflow_id}.json")

    def execute_step(self, step_name: str, skill: str, context: dict) -> dict:
        """Execute a workflow step."""
        state = self._load_state()

        if state["current_step"] != step_name:
            raise WorkflowError(f"Expected step {state['current_step']}, got {step_name}")

        # Execute skill (returns when LLM invokes it)
        result = {
            "skill": skill,
            "context": context,
            "step": step_name
        }

        # Advance state
        state["current_step"] = state["next_steps"].pop(0)
        state["completed_steps"].append(step_name)
        self._save_state(state)

        return result

    def wait_for_response(self, decision_id: str) -> dict:
        """Wait for user response (via polling)."""
        response_file = self.state_file.parent / f"{decision_id}.response.json"
        # Response will be written by post-tool-use hook when AskUserQuestion completes
        return self._poll_for_file(response_file)
```

**Pros:**
- Zero dependencies (just files)
- Works offline
- Free for all users
- Survives session restarts (if state is saved)

**Cons:**
- No automatic retries
- No dead letter queue
- Polling-based (not event-driven)
- More complex state management

**Verdict:** ✅ **Recommended as fallback for free tier**

### Approach 4: Hybrid Orchestration (Best of Both)

**Concept:** Use tiered agents + Workflow for cloud + file-based for local.

```
┌─────────────────────────────────────────────────────────┐
│                  PopKit Orchestration                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Agent Selection Layer                  │   │
│  │  (Tiered loading - unchanged, works great)       │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Semantic Routing Layer                 │   │
│  │  (Upstash Vector - semantic agent selection)     │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Workflow Orchestration Layer           │   │
│  │  ┌───────────────┐   ┌───────────────────────┐  │   │
│  │  │ Upstash       │   │ File-Based Engine     │  │   │
│  │  │ Workflow      │   │ (local fallback)      │  │   │
│  │  │ (Pro/Team)    │   │ (Free tier)           │  │   │
│  │  └───────────────┘   └───────────────────────┘  │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Response Routing Layer                 │   │
│  │  (AskUserQuestion responses → workflow events)   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Verdict:** ✅ **RECOMMENDED ARCHITECTURE**

---

## Recommended Architecture

### Overview

The recommended architecture **keeps the tiered agent structure** (it works well) and **adds orchestration layers** on top:

1. **Keep:** Tier-1/Tier-2 agent loading (unchanged)
2. **Add:** Semantic routing via Upstash Vector
3. **Add:** Workflow orchestration via Upstash Workflow (Pro) / file-based (Free)
4. **Add:** Response router for AskUserQuestion → workflow events
5. **Add:** Background agent spawning from workflows

### Component Diagram

```
                    ┌─────────────────────────────────┐
                    │         User Request            │
                    └───────────────┬─────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER (NEW)                  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Semantic Router (Upstash Vector)           │ │
│  │  • Query: "fix authentication bug" → bug-whisperer      │ │
│  │  • Query: "optimize database" → query-optimizer         │ │
│  │  • Fallback: keyword matching (existing)                │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                                │
│                              ▼                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Workflow Engine                             │ │
│  │  ┌───────────────────────┐  ┌─────────────────────────┐ │ │
│  │  │   Upstash Workflow    │  │   File-Based Engine     │ │ │
│  │  │   (Pro/Team tier)     │  │   (Free tier fallback)  │ │ │
│  │  │                       │  │                         │ │ │
│  │  │   • context.run()     │  │   • JSON state machine  │ │ │
│  │  │   • waitForEvent()    │  │   • File-based events   │ │ │
│  │  │   • context.call()    │  │   • Polling-based wait  │ │ │
│  │  │   • Auto-retry/DLQ    │  │   • Manual retry        │ │ │
│  │  └───────────────────────┘  └─────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                                │
│                              ▼                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Response Router                             │ │
│  │  • AskUserQuestion response → workflow.notify()         │ │
│  │  • Maps decision_id to workflow event                   │ │
│  │  • Routes to next skill based on selection              │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────┐
│                    EXISTING CLAUDE CODE LAYER                  │
│                                                               │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         Tiered Agent Loading (unchanged)                  │ │
│  │  • Tier-1: Always-active (11 agents)                      │ │
│  │  • Tier-2: On-demand (17 agents)                          │ │
│  │  • Feature Workflow (2 agents)                            │ │
│  │  • Assessors (6 agents)                                   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                │
│                              ▼                                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         Skills + Hooks (enhanced)                         │ │
│  │  • Skills can define workflow steps                       │ │
│  │  • Skills can define async agents to spawn                │ │
│  │  • Hooks publish events to orchestrator                   │ │
│  │  • Response hook routes to workflow                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Skill Workflow Definition

Skills can define the workflows they participate in:

```yaml
# SKILL.md frontmatter
---
name: pop-feature-dev
triggers:
  - "implement feature"
  - "build feature"

# NEW: Workflow definition
workflow:
  id: feature-development
  steps:
    - id: discovery
      description: "Understand requirements"
      next: exploration

    - id: exploration
      description: "Explore codebase"
      agent: code-explorer
      next: questions

    - id: questions
      description: "Clarify with user"
      type: user_decision
      question: "What approach should we take?"
      options:
        - id: simple
          label: "Simple implementation"
          next: implement_simple
        - id: comprehensive
          label: "Comprehensive with tests"
          next: implement_comprehensive

    - id: implement_simple
      description: "Implement basic feature"
      next: review

    - id: implement_comprehensive
      description: "Implement with tests"
      spawn_agents:
        - code-reviewer (implementation)
        - test-writer-fixer (tests)
      next: review

    - id: review
      description: "Review changes"
      agent: code-reviewer
      next: complete
---
```

### Response Routing

When AskUserQuestion completes, the response routes to the workflow:

```python
# hooks/post-tool-use.py
def handle_ask_user_question_response(tool_output: dict):
    """Route AskUserQuestion response to workflow."""
    answers = tool_output.get("answers", {})

    # Find active workflow
    workflow_id = get_active_workflow()
    if not workflow_id:
        return  # No active workflow, normal behavior

    # Get workflow engine
    engine = get_workflow_engine()  # Returns Upstash or file-based

    # Notify workflow of user decision
    for question_id, answer in answers.items():
        engine.notify_event(
            workflow_id=workflow_id,
            event_id=f"decision-{question_id}",
            data={"answer": answer}
        )
```

### Background Agent Spawning

Workflows can spawn background agents that run in parallel:

```typescript
// Workflow step that spawns parallel agents
await context.run("parallel-implementation", async () => {
  const agents = [
    { type: "code-reviewer", task: "Review implementation" },
    { type: "test-writer-fixer", task: "Write tests" },
    { type: "documentation-maintainer", task: "Update docs" }
  ];

  // Spawn all agents in parallel
  const results = await Promise.all(
    agents.map(agent =>
      context.call(`agent-${agent.type}`, {
        url: `${POPKIT_CLOUD}/v1/agents/${agent.type}`,
        body: { task: agent.task, context: currentContext }
      })
    )
  );

  return aggregateResults(results);
});
```

---

## Implementation Plan

### Phase 1: Workflow Infrastructure (2-3 weeks)

**Goal:** Add workflow engine without breaking existing functionality.

#### 1.1 File-Based Workflow Engine (Free Tier)

```python
# packages/plugin/hooks/utils/workflow_engine.py

@dataclass
class WorkflowStep:
    id: str
    description: str
    step_type: str  # "skill" | "agent" | "user_decision" | "spawn_agents"
    skill: Optional[str] = None
    agent: Optional[str] = None
    question: Optional[str] = None
    options: Optional[List[dict]] = None
    spawn_agents: Optional[List[dict]] = None
    next: Optional[str] = None
    next_map: Optional[Dict[str, str]] = None  # For user decisions

@dataclass
class WorkflowState:
    workflow_id: str
    current_step: str
    completed_steps: List[str]
    pending_events: Dict[str, Any]
    context: Dict[str, Any]
    created_at: str
    updated_at: str

class FileWorkflowEngine:
    """File-based workflow engine for free tier."""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.state_dir = Path(".claude/popkit/workflows")
        self.state_file = self.state_dir / f"{workflow_id}.json"

    def start_workflow(self, workflow_def: dict) -> WorkflowState:
        """Start a new workflow."""
        state = WorkflowState(
            workflow_id=self.workflow_id,
            current_step=workflow_def["steps"][0]["id"],
            completed_steps=[],
            pending_events={},
            context={},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self._save_state(state)
        return state

    def advance_step(self, step_result: dict) -> Optional[WorkflowStep]:
        """Advance to next step based on result."""
        state = self._load_state()
        current = self._get_step(state.current_step)

        # Determine next step
        if current.next_map and "decision" in step_result:
            next_step_id = current.next_map.get(step_result["decision"])
        else:
            next_step_id = current.next

        if not next_step_id:
            return None  # Workflow complete

        # Update state
        state.completed_steps.append(state.current_step)
        state.current_step = next_step_id
        state.updated_at = datetime.now().isoformat()
        self._save_state(state)

        return self._get_step(next_step_id)

    def wait_for_event(self, event_id: str, timeout_seconds: int = 3600) -> Optional[dict]:
        """Wait for an external event (polling-based)."""
        event_file = self.state_dir / f"{self.workflow_id}.{event_id}.event.json"
        deadline = time.time() + timeout_seconds

        while time.time() < deadline:
            if event_file.exists():
                data = json.loads(event_file.read_text())
                event_file.unlink()  # Clean up
                return data
            time.sleep(1)  # Poll every second

        return None  # Timeout

    def notify_event(self, event_id: str, data: dict) -> None:
        """Notify workflow of an external event."""
        event_file = self.state_dir / f"{self.workflow_id}.{event_id}.event.json"
        event_file.write_text(json.dumps(data))
```

#### 1.2 Upstash Workflow Integration (Pro Tier)

```typescript
// packages/cloud/src/routes/workflows.ts

import { serve } from "@upstash/workflow/cloudflare";

// Generic workflow executor
export const workflowHandler = serve(async (context) => {
  const { workflow_id, workflow_def, initial_context } = context.requestPayload;

  let currentContext = initial_context;

  for (const step of workflow_def.steps) {
    if (step.type === "skill") {
      currentContext = await context.run(`step-${step.id}`, async () => {
        return await invokeSkill(step.skill, currentContext);
      });
    }

    else if (step.type === "agent") {
      currentContext = await context.run(`step-${step.id}`, async () => {
        return await invokeAgent(step.agent, step.task, currentContext);
      });
    }

    else if (step.type === "user_decision") {
      const { eventData, timeout } = await context.waitForEvent(
        step.question,
        `decision-${workflow_id}-${step.id}`,
        { timeout: 3600 }
      );

      if (timeout) {
        return { status: "timeout", step: step.id };
      }

      currentContext = { ...currentContext, decision: eventData };
    }

    else if (step.type === "spawn_agents") {
      const results = await Promise.all(
        step.spawn_agents.map(agent =>
          context.call(`agent-${agent.type}`, {
            url: `${env.POPKIT_CLOUD}/v1/agents/${agent.type}`,
            body: { task: agent.task, context: currentContext }
          })
        )
      );
      currentContext = { ...currentContext, agent_results: results };
    }
  }

  return { status: "complete", context: currentContext };
});
```

#### 1.3 Response Router Hook

```python
# packages/plugin/hooks/utils/response_router.py

def route_user_response(tool_name: str, tool_output: dict) -> None:
    """Route AskUserQuestion responses to workflow engine."""
    if tool_name != "AskUserQuestion":
        return

    answers = tool_output.get("answers", {})
    if not answers:
        return

    # Get active workflow
    tracker = get_tracker()
    workflow_id = tracker.state.workflow_id if tracker.state else None

    if not workflow_id:
        return  # No active workflow

    # Get appropriate engine
    engine = get_workflow_engine(workflow_id)

    # Notify engine of each decision
    for question_id, answer in answers.items():
        engine.notify_event(
            event_id=f"decision-{question_id}",
            data={
                "question_id": question_id,
                "answer": answer,
                "timestamp": datetime.now().isoformat()
            }
        )
```

### Phase 2: Semantic Routing (1-2 weeks)

**Goal:** Add semantic agent/skill selection via Upstash Vector.

#### 2.1 Agent Embedding Index

```typescript
// packages/cloud/src/routes/vector.ts

// Index all agents with their capabilities
async function indexAgents() {
  const agents = await loadAgentDefinitions();

  for (const agent of agents) {
    await vectorIndex.upsert({
      id: agent.name,
      data: `${agent.name}: ${agent.description}. Keywords: ${agent.keywords.join(", ")}`,
      metadata: {
        tier: agent.tier,
        triggers: agent.triggers,
        effort: agent.effort,
        model: agent.model
      }
    });
  }
}

// Semantic agent search
app.post("/v1/agents/search", async (c) => {
  const { query, topK = 3 } = await c.req.json();

  const results = await vectorIndex.query({
    data: query,
    topK,
    includeMetadata: true
  });

  return c.json({
    agents: results.map(r => ({
      name: r.id,
      score: r.score,
      ...r.metadata
    }))
  });
});
```

#### 2.2 Hybrid Routing (Semantic + Keyword)

```python
# packages/plugin/hooks/utils/hybrid_router.py

class HybridRouter:
    """Routes requests using semantic + keyword matching."""

    def __init__(self):
        self.keyword_router = KeywordRouter()  # Existing
        self.vector_client = None  # Lazy init for Upstash

    async def route(self, request: str, context: dict) -> AgentSelection:
        """Select best agent for request."""
        # Try semantic routing first (if available)
        if self._has_vector_access():
            semantic_results = await self._semantic_search(request)
            if semantic_results and semantic_results[0].score > 0.8:
                return AgentSelection(
                    agent=semantic_results[0].id,
                    confidence=semantic_results[0].score,
                    method="semantic"
                )

        # Fall back to keyword routing
        keyword_result = self.keyword_router.route(request, context)
        return AgentSelection(
            agent=keyword_result.agent,
            confidence=keyword_result.confidence,
            method="keyword"
        )
```

### Phase 3: Skill Workflow Definitions (1-2 weeks)

**Goal:** Allow skills to define workflows in their frontmatter.

#### 3.1 Workflow Parser

```python
# packages/plugin/hooks/utils/workflow_parser.py

def parse_skill_workflow(skill_path: Path) -> Optional[dict]:
    """Parse workflow definition from skill frontmatter."""
    content = skill_path.read_text()

    # Extract frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            return frontmatter.get("workflow")

    return None

def validate_workflow(workflow: dict) -> List[str]:
    """Validate workflow definition."""
    errors = []

    if "id" not in workflow:
        errors.append("Workflow must have an 'id'")

    if "steps" not in workflow or not workflow["steps"]:
        errors.append("Workflow must have at least one step")

    step_ids = {s["id"] for s in workflow["steps"]}
    for step in workflow["steps"]:
        if step.get("next") and step["next"] not in step_ids:
            errors.append(f"Step '{step['id']}' references unknown step '{step['next']}'")

    return errors
```

#### 3.2 Workflow Invocation

```python
# packages/plugin/hooks/pre-tool-use.py

def handle_skill_invocation(tool_input: dict) -> dict:
    """Handle Skill tool invocation with workflow support."""
    skill_name = tool_input.get("skill", "")

    # Load skill
    skill_path = find_skill(skill_name)
    workflow = parse_skill_workflow(skill_path)

    if workflow:
        # Start workflow
        engine = get_workflow_engine()
        workflow_id = f"{workflow['id']}-{uuid4().hex[:8]}"

        engine.start_workflow(workflow_id, workflow)

        # Store workflow ID in skill state
        tracker = get_tracker()
        tracker.start_skill(skill_name, workflow_id=workflow_id)

        return {
            "decision": "allow",
            "workflow_started": workflow_id
        }

    # Normal skill invocation (no workflow)
    tracker = get_tracker()
    tracker.start_skill(skill_name)
    return {"decision": "allow"}
```

### Phase 4: Integration & Polish (1-2 weeks)

#### 4.1 Status Line Integration

```python
# packages/plugin/hooks/notification.py

def update_workflow_status(workflow_id: str):
    """Update status line with workflow progress."""
    engine = get_workflow_engine()
    state = engine.get_state(workflow_id)

    if not state:
        return

    progress = len(state.completed_steps) / len(state.all_steps) * 100

    return {
        "statusLine": f"Workflow: {state.current_step} ({progress:.0f}%)",
        "details": {
            "workflow_id": workflow_id,
            "current_step": state.current_step,
            "completed": state.completed_steps,
            "progress": progress
        }
    }
```

#### 4.2 Error Recovery

```python
# packages/plugin/hooks/utils/workflow_recovery.py

class WorkflowRecovery:
    """Handle workflow errors and recovery."""

    def handle_step_error(self, workflow_id: str, step_id: str, error: str):
        """Handle error in workflow step."""
        engine = get_workflow_engine()
        state = engine.get_state(workflow_id)

        # Record error
        state.errors.append({
            "step": step_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

        # Check retry policy
        step = engine.get_step(workflow_id, step_id)
        if step.retry_count < step.max_retries:
            # Retry step
            step.retry_count += 1
            return {"action": "retry", "step": step_id}

        # Check fallback
        if step.fallback_step:
            return {"action": "fallback", "step": step.fallback_step}

        # Escalate to user
        return {"action": "escalate", "error": error}
```

---

## Migration Strategy

### Backward Compatibility

1. **Existing skills work unchanged** - No workflow = normal behavior
2. **Existing hooks work unchanged** - Orchestration is additive
3. **Existing commands work unchanged** - `/popkit:*` commands preserved

### Gradual Rollout

1. **Week 1-2:** File-based workflow engine (internal testing)
2. **Week 3-4:** Upstash Workflow integration (Pro beta)
3. **Week 5-6:** Semantic routing (all tiers)
4. **Week 7-8:** Skill workflow definitions (documentation + examples)

### Feature Flags

```python
# packages/plugin/hooks/utils/feature_flags.py

FEATURES = {
    "workflow_engine": {
        "file_based": True,      # Always available
        "upstash": "pro",        # Pro tier
    },
    "semantic_routing": {
        "enabled": True,         # All tiers (with rate limits)
        "fallback": "keyword"    # Fallback to keyword routing
    },
    "skill_workflows": {
        "enabled": False,        # Disabled until Phase 3 complete
    }
}
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Workflow complexity** | Medium | High | Clear documentation, simple defaults, escape hatches |
| **Performance overhead** | Low | Medium | Async execution, caching, lazy loading |
| **Upstash dependency** | Low | Medium | File-based fallback always available |
| **Breaking changes** | Low | High | Backward compatibility as primary constraint |
| **User confusion** | Medium | Medium | Clear migration guides, opt-in for new features |
| **State corruption** | Low | High | Atomic writes, validation, recovery procedures |

---

## Conclusion

### What We're NOT Changing

1. **Tiered agent loading** - It works well, keep it
2. **Skill/hook architecture** - Sound foundation
3. **Claude Code integration** - Leverage native features

### What We're Adding

1. **Workflow orchestration layer** - For skill chaining and multi-step workflows
2. **Semantic routing** - For intelligent agent selection
3. **Response routing** - For AskUserQuestion → workflow integration
4. **Background agent spawning** - For parallel execution

### Key Insights

1. **Tiers ≠ Orchestration** - The tiered loading is for context efficiency, not workflow orchestration. These are separate concerns.

2. **Hooks can't orchestrate** - They're reactive, not proactive. Orchestration must happen at a higher level.

3. **Two engines are better than one** - Upstash Workflow for cloud/durable, file-based for local/free.

4. **Semantic routing complements keywords** - Use both, not either/or.

5. **Skills should define workflows** - Declarative workflow definitions in skill frontmatter.

### Next Steps

1. **Create Issue #206:** Workflow Engine Implementation (Phase 1)
2. **Create Issue #207:** Semantic Routing Integration (Phase 2)
3. **Create Issue #208:** Skill Workflow Definitions (Phase 3)
4. **Update Issue #205:** Link to this research document

---

**Document Version:** 1.0
**Author:** Claude Code (orchestration research)
**Last Updated:** 2025-12-12
