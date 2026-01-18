# Benchmark Automation Guide

**Goal**: Run benchmark tests unattended without user interaction

**Status**: ✅ Fully implemented and ready to use

## The Solution

We use a **two-layered approach** to prevent benchmarks from blocking on questions:

1. **Layer 1: Question-Free Prompts** - Design prompts that provide ALL context upfront
2. **Layer 2: Automated Responses** - Pre-defined answers for unexpected questions

## How It Works

### WITH PopKit Trials ✅

**Environment variables automatically set by `benchmark_runner.py`:**

```bash
POPKIT_BENCHMARK_MODE=true
POPKIT_BENCHMARK_RESPONSES=/path/to/responses.json
```

**PopKit skills check before calling `AskUserQuestion`:**

```python
from popkit_shared.utils.benchmark_responses import should_skip_question, get_response

if should_skip_question("Auth method", "What authentication method?"):
    response = get_response("Auth method", "What authentication method?")
    # Use auto-response - no blocking!
else:
    # Normal AskUserQuestion flow
```

**Result**: Questions are auto-answered, trials complete unattended.

### WITHOUT PopKit Baseline Trials ⚠️

**Problem**: PopKit code not available, Claude might still ask questions.

**Solutions**:

1. **Primary**: Write extremely detailed prompts (see PROMPT_GUIDELINES.md)
2. **Fallback**: Manual test guide for rare edge cases
3. **Alternative**: Accept that baseline might need supervision

## Directory Structure

```
packages/popkit-ops/tasks/
└── feature-addition/
    └── jwt-authentication/
        ├── task.yml           ← Task definition with detailed prompt
        └── responses.json     ← Automated responses
```

## Example Task

### task.yml
```yaml
id: jwt-authentication
category: feature-addition
description: Add JWT authentication

user_prompt: |
  Add JWT authentication using jsonwebtoken library.

  Implementation requirements:
  - Algorithm: HS256
  - Expiration: 24 hours
  - Secret: JWT_SECRET environment variable
  - Login endpoint: POST /auth/login
  - Protected routes: /api/*

  DO NOT ASK about implementation details.
  Proceed immediately with these specifications.

verification:
  - npm test
```

### responses.json
```json
{
  "responses": {
    "Auth method": "JWT",
    "Token expiration": "24 hours",
    "Run tests": true
  },
  "standardAutoApprove": [
    "test.*",
    "build.*",
    "install.*"
  ],
  "explicitDeclines": [
    "deploy.*production",
    "delete.*"
  ]
}
```

## Usage

### Run Single Benchmark

```bash
/popkit-ops:benchmark run jwt-authentication --trials 3
```

**What happens**:
1. `benchmark_runner.py` loads `task.yml` and `responses.json`
2. Sets `POPKIT_BENCHMARK_MODE=true` and `POPKIT_BENCHMARK_RESPONSES` env vars
3. For WITH PopKit trials:
   - Launches Claude with PopKit enabled
   - Skills auto-respond to questions
   - Recording saved to `~/.claude/popkit/recordings/`
4. For WITHOUT PopKit baseline:
   - Launches Claude with PopKit disabled
   - Prompt should be detailed enough to avoid questions
   - Recording saved to `~/.claude/projects/` (JSONL)
5. Analyzes both sets of recordings
6. Generates comparison report

### Run All Benchmarks

```bash
/popkit-ops:benchmark run-all --trials 5
```

### Check for Questions

Test if your prompt will ask questions:

```bash
# Without PopKit (baseline test)
claude plugin disable popkit-core popkit-dev popkit-ops
claude -p "$(cat tasks/jwt-authentication/task.yml | yq .user_prompt)"

# Did it ask any questions? If yes, add more detail to prompt.
```

## Response File Locations

`benchmark_runner.py` checks these locations in order:

1. **Alongside task YAML**: `tasks/jwt-authentication/responses.json`
2. **With category**: `tasks/feature-addition/jwt-authentication/responses.json`
3. **Without category**: `tasks/jwt-authentication/responses.json`
4. **Legacy format**: `tasks/feature-addition/jwt-authentication-responses.json`

**First match wins**.

## Creating New Tasks

### Step 1: Write Question-Free Prompt

```yaml
# task.yml
user_prompt: |
  EXTREMELY DETAILED INSTRUCTIONS HERE

  Include:
  - Exact library names and versions
  - All configuration values
  - File paths and names
  - Function signatures
  - Error handling requirements
  - Testing requirements

  DO NOT ASK about implementation choices.
  Proceed immediately.
```

See **PROMPT_GUIDELINES.md** for examples.

### Step 2: Create Response File

```json
{
  "responses": {
    "Expected Question 1": "Answer 1",
    "Expected Question 2": "Answer 2"
  },
  "standardAutoApprove": [
    "test.*",
    "build.*"
  ],
  "explicitDeclines": [
    "deploy.*",
    "delete.*"
  ]
}
```

See **RESPONSE_FILE_SCHEMA.md** for complete reference.

### Step 3: Test Locally

```bash
# Test WITH PopKit
export POPKIT_BENCHMARK_MODE=true
export POPKIT_BENCHMARK_RESPONSES="$(pwd)/tasks/my-task/responses.json"
/popkit-ops:benchmark run my-task --trials 1

# Test WITHOUT PopKit (baseline)
claude plugin disable popkit-core
claude -p "$(cat tasks/my-task/task.yml | yq .user_prompt)"
```

