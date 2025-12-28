# PopKit Work Tree Integration Guide

**The PopKit Way:** Issue-driven development with automatic work tree isolation and orchestration.

---

## What This Document Covers

How to work effectively with ElShaddai monorepo using `/popkit:dev work #N` workflow where:
- Work trees are **automatically created** from issue metadata
- **Port management** is automatic
- **Async agents** get isolated environments
- **"Do it the popkit way"** means: create an issue → `/popkit:dev work #N` → done

---

## The Ideal Workflow (80% of Your Time)

### You Say: "Create an issue for X and work on it the popkit way"

Here's what happens:

```bash
# Step 1: Create issue with Work Tree Context
/popkit:issue create "Add dark mode toggle to settings"

# Step 2: GitHub shows template → You fill in:
# - Application: genesis
# - Work Tree Type: feature
# - Power Mode: optional
# - Complexity: medium
# - Agents: code-architect, test-writer-fixer

# Step 3: Issue created (#142)
# You get a link to view it

# Step 4: Work on it (ONE COMMAND)
/popkit:dev work #142

# Behind the scenes, popkit does ALL of this automatically:
# ✅ Fetches issue #142 from GitHub
# ✅ Parses Work Tree Context (app=genesis, type=feature)
# ✅ Creates work tree: .worktrees/feature-142-dark-mode/
# ✅ Generates branch: feature/142-dark-mode
# ✅ Assigns port: 3102 (base 3002 + offset for work tree #1)
# ✅ Sets up .env.local with PORT=3102
# ✅ Parses PopKit Guidance (workflow, agents, phases)
# ✅ Routes through orchestrator → Full 7-phase workflow
# ✅ Executes in isolated work tree
# ✅ On completion:
#    - Pushes commits to feature branch
#    - Cleans up work tree
#    - Presents next actions

# Step 5: Done! No manual work tree management needed
```

---

## The Concept: Why This Matters

### Before (Traditional)
```
User: "Work on the auth system"
Dev: Switches branches manually
Dev: Finds port conflicts
Dev: Manages multiple async agents manually
Dev: Cleans up manually later
```

