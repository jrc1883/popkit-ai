# PopKit Workflow Benchmark Design

**Status:** Draft
**Created:** 2025-12-15
**Issue:** #81
**Author:** Claude Sonnet 4.5

---

## Executive Summary

Enable automated benchmarking of PopKit workflows by handling interactive `AskUserQuestion` prompts programmatically through pre-defined responses and a benchmark mode environment variable.

## Problem Statement

### Current Limitations

The existing benchmark system only tests "plugin enabled vs disabled" modes, which doesn't capture PopKit's actual value because:

1. **No Workflow Execution**: Enabling the plugin doesn't automatically invoke workflows
2. **Interactive Prompts**: Workflows like `/popkit:dev full` use `AskUserQuestion` that require human input
3. **Automation Gap**: Benchmarks can't wait for human interaction during automated runs
4. **Measurement Miss**: We're not measuring what PopKit actually does (workflow automation)

### Success Metrics

- Benchmark PopKit workflows end-to-end without human intervention
- No GitHub side effects during benchmark runs (no actual PRs, commits, etc.)
- Reproducible results with pre-defined decision paths
- Support for multiple workflow scenarios (dev, project-init, finish-branch, etc.)

---

## Architecture Overview

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│ Benchmark Runner (packages/benchmarks/)                      │
│  - Sets POPKIT_BENCHMARK_MODE=true                          │
│  - Provides workflowCommand                                 │
│  - Creates response file                                    │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ PopKit Plugin (packages/plugin/)                            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Pre-Tool-Use Hook                                        ││
│  │  - Detects POPKIT_BENCHMARK_MODE                        ││
│  │  - Intercepts AskUserQuestion                           ││
│  │  - Returns pre-defined responses                        ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Benchmark Response Utility (benchmark_responses.py)     ││
│  │  - is_benchmark_mode()                                  ││
│  │  - get_response(question_id)                            ││
│  │  - should_skip_question(question_id)                    ││
│  └─────────────────────────────────────────────────────────┘│
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Skills (pop-brainstorming, pop-finish-branch, etc.)        │
│  - Check benchmark mode before AskUserQuestion             │
│  - Use pre-defined responses in benchmark mode             │
│  - Skip GitHub operations in benchmark mode                │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Design

### 1. Extended Task Schema

**File:** `packages/benchmarks/src/types.ts`

Add new fields to the Task type:

```typescript
interface Task {
  // ... existing fields ...

  // New fields for PopKit workflows
  workflowType?: "vanilla" | "popkit-workflow";
  workflowCommand?: string; // e.g., '/popkit:dev full "Add user auth"'
  benchmarkResponses?: {
    [questionId: string]: string | string[]; // Pre-defined answers
  };
}
```

**Example Task:**

```json
{
  "id": "popkit-dev-auth",
  "workflowType": "popkit-workflow",
  "workflowCommand": "/popkit:dev full \"Add user authentication\"",
  "benchmarkResponses": {
    "brainstorm_approach": "Use JWT with refresh tokens (Recommended)",
    "tech_stack": ["Express.js", "jsonwebtoken", "bcrypt"],
    "continue_implementation": "Yes, proceed with implementation"
  }
}
```

### 2. Benchmark Runner Updates

**File:** `packages/benchmarks/src/run-benchmark.ts`

**Changes:**

1. **Set environment variable:**

   ```typescript
   if (task.workflowType === "popkit-workflow") {
     process.env.POPKIT_BENCHMARK_MODE = "true";
   }
   ```

2. **Create response file:**

   ```typescript
   const responsePath = path.join(workingDir, ".benchmark-responses.json");
   if (task.benchmarkResponses) {
     fs.writeFileSync(responsePath, JSON.stringify(task.benchmarkResponses, null, 2));
   }
   ```

3. **Build prompt with workflow command:**

   ```typescript
   if (task.workflowType === "popkit-workflow") {
     prompt = task.workflowCommand + "\n\n" + task.instruction;
   }
   ```

4. **Cleanup:**
   ```typescript
   if (fs.existsSync(responsePath)) {
     fs.unlinkSync(responsePath);
   }
   delete process.env.POPKIT_BENCHMARK_MODE;
   ```

### 3. Benchmark Response Utility

**New File:** `packages/plugin/hooks/utils/benchmark_responses.py`

