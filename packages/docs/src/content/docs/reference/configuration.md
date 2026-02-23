---
title: Configuration Reference
description: Complete reference for all PopKit configuration files and options
---

# Configuration Reference

PopKit uses a layered configuration system with project-local files. This reference documents all configuration files, their locations, and available options.

## File Locations

| File                             | Purpose                          | Scope            |
| -------------------------------- | -------------------------------- | ---------------- |
| `.claude/popkit/config.json`     | Project settings and preferences | Per-project      |
| `.claude/popkit/routines.json`   | Routine definitions and defaults | Per-project      |
| `.claude/popkit/state.json`      | Runtime state (auto-managed)     | Per-project      |
| `STATUS.json`                    | Session state for continuity     | Per-project root |
| `.claude/popkit/measurements/`   | Performance metrics (optional)   | Per-project      |
| `.claude/popkit/routines/<type>` | Custom routine definitions       | Per-project      |

---

## config.json

Project-level PopKit configuration.

### Location

```
<project-root>/.claude/popkit/config.json
```

### Schema

```json
{
  "project_name": "string",
  "prefix": "string",
  "defaults": {
    "morning": "string",
    "nightly": "string"
  },
  "routines": {
    "morning": [],
    "nightly": []
  }
}
```

### Fields

| Field              | Type   | Default       | Description                                |
| ------------------ | ------ | ------------- | ------------------------------------------ |
| `project_name`     | string | (auto-detect) | Human-readable project name                |
| `prefix`           | string | (generated)   | Short prefix for custom routine IDs        |
| `defaults.morning` | string | `"pk"`        | Default morning routine ID                 |
| `defaults.nightly` | string | `"pk"`        | Default nightly routine ID                 |
| `routines.morning` | array  | `[]`          | List of custom morning routine definitions |
| `routines.nightly` | array  | `[]`          | List of custom nightly routine definitions |

### Prefix Generation

The `prefix` is auto-generated from your project name:

| Project Name       | Generated Prefix |
| ------------------ | ---------------- |
| `Reseller Central` | `rc`             |
| `My Awesome App`   | `maa`            |
| `genesis`          | `gen`            |
| `popkit`           | `pop`            |

Custom routines use this prefix: `rc-1`, `rc-2`, etc.

### Example

```json
{
  "project_name": "Reseller Central",
  "prefix": "rc",
  "defaults": {
    "morning": "rc-1",
    "nightly": "pk"
  },
  "routines": {
    "morning": [
      {
        "id": "rc-1",
        "name": "Full Stack Check",
        "description": "Includes database and Redis health",
        "created": "2024-01-15T08:00:00Z",
        "based_on": "pk"
      }
    ],
    "nightly": []
  }
}
```

---

## routines.json

Detailed routine configuration (legacy format, merging into config.json).

### Location

```
<project-root>/.claude/popkit/routines.json
```

### Schema

```json
{
  "morning": {
    "default": "string",
    "routines": {
      "<id>": {
        "name": "string",
        "checks": []
      }
    }
  },
  "nightly": {
    "default": "string",
    "routines": {}
  }
}
```

---

## Routine Profiles

Pre-configured flag combinations for common use cases.

### Available Profiles

| Profile    | Flags Applied                                             | Use Case                    |
| ---------- | --------------------------------------------------------- | --------------------------- |
| `minimal`  | `--quick --skip-tests --skip-services --skip-deployments` | Fast health check (< 10s)   |
| `standard` | (defaults)                                                | Normal daily routine (~20s) |
| `thorough` | `--full --measure`                                        | Deep analysis (~60s)        |
| `ci`       | `--optimized --measure --simple --no-cache`               | CI/CD pipelines             |

### Usage

```bash
/popkit-dev:routine morning --profile minimal
/popkit-dev:routine morning --profile thorough
```

### Profile Flag Details

| Flag                 | Effect                                     |
| -------------------- | ------------------------------------------ |
| `--quick`            | One-line summary instead of full report    |
| `--skip-tests`       | Skip test execution                        |
| `--skip-services`    | Skip service health checks                 |
| `--skip-deployments` | Skip deployment status check               |
| `--full`             | Include all checks (slower)                |
| `--measure`          | Track performance metrics                  |
| `--optimized`        | Use caching for efficiency                 |
| `--simple`           | Markdown tables instead of ASCII dashboard |
| `--no-cache`         | Force fresh execution, bypass cache        |
| `--no-nightly`       | Skip "From Last Night" section             |
| `--no-upstream`      | Skip Anthropic upstream update check       |

### Smart Defaults

Some flags automatically enable others:

- `--measure` enables `--simple` (for parseable output)
- `--full` overrides `--optimized` (thorough checks can't be cached)

---

## STATUS.json

Session state file for cross-session continuity.

### Location

```
<project-root>/STATUS.json
```

### Schema

```json
{
  "session_id": "string",
  "timestamp": "ISO-8601",
  "last_morning_routine": {
    "executed_at": "ISO-8601",
    "ready_to_code_score": "string",
    "breakdown": {},
    "session_restored": "boolean"
  },
  "last_nightly_routine": {
    "executed_at": "ISO-8601",
    "sleep_score": "string"
  },
  "git_status": {
    "current_branch": "string",
    "commits_behind_remote": "number",
    "uncommitted_files": "number",
    "stashes": "number",
    "action_required": "string"
  },
  "metrics": {
    "ready_to_code_score": "string"
  },
  "recommendations": {
    "before_coding": [],
    "todays_focus": []
  }
}
```

### How It's Used

1. **Nightly routine** writes current state (branch, work summary, sleep score)
2. **Morning routine** reads previous state to restore context
3. **Session capture** (`/popkit-core:project capture`) updates manually

---

## Custom Routine Files

When you create a custom routine with `/popkit-dev:routine generate`, it creates:

### Directory Structure

```
.claude/popkit/routines/
├── morning/
│   └── rc-1/
│       ├── routine.md      # Routine definition
│       ├── config.json     # Routine config
│       └── checks/         # Custom check scripts
└── nightly/
    └── rc-1/
        ├── routine.md
        ├── config.json
        └── scripts/
```

### routine.md Format

```markdown
---
id: rc-1
name: Full Stack Check
type: morning
project: Reseller Central
prefix: rc
based_on: pk
created: 2024-01-15T08:00:00Z
modified: 2024-01-15T08:00:00Z
---

# Morning Routine: Full Stack Check

Custom checks for full-stack projects.

## Checks

### Git Status

\`\`\`bash
git status --porcelain
git log --oneline -3
\`\`\`

### Database Health

\`\`\`bash
pg_isready -h localhost -p 5432
\`\`\`

## Score Calculation

| Check     | Points | Criteria               |
| --------- | ------ | ---------------------- |
| Git clean | 25     | No uncommitted changes |
| Database  | 25     | PostgreSQL responding  |
| Redis     | 25     | Redis responding       |
| Tests     | 25     | All tests pass         |
```

### config.json Format

```json
{
  "id": "rc-1",
  "name": "Full Stack Check",
  "description": "Includes database and Redis health",
  "based_on": "pk",
  "checks": [
    { "name": "git_clean", "weight": 25, "script": "checks/git.sh" },
    { "name": "database", "weight": 25, "script": "checks/database.sh" },
    { "name": "redis", "weight": 25, "script": "checks/redis.sh" },
    { "name": "tests", "weight": 25, "script": "checks/tests.sh" }
  ],
  "score_weights": {
    "git_clean": 25,
    "database": 25,
    "redis": 25,
    "tests": 25
  }
}
```

---

## Measurement Files

When running with `--measure`, performance data is stored.

### Location

```
.claude/popkit/measurements/<routine>-<timestamp>.json
```

### Schema

```json
{
  "routine": "morning",
  "timestamp": "ISO-8601",
  "duration_ms": "number",
  "tool_calls": "number",
  "tokens": {
    "input": "number",
    "output": "number"
  },
  "cost_estimate_usd": "number",
  "breakdown": {
    "git_check": { "duration_ms": "number", "tokens": "number" },
    "github_check": { "duration_ms": "number", "tokens": "number" }
  },
  "results": {
    "ready_to_code_score": "number",
    "services_running": "number",
    "commits_behind": "number"
  }
}
```

### Viewing Measurements

```bash
# View latest measurement
/popkit-core:stats routine

# View specific routine
/popkit-core:stats routine morning

# View all measurements
/popkit-core:stats routine --all
```

---

## Environment Variables

PopKit respects these environment variables:

| Variable           | Purpose                       | Default  |
| ------------------ | ----------------------------- | -------- |
| `POPKIT_DEBUG`     | Enable debug output           | `false`  |
| `POPKIT_NO_COLOR`  | Disable colored output        | `false`  |
| `POPKIT_CACHE_TTL` | Cache time-to-live in seconds | `300`    |
| `GITHUB_TOKEN`     | GitHub API authentication     | (gh CLI) |

---

## Initialization

To initialize PopKit configuration for a new project:

```bash
# Initialize with defaults
/popkit-core:project init

# Or manually create config
python -m popkit_shared.utils.routine_storage init
```

This creates the `.claude/popkit/` directory structure and detects your project name/prefix.

---

## Next Steps

- Learn about [Routines](/features/routines/)
- Explore [Commands Reference](/reference/commands/)
- Review [Skills Reference](/reference/skills/)
