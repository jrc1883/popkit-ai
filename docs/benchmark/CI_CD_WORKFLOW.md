# PopKit Benchmark Suite - CI/CD Workflow Documentation

## Overview

The PopKit Benchmark Suite includes automated GitHub Actions workflow for continuous measurement of PopKit's value proposition. The workflow compares AI-assisted development **with PopKit enabled** vs **without PopKit** (baseline Claude Code) across 6 key metrics.

**Workflow File:** `.github/workflows/benchmark.yml`
**Issue:** #82 (Phase 3)
**Status:** ✅ Complete (infrastructure ready, execution simulation implemented)

---

## Metrics Tracked

| Metric               | Description                          | Source                                          |
| -------------------- | ------------------------------------ | ----------------------------------------------- |
| **Context Usage**    | Tokens consumed during task          | `routine_measurement.py` token estimation       |
| **Tool Calls**       | Number of Read/Write/Edit/Bash calls | `recording_analyzer.get_tool_usage_breakdown()` |
| **Backtracking**     | Code edited then reverted            | `transcript_parser` file edit detection         |
| **Error Recovery**   | Failed tool calls, retries needed    | `recording_analyzer.get_error_summary()`        |
| **Time to Complete** | Wall clock duration                  | `recording_analyzer.get_performance_metrics()`  |
| **Code Quality**     | Passes tests, lint, typecheck        | Verification command exit codes                 |

---

## Workflow Architecture

### Jobs

