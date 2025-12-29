# PopKit Behavior Validation Guide

**Issue:** #258 Self-Testing Framework
**Status:** Phase 3 Complete ✓

## Overview

The PopKit Self-Testing Framework validates PopKit's orchestration behavior during benchmarks. Instead of just testing output quality, it validates that PopKit routes to the correct agents, invokes appropriate skills, and follows expected patterns.

## Architecture

```
┌─────────────────┐
│  Benchmark Task │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  BenchmarkRunner                │
│  - Sets TEST_MODE=true          │
│  - Captures TELEMETRY events    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  BehaviorCaptureService         │
│  - Listens to stderr            │
│  - Parses TELEMETRY: events     │
│  - Builds BehaviorCapture       │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  BehaviorValidator              │
│  - Loads .expectations.json     │
│  - Validates behavior           │
│  - Generates violations         │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  BehaviorReportGenerator        │
│  - Creates markdown report      │
│  - Shows expected vs actual     │
│  - Provides recommendations     │
└─────────────────────────────────┘
```

## Key Components

### 1. Telemetry Emission (Python)

**Location:** `packages/plugin/hooks/utils/test_telemetry.py`

Python hooks emit TELEMETRY events when `TEST_MODE=true`:

```python
from test_telemetry import emit_routing_decision, emit_agent_invocation

# Emit routing decision
emit_routing_decision(
    trigger={'type': 'intent_analysis', 'value': 'build', 'confidence': 85},
    candidates=[{'agent': 'ui-designer', 'score': 90}],
    selected=['ui-designer']
)

# Emit agent invocation
emit_agent_invocation('ui-designer', 'agent-001', 'hook')
```

**Event Types:**
- `routing_decision` - Agent routing decisions
- `agent_invocation_start` - Agent starts
- `agent_invocation_complete` - Agent completes
- `skill_start` - Skill execution begins
- `skill_complete` - Skill execution ends
- `phase_transition` - Workflow phase changes
- `user_decision` - User answers AskUserQuestion
- `tool_call` - Tool invocations

### 2. Behavior Capture (TypeScript)

**Location:** `packages/benchmarks/src/behavior/capture.ts`

Captures TELEMETRY events from stderr and builds structured data:

```typescript
const captureService = new BehaviorCaptureService(
  'bouncing-balls',  // task ID
  'popkit',          // mode
  'session-123'      // session ID
);

// Attach to subprocess
captureService.attachToProcess(subprocess.stderr);

// After execution
const behavior = captureService.buildBehaviorCapture();
```

### 3. Expectation Schema (JSON)

**Location:** `packages/benchmarks/tasks/{task-id}.expectations.json`

Defines expected behavior for a task:

```json
{
  "taskId": "bouncing-balls",
  "description": "UI task: Create canvas animation",
  "mode": "popkit",

  "agents": {
    "shouldInvoke": [
      {
        "agents": ["ui-designer", "rapid-prototyper"],
        "reason": "UI task should trigger design agents",
        "required": false
      }
    ],
    "shouldNotInvoke": [
      {
        "agents": ["query-optimizer", "security-auditor"],
        "reason": "Backend agents irrelevant for frontend task",
        "required": true
      }
    ]
  },

  "tools": {
    "expectedPatterns": [
      {
        "pattern": "Write",
        "reason": "Should write implementation file",
        "severity": "critical",
        "minOccurrences": 1
      }
    ],
    "forbiddenPatterns": [
      {
        "pattern": "Bash:npm install",
        "reason": "Vanilla JS - no dependencies",
        "severity": "major"
      }
    ]
  },

  "performance": {
    "maxToolCalls": 25,
    "maxAgentInvocations": 3
  }
}
```

### 4. Validation Engine (TypeScript)

**Location:** `packages/benchmarks/src/validator/validator.ts`

Validates behavior against expectations:

```typescript
import { BehaviorValidator } from '@popkit/benchmarks';

const validator = new BehaviorValidator(expectations, behaviorCapture);
const result = validator.validate();

console.log(`Score: ${result.score}/100`);
console.log(`Passed: ${result.passed}`);
console.log(`Violations: ${result.summary.totalViolations}`);
```

### 5. Report Generator (TypeScript)

**Location:** `packages/benchmarks/src/validator/report.ts`

Generates markdown reports:

