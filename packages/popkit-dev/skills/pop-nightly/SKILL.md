---
name: nightly
description: "End-of-day cleanup and maintenance routine. Calculates Sleep Score (0-100) based on uncommitted work, branch cleanup, issue updates, CI status, and service shutdown. Automatically captures session state to STATUS.json. Use at end of work day before closing Claude Code."
---

# Nightly Routine

## Overview

Automated end-of-day maintenance that ensures clean project state before leaving for the day.

**Core principle:** Leave the codebase in a clean, resumable state with zero manual overhead.

**Trigger:** End of work day, before closing Claude Code

**Duration:** ~10-15 seconds (vs. ~60 seconds manual)

## Sleep Score (0-100)

See [examples/scoring-system.md](examples/scoring-system.md) for complete scoring documentation.

Comprehensive health check across 6 dimensions:

| Check | Points | Criteria |
|-------|--------|----------|
| Uncommitted work saved | 25 | No uncommitted changes OR committed |
| Branches cleaned | 20 | No stale merged branches |
| Issues updated | 20 | Today's issues have status updates |
| CI passing | 15 | Latest CI run successful |
| Services stopped | 10 | No dev services running |
| Logs archived | 10 | Session logs saved |

**Branch Protection Impact (Issue #142):**
- **Warning:** ⚠️ PROTECTED indicator if on protected branch with uncommitted work
- **Recommendation:** Create feature branch before committing

**Score Interpretation:**
- **90-100**: Perfect shutdown - ready for tomorrow
- **70-89**: Good - minor cleanup needed
- **50-69**: Fair - some uncommitted work or failed CI
- **0-49**: Poor - significant cleanup required

## Workflow

**Five-step process:**

1. **Collect Project State** - Using `capture_state.py` (git, GitHub, services)
2. **Calculate Sleep Score** - Using `sleep_score.py` module
3. **Generate Nightly Report** - Using `report_generator.py` module
4. **Capture Session State** - Update STATUS.json via `pop-session-capture`
5. **Present Report to User** - Display score, breakdown, and recommendations

## Data Collection

**Consolidated commands:**
- **Git**: Branch, last commit, status, stashes, merged branches
- **GitHub**: Open issues (last 5), latest CI run
- **Services**: Running processes, session logs

All wrapped in `capture_state.py` for consistent error handling.

## Integration

**Key utilities:**
- `capture_state.py` - Complete project state capture
- `routine_measurement.py` - Performance tracking (when using `--measure`)
- `routine_cache.py` - GitHub data caching (when using `--optimized`)

**Performance:**
- **Tool call reduction**: 64% (11 → 4 calls)
- **Execution time**: 75-83% faster (60s → 10-15s)
- **Token reduction**: 40-96% (with `--optimized`)

## Output Format

**Report includes:**
- Sleep Score (0-100) with visual indicator
- Score breakdown table
- Uncommitted changes list (if any)
- Recommendations before leaving
- Encouraging Bible verse (Issue #71)
- Next morning actions

## Next Actions (The PopKit Way)

**CRITICAL**: Always end with AskUserQuestion to keep PopKit in control.

**Context-aware options based on score:**
- **Score < 70**: Commit and push (Recommended), stash changes, or review files
- **Score >= 70**: Review tomorrow's priorities, check CI, or end session
- **Services running**: Stop all services (Recommended) or leave running
- **CI failing**: Investigate now, note for morning, or check logs

Never just show a report and end the session!

## Error Handling

**Graceful degradation:**
- Git not available → Skip git checks, continue with partial score
- GitHub CLI not available → Skip GitHub checks, continue with partial score
- Service check failures → Assume services stopped (safe default)

**Never block** - provide best possible score with available data.

## Usage Examples

```bash
# Basic usage
/popkit:routine nightly

# With measurement
/popkit:routine nightly --measure

# Quick summary
/popkit:routine nightly quick

# With optimization (caching)
/popkit:routine nightly --optimized
```

## Related Skills

- **pop-session-capture**: Updates STATUS.json (invoked automatically)
- **pop-morning**: Morning counterpart with Ready to Code score
- **pop-routine-optimized**: Optimized execution with caching

## Related Commands

- **/popkit:routine nightly**: Main entry point
- **/popkit:routine morning**: Morning routine
- **/popkit:next**: Context-aware next action recommendations

## Success Criteria

✅ Sleep Score accurately reflects project state
✅ STATUS.json always updated correctly
✅ Completes in <20 seconds
✅ Provides actionable recommendations
✅ Reduces manual workflow by 64%

---

**Skill Type**: Automated Routine
**Category**: Workflow Automation
**Tier**: Core (Always Available)
**Version**: 1.0.0
