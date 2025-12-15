# PopKit Workflow Benchmark Testing Design

> **For Claude:** Use `/popkit:dev execute` to implement this plan.

**Goal:** Enable benchmarking of PopKit workflows (not just plugin enabled/disabled) by handling interactive `AskUserQuestion` prompts programmatically.

**Related Issues:** #220 (Benchmark Suite), #236 (Benchmark Context)

---

## Problem Statement

Current benchmark approach only tests:
- **Vanilla**: Claude Code without PopKit plugin
- **PopKit**: Claude Code with PopKit plugin enabled

This doesn't measure PopKit's **actual value** because:
1. Simply enabling the plugin doesn't invoke workflows
2. Workflows like `/popkit:dev full` use interactive `AskUserQuestion` prompts
3. Benchmarks can't wait for human input

**Goal:** Test full PopKit workflows by programmatically handling AskUserQuestion.

---

## Research Findings

### Hook-Level Interception (NOT Feasible)

Research confirmed that Claude Code's hook protocol cannot intercept AskUserQuestion:

| Limitation | Reason |
|-----------|--------|
| Tool Protocol | Hooks only receive tool output, not input |
| Execution Order | Hooks run after user has already responded |
| No Return Mechanism | Hooks can't synthesize answers |
| Design Intent | AskUserQuestion is for human decisions |

**Conclusion:** Skill-level override is the only viable approach.

---

## Architecture Design

### Hybrid AskUserQuestion Handling

```
Benchmark Runner
├── Sets: POPKIT_BENCHMARK_MODE=true
├── Sets: POPKIT_BENCHMARK_RESPONSES=/path/to/responses.json
└── Invokes Claude with workflow command

PopKit Skills (modified)
├── Check: if POPKIT_BENCHMARK_MODE
│   ├── Standard prompts → auto-select first/recommended option
│   ├── Complex prompts → lookup in responses file
│   └── Unknown prompts → default to first option + log
└── Otherwise → normal AskUserQuestion prompt
```

### Response Categories

| Category | Handling | Example |
|----------|----------|---------|
| Standard | Auto-approve first option | "Continue?", "Proceed?", "Commit?" |
| Complex | Lookup in task responses | "Auth method?", "Framework?" |
| Dangerous | Always decline | "Create GitHub repo?", "Push to remote?" |
| Unknown | Default to first + log | Unexpected prompts |

---

## Implementation Plan

### Task 1: Extended Task Schema

**Files:**
- Modify: `packages/benchmarks/src/types.ts`
- Create: `packages/benchmarks/tasks/popkit/` (directory)

**Changes:**

Add new fields to BenchmarkTask interface:

```typescript
interface BenchmarkTask {
  // Existing fields...

  // New fields for PopKit workflow testing
  workflowType?: 'vanilla' | 'popkit' | 'power';
  workflowCommand?: string;  // e.g., "/popkit:dev full user authentication"

  benchmarkResponses?: {
    [questionHeader: string]: string | string[] | boolean | { other: string };
  };

  standardAutoApprove?: string[];  // Regex patterns
  explicitDeclines?: string[];     // Always decline (GitHub operations, etc.)
}
```

**Step 1: Update types.ts**

Add the new interface fields above.

**Step 2: Create popkit task directory**

```bash
mkdir packages/benchmarks/tasks/popkit
```

---

### Task 2: Benchmark Runner Updates

**Files:**
- Modify: `packages/benchmarks/src/runners/claude-runner.ts`

**Changes:**

1. Set environment variables for benchmark mode:

```typescript
// In runClaudeCli method, add to env:
env: {
  ...process.env,
  CI: 'true',
  POPKIT_BENCHMARK_MODE: 'true',
  POPKIT_BENCHMARK_RESPONSES: this.createResponseFile(task),
}
```

2. Handle workflowCommand:

```typescript
// In execute method, modify prompt building:
let prompt = task.prompt;
if (task.workflowCommand) {
  prompt = `${task.workflowCommand}\n\n${task.prompt}`;
}
```

3. Create response file helper:

