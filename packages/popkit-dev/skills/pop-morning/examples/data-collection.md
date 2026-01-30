# Data Collection Commands

Consolidated bash commands for efficient data gathering.

## Git Commands (Consolidated)

Single command to gather all git data:

```bash
{
  git fetch --quiet
  echo "=== BRANCH ==="
  git rev-parse --abbrev-ref HEAD
  echo "=== BEHIND ==="
  git rev-list --count HEAD..origin/$(git rev-parse --abbrev-ref HEAD)
  echo "=== STATUS ==="
  git status --porcelain
  echo "=== STASHES ==="
  git stash list | wc -l
}
```

## GitHub Commands (Consolidated)

```bash
{
  gh pr list --state open --json number,title,reviewDecision
  echo "---SEPARATOR---"
  gh issue list --state open --json number,title,assignees,labels
} > /tmp/gh_morning_data.json
```

## Service Check (Consolidated)

```bash
{
  ps aux | grep -E "(node|npm|pnpm|redis|postgres|supabase)" | grep -v grep
  echo "---SEPARATOR---"
  pnpm outdated --json 2>/dev/null || echo "{}"
} > /tmp/service_morning_data.txt
```

## Integration with capture_state.py

These commands are wrapped in the `capture_state.py` utility for consistent error handling and parsing.

```python
from popkit_shared.utils.capture_state import (
    capture_git_state,
    capture_github_state,
    capture_service_state,
    capture_project_state
)

# Capture all state at once
state = capture_project_state()
```
