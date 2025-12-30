# Git Worktree Integration - Quick Reference

**Status:** Research Complete, Implementation Pending
**Issue:** #617 (Closed - Research Complete)
**Updated:** 2025-12-30

---

## The PopKit Way (Vision)

**Goal:** Zero-overhead issue-driven development with automatic work tree management.

```bash
# Create issue
/popkit:issue create "Add dark mode toggle"
# → Issue #142 created

# Work on it (ONE COMMAND)
/popkit:dev work #142
# → PopKit handles everything automatically
```

---

## What Happens Automatically

When you run `/popkit:dev work #142`:

### 1. Issue Parsing
```
✅ Fetch issue from GitHub
✅ Parse Work Tree Context:
   - App: genesis
   - Type: feature
   - Safety: safe
```

### 2. Work Tree Creation
```
✅ Generate name: feature-142-dark-mode
✅ Create branch: feature/142-dark-mode
✅ Create work tree: .worktrees/feature-142-dark-mode/
✅ Assign port: 3102 (genesis base 3002 + 100)
```

### 3. Environment Setup
```
✅ Create .env.local with PORT=3102
✅ Run npm install (if needed)
✅ Verify tests pass (baseline)
```

### 4. Workflow Execution
```
✅ Parse PopKit Guidance
✅ Route through orchestrator
✅ Execute 7-phase workflow
✅ All work happens in isolated tree
```

### 5. Cleanup
```
✅ Push commits to feature branch
✅ Delete work tree
✅ Update state tracking
✅ Present next actions
```

---

## Work Tree Naming

Format: `<type>-<number>-<slugified-title>`

### Examples

| Issue | Title | Work Tree Name |
|-------|-------|----------------|
| #123 | Add user authentication | `feature-123-auth` |
| #456 | Fix login regression | `bugfix-456-login-regression` |
| #789 | Refactor component library | `refactor-789-components` |
| #999 | Security patch CVE-2024 | `hotfix-999-security-patch` |

### Rules

- **Max length:** 50 characters
- **No spaces:** Use hyphens
- **Slugified:** Lowercase, no punctuation
- **Include number:** Enables traceability

---

## Port Assignment

### Algorithm

```javascript
assignedPort = basePort + (workTreeIndex × 100)
```

### ElShaddai App Ports

| App | Base | WT 1 | WT 2 | WT 3 |
|-----|------|------|------|------|
| Genesis | 3002 | 3102 | 3202 | 3302 |
| Optimus | 3050 | 3150 | 3250 | 3350 |
| PopKit | 3007 | 3107 | 3207 | 3307 |
| Reseller | 5000 | 5100 | 5200 | 5300 |
| RunTheWorld | 3009 | 3109 | 3209 | 3309 |
| Consensus | 3003 | 3103 | 3203 | 3303 |
| Daniel-Son | 5173 | 5273 | 5373 | 5473 |
| AIProxy | 8000 | 8100 | 8200 | 8300 |
| Voice Clone | 8000 | 8100 | 8200 | 8300 |

**Note:** AIProxy and Voice Clone share base port - automatic conflict detection needed.

---

## Issue Template - Work Tree Context

All issue templates now include:

```markdown
## Work Tree Context

### Application
- [ ] genesis
- [ ] optimus
- [ ] popkit
- [ ] reseller-central
- [ ] runtheworld
- [ ] consensus
- [ ] daniel-son
- [ ] aiproxy
- [ ] voice-clone-app
- [ ] scribemaster
- [ ] cross-app

### Work Tree Type
- [ ] feature - New capability
- [ ] bugfix - Bug fix
- [ ] refactor - Code restructuring
- [ ] hotfix - Urgent production fix
- [ ] experimental - Proof of concept
- [ ] research - Investigation/spike
- [ ] docs - Documentation

### Async Safety Level
- [ ] safe - Multiple agents can work in parallel
- [ ] requires-lock - File-level coordination needed
- [ ] sequential - Must execute sequentially
```

---

## Power Mode Integration

### Isolated Agent Work Trees

**Scenario:** Issue #45 "Add Authentication" (Power Mode RECOMMENDED)

```
Main Work Tree: feature-45-auth (Port 3102)

Phase 1: Discovery (Shared)
├─ code-explorer
├─ code-architect
└─ researcher
└─ Checkpoint: Review findings

Phase 2: Implementation (Isolated)
├─ Agent 1: feature-45-auth-service (Port 3103)
├─ Agent 2: feature-45-auth-ui (Port 3104)
└─ Agent 3: feature-45-auth-tests (Port 3105)
└─ Checkpoint: Code review

Phase 3: Integration (Back to Main)
├─ Merge agent-1 → main tree
├─ Merge agent-2 → main tree
├─ Merge agent-3 → main tree
├─ Run full test suite
└─ Delete all sub-work-trees
```

**Benefits:**
- No file conflicts between agents
- True parallel execution
- Automatic merge coordination
- Isolated dev servers

---

## State Tracking

**File:** `.claude/popkit/work-tree-state.json`

**Purpose:** Track active work trees across sessions

**Schema:**
```json
{
  "active_worktrees": [
    {
      "id": "wt-001",
      "name": "feature-142-dark-mode",
      "issue_number": 142,
      "app_name": "genesis",
      "port": 3102,
      "branch_name": "feature/142-dark-mode",
      "status": "in_progress",
      "created_at": "2025-12-20T10:30:00Z"
    }
  ],
  "completed_worktrees": [...],
  "failed_worktrees": [...]
}
```

---

## Commands Reference

