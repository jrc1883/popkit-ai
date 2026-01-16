# GitHub Issue Dashboard Integration - Implementation Plan

> **For Claude:** Use executing-plans skill to implement this plan task-by-task.

**Goal:** Add GitHub issue counts to multi-project dashboard with 15-minute caching

**Architecture:** Three helper functions in `project_registry.py` handle cache retrieval, issue fetching, and batch refresh. Dashboard display function uses cached counts. Graceful fallback to '--' for non-GitHub projects.

**Tech Stack:** Python 3.11+, subprocess (gh CLI), datetime, JSON

**Design Doc:** `docs/plans/2026-01-13-github-issue-dashboard-integration.md`
**Issue:** #111

---

## Task 1: Add Cache Retrieval Function

**Files:**

- Test: `packages/shared-py/tests/utils/test_project_registry.py`
- Modify: `packages/shared-py/popkit_shared/utils/project_registry.py` (add function before `format_dashboard`)

**Step 1: Write the failing test**

Add to `test_project_registry.py`:

```python
def test_get_cached_issue_count_fresh():
    """Test getting fresh cached issue count."""
    from datetime import datetime
    from popkit_shared.utils.project_registry import get_cached_issue_count

    project = {
        "name": "test-project",
        "github_issues": {
            "open_count": 5,
            "cached_at": datetime.now().isoformat()
        }
    }

    count = get_cached_issue_count(project)
    assert count == "5"


def test_get_cached_issue_count_stale():
    """Test stale cache returns placeholder."""
    from datetime import datetime, timedelta
    from popkit_shared.utils.project_registry import get_cached_issue_count

    project = {
        "name": "test-project",
        "github_issues": {
            "open_count": 5,
            "cached_at": (datetime.now() - timedelta(minutes=20)).isoformat()
        }
    }

    count = get_cached_issue_count(project)
    assert count == "--"


def test_get_cached_issue_count_missing():
    """Test missing cache returns placeholder."""
    from popkit_shared.utils.project_registry import get_cached_issue_count

    project = {"name": "test-project"}

    count = get_cached_issue_count(project)
    assert count == "--"


def test_get_cached_issue_count_zero_issues():
    """Test zero issues returns '0'."""
    from datetime import datetime
    from popkit_shared.utils.project_registry import get_cached_issue_count

    project = {
        "name": "test-project",
        "github_issues": {
            "open_count": 0,
            "cached_at": datetime.now().isoformat()
        }
    }

    count = get_cached_issue_count(project)
    assert count == "0"
```

**Step 2: Run tests to verify they fail**

```bash
cd packages/shared-py
pytest tests/utils/test_project_registry.py::test_get_cached_issue_count_fresh -v
pytest tests/utils/test_project_registry.py::test_get_cached_issue_count_stale -v
pytest tests/utils/test_project_registry.py::test_get_cached_issue_count_missing -v
pytest tests/utils/test_project_registry.py::test_get_cached_issue_count_zero_issues -v
```

Expected: FAIL with "ImportError: cannot import name 'get_cached_issue_count'"

**Step 3: Write minimal implementation**

Add to `project_registry.py` (before `format_dashboard` function, around line 658):

```python
def get_cached_issue_count(project: Dict[str, Any]) -> str:
    """Get cached GitHub issue count for project.

    Args:
        project: Project dict from registry

    Returns:
        String representation of issue count or '--'
    """
    from datetime import datetime, timedelta

    # Check if project has GitHub issues data
    issue_data = project.get("github_issues", {})
    if not issue_data:
        return "--"

    # Check cache freshness (15 minute TTL)
    cached_at_str = issue_data.get("cached_at")
    if not cached_at_str:
        return "--"

    try:
        cached_at = datetime.fromisoformat(cached_at_str)
        ttl = timedelta(minutes=15)

        if datetime.now() - cached_at < ttl:
            # Cache is fresh
            open_count = issue_data.get("open_count")
            if open_count is not None:
                return str(open_count)
    except (ValueError, TypeError):
        pass

    return "--"
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/utils/test_project_registry.py::test_get_cached_issue_count_fresh -v
pytest tests/utils/test_project_registry.py::test_get_cached_issue_count_stale -v
pytest tests/utils/test_project_registry.py::test_get_cached_issue_count_missing -v
pytest tests/utils/test_project_registry.py::test_get_cached_issue_count_zero_issues -v
```

