# PopKit Self-Testing Framework - Architecture Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BENCHMARK RUNNER                            │
│                  (packages/benchmarks/src/runner.ts)                │
│                                                                     │
│  CLI: npm run benchmark -- bouncing-balls --record-behavior        │
│       │                                                             │
│       ├─▶ Sets TEST_MODE=true                                      │
│       ├─▶ Sets TEST_SESSION_ID={uuid}                              │
│       └─▶ Spawns Claude Code subprocess                            │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
    ┌─────────────────────┐   ┌─────────────────────┐
    │  CLAUDE CODE        │   │  BEHAVIOR CAPTURE   │
    │  SUBPROCESS         │   │  SERVICE            │
    │                     │   │                     │
    │  - Hooks execute    │──▶│  - Listens to       │
    │  - Emit telemetry   │   │    stdout           │
    │  - TELEMETRY:{...}  │   │  - Parses events    │
    └─────────────────────┘   │  - Aggregates data  │
                              └──────────┬──────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  behavior.json      │
                              │                     │
                              │  {                  │
                              │    routing: [...],  │
                              │    agents: [...],   │
                              │    skills: [...]    │
                              │  }                  │
                              └──────────┬──────────┘
                                         │
                ┌────────────────────────┴────────────────────────┐
                │                                                  │
                ▼                                                  ▼
    ┌─────────────────────┐                         ┌─────────────────────┐
    │  EXPECTATIONS       │                         │  VALIDATOR          │
    │                     │                         │                     │
    │  {task}.            │────────────────────────▶│  - Compare actual   │
    │  expectations.json  │                         │    vs expected      │
    │                     │                         │  - Generate         │
    │  - shouldInvoke     │                         │    violations       │
    │  - shouldNotInvoke  │                         │  - Calculate score  │
    │  - patterns         │                         └──────────┬──────────┘
    └─────────────────────┘                                    │
                                                               ▼
                                                    ┌─────────────────────┐
                                                    │  VALIDATION RESULT  │
                                                    │                     │
                                                    │  {                  │
                                                    │    passed: false,   │
                                                    │    score: 65/100,   │
                                                    │    violations: [...] │
                                                    │  }                  │
                                                    └──────────┬──────────┘
                                                               │
                                                               ▼
                                                    ┌─────────────────────┐
                                                    │  REPORT GENERATOR   │
                                                    │                     │
                                                    │  - Format markdown  │
                                                    │  - Add insights     │
                                                    │  - Recommendations  │
                                                    └──────────┬──────────┘
                                                               │
                                                               ▼
                                                    ┌─────────────────────┐
                                                    │ behavior-report.md  │
                                                    │                     │
                                                    │ What DID happen     │
                                                    │ What SHOULD happen  │
                                                    │ Gap analysis        │
                                                    └─────────────────────┘
```

## Telemetry Emission Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLAUDE CODE EXECUTION                        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ User prompt arrives
                                    ▼
                    ┌───────────────────────────────┐
                    │  user-prompt-submit.py        │
                    │                               │
                    │  if is_test_mode():           │
                    │    emit_event(...)            │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  agent-orchestrator.py        │
                    │  (PreToolUse hook)            │
                    │                               │
                    │  1. Analyze prompt            │
                    │  2. Route to agents           │
                    │  3. emit_routing_decision()   │──┐
                    └───────────────┬───────────────┘  │
                                    │                  │
                                    ▼                  │
                    ┌───────────────────────────────┐  │
                    │  Task tool invoked            │  │
                    │  (Agent execution starts)     │  │
                    │                               │  │
                    │  emit_agent_invocation()      │──┤
                    └───────────────┬───────────────┘  │
                                    │                  │
                                    ▼                  │
                    ┌───────────────────────────────┐  │
                    │  Skill tool invoked           │  │
                    │                               │  │
                    │  skill_state.py:              │  │
                    │    start_skill()              │  │
                    │    emit_skill_start()         │──┤
                    └───────────────┬───────────────┘  │
                                    │                  │
                                    ▼                  │
                    ┌───────────────────────────────┐  │
                    │  Skill executes               │  │
                    │  - Uses tools                 │  │
                    │  - Makes decisions            │  │
                    │  - Completes or errors        │  │
                    │                               │  │
                    │  emit_skill_complete()        │──┤
                    └───────────────┬───────────────┘  │
                                    │                  │
                                    ▼                  │
                    ┌───────────────────────────────┐  │
                    │  Workflow phase change        │  │
                    │  (if multi-phase workflow)    │  │
                    │                               │  │
                    │  emit_phase_transition()      │──┤
                    └───────────────┬───────────────┘  │
                                    │                  │
                                    ▼                  │
                    ┌───────────────────────────────┐  │
                    │  Agent completes              │  │
                    │                               │  │
                    │  emit_agent_completion()      │──┤
                    └───────────────────────────────┘  │
                                                       │
                    All events written to stdout       │
                    as TELEMETRY:{json}                │
                                                       │
                    ┌──────────────────────────────────┘
                    │
                    ▼
            ┌───────────────────────┐
            │  BehaviorCapture      │
            │  Service              │
            │                       │
            │  Aggregates all       │
            │  events into          │
            │  behavior.json        │
            └───────────────────────┘
```

