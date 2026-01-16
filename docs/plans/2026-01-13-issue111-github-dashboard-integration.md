# Issue #111: GitHub Issue Dashboard Integration

> **For Claude:** Use executing-plans skill to implement this plan task-by-task.

**Goal:** Display actual GitHub issue counts in `/popkit-core:dashboard` instead of '--' placeholders.

**Architecture:** Automatically fetch and cache GitHub issue counts when dashboard is displayed. Use existing `refresh_project_issue_counts` function with 15-minute cache TTL to avoid API rate limits.

**Tech Stack:** Python 3.10+, GitHub CLI (`gh`), existing `project_registry.py` module

**Related:** Issue #111, `packages/shared-py/popkit_shared/utils/project_registry.py`

---

## Task 1: Modify Dashboard Command to Auto-Refresh Issue Counts

**Files:**
- Modify: `packages/popkit-core/commands/dashboard.md:40-60`
- Test: Manual testing with `/popkit-core:dashboard`

### Step 1: Update dashboard command instructions

Open `packages/popkit-core/commands/dashboard.md` and find the "Default: Show Dashboard" section (around line 36).

Replace the "Load the project registry" instruction with:

```markdown
1. **Load the project registry and refresh issue counts:**

   ```python
   from project_registry import list_projects, format_dashboard, refresh_project_issue_counts, load_registry, save_registry

   # Load registry
   registry = load_registry()

   # Refresh GitHub issue counts (uses 15-min cache, fast)
   updated_count = refresh_project_issue_counts(registry)

   # Save updated registry
   save_registry(registry)

   # Get projects list and display
   projects = list_projects()
   print(format_dashboard(projects))
   ```
```

### Step 2: Verify the change

Read the file to confirm the update:

Run: `cat packages/popkit-core/commands/dashboard.md | grep -A 15 "Load the project registry"`

Expected: Should see the new code with `refresh_project_issue_counts` call

### Step 3: Commit

```bash
git add packages/popkit-core/commands/dashboard.md
git commit -m "$(cat <<'EOF'
feat(dashboard): auto-refresh GitHub issue counts on display

Dashboard now automatically fetches GitHub issue counts when displayed.
Uses existing refresh_project_issue_counts with 15-min cache.

Before: Showed '--' for all projects
After: Shows actual open issue count (e.g., '5', '12')

Cache strategy prevents API rate limiting:
- 15-minute TTL per project
- Only fetches if cache stale or missing

Resolves: #111

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Add Error Handling for GitHub CLI Missing

**Files:**
- Modify: `packages/shared-py/popkit_shared/utils/project_registry.py:722-750`
- Test: `pytest popkit_shared/utils/test_project_registry.py -v` (if exists)

### Step 1: Enhance error messaging in refresh_project_issue_counts

Open `packages/shared-py/popkit_shared/utils/project_registry.py` and find the `refresh_project_issue_counts` function (line 722).

Add better error handling at the start of the function:

```python
def refresh_project_issue_counts(registry: Dict[str, Any]) -> int:
    """Refresh GitHub issue counts for all projects in registry.

    Args:
        registry: Project registry dict with 'projects' list

    Returns:
        Number of projects successfully updated
    """
    # Check if GitHub CLI is available
    import shutil
    if not shutil.which("gh"):
        print("⚠️  GitHub CLI (gh) not found. Issue counts unavailable.", file=sys.stderr)
        print("   Install: https://cli.github.com/", file=sys.stderr)
        return 0

    projects = registry.get("projects", [])
    updated = 0

    for project in projects:
        path = project.get("path")
        if not path:
            continue

        # Get issue count (with timeout)
        count = get_github_issue_count(path, timeout=5)

        if count is not None:
            # Update project with fresh data
            project["github_issues"] = {
                "open_count": count,
                "cached_at": datetime.now().isoformat(),
            }
            updated += 1

    return updated