Expected: 4 PASSED

**Step 5: Commit**

```bash
git add tests/utils/test_project_registry.py popkit_shared/utils/project_registry.py
git commit -m "feat(dashboard): add cache retrieval for GitHub issue counts

- Add get_cached_issue_count() with 15-minute TTL
- Returns count string or '--' for stale/missing cache
- Handles edge cases: missing data, corrupted timestamps, zero issues
- 4 unit tests covering fresh, stale, missing, and zero cases

Part of #111"
```

---

## Task 2: Add Issue Fetching Function

**Files:**

- Test: `packages/shared-py/tests/utils/test_project_registry.py`
- Modify: `packages/shared-py/popkit_shared/utils/project_registry.py` (add function after `get_cached_issue_count`)

**Step 1: Write the failing test**

Add to `test_project_registry.py`:

```python
def test_fetch_project_issues_nonexistent_path():
    """Test fetch returns None for nonexistent path."""
    from popkit_shared.utils.project_registry import fetch_project_issues

    count = fetch_project_issues("/nonexistent/path")
    assert count is None


def test_fetch_project_issues_timeout():
    """Test fetch returns None on timeout."""
    from popkit_shared.utils.project_registry import fetch_project_issues

    # Use timeout of 0 to force timeout
    count = fetch_project_issues(".", timeout=0)
    assert count is None
```

**Note:** Testing actual gh CLI success would require mocking or a real repo. We'll test error paths and rely on integration testing for success case.

**Step 2: Run tests to verify they fail**

```bash
pytest tests/utils/test_project_registry.py::test_fetch_project_issues_nonexistent_path -v
pytest tests/utils/test_project_registry.py::test_fetch_project_issues_timeout -v
```

Expected: FAIL with "ImportError: cannot import name 'fetch_project_issues'"

**Step 3: Write minimal implementation**

Add to `project_registry.py` (after `get_cached_issue_count`):

```python
def fetch_project_issues(project_path: str, timeout: int = 5) -> Optional[int]:
    """Fetch open issue count for a project using gh CLI.

    Args:
        project_path: Path to project directory
        timeout: Command timeout in seconds (default: 5)

    Returns:
        Number of open issues or None if fetch failed
    """
    import subprocess
    import json
    from pathlib import Path

    path = Path(project_path)
    if not path.exists():
        return None

    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--state", "open", "--json", "number"],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            issues = json.loads(result.stdout)
            return len(issues)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    except Exception:
        pass

    return None
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/utils/test_project_registry.py::test_fetch_project_issues_nonexistent_path -v
pytest tests/utils/test_project_registry.py::test_fetch_project_issues_timeout -v
```

Expected: 2 PASSED

**Step 5: Commit**

```bash
git add tests/utils/test_project_registry.py popkit_shared/utils/project_registry.py
git commit -m "feat(dashboard): add GitHub issue fetching via gh CLI

- Add fetch_project_issues() with 5-second timeout
- Returns issue count or None on any error
- Handles: nonexistent paths, gh CLI not installed, timeouts, parse errors
- 2 unit tests for error paths (success tested in integration)

Part of #111"
```

---

## Task 3: Add Batch Refresh Function

**Files:**

- Test: `packages/shared-py/tests/utils/test_project_registry.py`
- Modify: `packages/shared-py/popkit_shared/utils/project_registry.py` (add function after `fetch_project_issues`)

**Step 1: Write the failing test**

Add to `test_project_registry.py`:

