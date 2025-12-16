# PopKit Self-Testing Framework Design

**Issue**: #258
**Status**: Design Phase
**Version**: 1.0.0
**Author**: PopKit Team
**Date**: 2025-12-15

## Executive Summary

PopKit currently validates **output quality** (does the code work?) but not **orchestration behavior** (did PopKit's multi-agent system actually activate?). This design document specifies a comprehensive self-testing framework that captures, validates, and reports on PopKit's internal behavior during benchmark testing.

**Core Problem**: During benchmark testing, we found that PopKit's todo app implementation worked correctly while vanilla Claude's was broken, yet both received similar quality scores (7/10). More critically, PopKit didn't invoke design agents despite being given a frontend task. We had no way to detect this orchestration failure.

**Solution**: A behavior recording and validation system that captures agent routing decisions, skill invocations, workflow transitions, and phase changes during benchmark execution, then compares actual behavior against expected behavior specifications.

---

## 1. Architecture Overview

### 1.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Benchmark Runner                          │
│  (packages/benchmarks/src/runner.ts)                        │
│                                                              │
│  --record-behavior flag triggers:                           │
│  1. Hook instrumentation enablement                         │
│  2. Behavior data collection                                │
│  3. Validation execution                                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ├─── Instrumentation Layer ───────────────┐
                   │                                          │
                   ▼                                          ▼
┌──────────────────────────────┐         ┌──────────────────────────────┐
│   Hook Telemetry System      │         │   Behavior Capture Service   │
│   (hooks/utils/)             │         │   (benchmarks/src/behavior/) │
│                              │         │                              │
│  - skill_state.py            │────────▶│  - capture.ts                │
│  - agent_orchestrator.py     │         │  - schema.ts                 │
│  - test_telemetry.py (NEW)   │         │  - storage.ts                │
└──────────────────────────────┘         └──────────────────────────────┘
                   │                                          │
                   │                                          │
                   ▼                                          ▼
┌──────────────────────────────┐         ┌──────────────────────────────┐
│   Behavior Data Storage      │         │   Validation Engine          │
│   (benchmark results/)       │         │   (benchmarks/src/validator/)│
│                              │         │                              │
│  behavior.json               │────────▶│  - validator.ts              │
│  └─ Routing events           │         │  - expectations.ts           │
│  └─ Agent invocations        │         │  - comparator.ts             │
│  └─ Skill executions         │         │  - reporter.ts               │
│  └─ Workflow phases          │         └──────────────────────────────┘
└──────────────────────────────┘                              │
                                                               ▼
                                             ┌──────────────────────────────┐
                                             │   Behavior Report            │
                                             │   (behavior-report.md)       │
                                             │                              │
                                             │  - What DID happen           │
                                             │  - What SHOULD have happened │
                                             │  - Gap analysis              │
                                             │  - Recommendations           │
                                             └──────────────────────────────┘
```

### 1.2 Data Flow

```
User Request
    │
    ├──▶ Benchmark Runner (--record-behavior)
    │        │
    │        ├──▶ Sets TEST_MODE=true env var
    │        │
    │        ├──▶ Executes task with PopKit
    │        │        │
    │        │        ├──▶ Hooks capture events
    │        │        │        │
    │        │        │        ├──▶ Agent routing decisions
    │        │        │        ├──▶ Skill invocations
    │        │        │        ├──▶ Workflow phase changes
    │        │        │        └──▶ Tool usage patterns
    │        │        │
    │        │        └──▶ Behavior Capture Service
    │        │                  │
    │        │                  └──▶ Writes behavior.json
    │        │
    │        ├──▶ Loads expectation spec
    │        │        │
    │        │        └──▶ tasks/{task-id}.expectations.json
    │        │
    │        └──▶ Validation Engine
    │                 │
    │                 ├──▶ Compares actual vs expected
    │                 │
    │                 └──▶ Generates behavior report
    │
    └──▶ Display results
             │
             ├──▶ Output quality: 7/10
             ├──▶ Behavior validation: ✅ PASS / ❌ FAIL
             └──▶ behavior-report.md
```

---

## 2. Behavior Data Schema

### 2.1 Core Data Structure

```typescript
/**
 * Complete behavior capture for a benchmark session
 */
interface BehaviorCapture {
  metadata: {
    taskId: string;
    mode: 'vanilla' | 'popkit' | 'power';
    captureVersion: string;  // Schema version
    timestamp: string;       // ISO 8601
    sessionId: string;
    testMode: boolean;
  };

  // Agent routing and selection
  routing: {
    decisions: RoutingDecision[];
    agentsConsidered: AgentEvaluation[];
    agentsSelected: string[];
    routingStrategy: 'keyword' | 'file-pattern' | 'error-pattern' | 'manual';
  };

  // Agent invocations
  agents: {
    invocations: AgentInvocation[];
    totalInvoked: number;
    parallelGroups: AgentGroup[];
    sequentialOrder: string[];
  };

  // Skill executions
  skills: {
    executions: SkillExecution[];
    totalInvoked: number;
    byCategory: Record<string, number>;
  };

  // Workflow tracking
  workflows: {
    active: WorkflowExecution[];
    phases: PhaseTransition[];
    completionStatus: Record<string, WorkflowStatus>;
  };

  // Tool usage patterns
  tools: {
    calls: ToolCall[];
    patterns: ToolPattern[];
    sequenceAnalysis: SequenceAnalysis;
  };

  // Decision points
  decisions: {
    userDecisions: UserDecision[];
    autoApproved: string[];
    declined: string[];
  };

  // Performance metrics
  performance: {
    routingTime: number;      // ms
    orchestrationTime: number; // ms
    totalHookTime: number;    // ms
  };
}

/**
 * Agent routing decision event
 */
interface RoutingDecision {
  timestamp: string;
  trigger: {
    type: 'keyword' | 'file-pattern' | 'error-pattern' | 'command';
    value: string;
    confidence: number;  // 0-100
  };
  candidates: AgentEvaluation[];
  selected: string[];
  reasoning: string;
  routingRule: string;  // From agents/config.json
}

/**
 * Agent evaluation during routing
 */
interface AgentEvaluation {
  agentName: string;
  tier: 'tier-1-always-active' | 'tier-2-on-demand' | 'feature-workflow';
  score: number;
  matchedKeywords: string[];
  matchedFilePatterns: string[];
  matchedErrorPatterns: string[];
  confidence: number;
  reason: string;
}

/**
 * Agent invocation event
 */
interface AgentInvocation {
  timestamp: string;
  agentName: string;
  tier: string;
  prompt: string;
  context: {
    files: string[];
    previousAgents: string[];
    workflowPhase?: string;
  };
  execution: {
    startTime: string;
    endTime?: string;
    durationMs?: number;
    exitCode?: number;
    error?: string;
  };
  output: {
    toolsUsed: string[];
    filesModified: string[];
    skillsInvoked: string[];
    decisions: string[];
  };
}

/**
 * Skill execution event
 */
interface SkillExecution {
  timestamp: string;
  skillName: string;
  invokedBy: 'user' | 'agent' | 'workflow';
  agentContext?: string;  // Which agent invoked it
  workflowId?: string;
  execution: {
    startTime: string;
    endTime?: string;
    durationMs?: number;
    toolCalls: number;
    errorOccurred: boolean;
    errorMessage?: string;
  };
  decisions: {
    required: string[];
    made: string[];
    pending: string[];
  };
  activityId?: string;  // From activity ledger
}

/**
 * Workflow phase transition
 */
interface PhaseTransition {
  timestamp: string;
  workflowType: 'feature-dev' | 'debug' | 'security-audit' | 'custom';
  fromPhase: string;
  toPhase: string;
  trigger: 'automatic' | 'user-decision' | 'completion';
  agentsActive: string[];
  context: Record<string, any>;
}

/**
 * Workflow execution status
 */
interface WorkflowStatus {
  workflowId: string;
  workflowType: string;
  status: 'active' | 'completed' | 'failed' | 'cancelled';
  phasesCompleted: string[];
  currentPhase?: string;
  agentsInvolved: string[];
}

/**
 * Tool usage pattern
 */
interface ToolPattern {
  pattern: string;
  description: string;
  occurrences: number;
  examples: ToolCall[];
}

/**
 * Tool call sequence analysis
 */
interface SequenceAnalysis {
  commonSequences: {
    sequence: string[];  // Tool names in order
    count: number;
    context: string;
  }[];
  antiPatterns: {
    sequence: string[];
    reason: string;
    count: number;
  }[];
}

/**
 * User decision event
 */
interface UserDecision {
  timestamp: string;
  skillContext?: string;
  decisionId: string;
  question: string;
  header: string;
  options: {
    label: string;
    description: string;
  }[];
  selected: string;
  isAutoApproved: boolean;
}

/**
 * Agent group (parallel execution)
 */
interface AgentGroup {
  groupId: string;
  agents: string[];
  startTime: string;
  endTime?: string;
  coordination: 'mesh' | 'star' | 'chain';
}

/**
 * Tool call tracking
 */
interface ToolCall {
  timestamp: string;
  toolName: string;
  input: Record<string, any>;
  context: {
    agent?: string;
    skill?: string;
    workflow?: string;
  };
}
```

### 2.2 Storage Format

**Location**: `packages/benchmarks/results/{task-id}/{mode}/behavior.json`

**Example**:
```json
{
  "metadata": {
    "taskId": "bouncing-balls",
    "mode": "popkit",
    "captureVersion": "1.0.0",
    "timestamp": "2025-12-15T10:30:00Z",
    "sessionId": "abc-123",
    "testMode": true
  },
  "routing": {
    "decisions": [
      {
        "timestamp": "2025-12-15T10:30:01Z",
        "trigger": {
          "type": "keyword",
          "value": "canvas animation UI",
          "confidence": 75
        },
        "candidates": [
          {
            "agentName": "ui-designer",
            "tier": "tier-2-on-demand",
            "score": 3,
            "matchedKeywords": ["canvas", "ui", "animation"],
            "confidence": 80,
            "reason": "Frontend task detected"
          },
          {
            "agentName": "rapid-prototyper",
            "tier": "tier-2-on-demand",
            "score": 2,
            "matchedKeywords": ["create", "animation"],
            "confidence": 60,
            "reason": "Creation task"
          }
        ],
        "selected": ["ui-designer"],
        "reasoning": "Task involves UI/canvas work, matched 3 frontend keywords",
        "routingRule": "keywords.ui -> ui-designer"
      }
    ],
    "agentsConsidered": [...],
    "agentsSelected": ["ui-designer"],
    "routingStrategy": "keyword"
  },
  "agents": {
    "invocations": [
      {
        "timestamp": "2025-12-15T10:30:02Z",
        "agentName": "ui-designer",
        "tier": "tier-2-on-demand",
        "prompt": "Create canvas with bouncing balls...",
        "execution": {
          "startTime": "2025-12-15T10:30:02Z",
          "endTime": "2025-12-15T10:31:30Z",
          "durationMs": 88000,
          "exitCode": 0
        },
        "output": {
          "toolsUsed": ["Write", "Edit", "Bash"],
          "filesModified": ["balls.js", "index.html"],
          "skillsInvoked": ["pop-verify-completion"],
          "decisions": []
        }
      }
    ],
    "totalInvoked": 1,
    "parallelGroups": [],
    "sequentialOrder": ["ui-designer"]
  },
  "skills": {
    "executions": [
      {
        "timestamp": "2025-12-15T10:31:20Z",
        "skillName": "pop-verify-completion",
        "invokedBy": "agent",
        "agentContext": "ui-designer",
        "execution": {
          "startTime": "2025-12-15T10:31:20Z",
          "endTime": "2025-12-15T10:31:28Z",
          "durationMs": 8000,
          "toolCalls": 3,
          "errorOccurred": false
        },
        "decisions": {
          "required": [],
          "made": [],
          "pending": []
        }
      }
    ],
    "totalInvoked": 1,
    "byCategory": {
      "verification": 1
    }
  },
  "workflows": {
    "active": [],
    "phases": [],
    "completionStatus": {}
  },
  "tools": {
    "calls": [...],
    "patterns": [
      {
        "pattern": "Write → Bash → Edit",
        "description": "Create file, test, refine pattern",
        "occurrences": 2
      }
    ],
    "sequenceAnalysis": {
      "commonSequences": [
        {
          "sequence": ["Write", "Bash", "Edit"],
          "count": 2,
          "context": "Iterative development"
        }
      ],
      "antiPatterns": []
    }
  },
  "decisions": {
    "userDecisions": [],
    "autoApproved": [],
    "declined": []
  },
  "performance": {
    "routingTime": 150,
    "orchestrationTime": 200,
    "totalHookTime": 450
  }
}
```

---

## 3. Behavior Expectations Schema

### 3.1 Expectation Specification

Each benchmark task can define expected behavior in a separate file:

**Location**: `packages/benchmarks/tasks/{task-id}.expectations.json`

```typescript
/**
 * Expected behavior specification for a benchmark task
 */
interface BehaviorExpectations {
  taskId: string;
  version: string;

  // Expected agent behavior
  agents: {
    // Should these agents be invoked?
    shouldInvoke?: {
      agents: string[];
      reason: string;
      required: boolean;  // MUST invoke (hard fail) or SHOULD invoke (warning)
    }[];

    // Should these agents NOT be invoked?
    shouldNotInvoke?: {
      agents: string[];
      reason: string;
    }[];

    // Expected invocation count
    invocationCount?: {
      min?: number;
      max?: number;
      exact?: number;
    };
  };

  // Expected skill usage
  skills: {
    shouldInvoke?: {
      skills: string[];
      reason: string;
      required: boolean;
    }[];

    shouldNotInvoke?: {
      skills: string[];
      reason: string;
    }[];
  };

  // Expected workflow activation
  workflows: {
    shouldActivate?: {
      workflowType: string;
      reason: string;
      phases?: string[];  // Expected phases
    }[];

    shouldNotActivate?: {
      workflowType: string;
      reason: string;
    }[];
  };

  // Expected routing behavior
  routing: {
    expectedTriggers?: {
      type: 'keyword' | 'file-pattern' | 'error-pattern';
      value: string;
      reason: string;
    }[];

    minimumConfidence?: number;  // Routing confidence threshold
  };

  // Expected tool patterns
  tools: {
    expectedPatterns?: {
      pattern: string;
      description: string;
      minOccurrences?: number;
    }[];

    forbiddenPatterns?: {
      pattern: string;
      reason: string;
    }[];
  };

  // Performance expectations
  performance: {
    maxRoutingTime?: number;      // ms
    maxOrchestrationTime?: number; // ms
    maxTotalHookTime?: number;    // ms
  };
}
```

### 3.2 Example Expectation File

**File**: `packages/benchmarks/tasks/bouncing-balls.expectations.json`

```json
{
  "taskId": "bouncing-balls",
  "version": "1.0.0",

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
        "agents": ["security-auditor", "database-optimizer"],
        "reason": "No security or database concerns in this task"
      }
    ],
    "invocationCount": {
      "min": 1,
      "max": 3
    }
  },

  "skills": {
    "shouldInvoke": [
      {
        "skills": ["pop-verify-completion"],
        "reason": "Should verify animation works before completion",
        "required": true
      }
    ]
  },

  "workflows": {
    "shouldNotActivate": [
      {
        "workflowType": "feature-dev",
        "reason": "Simple task, doesn't need 7-phase workflow"
      }
    ]
  },

  "routing": {
    "expectedTriggers": [
      {
        "type": "keyword",
        "value": "canvas|animation|ui",
        "reason": "Should detect UI-related keywords"
      }
    ],
    "minimumConfidence": 50
  },

  "tools": {
    "expectedPatterns": [
      {
        "pattern": "Write → Bash",
        "description": "Should test after creating files",
        "minOccurrences": 1
      }
    ],
    "forbiddenPatterns": [
      {
        "pattern": "TodoWrite",
        "reason": "PopKit should not use TodoWrite (it's not a PopKit feature)"
      }
    ]
  },

  "performance": {
    "maxRoutingTime": 500,
    "maxOrchestrationTime": 1000,
    "maxTotalHookTime": 2000
  }
}
```

---

## 4. Test Telemetry Integration

### 4.1 Test Mode Detection

**File**: `packages/plugin/hooks/utils/test_telemetry.py` (NEW)

```python
#!/usr/bin/env python3
"""
Test telemetry system for PopKit behavior capture (Issue #258).

Provides zero-overhead event emission when TEST_MODE=true.
Used by hooks to capture orchestration behavior during benchmark testing.
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

def is_test_mode() -> bool:
    """Check if we're running in test/benchmark mode."""
    return os.environ.get('TEST_MODE', '').lower() in ('true', '1', 'yes')