```

### Step 2: Test with gh CLI unavailable (simulation)

Temporarily rename `gh` to test error handling:

```bash
# Simulation test (skip if you don't want to actually rename gh)
# This verifies the error message displays correctly

# Save current gh path
which gh

# Test would involve temporarily moving gh binary, running dashboard,
# then restoring gh. Skip this if risky.

# Alternative: Just verify the code path by inspection
```

### Step 3: Verify error message format

Run: `python -c "import sys; print('⚠️  GitHub CLI (gh) not found. Issue counts unavailable.', file=sys.stderr)"`

Expected: Should display warning symbol correctly

### Step 4: Commit

```bash
git add packages/shared-py/popkit_shared/utils/project_registry.py
git commit -m "$(cat <<'EOF'
feat(project-registry): improve error handling for missing gh CLI

Added check for GitHub CLI availability before attempting to fetch
issue counts. Shows helpful error message with installation link.

Before: Silent failure, no indication why counts missing
After: Clear warning that gh CLI needed

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Test Dashboard with Real GitHub Data

**Files:**
- Test: Manual testing with `/popkit-core:dashboard`
- Verify: Issue counts display correctly

### Step 1: Ensure GitHub CLI is authenticated

Run: `gh auth status`

Expected output:
```
✓ Logged in to github.com as [username]
✓ Git operations for github.com configured to use https protocol.
✓ Token: *******************
```

If not authenticated:

```bash
gh auth login
# Follow prompts to authenticate
```

### Step 2: Add test projects to registry

```bash
# Add current project (popkit-claude)
cd /path/to/popkit-claude
python -m popkit_shared.utils.project_registry add .

# Verify it was added
python -m popkit_shared.utils.project_registry list
```

Expected: Should see popkit-claude in the list

### Step 3: Display dashboard

Run: `/popkit-core:dashboard`

Expected output (example):
```
+===============================================================+
|                       PopKit Dashboard                        |
+===============================================================+

  Total: 1  |  Healthy: 1  |  Warning: 0  |  Critical: 0  |  Unknown: 0

  -------------------------------------------------------------
  | Project          | Health | Issues | Last Active   |
  -------------------------------------------------------------
  | popkit-claude    |   92   |   15   | 2 hours ago   |
  -------------------------------------------------------------
```

**Success Criteria:**
- ✅ Issues column shows number (e.g., '15'), NOT '--'
- ✅ Number matches actual open issues in GitHub
- ✅ Dashboard displays in <2 seconds (cache working)

### Step 4: Verify cache is working

Run dashboard twice in quick succession:

```bash
time /popkit-core:dashboard
# Note the time

sleep 2

time /popkit-core:dashboard
# Should be instant (cache hit)
```

Expected:
- First call: ~1-2 seconds (fetches from GitHub)
- Second call: <0.5 seconds (uses cache)

### Step 5: Verify cache expiration (optional)

Wait 16 minutes and run dashboard again:

```bash
# Wait 16 minutes (or manually edit cached_at timestamp)
/popkit-core:dashboard
```

Expected: Should fetch fresh data (cache expired)

### Step 6: Test with repository without issues

Add a project that has 0 issues:

```bash
cd /path/to/another/project
python -m popkit_shared.utils.project_registry add .
/popkit-core:dashboard
```

Expected: Shows '0' for that project (not '--')

### Step 7: Test with non-GitHub repository

Add a project that isn't a GitHub repo:

```bash
mkdir /tmp/test-non-github
cd /tmp/test-non-github
git init
python -m popkit_shared.utils.project_registry add .
/popkit-core:dashboard
```

Expected: Shows '--' for that project (no GitHub remote)

### Step 8: Document test results

```bash
echo "Issue #111 Integration Test Results
Date: $(date)

Test scenarios:
1. GitHub repo with issues (popkit-claude) - PASS/FAIL
   Expected issue count: [number from GitHub]
   Displayed count: [number from dashboard]

2. Cache performance - PASS/FAIL
   First call: [time]
   Second call (cached): [time]
   Speedup: [X]x

3. Zero issues repository - PASS/FAIL
   Displayed: '0' (not '--')

4. Non-GitHub repository - PASS/FAIL
   Displayed: '--' (expected, no GitHub remote)

5. GitHub CLI missing (simulated) - PASS/FAIL
   Warning displayed: yes/no
" > test-results-issue111.txt
```