```typescript
private createResponseFile(task: BenchmarkTask): string {
  if (!task.benchmarkResponses) return '';

  const tempFile = join(this.workDir, 'benchmark-responses.json');
  writeFileSync(tempFile, JSON.stringify({
    responses: task.benchmarkResponses,
    standardAutoApprove: task.standardAutoApprove || [
      'Continue.*', 'Proceed.*', 'Commit.*', 'What.*next.*'
    ],
    explicitDeclines: task.explicitDeclines || [
      'Create.*repo', 'Push.*remote', 'Create.*issue', 'gh.*create'
    ]
  }));
  return tempFile;
}
```

---

### Task 3: Benchmark Response Utility

**Files:**
- Create: `packages/plugin/hooks/utils/benchmark_responses.py`

**Purpose:** Shared utility for skills to check benchmark mode and get responses.

```python
"""
Benchmark response utility for PopKit skills.

When POPKIT_BENCHMARK_MODE is set, skills can use this module
to get pre-defined responses instead of calling AskUserQuestion.
"""

import os
import json
import re
from typing import Optional, Dict, Any, Union

BENCHMARK_MODE = os.environ.get('POPKIT_BENCHMARK_MODE') == 'true'
RESPONSE_FILE = os.environ.get('POPKIT_BENCHMARK_RESPONSES', '')

_responses_cache: Optional[Dict[str, Any]] = None


def is_benchmark_mode() -> bool:
    """Check if running in benchmark mode."""
    return BENCHMARK_MODE


def load_responses() -> Dict[str, Any]:
    """Load benchmark responses from file."""
    global _responses_cache
    if _responses_cache is not None:
        return _responses_cache

    if not RESPONSE_FILE or not os.path.exists(RESPONSE_FILE):
        _responses_cache = {}
        return _responses_cache

    with open(RESPONSE_FILE, 'r') as f:
        _responses_cache = json.load(f)
    return _responses_cache


def get_response(question_header: str, question_text: str = '') -> Optional[Union[str, bool, list]]:
    """Get pre-defined response for a question.

    Args:
        question_header: The header of the AskUserQuestion (e.g., "Auth method")
        question_text: Full question text for pattern matching

    Returns:
        Pre-defined response or None if should prompt user
    """
    if not is_benchmark_mode():
        return None

    data = load_responses()

    # Check explicit declines first (always return false/no)
    for pattern in data.get('explicitDeclines', []):
        if re.search(pattern, question_text, re.IGNORECASE):
            return False

    # Check for explicit response
    responses = data.get('responses', {})
    if question_header in responses:
        return responses[question_header]

    # Check standard auto-approve patterns
    for pattern in data.get('standardAutoApprove', []):
        if re.search(pattern, question_text, re.IGNORECASE):
            return True  # Select first/recommended option

    # Default: return True to auto-select first option
    return True


def should_skip_question(question_header: str, question_text: str = '') -> bool:
    """Check if we should skip AskUserQuestion and use default."""
    return is_benchmark_mode() and get_response(question_header, question_text) is not None
```

---

### Task 4: Skill Template Update

**Files:**
- Modify: Key skills that use AskUserQuestion

**Skills to update:**
- `pop-brainstorming/SKILL.md`
- `pop-writing-plans/SKILL.md`
- `pop-project-init/SKILL.md`
- `pop-finish-branch/SKILL.md`

**Add to each skill's instructions:**

```markdown
## Benchmark Mode

When `POPKIT_BENCHMARK_MODE` environment variable is set:

1. Before calling AskUserQuestion, check for pre-defined response:
   - Load responses from `POPKIT_BENCHMARK_RESPONSES` file
   - Match question header to response key
   - If match found, use that response without prompting

2. For standard continuation prompts ("Continue?", "Proceed?"):
   - Auto-select first option

3. For GitHub operations ("Create repo?", "Push?"):
   - Always select "No" to prevent side effects

4. Log which responses were auto-selected for debugging
```

---

### Task 5: Create PopKit Benchmark Tasks

**Files:**
- Create: `packages/benchmarks/tasks/popkit/dev-auth.json`
- Create: `packages/benchmarks/tasks/popkit/project-init.json`
- Create: `packages/benchmarks/tasks/popkit/quick-fix.json`

