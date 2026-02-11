# Sleep Score System

Comprehensive health check across 6 dimensions (0-100 points).

## Score Components

| Check                  | Points | Criteria                            |
| ---------------------- | ------ | ----------------------------------- |
| Uncommitted work saved | 25     | No uncommitted changes OR committed |
| Branches cleaned       | 20     | No stale merged branches            |
| Issues updated         | 20     | Today's issues have status updates  |
| CI passing             | 15     | Latest CI run successful            |
| Services stopped       | 10     | No dev services running             |
| Logs archived          | 10     | Session logs saved                  |

## Branch Protection Impact (Issue #142)

If on protected branch with uncommitted work:

- **Warning:** Include ⚠️ PROTECTED indicator in output
- **Recommendation:** "Create feature branch and move uncommitted work before committing"
- **Option Priority:** Prioritize "Create feature branch" over "Commit and push"

## Score Interpretation

- **90-100**: Perfect shutdown - ready for tomorrow
- **70-89**: Good - minor cleanup needed
- **50-69**: Fair - some uncommitted work or failed CI
- **0-49**: Poor - significant cleanup required

## Calculation Implementation

```python
from pop_nightly.scripts.sleep_score import calculate_sleep_score

score, breakdown = calculate_sleep_score(state)
# score: 0-100
# breakdown: {
#   'uncommitted_work_saved': {'points': 0, 'max': 25, 'reason': '...'},
#   'branches_cleaned': {'points': 20, 'max': 20, 'reason': '...'},
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