```typescript
import { generateBehaviorReport } from '@popkit/benchmarks';

const report = generateBehaviorReport(result, expectations, behaviorCapture);
fs.writeFileSync('behavior-report.md', report);
```

## Writing Expectation Files

### Step 1: Create Expectation File

Create `tasks/{task-id}.expectations.json` with the following structure:

```json
{
  "taskId": "your-task-id",
  "description": "Brief description of what behavior you're testing",
  "mode": "popkit",

  "agents": { /* ... */ },
  "skills": { /* ... */ },
  "tools": { /* ... */ },
  "routing": { /* ... */ },
  "workflows": { /* ... */ },
  "performance": { /* ... */ },
  "decisions": { /* ... */ }
}
```

### Step 2: Define Agent Expectations

```json
"agents": {
  "shouldInvoke": [
    {
      "agents": ["agent-name"],
      "reason": "Why this agent should be invoked",
      "required": true,
      "invocationCount": {
        "min": 1,
        "max": 3
      }
    }
  ],
  "shouldNotInvoke": [
    {
      "agents": ["agent-name"],
      "reason": "Why this agent should NOT be invoked",
      "required": true
    }
  ],
  "exclusiveInvocation": {
    "agents": ["only-agent-1", "only-agent-2"],
    "reason": "Only these agents should be used"
  }
}
```

### Step 3: Define Tool Expectations

```json
"tools": {
  "expectedPatterns": [
    {
      "pattern": "Read",
      "reason": "Should read existing files",
      "severity": "major",
      "minOccurrences": 2
    }
  ],
  "forbiddenPatterns": [
    {
      "pattern": "Bash:git clone",
      "reason": "Should not clone external repos",
      "severity": "critical"
    }
  ],
  "sequences": {
    "antiPatterns": [
      {
        "sequence": ["Write", "Write", "Write"],
        "reason": "Multiple consecutive writes suggest inefficiency",
        "severity": "minor"
      }
    ]
  }
}
```

### Step 4: Define Performance Expectations

```json
"performance": {
  "maxToolCalls": 30,
  "maxAgentInvocations": 5,
  "maxTotalDurationMs": 180000
}
```

### Step 5: Run Validation

Validation happens automatically when:
1. Task has an `.expectations.json` file
2. Benchmark is run with `TEST_MODE=true`

```bash
# Automatic validation
npm run benchmark -- bouncing-balls popkit

# View report
cat /tmp/popkit-benchmark-*/bouncing-balls/behavior-report.md
```

## Violation Severity Levels

| Severity | Points | When to Use |
|----------|--------|-------------|
| Critical | -20 | Must fix - wrong agent invoked, forbidden tool used |
| Major | -10 | Should fix - expected agent missing, wrong routing |
| Minor | -5 | Nice to fix - too many tool calls, inefficiency |

**Passing Threshold:** 80/100

## Example: Full Workflow

### 1. Create Task Definition

`tasks/my-task.json`:
```json
{
  "id": "my-task",
  "name": "My Test Task",
  "prompt": "Build a simple web page",
  "category": "standard",
  "language": "javascript",
  "workflowCommand": "/popkit:dev \"Build a simple web page\"",
  "initialFiles": {
    "index.html": "<!DOCTYPE html><html>...</html>"
  },
  "tests": [...]
}
```

### 2. Create Expectation File

`tasks/my-task.expectations.json`:
```json
{
  "taskId": "my-task",
  "description": "Simple web page - should use UI agents",
  "mode": "popkit",

  "agents": {
    "shouldInvoke": [
      {
        "agents": ["ui-designer"],
        "reason": "UI task requires UI designer",
        "required": true
      }
    ]
  },

  "tools": {
    "expectedPatterns": [
      {
        "pattern": "Write",
        "reason": "Should write HTML/CSS/JS",
        "severity": "critical",
        "minOccurrences": 1
      }
    ]
  },

  "performance": {
    "maxToolCalls": 20
  }
}
```

### 3. Run Benchmark

```bash
cd packages/benchmarks
npm run benchmark -- my-task popkit
```

### 4. View Results

The behavior report is saved to the working directory:

```markdown
# Behavior Validation Report

**Task:** my-task
**Mode:** popkit
**Status:** ✓ PASSED ✅
**Score:** 100/100
**Date:** ...

## Executive Summary

PopKit orchestration validation passed with a score of **100/100**.

- **Total Checks:** 3
- **Passed:** 3 (100%)
- **Violations:** 0

## Violations

No violations detected. All expectations met! 🎉

## Expected vs Actual

### Agents

**Expected:**
- ui-designer

**Actual:**
- ui-designer

## Insights

- Perfect behavior! All expectations met.
```

