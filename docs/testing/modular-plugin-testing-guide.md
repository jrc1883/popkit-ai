# Modular Plugin Testing Guide

**Version:** 1.0
**Date:** 2025-12-21
**Issue:** #588 (Phase 5 Testing & Validation)

## Overview

This guide provides step-by-step instructions for testing the 4 modular PopKit plugins before v1.0.0 release.

## Pre-Testing Setup

### 1. Close Any Running Claude Code Instances

Close all Claude Code windows to start fresh.

### 2. Navigate to PopKit Directory

```bash
cd C:\Users\Josep\onedrive\documents\elshaddai\apps\popkit
```

### 3. Prepare Testing Checklist

Create a testing checklist file to track results:

```bash
# Create testing results file
touch docs/testing/test-results-YYYY-MM-DD.md
```

## Testing Phase 1: Local Plugin Loading

### Using --plugin-dir Flag

**IMPORTANT:** Local plugins are loaded using the `--plugin-dir` command-line flag, NOT via `/plugin install`.

**Test 1.1: Load All Plugins**

Start Claude Code with all 5 modular plugins loaded:

```bash
# From the popkit root directory
claude --plugin-dir ./packages/popkit --plugin-dir ./packages/popkit-dev --plugin-dir ./packages/popkit-ops --plugin-dir ./packages/popkit-research --plugin-dir ./packages/popkit-suite
```

**Expected:**
- Claude Code starts successfully
- No plugin loading errors in console

**Verify:**
```bash
# In Claude Code, check available commands
/help

# Should see all popkit: commands listed
```

**Test Commands:**
```bash
/popkit:account status
/popkit:stats session
/popkit:privacy status
```

**Expected:** Commands execute without crashes.

**Alternative: Load Individual Plugins**

If you need to test plugins individually:

```bash
# Load just popkit foundation
claude --plugin-dir ./packages/popkit

# Load popkit + popkit-dev
claude --plugin-dir ./packages/popkit --plugin-dir ./packages/popkit-dev

# etc.
```

**Test 1.2: Verify All Commands Available**

After loading all plugins, verify commands from each plugin:

```bash
# Foundation (popkit)
/popkit:account status
/popkit:stats session
/popkit:privacy status

# Development (popkit-dev)
/popkit:dev brainstorm
/popkit:git commit
/popkit:routine morning

# Operations (popkit-ops)
/popkit:assess anthropic
/popkit:security scan
/popkit:debug code

# Research (popkit-research)
/popkit:research list
/popkit:knowledge list
```

**Expected:** All 21 commands execute without crashes.

---

## Testing Phase 2: Command Functionality

### popkit (Foundation) - 7 Commands

| Command | Test | Expected Result | Status |
|---------|------|-----------------|--------|
| `/popkit:account status` | Run command | Shows account info or "No API key" | ☐ |
| `/popkit:stats session` | Run command | Displays session metrics | ☐ |
| `/popkit:privacy status` | Run command | Shows privacy settings | ☐ |
| `/popkit:bug report` | Run command | Starts bug reporting workflow | ☐ |
| `/popkit:plugin test` | Run command | Validates plugin structure | ☐ |
| `/popkit:cache status` | Run command | Shows cache info (may be placeholder) | ☐ |
| `/popkit:upgrade` | Run command | Shows premium features or signup | ☐ |

### popkit-dev (Development) - 7 Commands

| Command | Test | Expected Result | Status |
|---------|------|-----------------|--------|
| `/popkit:dev brainstorm` | Run with topic | Starts interactive questioning | ☐ |
| `/popkit:git commit` | Run in git repo | Generates commit message | ☐ |
| `/popkit:issue list` | Run command | Lists GitHub issues | ☐ |
| `/popkit:milestone list` | Run command | Lists milestones | ☐ |
| `/popkit:worktree list` | Run command | Lists worktrees | ☐ |
| `/popkit:routine morning` | Run command | Health check report | ☐ |
| `/popkit:next` | Run command | Context-aware recommendations | ☐ |

### popkit-ops (Operations) - 5 Commands

