---
name: morning
description: "Start-of-day setup and readiness routine. Calculates Ready to Code Score (0-100) based on session restoration, service health, dependency updates, branch sync, PR reviews, and issue triage. Automatically captures session state to STATUS.json. Use at start of work day after opening Claude Code."
---

# Morning Routine

## Overview

Automated start-of-day setup that ensures optimal development environment before starting work.

**Core principle:** Validate readiness to code and restore previous session context with zero manual overhead.

**Trigger:** Start of work day, after opening Claude Code

**Duration:** ~15-20 seconds (vs. ~90 seconds manual)

## Ready to Code Score (0-100)

See [examples/scoring-system.md](examples/scoring-system.md) for complete scoring documentation.

Comprehensive readiness check across 6 dimensions:

| Check | Points | Criteria |
|-------|--------|----------|
| Session Restored | 20 | Previous session context restored from STATUS.json |
| Services Healthy | 20 | All required dev services running |
| Dependencies Updated | 15 | Package dependencies up to date |
| Branches Synced | 15 | Local branch synced with remote |
| PRs Reviewed | 15 | No PRs waiting for review |
| Issues Triaged | 15 | All issues assigned/prioritized |

**Branch Protection Penalty (Issue #142):**
- **Penalty:** -10 points if on protected branch (`main`, `master`, `develop`, `production`) with uncommitted changes
- **Indicator:** Shows ⚠️ PROTECTED warning

**Score Interpretation:**
- **90-100**: Excellent - Fully ready to code
- **80-89**: Very Good - Almost ready, minor setup
- **70-79**: Good - Ready with minor issues
- **60-69**: Fair - 10-15 minutes setup needed
- **50-59**: Poor - Significant setup required
- **0-49**: Not Ready - Focus on environment setup

## Workflow

See [examples/workflow-implementation.md](examples/workflow-implementation.md) for complete implementation details.

**Six-step process:**

1. **Restore Previous Session** - Load context from STATUS.json (last nightly score, work summary, branch, stashes)
2. **Check Dev Environment** - Using `capture_state.py` utility (git, GitHub, services, dependencies)
3. **Calculate Ready to Code Score** - Using `ready_to_code_score.py` module
4. **Generate Morning Report** - Using `morning_report_generator.py` module
5. **Capture Session State** - Update STATUS.json with morning routine data
6. **Present Report to User** - Display score, breakdown, issues, and recommendations

## Data Collection

See [examples/data-collection.md](examples/data-collection.md) for consolidated bash commands.

**Consolidated commands:**
- **Git**: Single command for branch, commits behind, status, stashes (with `git fetch`)
- **GitHub**: PRs and issues in one call using `gh` CLI
- **Services**: Process check and dependency updates in one pass

All wrapped in `capture_state.py` for consistent error handling.

## Integration

See [examples/integration.md](examples/integration.md) for integration with shared utilities.

**Key utilities:**
- `capture_state.py` - Complete project state capture
- `routine_measurement.py` - Performance tracking (when using `--measure`)
- `routine_cache.py` - GitHub/service data caching (when using `--optimized`)

**Performance:**
- **Tool call reduction**: ~67% (15 → 5 calls)
- **Execution time**: 78-83% faster (90s → 15-20s)
- **Token reduction**: 40-96% (with `--optimized`)

## Output Format

See [examples/output-format.md](examples/output-format.md) for complete report examples.

**Report includes:**
- Ready to Code Score (0-100) with visual indicator and grade
- Score breakdown table (what contributed to score)
- Dev services status (if not all running)
- Branch sync status (if behind remote)
- Recommendations (actions before coding)
- Today's focus (PRs, issues, continuations)

## Next Actions (The PopKit Way)

See [examples/next-actions.md](examples/next-actions.md) for complete implementation.

**CRITICAL**: Always end with AskUserQuestion to keep PopKit in control.

**Context-aware options based on score:**
- **Score < 80**: Fix environment issues (Recommended)
- **Score >= 80**: Work on highest priority, review PRs, or continue yesterday's work
- **Issues need triage**: Triage now (Recommended) or skip

Never just show a report and end the session!

## Error Handling

See [examples/error-handling.md](examples/error-handling.md) for complete error handling strategy.

**Graceful degradation:**
- Git not available → Skip git checks, continue with partial score
- GitHub CLI not available → Skip GitHub checks, continue with partial score
- Service check failures → Best-effort, don't block
- Session restore failures → Start fresh session

**Never block** - provide best possible score with available data.

## Usage Examples

See [examples/usage.md](examples/usage.md) for all usage scenarios.

```bash
# Basic usage
/popkit:routine morning

# With measurement
/popkit:routine morning --measure

# Quick summary
/popkit:routine morning quick

# With optimization (caching)
/popkit:routine morning --optimized
```

## Related Skills

- **pop-session-resume**: Restores session context (invoked automatically)
- **pop-nightly**: Evening counterpart with Sleep Score
- **pop-routine-optimized**: Optimized execution with caching

## Related Commands

- **/popkit:routine morning**: Main entry point
- **/popkit:routine nightly**: Nightly routine
- **/popkit:next**: Context-aware next action recommendations

## Success Criteria

✅ Ready to Code Score accurately reflects environment state
✅ STATUS.json always updated correctly
✅ Completes in <25 seconds
✅ Provides actionable recommendations
✅ Session context successfully restored
✅ Reduces manual workflow by 67%

---

**Skill Type**: Automated Routine
**Category**: Workflow Automation
**Tier**: Core (Always Available)
**Version**: 1.0.0
