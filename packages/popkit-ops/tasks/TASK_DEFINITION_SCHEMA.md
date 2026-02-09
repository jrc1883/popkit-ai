# Benchmark Task Definition Schema

## Overview

Benchmark tasks are defined in YAML format. This allows users to easily create custom benchmarks for their own applications.

## File Location

Tasks are organized by category:

```
packages/popkit-ops/tasks/
├── feature-addition/
├── bug-fixing/
├── refactoring/
└── code-review/
```

Each task consists of two files:

1. `<task-id>.yml` - Task definition
2. `<task-id>-responses.json` - Automated responses for benchmark mode

## Complete YAML Schema

```yaml
# ============================================================================
# REQUIRED FIELDS
# ============================================================================

id:
  string
  # Unique identifier for this task (lowercase, hyphens)
  # Example: jwt-authentication, race-condition-fix

category:
  enum
  # One of: feature-addition | bug-fixing | refactoring | code-review

description:
  string
  # One-line summary of the task
  # Example: "Add JWT-based user authentication to Express API"

user_prompt:
  string (multiline)
  # Complete task instructions that will be given to Claude Code
  # Should be detailed, specific, and actionable
  # Include: requirements, expected behavior, edge cases, testing needs

# ============================================================================
# OPTIONAL FIELDS (but recommended)
# ============================================================================

# --- Codebase Configuration ---
codebase:
  string
  # Name of the demo codebase to use
  # Example: demo-app-express, demo-app-react, custom-repo-url

initial_state:
  string
  # Git ref to checkout before starting task
  # Options: branch name, tag, commit hash, "main", "HEAD"
  # Default: "main"

difficulty:
  enum
  # Estimated difficulty level
  # Options: easy | medium | hard | expert
  # Used for: filtering, reporting, time estimation

# --- File Tracking ---
expected_files:
  list[string]
  # Files expected to be created or modified
  # Used for: verification, change detection
  # Example:
  #   - "src/routes/auth.js"
  #   - "src/middleware/authenticate.js"

# --- Verification ---
verification:
  list[string]
  # Commands to run after task completion
  # Exit code 0 = pass, non-zero = fail
  # Example:
  #   - npm test
  #   - npm run lint
  #   - npx tsc --noEmit
  #   - python -m pytest
  #   - cargo test

expected_outcomes:
  list[string]
  # Human-readable outcomes to verify
  # Used for: documentation, validation
  # Example:
  #   - "POST /auth/login endpoint exists"
  #   - "Tests pass for authentication flow"

# --- Time & Dependencies ---
estimated_duration_minutes:
  int
  # Expected completion time in minutes
  # Used for: benchmarking, timeouts, reporting

dependencies:
  list[string]
  # npm/pip/cargo packages that may need installation
  # Example:
  #   - jsonwebtoken
  #   - bcrypt
  #   - pytest-asyncio

# ============================================================================
# ADVANCED FIELDS (optional)
# ============================================================================

# --- Environment Configuration ---
environment:
  object
  # Environment variables needed for this task
  # Example:
  #   NODE_ENV: test
  #   DATABASE_URL: sqlite::memory:
  #   LOG_LEVEL: debug

pre_setup_commands:
  list[string]
  # Commands to run before starting task
  # Example:
  #   - npm install
  #   - python -m venv venv
  #   - source venv/bin/activate

post_setup_commands:
  list[string]
  # Commands to run after task completion
  # Example:
  #   - npm run build
  #   - docker-compose down

# --- Codebase Constraints ---
codebase_constraints:
  object
  # Constraints for code changes
  # Example:
  #   max_files_changed: 10
  #   allowed_directories:
  #     - src/
  #     - tests/
  #   forbidden_patterns:
  #     - "console.log"
  #     - "debugger"

# --- Success Criteria ---
success_criteria:
  object
  # Detailed success criteria beyond verification commands
  # Example:
  #   performance:
  #     max_response_time_ms: 500
  #   security:
  #     no_secrets_in_code: true
  #   coverage:
  #     min_line_coverage: 80

# --- Metadata ---
tags:
  list[string]
  # Tags for filtering/searching tasks
  # Example:
  #   - authentication
  #   - security
  #   - api

author:
  string
  # Task creator (for template gallery)

created_at:
  string (ISO 8601)
  # Creation timestamp

version:
  string (semver)
  # Task definition version

# --- Related Tasks ---
related_tasks:
  list[string]
  # IDs of related tasks
  # Example:
  #   - oauth-implementation
  #   - session-management

prerequisites:
  list[string]
  # Tasks that should be completed first
  # Example:
  #   - user-model-creation
  #   - database-setup
```

## Minimal Example

```yaml
id: simple-feature
category: feature-addition
description: Add health check endpoint
user_prompt: |
  Create a GET /health endpoint that returns:
  - Status: "ok"
  - Timestamp: current ISO timestamp
  - Uptime: process uptime in seconds
```