## Best Practices

### 1. Start Simple

Begin with basic expectations and add more as you understand the behavior:

```json
{
  "taskId": "my-task",
  "mode": "popkit",
  "agents": {
    "shouldInvoke": [
      {
        "agents": ["relevant-agent"],
        "reason": "Basic check",
        "required": false
      }
    ]
  }
}
```

### 2. Use Required Wisely

Set `required: true` only for critical expectations:
- Wrong agent would break the task
- Forbidden tool causes security issues
- Must-have routing decisions

### 3. Set Realistic Performance Limits

Base performance expectations on baseline measurements:

```json
"performance": {
  "maxToolCalls": 30,  // 20% over baseline
  "maxAgentInvocations": 3
}
```

### 4. Document Reasons

Always provide clear reasons for expectations:

```json
"shouldNotInvoke": [
  {
    "agents": ["security-auditor"],
    "reason": "Simple UI task - no security concerns",
    "required": true
  }
]
```

### 5. Test Expectations

Run benchmarks and verify that:
- Expected agents are actually invoked
- Forbidden patterns don't occur
- Performance limits are achievable

## Troubleshooting

### No Behavior Captured

**Problem:** BehaviorCapture is empty

**Solutions:**
1. Verify `TEST_MODE=true` is set
2. Check that Python hooks are emitting telemetry
3. Ensure stderr is being captured

### Validation Not Running

**Problem:** No validation result in benchmark output

**Solutions:**
1. Check that `.expectations.json` file exists
2. Verify file is in `packages/benchmarks/tasks/`
3. Check logs for validation errors

### Low Validation Score

**Problem:** Score below 80/100

**Solutions:**
1. Review violations in behavior report
2. Check if expectations are too strict
3. Verify agent routing configuration
4. Update expectations based on actual behavior

### False Positives

**Problem:** Violations for correct behavior

**Solutions:**
1. Review expectation definitions
2. Adjust severity levels
3. Add flexibility with min/max ranges
4. Set `required: false` for optional checks

## Advanced Usage

### Custom Validation Logic

```typescript
import { BehaviorValidator } from '@popkit/benchmarks';

class CustomValidator extends BehaviorValidator {
  protected validateCustom(): void {
    // Add custom validation logic
    if (this.capture.agents.total_invoked > 10) {
      this.violations.push({
        category: 'agent',
        severity: 'minor',
        expected: 'Reasonable agent count',
        actual: `${this.capture.agents.total_invoked} agents`,
        reason: 'Too many agents invoked',
      });
    }
  }
}
```

### Programmatic Validation

```typescript
import {
  loadTask,
  BehaviorCaptureService,
  BehaviorValidator,
  generateBehaviorReport,
} from '@popkit/benchmarks';

// Load task and expectations
const task = loadTask('my-task');
const expectations = JSON.parse(
  fs.readFileSync(`tasks/${task.id}.expectations.json`, 'utf-8')
);

// Run validation
const validator = new BehaviorValidator(expectations, behaviorCapture);
const result = validator.validate();

if (result.passed) {
  console.log('✅ Validation passed!');
} else {
  console.log('❌ Validation failed!');
  console.log(`Score: ${result.score}/100`);

  // Generate detailed report
  const report = generateBehaviorReport(result, expectations, behaviorCapture);
  fs.writeFileSync('detailed-report.md', report);
}
```

## Next Steps

1. **Write expectations** for your benchmark tasks
2. **Run benchmarks** with validation enabled
3. **Review reports** to understand behavior
4. **Iterate** on expectations based on results
5. **Share learnings** with the team

## Resources

- **Design Document:** `docs/designs/self-testing-framework-design.md`
- **Architecture:** `docs/designs/self-testing-architecture.md`
- **Implementation Checklist:** `docs/designs/self-testing-implementation-checklist.md`
- **Example Expectation:** `packages/benchmarks/tasks/bouncing-balls.expectations.json`

## Support

For questions or issues with behavior validation:
1. Check this guide first
2. Review the design documents
3. Check existing expectation files for examples
4. Open an issue on GitHub with #258 label
