# PopKit Sandbox Testing & Observability Platform

**Date:** 2025-12-14
**Status:** Design Complete
**Related Issues:** #27, #122
**Author:** Claude + Joseph

---

## Executive Summary

A comprehensive testing and observability platform for PopKit that:
1. **Tests** skills, commands, and user scenarios in isolated environments
2. **Captures** full telemetry (tool calls, decisions, timing, tokens)
3. **Supports** both local execution and E2B cloud sandboxes
4. **Streams** data to Upstash for real-time monitoring and analytics

---

## 1. Goals

### Primary Goals
- **Observability**: Real-time monitoring of AI execution with full trace capture
- **Validation Testing**: Test PopKit workflows in isolated environments before release
- **User Simulation**: Simulate user requests end-to-end to measure PopKit's value

### Success Metrics
- 100% of P0 skills have test coverage
- Test execution captures all tool calls with <10ms overhead
- Regression detection catches performance degradation >20%
- Upstash sync latency <100ms for real-time streaming

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PopKit Test Orchestrator                         │
│  (/popkit:test or pop-sandbox-test skill)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────────┐         ┌─────────────────┐                  │
│   │  Test Matrix    │         │  Test Runner    │                  │
│   │  - Skills       │────────▶│  - Local Mode   │                  │
│   │  - Commands     │         │  - E2B Mode     │                  │
│   │  - Scenarios    │         │  - Hybrid Mode  │                  │
│   └─────────────────┘         └────────┬────────┘                  │
│                                        │                            │
│   ┌────────────────────────────────────▼────────────────────────┐  │
│   │              Telemetry Collector (hooks)                     │  │
│   │  - Tool calls (name, input, output, timing)                 │  │
│   │  - Decision points (AskUserQuestion invocations)            │  │
│   │  - Token counts (input/output per request)                  │  │
│   │  - Custom events (skill start/end, phase transitions)       │  │
│   └────────────────────────────────────┬────────────────────────┘  │
│                                        │                            │
└────────────────────────────────────────┼────────────────────────────┘
                                         │
           ┌─────────────────────────────┼─────────────────────────────┐
           │                             │                             │
           ▼                             ▼                             ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Local Storage     │    │   Upstash Redis     │    │   E2B Native Logs   │
│   ~/.popkit/tests/  │    │   (Real-time)       │    │   (Per-sandbox)     │
│   - session.jsonl   │    │   - Redis Streams   │    │   - stdout/stderr   │
│   - traces.jsonl    │    │   - Time-series     │    │   - file artifacts  │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                             │                             │
           └─────────────────────────────┼─────────────────────────────┘
                                         │
                                         ▼
                            ┌─────────────────────┐
                            │  Analytics Layer    │
                            │  - Comparison views │
                            │  - Regression detect│
                            │  - Cost analysis    │
                            └─────────────────────┘
```

### Core Components

| Component | Purpose | Location |
|-----------|---------|----------|
| Test Orchestrator | Manages test execution | `pop-sandbox-test` skill |
| Telemetry Collector | Hooks that capture everything | `hooks/utils/test_telemetry.py` |
| Local Storage | File-based for local runs | `~/.popkit/tests/` |
| Upstash Sync | Real-time cloud streaming | `hooks/utils/upstash_telemetry.py` |
| E2B Runner | Cloud sandbox execution | `hooks/utils/e2b_runner.py` |
| Analytics | Query and compare | Future: cloud dashboard |

---

## 3. Telemetry Schema

### TestSession

```typescript
interface TestSession {
  id: string;                    // Unique session ID (UUID)
  mode: "local" | "e2b";         // Execution environment
  test_type: "skill" | "command" | "scenario";
  test_name: string;             // e.g., "pop-brainstorming", "/popkit:dev"
  started_at: string;            // ISO timestamp
  ended_at: string;

  // Execution trace
  traces: ToolTrace[];
  decisions: DecisionPoint[];
  events: CustomEvent[];

  // Metrics
  metrics: {
    total_duration_ms: number;
    tool_calls: number;
    tokens_in: number;
    tokens_out: number;
    estimated_cost_usd: number;
  };