### After (PopKit Way)
```
User: `/popkit:dev work #123`
PopKit: Handles everything automatically
User: Done when work is complete
```

---

## How It Works: The 4-Layer Architecture

### Layer 1: GitHub Issues (Metadata)

**Location:** `.github/ISSUE_TEMPLATE/*.md`

**New Section: Work Tree Context**
```markdown
## Work Tree Context

### Application
- [x] genesis

### Work Tree Type
- [x] feature

### Async Safety Level
- [x] safe

### Development Ports
[auto-assigned]
```

**Why:** Gives `/popkit:dev work #N` the context it needs to create the right environment.

---

### Layer 2: Issue Parser (Extraction)

**Location:** `apps/popkit/packages/plugin/hooks/utils/github_issues.py`

**Function:** `parse_work_tree_context(issue_body)`

```python
def parse_work_tree_context(issue_body: str) -> Dict[str, Any]:
    """
    Extract Work Tree Context from issue.

    Returns:
    {
        "app_name": "genesis",
        "work_tree_type": "feature",
        "async_safety": "safe",
        "estimated_ports": 1,
        "worktree_name": "feature-142-dark-mode",
        "assigned_port": 3102,
        "branch_name": "feature/142-dark-mode"
    }
    """
```

**New capability:** Parses Work Tree Context section in addition to PopKit Guidance.

---

### Layer 3: Work Tree Creator (Automation)

**Location:** `/popkit:dev work` command implementation

**The Enhanced Flow:**

```
1. Fetch issue
   gh issue view 142 --json ...

2. Parse Work Tree Context
   github_issues.py::parse_work_tree_context()
   → Returns: app_name, type, safety level, port assignment

3. Create work tree
   git worktree add .worktrees/feature-142-dark-mode \
       -b feature/142-dark-mode main

4. Set up environment
   - Create .env.local with PORT=3102
   - npm install (if needed)
   - Run baseline tests

5. Parse PopKit Guidance
   github_issues.py::parse_popkit_guidance()
   → Returns: workflow, phases, agents, power mode, complexity

6. Route through orchestrator
   - Analyze: complexity → quick or full mode
   - Activate: Power Mode if needed
   - Select agents based on guidance

7. Execute workflow
   - Phase 1: Discovery (if full mode)
   - Phase 2-7: Following orchestrated path

8. On completion
   - Push commits to feature branch
   - Delete work tree
   - Clean up environment
   - Present next actions
```

---

### Layer 4: Power Mode Coordination (Parallelization)

**Location:** `apps/popkit/packages/plugin/power-mode/coordinator.py`

**New capability:** Work tree-aware parallel execution

```
Issue #45: "Add authentication system"
Type: feature | Safety: safe | Power Mode: RECOMMENDED

Phase 1: Discovery (shared work tree)
├─ code-explorer analyzes codebase
├─ code-architect plans design
└─ researcher finds best libraries

[Checkpoint: Review findings]

Phase 2: Implementation (isolated work trees)
├─ Agent 1: feature-45-auth-service → .worktrees/feature-45-auth-service/
│  └─ Implements AuthService class
├─ Agent 2: feature-45-auth-ui → .worktrees/feature-45-auth-ui/
│  └─ Implements login components
└─ Agent 3: feature-45-auth-tests → .worktrees/feature-45-auth-tests/
   └─ Writes comprehensive tests

[Parallel execution with file-level coordination]

[Checkpoint: Code review, conflict resolution]

Phase 3: Integration (main work tree)
├─ Merge all three isolated work trees
├─ Run full test suite
└─ Final review

Result: Complete feature in single main work tree
```

**How Coordination Works:**
1. Main work tree for issue (feature-45-auth/)
2. Sub-work-trees per agent batch (feature-45-auth-service/, etc.)
3. State tracking: `.claude/popkit/work-tree-state.json`
4. Automatic conflict detection
5. Sequential merge-back on completion

---

## File Structure

### Monorepo Layout After Implementation

```
elshaddai/
├── main (always clean)
├── .worktrees/
│   ├── feature-142-dark-mode/           ← Auto-created by /popkit:dev work #142
│   │   ├── .env.local (PORT=3102)       ← Auto-configured
│   │   ├── apps/
│   │   │   └── genesis/
│   │   │       ├── src/
│   │   │       └── package.json
│   │   └── .git
│   │
│   ├── bugfix-145-login-mobile/         ← Auto-created by /popkit:dev work #145
│   │   ├── .env.local (PORT=3103)
│   │   └── ...
│   │
│   └── feature-148-auth-service/        ← Power Mode parallel agent work tree
│       ├── .env.local
│       └── ...
│
├── docs/
│   ├── WORK_TREE_STRATEGY.md            ← This explains work tree concepts
│   ├── POPKIT_WORK_INTEGRATION_GUIDE.md ← This file (workflow guide)
│   └── POPKIT_DEV_WORK_IMPLEMENTATION.md ← Technical implementation details
│
├── .claude/popkit/
│   └── work-tree-state.json             ← Tracks active work trees
│
└── apps/
    ├── genesis/
    │   ├── .github/ISSUE_TEMPLATE/
    │   │   ├── feature_request.md       ← Updated with Work Tree Context
    │   │   ├── bug_report.md            ← Updated with Work Tree Context
    │   │   └── ...
    │   └── ...
    │
    └── [9 more apps...]
```

---

## Usage: The Different Issue Types

### 1. Feature Request

```bash
/popkit:issue create "Add real-time notifications"

# Template shows:
## Work Tree Context
### Application
- [ ] genesis ← You check ONE or more

### Work Tree Type
- [ ] feature ← You check ONE
- [ ] bugfix
- [ ] refactor
- [ ] experimental

### Async Safety Level
- [ ] safe ← You check ONE
- [ ] requires-lock
- [ ] sequential
```

Then:

```bash
/popkit:dev work #150

# PopKit creates: feature-150-real-time-notifications
# Dev server: port 3102
# Phases: discovery, architecture, implementation, testing, review, documentation
# Agents: code-architect, code-explorer, test-writer-fixer
# Power Mode: YES (3 agents)
```

### 2. Bug Report

```bash
/popkit:issue create --template bug "Login fails on mobile"

# Automatically checks:
## Work Tree Context
### Application
- [x] genesis ← User specifies

### Work Tree Type
- [x] bugfix ← Pre-checked

### Async Safety Level
- [x] safe ← Pre-checked (most bugs are safe)
```

Then:

```bash
/popkit:dev work #151

# PopKit creates: bugfix-151-login-mobile
# Dev server: port 3104
# Phases: discovery, implementation, testing, review
# Agents: bug-whisperer, test-writer-fixer
# Power Mode: NO (sequential, focused debugging)
```

### 3. Architecture / Epic

```bash
/popkit:issue create --template architecture "Refactor authentication system"

## Work Tree Context
### Applications Affected
- [x] genesis
- [x] optimus
- [x] popkit
- [x] cross-app

### Work Tree Type
- [x] refactor

### Async Safety Level
- [x] requires-lock ← Epic work has dependencies
```

Then:

```bash
/popkit:dev work #152

# PopKit creates: refactor-152-auth-system
# Dev servers: Multiple ports for testing across apps
# Phases: discovery, architecture, implementation, testing, documentation, review
# Agents: code-architect, migration-specialist, refactoring-expert
# Power Mode: YES with coordination
#
# Sub-work-trees for parallel phases:
# - refactor-152-auth-service/
# - refactor-152-auth-ui/
# - refactor-152-auth-tests/
```

### 4. Research

```bash
/popkit:issue create --template research "Evaluate real-time library options"

## Work Tree Context
### Primary Application
- [x] research

### Work Tree Type
- [x] research

### Async Safety Level
- [x] safe ← Research is isolated
```

Then:

```bash
/popkit:dev work #153

# PopKit creates: research-153-real-time-libraries
# Dev server: Optional (depends on POC)
# Phases: discovery, documentation, recommendation
# Agents: researcher, code-explorer
# Power Mode: NO (exploration work is sequential)
# Output: Research summary, comparison matrix, recommendations
```

---

## Power Mode in Action

### Example: Issue #45 - "Add Authentication System"

**Issue Metadata:**
```markdown
## Work Tree Context
### Application
- [x] genesis

### Work Tree Type
- [x] feature

### Async Safety Level
- [x] safe

## PopKit Guidance
### Power Mode
- [x] **Recommended** - Multiple agents beneficial
```

**Command:**
```bash
/popkit:dev work #45
# Or explicitly: /popkit:dev work #45 -p
```

**What Happens Behind Scenes:**

```
PHASE 1: DISCOVERY (shared work tree: feature-45-auth/)
├─ code-explorer
│  └─ Analyzes current auth patterns in genesis
│     • Finds: No existing auth, Supabase available
│     • Notes: NextAuth.js recommended
│     └─ Output: exploration report
├─ code-architect
│  └─ Plans architecture
│     • Context provider for auth state
│     • API route for login/logout
│     • Middleware for protected routes
│     └─ Output: architecture diagram
└─ researcher
   └─ Evaluates auth libraries
      • NextAuth.js vs Clerk vs Auth0
      • Compares Supabase Auth integration
      └─ Output: comparison matrix

[Checkpoint: Review findings → User approves]

PHASE 2: IMPLEMENTATION (parallel agent work trees)
Agent 1: feature-45-auth-context/
  ├─ Creates AuthContext provider
  ├─ Manages login/logout state
  └─ Provides auth hooks

Agent 2: feature-45-auth-api/
  ├─ Implements API routes
  ├─ Handles database updates
  └─ Manages sessions

Agent 3: feature-45-auth-tests/
  ├─ Writes E2E tests
  ├─ Tests auth flows
  └─ Tests error cases

[All three agents work simultaneously]
[File conflicts automatically detected and reported]

[Checkpoint: Code review → Addresses feedback]

PHASE 3: INTEGRATION (back to main work tree)
├─ Merge feature-45-auth-context/ → feature-45-auth/
├─ Merge feature-45-auth-api/ → feature-45-auth/
├─ Merge feature-45-auth-tests/ → feature-45-auth/
├─ Run full test suite
├─ Delete all sub-work-trees
└─ Final review

Result: Complete auth system ready for merge to main
```

**Port Management:**
```
genesis base port: 3002
Main work tree:     3102  (feature-45-auth/)
Agent 1 tree:       3103  (feature-45-auth-context/)
Agent 2 tree:       3104  (feature-45-auth-api/)
Agent 3 tree:       3105  (feature-45-auth-tests/)

All configured automatically in respective .env.local files
```

---

## Integration with `/popkit:dev` Command

### How `/popkit:dev work #N` Gets Enhanced

**Current Implementation (Before):**
```
1. Fetch issue
2. Parse PopKit Guidance → workflow, phases, agents, power mode
3. Route through orchestrator (quick/full mode)
4. Execute workflow
```

**Enhanced Implementation (After):**
```
1. Fetch issue
2. Parse Work Tree Context ← NEW
   - Extract app name
   - Determine work tree type
   - Infer async safety
   - Calculate port assignment
3. Create work tree ← NEW
   - git worktree add
   - Set up .env.local
   - Initialize environment
4. Parse PopKit Guidance
   - workflow, phases, agents, power mode
5. Route through orchestrator (quick/full mode)
6. Execute workflow IN WORK TREE CONTEXT ← ENHANCED
7. On completion:
   - Push to feature branch
   - Clean up work tree ← NEW
   - Update state tracking ← NEW
```

---

## Configuration Files Updated

### 1. Issue Templates (4 files)

**Files:** `.github/ISSUE_TEMPLATE/`
- `feature_request.md` ✅ Updated with Work Tree Context
- `bug_report.md` ✅ Updated with Work Tree Context
- `architecture.md` ✅ Updated with Work Tree Context
- `research.md` ✅ Updated with Work Tree Context

**New Section:**
```markdown
## Work Tree Context

### Application
### Work Tree Type
### Async Safety Level
### Development Ports
```

### 2. Issue Parser

**File:** `apps/popkit/packages/plugin/hooks/utils/github_issues.py`

**New Function:**
```python
def parse_work_tree_context(issue_body: str) -> Dict[str, Any]:
    """Parse Work Tree Context section from issue body."""
    return {
        "app_name": str,
        "work_tree_type": str,
        "async_safety": str,
        "estimated_ports": int,
        "worktree_name": str,
        "assigned_port": int,
        "branch_name": str
    }
```

**Enhancement to existing function:**
```python
def get_workflow_config(issue_number: int) -> Dict[str, Any]:
    """Now also returns work_tree_context key."""
    return {
        "issue": {...},
        "work_tree_context": {...},  # NEW
        "config": {...},
        # ... rest of existing fields
    }
```

### 3. Dev Work Command

**File:** `apps/popkit/packages/plugin/commands/dev.md`

**Enhanced `work` Mode section:**
```markdown
## Mode: work

Issue-driven development with automatic work tree creation.

### Process

1. **Fetch Issue**: `gh issue view <number> --json ...`
2. **[NEW] Parse Work Tree Context**: Extract app, type, ports
3. **[NEW] Create Work Tree**: git worktree add .worktrees/<name>
4. **[NEW] Set Up Environment**: .env.local, npm install
5. Parse PopKit Guidance: Extract workflow, agents, phases
6. Route through orchestrator: Quick or full mode
7. Execute workflow in work tree
8. **[NEW] Cleanup**: Delete work tree, clean environment
```

### 4. Work Tree State Tracking

**File:** `.claude/popkit/work-tree-state.json`

**New state structure:**
```json
{
  "active_worktrees": [
    {
      "name": "feature-142-dark-mode",
      "issue_number": 142,
      "app_name": "genesis",
      "type": "feature",
      "created_at": "2025-12-20T10:30:00Z",
      "port": 3102,
      "branch": "feature/142-dark-mode",
      "status": "in_progress"
    }
  ],
  "completed_worktrees": [
    {
      "name": "bugfix-140-validation",
      "issue_number": 140,
      "completed_at": "2025-12-19T15:45:00Z",
      "branch_merged": true
    }
  ]
}
```

---

## How to Use This (Your Daily Workflow)

### Scenario 1: Simple Bug Fix

```bash
# Create issue
/popkit:issue create "Fix validation error on signup form"

# GitHub shows bug template → You select:
# Application: genesis
# Work Tree Type: bugfix (pre-filled)
# Safety: safe (pre-filled)
# (Guidance section: pre-fills bug-whisperer agent, etc.)

# Issue created: #155

# Work on it
/popkit:dev work #155

# PopKit:
# 1. Creates: .worktrees/bugfix-155-validation-error/
# 2. Sets port: 3106
# 3. Runs: discovery → implementation → testing → review
# 4. On done: Cleanup, presents next action

# You're done! No manual work tree management.
```

### Scenario 2: Complex Feature (Power Mode)

```bash
# Create issue
/popkit:issue create "Implement real-time notifications"

# Select:
# Application: genesis
# Work Tree Type: feature
# Safety: safe (agents can work in parallel)
# Complexity: large
# (Guidance: feature template with multiple agents)

# Issue created: #156

# Work with Power Mode
/popkit:dev work #156 -p

# PopKit:
# 1. Creates main: .worktrees/feature-156-notifications/
# 2. Creates sub-work-trees for parallel agents
# 3. Phase 1: All agents share main tree (discovery)
# 4. Phase 2: Each agent gets isolated tree (implementation)
# 5. Phase 3: Merge back and finalize
# 6. On done: All work trees cleaned up

# Multiple agents work simultaneously, no conflicts
```

### Scenario 3: Multi-App Refactoring

```bash
# Create parent epic
/popkit:issue create "Refactor shared types library"

# Select:
# Applications: genesis, optimus, reseller-central
# Work Tree Type: refactor
# Safety: requires-lock (coordination needed)
# (Creates: refactor-157-types)

# Issue created: #157

/popkit:dev work #157

# PopKit:
# 1. Creates: .worktrees/refactor-157-types/
# 2. Updates types package
# 3. Creates sub-issues for each app:
#    - #157a: Update genesis imports
#    - #157b: Update optimus imports
#    - #157c: Update reseller-central imports
# 4. Links them all together
# 5. Coordinates across work trees
#
# After #157 completes:
# /popkit:dev work #157a
# /popkit:dev work #157b
# /popkit:dev work #157c
# All use same refactored types
```

---

## What This Enables ("Do It The PopKit Way")

### Before Implementing This

```bash
# User says: "Add authentication"
Developer: Manually creates branch
Developer: Sets up port configuration
Developer: Creates work tree (if lucky)
Developer: Manages multiple agents manually
Developer: Cleans up manually (often forgot)
Developer: Manual coordination with other agents
Time spent: Overhead work, not real development
```

### After Implementing This

```bash
# User says: "Add authentication"
Developer: /popkit:issue create "Add authentication"
Developer: /popkit:dev work #N
PopKit: Handles ALL the orchestration
Developer: Focuses on actual problem
PopKit: Auto-cleanup, no leftovers
Time spent: 100% on real development
```

---

## Files to Implement/Update

### Phase 1: Done (Templates & Documentation)
- ✅ `/home/user/elshaddai/docs/WORK_TREE_STRATEGY.md` - Created
- ✅ `/home/user/elshaddai/docs/POPKIT_WORK_INTEGRATION_GUIDE.md` - This file
- ✅ `.github/ISSUE_TEMPLATE/feature_request.md` - Updated
- ✅ `.github/ISSUE_TEMPLATE/bug_report.md` - Updated
- ✅ `.github/ISSUE_TEMPLATE/architecture.md` - Updated
- ✅ `.github/ISSUE_TEMPLATE/research.md` - Updated

### Phase 2: Implementation Needed
- ⏳ `apps/popkit/packages/plugin/hooks/utils/github_issues.py`
  - Add: `parse_work_tree_context()` function
  - Update: `get_workflow_config()` to include work tree context

- ⏳ `apps/popkit/packages/plugin/commands/dev.md`
  - Update: `work` mode section with work tree steps

- ⏳ `.claude/popkit/work-tree-state.json`
  - Create: New state tracking file

- ⏳ `apps/popkit/packages/plugin/power-mode/coordinator.py`
  - Update: Add work tree coordination logic
  - Add: Port assignment algorithm
  - Add: Sub-work-tree creation for agents

### Phase 3: Testing & Refinement
- ⏳ Create integration tests
- ⏳ Test multi-app work trees
- ⏳ Test Power Mode coordination
- ⏳ Document edge cases

---

## Next Steps to Complete Implementation

1. **Update the issue parser** (`github_issues.py`)
   - Add `parse_work_tree_context()` function
   - Parse app, type, safety level from checkboxes

2. **Enhance `popkit:dev work #N` command**
   - Add work tree creation step
   - Add port assignment logic
   - Add environment setup
   - Add cleanup on completion

3. **Update Power Mode coordinator**
   - Track work tree ownership
   - Assign ports for sub-work-trees
   - Handle merge-back from isolated trees

4. **Create state tracking**
   - Initialize `.claude/popkit/work-tree-state.json`
   - Track active/completed work trees
   - Use for cleanup verification

5. **Test end-to-end workflows**
   - Create simple feature
   - Create complex feature with Power Mode
   - Verify port management
   - Verify cleanup

---

**Last Updated:** 2025-12-20
**Status:** Design & Template Updates Complete
**Next:** Implementation in popkit code
**Related Issues:** #39 (Work Tree Integration)
