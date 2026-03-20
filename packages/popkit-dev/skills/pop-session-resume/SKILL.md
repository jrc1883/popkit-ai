---
name: session-resume
description: "Use at start of new session to restore context from STATUS.json - loads previous state, displays session type, shows what to continue working on. Calculates session type (Continuation/Resume/Fresh Start) based on time gap. Do NOT use mid-session or when starting fresh work unrelated to previous session - just begin the new task directly."
---

# Session Resume

## Overview

Restore context from STATUS.json when starting a new Claude Code session.

**Core principle:** Start where you left off, not from scratch.

**Trigger:** Beginning of new conversation (via session-start hook or manual)

## Session Types

Based on time since last update:

| Time Gap         | Session Type | Behavior                           |
| ---------------- | ------------ | ---------------------------------- |
| < 30 min         | Continuation | Quick restore, assume full context |
| 30 min - 4 hours | Resume       | Restore context, brief refresh     |
| > 4 hours        | Fresh Start  | Full context load, verify state    |

## Resume Process

### Step 1: Load STATUS.json

```bash
# Check for STATUS.json
if [ -f ".claude/STATUS.json" ]; then
  cat .claude/STATUS.json
elif [ -f "STATUS.json" ]; then
  cat STATUS.json
fi
```

### Step 2: Calculate Session Type

```javascript
const lastUpdate = new Date(status.lastUpdate);
const now = new Date();
const hoursSince = (now - lastUpdate) / (1000 * 60 * 60);

if (hoursSince < 0.5) return "Continuation";
if (hoursSince < 4) return "Resume";
return "Fresh Start";
```

### Step 3: Display Session Summary

**Continuation (< 30 min):**

```
⚡ Continuation Session
Last: 15 minutes ago

Quick context:
- Branch: feature/auth
- Session branch: main
- Focus: Password reset flow
- Next: Add email template

Ready to continue.
```

**Resume (30 min - 4 hours):**

```
🔄 Resume Session
Last: 2 hours ago

Context restore:
- Branch: feature/auth (2 uncommitted files)
- Session branch: auth-bug (investigating token expiry)
- Last commit: feat: add login form
- In Progress: Implement password reset flow
- Focus: Authentication system
- Next: Add forgot password email template

Key decisions from last session:
- Using nodemailer for emails
- Password reset expires in 1 hour

Shall I continue with the next action?
```

**Fresh Start (> 4 hours):**

```
🌅 Fresh Start Session
Last activity: Yesterday at 2:30 PM

Full context load:
- Branch: feature/auth (2 uncommitted files)
- Session branch: main
- Last commit: feat: add login form
- Test status: 45 passing
- Build status: passing

Session branches (2 unmerged):
- auth-bug: Token expiry investigation (1 day old)
- cache-research: Redis vs Memcached spike (4 days old, STALE)

Tasks in progress:
- [ ] Implement password reset flow

Last focus: Authentication system
Last blocker: None

Recommended: Review STATUS.json and verify current state before continuing.
```

### Step 4: Verify Current State (Fresh Start only)

For fresh starts, verify the saved state is still accurate:

```bash
# Verify branch
git branch --show-current

# Verify uncommitted count
git status --porcelain | wc -l

# Run tests
npm test

# Check services
curl -s http://localhost:3000/health
```

Report discrepancies if any.

### Step 4b: Restore Session Branch Context

Check STATUS.json for session branch state and restore it:

```python
# Check for session branch context
branches = status.get("branches", {})
current_branch = status.get("currentBranch", "main")

if current_branch != "main":
    branch_data = branches.get(current_branch, {})
    print(f"Last session branch: {current_branch}")
    print(f"Reason: {branch_data.get('reason', 'unknown')}")
    print(f"Parent: {branch_data.get('parent', 'main')}")

# List unmerged branches
unmerged = [b for b in branches.values()
            if b.get("id") != "main" and not b.get("merged", False)]
if unmerged:
    print(f"\nUnmerged session branches: {len(unmerged)}")
    for b in unmerged:
        print(f"  - {b['id']}: {b.get('reason', '')}")
```

**Behavior by session type:**

- **Continuation**: Silently restore to last active session branch
- **Resume**: Show which session branch was active, offer to switch back
- **Fresh Start**: List all unmerged branches, recommend cleanup of stale ones

### Step 5: Offer to Continue

After displaying context:

```
Ready to continue. Options:

1. Continue with: [nextAction from STATUS.json]
2. Switch to session branch: auth-bug (investigating token expiry)
3. Review full context first
4. Start fresh (ignore previous session)

What would you like to do?
```

## Output Format

```
┌─────────────────────────────────────────────┐
│ 🔄 Resume Session                           │
│ Last: 2 hours ago                           │
├─────────────────────────────────────────────┤
│ Branch: feature/auth                        │
│ Session branch: auth-bug                    │
│ Uncommitted: 2 files                        │
│ Tests: 45 passing                           │
├─────────────────────────────────────────────┤
│ Session Branches (2 unmerged):              │
│ • auth-bug: Token expiry (active)           │
│ • cache-research: Redis spike (4d, stale)   │
├─────────────────────────────────────────────┤
│ In Progress:                                │
│ • Implement password reset flow             │
├─────────────────────────────────────────────┤
│ Next Action:                                │
│ Add forgot password email template          │
└─────────────────────────────────────────────┘
```

## Integration

**Pairs with:**

- **session-capture** - Creates STATUS.json that this reads
- **session-branch** - Session branching for side investigations (branch context stored in STATUS.json)
- **context-restore** - More detailed context loading

**Session branch integration:**

- Reads `branches` and `currentBranch` from STATUS.json
- Restores session branch context on resume
- Shows unmerged branches for awareness
- Offers to switch back to last active session branch

**Hook integration:**

- Triggered by session-start hook
- Runs automatically when Claude Code starts