  // Result
  outcome: "success" | "failure" | "partial";
  artifacts: string[];           // Files created
  error?: string;
}
```

### ToolTrace

```typescript
interface ToolTrace {
  timestamp: string;             // ISO timestamp
  sequence: number;              // Order in session
  tool_name: string;             // "Bash", "Read", "Edit", "Write", etc.
  tool_input: Record<string, any>;
  tool_output: string;           // Truncated if >10KB
  duration_ms: number;
  success: boolean;
  error?: string;
}
```

### DecisionPoint

```typescript
interface DecisionPoint {
  timestamp: string;
  question: string;
  header: string;
  options: Array<{label: string, description: string}>;
  selected: string;
  context: string;               // What led to this decision
}
```

### CustomEvent

```typescript
interface CustomEvent {
  timestamp: string;
  event_type: string;            // "skill_start", "skill_end", "phase_change", etc.
  data: Record<string, any>;
}
```

---

## 4. Execution Modes

### Mode 1: Local Testing

```
┌──────────────────────────────────────────────────────────────────┐
│                     Local Test Runner                             │
├──────────────────────────────────────────────────────────────────┤
│  1. Create temp directory: /tmp/popkit-test-{uuid}/              │
│  2. Initialize test project:                                     │
│     - git init                                                   │
│     - Create package.json with test dependencies                 │
│     - Copy test fixtures if needed                               │
│  3. Set POPKIT_TEST_MODE=true environment variable               │
│  4. Run test scenario via Claude Code CLI:                       │
│     - claude --dangerously-skip-permissions "test prompt"        │
│  5. Telemetry hooks write to ~/.popkit/tests/{session_id}/       │
│  6. Background sync to Upstash (non-blocking)                    │
│  7. Cleanup temp directory                                       │
│  8. Return session summary                                       │
└──────────────────────────────────────────────────────────────────┘
```

**Local Storage Structure:**

```
~/.popkit/tests/
├── sessions/
│   └── {session_id}/
│       ├── meta.json           # Session metadata
│       ├── traces.jsonl        # Streaming tool traces (append-only)
│       ├── decisions.jsonl     # Decision points
│       ├── events.jsonl        # Custom events
│       └── artifacts/          # Files created during test
├── index.json                  # Session index for quick lookup
└── config.json                 # Test runner configuration
```

### Mode 2: E2B Cloud Testing

```
┌──────────────────────────────────────────────────────────────────┐
│                     E2B Test Runner                               │
├──────────────────────────────────────────────────────────────────┤
│  1. Create E2B sandbox:                                          │
│     - Template: anthropic-claude-code                            │
│     - Timeout: 600s (10 minutes)                                 │
│  2. Set environment variables:                                   │
│     - ANTHROPIC_API_KEY (from secrets)                           │
│     - POPKIT_TEST_MODE=true                                      │
│     - UPSTASH_REDIS_REST_URL (for direct streaming)              │
│  3. Upload test scenario definition                              │
│  4. Execute via Claude Code CLI in sandbox                       │
│  5. Telemetry streams directly to Upstash (real-time)            │
│  6. Download artifacts from sandbox filesystem                   │
│  7. Close sandbox                                                │
│  8. Finalize session in Upstash                                  │
└──────────────────────────────────────────────────────────────────┘
```

**E2B Benefits:**
- Fully isolated (no local file contamination)
- Reproducible environment
- Parallel execution (up to 20 concurrent on Hobby tier)
- Network access for real API calls

### Mode Comparison

| Aspect | Local | E2B |
|--------|-------|-----|
| Setup | None | E2B API key required |
| Cost | Free | ~$0.006 per 5-min run |
| Isolation | Partial (temp dir) | Full (sandbox) |
| Parallelism | Limited by machine | Up to 20 concurrent |
| Telemetry | Local → Upstash (async) | Direct → Upstash |
| Best for | Development, quick tests | CI/CD, release validation |

---

## 5. Test Matrix

### Priority Tiers

#### P0: Critical Path (Must pass for release)

**Skills:**
- `pop-brainstorming` - Core ideation workflow
- `pop-writing-plans` - Plan generation
- `pop-code-review` - Quality gate
- `pop-session-capture` - State management
- `pop-plugin-test` - Self-validation

**Commands:**
- `/popkit:dev` - Main development entry point
- `/popkit:git` - Git workflow
- `/popkit:routine morning` - Health check

#### P1: Important (Should pass)

**Skills:**
- `pop-morning-generator` - Routine support
- `pop-systematic-debugging` - Bug workflow
- `pop-assessment-*` - Quality assessments

**Commands:**
- `/popkit:project init` - Project setup
- `/popkit:power init` - Multi-agent setup
- `/popkit:issue create` - GitHub integration

#### P2: Nice to Have

- All remaining skills
- All remaining commands
- Edge case scenarios

### Test Definition Format

```yaml
# tests/matrix/skills/pop-brainstorming.yaml
name: pop-brainstorming
type: skill
priority: P0