```python
"""
Benchmark response utilities for automated testing.

Provides pre-defined responses to AskUserQuestion during benchmark runs.
"""

import os
import json
from pathlib import Path
from typing import Optional, Union, List, Dict, Any


def is_benchmark_mode() -> bool:
    """
    Check if running in benchmark mode.

    Returns:
        True if POPKIT_BENCHMARK_MODE environment variable is set
    """
    return os.getenv("POPKIT_BENCHMARK_MODE") == "true"


def get_response_file_path() -> Optional[Path]:
    """
    Get path to benchmark responses file.

    Returns:
        Path to .benchmark-responses.json if it exists
    """
    cwd = Path.cwd()
    response_file = cwd / ".benchmark-responses.json"
    return response_file if response_file.exists() else None


def load_responses() -> Dict[str, Any]:
    """
    Load benchmark responses from file.

    Returns:
        Dictionary of question_id -> response mappings
    """
    response_file = get_response_file_path()
    if not response_file:
        return {}

    try:
        with open(response_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def get_response(question_id: str) -> Optional[Union[str, List[str]]]:
    """
    Get pre-defined response for a question.

    Args:
        question_id: Identifier for the question

    Returns:
        Pre-defined response (string or list of strings for multi-select)
        None if no response defined
    """
    responses = load_responses()
    return responses.get(question_id)


def should_skip_question(question_id: str) -> bool:
    """
    Check if question should be skipped in benchmark mode.

    Args:
        question_id: Identifier for the question

    Returns:
        True if question has a pre-defined response
    """
    response = get_response(question_id)
    return response is not None
```

### 4. Skill Template Updates

Each skill that uses `AskUserQuestion` needs benchmark mode support.

**Example: `pop-brainstorming/SKILL.md`**

Add to skill instructions:

````markdown
## Benchmark Mode Support

When `POPKIT_BENCHMARK_MODE=true`:

1. Check for benchmark mode:

   ```python
   from benchmark_responses import is_benchmark_mode, get_response

   if is_benchmark_mode():
       response = get_response("brainstorm_approach")
       if response:
           # Use pre-defined response instead of AskUserQuestion
           proceed_with_design(response)
   ```
````

2. Question IDs used in this skill:
   - `brainstorm_approach`: Design approach selection
   - `tech_stack`: Technology stack selection
   - `continue_implementation`: Proceed to implementation decision

3. GitHub Operations: Skip all GitHub operations in benchmark mode
   - Do NOT create issues
   - Do NOT create branches
   - Do NOT push commits

````

**Skills to Update:**
1. `pop-brainstorming` - Design approach questions
2. `pop-writing-plans` - Implementation plan questions
3. `pop-project-init` - Project initialization questions
4. `pop-finish-branch` - PR creation and merge questions

### 5. PopKit Benchmark Tasks

Create task files in `packages/benchmarks/tasks/popkit/`

#### Task 1: Full Dev Workflow
**File:** `popkit-dev-auth.json`

```json
{
  "id": "popkit-dev-auth",
  "name": "PopKit Full Dev Workflow - User Auth",
  "workflowType": "popkit-workflow",
  "workflowCommand": "/popkit:dev full \"Add user authentication with JWT\"",
  "instruction": "Follow the workflow to implement authentication",
  "benchmarkResponses": {
    "brainstorm_approach": "Use JWT with refresh tokens (Recommended)",
    "tech_stack": ["Express.js", "jsonwebtoken", "bcrypt"],
    "implementation_steps": ["Database schema", "Auth routes", "Middleware", "Tests"],
    "continue_implementation": "Yes, proceed",
    "create_pr": "No, skip PR creation"
  },
  "success_criteria": [
    "Authentication logic implemented",
    "Tests written",
    "No GitHub side effects"
  ]
}
````

#### Task 2: Project Initialization

**File:** `popkit-project-init.json`

```json
{
  "id": "popkit-project-init",
  "name": "PopKit Project Init",
  "workflowType": "popkit-workflow",
  "workflowCommand": "/popkit:project init",
  "instruction": "Initialize PopKit project configuration",
  "benchmarkResponses": {
    "project_type": "Web Application (Recommended)",
    "tech_stack": ["React", "Node.js", "TypeScript"],
    "testing_framework": "Jest",
    "enable_power_mode": "No"
  },
  "success_criteria": ["CLAUDE.md created", "Project config initialized", "No network calls"]
}
```

#### Task 3: Quick Fix Workflow

**File:** `popkit-quick-fix.json`

```json
{
  "id": "popkit-quick-fix",
  "name": "PopKit Quick Fix Workflow",
  "workflowType": "popkit-workflow",
  "workflowCommand": "/popkit:dev quick \"Fix login button styling\"",
  "instruction": "Quick fix for CSS issue",
  "benchmarkResponses": {
    "fix_approach": "Update CSS directly (Recommended)",
    "test_fix": "Manual testing only",
    "create_pr": "No"
  },
  "success_criteria": ["CSS fix applied", "No test failures", "No GitHub operations"]
}
```

### 6. Hook Integration

**File:** `packages/plugin/hooks/pre-tool-use.py`

Add benchmark mode check for `AskUserQuestion`:

```python
from utils.benchmark_responses import (
    is_benchmark_mode,
    get_response,
    should_skip_question
)

