# PopKit Benchmark Suite

**Version:** 1.0.0
**Status:** Phase 1 Complete (Core Infrastructure)
**Issue:** #82

## Overview

Quantitatively measures PopKit's value by comparing AI-assisted development with PopKit enabled vs without PopKit (baseline Claude Code).

## Features

### Metrics Collected

1. **Context Usage** - Tokens consumed during task
2. **Tool Calls** - Number of Read, Write, Edit, Bash calls
3. **Backtracking** - Code edited then reverted
4. **Error Recovery** - Failed tool calls, retries needed
5. **Time to Complete** - Wall clock duration
6. **Code Quality** - Passes tests, lint, typecheck

### Statistical Analysis

- **T-tests**: Determine statistical significance (p < 0.05)
- **Cohen's d**: Effect size measurement (> 0.8 = large effect)
- **95% Confidence Intervals**: Mean improvements with certainty bounds
- **Multiple Trials**: 3-5 trials per task for rigor

## Components

### 1. Commands

- `/popkit-ops:benchmark run <task-id> --trials N` - Execute benchmark
- `/popkit-ops:benchmark analyze` - Analyze results
- `/popkit-ops:benchmark report` - Generate reports

### 2. Core Modules

| Module                  | Purpose                 | Lines | Status      |
| ----------------------- | ----------------------- | ----- | ----------- |
| `codebase_manager.py`   | Git worktree management | 300   | ✅ Complete |
| `benchmark_runner.py`   | Execution orchestration | 618   | ✅ Complete |
| `benchmark_analyzer.py` | Statistical analysis    | 535   | ✅ Complete |
| `report_generator.py`   | Markdown/HTML reports   | 350   | ✅ Complete |

### 3. Task Definitions

Tasks are defined in YAML format in `packages/popkit-ops/tasks/<category>/`:

- `feature-addition/jwt-authentication.yml` - Add JWT auth to Express API
- `bug-fixing/race-condition-fix.yml` - Fix concurrent file processing

**Format:**

```yaml
id: task-id
category: feature-addition | bug-fixing | refactoring | code-review
description: Human-readable description
user_prompt: |
  Detailed task instructions...
verification:
  - npm test
  - npm run lint
expected_outcomes:
  - "Feature X exists"
```

## Usage

### Basic Execution

```bash
# Run single task with 5 trials
/popkit-ops:benchmark run jwt-authentication --trials 5

# Run all tasks with 3 trials
/popkit-ops:benchmark run all --trials 3

# Analyze recent results
/popkit-ops:benchmark analyze

# Generate comprehensive report
/popkit-ops:benchmark report
```

### CLI Testing

```bash
# Test codebase manager
python scripts/codebase_manager.py create jwt-auth 1 HEAD
python scripts/codebase_manager.py list
python scripts/codebase_manager.py cleanup-all

# Test benchmark runner (mock mode)
python scripts/benchmark_runner.py tasks/feature-addition/jwt-authentication.yml --trials 3 --config all --verbose

# Test analyzer (sample data)
python scripts/benchmark_analyzer.py

# Test report generator (sample data)
python scripts/report_generator.py
```

## Architecture

### Execution Flow

```
1. User runs: /popkit-ops:benchmark run jwt-authentication --trials 5
   ↓
2. benchmark_runner.py loads task definition
   ↓
3. For each trial (1-5):
   a. Create fresh git worktree (codebase_manager.py)
   b. Run WITH PopKit (recording enabled)
   c. Run WITHOUT PopKit (baseline, recording enabled)
   d. Collect recordings from ~/.claude/popkit/recordings/
   ↓
4. benchmark_analyzer.py processes all recordings
   ├─ Extract metrics using RecordingAnalyzer
   ├─ Calculate t-tests for significance
   ├─ Calculate Cohen's d for effect size
   └─ Generate 95% confidence intervals
   ↓
5. report_generator.py creates markdown + HTML reports
   ↓
6. Display summary and save to docs/benchmark/results/
```

### Environment Variables

```bash
POPKIT_RECORD=true                          # Enable session recording
POPKIT_BENCHMARK_MODE=true                  # Enable benchmark automation
POPKIT_BENCHMARK_RESPONSES=responses.json   # Response file for automation
CLAUDE_DISABLE_PLUGINS=popkit-*             # Disable PopKit for baseline
TEST_MODE=true                              # Mock execution for testing
```