| Command | Test | Expected Result | Status |
|---------|------|-----------------|--------|
| `/popkit:assess anthropic` | Run command | Code quality assessment | ☐ |
| `/popkit:audit quarterly` | Run command | Health audit report | ☐ |
| `/popkit:debug code` | Run command | Debugging workflow | ☐ |
| `/popkit:security scan` | Run command | Security scanning | ☐ |
| `/popkit:deploy init` | Run command | Deployment setup | ☐ |

### popkit-research (Knowledge) - 2 Commands

| Command | Test | Expected Result | Status |
|---------|------|-----------------|--------|
| `/popkit:research list` | Run command | Lists research items | ☐ |
| `/popkit:knowledge list` | Run command | Lists knowledge entries | ☐ |

---

## Testing Phase 3: Skill Execution

Test that skills are globally available and executable:

### Test 3.1: Invoke Skills from popkit-dev

```
Use the Skill tool with skill="popkit:pop-brainstorming"
```

**Expected:** Skill executes, starts interactive questioning.

### Test 3.2: Invoke Skills from popkit-ops

```
Use the Skill tool with skill="popkit:pop-assessment-security"
```

**Expected:** Security assessment runs.

### Test 3.3: Cross-Plugin Skill Access

Install only popkit-dev and popkit-ops, then verify:

```
Use the Skill tool with skill="popkit:pop-systematic-debugging"
```

**Expected:** Skill from popkit-ops works even when invoked in popkit-dev context.

---

## Testing Phase 4: Agent Routing

### Test 4.1: Tier 1 Agent Activation

Create scenarios that should trigger agents:

**code-reviewer (popkit-dev):**
```
"Please review the code I just wrote in auth.ts"
```
**Expected:** code-reviewer agent activates.

**security-auditor (popkit-ops):**
```
"Scan this code for security vulnerabilities"
```
**Expected:** security-auditor agent activates.

**bug-whisperer (popkit-ops):**
```
"I have a weird bug that only happens sometimes"
```
**Expected:** bug-whisperer agent activates.

### Test 4.2: Tier 2 Agent Activation

**researcher (popkit-research):**
```
Use the Task tool with subagent_type="researcher"
```
**Expected:** Researcher agent launches for project analysis.

---

## Testing Phase 5: Performance Measurement

### Test 5.1: Context Window Impact

**Baseline Measurement:**
```bash
# Before any plugins installed
# Note the baseline token count from Claude Code
```

**After Each Plugin:**
```bash
# After popkit: Note token increase
# After popkit-dev: Note token increase
# After popkit-ops: Note token increase
# After popkit-research: Note token increase
```

**Calculate:**
- Total increase vs baseline
- Percentage increase
- Compare to monolithic version (if data available)

**Target:** < 25% increase vs monolithic version

### Test 5.2: Installation Time

Measure installation time for each plugin:

| Plugin | Installation Time | Target | Status |
|--------|-------------------|--------|--------|
| popkit | ___ seconds | < 30s | ☐ |
| popkit-dev | ___ seconds | < 60s | ☐ |
| popkit-ops | ___ seconds | < 60s | ☐ |
| popkit-research | ___ seconds | < 30s | ☐ |
| popkit-suite | ___ seconds | < 5s | ☐ |

---

## Testing Phase 6: Integration Testing

### Test 6.1: Cross-Plugin Skill Sharing

**Step 1:** Install popkit-dev only
```bash
/plugin list
# Count available skills - should be 10 from popkit-dev
```

**Step 2:** Install popkit-ops
```bash
/plugin list
# Count available skills - should now be 16 total (10 + 6)
```

**Step 3:** Verify skills work across plugins
```
# From popkit-dev context, use a skill from popkit-ops
Use the Skill tool with skill="popkit:pop-assessment-security"
```

**Expected:** Skill executes successfully.

### Test 6.2: Bundled Utilities

**Verify no import conflicts:**
- Each plugin has 70 bundled utility files
- No errors when plugins load simultaneously
- Python utilities execute correctly

**Check:**
```bash
# In each plugin directory
ls packages/popkit/hooks/utils/ | wc -l     # Should be 70
ls packages/popkit-ops/hooks/utils/ | wc -l # Should be 70
ls packages/popkit-research/hooks/utils/ | wc -l # Should be 70
```

---

## Testing Phase 7: Documentation Validation

### Test 7.1: README Accuracy

For each plugin, verify README matches actual functionality:

**popkit:**
- [ ] Lists 7 commands correctly
- [ ] Installation instructions work
- [ ] Examples execute successfully

**popkit-dev:**
- [ ] Lists 7 commands correctly
- [ ] Lists 10 skills correctly
- [ ] Lists 5 agents correctly
- [ ] Examples execute successfully

**popkit-ops:**
- [ ] Lists 5 commands correctly
- [ ] Lists 6 skills correctly
- [ ] Lists 6 agents correctly

**popkit-research:**
- [ ] Lists 2 commands correctly
- [ ] Lists 3 skills correctly
- [ ] Lists 1 agent correctly

**popkit-suite:**
- [ ] Installation guide accurate
- [ ] Plugin descriptions match reality
- [ ] Total counts correct (21 commands, 19 skills, 13 agents)

### Test 7.2: CHANGELOG Completeness

- [ ] All 5 plugins have CHANGELOG.md
- [ ] Version numbers consistent (1.0.0-beta.1)
- [ ] Issue references correct (#584, #585, #586, #587)

---

## Testing Phase 8: Migration Path

### Test 8.1: Fresh Installation (New Users)

**Scenario:** New user following popkit-suite README

**Steps:**
1. Follow "Quick Install" instructions from popkit-suite README
2. Install all 4 plugins in order
3. Restart Claude Code
4. Verify all 21 commands available
5. Test sample commands from each plugin

**Success Criteria:**
- All installations complete successfully
- All 21 commands work
- No confusion or blockers

### Test 8.2: Migration from Monolithic (Existing Users)

**Scenario:** User upgrading from v0.2.x monolithic

**Steps:**
1. Document current monolithic installation state
2. Uninstall monolithic popkit
3. Install 4 new plugins following migration guide
4. Restart Claude Code
5. Verify all functionality preserved

**Success Criteria:**
- Migration guide is clear
- No functionality loss
- Same or better performance

---

## Quality Gates

### P0 (Must Pass)

- [ ] All 21 commands execute without crashes
- [ ] Skills invocable from any plugin
- [ ] Agents route correctly
- [ ] Installation completes successfully (all 5 plugins)
- [ ] No security vulnerabilities detected
- [ ] No data loss potential identified

### P1 (Should Pass)

- [ ] Documentation 100% accurate
- [ ] Context window increase < 25% vs monolithic
- [ ] Installation time < 60s per plugin
- [ ] Migration path tested and clear

---

## Success Metrics

Fill in after testing:

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Installation Success Rate | 100% (5/5) | ___ | ☐ |
| Command Success Rate | > 95% (20/21) | ___ | ☐ |
| Skill Success Rate | > 90% (17/19) | ___ | ☐ |
| Agent Routing Accuracy | > 90% | ___ | ☐ |
| Context Window Increase | < 25% | ___% | ☐ |

---

## Issue Tracking

### Bugs Discovered

Document any bugs found during testing:

| Bug | Severity | Plugin | Description | Issue # |
|-----|----------|--------|-------------|---------|
| | | | | |

### Improvements Needed

Document non-blocking improvements:

| Improvement | Plugin | Description | Issue # |
|-------------|--------|-------------|---------|
| | | | |

---

## Test Results Summary

**Date Tested:** ___________
**Tester:** ___________
**Environment:** Claude Code version _____

### Overall Results

- **P0 Gates:** ☐ All Passed / ☐ Some Failed
- **P1 Gates:** ☐ All Passed / ☐ Some Failed
- **Ready for v1.0.0:** ☐ Yes / ☐ No (blockers: ___)

### Recommendations

- [ ] Proceed to Phase 6 (Documentation & Release)
- [ ] Fix blocking issues first
- [ ] Conduct additional testing

---

## Next Steps

After completing this testing guide:

1. **Document all results** in test-results-YYYY-MM-DD.md
2. **File issues** for any bugs discovered
3. **Update Issue #588** with test completion status
4. **If P0 gates pass:** Proceed to Issue #579 (Documentation & Release)
5. **If P0 gates fail:** Fix blockers and re-test

---

**Related Issues:**
- #588 - Phase 5 Testing & Validation
- #580 - Plugin Modularization Epic (COMPLETED)
- #579 - Documentation and Marketplace Release (next phase)