## Data Flow: Hook to Report

```
┌──────────────────────────────────────────────────────────────────────┐
│ 1. HOOK EXECUTION                                                    │
└──────────────────────────────────────────────────────────────────────┘

agent-orchestrator.py:
  routing_decision = {
    trigger: { type: "keyword", value: "canvas", confidence: 75 },
    candidates: [
      { agent: "ui-designer", score: 3, matched: ["canvas", "ui", "animation"] }
    ],
    selected: ["ui-designer"]
  }

  emit_routing_decision(routing_decision)
      │
      └─▶ print("TELEMETRY:" + json.dumps(event))

                            ▼

┌──────────────────────────────────────────────────────────────────────┐
│ 2. CAPTURE SERVICE                                                   │
└──────────────────────────────────────────────────────────────────────┘

BehaviorCaptureService.processLine():
  if line.startsWith("TELEMETRY:"):
    event = JSON.parse(line.substring(10))
    this.events.push(event)

                            ▼

┌──────────────────────────────────────────────────────────────────────┐
│ 3. AGGREGATION                                                       │
└──────────────────────────────────────────────────────────────────────┘

buildBehaviorCapture():
  behavior = {
    routing: {
      decisions: events.filter(e => e.type === 'routing_decision'),
      agentsSelected: [...unique agents...]
    },
    agents: {
      invocations: events.filter(e => e.type === 'agent_invocation_start'),
      totalInvoked: count
    }
  }

                            ▼

┌──────────────────────────────────────────────────────────────────────┐
│ 4. VALIDATION                                                        │
└──────────────────────────────────────────────────────────────────────┘

BehaviorValidator.validateAgents():
  expected: ["ui-designer", "rapid-prototyper"]
  actual: []

  violation = {
    category: "agent",
    severity: "critical",
    message: "Expected agents not invoked: ui-designer, rapid-prototyper",
    expected: ["ui-designer", "rapid-prototyper"],
    actual: [],
    impact: "Canvas animation is a frontend UI task"
  }

                            ▼

┌──────────────────────────────────────────────────────────────────────┐
│ 5. REPORT GENERATION                                                 │
└──────────────────────────────────────────────────────────────────────┘

generateReport():
  # PopKit Behavior Validation Report

  **Score**: 65/100
  **Status**: ❌ FAILED

  ## Violations
  ### CRITICAL
  - **agent**: Expected agents not invoked: ui-designer, rapid-prototyper
    - Expected: ["ui-designer", "rapid-prototyper"]
    - Actual: []
    - Impact: Canvas animation is a frontend UI task

  ## Recommendations
  1. Fix agent routing for frontend tasks
  2. Add "canvas|animation" to routing keywords
```

## Validation Decision Tree

```
┌─────────────────────────┐
│ For each expectation    │
└────────────┬────────────┘
             │
             ▼
    ┌────────────────────┐
    │ Agent Expectations │
    └────────┬───────────┘
             │
             ├─▶ shouldInvoke?
             │   │
             │   ├─▶ Check actual.agents.agentsSelected
             │   │
             │   ├─▶ Missing agents?
             │   │   ├─▶ required=true  → CRITICAL violation
             │   │   └─▶ required=false → MAJOR violation
             │   │
             │   └─▶ All present → ✅ PASS
             │
             ├─▶ shouldNotInvoke?
             │   │
             │   ├─▶ Check actual.agents.agentsSelected
             │   │
             │   ├─▶ Unexpected agents?
             │   │   └─▶ MAJOR violation
             │   │
             │   └─▶ None present → ✅ PASS
             │
             └─▶ invocationCount?
                 │
                 ├─▶ exact? → actual === expected
                 ├─▶ min?   → actual >= min
                 └─▶ max?   → actual <= max
                     │
                     ├─▶ Out of range → MINOR violation
                     └─▶ In range     → ✅ PASS

    ┌────────────────────┐
    │ Skill Expectations │
    └────────┬───────────┘
             │
             ├─▶ shouldInvoke?
             │   └─▶ [same logic as agents]
             │
             └─▶ shouldNotInvoke?
                 └─▶ [same logic as agents]

    ┌────────────────────┐
    │ Tool Expectations  │
    └────────┬───────────┘
             │
             ├─▶ expectedPatterns?
             │   │
             │   ├─▶ Check actual.tools.patterns
             │   │
             │   ├─▶ Pattern found?
             │   │   └─▶ Count >= minOccurrences → ✅ PASS
             │   │
             │   └─▶ Pattern not found → MINOR violation
             │
             └─▶ forbiddenPatterns?
                 │
                 ├─▶ Check actual.tools.patterns
                 │
                 ├─▶ Pattern found?
                 │   └─▶ CRITICAL violation
                 │
                 └─▶ Pattern not found → ✅ PASS

    ┌──────────────────────────┐
    │ Workflow Expectations    │
    └────────┬─────────────────┘
             │
             └─▶ [similar logic for workflow activation]

    ┌──────────────────────────┐
    │ Performance Expectations │
    └────────┬─────────────────┘
             │
             └─▶ Check timing thresholds
                 └─▶ Exceeded? → MINOR violation
```

