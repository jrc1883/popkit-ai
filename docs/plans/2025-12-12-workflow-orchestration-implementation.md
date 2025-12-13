# Workflow Orchestration System - Implementation Plan

**Date:** 2025-12-12
**Status:** Ready for Implementation
**Research:** [2025-12-12-orchestration-architecture-evaluation.md](../research/2025-12-12-orchestration-architecture-evaluation.md)
**Parent Issues:** #205 (Research), #173 (Skill Automation), #115 (Intelligent Orchestration Epic)

---

## Executive Summary

Implement a **programmatic workflow orchestration layer** that enables:
1. Skills to define multi-step workflows
2. AskUserQuestion responses to route to workflow steps
3. Parallel agent spawning from workflows
4. Cross-session workflow persistence

**Key Insight:** The tiered agent structure is correct for context efficiency. The gap is a workflow orchestration layer that chains skills programmatically.

---

## Architecture Decision

After comprehensive research ([see full analysis](../research/2025-12-12-orchestration-architecture-evaluation.md)), the recommendation is:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Keep tiered agents? | **YES** | Works well for context efficiency |
| Add workflow layer? | **YES** | Missing capability for skill chaining |
| Workflow backend | **Dual: File + Upstash** | File for free tier, Upstash for Pro |
| Response routing | **PostToolUse hook** | Can intercept AskUserQuestion responses |
| Semantic routing | **Upstash Vector** | Enhances agent selection |

---

## Implementation Phases

### Phase 1: File-Based Workflow Engine (Free Tier Foundation)

**Goal:** Zero-dependency workflow engine for all users.

**New Files:**
```
packages/plugin/hooks/utils/
├── workflow_engine.py       # Core workflow state machine
├── workflow_parser.py       # Parse workflow definitions from YAML
└── response_router.py       # Route AskUserQuestion responses
```

**Implementation:**

```python
# workflow_engine.py - Core classes
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
    next_map: Optional[Dict[str, str]] = None

@dataclass
class WorkflowState:
    workflow_id: str
    workflow_name: str
    current_step: str
    completed_steps: List[str]
    pending_events: Dict[str, Any]
    context: Dict[str, Any]
    created_at: str
    updated_at: str
    status: str  # "running" | "waiting" | "complete" | "error"

class FileWorkflowEngine:
    """File-based workflow engine using .claude/popkit/workflows/"""

    def start_workflow(self, workflow_def: dict, initial_context: dict) -> WorkflowState
    def get_current_step(self) -> Optional[WorkflowStep]
    def advance_step(self, step_result: dict) -> Optional[WorkflowStep]
    def wait_for_event(self, event_id: str) -> None  # Sets status to "waiting"
    def notify_event(self, event_id: str, data: dict) -> None
    def get_state(self) -> WorkflowState
```

**File Structure:**
```
.claude/popkit/workflows/
├── feature-dev-abc123.json    # Workflow state
├── feature-dev-abc123.events/ # Pending events
│   └── decision-approach.json
└── feature-dev-abc123.log     # Workflow history
```

**Deliverables:**
- [ ] `workflow_engine.py` - State machine implementation
- [ ] `workflow_parser.py` - YAML frontmatter parser for workflow definitions
- [ ] `response_router.py` - AskUserQuestion response routing
- [ ] Integration with `post-tool-use.py` hook
- [ ] Unit tests for workflow engine

**Acceptance Criteria:**
- [ ] Workflows can be started, advanced, and completed
- [ ] State persists across Claude Code sessions
- [ ] AskUserQuestion responses route to correct workflow step
- [ ] Works without any cloud dependencies

---

### Phase 2: Skill Workflow Definitions

**Goal:** Skills can declare workflows in their frontmatter.

**New YAML Schema:**