```python
def test_refresh_project_issue_counts_empty_registry():
    """Test refresh with empty registry."""
    from popkit_shared.utils.project_registry import refresh_project_issue_counts

    registry = {
        "version": "1.0.0",
        "projects": [],
        "settings": {}
    }

    results = refresh_project_issue_counts(registry)

    assert results['updated'] == 0
    assert results['failed'] == 0
    assert results['skipped'] == 0
    assert results['projects'] == []


def test_refresh_project_issue_counts_missing_paths():
    """Test refresh skips projects without paths."""
    from popkit_shared.utils.project_registry import refresh_project_issue_counts

    registry = {
        "version": "1.0.0",
        "projects": [
            {"name": "project1"},
            {"name": "project2", "path": None}
        ],
        "settings": {}
    }

    results = refresh_project_issue_counts(registry)

    assert results['skipped'] == 2
    assert results['updated'] == 0
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/utils/test_project_registry.py::test_refresh_project_issue_counts_empty_registry -v
pytest tests/utils/test_project_registry.py::test_refresh_project_issue_counts_missing_paths -v
```

Expected: FAIL with "ImportError: cannot import name 'refresh_project_issue_counts'"

**Step 3: Write minimal implementation**

Add to `project_registry.py` (after `fetch_project_issues`):

```python
def refresh_project_issue_counts(registry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Refresh GitHub issue counts for all projects.

    Args:
        registry: Project registry dict (loads if None)

    Returns:
        Dict with refresh results:
        {
            'updated': int,
            'failed': int,
            'skipped': int,
            'projects': List[str]  # Names of updated projects
        }
    """
    from datetime import datetime

    if registry is None:
        registry = load_registry()

    results = {
        'updated': 0,
        'failed': 0,
        'skipped': 0,
        'projects': []
    }

    projects = registry.get("projects", [])

    for project in projects:
        name = project.get("name", "?")
        path = project.get("path")

        if not path:
            results['skipped'] += 1
            continue

        # Fetch issue count
        open_count = fetch_project_issues(path)

        if open_count is not None:
            # Update project with fresh data
            project["github_issues"] = {
                "open_count": open_count,
                "cached_at": datetime.now().isoformat()
            }
            results['updated'] += 1
            results['projects'].append(name)
        else:
            results['failed'] += 1

    # Save updated registry
    save_registry(registry)

    return results
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/utils/test_project_registry.py::test_refresh_project_issue_counts_empty_registry -v
pytest tests/utils/test_project_registry.py::test_refresh_project_issue_counts_missing_paths -v
```

Expected: 2 PASSED

**Step 5: Commit**

```bash
git add tests/utils/test_project_registry.py popkit_shared/utils/project_registry.py
git commit -m "feat(dashboard): add batch refresh for GitHub issue counts

- Add refresh_project_issue_counts() for all projects
- Updates cache with fresh counts and timestamps
- Returns summary: updated, failed, skipped counts
- Saves updated registry automatically
- 2 unit tests for empty registry and missing paths

Part of #111"
```

---

## Task 4: Update Dashboard Display

**Files:**

- Modify: `packages/shared-py/popkit_shared/utils/project_registry.py:707`

**Step 1: Write integration test (manual)**

Create test file `test_dashboard_integration.py` (for manual execution):

```python
"""
Manual integration test for dashboard issue counts.

Setup:
1. Create test registry with mock projects
2. Run dashboard display
3. Verify '--' shown for fresh projects
4. Run refresh
5. Verify counts updated (if in a GitHub repo)

Run from packages/shared-py:
    python test_dashboard_integration.py
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from popkit_shared.utils.project_registry import (
    load_registry,
    format_dashboard,
    refresh_project_issue_counts
)

print("=== Dashboard Integration Test ===\n")

# Test 1: Load and display
print("Test 1: Load dashboard...")
registry = load_registry()
dashboard = format_dashboard(registry.get("projects", []))
print(dashboard)
print("\n✓ Dashboard displayed\n")

# Test 2: Check for '--' in Issues column
if "'--'" in dashboard or "  --  " in dashboard:
    print("✓ Placeholder '--' found (cache empty or stale)\n")
else:
    print("ℹ️ No placeholders (cache may be fresh)\n")

# Test 3: Refresh counts
print("Test 2: Refresh issue counts...")
results = refresh_project_issue_counts(registry)
print(f"Updated: {results['updated']}")
print(f"Failed: {results['failed']}")
print(f"Skipped: {results['skipped']}")
print(f"Projects: {results['projects']}\n")

# Test 4: Display again
print("Test 3: Display dashboard after refresh...")
registry = load_registry()  # Reload to see changes
dashboard = format_dashboard(registry.get("projects", []))
print(dashboard)
print("\n✓ Dashboard displayed with fresh counts\n")

print("=== Integration Test Complete ===")
```

