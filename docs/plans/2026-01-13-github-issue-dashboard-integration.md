# GitHub Issue Dashboard Integration - Design Document

**Date:** 2026-01-13
**Issue:** #111
**Author:** Joseph Cannon (with Claude)
**Status:** Design Complete - Ready for Implementation

---

## Overview

Integrate GitHub issue counts into the PopKit multi-project dashboard to provide better project health visibility.

### Problem Statement

The dashboard currently displays `'--'` for the Issues column (line 707 of `project_registry.py`). Users managing multiple PopKit-enabled projects cannot see at a glance which projects have open issues requiring attention.

### Success Criteria

1. Dashboard displays actual open issue counts for GitHub projects
2. Non-GitHub projects gracefully show `'--'` placeholder
3. Issue counts are cached to avoid slow dashboard loads
4. Manual refresh available for fetching fresh counts
5. Implementation leverages existing `github_issues.py` utilities

---

## Design Decisions

### 1. Display Format: Simple Open Count

**Chosen:** Display total open issue count as simple number (e.g., `5`, `12`, `0`)

**Rationale:**
- Clean, scannable at a glance
- Fits existing 6-character column width
- Most actionable metric (shows volume of open work)

**Alternatives considered:**
- Open/closed ratio (`5/23`) - too much information
- Priority breakdown (`2H/3M/1L`) - requires label parsing
- Smart status indicator (`!5`, `~3`) - adds complexity

### 2. Error Handling: Show Placeholder

**Chosen:** Display `'--'` for non-GitHub projects or fetch failures

**Rationale:**
- Consistent with current behavior
- Distinguishes "no data" from "zero issues"
- No confusing error messages in dashboard

**Alternatives considered:**
- Show `0` silently - misleading for non-GitHub projects
- Show `N/A` explicitly - clutters display
- Skip column entirely - all-or-nothing approach too rigid

### 3. Performance: Cache with Manual Refresh

**Chosen:** Cache issue counts for 15 minutes, allow manual refresh

**Rationale:**
- Dashboard loads instantly (no network delay)
- User controls when to pay fetch cost
- Graceful degradation without gh CLI

**Alternatives considered:**
- Async loading - complex implementation
- Fetch synchronously - 5-10 second dashboard load time
- On-demand flag - hidden functionality

---

## Architecture

### Components

**1. Cache Management**
- **Storage:** `~/.claude/popkit/projects.json` (existing registry)
- **Format:** Add `github_issues` field to each project
- **TTL:** 15 minutes (fresh), 60 minutes (expired)

**2. Issue Fetching**
- **Method:** `gh issue list --state open --json number`
- **Timeout:** 5 seconds per project
- **Fallback:** Return `None` on any error

**3. Display Integration**
- **Location:** `format_dashboard()` function, line 707
- **Format:** Right-aligned numeric string in 6-char column

### Data Flow

```
User runs /dashboard
  ↓
Load registry (~/.claude/popkit/projects.json)
  ↓
For each project:
  - Check cache freshness
  - If fresh: display cached count
  - If stale: display '--'
  ↓
Display dashboard (instant)

User runs /dashboard refresh
  ↓
For each project:
  - Run: gh issue list --state open --json number
  - Parse JSON, count issues
  - Update cache with count + timestamp
  - Save registry
  ↓
Display "Updated: X projects" summary
```

### Cache Entry Format

```json
{
  "name": "popkit",
  "path": "/path/to/popkit-claude",
  "healthScore": 92,
  "lastActive": "2026-01-13T12:00:00Z",
  "github_issues": {
    "open_count": 5,
    "cached_at": "2026-01-13T12:00:00Z"
  }
}
```

---

## Implementation Plan

### File Changes

**1. packages/shared-py/popkit_shared/utils/project_registry.py**

Add three new functions:
- `get_cached_issue_count(project)` - Retrieve cached count or '--'
- `fetch_project_issues(path, timeout)` - Fetch via gh CLI
- `refresh_project_issue_counts(registry)` - Batch refresh all projects

Modify line 707:
```python
# Before:
issues = "--"  # TODO(#692): Integrate with GitHub issues

# After:
issues = get_cached_issue_count(p).rjust(6)
```

