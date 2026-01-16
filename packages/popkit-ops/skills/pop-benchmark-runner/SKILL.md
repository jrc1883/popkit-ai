---
name: pop-benchmark-runner
description: "Orchestrates benchmark execution comparing PopKit vs baseline Claude Code"
version: "1.0.0"
category: "operations"
context: "fork"
---

# Benchmark Runner Skill

## Overview

Automates the execution of benchmark tasks that quantitatively measure PopKit's value by comparing AI-assisted development with PopKit enabled vs without PopKit (baseline Claude Code).

## Core Functions

1. **Task Execution** - Runs benchmark tasks in isolated git worktrees
2. **Recording Collection** - Captures all tool calls, durations, and results
3. **Statistical Analysis** - Calculates t-tests, effect sizes, confidence intervals
4. **Report Generation** - Creates markdown and HTML reports with visualizations

## Workflow

### Phase 1: Setup

```python
from popkit_shared.utils.benchmark_responses import is_benchmark_mode, load_responses_file
from pathlib import Path
import yaml

# Load task definition
task_file = Path(f"packages/popkit-ops/tasks/{category}/{task_id}.yml")
task_def = yaml.safe_load(task_file.read_text())

# Setup benchmark responses for automation
os.environ["POPKIT_BENCHMARK_MODE"] = "true"
os.environ["POPKIT_BENCHMARK_RESPONSES"] = f"packages/popkit-ops/tasks/{category}/{task_id}-responses.json"
```

### Phase 2: Worktree Creation

```python
from pop_benchmark_runner.scripts.codebase_manager import CodebaseManager

manager = CodebaseManager()

# Create isolated worktree for each trial
for trial in range(1, trials + 1):
    worktree_path = manager.create_worktree(
        task_id=task_id,
        trial_num=trial,
        baseline_ref=task_def["initial_state"]
    )
    # Returns: benchmark-worktrees/<task-id>-<trial>-<timestamp>/
```

### Phase 3: Benchmark Execution

```python
from pop_benchmark_runner.scripts.benchmark_runner import BenchmarkRunner

runner = BenchmarkRunner(task_def, trials=5)

# Run with PopKit (recording enabled)
with_popkit_recordings = runner.run_with_popkit()

# Run without PopKit (baseline, recording enabled)
without_popkit_recordings = runner.run_baseline()

# Returns: List[Path] - paths to recording JSON files
```

### Phase 4: Analysis

```python
from pop_benchmark_runner.scripts.benchmark_analyzer import BenchmarkAnalyzer

analyzer = BenchmarkAnalyzer(
    with_popkit_recordings=with_popkit_recordings,
    baseline_recordings=without_popkit_recordings
)

results = analyzer.analyze()
# Returns: {
#   "metrics": { metric_name: { "with_popkit": ..., "baseline": ..., "improvement": ..., "p_value": ..., "effect_size": ... } },
#   "summary": { "significant_metrics": ..., "overall_effect_size": ... }
# }
```

### Phase 5: Reporting

```python
from pop_benchmark_runner.scripts.report_generator import ReportGenerator

generator = ReportGenerator(results, task_def)

# Generate markdown report
md_report = generator.generate_markdown()

# Generate HTML dashboard
html_report = generator.generate_html()

# Save reports
output_dir = Path("docs/benchmark/results")
output_dir.mkdir(parents=True, exist_ok=True)
(output_dir / f"{task_id}-{timestamp}.md").write_text(md_report)
(output_dir / f"{task_id}-{timestamp}.html").write_text(html_report)
```

## Metrics Collected

### 1. Context Usage (Tokens)

**Source**: `routine_measurement.py` token estimation

```python
from popkit_shared.utils.routine_measurement import RoutineMeasurement

measurement = RoutineMeasurement.from_recording(recording_path)
context_usage = measurement.total_tokens
```

### 2. Tool Calls

**Source**: `recording_analyzer.py` tool usage breakdown

```python
from popkit_shared.utils.recording_analyzer import RecordingAnalyzer

analyzer = RecordingAnalyzer(recording_path)
tool_usage = analyzer.get_tool_usage_breakdown()
total_tool_calls = sum(tool["count"] for tool in tool_usage.values())
```

### 3. Backtracking (Code Reverts)

**Source**: `transcript_parser.py` file edit detection

```python
from popkit_shared.utils.transcript_parser import parse_transcript

transcript = parse_transcript(recording_path)
file_edits = {}
for event in transcript:
    if event["type"] in ["Write", "Edit"]:
        file_path = event["parameters"].get("file_path")
        if file_path not in file_edits:
            file_edits[file_path] = []
        file_edits[file_path].append(event)

# Count files edited multiple times (backtracking)
backtracking_count = sum(1 for edits in file_edits.values() if len(edits) > 1)
```

### 4. Error Recovery

**Source**: `recording_analyzer.py` error summary

```python
analyzer = RecordingAnalyzer(recording_path)
error_summary = analyzer.get_error_summary()
error_count = error_summary["total_errors"]
error_rate = error_summary["error_rate"]
```

### 5. Time to Complete

**Source**: `recording_analyzer.py` performance metrics

```python
analyzer = RecordingAnalyzer(recording_path)
performance = analyzer.get_performance_metrics()
duration_ms = performance["total_duration_ms"]
```