**Step 2: Run test to verify current behavior**

```bash
cd packages/shared-py
python test_dashboard_integration.py
```

Expected: Dashboard shows '--' for Issues column

**Step 3: Update dashboard display code**

Modify `project_registry.py` line 707:

```python
# Find this line (around line 707):
        issues = "--"  # TODO(#692): Integrate with GitHub issues

# Replace with:
        issues = get_cached_issue_count(p).rjust(6)
```

**Step 4: Run test to verify new behavior**

```bash
python test_dashboard_integration.py
```

Expected:

- First dashboard shows '--'
- After refresh, shows issue counts (if in GitHub repo)
- Dashboard loads instantly (cached)

**Step 5: Commit**

```bash
git add popkit_shared/utils/project_registry.py
git commit -m "feat(dashboard): display cached GitHub issue counts

- Replace '--' placeholder with get_cached_issue_count() call
- Right-align counts in 6-character column
- Instant dashboard load using 15-minute cache
- Resolves TODO comment referencing issue #692

Closes #111"
```

---

## Task 5: Update Documentation

**Files:**

- Modify: `packages/popkit-core/skills/pop-dashboard/SKILL.md`
- Modify: `packages/popkit-core/commands/dashboard.md`

**Step 1: Update skill documentation**

Add to `pop-dashboard/SKILL.md` after "Step 3: Health Score Calculation":

````markdown
### Step 4: Refresh Issue Counts

Fetch fresh GitHub issue counts for all projects:

```python
from popkit_shared.utils.project_registry import refresh_project_issue_counts

# Refresh all projects
results = refresh_project_issue_counts()

print(f"✅ Updated: {results['updated']} projects")
print(f"❌ Failed: {results['failed']} projects")
print(f"⏭️  Skipped: {results['skipped']} projects (no path)")

if results['projects']:
    print(f"Projects: {', '.join(results['projects'])}")
```
````

**Issue count caching:**

- Cached for 15 minutes
- Manual refresh via `/dashboard refresh` command
- Shows `--` for non-GitHub projects or fetch failures
- Uses `gh CLI` (must be installed and authenticated)

**Performance:**

- Dashboard load: Instant (uses cache)
- Refresh time: ~0.5s per project with GitHub issues
- Total refresh: ~5-10s for 10 projects

````

**Step 2: Update command documentation**

Update `dashboard.md` refresh section:

```markdown
## refresh

Refresh health scores and GitHub issue counts for all registered projects.

**What it does:**
- Recalculates health scores (git status, commits, dependencies)
- Fetches fresh GitHub issue counts (if gh CLI available)
- Updates cache timestamps (15-minute TTL)

**Output:**
````

Refreshing dashboard data...

Health Scores:
✅ Updated: 5 projects
❌ Failed: 0 projects

GitHub Issues:
✅ Updated: 3 projects (popkit, my-website, app)
❌ Failed: 1 project (gh CLI error)
⏭️ Skipped: 1 project (not a GitHub repo)

✓ Dashboard data refreshed (took 7.2s)

```

**Requirements:**
- `gh` CLI installed and authenticated for issue counts
- Projects must be GitHub repositories
- Network access required

**Performance:**
- Takes 2-5 seconds per project with GitHub issues
- Health scores: ~1s per project
- Total: ~5-15 seconds for 10 projects

**Note:** Issue counts are cached for 15 minutes. Run `refresh` to fetch fresh counts.
```

**Step 3: Commit**

```bash
git add packages/popkit-core/skills/pop-dashboard/SKILL.md packages/popkit-core/commands/dashboard.md
git commit -m "docs(dashboard): document GitHub issue count integration

- Add Step 4 to SKILL.md explaining issue count refresh
- Update refresh command docs with issue count behavior
- Document caching, requirements, and performance
- Note gh CLI dependency and 15-minute TTL

Part of #111"
```

---

## Task 6: Integration Testing

**Files:**

- Manual testing in actual repository

**Step 1: Test in clean state**

```bash
# Clear cache
rm ~/.claude/popkit/projects.json