```yaml
# SKILL.md frontmatter
---
name: pop-feature-dev
description: 7-phase feature development workflow
triggers:
  - "implement feature"
  - "build feature"

workflow:
  id: feature-development
  version: 1
  steps:
    - id: discovery
      description: "Understand requirements and constraints"
      type: skill
      skill: pop-research-analyze
      next: exploration

    - id: exploration
      description: "Explore existing codebase patterns"
      type: agent
      agent: code-explorer
      next: approach_decision

    - id: approach_decision
      description: "Clarify implementation approach with user"
      type: user_decision
      question: "Which implementation approach should we use?"
      header: "Approach"
      options:
        - id: minimal
          label: "Minimal"
          description: "Quick implementation, basic functionality"
          next: implement_minimal
        - id: comprehensive
          label: "Comprehensive"
          description: "Full implementation with tests and docs"
          next: implement_comprehensive
        - id: research_more
          label: "Research more"
          description: "Need more exploration first"
          next: exploration

    - id: implement_minimal
      description: "Basic implementation"
      type: skill
      skill: pop-quick-implement
      next: review

    - id: implement_comprehensive
      description: "Full implementation with parallel agents"
      type: spawn_agents
      agents:
        - type: code-reviewer
          task: "Review implementation as it's built"
        - type: test-writer-fixer
          task: "Write tests for new functionality"
      wait_for: all
      next: review

    - id: review
      description: "Final code review"
      type: agent
      agent: code-reviewer
      next: complete

    - id: complete
      description: "Workflow complete"
      type: terminal
---
```

**Deliverables:**
- [ ] JSON Schema for workflow definitions
- [ ] Workflow validator (in `workflow_parser.py`)
- [ ] Update skill loader to extract workflow definitions
- [ ] Add workflow definitions to 5 key skills:
  - `pop-feature-dev`
  - `pop-brainstorming` → `pop-writing-plans`
  - `pop-project-analyze`
  - `pop-debug-complex`
  - `pop-security-audit`

**Acceptance Criteria:**
- [ ] Valid workflow definitions parse correctly
- [ ] Invalid definitions produce helpful error messages
- [ ] Workflow steps can be any of: skill, agent, user_decision, spawn_agents, terminal
- [ ] Options in user_decision map to specific next steps

---

### Phase 3: Response Router Integration

**Goal:** AskUserQuestion responses automatically advance workflows.

**Hook Integration:**

```python
# hooks/post-tool-use.py - Add response routing

def handle_tool_output(tool_name: str, tool_output: dict):
    # ... existing code ...

    # NEW: Route AskUserQuestion responses
    if tool_name == "AskUserQuestion":
        route_user_response(tool_output)

def route_user_response(tool_output: dict):
    """Route AskUserQuestion response to active workflow."""
    from workflow_engine import get_active_workflow

    workflow = get_active_workflow()
    if not workflow:
        return  # No active workflow, normal behavior

    current_step = workflow.get_current_step()
    if current_step.step_type != "user_decision":
        return  # Not waiting for a decision

    # Extract answer
    answers = tool_output.get("answers", {})
    if not answers:
        return

    # Find matching option
    for header, answer in answers.items():
        if header.lower() == current_step.header.lower():
            # Determine next step from answer
            next_step = None
            for option in current_step.options:
                if option["label"].lower() == answer.lower():
                    next_step = option.get("next")
                    break

            if next_step:
                # Advance workflow
                workflow.advance_step({"decision": answer, "next": next_step})

                # Return guidance to Claude
                return {
                    "message": f"Workflow advancing to: {next_step}",
                    "workflow_context": workflow.get_state().context
                }
```

**Deliverables:**
- [ ] Response routing in `post-tool-use.py`
- [ ] Workflow state updates on user decisions
- [ ] Context injection for next skill/agent
- [ ] Logging of workflow transitions

**Acceptance Criteria:**
- [ ] User selecting an option advances the workflow
- [ ] Next skill/agent receives context from previous steps
- [ ] Workflow history shows decision audit trail
- [ ] Invalid responses handled gracefully

---

### Phase 4: Upstash Workflow Integration (Pro Tier)

**Goal:** Durable workflows with cloud persistence and advanced features.

**Cloud API Routes:**