### Step 4: Validate

**Questions to ask**:
- ✅ Did WITH PopKit trial complete without blocking?
- ✅ Did WITHOUT PopKit trial complete without blocking?
- ✅ Were any questions logged by `benchmark_responses.py`?
- ✅ Is the prompt detailed enough?

**If any question was asked**:
1. Add more detail to prompt (preferred)
2. OR add response to `responses.json` (fallback)

## Troubleshooting

### Benchmark Blocked on Question

**Symptoms**: Claude session waiting for user input

**Diagnosis**:
```bash
# Check if benchmark mode is enabled
echo $POPKIT_BENCHMARK_MODE  # Should be "true"

# Check if response file is set
echo $POPKIT_BENCHMARK_RESPONSES  # Should be path to responses.json

# Check if response file exists
ls -l $POPKIT_BENCHMARK_RESPONSES
```

**Solutions**:
1. **For WITH PopKit**: Add response to `responses.json`
2. **For WITHOUT PopKit**: Make prompt more detailed
3. **Both**: Use `standardAutoApprove` patterns for common questions

### Unexpected Auto-Response

**Symptoms**: Wrong option selected automatically

**Diagnosis**:
```bash
# Enable verbose logging
export POPKIT_BENCHMARK_VERBOSE=true
/popkit-ops:benchmark run my-task --trials 1

# Check logs for auto-responses
# [benchmark] Auto-response: <header> = <value>
```

**Solutions**:
1. Check `standardAutoApprove` patterns - are they too broad?
2. Add explicit response for fine-grained control
3. Review prompt - can you eliminate the question?

### Baseline Blocking (No PopKit)

**Symptoms**: Baseline trials block on questions, WITH PopKit works fine

**Root cause**: PopKit code not available for baseline, only JSONL recording

**Solutions**:
1. **Best**: Rewrite prompt to be more detailed (eliminates question)
2. **Acceptable**: Document expected questions in test guide
3. **Workaround**: Have someone monitor baseline trials and answer questions

## Implementation Details

### Files Involved

1. **`benchmark_responses.py`** (`shared-py/popkit_shared/utils/`)
   - Loads response file
   - Checks if question should be auto-answered
   - Returns pre-defined response

2. **`benchmark_runner.py`** (`pop-benchmark-runner/scripts/`)
   - Sets `POPKIT_BENCHMARK_MODE=true`
   - Finds and loads response file
   - Sets `POPKIT_BENCHMARK_RESPONSES` env var
   - Launches Claude sessions

3. **PopKit Skills** (throughout codebase)
   - Check `is_benchmark_mode()` before `AskUserQuestion`
   - Use `get_response()` if in benchmark mode
   - Fall back to normal flow if not

### Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `POPKIT_BENCHMARK_MODE` | `true` | Enable automated responses |
| `POPKIT_BENCHMARK_RESPONSES` | `/path/to/responses.json` | Response definitions |
| `POPKIT_BENCHMARK_VERBOSE` | `true` | Log auto-responses (debugging) |

### Response File Format

```json
{
  "responses": {
    "Question Header": "Answer",
    ...
  },
  "standardAutoApprove": ["pattern1", "pattern2"],
  "explicitDeclines": ["pattern1", "pattern2"]
}
```

**Matching priority**:
1. `explicitDeclines` (safety first)
2. `responses[header]` (exact match)
3. `standardAutoApprove` (pattern match)
4. Default: auto-select first option

## Best Practices

### ✅ DO

- Write extremely detailed prompts
- Include ALL technical specifications
- Add "DO NOT ASK" directive to prompts
- Use `standardAutoApprove` for safe operations
- Use `explicitDeclines` for dangerous operations
- Test both WITH and WITHOUT PopKit

### ❌ DON'T

- Assume context from previous conversations
- Leave open-ended choices in prompts
- Rely solely on response files (prefer detailed prompts)
- Use overly broad auto-approve patterns
- Skip testing baseline (WITHOUT PopKit)

## Example Workflow

```bash
# 1. Create task definition
cat > tasks/my-task/task.yml <<EOF
id: my-task
user_prompt: |
  EXTREMELY DETAILED INSTRUCTIONS...
  DO NOT ASK QUESTIONS.
EOF

# 2. Create response file
cat > tasks/my-task/responses.json <<EOF
{
  "responses": {"Key": "Value"},
  "standardAutoApprove": ["test.*"]
}
EOF

# 3. Test WITH PopKit
export POPKIT_BENCHMARK_MODE=true
export POPKIT_BENCHMARK_RESPONSES="$(pwd)/tasks/my-task/responses.json"
/popkit-ops:benchmark run my-task --trials 1

# 4. Test WITHOUT PopKit
claude plugin disable popkit-core
claude -p "$(cat tasks/my-task/task.yml | yq .user_prompt)"

# 5. Run full benchmark
/popkit-ops:benchmark run my-task --trials 5
```

## See Also

- **RESPONSE_FILE_SCHEMA.md** - Complete response file reference
- **PROMPT_GUIDELINES.md** - Writing question-free prompts
- **TASK_DEFINITION_SCHEMA.md** - Full task YAML format
- **benchmark_responses.py** - Implementation source code
