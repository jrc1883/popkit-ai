---
name: pop-benchmark-runner
description: "Orchestrates benchmark execution comparing PopKit vs baseline Claude Code"
version: "1.0.0"
category: "operations"
context: "fork"
---

# Benchmark Runner Skill

## Overview

Automates quantitative measurement of PopKit's value by comparing AI-assisted development with PopKit enabled vs without PopKit (baseline Claude Code). Orchestrates trials in separate windows for side-by-side observation.

## Core Functions

1. **Orchestrated Execution** - Spawns trials in separate windows for visual monitoring
2. **Task Execution** - Runs benchmark tasks in isolated git worktrees
3. **Recording Collection** - Captures all tool calls, durations, and results
4. **Statistical Analysis** - Calculates t-tests, effect sizes, confidence intervals
5. **Report Generation** - Creates markdown and HTML reports with visualizations

## Usage

```bash
# Run benchmark with 3 trials
/popkit-ops:benchmark run jwt-authentication --trials 3

# Custom task
/popkit-ops:benchmark run custom-task --trials 5 --verbose
```

## Workflow

```
┌─────────────────────────────────────────────────────────┐
│ Current Claude Session (Orchestrator)                   │
│                                                          │
│  1. Load task definition and responses                  │
│  2. For each trial:                                     │
│     ├─ Spawn WITH PopKit window → New terminal         │
│     ├─ Spawn BASELINE window → New terminal            │
│     └─ Monitor via recording files (poll every 3s)     │
│  3. Collect all recordings when complete               │
│  4. Run statistical analysis                            │
│  5. Generate and open HTML report                       │
└─────────────────────────────────────────────────────────┘
         │                           │
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│ WITH PopKit      │        │ BASELINE         │
│ Terminal Window  │        │ Terminal Window  │
│                  │        │                  │
│ Claude Code      │        │ Claude Code      │
│ + PopKit enabled │        │ PopKit disabled  │
│                  │        │                  │
│ Recording: JSON  │        │ Recording: JSONL │
└──────────────────┘        └──────────────────┘
```

## User Experience Flow

```bash
# User runs in current Claude session
/popkit-ops:benchmark run jwt-authentication --trials 3

# Orchestrator takes over:
🚀 PopKit Benchmark Suite
▶ Trial 1/3 WITH PopKit - Launching window...
  [New terminal window opens → user sees Claude working with PopKit]
▶ Trial 1/3 BASELINE - Launching window...
  [New terminal window opens → user sees vanilla Claude working]
⏳ Monitoring trials... (watch the windows work)
✓ Trial 1 WITH PopKit completed (45s)
✓ Trial 1 BASELINE completed (68s)
...
📊 Analyzing results...
📈 Generating HTML report...
🎉 Opening report in browser...
```

## Metrics Collected

### Primary Metrics

1. **Context Usage** (tokens) - Via `routine_measurement.py`
2. **Tool Calls** - Via `recording_analyzer.py` tool usage breakdown
3. **Backtracking** (code reverts) - Via `transcript_parser.py` file edit detection
4. **Error Recovery** - Via `recording_analyzer.py` error summary
5. **Time to Complete** - Via `recording_analyzer.py` performance metrics
6. **Code Quality** - Via verification command exit codes

## Statistical Analysis

### T-Test (Statistical Significance)

```python
from scipy import stats

t_statistic, p_value = stats.ttest_ind(with_popkit_values, baseline_values)
is_significant = p_value < 0.05  # p < 0.05 means statistically significant
```

### Cohen's d (Effect Size)

```python
# Calculate effect size
effect_size = cohens_d(with_popkit_values, baseline_values)

# Interpret:
# d < 0.2: small effect
# d >= 0.5: medium effect
# d >= 0.8: large effect
```

### Confidence Intervals

95% confidence intervals calculated for all metrics to show variance range.

## Task Definition Format

Tasks are YAML files in `packages/popkit-ops/tasks/<category>/<task-id>.yml`:

```yaml
id: jwt-authentication
category: feature-addition
description: Add JWT-based user authentication to Express API
codebase: demo-app-express
initial_state: git checkout baseline-v1.0

user_prompt: |
  Implement JWT authentication with:
  - POST /auth/login endpoint (username/password)
  - JWT token generation with 1-hour expiry
  - Protected middleware for authenticated routes
  - Error handling for invalid credentials

verification:
  - npm test
  - npm run lint
  - npx tsc --noEmit

expected_outcomes:
  - "/auth/login endpoint exists"
  - "Tests pass for authentication flow"
  - "Protected routes return 401 without token"
```

## Benchmark Response Files

Response files enable automation without user interaction (`<task-id>-responses.json`):

```json
{
  "responses": {
    "Auth method": "JWT (jsonwebtoken library)",
    "Token storage": "HTTP-only cookies (security best practice)",
    "Token expiry": "1 hour (3600 seconds)",
    "Error handling": "Standard HTTP status codes (401, 403, 500)"
  },
  "standardAutoApprove": ["install.*dependencies", "run.*tests", "commit.*changes"]
}
```

## Environment Variables

```bash
POPKIT_RECORD=true                                 # Enable session recording
POPKIT_BENCHMARK_MODE=true                         # Enable benchmark automation
POPKIT_BENCHMARK_RESPONSES=<path-to-responses.json> # Response file
POPKIT_COMMAND=benchmark-<task-id>                 # Command name for recording
```

## Success Criteria

For a benchmark to be considered valid:

1. At least 3 successful trials per configuration (with/without PopKit)
2. All verification commands pass in with-PopKit configuration
3. Statistical significance (p < 0.05) for at least 4/6 metrics
4. Large effect size (Cohen's d > 0.8) for at least 3/6 metrics
5. Consistent results (standard deviation < 20% of mean)

## Related Files

- `benchmark_orchestrator.py` - Orchestrates parallel trials in separate windows
- `benchmark_runner.py` - Single trial execution (called by orchestrator)
- `benchmark_analyzer.py` - Statistical analysis
- `codebase_manager.py` - Git worktree management
- `report_generator.py` - Markdown/HTML reports
- `../../../shared-py/popkit_shared/utils/recording_analyzer.py` - Metrics extraction
- `../../../shared-py/popkit_shared/utils/routine_measurement.py` - Token tracking
- `../../../shared-py/popkit_shared/utils/benchmark_responses.py` - Automation

## Testing

```bash
# Unit tests
python -m pytest packages/popkit-ops/skills/pop-benchmark-runner/tests/ -v

# Integration test
/popkit-ops:benchmark run simple-feature --trials 1
```
