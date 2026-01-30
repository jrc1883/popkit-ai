# Ready to Code Score System

Comprehensive readiness check across 6 dimensions (0-100 points).

## Score Components

| Check | Points | Criteria |
|-------|--------|----------|
| Session Restored | 20 | Previous session context restored from STATUS.json |
| Services Healthy | 20 | All required dev services running |
| Dependencies Updated | 15 | Package dependencies up to date |
| Branches Synced | 15 | Local branch synced with remote |
| PRs Reviewed | 15 | No PRs waiting for review |
| Issues Triaged | 15 | All issues assigned/prioritized |

## Branch Protection Penalty (Issue #142)

If on protected branch (`main`, `master`, `develop`, `production`) with uncommitted changes:

- **Penalty:** -10 points from Branches Synced score
- **Indicator:** Show ⚠️ PROTECTED warning in Current State table
- **Recommendation:** Create feature branch before starting work

## Score Interpretation

- **90-100**: Excellent - Fully ready to code
- **80-89**: Very Good - Almost ready, minor setup
- **70-79**: Good - Ready with minor issues
- **60-69**: Fair - 10-15 minutes setup needed
- **50-59**: Poor - Significant setup required
- **0-49**: Not Ready - Focus on environment setup

## Calculation Implementation

```python
from pop_morning.scripts.ready_to_code_score import calculate_ready_to_code_score

score, breakdown = calculate_ready_to_code_score(state)
# score: 0-100
# breakdown: {
#   'session_restored': {'points': 20, 'max': 20, 'reason': '...'},
#   'services_healthy': {'points': 10, 'max': 20, 'reason': '...'},
#   ...
# }
```

## Protected Branch Detection

```python
from popkit_shared.utils.session_recorder import is_recording_enabled, record_reasoning

# Get current branch
current_branch = git_output['branch']

# Protected branches
PROTECTED_BRANCHES = ["main", "master", "develop", "production"]
is_protected = current_branch in PROTECTED_BRANCHES

# Record if on protected branch
if is_recording_enabled():
    record_reasoning(
        step="Check branch protection",
        reasoning=f"Branch '{current_branch}' is {'PROTECTED' if is_protected else 'not protected'}",
        data={
            "current_branch": current_branch,
            "is_protected": is_protected
        }
    )
```