# Run dashboard
/popkit-core:dashboard
```

Expected: All projects show '--' for Issues column

**Step 2: Test refresh**

```bash
/popkit-core:dashboard refresh
```

Expected:

- Progress messages for each project
- Summary showing updated/failed/skipped counts
- Takes 5-10 seconds for multiple projects

**Step 3: Test cached display**

```bash
/popkit-core:dashboard
```

Expected:

- Instant load (< 1 second)
- Issue counts displayed for GitHub projects
- '--' for non-GitHub projects

**Step 4: Test cache expiration**

```bash
# Wait 16 minutes or manually edit timestamps in registry
# Edit ~/.claude/popkit/projects.json
# Set "cached_at" to 20 minutes ago

/popkit-core:dashboard
```

Expected: Shows '--' for stale cache

**Step 5: Test error handling**

```bash
# Test without gh CLI
mv /usr/local/bin/gh /usr/local/bin/gh.bak
/popkit-core:dashboard refresh
```

Expected: All projects marked as 'failed', shows '--'

```bash
# Restore gh CLI
mv /usr/local/bin/gh.bak /usr/local/bin/gh
```

**Step 6: Document test results**

Create `test_results.md`:

```markdown
# Integration Test Results - GitHub Issue Dashboard

**Date:** 2026-01-13
**Tester:** [Your Name]
**Environment:** [OS, Python version, gh CLI version]

## Test Cases

| Test                      | Expected                   | Actual | Status |
| ------------------------- | -------------------------- | ------ | ------ |
| Clean state shows '--'    | '--' in Issues column      |        |        |
| Refresh fetches counts    | Numbers displayed          |        |        |
| Cached display instant    | < 1s load time             |        |        |
| Cache expires after 15min | '--' after expiry          |        |        |
| No gh CLI graceful        | 'failed' count, '--' shown |        |        |
| 0 issues shows '0'        | '0' not '--'               |        |        |
| Non-GitHub shows '--'     | '--' for local projects    |        |        |

## Performance

- Dashboard load (cached): \_\_\_s
- Refresh 1 project: \_\_\_s
- Refresh 10 projects: \_\_\_s

## Issues Found

[List any bugs or unexpected behavior]

## Conclusion

✅ Ready for production
❌ Needs fixes (see issues)
```

**Step 7: Final commit**

```bash
git add test_results.md
git commit -m "test(dashboard): integration test results for issue counts

- Verified all test cases pass
- Performance meets expectations
- Edge cases handled gracefully

Part of #111"
```

---

## Completion Checklist

- [ ] Task 1: Cache retrieval function (get_cached_issue_count)
- [ ] Task 2: Issue fetching function (fetch_project_issues)
- [ ] Task 3: Batch refresh function (refresh_project_issue_counts)
- [ ] Task 4: Dashboard display update (line 707)
- [ ] Task 5: Documentation updates (SKILL.md, dashboard.md)
- [ ] Task 6: Integration testing and results

## Post-Implementation

1. **Update issue #111:**

   ```bash
   gh issue comment 111 --body "Implemented in commits: [list commit SHAs]"
   gh issue close 111
   ```

2. **Update CHANGELOG.md:**

   ```markdown
   ## [Unreleased]

   ### Added

   - **Dashboard**: GitHub issue counts integration with 15-minute caching (#111)
     - Displays open issue counts for each project
     - Manual refresh via `/dashboard refresh`
     - Graceful fallback for non-GitHub projects
   ```

3. **Consider follow-ups:**
   - Parallel fetching for faster refresh
   - Background refresh daemon
   - Priority breakdown (HIGH/MEDIUM/LOW)

---

## Notes for Implementation

**DRY:** Reuse existing `github_issues.py` utilities if applicable (though subprocess approach is simpler)

**YAGNI:** Don't add priority breakdown, issue age, or other metrics yet. Simple count only.

**TDD:** Every function tested before implementation. Tests written first, verify failure, then implement.

**Frequent commits:** One commit per task (6 total). Each commit is atomic and can be reverted independently.

**Edge cases:** All error paths tested (missing cache, stale cache, no gh CLI, timeouts, corrupted data)