setup:
  project_type: typescript
  files:
    - path: package.json
      content: |
        {"name": "test-project", "version": "1.0.0"}

scenarios:
  - name: "Basic brainstorm"
    prompt: "I want to brainstorm a user authentication feature"
    expected:
      skills_invoked: ["pop-brainstorming"]
      decisions_made: true
      artifacts_created: ["docs/plans/*.md"]
    timeout_ms: 120000

  - name: "Brainstorm with PDF input"
    prompt: "Here's a design doc: /fixtures/sample-prd.pdf - brainstorm implementation"
    fixtures:
      - sample-prd.pdf
    expected:
      skills_invoked: ["pop-brainstorming"]
```

### User Scenario Tests

```yaml
# tests/matrix/scenarios/build-login-page.yaml
name: build-login-page
type: scenario
priority: P1

prompt: |
  Build me a login page with email and password authentication.
  Use React and include form validation.

expected:
  duration_max_ms: 300000
  skills_invoked:
    - pop-brainstorming
    - pop-writing-plans
  files_created:
    - "**/*.tsx"
    - "**/*.css"
  contains_patterns:
    - "useState"
    - "email"
    - "password"

validation:
  - type: file_exists
    pattern: "src/**/*Login*.tsx"
  - type: syntax_check
    language: typescript
```

---

## 6. Upstash Integration

### Redis Streams for Real-Time Telemetry

```python
# hooks/utils/upstash_telemetry.py

import os
import json
from datetime import datetime
from typing import Optional
from upstash_redis import Redis

class UpstashTelemetry:
    """Stream telemetry to Upstash Redis in real-time."""

    def __init__(self):
        url = os.environ.get("UPSTASH_REDIS_REST_URL")
        token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

        if url and token:
            self.redis = Redis(url=url, token=token)
            self.enabled = True
        else:
            self.redis = None
            self.enabled = False

    def emit_trace(self, session_id: str, trace: dict):
        """Stream a tool trace."""
        if not self.enabled:
            return

        trace["timestamp"] = datetime.utcnow().isoformat()
        self.redis.xadd(
            f"popkit:test:{session_id}:traces",
            {"data": json.dumps(trace)},
            maxlen=10000
        )

    def emit_decision(self, session_id: str, decision: dict):
        """Stream a decision point."""
        if not self.enabled:
            return

        decision["timestamp"] = datetime.utcnow().isoformat()
        self.redis.xadd(
            f"popkit:test:{session_id}:decisions",
            {"data": json.dumps(decision)},
            maxlen=1000
        )

    def emit_event(self, session_id: str, event_type: str, data: dict):
        """Stream a custom event."""
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        }
        self.redis.xadd(
            f"popkit:test:{session_id}:events",
            {"data": json.dumps(event)},
            maxlen=1000
        )

    def start_session(self, session_id: str, meta: dict):
        """Initialize a test session."""
        if not self.enabled:
            return

        meta["started_at"] = datetime.utcnow().isoformat()
        self.redis.hset(f"popkit:test:{session_id}:meta", meta)
        self.redis.sadd("popkit:test:sessions", session_id)

    def end_session(self, session_id: str, metrics: dict):
        """Finalize a test session with metrics."""
        if not self.enabled:
            return

        metrics["ended_at"] = datetime.utcnow().isoformat()
        self.redis.hset(f"popkit:test:{session_id}:meta", metrics)


# Singleton instance
_telemetry: Optional[UpstashTelemetry] = None

def get_telemetry() -> UpstashTelemetry:
    global _telemetry
    if _telemetry is None:
        _telemetry = UpstashTelemetry()
    return _telemetry
```

### Querying Results

```python
# hooks/utils/test_analytics.py

def get_session(session_id: str) -> dict:
    """Get full session data."""
    redis = get_telemetry().redis

    meta = redis.hgetall(f"popkit:test:{session_id}:meta")
    traces = redis.xrange(f"popkit:test:{session_id}:traces")
    decisions = redis.xrange(f"popkit:test:{session_id}:decisions")
    events = redis.xrange(f"popkit:test:{session_id}:events")

    return {
        "meta": meta,
        "traces": [json.loads(t["data"]) for _, t in traces],
        "decisions": [json.loads(d["data"]) for _, d in decisions],
        "events": [json.loads(e["data"]) for _, e in events]
    }

