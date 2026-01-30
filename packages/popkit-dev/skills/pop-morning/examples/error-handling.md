# Error Handling

Graceful degradation for missing tools or failures.

## Git Not Available

```python
try:
    git_state = capture_git_state()
except GitNotFoundError:
    print("[WARN] Git not available - skipping git checks")
    # Continue with partial score
```

## GitHub CLI Not Available

```python
try:
    github_state = capture_github_state()
except GhNotFoundError:
    print("[WARN] GitHub CLI not available - skipping GitHub checks")
    # Continue with partial score
```

## Service Check Failures

```python
# Service checks are best-effort
# If they fail, provide recommendations but don't block
```

## Session Restore Failures

```python
try:
    session_data = restore_session()
except Exception:
    print("[WARN] Could not restore session - starting fresh")
    session_data = {'restored': False}
```

## Best Practices

- **Never block**: Continue with partial score if tools unavailable
- **Clear warnings**: Tell user what checks were skipped
- **Graceful degradation**: Provide best possible score with available data
- **Helpful messages**: Guide user to install missing tools if needed