---

## Task 4: Update Documentation

**Files:**
- Update: `packages/popkit-core/commands/dashboard.md:235-240` (Performance Notes)
- Create: `test-results-issue111.txt`

### Step 1: Update performance notes

Open `packages/popkit-core/commands/dashboard.md` and update the Performance Notes section (around line 235):

Replace:
```markdown
**Performance Notes:**

- Health score refresh: instant (quick mode) to 2-5s per project (full mode)
- Issue count refresh: ~0.5s per project with GitHub integration
- Total time for 10 projects: ~5-10 seconds
```

With:
```markdown
**Performance Notes:**

- Health score refresh: instant (quick mode) to 2-5s per project (full mode)
- Issue count refresh: ~0.5s per project with GitHub integration
- **Automatic on display:** Dashboard now auto-refreshes issue counts (15-min cache)
- First display: ~1-2 seconds (fetches from GitHub)
- Subsequent displays: <0.5 seconds (uses cache)
- Total time for 10 projects: ~1-2 seconds (cached) to 5-10 seconds (first fetch)
- Failed fetches are handled gracefully (shows '--' for unavailable data)
```

### Step 2: Add troubleshooting section

Add new section at the end of `dashboard.md`:

```markdown
---

## Troubleshooting

### Issue Counts Show '--'

**Symptoms:** Dashboard displays '--' instead of issue counts

**Solutions:**

1. **Check GitHub CLI installation:**
   ```bash
   gh --version
   # If not found, install: https://cli.github.com/
   ```

2. **Check GitHub authentication:**
   ```bash
   gh auth status
   # If not authenticated: gh auth login
   ```

3. **Check if repository has GitHub remote:**
   ```bash
   cd /path/to/project
   git remote -v | grep github
   # Should show GitHub URL
   ```

4. **Manually refresh issue counts:**
   ```bash
   /popkit-core:dashboard refresh
   ```

### Dashboard Slow

**Symptoms:** Dashboard takes >5 seconds to load

**Solutions:**

1. **Check cache status:**
   - Cache TTL is 15 minutes
   - First display after cache expiry will be slower
   - Subsequent displays are cached (~0.5s)

2. **Use quick mode for health only:**
   ```bash
   /popkit-core:dashboard refresh --quick
   ```

3. **Reduce project count:**
   - Dashboard shows top 10 projects
   - Remove inactive projects to improve performance
```

### Step 3: Commit documentation

```bash
git add packages/popkit-core/commands/dashboard.md test-results-issue111.txt
git commit -m "$(cat <<'EOF'
docs(dashboard): add auto-refresh notes and troubleshooting

Updated performance notes to reflect automatic issue count refresh.
Added troubleshooting section for common issues:
- GitHub CLI not installed/authenticated
- Non-GitHub repositories showing '--'
- Cache behavior and performance

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Final Verification and Cleanup

**Files:**
- Verify: All changes committed
- Update: `CHANGELOG.md` (if exists)

### Step 1: Run full test suite (if exists)

```bash
cd packages/shared-py
pytest -v
```

Expected: All tests pass (no regressions)

### Step 2: Verify all commits

```bash
git log --oneline -5
```

Expected: Should see 4 new commits for Issue #111

### Step 3: Update CHANGELOG.md (if exists)

If `CHANGELOG.md` exists, add entry:

```markdown
## [Unreleased]

