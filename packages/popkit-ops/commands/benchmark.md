---
description: "run | analyze | report - Benchmark PopKit value vs baseline"
argument-hint: "<subcommand> [task-id] [options]"
---

# /popkit-ops:benchmark

Quantitatively measure PopKit's value by comparing AI-assisted development with PopKit enabled vs without PopKit (baseline Claude Code).

## Usage

```bash
/popkit-ops:benchmark run <task-id> --trials 5    # Run benchmark for specific task
/popkit-ops:benchmark run all --trials 3          # Run all benchmark tasks
/popkit-ops:benchmark analyze                     # Analyze recent benchmark results
/popkit-ops:benchmark report                      # Generate comprehensive report
```

## Subcommands

### run

Execute benchmark trials comparing with/without PopKit.

**Arguments:**

- `<task-id>` - Task to benchmark (e.g., `jwt-authentication`) or `all` for full suite
- `--trials N` - Number of trials per task (default: 3, recommended: 5 for statistical significance)
- `--no-cleanup` - Keep worktrees after completion (for debugging)

**Example:**

```bash
/popkit-ops:benchmark run jwt-authentication --trials 5
```

### analyze

Analyze recordings from recent benchmark runs and calculate statistics.

**Options:**

- `--task <task-id>` - Analyze specific task (default: all recent)
- `--show-details` - Show detailed metric breakdown

**Example:**

```bash
/popkit-ops:benchmark analyze --task jwt-authentication --show-details
```

### report

Generate comprehensive benchmark report with visualizations.

**Options:**

- `--format markdown|html|both` - Report format (default: both)
- `--output <path>` - Output directory (default: `docs/benchmark/results/`)

**Example:**

```bash
/popkit-ops:benchmark report --format both
```

## Instructions

This command invokes the `pop-benchmark-runner` skill to execute the benchmark workflow using the **orchestrator pattern** for side-by-side trial viewing.

### When user runs `/popkit-ops:benchmark run <task-id> --trials N`:

1. **Invoke the pop-benchmark-runner skill:**

   ```
   Use Skill tool: skill="popkit-ops:pop-benchmark-runner", args="run <task-id> --trials N"
   ```

