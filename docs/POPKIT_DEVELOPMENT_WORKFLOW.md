# PopKit Development Workflow

**Created:** 2026-01-08
**Purpose:** Document how to use PopKit's own tools when developing PopKit

---

## The Problem

During today's session, I (Claude) made critical mistakes:

1. **Not monitoring CI after pushes** - Assumed workflows passed without checking
2. **Not using PopKit's own commands** - Used vanilla git instead of `/popkit:git`
3. **Not leveraging PopKit agents** - Could have used specialized agents for tasks
4. **Not initializing PopKit** - Never ran `/popkit:next` to activate the system

**Result:** Multiple PR failures that could have been caught immediately if I'd monitored CI like PopKit is designed to do.

---

## The PopKit Way: Correct Workflow

### 1. Session Initialization

**ALWAYS start with:**

```bash
/popkit:next
```

This:

- Analyzes current project state
- Loads context from previous sessions
- Activates Power Mode if available
- Suggests next actions based on project status

### 2. Making Code Changes

**Use PopKit commands, not vanilla tools:**

| Instead of...             | Use PopKit...         | Why                                        |
| ------------------------- | --------------------- | ------------------------------------------ |
| `git add . && git commit` | `/popkit:git commit`  | Validates commits, follows conventions     |
| Manual PR creation        | `/popkit:git pr`      | Generates comprehensive PR descriptions    |
| `git status`              | `/popkit:git status`  | Enhanced context with project intelligence |
| Manual testing            | `/popkit:plugin test` | Validates plugin integrity                 |

### 3. Monitoring CI (CRITICAL)

**After pushing ANY PR:**

```bash
# Check PR status immediately
gh pr checks <PR_NUMBER>

# Wait 30s-1m for workflows to start, then check again
sleep 30 && gh pr checks <PR_NUMBER>

# For detailed failure analysis
gh pr view <PR_NUMBER> --json statusCheckRollup
```

**Set up monitoring loop:**

```bash
# Watch CI status in real-time
watch -n 10 'gh pr checks <PR_NUMBER>'
```

### 4. Using PopKit Agents

PopKit has specialized agents for specific tasks:

**When working on security issues:**

```bash
# Use the security assessment agent
/popkit:security scan
```

**When reviewing code:**

```bash
# Use the code review agent
/popkit:review
```

**When debugging:**

```bash
# Use the systematic debugging skill
/popkit:debug
```

### 5. Power Mode Orchestration

For complex multi-step tasks:

```bash
# Activate Power Mode
/popkit:power enable

# Power Mode will:
# - Spawn multiple specialized agents
# - Coordinate parallel work
# - Monitor all agent progress
# - Report back with consolidated results
```

---

## Today's Lessons Learned

### What Went Wrong

**Scenario:** Fixed security vulnerabilities and pushed PR #33

**What I did (WRONG):**

1. Made changes locally
2. Committed with git directly
3. Pushed to GitHub
4. **Assumed it worked** ❌
5. Moved on to next task

**What happened:**

- CI failed (Greet First-Time Contributors workflow)
- IP Leak Scanner found false positive
- Had to create additional PRs to fix

### What I Should Have Done (RIGHT)

**PopKit-powered workflow:**

1. **Initialize session**

   ```bash
   /popkit:next
   ```

2. **Use PopKit git commands**

   ```bash
   /popkit:git commit "fix: security vulnerabilities"
   /popkit:git pr
   ```

3. **Monitor CI immediately** ✅

   ```bash
   gh pr checks 33
   # See failure immediately: "Greet First-Time Contributors: fail"
   # See IP leak: "Found 1 potential IP leaks"
   ```

4. **Fix issues on same branch**

   ```bash
   # Fix greeting workflow
   # Fix IP scanner
   # Push again
   # Monitor again
   ```

5. **Iterate until green** ✅
   ```bash
   # Keep checking: gh pr checks 33
   # All checks pass ✅
   # Ready to merge
   ```

---

## PopKit Self-Hosting Principles

**PopKit should eat its own dog food:**

1. **Development of PopKit uses PopKit**
   - Use `/popkit:git` for all git operations
   - Use `/popkit:plugin test` for validation
   - Use `/popkit:next` to guide development

2. **CI monitoring is built-in**
   - After any push, immediately check status
   - Don't assume workflows pass
   - Iterate on failures in the same branch

3. **Leverage PopKit intelligence**
   - Use agents for specialized tasks
   - Use Power Mode for complex orchestration
   - Use skills for repeatable workflows

4. **Ask user questions when blocked**
   - Use `AskUserQuestion` tool for clarification
   - Don't make assumptions about intent
   - Confirm breaking changes before proceeding

---

## Implementation Checklist

To make this workflow automatic, PopKit should:

- [ ] Hook into git push to auto-monitor CI
- [ ] Add `/popkit:pr monitor` command
- [ ] Create post-push hook that checks CI status
- [ ] Integrate gh CLI for PR status checking
- [ ] Add Power Mode auto-monitoring feature
- [ ] Create skill: `pop-ci-monitor`
- [ ] Add agent: `ci-monitor` (watches PR status)

---

## Quick Reference

### Essential Commands

```bash
# Start session
/popkit:next

# Git operations
/popkit:git status
/popkit:git commit
/popkit:git pr

# Testing
/popkit:plugin test
/popkit:security scan

# CI monitoring (manual until automated)
gh pr checks <PR_NUMBER>
watch -n 10 'gh pr checks <PR_NUMBER>'
```

### Monitoring Pattern

```bash
# After every push:
1. gh pr checks <PR>          # Immediate check
2. sleep 30                    # Wait for startup
3. gh pr checks <PR>          # Check again
4. If failures → fix → push → repeat
5. All green → ready to merge
```

---

## Future Enhancements

**PopKit CI Integration Epic:**

1. **Auto-monitoring:** Hooks that check CI after push
2. **Proactive alerts:** Notify when CI fails
3. **Smart iteration:** Suggest fixes based on failure type
4. **Power Mode integration:** Spawn agents to fix CI failures
5. **Learning system:** Remember common failure patterns

---

**Bottom Line:**
PopKit is designed to monitor, validate, and guide development.
We should use it when developing PopKit itself.

That's what "eating your own dog food" means.