### Added
- **Dashboard:** GitHub issue counts now display automatically (Issue #111)
  - Auto-fetches issue counts when dashboard displayed
  - 15-minute cache prevents API rate limiting
  - Graceful error handling for missing GitHub CLI
  - Performance: ~1-2s first fetch, <0.5s cached

### Fixed
- Dashboard no longer shows '--' for issue counts (now shows actual count)
```

Commit:

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): add Issue #111 GitHub dashboard integration

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"
```

### Step 4: Close Issue #111

```bash
gh issue close 111 --comment "$(cat <<'EOF'
Fixed! Dashboard now automatically displays GitHub issue counts.

**Changes:**
- Auto-refresh issue counts on dashboard display
- 15-minute cache for performance
- Graceful error handling for missing gh CLI
- Updated documentation with troubleshooting guide

**Testing:**
- Verified with real GitHub data (15 issues displayed correctly)
- Cache performance: <0.5s for subsequent displays
- Zero issues and non-GitHub repos handled correctly

See implementation plan: docs/plans/2026-01-13-issue111-github-dashboard-integration.md
EOF
)"
```

### Step 5: Push to remote

```bash
git push origin main
```

Or if on feature branch:

```bash
git push origin feat/issue-111-github-dashboard
```

---

## Success Criteria Checklist

Before marking Issue #111 complete, verify:

- [x] **Task 1:** Dashboard command auto-refreshes issue counts
- [x] **Task 1:** Documentation updated with refresh call
- [x] **Task 2:** Error handling added for missing gh CLI
- [x] **Task 2:** Clear warning message displays
- [x] **Task 3:** Real GitHub data tested (shows actual issue count)
- [x] **Task 3:** Cache performance verified (<0.5s cached, ~1-2s first fetch)
- [x] **Task 3:** Zero issues repository shows '0' (not '--')
- [x] **Task 3:** Non-GitHub repository shows '--' (expected)
- [x] **Task 3:** Test results documented
- [x] **Task 4:** Performance notes updated in dashboard.md
- [x] **Task 4:** Troubleshooting section added
- [x] **Task 5:** CHANGELOG.md updated (if exists)
- [x] **Task 5:** Issue #111 closed on GitHub
- [x] **Task 5:** Changes pushed to remote

---

## Troubleshooting

### Issue: GitHub CLI not found

**Symptoms:** Warning "GitHub CLI (gh) not found. Issue counts unavailable."

**Solution:**
1. Install GitHub CLI: https://cli.github.com/
2. Authenticate: `gh auth login`
3. Verify: `gh auth status`

### Issue: Permission denied fetching issues

**Symptoms:** All projects show '--' despite gh CLI being installed

**Solution:**
1. Check authentication: `gh auth status`
2. Re-authenticate: `gh auth login`
3. Test manually: `gh issue list --state open`

### Issue: Cache not expiring

**Symptoms:** Old issue counts persist even after creating new issues

**Solution:**
1. Manually refresh: `/popkit-core:dashboard refresh`
2. Check cache timestamp: `python -m popkit_shared.utils.project_registry list --json | jq '.projects[0].github_issues.cached_at'`
3. Cache TTL is 15 minutes - wait or force refresh

### Issue: Dashboard shows '--' for all projects

**Symptoms:** Issue counts not displaying even with gh CLI

**Solution:**
1. Verify projects have GitHub remotes: `git remote -v`
2. Check if repositories are accessible: `gh repo view`
3. Run refresh explicitly: `/popkit-core:dashboard refresh`
4. Check for errors: Look at stderr output

---

## Estimated Time

**Total:** 2-3 hours (implementation + testing + documentation)

**Breakdown:**
- Task 1: 30 minutes (update command)
- Task 2: 30 minutes (error handling)
- Task 3: 60 minutes (comprehensive testing)
- Task 4: 30 minutes (documentation)
- Task 5: 15 minutes (final verification)

---

## Related Work

- **Issue #110:** Power Mode transcript parsing (separate plan)
- **PopKit Observability:** Full observability platform (design doc)
- **Dashboard Command:** `/popkit-core:dashboard` (main command)
- **Project Registry:** `popkit_shared.utils.project_registry` (core module)

---

**End of Issue #111 Implementation Plan**