## Integration with Existing Infrastructure

### Leverages Shared Utilities

- `packages/shared-py/popkit_shared/utils/recording_analyzer.py` - Metrics extraction
- `packages/shared-py/popkit_shared/utils/routine_measurement.py` - Token tracking
- `packages/shared-py/popkit_shared/utils/benchmark_responses.py` - Automation
- `packages/shared-py/popkit_shared/utils/transcript_parser.py` - Backtracking detection

### Recording Format

Uses existing session recording infrastructure:

- Command: `/popkit-core:record start|stop|status`
- Storage: `~/.claude/popkit/recordings/*.json`
- Format: JSONL events with tool calls, durations, errors

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

**Statistical Significance**: All metrics show improvements (p < 0.05)
**Overall Effect Size**: 1.35 (large effect)
```

## Next Steps (Phase 2-4)

### Phase 2: Task Definitions (Days 6-8)

- [ ] Define 6 more task YAML files (total 8: 2 per category)
- [ ] Create benchmark response files for each task
- [ ] Test task definitions with manual execution

### Phase 3: CI/CD Automation (Days 9-11)

- [ ] Create `.github/workflows/benchmark.yml`
- [ ] Setup two Claude Code instances (with/without PopKit)
- [ ] Configure weekly automated runs
- [ ] Upload results as GitHub artifacts

### Phase 4: Testing & Validation (Days 12-13)

- [ ] Create unit tests for all 4 core modules
- [ ] Run full benchmark suite (8 tasks × 5 trials)
- [ ] Verify statistical significance
- [ ] Document results in `docs/benchmark/`

## Testing

### Unit Tests (To be implemented)

```bash
# Test individual components
pytest packages/popkit-ops/skills/pop-benchmark-runner/tests/test_codebase_manager.py -v
pytest packages/popkit-ops/skills/pop-benchmark-runner/tests/test_benchmark_runner.py -v
pytest packages/popkit-ops/skills/pop-benchmark-runner/tests/test_benchmark_analyzer.py -v
pytest packages/popkit-ops/skills/pop-benchmark-runner/tests/test_report_generator.py -v
```

### Integration Tests

```bash
# Test single task execution
/popkit-ops:benchmark run jwt-authentication --trials 1

# Test full suite
/popkit-ops:benchmark run all --trials 3
```

## Success Criteria

For Phase 1 completion:

- ✅ All 4 core modules implemented
- ✅ Command file created
- ✅ Skill documentation complete
- ✅ 2 example task definitions created
- ✅ Codebase manager tested with git worktrees
- ✅ Benchmark runner tested in mock mode
- ✅ Analyzer tested with sample data
- ✅ Report generator tested with sample data

For full benchmark validation:

- [ ] All 8 tasks complete successfully
- [ ] Statistical significance (p < 0.05) for 4+ metrics
- [ ] Large effect size (Cohen's d > 0.8) for 3+ metrics
- [ ] Consistent results (std dev < 20% of mean)
- [ ] CI/CD workflow operational

## Known Limitations

1. **Mock Execution**: Phase 1 uses mock Claude Code execution. Phase 2 will integrate real instances.
2. **Task Coverage**: Only 2 tasks defined (JWT auth, race condition). Need 6 more for full suite.
3. **Windows Path Length**: Using short paths (`C:/temp/bench/`) to avoid MAX_PATH issues.
4. **CI Configuration**: GitHub Actions workflow not yet implemented.

## Related Documentation

- [Issue #82](https://github.com/jrc1883/popkit-ai/issues/82) - Original feature request
- [docs/VIBE_CODED_BENCHMARK_RESULTS.md](docs/VIBE_CODED_BENCHMARK_RESULTS.md) - Vibe-coded ambiguity benchmark tracking (Issue #84)
- [SKILL.md](SKILL.md) - Detailed skill documentation
- [../../commands/benchmark.md](../../commands/benchmark.md) - Command reference
- [Plan](~/.claude/plans/modular-honking-pretzel.md) - Implementation plan

## License

MIT