1. **setup** - Validate environment and configure benchmark parameters
2. **benchmark-matrix** - Execute benchmarks using matrix strategy (task × PopKit enabled/disabled)
3. **analyze** - Statistical analysis (t-tests, Cohen's d, 95% CIs)
4. **report** - Generate markdown and HTML reports
5. **deploy-pages** - Publish results to GitHub Pages
6. **notify** - Send summary and PR comments

### Matrix Strategy

The workflow uses GitHub Actions matrix strategy to run benchmarks efficiently:

```yaml
strategy:
  matrix:
    task_id: [jwt-authentication, dark-mode-implementation, ...]
    popkit_enabled: [true, false]
```

**Benefits:**

- Parallel execution (up to 16 tasks × 2 configurations = 32 concurrent jobs)
- Consistent environment across with/without PopKit runs
- Automatic retry on failure
- Clear separation of results

---

## Trigger Strategy

### Philosophy: Manual During Beta, Automated Post-v1.0

**Why this approach?**

- AI responses vary between runs (non-deterministic)
- Weekly automation without code changes measures AI variance, not PopKit improvements
- Benchmarks are only meaningful when something actually changed
- During beta development, manual control is more appropriate

**Post-v1.0 Plan:**

- Enable pre-release automation (validate before tagging)
- Monthly trend analysis (not weekly)
- Event-driven triggers (when PopKit code changes)

---

## Triggers

### 1. Manual Trigger (workflow_dispatch) - PRIMARY METHOD

**Use Case:** On-demand benchmarking when you need validation

**Inputs:**

- `task_ids` - Comma-separated task IDs or "all" (default: `jwt-authentication,dark-mode-implementation`)
- `trials` - Number of trials (3, 5, or 7) (default: 3)
- `report_format` - markdown, html, or both (default: both)
- `reason` - Why you're running this benchmark (for documentation) (default: "Manual validation")

**How to Trigger:**

1. Go to Actions tab in GitHub
2. Select "Benchmark Suite" workflow
3. Click "Run workflow"
4. Configure inputs (including reason)
5. Click "Run workflow"

**Example:**

```yaml
task_ids: jwt-authentication,race-condition-fix
trials: 5
report_format: both
reason: Testing new agent optimization feature
```

**When to use:**

- After implementing major PopKit improvements
- Before creating a release
- When validating specific optimizations
- When you need concrete performance data

### 2. PR Trigger (pull_request + label) - OPTIONAL VALIDATION

**Use Case:** Validate benchmark-related changes in pull requests

**Trigger:** Add `benchmark` label to PR

**Configuration:**

- Quick run (2 sample tasks: jwt-authentication, race-condition-fix)
- 3 trials per task per configuration
- Markdown report only
- Results posted as PR comment

**Total Runtime:** ~20-30 minutes (when fully implemented)

**When to use:**

- PRs that modify benchmark infrastructure
- PRs that change core PopKit workflow code
- When you want to verify no performance regressions

### 3. Pre-Release Trigger (release) - FUTURE (Post-v1.0)

**Status:** Commented out, ready to enable

**Use Case:** Automatically benchmark before each release

**Configuration:**

```yaml
# release:
#   types: [published]
```

**Activation Plan:**

- Enable after v1.0.0 release
- Run full benchmark suite (all 8 tasks, 5 trials)
- Publish results to GitHub Pages
- Block release if major regressions detected

---

## Workflow Stages

### Stage 1: Setup & Validation

**Job:** `setup`
**Purpose:** Validate environment and configure parameters
**Duration:** ~30 seconds

**Steps:**

1. Checkout repository
2. Setup Python 3.11 with pip cache
3. Install dependencies (shared-py, PyYAML)
4. Configure benchmark parameters (based on trigger type)
5. Validate task YAML syntax
6. Check Claude Code availability

**Outputs:**

- `task_ids` - Tasks to benchmark
- `trials` - Number of trials per task
- `report_format` - Report format (markdown/html/both)
- `should_run` - Whether to proceed with benchmark

### Stage 2: Benchmark Execution

**Job:** `benchmark-matrix`
**Purpose:** Execute benchmarks with matrix strategy
**Duration:** ~5-15 minutes per task (simulated: ~1 minute)

**Matrix Dimensions:**

- 8 tasks × 2 configurations (with/without PopKit) = 16 concurrent jobs
- Each job runs N trials (3-5)

**Steps:**

1. Checkout repository
2. Setup Python 3.11 and Node.js 20
3. Install dependencies (numpy, scipy, matplotlib)
4. Conditionally install PopKit plugins (if `popkit_enabled: true`)
5. Prepare benchmark environment (worktree, env vars)
6. Execute benchmark trials (SIMULATED in Phase 3)
7. Collect metrics (RecordingAnalyzer integration pending)
8. Upload results as artifacts (retention: 90 days)

**Artifacts:**

- `benchmark-results-<task-id>-popkit-<true|false>`
- Contains: recordings, metrics, logs

### Stage 3: Analysis & Statistics

**Job:** `analyze`
**Purpose:** Statistical analysis across all tasks
**Duration:** ~2-5 minutes

**Steps:**

1. Download all benchmark result artifacts
2. Run statistical analysis:
   - Independent samples t-tests (p-values)
   - Cohen's d effect sizes
   - 95% confidence intervals
   - Cross-task aggregation
3. Upload analysis artifacts (retention: 90 days)

**Outputs:**

- Statistical significance (p < 0.05)
- Effect sizes (small/medium/large)
- Confidence intervals for improvements

### Stage 4: Report Generation

**Job:** `report`
**Purpose:** Generate human-readable reports
**Duration:** ~1-2 minutes

**Reports Generated:**

1. **Markdown Report** (`docs/benchmark/results/<run-id>.md`):
   - Summary tables
   - Per-task breakdowns
   - Statistical significance indicators

2. **HTML Dashboard** (`docs/benchmark/results/<run-id>.html`):
   - Interactive visualizations (Chart.js)
   - Trend charts (historical data)
   - Filterable task views

**Artifacts:**

- `benchmark-reports` (retention: 365 days)
- Uploaded to GitHub Pages (permanent)

### Stage 5: GitHub Pages Deployment

**Job:** `deploy-pages`
**Purpose:** Publish results to public URL
**Duration:** ~1 minute
**Condition:** Only for scheduled and manual runs

**Process:**

1. Prepare gh-pages directory
2. Upload Pages artifact
3. Deploy to GitHub Pages environment
4. Output public URL

**Result:**

- Public dashboard at `https://<username>.github.io/popkit-claude/benchmark/`
- Persistent historical data

### Stage 6: Notification & Summary

**Job:** `notify`
**Purpose:** Send results summary
**Duration:** ~30 seconds

**Actions:**

1. **Workflow Summary** (all runs):
   - Configuration details
   - Job status table
   - Links to artifacts
   - Phase 3 completion note

2. **PR Comment** (PR-triggered only):
   - Benchmark results summary
   - Status of each job
   - Link to detailed workflow run
   - Note about simulation status

---

## Environment Requirements

### Required Secrets

None required for Phase 3 (simulated execution).

**Phase 4 Requirements:**

- `CLAUDE_API_KEY` - For Claude Code execution (if using API mode)
- `ANTHROPIC_API_KEY` - Alternative name (if using Anthropic SDK)

### Required Permissions

```yaml
permissions:
  contents: read # Read repository
  pages: write # Deploy to GitHub Pages
  id-token: write # GitHub Pages authentication
  pull-requests: write # Comment on PRs (implicit via github-script)
```

### Concurrency Control

```yaml
concurrency:
  group: benchmark-${{ github.ref }}
  cancel-in-progress: true
```

**Behavior:** Only one benchmark run per branch at a time. New runs cancel in-progress runs.

---

## Artifacts & Retention

| Artifact              | Retention | Purpose                                   |
| --------------------- | --------- | ----------------------------------------- |
| `benchmark-results-*` | 90 days   | Raw benchmark data (per task, per config) |
| `benchmark-analysis`  | 90 days   | Statistical analysis results              |
| `benchmark-reports`   | 365 days  | Generated markdown/HTML reports           |
| GitHub Pages          | Permanent | Public dashboard with historical data     |

---

## Current Implementation Status (Phase 3)

### ✅ Complete

1. **Workflow Structure**
   - 6 jobs with proper dependencies
   - Matrix strategy for parallel execution
   - 3 trigger types (manual, schedule, PR)

2. **Environment Setup**
   - Python 3.11 with pip cache
   - Node.js 20 with npm cache
   - Dependency installation (shared-py, analysis libs)

3. **Configuration**
   - Input validation
   - Dynamic task selection
   - Trial count selection
   - Report format selection

4. **Artifact Management**
   - Upload results per task
   - Download and aggregate for analysis
   - Retention policies (90/365 days)

5. **GitHub Pages Deployment**
   - Automated deployment
   - Public URL generation
   - Historical data persistence

6. **Notifications**
   - Workflow summary (all runs)
   - PR comments (PR-triggered runs)
   - Status badges (future enhancement)

### ⏳ Pending (Phase 4)

1. **Actual Execution**
   - Claude Code CLI integration
   - Real benchmark trials
   - Recording capture
   - Metric extraction

2. **Statistical Analysis**
   - BenchmarkAnalyzer integration
   - T-test calculation
   - Cohen's d computation
   - Confidence interval generation

3. **Report Generation**
   - ReportGenerator integration
   - Chart.js visualizations
   - Trend analysis
   - Historical comparisons

4. **Testing**
   - Unit tests for workflow scripts
   - Integration tests with mock data
   - End-to-end workflow validation

---

## Usage Examples

### Example 1: Quick Validation (2 tasks)

**Trigger:** Manual workflow dispatch

**Use Case:** Testing a specific optimization or bug fix

**Configuration:**

```yaml
task_ids: jwt-authentication,race-condition-fix
trials: 3
report_format: markdown
reason: Testing new agent routing optimization
```

**Expected Runtime:** ~10-15 minutes (when fully implemented)

**Output:**

- Markdown report in workflow summary
- Artifacts available for download (90 days)

### Example 2: Full Benchmark Suite (8 tasks)

**Trigger:** Manual workflow dispatch

**Use Case:** Pre-release validation or major feature testing

**Configuration:**

```yaml
task_ids: all
trials: 5
report_format: both
reason: Pre-release validation for v1.0.0
```

**Expected Runtime:** ~2-4 hours (when fully implemented)

**Output:**

- HTML dashboard on GitHub Pages
- Markdown report in artifacts
- Workflow summary
- Comprehensive statistical analysis

### Example 3: PR Validation

**Trigger:** Add `benchmark` label to PR

**Use Case:** Validate benchmark infrastructure changes or core workflow updates

**Configuration:**

```yaml
task_ids: jwt-authentication,race-condition-fix
trials: 3
report_format: markdown
reason: PR validation (label: benchmark)
```

**Expected Runtime:** ~20-30 minutes (when fully implemented)

**Output:**

- PR comment with results summary
- Markdown report in artifacts
- Pass/fail status for PR checks

---

## Monitoring & Debugging

### Workflow Logs

All jobs produce structured logs:

- Setup: Configuration details, validation results
- Benchmark: Execution status, trial progress
- Analysis: Statistical results, significance tests
- Report: Generated report summaries
- Notify: Summary and notification status

### Artifact Inspection

Download artifacts for debugging:

```bash
gh run download <run-id> --name benchmark-results-jwt-authentication-popkit-true
```

### Failed Jobs

Common failure scenarios and resolutions:

1. **Setup Validation Failed**
   - Cause: Invalid YAML syntax in task definition
   - Fix: Run local validation with `python -c "import yaml; yaml.safe_load(open('task.yml'))"`

2. **Benchmark Execution Failed**
   - Cause: Claude Code not available, environment issues
   - Fix: Check Claude Code installation, verify dependencies

3. **Analysis Failed**
   - Cause: Missing or corrupted results artifacts
   - Fix: Re-run benchmark, check artifact upload logs

4. **Report Generation Failed**
   - Cause: Invalid analysis data, template errors
   - Fix: Check analysis output, validate template syntax

5. **GitHub Pages Deployment Failed**
   - Cause: Permissions issue, invalid artifact
   - Fix: Check repository settings (Pages enabled), verify artifact contents

---

## Future Enhancements (Post-Phase 4)

1. **Performance Optimizations**
   - Caching of benchmark environments
   - Incremental benchmarking (only changed tasks)
   - Parallel trial execution within jobs

2. **Advanced Reporting**
   - Slack/Discord notifications
   - Email summaries
   - Status badges for README

3. **Trend Analysis**
   - Historical performance tracking
   - Regression detection
   - Automatic alerts on degradation

4. **Custom Task Templates**
   - Gallery of community-contributed tasks
   - Task validation and scoring
   - Task discovery and recommendation

5. **Cloud Integration**
   - PopKit Cloud synchronization
   - Multi-repository benchmarking
   - Cross-project comparisons

---

## Related Documentation

- **Task Definition Schema**: `packages/popkit-ops/tasks/TASK_DEFINITION_SCHEMA.md`
- **Benchmark Command**: `packages/popkit-ops/commands/benchmark.md`
- **Benchmark Runner Skill**: `packages/popkit-ops/skills/pop-benchmark-runner/SKILL.md`
- **Implementation Status**: `packages/popkit-ops/skills/pop-benchmark-runner/IMPLEMENTATION_STATUS.md`

---

## Support

For issues, questions, or contributions:

- **GitHub Issues**: https://github.com/jrc1883/popkit-claude/issues
- **Issue #82**: PopKit Benchmark Suite tracking issue
- **Discussions**: GitHub Discussions (future)

---

**Phase 3 Status:** ✅ Complete - CI/CD infrastructure ready
**Next Phase:** Phase 4 - Testing & validation (unit tests, full suite execution, end-to-end integration)