**2. packages/popkit-core/skills/pop-dashboard/SKILL.md**

Add documentation:
- Step 4: Refresh Issue Counts
- Cache behavior explanation
- Performance notes

**3. packages/popkit-core/commands/dashboard.md**

Update `refresh` subcommand:
- Explain issue count refresh
- Document output format
- Note performance characteristics

### Testing Strategy

**Unit Tests:**
- `test_get_cached_issue_count_fresh()` - Verify fresh cache returns count
- `test_get_cached_issue_count_stale()` - Verify stale cache returns '--'
- `test_get_cached_issue_count_missing()` - Verify missing cache returns '--'
- `test_fetch_project_issues_success()` - Mock gh CLI success
- `test_fetch_project_issues_failure()` - Mock gh CLI failure

**Integration Test:**
1. Run `/dashboard` - verify '--' displayed
2. Run `/dashboard refresh` - verify counts fetched
3. Run `/dashboard` - verify cached counts displayed
4. Wait 16 minutes
5. Run `/dashboard` - verify cache expired, shows '--'

---

## Edge Cases

| Scenario | Behavior | Implementation |
|----------|----------|----------------|
| No gh CLI | Show '--' | Catch `FileNotFoundError` |
| Not a git repo | Show '--' | gh CLI error caught silently |
| No GitHub remote | Show '--' | gh CLI error caught silently |
| Network timeout | Show '--', keep stale | 5s timeout, exception caught |
| Rate limit | Keep stale cache | gh CLI error, preserve previous value |
| 0 open issues | Show '0' | Valid count, display as success |
| Cache corrupted | Show '--' | `try/except` on datetime parsing |
| 10+ projects | Sequential fetch, ~20s | User sees progress |

---

## Performance Analysis

### Current Implementation (Sequential)
- **Dashboard load:** Instant (uses cache)
- **Refresh time:** ~0.5s per project with issues
- **Total refresh:** ~5-10s for 10 projects
- **Network:** 1 request per project

### Future Optimizations
- **Parallel fetching:** Thread pool, reduce to ~2-5s
- **Incremental refresh:** Only stale projects
- **Background refresh:** Cron job every 15 minutes
- **Real-time updates:** GitHub webhooks (advanced)

---

## Security & Privacy

**No sensitive data exposed:**
- Only counts are cached, not issue content
- Uses gh CLI (respects user's GitHub auth)
- No API tokens stored in registry
- Falls back gracefully without gh CLI

**Rate limiting:**
- Respects GitHub API rate limits via gh CLI
- 5-second timeout prevents hanging
- Manual refresh gives user control

---

## Migration & Compatibility

### Backward Compatibility
- ✅ Existing registries work unchanged
- ✅ New `github_issues` field is optional
- ✅ No breaking changes to registry format

### Upgrade Path
1. Install updated `project_registry.py`
2. Run `/dashboard refresh` to populate cache
3. Dashboard now shows issue counts

### Rollback Plan
- Remove `github_issues` field from registry
- Revert line 707 to `issues = "--"`
- No data loss or migration needed

---

## Future Enhancements

**Phase 2 - Enhanced Metrics:**
- Priority breakdown in tooltip
- Issue age (stale issue detection)
- Issue velocity (open/close rate)

**Phase 3 - Interactive Features:**
- Click issue count to open issue list
- Filter dashboard by issue status
- Sort by issue count

**Phase 4 - Multi-Platform:**
- GitLab issue support
- JIRA integration
- Custom issue trackers

---

## References

- **Issue #111:** Dashboard: Integrate GitHub issue counts in project dashboard
- **Code:** `packages/shared-py/popkit_shared/utils/project_registry.py:707`
- **Utilities:** `github_issues.py`, `issue_list.py`
- **Command:** `/popkit-core:dashboard`
- **TODO Comment:** Line 707 references issue #692 (should be #111)

---

## Approval Status

**Design Approved:** 2026-01-13
**Ready for Implementation:** Yes
**Estimated Effort:** 2-3 hours
**Complexity:** Low (leverages existing utilities)