def handle_ask_user_question(tool_input: dict) -> dict:
    """
    Handle AskUserQuestion tool calls.

    In benchmark mode, returns pre-defined responses.
    """
    if not is_benchmark_mode():
        return {"action": "continue"}

    # Extract question ID from tool input
    questions = tool_input.get("questions", [])
    if not questions:
        return {"action": "continue"}

    # For simplicity, use first question's header as ID
    question_id = questions[0].get("header", "").lower().replace(" ", "_")

    if should_skip_question(question_id):
        response = get_response(question_id)
        return {
            "action": "block",
            "synthetic_response": {
                question_id: response
            }
        }

    return {"action": "continue"}
```

---

## Implementation Plan

### Phase 1: Foundation (Day 1-2)

1. Create `benchmark_responses.py` utility
2. Update task schema in `types.ts`
3. Update benchmark runner with env variable and response file handling

### Phase 2: Integration (Day 3-4)

4. Add benchmark mode check to pre-tool-use hook
5. Update skill templates with benchmark instructions
6. Test with mock responses

### Phase 3: Tasks (Day 5-6)

7. Create PopKit benchmark task definitions
8. Implement response mappings
9. Test each workflow end-to-end

### Phase 4: Validation (Day 7)

10. Run full benchmark suite
11. Verify no GitHub side effects
12. Document results and update README

---

## Testing Strategy

### Unit Tests

- `benchmark_responses.py` functions
- Response file parsing
- Environment variable detection

### Integration Tests

- Run benchmarks with pre-defined responses
- Verify skills use responses correctly
- Confirm no network/GitHub operations

### End-to-End Tests

```bash
# Test full workflow
npx tsx run-benchmark.ts popkit-dev-auth popkit

# Expected: Completes without human input
# Expected: No GitHub API calls
# Expected: All tasks complete successfully
```

---

## Edge Cases & Error Handling

### Missing Response File

- **Scenario:** `.benchmark-responses.json` not found
- **Handling:** `load_responses()` returns empty dict, questions proceed normally

### Malformed Response File

- **Scenario:** Invalid JSON in response file
- **Handling:** Catch `JSONDecodeError`, return empty dict, log warning

### Missing Response for Question

- **Scenario:** Question ID not in responses
- **Handling:** Fall through to normal AskUserQuestion flow

### GitHub Operations

- **Scenario:** Skill attempts PR creation in benchmark mode
- **Handling:** Skills check `is_benchmark_mode()` and skip GitHub operations

---

## Security Considerations

1. **Credential Leakage**: Benchmark responses are JSON files - never store credentials
2. **Side Effects**: All skills must check benchmark mode before external operations
3. **File Cleanup**: Response files must be deleted after benchmark completion
4. **Environment Isolation**: Each benchmark run should have isolated working directory

---

## Success Criteria

- [x] Design document complete
- [ ] `benchmark_responses.py` implemented and tested
- [ ] Benchmark runner supports workflow commands
- [ ] 3+ PopKit workflow tasks created
- [ ] No GitHub side effects during benchmarks
- [ ] Can run: `npx tsx run-benchmark.ts popkit-dev-auth popkit`
- [ ] Documentation updated (README, STATUS.json)

---

## Future Enhancements

1. **Response Templates**: Library of common response patterns
2. **Validation**: Schema validation for benchmark responses
3. **Metrics**: Measure workflow efficiency gains
4. **Visualization**: Compare vanilla vs PopKit workflow performance
5. **CI Integration**: Run benchmarks in GitHub Actions

---

## References

- Issue #81: PopKit Workflow Benchmark Testing
- Issue #260 (elshaddai): PopKit Benchmark Suite
- Issue #248 (elshaddai): Benchmark System Development Context
- PopKit Design Principles: Workflow automation without human intervention

---

**Status:** Ready for Implementation
**Next Step:** Begin Phase 1 (Foundation)