def compare_sessions(session_a: str, session_b: str) -> dict:
    """Compare two test runs for regression detection."""
    a = get_session(session_a)
    b = get_session(session_b)

    return {
        "duration_diff_ms": b["meta"]["total_duration_ms"] - a["meta"]["total_duration_ms"],
        "duration_change_pct": ((b["meta"]["total_duration_ms"] - a["meta"]["total_duration_ms"])
                                / a["meta"]["total_duration_ms"]) * 100,
        "token_diff": b["meta"]["tokens_out"] - a["meta"]["tokens_out"],
        "cost_diff_usd": b["meta"]["estimated_cost_usd"] - a["meta"]["estimated_cost_usd"],
        "tool_call_diff": len(b["traces"]) - len(a["traces"]),
        "regression_detected": (
            b["meta"]["total_duration_ms"] > a["meta"]["total_duration_ms"] * 1.2 or
            b["meta"]["tokens_out"] > a["meta"]["tokens_out"] * 1.2
        )
    }

def list_sessions(test_name: Optional[str] = None, limit: int = 100) -> list:
    """List recent test sessions."""
    redis = get_telemetry().redis
    session_ids = redis.smembers("popkit:test:sessions")

    sessions = []
    for sid in list(session_ids)[:limit]:
        meta = redis.hgetall(f"popkit:test:{sid}:meta")
        if test_name is None or meta.get("test_name") == test_name:
            sessions.append({"id": sid, **meta})

    return sorted(sessions, key=lambda x: x.get("started_at", ""), reverse=True)
```

---

## 7. Hook Integration

### Modified post-tool-use.py

```python
# In hooks/post-tool-use.py

import os
import time
from hooks.utils.upstash_telemetry import get_telemetry
from hooks.utils.local_telemetry import get_local_writer

# Check if we're in test mode
TEST_MODE = os.environ.get("POPKIT_TEST_MODE") == "true"
SESSION_ID = os.environ.get("POPKIT_TEST_SESSION_ID")

def emit_tool_trace(tool_name: str, tool_input: dict, tool_output: str,
                    duration_ms: float, success: bool, error: str = None):
    """Emit telemetry for a tool call."""
    if not TEST_MODE or not SESSION_ID:
        return

    trace = {
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output[:10000],  # Truncate large outputs
        "duration_ms": duration_ms,
        "success": success,
        "error": error
    }

    # Write to local storage
    get_local_writer().write_trace(SESSION_ID, trace)

    # Stream to Upstash (non-blocking)
    get_telemetry().emit_trace(SESSION_ID, trace)
```

### Capturing AskUserQuestion Decisions

```python
# In hooks that handle AskUserQuestion responses

def emit_decision(question: str, header: str, options: list, selected: str):
    """Emit telemetry for a decision point."""
    if not TEST_MODE or not SESSION_ID:
        return

    decision = {
        "question": question,
        "header": header,
        "options": options,
        "selected": selected
    }

    get_local_writer().write_decision(SESSION_ID, decision)
    get_telemetry().emit_decision(SESSION_ID, decision)
```

---

## 8. E2B Runner Implementation

```python
# hooks/utils/e2b_runner.py

import os
import json
from typing import Optional
from e2b_code_interpreter import Sandbox

