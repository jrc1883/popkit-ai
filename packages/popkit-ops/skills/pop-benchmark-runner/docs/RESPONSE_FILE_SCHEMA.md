# Benchmark Response File Schema

**Purpose**: Automate responses to `AskUserQuestion` during benchmark execution

**Location**: Store alongside task definitions (e.g., `tasks/my-task/responses.json`)

## Full Schema

```json
{
  "responses": {
    "<question_header>": "<response>",
    ...
  },
  "standardAutoApprove": [
    "<regex_pattern>",
    ...
  ],
  "explicitDeclines": [
    "<regex_pattern>",
    ...
  ]
}
```

## Field Descriptions

### `responses` (Required)
**Type**: `Object<string, string | boolean | string[] | object>`

Map of question headers to their responses.

**Key**: The `header` field from `AskUserQuestion` (e.g., "Auth method", "Database", "Deploy target")

**Value types**:
- **String**: Single selection (matches option label exactly)
- **Boolean**:
  - `true` = Auto-approve (select first/recommended option)
  - `false` = Decline (select last option or "no")
- **Array of strings**: Multi-selection (for `multiSelect: true` questions)
- **Object with `other` key**: Free-text response for "Other" option

**Examples**:
```json
{
  "responses": {
    "Auth method": "JWT",                              // Single select
    "Database": "PostgreSQL",                          // Single select
    "Features": ["caching", "rate-limiting"],          // Multi-select
    "Custom config": {"other": "port=8080,ssl=true"},  // Free text
    "Run tests": true,                                 // Auto-approve
    "Deploy to production": false                      // Decline
  }
}
```

### `standardAutoApprove` (Optional)
**Type**: `Array<string>`

Regex patterns for questions that should be auto-approved without explicit responses.

**Behavior**: When a question text matches any pattern, automatically select the first/recommended option.

**Use cases**:
- Common operations: tests, builds, linting
- Safe actions that should always proceed
- Developer workflow steps

**Examples**:
```json
{
  "standardAutoApprove": [
    "test.*",           // "run tests?", "test coverage?", etc.
    "build.*",          // "build project?", "build docker image?", etc.
    "lint.*",           // "run linter?", "lint --fix?", etc.
    "install.*",        // "install dependencies?", etc.
    "format.*"          // "format code?", etc.
  ]
}
```

### `explicitDeclines` (Optional)
**Type**: `Array<string>`

Regex patterns for questions that should ALWAYS be declined.

**Behavior**: When a question text matches any pattern, automatically select "no" or the last option.

**Use cases**:
- Dangerous operations: production deploys, data deletion
- Operations that would break automation
- Actions requiring manual verification

**Examples**:
```json
{
  "explicitDeclines": [
    "deploy to production",
    "delete.*",
    "drop database",
    "force push.*",
    "publish to npm"
  ]
}
```

## Matching Priority

Responses are evaluated in this order:

1. **`explicitDeclines`** - Always checked first (safety first!)
2. **`responses[header]`** - Exact header match
3. **`standardAutoApprove`** - Pattern match on question text
4. **Default**: Auto-select first option (prevents blocking)

## Complete Example

```json
{
  "responses": {
    "Auth method": "JWT",
    "Token expiration": "24 hours",
    "Database": "PostgreSQL",
    "Enable caching": true,
    "Features to enable": ["rate-limiting", "logging", "metrics"],
    "Custom middleware": {"other": "cors,helmet,compression"}
  },
  "standardAutoApprove": [
    "run tests",
    "run build",
    "run lint",
    "install dependencies",
    "format code",
    "add to git"
  ],
  "explicitDeclines": [
    "deploy to production",
    "delete.*",
    "drop.*database",
    "force push",
    "publish.*"
  ]
}
```

## Task Definition Integration

### Directory Structure
```
tasks/
├── jwt-authentication/
│   ├── task.yml
│   └── responses.json     ← Response file
├── race-condition-fix/
│   ├── task.yml
│   └── responses.json
└── ...
```

### Task Definition (YAML)
```yaml
id: jwt-authentication
category: feature-addition
description: Add JWT authentication

user_prompt: |
  Add JWT authentication using jsonwebtoken library.

  Use these defaults:
  - Algorithm: HS256
  - Expiration: 24 hours
  - Secret: JWT_SECRET from .env

  NO questions about implementation details - proceed immediately.

verification:
  - npm test
  - npm run test:auth
```

### Response File (`responses.json`)
```json
{
  "responses": {
    "Auth method": "JWT",
    "Token expiration": "24 hours"
  },
  "standardAutoApprove": [
    "test.*",
    "build.*"
  ],
  "explicitDeclines": [
    "deploy.*"
  ]
}
```

## Usage in Benchmark Runner