**Example: dev-auth.json**

```json
{
  "id": "popkit-dev-auth",
  "name": "User Authentication via PopKit Dev Workflow",
  "description": "Build OAuth authentication using /popkit:dev full workflow",
  "category": "feature",
  "language": "typescript",
  "framework": "nextjs",

  "workflowType": "popkit",
  "workflowCommand": "/popkit:dev full user authentication with OAuth",

  "prompt": "Create a user authentication system with Google and GitHub OAuth providers. Use NextAuth.js with a PostgreSQL database.",

  "benchmarkResponses": {
    "Auth method": "OAuth providers",
    "OAuth provider": ["Google", "GitHub"],
    "Database": "PostgreSQL",
    "Session storage": "JWT",
    "Additional requirements": {
      "other": "Include rate limiting on login attempts"
    }
  },

  "standardAutoApprove": [
    "Continue to next phase",
    "Proceed with",
    "Approve.*architecture",
    "Commit"
  ],

  "explicitDeclines": [
    "Create.*GitHub.*repo",
    "Push.*remote",
    "Create.*issue"
  ],

  "initialFiles": {
    "package.json": "{\n  \"name\": \"auth-benchmark\",\n  \"version\": \"1.0.0\",\n  \"dependencies\": {\n    \"next\": \"14.0.0\",\n    \"react\": \"18.2.0\"\n  }\n}",
    "tsconfig.json": "{\n  \"compilerOptions\": {\n    \"target\": \"ES2022\",\n    \"strict\": true\n  }\n}"
  },

  "tests": [
    {
      "id": "auth-files-exist",
      "name": "Authentication files created",
      "command": "node -e \"const fs=require('fs'); const files=['src/app/api/auth', 'src/lib/auth']; const exists=files.some(f=>fs.existsSync(f)); process.exit(exists?0:1)\""
    },
    {
      "id": "oauth-config",
      "name": "OAuth providers configured",
      "command": "node -e \"const fs=require('fs'); const c=fs.readFileSync('src/lib/auth.ts','utf8'); process.exit(c.includes('Google')&&c.includes('GitHub')?0:1)\""
    }
  ],

  "qualityChecks": [
    {
      "id": "typescript-valid",
      "name": "TypeScript compiles",
      "command": "npx tsc --noEmit"
    }
  ],

  "timeoutSeconds": 600,
  "minSuccessRate": 0.8
}
```

---

### Task 6: Update Benchmark Status Documentation

**Files:**
- Modify: `packages/benchmarks/STATUS.json`
- Modify: `packages/benchmarks/README.md`

**Updates:**

Add PopKit workflow testing status and documentation for the new task format.

---

## Acceptance Criteria

- [ ] Task schema supports `workflowCommand` and `benchmarkResponses`
- [ ] Benchmark runner sets `POPKIT_BENCHMARK_MODE` environment variable
- [ ] `benchmark_responses.py` utility created and tested
- [ ] At least 3 PopKit workflow benchmark tasks created
- [ ] Can run: `npx tsx run-benchmark.ts popkit-dev-auth popkit`
- [ ] Results capture workflow phases (exploration, architecture, implementation)
- [ ] No GitHub side effects (repos, issues) during benchmark runs

---

## Future Enhancements

1. **Workflow Phase Metrics**: Track time spent in each phase (discovery, exploration, etc.)
2. **Skill Invocation Tracking**: Log which skills were invoked during workflow
3. **Response Quality Analysis**: Compare generated code when using different responses
4. **A/B Testing**: Same prompt with different response configurations

---

## Related Files

| File | Purpose |
|------|---------|
| `packages/benchmarks/src/types.ts` | Task schema definitions |
| `packages/benchmarks/src/runners/claude-runner.ts` | Benchmark execution |
| `packages/plugin/hooks/utils/benchmark_responses.py` | Response lookup utility |
| `packages/plugin/skills/pop-brainstorming/SKILL.md` | Example skill to update |

---

*Generated from brainstorming session 2025-12-15*