## Complete Example

```yaml
id: jwt-authentication
category: feature-addition
description: Add JWT-based user authentication to Express API
codebase: demo-app-express
initial_state: main
difficulty: medium

user_prompt: |
  Implement JWT authentication with:
  1. POST /auth/login endpoint
  2. Authentication middleware
  3. Protect existing routes
  4. Error handling
  5. Testing

expected_files:
  - "src/routes/auth.js"
  - "src/middleware/authenticate.js"
  - "tests/auth.test.js"

verification:
  - npm test
  - npm run lint
  - npx tsc --noEmit

expected_outcomes:
  - "Login endpoint exists"
  - "Protected routes return 401 without token"
  - "All tests pass"

estimated_duration_minutes: 8

dependencies:
  - jsonwebtoken
  - bcrypt

environment:
  NODE_ENV: test
  JWT_SECRET: test-secret-key

tags:
  - authentication
  - security
  - jwt

author: PopKit Team
version: 1.0.0
```

## Benchmark Responses File

Companion JSON file for automated responses during benchmark execution:

```json
{
  "responses": {
    "Question Header": "Selected answer",
    "Auth method": "JWT (jsonwebtoken)",
    "Token storage": "HTTP-only cookies"
  },
  "standardAutoApprove": ["install.*dependencies", "run.*tests", "commit.*changes"],
  "explicitDeclines": []
}
```

## Creating Your Own Task

### Step 1: Create YAML file

```bash
# Choose appropriate category
cd packages/popkit-ops/tasks/feature-addition/

# Create your task definition
touch my-custom-task.yml
```

### Step 2: Define task

```yaml
id: my-custom-task
category: feature-addition
description: Your task description here
user_prompt: |
  Detailed instructions for Claude Code...
verification:
  - npm test
```

### Step 3: Create responses file (optional)

```bash
touch my-custom-task-responses.json
```

```json
{
  "responses": {
    "Your question": "Your answer"
  },
  "standardAutoApprove": ["test.*", "lint.*"]
}
```

### Step 4: Run benchmark

```bash
/popkit-ops:benchmark run my-custom-task --trials 3
```

## Task Template Gallery (Future)

Vision for community-contributed tasks:

```
popkit-cloud.com/benchmarks/
├── official/          # PopKit team tasks
├── community/         # User-submitted tasks
└── private/           # Organization-specific tasks
```

Users will be able to:

- Browse task templates
- Download YAML definitions
- Submit their own tasks
- Rate and comment on tasks
- Filter by language, framework, difficulty

## Best Practices

### 1. Clear Instructions

```yaml
user_prompt: |
  # Good: Specific and actionable
  Create GET /users endpoint that:
  - Returns array of users from database
  - Supports pagination (?page=N&limit=M)
  - Returns 400 for invalid params

  # Bad: Vague
  Add user endpoint
```

### 2. Verification Commands

```yaml
# Good: Multiple verification layers
verification:
  - npm test                    # Unit tests
  - npm run test:integration    # Integration tests
  - npm run lint                # Code quality
  - npx tsc --noEmit           # Type checking

# Bad: Single verification
verification:
  - npm test
```

### 3. Expected Outcomes

```yaml
# Good: Specific, measurable
expected_outcomes:
  - "GET /users returns 200 status"
  - "Pagination params validated"
  - "Test coverage above 80%"

# Bad: Generic
expected_outcomes:
  - "Endpoint works"
```

### 4. Realistic Time Estimates

```yaml
# Consider:
# - Reading existing code
# - Implementing feature
# - Writing tests
# - Debugging
estimated_duration_minutes: 15 # Be generous!
```

## Validation

Before running a benchmark, validate your YAML:

```bash
# Validate syntax
python -c "import yaml; yaml.safe_load(open('my-task.yml'))"

# Validate schema (future)
/popkit-ops:benchmark validate my-task.yml
```

## Output Integration

### Local Output (Current)

- Markdown: `docs/benchmark/results/my-task-YYYY-MM-DD.md`
- HTML: `docs/benchmark/results/my-task-YYYY-MM-DD.html`
- JSON: `docs/benchmark/results/my-task-YYYY-MM-DD.json`

### PopKit Cloud (Future)

- Automatic upload if subscribed
- Historical trend analysis
- Embedding-based insights
- Cross-project comparison
- Team dashboards

```bash
# Future: Cloud integration
/popkit-ops:benchmark run my-task --upload-cloud
# → Results at https://popkit-cloud.com/benchmarks/my-task/latest
```

## Contributing Tasks

Want to share your benchmark tasks?

1. Create task YAML + responses JSON
2. Test locally: `/popkit-ops:benchmark run your-task --trials 3`
3. Submit PR to `packages/popkit-ops/tasks/`
4. Tag: `benchmark-task`
5. Include: README with task rationale

Community tasks help everyone measure PopKit's value on diverse workloads!
