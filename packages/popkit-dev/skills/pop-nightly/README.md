# Pop-Nightly Skill

Automated end-of-day maintenance routine for PopKit.

## Overview

The `pop-nightly` skill provides a comprehensive nightly routine that:
- Calculates Sleep Score (0-100) based on project health
- Generates actionable nightly report
- Automatically captures session state to STATUS.json
- Provides recommendations before leaving

## Sleep Score (0-100)

| Check | Points | Description |
|-------|--------|-------------|
| Uncommitted work saved | 25 | No uncommitted changes OR committed |
| Branches cleaned | 20 | No stale merged branches |
| Issues updated | 20 | Today's issues have status updates |
| CI passing | 15 | Latest CI run successful |
| Services stopped | 10 | No dev services running |
| Logs archived | 10 | Session logs saved |

**Total**: 100 points

## Usage

### Via Command

```bash
/popkit:routine nightly              # Full nightly routine
/popkit:routine nightly quick        # One-line summary
/popkit:routine nightly --measure    # Track performance metrics
/popkit:routine nightly --optimized  # Use caching
```

### Standalone (Development)

```bash
cd packages/popkit-dev/skills/pop-nightly
python scripts/nightly_workflow.py
python scripts/nightly_workflow.py --quick
python scripts/nightly_workflow.py --measure
```

## Files

```
pop-nightly/
├── SKILL.md                    # Skill definition and documentation
├── README.md                   # This file
├── scripts/
│   ├── nightly_workflow.py    # Main orchestration
│   ├── sleep_score.py         # Score calculation logic
│   └── report_generator.py    # Report formatting
├── workflows/
│   └── nightly-workflow.json  # Workflow steps definition
└── tests/
    └── test_sleep_score.py    # Unit tests
```

## Integration

### Utilities Used

- **capture_state.py**: Git/GitHub/service data collection
- **routine_measurement.py**: Performance tracking
- **routine_cache.py**: Caching for efficiency
- **session_recorder.py**: Recording support

### Skills Invoked

- **pop-session-capture**: Automatic STATUS.json updates

## Development

### Run Tests

```bash
cd packages/popkit-dev/skills/pop-nightly
python -m unittest tests/test_sleep_score.py
```

### Test Sleep Score Calculation

```bash
python scripts/sleep_score.py
# → Runs with sample data and shows output
```

### Test Report Generation

```bash
python scripts/report_generator.py
# → Generates sample report
```

## Performance

### Baseline (Manual)
- Tool calls: 11
- Duration: ~60 seconds
- Token usage: High (no caching)

### Optimized (Automated)
- Tool calls: 4 (64% reduction)
- Duration: ~10-15 seconds (75-83% improvement)
- Token usage: 40-96% reduction (with --optimized)

## Example Output

```markdown
# 🌙 Nightly Routine Report

**Date**: 2025-12-28
**Sleep Score**: 60/100 ⚠️

**Grade**: C - Fair - some uncommitted work or issues

## Score Breakdown

| Check | Points | Status |
|-------|--------|--------|
| Uncommitted work saved | 0/25 | ❌ 3 uncommitted files |
| Branches cleaned | 20/20 | ✅ No stale branches |
| Issues updated | 20/20 | ✅ All issues current |
| CI passing | 0/15 | ❌ Latest run skipped |
| Services stopped | 10/10 | ✅ All services stopped |
| Logs archived | 10/10 | ✅ No logs to archive |

## 📝 Uncommitted Changes

**3 files need attention:**

- `apps/popkit/packages/websitebuild-popkit-test-beta.txt` (deleted)
- `pnpm-lock.yaml` (modified)
- `.npmrc` (untracked)

## 📋 Recommendations

**Before Leaving:**
- Commit or stash 3 uncommitted files
- Review 8 stashes - consider cleaning up old ones

**Next Morning:**
- Run `/popkit:routine morning` to check overnight changes
- Review and address items from nightly report

---

STATUS.json updated ✅
Session state captured for tomorrow's resume.
```

## Version History

- **1.0.0** (2025-12-28): Initial implementation
  - Sleep Score calculation
  - Nightly report generation
  - STATUS.json integration
  - Recording-driven development methodology

## Related

- **pop-morning**: Morning counterpart with Ready to Code score
- **pop-session-capture**: Session state management
- **pop-routine-optimized**: Optimized execution with caching