### 6. Code Quality

**Source**: Verification command exit codes

```python
verification_commands = task_def["verification"]
# E.g., ["npm test", "npm run lint", "npx tsc --noEmit"]

quality_results = []
for cmd in verification_commands:
    result = subprocess.run(cmd.split(), capture_output=True)
    quality_results.append(result.returncode == 0)

pass_rate = sum(quality_results) / len(quality_results)
```

## Statistical Analysis

### T-Test (Statistical Significance)

```python
from scipy import stats
import numpy as np

# Extract metric values from each trial
with_popkit_values = [trial["context_usage"] for trial in with_popkit_trials]
baseline_values = [trial["context_usage"] for trial in baseline_trials]

# Perform independent samples t-test
t_statistic, p_value = stats.ttest_ind(with_popkit_values, baseline_values)

# Interpret: p < 0.05 means statistically significant difference
is_significant = p_value < 0.05
```

### Cohen's d (Effect Size)

```python
def cohens_d(group1, group2):
    """Calculate Cohen's d effect size."""
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)

    # Pooled standard deviation
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

    # Effect size
    d = (mean1 - mean2) / pooled_std
    return abs(d)

effect_size = cohens_d(with_popkit_values, baseline_values)

# Interpret:
# d < 0.2: small effect
# d >= 0.5: medium effect
# d >= 0.8: large effect
```

### Confidence Intervals

```python
def confidence_interval(data, confidence=0.95):
    """Calculate confidence interval for mean."""
    mean = np.mean(data)
    sem = stats.sem(data)  # Standard error of mean
    ci = sem * stats.t.ppf((1 + confidence) / 2, len(data) - 1)
    return (mean - ci, mean + ci)

with_popkit_ci = confidence_interval(with_popkit_values)
baseline_ci = confidence_interval(baseline_values)
```

## Task Definition Format

Task definitions are YAML files in `packages/popkit-ops/tasks/<category>/<task-id>.yml`:

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
  "standardAutoApprove": [
    "install.*dependencies",
    "run.*tests",
    "commit.*changes"
  ]
}
```

## Environment Variables

```bash
POPKIT_RECORD=true                                 # Enable session recording
POPKIT_BENCHMARK_MODE=true                         # Enable benchmark automation
POPKIT_BENCHMARK_RESPONSES=<path-to-responses.json> # Response file
POPKIT_COMMAND=benchmark-<task-id>                 # Command name for recording
```

## Output Structure

```
docs/benchmark/results/
├── jwt-authentication-2025-01-15.md     # Markdown report
├── jwt-authentication-2025-01-15.html   # HTML dashboard
├── jwt-authentication-2025-01-15.json   # Raw data
└── index.html                           # Dashboard landing page
```

## Error Handling

### Worktree Creation Failures

```python
try:
    worktree_path = manager.create_worktree(task_id, trial, baseline_ref)
except WorktreeExistsError:
    # Cleanup and retry
    manager.cleanup_worktree(task_id, trial)
    worktree_path = manager.create_worktree(task_id, trial, baseline_ref)
except GitError as e:
    print(f"[ERROR] Git operation failed: {e}")
    # Skip this trial, continue with others
```

### Verification Command Failures

```python
for cmd in verification_commands:
    result = subprocess.run(cmd.split(), capture_output=True, timeout=300)
    if result.returncode != 0:
        print(f"[WARN] Verification command failed: {cmd}")
        print(f"  stdout: {result.stdout.decode()}")
        print(f"  stderr: {result.stderr.decode()}")
        # Record failure but continue analysis
```

### Recording Collection Failures

```python
recordings = []
for recording_file in expected_recordings:
    if not recording_file.exists():
        print(f"[WARN] Recording not found: {recording_file}")
        continue
    try:
        recordings.append(RecordingAnalyzer(recording_file))
    except Exception as e:
        print(f"[ERROR] Failed to load recording {recording_file}: {e}")

if len(recordings) < trials * 0.5:  # Less than 50% success
    raise InsufficientDataError("Too many recording failures for valid analysis")
```

## Success Criteria

For a benchmark to be considered valid:

1. ✅ At least 3 successful trials per configuration (with/without PopKit)
2. ✅ All verification commands pass in with-PopKit configuration
3. ✅ Statistical significance (p < 0.05) for at least 4/6 metrics
4. ✅ Large effect size (Cohen's d > 0.8) for at least 3/6 metrics
5. ✅ Consistent results (standard deviation < 20% of mean)

## Related Files

- `benchmark_runner.py` - Orchestrates execution
- `benchmark_analyzer.py` - Statistical analysis
- `codebase_manager.py` - Git worktree management
- `report_generator.py` - Markdown/HTML reports
- `../../../shared-py/popkit_shared/utils/recording_analyzer.py` - Metrics extraction
- `../../../shared-py/popkit_shared/utils/routine_measurement.py` - Token tracking
- `../../../shared-py/popkit_shared/utils/benchmark_responses.py` - Automation

## Testing

Unit tests verify each component:

```bash
python -m pytest packages/popkit-ops/skills/pop-benchmark-runner/tests/ -v
```

Integration test runs a simple benchmark:

```bash
/popkit-ops:benchmark run simple-feature --trials 1
```