```python
# benchmark_runner.py automatically sets:
os.environ["POPKIT_BENCHMARK_MODE"] = "true"
os.environ["POPKIT_BENCHMARK_RESPONSES"] = str(response_file_path)

# Then launches Claude:
subprocess.run(["claude", "-p", task_prompt], env=env)
```

## Usage in PopKit Skills

Skills should check benchmark mode before calling `AskUserQuestion`:

```python
from popkit_shared.utils.benchmark_responses import (
    is_benchmark_mode,
    get_response,
    should_skip_question,
    log_benchmark_response
)

# Before AskUserQuestion:
if should_skip_question("Auth method", "What authentication method?"):
    response = get_response("Auth method", "What authentication method?")
    log_benchmark_response("Auth method", "What authentication method?", response)
    # Use response directly
else:
    # Normal AskUserQuestion flow
    response = ask_user_question(...)
```

## Design Guidelines

### 1. Minimize Questions in Prompts

**Bad prompt** (will ask many questions):
```yaml
user_prompt: "Add JWT authentication"
```

**Good prompt** (provides all context):
```yaml
user_prompt: |
  Add JWT authentication using jsonwebtoken library.

  Requirements:
  - Use HS256 algorithm with secret from .env (JWT_SECRET)
  - Implement /auth/login endpoint (POST)
  - Return token valid for 24 hours
  - Add middleware to verify tokens
  - Protect /api/* routes with auth middleware

  Do NOT ask for implementation preferences - use these defaults.
  Proceed immediately with implementation.
```

### 2. Provide Responses for All Expected Questions

If Claude might ask a question, define a response:
```json
{
  "responses": {
    "Database type": "PostgreSQL",
    "Port number": "5432",
    "Use connection pooling": true,
    "Max connections": {"other": "20"}
  }
}
```

### 3. Use Patterns for Repetitive Questions

Instead of:
```json
{
  "responses": {
    "Run tests": true,
    "Run unit tests": true,
    "Run integration tests": true,
    "Run e2e tests": true
  }
}
```

Use:
```json
{
  "standardAutoApprove": ["test.*", "run.*test.*"]
}
```

### 4. Safety First with Explicit Declines

Always decline dangerous operations:
```json
{
  "explicitDeclines": [
    "deploy to production",
    "delete.*",
    "drop.*",
    "force.*push",
    "publish.*npm"
  ]
}
```

## Troubleshooting

### Question Still Blocking Benchmark?

**Check**:
1. Is `POPKIT_BENCHMARK_MODE=true` set?
2. Is `POPKIT_BENCHMARK_RESPONSES` pointing to correct file?
3. Does response file have valid JSON?
4. Is skill checking `should_skip_question()` before `AskUserQuestion`?
5. Does question header match exactly (case-sensitive)?

**Debug**:
```bash
export POPKIT_BENCHMARK_VERBOSE=true
# Now benchmark_responses.py logs all auto-responses
```

### Unexpected Auto-Responses?

**Check**:
1. Review `standardAutoApprove` patterns - are they too broad?
2. Check default behavior (auto-selects first option if no match)
3. Add explicit responses for fine-grained control

### Response Not Applied?

**Common issues**:
- Header mismatch: `"auth method"` vs `"Auth method"` (case matters!)
- Pattern syntax: Use regex, not glob (`test.*` not `test*`)
- JSON syntax: Trailing commas break JSON
- File path: Response file must exist and be readable

## Testing Response Files

```bash
# Test response file is valid JSON
python -m json.tool tasks/my-task/responses.json

# Test benchmark mode locally
export POPKIT_BENCHMARK_MODE=true
export POPKIT_BENCHMARK_RESPONSES="$(pwd)/tasks/my-task/responses.json"
/popkit-ops:benchmark run my-task --trials 1
```

## Examples by Category

### Feature Addition
```json
{
  "responses": {
    "Implementation approach": "Incremental",
    "Add tests": true,
    "Framework": "Express.js"
  },
  "standardAutoApprove": ["test.*", "build.*", "commit.*"]
}
```

### Bug Fixing
```json
{
  "responses": {
    "Fix approach": "Root cause",
    "Add regression test": true
  },
  "standardAutoApprove": ["test.*", "verify.*"]
}
```

### Refactoring
```json
{
  "responses": {
    "Refactor scope": "Single file",
    "Run tests after": true,
    "Update documentation": true
  },
  "standardAutoApprove": ["test.*", "lint.*"]
}
```

### Performance Optimization
```json
{
  "responses": {
    "Optimization target": "Database queries",
    "Run benchmarks": true,
    "Profile first": true
  },
  "standardAutoApprove": ["test.*", "benchmark.*", "measure.*"]
}
```

## See Also

- `benchmark_responses.py` - Implementation details
- `TASK_DEFINITION_SCHEMA.md` - Full task format
- `PROMPT_GUIDELINES.md` - Writing question-free prompts