## Score Calculation

```
Initial Score: 100

For each violation:
  ├─▶ CRITICAL: -30 points
  ├─▶ MAJOR:    -15 points
  └─▶ MINOR:    -5 points

For each warning: -3 points

Final Score: max(0, score)

Example:
  Start:          100
  - 1 CRITICAL:   -30  (70)
  - 1 MAJOR:      -15  (55)
  - 2 MINOR:      -10  (45)
  - 3 warnings:   -9   (36)
  ──────────────────────
  Final:          36/100 ❌ FAIL
```

## File Structure

```
packages/
├─ plugin/
│  └─ hooks/
│     ├─ agent-orchestrator.py          [MODIFIED: emit telemetry]
│     └─ utils/
│        ├─ skill_state.py               [MODIFIED: already has telemetry!]
│        └─ test_telemetry.py            [NEW: telemetry emission]
│
└─ benchmarks/
   ├─ src/
   │  ├─ runner.ts                       [MODIFIED: add --record-behavior]
   │  ├─ behavior/
   │  │  ├─ capture.ts                   [NEW: capture service]
   │  │  └─ schema.ts                    [NEW: data schemas]
   │  ├─ validator/
   │  │  ├─ validator.ts                 [NEW: validation engine]
   │  │  └─ expectations.ts              [NEW: expectation types]
   │  └─ reports/
   │     └─ behavior-report.ts           [NEW: report generator]
   │
   ├─ tasks/
   │  ├─ bouncing-balls.json             [EXISTING]
   │  ├─ bouncing-balls.expectations.json [NEW: behavior expectations]
   │  └─ hello-world.expectations.json   [NEW: simple task expectations]
   │
   └─ results/
      └─ {task-id}/
         └─ {mode}/
            ├─ session.json              [EXISTING: output quality]
            ├─ behavior.json             [NEW: behavior data]
            └─ behavior-report.md        [NEW: validation report]
```

## Event Timeline Example

```
Time  | Event                    | Source                | Data
------+--------------------------+-----------------------+------------------------
0ms   | routing_decision         | agent-orchestrator.py | trigger: "canvas UI"
      |                          |                       | selected: ["ui-designer"]
------+--------------------------+-----------------------+------------------------
50ms  | agent_invocation_start   | agent-orchestrator.py | agent: "ui-designer"
      |                          |                       | prompt: "Create canvas..."
------+--------------------------+-----------------------+------------------------
100ms | skill_start              | skill_state.py        | skill: "pop-verify-completion"
      |                          |                       | invoked_by: "agent"
------+--------------------------+-----------------------+------------------------
150ms | tool_call                | (captured separately) | tool: "Write"
      |                          |                       | file: "balls.js"
------+--------------------------+-----------------------+------------------------
200ms | tool_call                | (captured separately) | tool: "Bash"
      |                          |                       | command: "node --check balls.js"
------+--------------------------+-----------------------+------------------------
250ms | skill_complete           | skill_state.py        | skill: "pop-verify-completion"
      |                          |                       | duration: 150ms
      |                          |                       | tool_calls: 3
------+--------------------------+-----------------------+------------------------
300ms | agent_invocation_complete| agent-orchestrator.py | agent: "ui-designer"
      |                          |                       | duration: 250ms
      |                          |                       | exit_code: 0
------+--------------------------+-----------------------+------------------------

All events aggregated into behavior.json:
{
  "routing": { "decisions": [event at 0ms] },
  "agents": { "invocations": [events at 50ms, 300ms] },
  "skills": { "executions": [events at 100ms, 250ms] },
  "tools": { "calls": [events at 150ms, 200ms] }
}
```

---

**Visual Guide Complete**
**See**: [self-testing-framework-design.md](./self-testing-framework-design.md) for full specification