def get_test_session_id() -> Optional[str]:
    """Get the current test session ID."""
    return os.environ.get('TEST_SESSION_ID')

def create_event(
    event_type: str,
    data: Dict[str, Any],
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """Create a telemetry event.

    Args:
        event_type: Type of event (e.g., 'agent_routed', 'skill_start')
        data: Event-specific data
        timestamp: ISO 8601 timestamp (defaults to now)

    Returns:
        Formatted event dict
    """
    return {
        'id': str(uuid.uuid4()),
        'type': event_type,
        'timestamp': timestamp or datetime.utcnow().isoformat() + 'Z',
        'session_id': get_test_session_id(),
        'data': data
    }

def emit_event(event: Dict[str, Any]) -> None:
    """Emit event to stdout in JSONL format.

    Events are captured by benchmark runner and aggregated into behavior.json.
    """
    if is_test_mode():
        print(f"TELEMETRY:{json.dumps(event)}", flush=True)

def emit_routing_decision(
    trigger_type: str,
    trigger_value: str,
    candidates: list,
    selected: list,
    reasoning: str,
    routing_rule: str,
    confidence: float
) -> None:
    """Emit agent routing decision event."""
    event = create_event('routing_decision', {
        'trigger': {
            'type': trigger_type,
            'value': trigger_value,
            'confidence': confidence
        },
        'candidates': candidates,
        'selected': selected,
        'reasoning': reasoning,
        'routing_rule': routing_rule
    })
    emit_event(event)

def emit_agent_invocation(
    agent_name: str,
    tier: str,
    prompt: str,
    context: Dict[str, Any]
) -> str:
    """Emit agent invocation start event.

    Returns:
        Event ID for correlation with completion event
    """
    event = create_event('agent_invocation_start', {
        'agent_name': agent_name,
        'tier': tier,
        'prompt': prompt[:200],  # Truncate long prompts
        'context': context
    })
    emit_event(event)
    return event['id']

def emit_agent_completion(
    invocation_id: str,
    agent_name: str,
    duration_ms: float,
    exit_code: int,
    output: Dict[str, Any]
) -> None:
    """Emit agent invocation completion event."""
    event = create_event('agent_invocation_complete', {
        'invocation_id': invocation_id,
        'agent_name': agent_name,
        'duration_ms': duration_ms,
        'exit_code': exit_code,
        'output': output
    })
    emit_event(event)

def emit_skill_start(
    skill_name: str,
    invoked_by: str,
    workflow_id: Optional[str] = None
) -> str:
    """Emit skill execution start event.

    Returns:
        Event ID for correlation
    """
    event = create_event('skill_start', {
        'skill_name': skill_name,
        'invoked_by': invoked_by,
        'workflow_id': workflow_id
    })
    emit_event(event)
    return event['id']

def emit_skill_complete(
    execution_id: str,
    skill_name: str,
    duration_ms: float,
    tool_calls: int,
    error: Optional[str] = None
) -> None:
    """Emit skill execution completion event."""
    event = create_event('skill_complete', {
        'execution_id': execution_id,
        'skill_name': skill_name,
        'duration_ms': duration_ms,
        'tool_calls': tool_calls,
        'error_occurred': error is not None,
        'error_message': error
    })
    emit_event(event)

def emit_phase_transition(
    workflow_type: str,
    from_phase: str,
    to_phase: str,
    trigger: str,
    agents_active: list
) -> None:
    """Emit workflow phase transition event."""
    event = create_event('phase_transition', {
        'workflow_type': workflow_type,
        'from_phase': from_phase,
        'to_phase': to_phase,
        'trigger': trigger,
        'agents_active': agents_active
    })
    emit_event(event)

def emit_tool_pattern(
    pattern: str,
    description: str,
    context: Dict[str, Any]
) -> None:
    """Emit tool usage pattern detection."""
    event = create_event('tool_pattern', {
        'pattern': pattern,
        'description': description,
        'context': context
    })
    emit_event(event)
```

### 4.2 Hook Integration Points

**Modify**: `packages/plugin/hooks/agent-orchestrator.py`

```python
# Add at top of file
from utils.test_telemetry import (
    is_test_mode,
    emit_routing_decision,
    emit_agent_invocation
)

# In create_orchestration_plan method, after routing decision:
if is_test_mode():
    emit_routing_decision(
        trigger_type=analysis['routing_strategy'],
        trigger_value=prompt[:100],
        candidates=[{
            'agent_name': a['name'],
            'tier': a.get('tier', 'unknown'),
            'score': a.get('score', 0),
            'confidence': a.get('confidence', 0)
        } for a in analysis['suggested_agents']],
        selected=[a['name'] for a in selected_agents],
        reasoning=plan['recommendations'],
        routing_rule='auto',
        confidence=analysis.get('confidence', 0)
    )
```

**Modify**: `packages/plugin/hooks/utils/skill_state.py`

```python
# Already has test_telemetry integration!
# Lines 24-32 show the import and fallback
# emit_telemetry_event method already implemented (lines 117-134)
# Integration points: start_skill (line 153), end_skill (line 184), record_phase_change (line 286)
```

---

## 5. Behavior Capture Service

### 5.1 Capture Implementation

**File**: `packages/benchmarks/src/behavior/capture.ts` (NEW)

```typescript
import { Readable } from 'stream';
import { BehaviorCapture, TelemetryEvent } from './schema.js';

/**
 * Captures behavior telemetry from benchmark execution.
 *
 * Listens to stdout from Claude Code subprocess for TELEMETRY: events,
 * aggregates them into structured behavior data.
 */
export class BehaviorCaptureService {
  private events: TelemetryEvent[] = [];
  private sessionId: string;
  private taskId: string;
  private mode: string;

  constructor(taskId: string, mode: string, sessionId: string) {
    this.taskId = taskId;
    this.mode = mode;
    this.sessionId = sessionId;
  }

  /**
   * Attach to Claude Code subprocess stdout to capture events
   */
  attachToProcess(stdout: Readable): void {
    let buffer = '';

    stdout.on('data', (chunk: Buffer) => {
      buffer += chunk.toString();

      // Process complete lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';  // Keep incomplete line in buffer

      for (const line of lines) {
        this.processLine(line);
      }
    });

    stdout.on('end', () => {
      if (buffer.trim()) {
        this.processLine(buffer);
      }
    });
  }

  /**
   * Process a single line of output
   */
  private processLine(line: string): void {
    // Look for telemetry events: "TELEMETRY:{...json...}"
    const match = line.match(/TELEMETRY:(\{.*\})/);
    if (match) {
      try {
        const event = JSON.parse(match[1]);
        this.events.push(event);
      } catch (error) {
        console.warn('Failed to parse telemetry event:', line);
      }
    }
  }

  /**
   * Build final behavior capture from collected events
   */
  buildBehaviorCapture(): BehaviorCapture {
    const capture: BehaviorCapture = {
      metadata: {
        taskId: this.taskId,
        mode: this.mode as any,
        captureVersion: '1.0.0',
        timestamp: new Date().toISOString(),
        sessionId: this.sessionId,
        testMode: true
      },
      routing: this.analyzeRouting(),
      agents: this.analyzeAgents(),
      skills: this.analyzeSkills(),
      workflows: this.analyzeWorkflows(),
      tools: this.analyzeTools(),
      decisions: this.analyzeDecisions(),
      performance: this.analyzePerformance()
    };

    return capture;
  }

  private analyzeRouting() {
    const routingEvents = this.events.filter(e => e.type === 'routing_decision');

    return {
      decisions: routingEvents.map(e => ({
        timestamp: e.timestamp,
        trigger: e.data.trigger,
        candidates: e.data.candidates,
        selected: e.data.selected,
        reasoning: e.data.reasoning,
        routingRule: e.data.routing_rule
      })),
      agentsConsidered: routingEvents.flatMap(e => e.data.candidates),
      agentsSelected: [...new Set(routingEvents.flatMap(e => e.data.selected))],
      routingStrategy: routingEvents[0]?.data.trigger.type || 'unknown'
    };
  }

  private analyzeAgents() {
    const startEvents = this.events.filter(e => e.type === 'agent_invocation_start');
    const completeEvents = this.events.filter(e => e.type === 'agent_invocation_complete');

    const invocations = startEvents.map(start => {
      const complete = completeEvents.find(c => c.data.invocation_id === start.id);

      return {
        timestamp: start.timestamp,
        agentName: start.data.agent_name,
        tier: start.data.tier,
        prompt: start.data.prompt,
        context: start.data.context,
        execution: {
          startTime: start.timestamp,
          endTime: complete?.timestamp,
          durationMs: complete?.data.duration_ms,
          exitCode: complete?.data.exit_code,
          error: complete?.data.exit_code !== 0 ? 'Agent failed' : undefined
        },
        output: complete?.data.output || {
          toolsUsed: [],
          filesModified: [],
          skillsInvoked: [],
          decisions: []
        }
      };
    });

    return {
      invocations,
      totalInvoked: invocations.length,
      parallelGroups: this.detectParallelGroups(invocations),
      sequentialOrder: invocations.map(i => i.agentName)
    };
  }

  private analyzeSkills() {
    const startEvents = this.events.filter(e => e.type === 'skill_start');
    const completeEvents = this.events.filter(e => e.type === 'skill_complete');

    const executions = startEvents.map(start => {
      const complete = completeEvents.find(c => c.data.execution_id === start.id);

      return {
        timestamp: start.timestamp,
        skillName: start.data.skill_name,
        invokedBy: start.data.invoked_by,
        agentContext: start.data.invoked_by === 'agent' ? 'unknown' : undefined,
        workflowId: start.data.workflow_id,
        execution: {
          startTime: start.timestamp,
          endTime: complete?.timestamp,
          durationMs: complete?.data.duration_ms,
          toolCalls: complete?.data.tool_calls || 0,
          errorOccurred: complete?.data.error_occurred || false,
          errorMessage: complete?.data.error_message
        },
        decisions: {
          required: [],
          made: [],
          pending: []
        }
      };
    });

    // Categorize skills
    const byCategory: Record<string, number> = {};
    for (const exec of executions) {
      const category = this.categorizeSkill(exec.skillName);
      byCategory[category] = (byCategory[category] || 0) + 1;
    }

    return {
      executions,
      totalInvoked: executions.length,
      byCategory
    };
  }

  private analyzeWorkflows() {
    const phaseEvents = this.events.filter(e => e.type === 'phase_transition');

    return {
      active: [],
      phases: phaseEvents.map(e => ({
        timestamp: e.timestamp,
        workflowType: e.data.workflow_type,
        fromPhase: e.data.from_phase,
        toPhase: e.data.to_phase,
        trigger: e.data.trigger,
        agentsActive: e.data.agents_active,
        context: {}
      })),
      completionStatus: {}
    };
  }

  private analyzeTools() {
    // Tool analysis would come from tool-calls.json (already captured)
    return {
      calls: [],
      patterns: [],
      sequenceAnalysis: {
        commonSequences: [],
        antiPatterns: []
      }
    };
  }

  private analyzeDecisions() {
    return {
      userDecisions: [],
      autoApproved: [],
      declined: []
    };
  }

  private analyzePerformance() {
    const routingEvents = this.events.filter(e => e.type === 'routing_decision');
    const agentEvents = this.events.filter(e =>
      e.type === 'agent_invocation_start' || e.type === 'agent_invocation_complete'
    );

    return {
      routingTime: routingEvents.length * 50,  // Estimate
      orchestrationTime: agentEvents.length * 100,  // Estimate
      totalHookTime: this.events.length * 10  // Estimate
    };
  }

  private detectParallelGroups(invocations: any[]) {
    // Simple heuristic: if multiple agents start within 1 second, they're parallel
    const groups: any[] = [];

    // This would be more sophisticated in real implementation
    return groups;
  }

  private categorizeSkill(skillName: string): string {
    if (skillName.includes('verify') || skillName.includes('test')) return 'verification';
    if (skillName.includes('debug') || skillName.includes('trace')) return 'debugging';
    if (skillName.includes('review') || skillName.includes('audit')) return 'quality';
    if (skillName.includes('project') || skillName.includes('init')) return 'project-management';
    return 'other';
  }
}
```

---

## 6. Validation Engine

### 6.1 Validator Implementation

**File**: `packages/benchmarks/src/validator/validator.ts` (NEW)

```typescript
import { BehaviorCapture } from '../behavior/schema.js';
import { BehaviorExpectations } from './expectations.js';

export interface ValidationResult {
  passed: boolean;
  score: number;  // 0-100
  violations: Violation[];
  warnings: Warning[];
  insights: string[];
}

export interface Violation {
  category: 'agent' | 'skill' | 'workflow' | 'routing' | 'tool' | 'performance';
  severity: 'critical' | 'major' | 'minor';
  message: string;
  expected: any;
  actual: any;
  impact: string;
}

export interface Warning {
  category: string;
  message: string;
  recommendation: string;
}

/**
 * Validates actual behavior against expectations
 */
export class BehaviorValidator {
  constructor(
    private expectations: BehaviorExpectations,
    private actual: BehaviorCapture
  ) {}

  /**
   * Run all validations
   */
  validate(): ValidationResult {
    const violations: Violation[] = [];
    const warnings: Warning[] = [];
    const insights: string[] = [];

    // Validate agents
    violations.push(...this.validateAgents());

    // Validate skills
    violations.push(...this.validateSkills());

    // Validate workflows
    violations.push(...this.validateWorkflows());

    // Validate routing
    violations.push(...this.validateRouting());

    // Validate tools
    violations.push(...this.validateTools());

    // Validate performance
    violations.push(...this.validatePerformance());

    // Generate warnings
    warnings.push(...this.generateWarnings());

    // Generate insights
    insights.push(...this.generateInsights());

    // Calculate score
    const score = this.calculateScore(violations, warnings);

    return {
      passed: violations.filter(v => v.severity === 'critical').length === 0,
      score,
      violations,
      warnings,
      insights
    };
  }

  private validateAgents(): Violation[] {
    const violations: Violation[] = [];
    const agentExpectations = this.expectations.agents;

    if (!agentExpectations) return violations;

    // Check shouldInvoke
    if (agentExpectations.shouldInvoke) {
      for (const expectation of agentExpectations.shouldInvoke) {
        const invokedAgents = this.actual.agents.agentsSelected;
        const missing = expectation.agents.filter(a => !invokedAgents.includes(a));

        if (missing.length > 0) {
          violations.push({
            category: 'agent',
            severity: expectation.required ? 'critical' : 'major',
            message: `Expected agents not invoked: ${missing.join(', ')}`,
            expected: expectation.agents,
            actual: invokedAgents,
            impact: expectation.reason
          });
        }
      }
    }

    // Check shouldNotInvoke
    if (agentExpectations.shouldNotInvoke) {
      for (const expectation of agentExpectations.shouldNotInvoke) {
        const invokedAgents = this.actual.agents.agentsSelected;
        const unexpected = expectation.agents.filter(a => invokedAgents.includes(a));

        if (unexpected.length > 0) {
          violations.push({
            category: 'agent',
            severity: 'major',
            message: `Unexpected agents invoked: ${unexpected.join(', ')}`,
            expected: `Not ${expectation.agents.join(', ')}`,
            actual: unexpected,
            impact: expectation.reason
          });
        }
      }
    }

    // Check invocation count
    if (agentExpectations.invocationCount) {
      const count = this.actual.agents.totalInvoked;
      const { min, max, exact } = agentExpectations.invocationCount;

      if (exact !== undefined && count !== exact) {
        violations.push({
          category: 'agent',
          severity: 'minor',
          message: `Agent invocation count mismatch`,
          expected: exact,
          actual: count,
          impact: 'May indicate over/under-orchestration'
        });
      } else if (min !== undefined && count < min) {
        violations.push({
          category: 'agent',
          severity: 'major',
          message: `Too few agent invocations`,
          expected: `>= ${min}`,
          actual: count,
          impact: 'PopKit may not be orchestrating enough'
        });
      } else if (max !== undefined && count > max) {
        violations.push({
          category: 'agent',
          severity: 'minor',
          message: `Too many agent invocations`,
          expected: `<= ${max}`,
          actual: count,
          impact: 'May be over-orchestrating'
        });
      }
    }

    return violations;
  }

  private validateSkills(): Violation[] {
    const violations: Violation[] = [];
    const skillExpectations = this.expectations.skills;

    if (!skillExpectations) return violations;

    const invokedSkills = this.actual.skills.executions.map(e => e.skillName);

    // Check shouldInvoke
    if (skillExpectations.shouldInvoke) {
      for (const expectation of skillExpectations.shouldInvoke) {
        const missing = expectation.skills.filter(s => !invokedSkills.includes(s));

        if (missing.length > 0) {
          violations.push({
            category: 'skill',
            severity: expectation.required ? 'critical' : 'major',
            message: `Expected skills not invoked: ${missing.join(', ')}`,
            expected: expectation.skills,
            actual: invokedSkills,
            impact: expectation.reason
          });
        }
      }
    }

    // Check shouldNotInvoke
    if (skillExpectations.shouldNotInvoke) {
      for (const expectation of skillExpectations.shouldNotInvoke) {
        const unexpected = expectation.skills.filter(s => invokedSkills.includes(s));

        if (unexpected.length > 0) {
          violations.push({
            category: 'skill',
            severity: 'major',
            message: `Unexpected skills invoked: ${unexpected.join(', ')}`,
            expected: `Not ${expectation.skills.join(', ')}`,
            actual: unexpected,
            impact: expectation.reason
          });
        }
      }
    }

    return violations;
  }

  private validateWorkflows(): Violation[] {
    const violations: Violation[] = [];
    const workflowExpectations = this.expectations.workflows;

    if (!workflowExpectations) return violations;

    const activeWorkflows = this.actual.workflows.phases.map(p => p.workflowType);

    // Check shouldActivate
    if (workflowExpectations.shouldActivate) {
      for (const expectation of workflowExpectations.shouldActivate) {
        if (!activeWorkflows.includes(expectation.workflowType)) {
          violations.push({
            category: 'workflow',
            severity: 'major',
            message: `Expected workflow not activated: ${expectation.workflowType}`,
            expected: expectation.workflowType,
            actual: activeWorkflows,
            impact: expectation.reason
          });
        }
      }
    }

    // Check shouldNotActivate
    if (workflowExpectations.shouldNotActivate) {
      for (const expectation of workflowExpectations.shouldNotActivate) {
        if (activeWorkflows.includes(expectation.workflowType)) {
          violations.push({
            category: 'workflow',
            severity: 'minor',
            message: `Unexpected workflow activated: ${expectation.workflowType}`,
            expected: `Not ${expectation.workflowType}`,
            actual: activeWorkflows,
            impact: expectation.reason
          });
        }
      }
    }

    return violations;
  }

  private validateRouting(): Violation[] {
    const violations: Violation[] = [];
    const routingExpectations = this.expectations.routing;

    if (!routingExpectations) return violations;

    // Check minimum confidence
    if (routingExpectations.minimumConfidence !== undefined) {
      const avgConfidence = this.actual.routing.decisions.reduce(
        (sum, d) => sum + d.trigger.confidence, 0
      ) / Math.max(this.actual.routing.decisions.length, 1);

      if (avgConfidence < routingExpectations.minimumConfidence) {
        violations.push({
          category: 'routing',
          severity: 'minor',
          message: 'Routing confidence below threshold',
          expected: routingExpectations.minimumConfidence,
          actual: avgConfidence,
          impact: 'Low confidence routing may select wrong agents'
        });
      }
    }

    return violations;
  }

  private validateTools(): Violation[] {
    const violations: Violation[] = [];
    const toolExpectations = this.expectations.tools;

    if (!toolExpectations) return violations;

    // Check forbidden patterns
    if (toolExpectations.forbiddenPatterns) {
      for (const forbidden of toolExpectations.forbiddenPatterns) {
        const matches = this.actual.tools.patterns.filter(p =>
          p.pattern.includes(forbidden.pattern)
        );

        if (matches.length > 0) {
          violations.push({
            category: 'tool',
            severity: 'critical',
            message: `Forbidden tool pattern detected: ${forbidden.pattern}`,
            expected: 'Pattern should not occur',
            actual: matches,
            impact: forbidden.reason
          });
        }
      }
    }

    return violations;
  }

  private validatePerformance(): Violation[] {
    const violations: Violation[] = [];
    const perfExpectations = this.expectations.performance;

    if (!perfExpectations) return violations;

    const perf = this.actual.performance;

    if (perfExpectations.maxRoutingTime && perf.routingTime > perfExpectations.maxRoutingTime) {
      violations.push({
        category: 'performance',
        severity: 'minor',
        message: 'Routing took too long',
        expected: `<= ${perfExpectations.maxRoutingTime}ms`,
        actual: `${perf.routingTime}ms`,
        impact: 'Slow routing adds overhead'
      });
    }

    return violations;
  }

  private generateWarnings(): Warning[] {
    const warnings: Warning[] = [];

    // No agents invoked at all
    if (this.actual.agents.totalInvoked === 0) {
      warnings.push({
        category: 'orchestration',
        message: 'No agents were invoked during execution',
        recommendation: 'Check if PopKit is properly activated. Task may not have triggered routing.'
      });
    }

    // No skills invoked
    if (this.actual.skills.totalInvoked === 0) {
      warnings.push({
        category: 'features',
        message: 'No PopKit skills were used',
        recommendation: 'Verify agents are invoking skills. May indicate vanilla-like behavior.'
      });
    }

    return warnings;
  }

  private generateInsights(): string[] {
    const insights: string[] = [];

    // Agent diversity
    const uniqueAgents = new Set(this.actual.agents.invocations.map(i => i.agentName));
    insights.push(`${uniqueAgents.size} unique agent(s) invoked`);

    // Skill usage
    const uniqueSkills = new Set(this.actual.skills.executions.map(e => e.skillName));
    insights.push(`${uniqueSkills.size} unique skill(s) used`);

    // Workflow complexity
    if (this.actual.workflows.phases.length > 0) {
      insights.push(`Multi-phase workflow detected (${this.actual.workflows.phases.length} transitions)`);
    } else {
      insights.push('Simple execution, no workflow phases');
    }

    return insights;
  }

  private calculateScore(violations: Violation[], warnings: Warning[]): number {
    let score = 100;

    // Deduct points for violations
    for (const violation of violations) {
      switch (violation.severity) {
        case 'critical':
          score -= 30;
          break;
        case 'major':
          score -= 15;
          break;
        case 'minor':
          score -= 5;
          break;
      }
    }

    // Deduct points for warnings
    score -= warnings.length * 3;

    return Math.max(0, score);
  }
}
```

---

## 7. Integration with Benchmark Runner

### 7.1 Runner Modifications

**Modify**: `packages/benchmarks/src/runner.ts`

```typescript
import { BehaviorCaptureService } from './behavior/capture.js';
import { BehaviorValidator } from './validator/validator.js';
import { loadExpectations } from './validator/expectations.js';
import { writeBehaviorReport } from './reports/behavior-report.js';

export interface BenchmarkOptions {
  // ... existing options ...
  recordBehavior?: boolean;  // NEW: Enable behavior recording
}

export async function runBenchmark(
  taskId: string,
  mode: 'vanilla' | 'popkit' | 'power',
  options: BenchmarkOptions
): Promise<BenchmarkResult> {
  const sessionId = generateSessionId();

  // Enable test mode if behavior recording requested
  if (options.recordBehavior) {
    process.env.TEST_MODE = 'true';
    process.env.TEST_SESSION_ID = sessionId;
  }

  // Initialize behavior capture
  let behaviorCapture: BehaviorCaptureService | null = null;
  if (options.recordBehavior) {
    behaviorCapture = new BehaviorCaptureService(taskId, mode, sessionId);
  }

  // Start Claude Code subprocess
  const subprocess = spawn('claude', [...]);

  // Attach behavior capture to stdout
  if (behaviorCapture) {
    behaviorCapture.attachToProcess(subprocess.stdout);
  }

  // ... existing execution logic ...

  // Build behavior data
  let behaviorValidation: ValidationResult | null = null;
  if (behaviorCapture && options.recordBehavior) {
    const behavior = behaviorCapture.buildBehaviorCapture();

    // Save behavior.json
    await saveBehaviorData(resultsDir, behavior);

    // Load expectations and validate
    const expectations = await loadExpectations(taskId);
    if (expectations) {
      const validator = new BehaviorValidator(expectations, behavior);
      behaviorValidation = validator.validate();

      // Generate behavior report
      await writeBehaviorReport(resultsDir, behaviorValidation, behavior, expectations);
    }
  }

  return {
    // ... existing result fields ...
    behaviorValidation  // NEW: Include validation results
  };
}
```

### 7.2 CLI Flag Support

**Modify**: `packages/benchmarks/src/cli.ts`

```typescript
program
  .command('run')
  .option('--record-behavior', 'Capture and validate orchestration behavior')
  .action(async (options) => {
    const result = await runBenchmark(taskId, mode, {
      recordBehavior: options.recordBehavior
    });

    // Display behavior validation
    if (result.behaviorValidation) {
      console.log('\nBehavior Validation:');
      console.log(`  Score: ${result.behaviorValidation.score}/100`);
      console.log(`  Status: ${result.behaviorValidation.passed ? '✅ PASS' : '❌ FAIL'}`);

      if (result.behaviorValidation.violations.length > 0) {
        console.log(`  Violations: ${result.behaviorValidation.violations.length}`);
      }

      console.log(`  Report: ${resultsDir}/behavior-report.md`);
    }
  });
```

---

## 8. Behavior Report Generator

### 8.1 Report Template

**File**: `packages/benchmarks/src/reports/behavior-report.ts` (NEW)

```typescript
import { BehaviorCapture } from '../behavior/schema.js';
import { BehaviorExpectations } from '../validator/expectations.js';
import { ValidationResult } from '../validator/validator.js';
import { writeFile } from 'fs/promises';
import { join } from 'path';

export async function writeBehaviorReport(
  resultsDir: string,
  validation: ValidationResult,
  actual: BehaviorCapture,
  expected: BehaviorExpectations
): Promise<void> {
  const report = generateReport(validation, actual, expected);
  await writeFile(join(resultsDir, 'behavior-report.md'), report);
}

function generateReport(
  validation: ValidationResult,
  actual: BehaviorCapture,
  expected: BehaviorExpectations
): string {
  const lines: string[] = [];

  lines.push('# PopKit Behavior Validation Report');
  lines.push('');
  lines.push(`**Task**: ${actual.metadata.taskId}`);
  lines.push(`**Mode**: ${actual.metadata.mode}`);
  lines.push(`**Timestamp**: ${actual.metadata.timestamp}`);
  lines.push(`**Session**: ${actual.metadata.sessionId}`);
  lines.push('');

  // Executive Summary
  lines.push('## Executive Summary');
  lines.push('');
  lines.push(`**Validation Score**: ${validation.score}/100`);
  lines.push(`**Status**: ${validation.passed ? '✅ PASSED' : '❌ FAILED'}`);
  lines.push('');
  lines.push(`- **Violations**: ${validation.violations.length} (${validation.violations.filter(v => v.severity === 'critical').length} critical)`);
  lines.push(`- **Warnings**: ${validation.warnings.length}`);
  lines.push(`- **Agents Invoked**: ${actual.agents.totalInvoked}`);
  lines.push(`- **Skills Used**: ${actual.skills.totalInvoked}`);
  lines.push('');

  // Key Insights
  if (validation.insights.length > 0) {
    lines.push('## Key Insights');
    lines.push('');
    for (const insight of validation.insights) {
      lines.push(`- ${insight}`);
    }
    lines.push('');
  }

  // Violations
  if (validation.violations.length > 0) {
    lines.push('## Violations');
    lines.push('');

    const bySeverity = {
      critical: validation.violations.filter(v => v.severity === 'critical'),
      major: validation.violations.filter(v => v.severity === 'major'),
      minor: validation.violations.filter(v => v.severity === 'minor')
    };

    for (const [severity, violations] of Object.entries(bySeverity)) {
      if (violations.length > 0) {
        lines.push(`### ${severity.toUpperCase()} (${violations.length})`);
        lines.push('');

        for (const v of violations) {
          lines.push(`#### ${v.category}: ${v.message}`);
          lines.push('');
          lines.push(`**Expected**: ${JSON.stringify(v.expected)}`);
          lines.push(`**Actual**: ${JSON.stringify(v.actual)}`);
          lines.push(`**Impact**: ${v.impact}`);
          lines.push('');
        }
      }
    }
  }

  // Warnings
  if (validation.warnings.length > 0) {
    lines.push('## Warnings');
    lines.push('');

    for (const warning of validation.warnings) {
      lines.push(`### ${warning.category}: ${warning.message}`);
      lines.push('');
      lines.push(`**Recommendation**: ${warning.recommendation}`);
      lines.push('');
    }
  }

  // Detailed Behavior Analysis
  lines.push('## Detailed Behavior Analysis');
  lines.push('');

  // Agent Routing
  lines.push('### Agent Routing');
  lines.push('');
  if (actual.routing.decisions.length === 0) {
    lines.push('⚠️ **No routing decisions recorded**');
    lines.push('');
  } else {
    for (const decision of actual.routing.decisions) {
      lines.push(`**Routing Event** (${decision.timestamp})`);
      lines.push(`- Trigger: ${decision.trigger.type} - "${decision.trigger.value}" (confidence: ${decision.trigger.confidence})`);
      lines.push(`- Candidates: ${decision.candidates.map(c => `${c.agentName} (score: ${c.score})`).join(', ')}`);
      lines.push(`- Selected: ${decision.selected.join(', ')}`);
      lines.push(`- Reasoning: ${decision.reasoning}`);
      lines.push('');
    }
  }

  // Agent Invocations
  lines.push('### Agent Invocations');
  lines.push('');
  if (actual.agents.invocations.length === 0) {
    lines.push('⚠️ **No agents were invoked**');
    lines.push('');
  } else {
    for (const invocation of actual.agents.invocations) {
      lines.push(`**${invocation.agentName}** (${invocation.tier})`);
      lines.push(`- Start: ${invocation.execution.startTime}`);
      lines.push(`- Duration: ${invocation.execution.durationMs}ms`);
      lines.push(`- Tools: ${invocation.output.toolsUsed.join(', ')}`);
      lines.push(`- Files: ${invocation.output.filesModified.join(', ')}`);
      lines.push(`- Skills: ${invocation.output.skillsInvoked.join(', ')}`);
      lines.push('');
    }
  }

  // Skill Executions
  lines.push('### Skill Executions');
  lines.push('');
  if (actual.skills.executions.length === 0) {
    lines.push('⚠️ **No skills were executed**');
    lines.push('');
  } else {
    for (const execution of actual.skills.executions) {
      lines.push(`**${execution.skillName}**`);
      lines.push(`- Invoked by: ${execution.invokedBy}`);
      if (execution.agentContext) {
        lines.push(`- Agent context: ${execution.agentContext}`);
      }
      lines.push(`- Duration: ${execution.execution.durationMs}ms`);
      lines.push(`- Tool calls: ${execution.execution.toolCalls}`);
      if (execution.execution.errorOccurred) {
        lines.push(`- ❌ Error: ${execution.execution.errorMessage}`);
      }
      lines.push('');
    }

    lines.push('**Skills by Category**:');
    for (const [category, count] of Object.entries(actual.skills.byCategory)) {
      lines.push(`- ${category}: ${count}`);
    }
    lines.push('');
  }

  // Workflow Phases
  if (actual.workflows.phases.length > 0) {
    lines.push('### Workflow Phases');
    lines.push('');

    for (const phase of actual.workflows.phases) {
      lines.push(`**${phase.workflowType}**: ${phase.fromPhase} → ${phase.toPhase}`);
      lines.push(`- Timestamp: ${phase.timestamp}`);
      lines.push(`- Trigger: ${phase.trigger}`);
      lines.push(`- Agents: ${phase.agentsActive.join(', ')}`);
      lines.push('');
    }
  }

  // Expectations vs Actual
  lines.push('## Expected vs Actual Comparison');
  lines.push('');

  lines.push('### Agents');
  lines.push('');
  lines.push('| Aspect | Expected | Actual | Status |');
  lines.push('|--------|----------|--------|--------|');

  if (expected.agents?.shouldInvoke) {
    for (const exp of expected.agents.shouldInvoke) {
      const actualAgents = actual.agents.agentsSelected;
      const matches = exp.agents.filter(a => actualAgents.includes(a));
      const status = matches.length === exp.agents.length ? '✅' : '❌';
      lines.push(`| Should invoke | ${exp.agents.join(', ')} | ${matches.join(', ') || 'None'} | ${status} |`);
    }
  }

  if (expected.agents?.shouldNotInvoke) {
    for (const exp of expected.agents.shouldNotInvoke) {
      const actualAgents = actual.agents.agentsSelected;
      const unexpected = exp.agents.filter(a => actualAgents.includes(a));
      const status = unexpected.length === 0 ? '✅' : '❌';
      lines.push(`| Should NOT invoke | ${exp.agents.join(', ')} | ${unexpected.join(', ') || 'None'} | ${status} |`);
    }
  }

  lines.push('');

  // Performance Metrics
  lines.push('## Performance Metrics');
  lines.push('');
  lines.push('| Metric | Value | Threshold | Status |');
  lines.push('|--------|-------|-----------|--------|');
  lines.push(`| Routing time | ${actual.performance.routingTime}ms | ${expected.performance?.maxRoutingTime || 'N/A'}ms | ${actual.performance.routingTime <= (expected.performance?.maxRoutingTime || Infinity) ? '✅' : '❌'} |`);
  lines.push(`| Orchestration time | ${actual.performance.orchestrationTime}ms | ${expected.performance?.maxOrchestrationTime || 'N/A'}ms | ${actual.performance.orchestrationTime <= (expected.performance?.maxOrchestrationTime || Infinity) ? '✅' : '❌'} |`);
  lines.push(`| Total hook time | ${actual.performance.totalHookTime}ms | ${expected.performance?.maxTotalHookTime || 'N/A'}ms | ${actual.performance.totalHookTime <= (expected.performance?.maxTotalHookTime || Infinity) ? '✅' : '❌'} |`);
  lines.push('');

  // Recommendations
  lines.push('## Recommendations');
  lines.push('');

  if (validation.violations.length === 0) {
    lines.push('✅ All behavior expectations met! PopKit is orchestrating correctly.');
  } else {
    lines.push('Based on the violations found, we recommend:');
    lines.push('');

    const criticalViolations = validation.violations.filter(v => v.severity === 'critical');
    if (criticalViolations.length > 0) {
      lines.push('**Critical Issues (fix immediately)**:');
      for (const v of criticalViolations) {
        lines.push(`1. ${v.message} - ${v.impact}`);
      }
      lines.push('');
    }

    const majorViolations = validation.violations.filter(v => v.severity === 'major');
    if (majorViolations.length > 0) {
      lines.push('**Major Issues (address soon)**:');
      for (const v of majorViolations) {
        lines.push(`1. ${v.message} - ${v.impact}`);
      }
      lines.push('');
    }
  }

  // Footer
  lines.push('---');
  lines.push('');
  lines.push('*Generated by PopKit Self-Testing Framework v1.0.0*');
  lines.push('');

  return lines.join('\n');
}
```

---

## 9. Test Scenarios

### 9.1 Simple Task Scenario

**Task**: Create a "Hello World" HTML page

**Expected Behavior**:
```json
{
  "taskId": "hello-world",
  "agents": {
    "shouldNotInvoke": [
      {
        "agents": ["power-coordinator"],
        "reason": "Simple task doesn't need Power Mode"
      }
    ],
    "invocationCount": {
      "max": 1
    }
  },
  "workflows": {
    "shouldNotActivate": [
      {
        "workflowType": "feature-dev",
        "reason": "Too simple for 7-phase workflow"
      }
    ]
  }
}
```

**Validation**: Should confirm PopKit doesn't over-engineer simple tasks.

### 9.2 Frontend Task Scenario

**Task**: Create bouncing balls canvas animation (current benchmark)

**Expected Behavior**:
```json
{
  "taskId": "bouncing-balls",
  "agents": {
    "shouldInvoke": [
      {
        "agents": ["ui-designer", "rapid-prototyper"],
        "reason": "Frontend UI task",
        "required": false
      }
    ]
  },
  "routing": {
    "expectedTriggers": [
      {
        "type": "keyword",
        "value": "canvas|animation|ui",
        "reason": "Should detect UI keywords"
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

**Validation**: Confirms UI-specific agents are routed correctly.

### 9.3 Complex Feature Scenario

**Task**: Build a full-stack TODO application with authentication

**Expected Behavior**:
```json
{
  "taskId": "fullstack-todo",
  "agents": {
    "shouldInvoke": [
      {
        "agents": ["code-architect", "security-auditor", "api-designer"],
        "reason": "Complex full-stack task needs architecture and security review",
        "required": true
      }
    ],
    "invocationCount": {
      "min": 3,
      "max": 8
    }
  },
  "workflows": {
    "shouldActivate": [
      {
        "workflowType": "feature-dev",
        "reason": "Complex enough to warrant 7-phase workflow",
        "phases": ["Discovery", "Exploration", "Architecture", "Implementation", "Review"]
      }
    ]
  },
  "skills": {
    "shouldInvoke": [
      {
        "skills": ["pop-verify-completion", "pop-code-review"],
        "reason": "Should verify and review complex implementation",
        "required": true
      }
    ]
  }
}
```

**Validation**: Confirms PopKit activates full workflow for complex tasks.

### 9.4 Power Mode Recommendation Scenario

**Task**: Refactor entire codebase for new architecture

**Expected Behavior**:
```json
{
  "taskId": "architecture-refactor",
  "agents": {
    "shouldInvoke": [
      {
        "agents": ["power-coordinator"],
        "reason": "Epic task should trigger Power Mode suggestion",
        "required": false
      }
    ]
  },
  "decisions": {
    "expectedDecisions": [
      {
        "questionPattern": ".*Power Mode.*",
        "reason": "Should suggest Power Mode for epic tasks"
      }
    ]
  }
}
```

**Validation**: Confirms Power Mode is suggested for epic-scale work.

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create behavior data schemas (`schema.ts`)
- [ ] Implement `test_telemetry.py` module
- [ ] Add telemetry emission to `skill_state.py` (already partially done!)
- [ ] Add telemetry emission to `agent-orchestrator.py`
- [ ] Create `BehaviorCaptureService` class
- [ ] Test telemetry capture with simple benchmark

### Phase 2: Validation Engine (Week 2)
- [ ] Create expectations schema (`expectations.ts`)
- [ ] Implement `BehaviorValidator` class
- [ ] Write first expectation file (`bouncing-balls.expectations.json`)
- [ ] Create behavior report generator
- [ ] Test validation with bouncing-balls benchmark

### Phase 3: Integration (Week 3)
- [ ] Integrate with benchmark runner
- [ ] Add `--record-behavior` CLI flag
- [ ] Test full end-to-end flow
- [ ] Create 3-5 more expectation files for existing benchmarks
- [ ] Document usage in benchmark README

### Phase 4: Enhancement (Week 4)
- [ ] Add sequence analysis for tool patterns
- [ ] Improve parallel group detection
- [ ] Add comparative analysis (vanilla vs popkit behavior)
- [ ] Create behavior diff visualization
- [ ] Performance optimization

### Phase 5: Refinement (Ongoing)
- [ ] Gather feedback from benchmark runs
- [ ] Tune expectation specifications
- [ ] Add more sophisticated validation rules
- [ ] Create expectation templates for common scenarios
- [ ] Build expectation generator tool

---

## 11. Success Metrics

### 11.1 Framework Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Capture Accuracy** | 100% | All agent/skill invocations captured |
| **Validation Precision** | >95% | False positive rate <5% |
| **Performance Overhead** | <5% | Benchmark runtime increase |
| **Report Clarity** | 90%+ satisfaction | Team feedback survey |

### 11.2 Detection Capabilities

The framework should detect:

1. **Missing Orchestration**: PopKit not activating when it should
2. **Over-Orchestration**: Too many agents for simple tasks
3. **Wrong Agent Selection**: Routing to inappropriate agents
4. **Skill Underutilization**: Not using PopKit features effectively
5. **Workflow Failures**: Phase transitions not happening
6. **Anti-Patterns**: TodoWrite usage, inefficient tool sequences

### 11.3 Business Value

- **Development Confidence**: Know when PopKit is working vs regressing
- **Quality Assurance**: Automated detection of orchestration bugs
- **Performance Tracking**: Monitor hook overhead over time
- **Feature Validation**: Confirm new routing rules work correctly
- **Documentation**: Behavior reports serve as execution documentation

---

## 12. Future Enhancements

### 12.1 Short-term (v1.1)

- **Visual Dashboards**: Web UI for behavior visualization
- **Trend Analysis**: Track behavior changes across versions
- **Expectation Generator**: Auto-generate expectations from successful runs
- **Comparative Mode**: Side-by-side vanilla vs popkit behavior

### 12.2 Medium-term (v1.2)

- **Machine Learning**: Predict expected behavior for new tasks
- **Anomaly Detection**: Flag unusual orchestration patterns
- **Cost Analysis**: Track API costs per orchestration decision
- **Real-time Monitoring**: Live behavior tracking during development

### 12.3 Long-term (v2.0)

- **Self-Healing**: Automatically adjust routing rules based on failures
- **A/B Testing**: Compare different orchestration strategies
- **Production Monitoring**: Behavior tracking in real user sessions
- **Multi-Project Learning**: Share behavior patterns across projects

---

## 13. Risk Mitigation

### 13.1 Risks and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Performance overhead** | High | Medium | Lazy loading, minimal JSON parsing, async processing |
| **False positives** | Medium | High | Tunable thresholds, required vs optional expectations |
| **Incomplete capture** | High | Medium | Comprehensive hook coverage, fallback to stderr parsing |
| **Complex expectations** | Low | High | Templates, generator tools, clear documentation |
| **Maintenance burden** | Medium | Medium | Auto-sync with routing config, expectation versioning |

### 13.2 Testing Strategy

1. **Unit Tests**: Test each validator rule independently
2. **Integration Tests**: Full capture → validate → report flow
3. **Regression Tests**: Existing benchmarks should maintain behavior
4. **Performance Tests**: Measure overhead with/without recording
5. **Edge Case Tests**: Error scenarios, missing data, malformed events

---

## 14. Documentation Requirements

### 14.1 User Documentation

- **Quick Start**: How to run benchmarks with `--record-behavior`
- **Expectation Guide**: How to write expectation files
- **Report Reading**: How to interpret behavior reports
- **Troubleshooting**: Common issues and solutions

### 14.2 Developer Documentation

- **Architecture**: System design and data flow
- **Schema Reference**: Complete field documentation
- **Hook Integration**: How to emit telemetry events
- **Validator Extension**: How to add new validation rules

### 14.3 Examples

- **Simple Task**: Minimal expectation example
- **Complex Task**: Full-featured expectation example
- **Custom Validator**: How to write custom validation logic
- **Behavior Analysis**: Interpreting patterns in behavior data

---

## 15. Conclusion

This self-testing framework transforms PopKit from a black box into a transparent, measurable system. By capturing and validating orchestration behavior, we can:

1. **Catch regressions early**: Know immediately when routing breaks
2. **Validate new features**: Confirm agents and workflows activate correctly
3. **Optimize performance**: Identify and fix orchestration bottlenecks
4. **Build confidence**: Trust that PopKit is working as designed
5. **Document execution**: Behavior reports serve as audit trails

The framework is designed to be:
- **Zero-overhead** when not in test mode
- **Non-invasive** to existing code
- **Extensible** for new validation rules
- **Actionable** with clear reports and recommendations

**Next Steps**: Begin Phase 1 implementation with foundation components, starting with test telemetry and behavior capture service.

---

**Design Document Version**: 1.0.0
**Status**: ✅ Ready for Implementation
**Estimated Effort**: 4 weeks (4 phases)
**Priority**: P1-high (Issue #258)