2. **The skill will orchestrate trials in separate windows:**
   - Load task definition from `packages/popkit-ops/tasks/<category>/<task-id>.yml`
   - Load response file from `packages/popkit-ops/tasks/<category>/<task-id>/responses.json`
   - For each trial (1 to N):
     - Create fresh git worktrees for isolated test environments
     - Spawn new Claude Code window for WITH PopKit trial
     - Spawn new Claude Code window for BASELINE trial
     - Monitor both trials via recording files
     - Show progress in orchestrator window
   - Collect all recordings when trials complete
   - Run statistical analysis (t-tests, Cohen's d effect size)
   - Generate HTML report and open in browser

3. **User Experience:**
   - Run one command in current Claude session
   - See separate terminal windows open automatically (2 per trial)
   - Watch WITH PopKit and BASELINE trials work side-by-side
   - Orchestrator window shows real-time progress
   - HTML report opens automatically when complete

4. **Display summary:**
   - Show metric improvements (context usage, tool calls, backtracking, errors, time, code quality)
   - Show statistical significance (p-values, effect sizes)
   - Link to full report in `docs/benchmark/results/`

### When user runs `/popkit-ops:benchmark analyze`:

1. **Invoke the pop-benchmark-runner skill:**

   ```
   Use Skill tool: skill="popkit-ops:pop-benchmark-runner", args="analyze"
   ```

2. **The skill will:**
   - Find recent benchmark recordings
   - Extract metrics using `RecordingAnalyzer`
   - Calculate statistics across trials
   - Display comparison tables

### When user runs `/popkit-ops:benchmark report`:

1. **Invoke the pop-benchmark-runner skill:**

   ```
   Use Skill tool: skill="popkit-ops:pop-benchmark-runner", args="report --format both"
   ```

2. **The skill will:**
   - Generate markdown report with tables and charts
   - Generate HTML dashboard with interactive visualizations
   - Save to `docs/benchmark/results/`
   - Display summary and link to reports

## Metrics Collected

The benchmark suite measures 6 key metrics:

| Metric               | Description                             | Source                                          |
| -------------------- | --------------------------------------- | ----------------------------------------------- |
| **Context Usage**    | Tokens consumed during task             | `routine_measurement.py` token estimation       |
| **Tool Calls**       | Number of Read, Write, Edit, Bash calls | `recording_analyzer.get_tool_usage_breakdown()` |
| **Backtracking**     | Code edited then reverted               | `transcript_parser` file edit detection         |
| **Error Recovery**   | Failed tool calls, retries needed       | `recording_analyzer.get_error_summary()`        |
| **Time to Complete** | Wall clock duration                     | `recording_analyzer.get_performance_metrics()`  |
| **Code Quality**     | Passes tests, lint, typecheck           | Verification command exit codes                 |

## Task Categories

Benchmark tasks are organized into 4 categories:

1. **Feature Addition** - Add new functionality (e.g., JWT auth, dark mode)
2. **Bug Fixing** - Fix existing issues (e.g., race condition, CI failures)
3. **Refactoring** - Improve code structure (e.g., async/await, extract utilities)
4. **Code Review** - Identify issues (e.g., security review, performance bottlenecks)

## Statistical Analysis

Each benchmark run includes:

- **T-tests**: Determine if differences are statistically significant (p < 0.05)
- **Cohen's d**: Effect size measurement (> 0.5 = medium, > 0.8 = large effect)
- **Confidence Intervals**: 95% CI for mean improvements
- **Multiple Trials**: 3-5 trials per task for statistical rigor

## Example Output

```
## Benchmark Results: jwt-authentication

**Task**: Add JWT-based user authentication
**Trials**: 5 per configuration
**Duration**: 45 minutes

### Metric Improvements (With PopKit vs Baseline)

| Metric | Baseline | With PopKit | Improvement | p-value | Effect Size |
|--------|----------|-------------|-------------|---------|-------------|
| Context Usage | 12,450 tokens | 8,720 tokens | -30.0% | 0.003 | 1.2 (large) |
| Tool Calls | 48 calls | 32 calls | -33.3% | 0.001 | 1.5 (large) |
| Backtracking | 8 reverts | 2 reverts | -75.0% | 0.002 | 1.8 (large) |
| Error Recovery | 5 errors | 1 error | -80.0% | 0.004 | 1.3 (large) |
| Time to Complete | 8.2 min | 5.4 min | -34.1% | 0.001 | 1.4 (large) |
| Code Quality | 85% pass | 100% pass | +15.0% | 0.010 | 0.9 (large) |

**Statistical Significance**: All metrics show statistically significant improvements (p < 0.05)
**Overall Effect Size**: 1.35 (large effect)

Full report: docs/benchmark/results/jwt-authentication-2025-01-15.html
```

## Related Commands

- `/popkit-core:record start|stop|status` - Manual session recording
- `/popkit-ops:assess all` - Code quality assessments
- `/popkit-ops:audit health` - Overall project health check
- `/popkit-dev:worktree create|list` - Manual worktree management

## Notes

- Benchmark runs can take 30-60 minutes depending on task complexity
- **Orchestrator Pattern**: Current session becomes orchestrator, spawns trials in new windows
- **User watches trials**: See WITH PopKit and BASELINE work side-by-side in separate terminal windows
- **Automatic monitoring**: Orchestrator tracks progress by polling recording files every 3 seconds
- **Recordings**: WITH PopKit trials → `.claude/popkit/recordings/` (JSON), BASELINE trials → `.claude/projects/` (JSONL)
- **Git worktrees**: Created in `benchmark-worktrees/` and cleaned up after completion
- Use `--no-cleanup` flag to keep worktrees for debugging
- **Cross-platform**: Window spawning works on Windows (cmd), Mac (Terminal), Linux (gnome-terminal)

## Success Criteria

For a benchmark to be valid:

- ✅ All trials complete successfully
- ✅ All verification commands pass (tests, lint, typecheck)
- ✅ Statistical significance (p < 0.05) for at least 4/6 metrics
- ✅ Large effect size (Cohen's d > 0.8) for at least 3/6 metrics
- ✅ Consistent results across trials (low standard deviation)
