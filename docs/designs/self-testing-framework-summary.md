# PopKit Self-Testing Framework - Executive Summary

**Issue**: #258
**Full Design**: [self-testing-framework-design.md](./self-testing-framework-design.md)
**Status**: Design Complete - Ready for Implementation

## The Problem

PopKit validates **output quality** (does the code work?) but not **orchestration behavior** (did PopKit actually orchestrate agents?).

**Real Example**:
- Bouncing balls benchmark: PopKit's code worked, vanilla's was broken
- Both got similar quality scores (7/10)
- PopKit didn't invoke design agents despite frontend task
- We had no way to detect this orchestration failure

## The Solution

A behavior recording and validation system that:

1. **Captures** agent routing, skill invocations, workflow phases during benchmarks
2. **Compares** actual behavior against expected behavior specifications
3. **Reports** gaps, violations, and recommendations

## How It Works

```
Benchmark Run (--record-behavior)
    │
    ├─▶ Hooks emit telemetry events (TELEMETRY:{...json...})
    │    - Agent routing decisions
    │    - Skill executions
    │    - Workflow phase changes
    │
    ├─▶ Capture service aggregates into behavior.json
    │
    ├─▶ Validator compares against expectations
    │
    └─▶ Generates behavior-report.md
         ✅ PASS / ❌ FAIL + detailed analysis
```

## Key Components

### 1. Test Telemetry (`hooks/utils/test_telemetry.py`)
- Zero-overhead event emission when `TEST_MODE=true`
- Events: `routing_decision`, `agent_invocation`, `skill_start`, `phase_transition`
- JSONL format to stdout: `TELEMETRY:{...}`

### 2. Behavior Capture (`benchmarks/src/behavior/capture.ts`)
- Listens to subprocess stdout for telemetry events
- Aggregates into structured `behavior.json`
- Tracks: routing, agents, skills, workflows, tools, decisions, performance

### 3. Expectations Spec (`tasks/{task-id}.expectations.json`)
- Define what SHOULD happen for each benchmark
- Example: "bouncing-balls should invoke ui-designer agent"
- Supports required (MUST) and optional (SHOULD) expectations

### 4. Validator (`benchmarks/src/validator/validator.ts`)
- Compares actual behavior vs expectations
- Generates violations (critical/major/minor)
- Calculates behavior score (0-100)

### 5. Report Generator (`benchmarks/src/reports/behavior-report.ts`)
- Comprehensive markdown report
- What happened vs what should have happened
- Gap analysis and recommendations

## Example Expectation File

```json
{
  "taskId": "bouncing-balls",
  "agents": {
    "shouldInvoke": [
      {
        "agents": ["ui-designer", "rapid-prototyper"],
        "reason": "Canvas animation is a frontend UI task",
        "required": false
      }
    ],
    "shouldNotInvoke": [
      {
        "agents": ["security-auditor"],
        "reason": "No security concerns in this task"
      }
    ]
  },
  "skills": {
    "shouldInvoke": [
      {
        "skills": ["pop-verify-completion"],
        "reason": "Should verify animation works",
        "required": true
      }
    ]
  },
  "tools": {
    "forbiddenPatterns": [
      {
        "pattern": "TodoWrite",
        "reason": "Not a PopKit feature"
      }
    ]
  }
}
```

## Example Report Output

```markdown
# PopKit Behavior Validation Report

**Task**: bouncing-balls
**Mode**: popkit
**Score**: 65/100
**Status**: ❌ FAILED

## Violations

### CRITICAL (1)
- **agent**: Expected agents not invoked: ui-designer
  - Expected: ui-designer, rapid-prototyper
  - Actual: None
  - Impact: Canvas animation is a frontend UI task

### MAJOR (1)
- **tool**: Forbidden tool pattern detected: TodoWrite
  - Expected: Pattern should not occur
  - Actual: 3 occurrences
  - Impact: Not a PopKit feature

## Recommendations

1. Fix agent routing for frontend tasks - add "canvas|animation" keywords
2. Remove TodoWrite usage - it's not part of PopKit orchestration
```

## What This Detects

- Missing orchestration (PopKit not activating)
- Over-orchestration (too many agents for simple tasks)
- Wrong agent selection (routing to inappropriate agents)
- Skill underutilization (not using PopKit features)
- Workflow failures (phase transitions not happening)
- Anti-patterns (TodoWrite usage, inefficient tool sequences)

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
- Create schemas and test_telemetry.py
- Add telemetry to existing hooks
- Build BehaviorCaptureService
- Test with simple benchmark

### Phase 2: Validation (Week 2)
- Create expectations schema
- Build BehaviorValidator
- Write first expectation file
- Generate reports

### Phase 3: Integration (Week 3)
- Integrate with benchmark runner
- Add --record-behavior flag
- Test end-to-end
- Create more expectation files

### Phase 4: Enhancement (Week 4)
- Sequence analysis
- Comparative analysis
- Performance optimization

## Success Metrics

| Metric | Target |
|--------|--------|
| Capture Accuracy | 100% of agent/skill invocations |
| Validation Precision | >95% (false positives <5%) |
| Performance Overhead | <5% benchmark runtime increase |

## Key Benefits

1. **Catch regressions early**: Know immediately when routing breaks
2. **Validate new features**: Confirm agents activate correctly
3. **Optimize performance**: Identify orchestration bottlenecks
4. **Build confidence**: Trust PopKit is working as designed
5. **Document execution**: Behavior reports serve as audit trails

## Technical Highlights

- **Zero overhead** when TEST_MODE not set
- **Non-invasive**: Hooks already have telemetry integration points
- **Extensible**: Easy to add new validation rules
- **Actionable**: Clear reports with specific recommendations

## Files to Create

**New Files** (~8):
- `packages/plugin/hooks/utils/test_telemetry.py`
- `packages/benchmarks/src/behavior/capture.ts`
- `packages/benchmarks/src/behavior/schema.ts`
- `packages/benchmarks/src/validator/validator.ts`
- `packages/benchmarks/src/validator/expectations.ts`
- `packages/benchmarks/src/reports/behavior-report.ts`
- `packages/benchmarks/tasks/bouncing-balls.expectations.json`
- `packages/benchmarks/tasks/hello-world.expectations.json`

**Modified Files** (~3):
- `packages/benchmarks/src/runner.ts` (add --record-behavior)
- `packages/plugin/hooks/agent-orchestrator.py` (emit telemetry)
- `packages/plugin/hooks/utils/skill_state.py` (already has telemetry!)

## Next Steps

1. Review this design document
2. Approve for implementation
3. Start Phase 1: Foundation components
4. Iterate based on real benchmark data

---

**Design Complete**: ✅
**Estimated Effort**: 4 weeks
**Priority**: P1-high
**Issue**: #258