### Existing (Manual)

```bash
# Create work tree manually
/popkit:worktree create feature-auth

# List active work trees
/popkit:worktree list

# Remove work tree
/popkit:worktree remove feature-auth

# Clean up stale work trees
/popkit:worktree prune
```

### Future (Automatic via /popkit:dev work)

```bash
# Work on issue (automatic work tree creation)
/popkit:dev work #142

# Work with Power Mode
/popkit:dev work #142 -p

# List stale work trees
/popkit:worktree list --stale

# Analyze parallel work opportunities
/popkit:worktree analyze
```

---

## Implementation Functions

### Key Functions to Implement

```python
# 1. Parse issue metadata
parse_work_tree_context(issue_body: str) -> Dict[str, Any]

# 2. Generate work tree name
generate_worktree_name(
    issue_number: int,
    issue_title: str,
    work_tree_type: str
) -> str

# 3. Assign port
assign_work_tree_port(
    app_name: str,
    work_tree_index: int = 1
) -> int

# 4. Create work tree
create_work_tree(
    name: str,
    branch: str,
    base_branch: str = "main"
) -> str

# 5. Setup environment
setup_work_tree_environment(
    path: str,
    app_name: str,
    port: int
) -> bool

# 6. Track state
add_active_worktree(...) -> str
mark_worktree_completed(wt_id: str) -> None

# 7. Cleanup
cleanup_work_tree(name: str, delete_branch: bool = False) -> bool
```

---

## File Locations

### Research Documents
- `docs/research/git-worktree-strategy.md` (13.8 KB)
- `docs/research/git-worktree-integration-guide.md` (20.8 KB)
- `docs/research/git-worktree-implementation-roadmap.md` (28.0 KB)
- `docs/research/git-worktree-integration-summary.md` (Executive summary)
- `docs/research/git-worktree-quick-reference.md` (This file)

### Implementation Files (To Be Modified)
- `packages/popkit-dev/hooks/utils/github_issues.py` (add parsers)
- `packages/popkit-dev/commands/dev.md` (update work mode)
- `packages/popkit-core/power-mode/coordinator.py` (add coordination)
- `.claude/popkit/work-tree-state.json` (create state file)

### Issue Templates (Updated ✅)
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/architecture.md`
- `.github/ISSUE_TEMPLATE/research.md`

---

## Implementation Timeline

**Total Effort:** 12-14 hours

### Week 1: Parser & Functions (2-3 hours)
- Implement parsers and naming functions
- Write unit tests

### Week 2: Work Tree Creation (3-4 hours)
- Enhance `/popkit:dev work` command
- Implement state tracking

### Week 3: Power Mode (3-4 hours)
- Add work tree coordination
- Implement sub-work-tree creation

### Week 4: Testing (2-3 hours)
- Manual testing
- Bug fixes
- Documentation updates

---

## Success Criteria

### Must Have
- [ ] Automatic work tree creation from `/popkit:dev work #N`
- [ ] Automatic port assignment
- [ ] Environment setup (.env.local)
- [ ] Automatic cleanup
- [ ] State tracking across sessions

### Should Have
- [ ] Power Mode sub-work-tree isolation
- [ ] Merge coordination
- [ ] Conflict detection
- [ ] Stale work tree cleanup

### Nice to Have
- [ ] Visual work tree dashboard
- [ ] Performance monitoring
- [ ] Cross-app coordination
- [ ] Work tree templates

---

## Common Workflows

### Simple Feature
```bash
/popkit:issue create "Add dark mode"
# Select: genesis, feature, safe
/popkit:dev work #150
# PopKit: Creates feature-150-dark-mode, runs workflow, cleans up
```

### Bug Fix
```bash
/popkit:issue create "Fix login on mobile" --template bug
# Auto-filled: bugfix, safe
/popkit:dev work #151
# PopKit: Creates bugfix-151-login-mobile, sequential execution
```

### Complex Feature (Power Mode)
```bash
/popkit:issue create "Add authentication"
# Select: genesis, feature, safe, Power Mode: RECOMMENDED
/popkit:dev work #152 -p
# PopKit: Creates main + 3 agent work trees, parallel execution
```

### Multi-App Epic
```bash
/popkit:issue create "Refactor types" --template architecture
# Select: genesis, optimus, popkit (multiple apps)
/popkit:dev work #153
# PopKit: Creates single work tree, coordinates across apps
```

---

## Troubleshooting

### Port Already in Use
```bash
# Find what's using it
netstat -ano | findstr :3102

# Kill the process
taskkill /PID <PID> /F
```

### Work Tree Won't Delete
```bash
# Force remove
git worktree remove --force .worktrees/feature-123-stale

# Prune orphaned refs
git worktree prune
```

### Tests Failing
```bash
# Check baseline in main
git checkout main
npm test

# If main passes, issue is in work tree
# If main fails, issue exists before work tree creation
```

---

## Next Steps

1. **Review Research:** Read the three main research documents
2. **Create Implementation Issue:** Track development in separate issue
3. **Follow Roadmap:** Use `git-worktree-implementation-roadmap.md`
4. **Target Milestone:** v2.0.0 (Multi-Model Platform)

---

## References

- **Issue:** #617 (Research Complete)
- **Branch:** `claude/research-work-tree-usage-39lKV` (Merged in PR #533)
- **Milestone:** v2.0.0
- **Size:** Large (12-14 hours)
- **Priority:** P2-medium (phase:next)

---

**Last Updated:** 2025-12-30
**Status:** Quick Reference - Implementation Pending