class E2BTestRunner:
    """Run tests in E2B cloud sandboxes."""

    def __init__(self):
        self.api_key = os.environ.get("E2B_API_KEY")
        if not self.api_key:
            raise ValueError("E2B_API_KEY environment variable required")

    async def run_test(self, test_def: dict) -> dict:
        """Execute a test in an E2B sandbox."""
        session_id = f"e2b-{uuid.uuid4().hex[:8]}"

        # Create sandbox with Claude Code template
        sbx = await Sandbox.create(
            template="anthropic-claude-code",
            timeout=test_def.get("timeout_ms", 600000) // 1000,
            envs={
                "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
                "POPKIT_TEST_MODE": "true",
                "POPKIT_TEST_SESSION_ID": session_id,
                "UPSTASH_REDIS_REST_URL": os.environ.get("UPSTASH_REDIS_REST_URL"),
                "UPSTASH_REDIS_REST_TOKEN": os.environ.get("UPSTASH_REDIS_REST_TOKEN"),
            }
        )

        try:
            # Setup test project
            await self._setup_project(sbx, test_def)

            # Run the test
            result = await sbx.commands.run(
                f'claude --dangerously-skip-permissions "{test_def["prompt"]}"',
                timeout=test_def.get("timeout_ms", 600000) // 1000
            )

            # Collect artifacts
            artifacts = await self._collect_artifacts(sbx, test_def)

            return {
                "session_id": session_id,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "artifacts": artifacts,
                "success": result.exit_code == 0
            }

        finally:
            await sbx.close()

    async def _setup_project(self, sbx: Sandbox, test_def: dict):
        """Setup the test project in sandbox."""
        # Create project files
        for file_def in test_def.get("setup", {}).get("files", []):
            await sbx.files.write(file_def["path"], file_def["content"])

        # Upload fixtures
        for fixture in test_def.get("fixtures", []):
            local_path = f"tests/fixtures/{fixture}"
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    await sbx.files.write(f"/fixtures/{fixture}", f.read())

        # Install dependencies if package.json exists
        if any(f["path"] == "package.json" for f in test_def.get("setup", {}).get("files", [])):
            await sbx.commands.run("npm install")

    async def _collect_artifacts(self, sbx: Sandbox, test_def: dict) -> list:
        """Download artifacts from sandbox."""
        artifacts = []

        for pattern in test_def.get("expected", {}).get("artifacts_created", []):
            # List files matching pattern
            files = await sbx.files.list("/")
            for f in self._match_pattern(files, pattern):
                content = await sbx.files.read(f)
                artifacts.append({"path": f, "content": content})

        return artifacts
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Issues #A, #B)

**Deliverables:**
- Telemetry schema defined in TypeScript/Python
- Local JSONL storage writer
- Hook modifications for test mode detection

**Files:**
- `hooks/utils/test_telemetry.py`
- `hooks/utils/local_telemetry.py`
- `tests/schema/telemetry.ts`

### Phase 2: Local Runner (Issue #C)

**Deliverables:**
- `pop-sandbox-test` skill
- Local test execution with telemetry capture
- Basic test matrix (P0 skills)

**Files:**
- `skills/pop-sandbox-test/SKILL.md`
- `hooks/utils/local_test_runner.py`
- `tests/matrix/skills/*.yaml`

### Phase 3: Cloud Integration (Issues #D, #E)

**Deliverables:**
- Upstash streaming integration
- E2B runner implementation
- Mode switching (local vs cloud)

**Files:**
- `hooks/utils/upstash_telemetry.py`
- `hooks/utils/e2b_runner.py`

### Phase 4: Full Matrix & Analytics (Issues #F, #G)

**Deliverables:**
- Complete test matrix (all priorities)
- Comparison and regression detection
- `/popkit:test` command

**Files:**
- `tests/matrix/**/*.yaml`
- `hooks/utils/test_analytics.py`
- `commands/test.md`

---

## 10. Dependencies

### Required Environment Variables

| Variable | Purpose | Required For |
|----------|---------|--------------|
| `POPKIT_TEST_MODE` | Enable telemetry capture | All test modes |
| `POPKIT_TEST_SESSION_ID` | Session identifier | All test modes |
| `UPSTASH_REDIS_REST_URL` | Upstash connection | Cloud sync |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash auth | Cloud sync |
| `E2B_API_KEY` | E2B sandbox access | E2B mode |
| `ANTHROPIC_API_KEY` | Claude API access | E2B mode |

### npm/pip Packages

```
# Python
upstash-redis>=1.0.0
e2b-code-interpreter>=0.0.11

# TypeScript (for E2B runner if needed)
@e2b/code-interpreter
```

---

## 11. Open Questions

1. **Token counting**: How do we accurately count tokens when running in E2B? May need to proxy API calls.

2. **Cost tracking**: Should we track actual API costs or estimated? Actual requires API billing access.

3. **Parallelism**: How many concurrent tests should we support? E2B Hobby tier allows 20.

4. **Retention**: How long to keep test sessions in Upstash? Suggest 30 days for free tier.

5. **CI Integration**: Should tests run on every commit, or only on release branches?

---

## 12. References

- [E2B Documentation](https://e2b.dev/docs)
- [E2B Integration Research](../research/E2B_INTEGRATION_RESEARCH.md)
- [Upstash Redis Streams](https://upstash.com/docs/redis/features/streams)
- [Claude Code CLI](https://docs.anthropic.com/claude-code)
- Issue #27: Code Execution Tool for Plan Validation
- Issue #122: E2B.dev integration research (closed)

---

## 13. Next Steps

1. Create GitHub issues for each implementation phase
2. Start with Phase 1 (Foundation) - telemetry schema and local storage
3. Test locally before adding cloud integration
4. Iterate based on real usage patterns
