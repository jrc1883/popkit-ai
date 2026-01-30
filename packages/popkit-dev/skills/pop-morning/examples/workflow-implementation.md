# Workflow Implementation

Complete workflow steps with code examples.

## 1. Restore Previous Session

Load context from STATUS.json:

```python
from pathlib import Path
import json

status_file = Path('STATUS.json')
if status_file.exists():
    status = json.loads(status_file.read_text())

    # Extract session context
    last_nightly = status.get('last_nightly_routine', {})
    git_status = status.get('git_status', {})

    session_data = {
        'restored': True,
        'last_nightly_score': last_nightly.get('sleep_score'),
        'last_work_summary': git_status.get('action_required'),
        'previous_branch': git_status.get('current_branch'),
        'stashed_count': git_status.get('stashes', 0)
    }
```

**Restored Context Includes:**

- Last nightly routine Sleep Score
- Previous work summary
- Git branch and uncommitted work
- Stashed changes count

## 2. Check Dev Environment

Using `capture_state.py` utility with morning-specific checks:

```python
from popkit_shared.utils.capture_state import capture_project_state

state = capture_project_state()
# Returns: {
#   'git': {...},
#   'github': {...},
#   'services': {...}
# }
```

**Git Analysis:**

- Current branch
- Commits behind remote (after git fetch)
- Uncommitted files
- Stashed changes

**GitHub Analysis:**

- PRs needing review (no review decision or changes requested)
- Issues needing triage (no assignee or labels)
- Latest CI status

**Service Analysis:**

- Running dev services (node, npm, pnpm, redis, postgres, supabase)
- Required services vs. running services

**Dependency Analysis:**

- Outdated package count
- Major/minor updates available

## 3. Calculate Ready to Code Score

Using `ready_to_code_score.py` module:

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

## 4. Generate Morning Report

Using `morning_report_generator.py` module:

```python
from pop_morning.scripts.morning_report_generator import generate_morning_report

report = generate_morning_report(score, breakdown, state)
# Returns formatted markdown report with:
# - Ready to Code Score headline
# - Score breakdown table
# - Service status (if not all running)
# - Setup recommendations
# - Today's focus items
```

## 5. Capture Session State

Update STATUS.json with morning routine data:

```python
# This happens automatically via direct STATUS.json update
# Updates STATUS.json with:
# - Morning routine execution timestamp
# - Ready to Code score
# - Session restoration status
# - Dev environment state
# - Recommendations
```

## 6. Present Report to User

Display morning report with:

- **Ready to Code Score** (0-100) with visual indicator
- **Score Breakdown** - What contributed to the score
- **Setup Issues** - Services down, sync needed, outdated deps
- **Recommendations** - Actions before coding
- **Today's Focus** - PRs to review, issues to triage
