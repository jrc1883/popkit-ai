---
title: Morning/Nightly Routines
description: Day-bracketing workflows with health checks
---

# Morning/Nightly Routines

PopKit provides day-bracketing workflows that check project health at the start and end of each day.

## Morning Routine

**Command**: `/popkit-dev:routine morning`

**What it does**:

1. **Project Health Check**
   - Git status and unpushed commits
   - Dependency updates available
   - Test failures
   - Security vulnerabilities

2. **Context Restoration**
   - Restore previous session state
   - Load work-in-progress branches
   - Review open PRs

3. **Daily Planning**
   - Show open issues
   - Suggest priority tasks
   - Review milestones

4. **Ready to Code Score**
   - 0-100 score based on health
   - Green (90+): All systems go
   - Yellow (70-89): Minor issues
   - Red (<70): Critical issues

**Output**:
```
☀️ Morning Routine Report

Ready to Code Score: 92/100 ✅

✅ Git Status: Clean working tree
✅ Dependencies: Up to date
✅ Tests: All passing
⚠️  Security: 2 low-severity vulnerabilities

📋 Today's Priorities:
1. Complete PR #123 (Code review feedback)
2. Work on Issue #456 (User authentication)
3. Update documentation for v2.0

🎯 Next Steps:
- Fix security vulnerabilities (low priority)
- Continue work on feat/auth branch
- Review open PRs
```

## Nightly Routine

**Command**: `/popkit-dev:routine nightly`

**What it does**:

1. **Work Summary**
   - List commits made today
   - Show files modified
   - Count lines added/removed

2. **State Capture**
   - Save current work state
   - Capture open files
   - Store session context

3. **Cleanup Tasks**
   - Stash uncommitted changes
   - Delete merged branches
   - Clear temporary files

4. **Sleep Score**
   - 0-100 score based on cleanup
   - Green (90+): Ready to rest
   - Yellow (70-89): Minor cleanup needed
   - Red (<70): Incomplete work

**Output**:
```
🌙 Nightly Routine Report

Sleep Score: 88/100 ✅

📊 Today's Activity:
- 5 commits created
- 12 files modified
- +324 lines added, -87 lines removed

✅ State captured for tomorrow
✅ Branches cleaned up
⚠️  Uncommitted changes stashed

💤 Tomorrow's Context:
- Resume work on feat/auth branch
- Review PR feedback on #123
- Continue with Issue #456

🎯 Recommended Actions:
- Push feat/auth branch (recommended)
- Other
```

## Quick Mode

For faster execution, use quick mode:

```bash
# Morning quick check
/popkit-dev:routine morning quick

# Nightly quick summary
/popkit-dev:routine nightly quick
```

Quick mode skips detailed analysis and provides summary only.

## Custom Routines

Create custom routines for your workflow:

### 1. Generate Template

```bash
/popkit-dev:routine generate lunch-break
```

### 2. Edit Template

Edit `.popkit/routines/lunch-break.json`

### 3. Run Custom Routine

```bash
/popkit-dev:routine lunch-break
```

## Routine Configuration

Configure routine behavior in `.popkit/config.json`:

```json
{
  "routines": {
    "morning": {
      "enabled": true,
      "autoRun": false,
      "checks": ["git", "dependencies", "tests", "security"]
    },
    "nightly": {
      "enabled": true,
      "autoRun": false,
      "cleanup": ["branches", "temp-files", "stash"]
    }
  }
}
```

## Best Practices

1. **Run Morning Routine First**: Start each day with health check
2. **Run Nightly Routine Last**: End each day with cleanup
3. **Address Red Scores**: Fix critical issues before coding
4. **Review Priorities**: Use morning routine for planning
5. **Commit Before Nightly**: Ensure work is saved

## Troubleshooting

### Morning Routine Shows Red Score

**Symptom**: Low Ready to Code score

**Solutions**:
- Fix test failures
- Update dependencies
- Address security issues
- Clean git state

### Nightly Routine Shows Red Score

**Symptom**: Low Sleep score

**Solutions**:
- Commit or stash changes
- Push completed work
- Close or save work-in-progress
- Clean up temporary files

### Context Not Restored

**Symptom**: Morning routine doesn't restore previous work

**Solution**:
- Ensure nightly routine ran successfully
- Check `.popkit/state/` directory exists
- Manually run: `/popkit-core:project restore`

## Next Steps

- Learn about [Power Mode](/features/power-mode/)
- Explore [Feature Development](/features/feature-dev/)
- Review [Git Workflows](/features/git-workflows/)