```typescript
// packages/cloud/src/routes/workflows.ts

import { serve } from "@upstash/workflow/cloudflare";

// Start a workflow
app.post("/v1/workflows", async (c) => {
  const { workflow_def, initial_context, user_id } = await c.req.json();

  // Validate entitlement
  if (!await hasProEntitlement(user_id)) {
    return c.json({ error: "Pro tier required for cloud workflows" }, 403);
  }

  // Start Upstash Workflow
  const workflowRun = await workflowClient.trigger({
    url: `${env.WORKER_URL}/v1/workflows/execute`,
    body: { workflow_def, initial_context }
  });

  return c.json({
    workflow_id: workflowRun.workflowRunId,
    status: "started"
  });
});

// Workflow executor
export const workflowExecutor = serve(async (context) => {
  const { workflow_def, initial_context } = context.requestPayload;

  let currentContext = initial_context;

  for (const step of workflow_def.steps) {
    if (step.type === "user_decision") {
      // Wait for user input via event
      const { eventData, timeout } = await context.waitForEvent(
        step.question,
        `decision-${context.workflowRunId}-${step.id}`,
        { timeout: "24h" }
      );

      if (timeout) {
        return { status: "timeout", step: step.id };
      }

      // Route based on decision
      const selectedOption = step.options.find(
        o => o.label.toLowerCase() === eventData.answer.toLowerCase()
      );
      currentContext = { ...currentContext, decision: eventData };
      // Continue to selectedOption.next
    }

    else if (step.type === "spawn_agents") {
      // Parallel agent execution
      const results = await Promise.all(
        step.agents.map(agent =>
          context.call(`agent-${agent.type}`, {
            url: `${env.WORKER_URL}/v1/agents/${agent.type}`,
            body: { task: agent.task, context: currentContext }
          })
        )
      );
      currentContext = { ...currentContext, agent_results: results };
    }
  }

  return { status: "complete", context: currentContext };
});

// Notify workflow of user decision
app.post("/v1/workflows/:id/events", async (c) => {
  const { id } = c.req.param();
  const { event_id, data } = await c.req.json();

  await workflowClient.notify({
    eventId: event_id,
    eventData: data
  });

  return c.json({ status: "notified" });
});
```

**Plugin Integration:**

```python
# hooks/utils/workflow_engine.py

class UpstashWorkflowEngine:
    """Cloud-backed workflow engine for Pro tier."""

    def __init__(self, api_client):
        self.client = api_client

    def start_workflow(self, workflow_def: dict, context: dict) -> str:
        """Start a cloud workflow, return workflow ID."""
        response = self.client.post("/v1/workflows", {
            "workflow_def": workflow_def,
            "initial_context": context
        })
        return response["workflow_id"]

    def notify_decision(self, workflow_id: str, event_id: str, answer: str):
        """Send user decision to cloud workflow."""
        self.client.post(f"/v1/workflows/{workflow_id}/events", {
            "event_id": event_id,
            "data": {"answer": answer}
        })

    def get_status(self, workflow_id: str) -> dict:
        """Get workflow status from cloud."""
        return self.client.get(f"/v1/workflows/{workflow_id}")

def get_workflow_engine():
    """Factory: Return appropriate engine based on tier."""
    from premium_checker import is_pro_tier

    if is_pro_tier():
        from cloud_client import get_cloud_client
        return UpstashWorkflowEngine(get_cloud_client())
    else:
        return FileWorkflowEngine()
```

**Deliverables:**
- [ ] Upstash Workflow integration in `packages/cloud/`
- [ ] `UpstashWorkflowEngine` class in plugin
- [ ] Engine factory for tier-based selection
- [ ] Cloud API routes for workflow management
- [ ] Event notification endpoint

**Acceptance Criteria:**
- [ ] Pro users get cloud-backed durable workflows
- [ ] Free users fall back to file-based workflows
- [ ] Workflows survive Claude Code session restarts
- [ ] `waitForEvent` works for user decisions

---

### Phase 5: Semantic Routing Enhancement

**Goal:** Intelligent agent/skill selection via embeddings.

**Components:**

```python
# hooks/utils/semantic_router.py - Enhanced version

class SemanticRouter:
    """Route requests using semantic similarity + keyword fallback."""

    def __init__(self):
        self.vector_client = None  # Lazy init
        self.keyword_router = KeywordRouter()

    async def route(self, request: str, context: dict) -> RouteResult:
        """Select best agent/skill for request."""

        # Try semantic routing first (if Pro tier)
        if self._has_vector_access():
            results = await self._semantic_search(request, top_k=3)
            if results and results[0].score > 0.85:
                return RouteResult(
                    target=results[0].id,
                    confidence=results[0].score,
                    method="semantic"
                )

        # Fall back to keyword routing
        keyword_result = self.keyword_router.route(request, context)
        return RouteResult(
            target=keyword_result.agent,
            confidence=keyword_result.confidence,
            method="keyword"
        )

    async def _semantic_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Search agent/skill embeddings."""
        return await self.vector_client.query(
            data=query,
            top_k=top_k,
            include_metadata=True
        )
```

