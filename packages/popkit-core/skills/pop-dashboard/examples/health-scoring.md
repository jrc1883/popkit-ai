# Health Score Calculation

## Health Score Breakdown

| Component         | Points | Criteria                                                                  |
| ----------------- | ------ | ------------------------------------------------------------------------- |
| **Git Status**    | 20     | Clean working tree (+20), uncommitted (-5/10 files), unpushed (-5/commit) |
| **Build Status**  | 20     | Passed (+20), warnings (-2 each), failed (0)                              |
| **Test Coverage** | 20     | >80% (+20), 60-80% (+15), <60% (+10), none (+5)                           |
| **Issue Health**  | 20     | No stale (+20), -2 per stale issue (>30 days)                             |
| **Activity**      | 20     | Today (+20), week (+15), month (+10), older (+5)                          |

## Implementation

```python
from health_calculator import calculate_health_score, calculate_quick_health

# Full health check (slower, more accurate)
result = calculate_health_score("/path/to/project")
print(f"Health: {result['score']}/100")
print(f"Breakdown: {result['breakdown']}")

# Quick health check (git + activity only)
quick_score = calculate_quick_health("/path/to/project")
print(f"Quick Health: {quick_score}/100")
```

## Performance

- **Full check**: ~2-3 seconds (runs tests, calculates coverage)
- **Quick check**: ~0.5 seconds (git status + file timestamps only)
- **Dashboard**: Uses quick check by default for speed

## Refresh Health Scores

```python
from project_registry import list_projects, update_health_score
from health_calculator import calculate_health_score

for project in list_projects():
    result = calculate_health_score(project["path"])
    update_health_score(project["name"], result["score"])
    print(f"{project['name']}: {result['score']}/100")
```
