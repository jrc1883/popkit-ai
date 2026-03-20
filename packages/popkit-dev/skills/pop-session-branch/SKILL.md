---
name: session-branch
description: "Create, switch, and merge session branches for side investigations. Branch off to explore bugs, research APIs, or debug issues without polluting main context. Use when you need to temporarily focus on something different, then return to your main work."
---

# Session Branch

## Overview

Branch off from your main session to investigate something without polluting the main context. Inspired by Pi's DAG-based session architecture.

**Trigger:** When you need to temporarily investigate something unrelated to your main task

## Commands

### Create Branch

```bash
# Create a new branch for investigation
python "${CLAUDE_PLUGIN_ROOT}/skills/pop-session-branch/scripts/branch_operations.py" \
  create "branch-name" "Reason for branching"
```

Creates a new branch, copies current context, and switches to it.

### Switch Branch

```bash
# Switch to a different branch
python "${CLAUDE_PLUGIN_ROOT}/skills/pop-session-branch/scripts/branch_operations.py" \
  switch "branch-name"
```

### Merge Branch

```bash
# Merge findings back to parent
python "${CLAUDE_PLUGIN_ROOT}/skills/pop-session-branch/scripts/branch_operations.py" \
  merge "branch-name" "What was learned/fixed"
```

### List Branches

```bash
# List all branches
python "${CLAUDE_PLUGIN_ROOT}/skills/pop-session-branch/scripts/branch_operations.py" \
  list
```

### Delete Branch

```bash
# Delete a merged branch
python "${CLAUDE_PLUGIN_ROOT}/skills/pop-session-branch/scripts/branch_operations.py" \
  delete "branch-name"
```

## Use Cases

### Bug Investigation

```
User: "There's a weird auth issue, can you investigate?"

1. Create branch: "auth-investigation"
2. Investigate the bug (read files, run tests, etc.)
3. Fix the bug or document findings
4. Merge back: "Fixed: Token refresh was missing error handling"
5. Return to main task with findings preserved
```

### Research Spike

```
User: "Before we implement caching, research Redis vs Memcached"

1. Create branch: "cache-research"
2. Research both options (web search, docs, etc.)
3. Document pros/cons in branch context
4. Merge back: "Decision: Redis for persistence and pub/sub support"
5. Continue main implementation with decision recorded
```

### Debugging Tangent

```
User: "Why is this test failing?"

1. Create branch: "test-failure-debug"
2. Debug the test (read test code, check fixtures, etc.)
3. Identify root cause
4. Merge back: "Root cause: Mock was returning wrong type"
5. Main context unaffected by debug details
```

## Branch Lifecycle

```
main ──────────────┬─────────────────────► (continues)
                   │
                   └── auth-bug ──► merge ─┘
                        │
                        └── Investigate token expiry
                        └── Fix refresh logic
                        └── Outcome: "Fixed token refresh"
```

## STATUS.json Structure

```json
{
  "branches": {
    "main": {
      "id": "main",
      "parent": null,
      "context": { "focusArea": "Feature implementation" },
      "tasks": { "inProgress": ["Implement user auth"] }
    },
    "auth-bug": {
      "id": "auth-bug",
      "parent": "main",
      "reason": "Investigating token expiry",
      "context": { "focusArea": "Token refresh debugging" },
      "merged": true,
      "outcome": "Fixed: Token refresh now handles errors"
    }
  },
  "currentBranch": "main",
  "branchHistory": [
    { "action": "branch", "from": "main", "to": "auth-bug" },
    { "action": "merge", "from": "auth-bug", "to": "main", "outcome": "..." }
  ]
}
```

## Integration

**Morning Routine:** Shows active branches with last activity
**Nightly Routine:** Warns about unmerged branches
**Session Resume:** Restores correct branch context
**Recording:** Branch events captured in session recording

## Best Practices

1. **Name branches descriptively:** `auth-bug`, `redis-research`, `test-failure-42`
2. **Write clear reasons:** Helps future you understand why you branched
3. **Merge with outcomes:** Document what you learned/fixed
4. **Don't over-branch:** Only branch for substantial tangents (5+ minutes)
5. **Clean up:** Delete merged branches to reduce clutter
