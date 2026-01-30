# Integration with Existing Utilities

## capture_state.py

Located: `packages/shared-py/popkit_shared/utils/capture_state.py`

```python
def capture_project_state() -> dict:
    """Capture complete project state for morning routine."""
    return {
        'git': capture_git_state(),
        'github': capture_github_state(),
        'services': capture_service_state(),
        'timestamp': datetime.now().isoformat()
    }
```

## routine_measurement.py

Located: `packages/shared-py/popkit_shared/utils/routine_measurement.py`

When invoked with `--measure` flag:

- Tracks tool call count
- Measures duration
- Calculates token usage
- Saves to `.claude/popkit/measurements/morning-<timestamp>.json`

## routine_cache.py

Located: `packages/shared-py/popkit_shared/utils/routine_cache.py`

Caching strategy:

- **Never cache**: Git status (changes frequently)
- **Cache 5 min**: Service status, dependency checks
- **Cache 15 min**: GitHub PR/issue data

## Optimization Features

### Tool Call Reduction

- **Estimated Baseline**: ~15 tool calls (manual)
- **Optimized**: ~5 tool calls (automated)
- **Reduction**: ~67%

### Execution Time

- **Estimated Baseline**: ~90 seconds (manual, with thinking)
- **Optimized**: ~15-20 seconds (automated)
- **Improvement**: 78-83%

### Caching

With `--optimized` flag:

- Uses `routine_cache.py` for GitHub/service data
- Reduces redundant API calls
- 40-96% token reduction (per routine.md)
