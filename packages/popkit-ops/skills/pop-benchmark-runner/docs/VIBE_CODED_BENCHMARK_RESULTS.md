# Vibe-Coded Benchmark Results

## Status

- Last updated: 2026-02-18
- Issue: `#84`
- Scope: ambiguity handling benchmarks for intentionally vague prompts

## Path migration from legacy issue text

Issue `#84` referenced `packages/benchmarks/*` and `docs/research/*`, but active benchmark infrastructure is now:

- Tasks: `packages/popkit-ops/tasks/`
- Runner/orchestrator: `packages/popkit-ops/skills/pop-benchmark-runner/scripts/`
- Benchmark docs: `packages/popkit-ops/skills/pop-benchmark-runner/docs/`

## Vibe task IDs added

- `todo-app-vibe` (`packages/popkit-ops/tasks/feature-addition/todo-app-vibe.yml`)
- `bug-fix-vibe` (`packages/popkit-ops/tasks/bug-fixing/bug-fix-vibe.yml`)

## Dry-run execution (completed)

Date run: 2026-02-17 (local)
Mode: `benchmark_runner.py --test-mode --trials 1 --config all`

| Task ID         | With PopKit | Baseline    | Result |
| --------------- | ----------- | ----------- | ------ |
| `todo-app-vibe` | 1/1 success | 1/1 success | pass   |
| `bug-fix-vibe`  | 1/1 success | 1/1 success | pass   |

Notes:

- Dry runs validate orchestration plumbing, task resolution, and recording collection.
- Dry runs do **not** measure real implementation quality or ambiguity handling behavior.

## Real benchmark run commands

```bash
python packages/popkit-ops/skills/pop-benchmark-runner/scripts/benchmark_orchestrator.py todo-app-vibe --trials 3 --verbose
python packages/popkit-ops/skills/pop-benchmark-runner/scripts/benchmark_orchestrator.py bug-fix-vibe --trials 3 --verbose
```

## Comparison template for real runs

| Metric                | Structured Baseline | Vibe Baseline | Structured PopKit | Vibe PopKit | Notes                     |
| --------------------- | ------------------- | ------------- | ----------------- | ----------- | ------------------------- |
| Quality score (1-10)  | TBD                 | TBD           | TBD               | TBD         | Manual rubric             |
| Questions asked       | TBD                 | TBD           | TBD               | TBD         | Clarification count       |
| Assumptions made      | TBD                 | TBD           | TBD               | TBD         | Explicit assumption count |
| Brainstorming usage   | TBD                 | TBD           | TBD               | TBD         | Presence + usefulness     |
| Time to complete      | TBD                 | TBD           | TBD               | TBD         | Analyzer output           |
| Error recovery events | TBD                 | TBD           | TBD               | TBD         | Analyzer output           |

## Recommendations

1. Keep three prompt quality tiers: structured, junior, vibe-coded.
2. Add ambiguity-specific scoring (assumptions quality, clarification precision).
3. Preserve structured tasks for regression stability; use vibe-coded tasks for resilience testing.
4. Require both quantitative metrics and reviewer quality scoring for benchmark sign-off.