**Agent/Skill Embedding Index:**

```python
# scripts/build_semantic_index.py

def build_agent_index():
    """Build semantic index of all agents and skills."""
    index = []

    # Index agents
    for tier in ["tier-1-always-active", "tier-2-on-demand"]:
        for agent_dir in (AGENTS_DIR / tier).iterdir():
            if (agent_dir / "AGENT.md").exists():
                content = (agent_dir / "AGENT.md").read_text()
                index.append({
                    "id": f"agent:{agent_dir.name}",
                    "type": "agent",
                    "content": extract_description(content),
                    "metadata": {
                        "tier": tier,
                        "keywords": extract_keywords(content)
                    }
                })

    # Index skills
    for skill_dir in SKILLS_DIR.iterdir():
        if (skill_dir / "SKILL.md").exists():
            content = (skill_dir / "SKILL.md").read_text()
            index.append({
                "id": f"skill:{skill_dir.name}",
                "type": "skill",
                "content": extract_description(content),
                "metadata": {
                    "triggers": extract_triggers(content),
                    "has_workflow": has_workflow(content)
                }
            })

    return index
```

**Deliverables:**
- [ ] Enhanced `semantic_router.py`
- [ ] Agent/skill embedding index builder
- [ ] Upstash Vector integration
- [ ] Hybrid routing (semantic + keyword)

**Acceptance Criteria:**
- [ ] Semantic search finds relevant agents/skills
- [ ] Falls back to keyword routing gracefully
- [ ] Index updates when agents/skills change
- [ ] Pro users get semantic routing, free users get keyword

---

## GitHub Issues to Create

Based on this plan, create the following issues:

### Issue #206: File-Based Workflow Engine
**Labels:** `enhancement`, `plugin`, `hooks`, `phase:now`
**Priority:** P1-high

### Issue #207: Skill Workflow Definitions
**Labels:** `enhancement`, `plugin`, `skills`, `phase:now`
**Priority:** P1-high
**Blocked by:** #206

### Issue #208: Response Router Integration
**Labels:** `enhancement`, `hooks`, `phase:now`
**Priority:** P1-high
**Blocked by:** #206

### Issue #209: Upstash Workflow Integration
**Labels:** `enhancement`, `cloud`, `premium`, `phase:next`
**Priority:** P2-medium
**Blocked by:** #206, #208

### Issue #210: Semantic Routing Enhancement
**Labels:** `enhancement`, `hooks`, `cloud`, `phase:next`
**Priority:** P2-medium

### Update Issue #205
Link to this plan and the research document.

---

## Migration & Compatibility

### Backward Compatibility

| Component | Impact |
|-----------|--------|
| Existing skills | **None** - Skills without workflow definitions work unchanged |
| Existing hooks | **None** - New routing is additive |
| Existing commands | **None** - Commands work as before |
| Existing config.json | **None** - Workflows in skills, not config |

### Gradual Rollout

1. **Week 1-2:** File-based engine + 2 skill workflows
2. **Week 3-4:** Response router + remaining skill workflows
3. **Week 5-6:** Upstash integration (Pro beta)
4. **Week 7-8:** Semantic routing + polish

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Token reduction | 30% for workflow tasks | Compare before/after on same task |
| Response time | 2x faster for deterministic flows | Measure end-to-end time |
| Workflow completion | 80% workflows complete successfully | Track workflow status |
| User satisfaction | Positive feedback on `/popkit:dev` | User surveys |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Workflow complexity | Medium | High | Simple defaults, escape hatches |
| State corruption | Low | High | Atomic writes, validation, recovery |
| Hook limitations | Low | Medium | Design within Claude Code constraints |
| User confusion | Medium | Medium | Clear docs, gradual introduction |

---

## Next Steps

1. **Approve this plan** - Review and confirm approach
2. **Create GitHub issues** - #206-#210 with proper PopKit Guidance
3. **Start Phase 1** - File-based workflow engine
4. **Update research issue #205** - Link to this plan

---

*This plan synthesizes research from orchestration-architecture-evaluation.md and aligns with existing issues #173, #205, and #115.*
