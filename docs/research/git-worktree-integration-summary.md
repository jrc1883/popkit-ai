# Git Worktree Integration Research - Executive Summary

**Issue:** #617
**Status:** Research Complete, Implementation Planned
**Created:** 2025-12-20
**Updated:** 2025-12-30

---

## Executive Summary

This document summarizes the comprehensive research on integrating Git worktrees with PopKit's issue-driven development workflow. The goal is to enable automatic, isolated workspace creation for each GitHub issue with zero manual overhead.

**Key Achievement:** "The PopKit Way" - One command (`/popkit:dev work #N`) automatically handles workspace creation, environment setup, workflow execution, and cleanup.

---

## Research Documents

Three comprehensive documents have been created and merged into the repository:

### 1. [Git Worktree Strategy](git-worktree-strategy.md) (13.8 KB)

**Purpose:** Foundation document covering work tree naming, structure, and best practices

**Key Sections:**
- Work tree naming convention: `<type>-<number>-<slugified-title>`
- Port assignment strategy: base port + (work tree index × 100)
- Safety levels for async execution (none/requires-lock/safe)
- Cleanup strategies (automatic and manual)
- Integration with Power Mode for parallel agents

**Example Naming:**
```
Issue #123 "Add user authentication" → feature-123-auth-system
Issue #456 "Fix login regression" → bugfix-456-login-regression
Issue #789 "Refactor components" → refactor-789-components
```

**Port Assignment:**
```javascript
// Genesis base port: 3002
const basePort = 3002;
const workTreeIndex = 1;
const assignedPort = basePort + (100 * workTreeIndex); // 3102
```

### 2. [Git Worktree Integration Guide](git-worktree-integration-guide.md) (20.8 KB)

**Purpose:** User-facing workflow guide showing the ideal developer experience

**Key Features:**
- Step-by-step walkthrough of "The PopKit Way"
- Issue templates with Work Tree Context metadata
- Automatic workspace isolation and port management
- Power Mode coordination with sub-work-trees
- Complete examples for different issue types

**The Ideal Workflow:**
```bash
# Step 1: Create issue with Work Tree Context
/popkit:issue create "Add dark mode toggle"

# Step 2: Work on it (ONE COMMAND)
/popkit:dev work #142

# Behind the scenes, PopKit automatically:
# ✅ Parses issue metadata (app, type, safety level)
# ✅ Creates isolated work tree
# ✅ Assigns dev server port (3102)
# ✅ Sets up .env.local
# ✅ Executes 7-phase workflow
# ✅ Cleans up on completion
```

**Power Mode Example:**
```
Issue #45: "Add Authentication System"

Phase 1: Discovery (shared work tree)
├─ code-explorer: Analyzes codebase
├─ code-architect: Plans architecture
└─ researcher: Evaluates libraries

Phase 2: Implementation (isolated work trees)
├─ Agent 1: feature-45-auth-service → .worktrees/feature-45-auth-service/
├─ Agent 2: feature-45-auth-ui → .worktrees/feature-45-auth-ui/
└─ Agent 3: feature-45-auth-tests → .worktrees/feature-45-auth-tests/

Phase 3: Integration (back to main work tree)
├─ Merge all isolated work trees
├─ Run full test suite
└─ Final review
```

### 3. [Git Worktree Implementation Roadmap](git-worktree-implementation-roadmap.md) (28.0 KB)

**Purpose:** Detailed technical implementation plan with code examples

**Implementation Phases:**

#### Phase 1: Design & Documentation ✅ COMPLETE
- Issue templates updated with Work Tree Context section
- Strategy documents created
- User workflow guide written

#### Phase 2: Code Implementation ⏳ READY
- Parser functions for Work Tree Context
- Work tree name generator
- Port assignment algorithm
- Enhanced `/popkit:dev work #N` command
- Power Mode coordinator updates
- State tracking file

#### Phase 3: Testing ⏳ READY
- Unit tests for all new functions
- Integration tests for end-to-end workflows
- Manual testing checklist

#### Phase 4: Deployment & Documentation ⏳ READY
- Release notes
- README updates
- Changelog entries

**Key Functions to Implement:**

```python
# 1. Parse Work Tree Context from issue body
def parse_work_tree_context(issue_body: str) -> Dict[str, Any]:
    """
    Returns:
    {
        "app_name": "genesis",
        "work_tree_type": "feature",
        "async_safety": "safe",
        "worktree_name": "feature-142-dark-mode"
    }
    """

# 2. Generate work tree name
def generate_worktree_name(
    issue_number: int,
    issue_title: str,
    work_tree_type: str
) -> str:
    """
    Example: generate_worktree_name(142, "Add dark mode toggle", "feature")
    Returns: "feature-142-dark-mode-toggle"
    """

# 3. Assign port
def assign_work_tree_port(
    app_name: str,
    work_tree_index: int = 1
) -> int:
    """
    Example: assign_work_tree_port("genesis", 1)
    Returns: 3102 (3002 + 100)
    """
```

---

## Issue Templates Enhanced

All four issue templates have been updated with Work Tree Context sections:

### Feature Request Template
```markdown
## Work Tree Context

### Application
- [ ] genesis
- [ ] optimus
- [ ] popkit
- [etc.]

### Work Tree Type
- [ ] feature
- [ ] bugfix
- [ ] refactor
- [ ] experimental

### Async Safety Level
- [ ] safe - Multiple agents can work in parallel
- [ ] requires-lock - File-level coordination needed
- [ ] sequential - Must execute sequentially
```

### Templates Updated:
- ✅ `feature_request.md`
- ✅ `bug_report.md`
- ✅ `architecture.md`
- ✅ `research.md`

---

## State Tracking

New state file: `.claude/popkit/work-tree-state.json`

**Schema:**
```json
{
  "version": "1.0.0",
  "active_worktrees": [
    {
      "id": "wt-001",
      "name": "feature-142-dark-mode",
      "issue_number": 142,
      "app_name": "genesis",
      "work_tree_type": "feature",
      "port": 3102,
      "branch_name": "feature/142-dark-mode",
      "path": ".worktrees/feature-142-dark-mode",
      "created_at": "2025-12-20T10:30:00Z",
      "status": "in_progress"
    }
  ],
  "completed_worktrees": [...],
  "failed_worktrees": [...]
}
```

---

## Port Assignment Strategy

### ElShaddai Monorepo App Ports

| App | Base Port | Work Tree Offset | Example |
|-----|-----------|------------------|---------|
| Genesis | 3002 | +100 per tree | 3102, 3202, 3302 |
| Optimus | 3050 | +100 per tree | 3150, 3250, 3350 |
| Consensus | 3003 | +100 per tree | 3103, 3203, 3303 |
| Daniel-Son | 5173 | +100 per tree | 5273, 5373, 5473 |
| Reseller Central | 5000 | +100 per tree | 5100, 5200, 5300 |
| RunTheWorld | 3009 | +100 per tree | 3109, 3209, 3309 |
| PopKit Cloud | 3007 | +100 per tree | 3107, 3207, 3307 |
| AIProxy | 8000 | +100 per tree | 8100, 8200, 8300 |
| Voice Clone | 8000 | +100 per tree | 8100, 8200, 8300 |
| ScribeMaster | N/A | CLI only | N/A |

**Conflict Resolution:**
- Voice Clone and AIProxy both use 8000 base port
- Solution: Automatic detection and alternative port assignment
- Fallback: Use next available port in range

---

## Power Mode Coordination

### Work Tree Isolation for Parallel Agents

**Scenario:** Issue #45 "Add Authentication System" with Power Mode

**Execution Flow:**

```
Main Work Tree: .worktrees/feature-45-auth/ (Port 3102)

Phase 1: Discovery (Shared)
├─ All agents work in main tree
├─ Read-only analysis phase
└─ Checkpoint: Review findings

Phase 2: Implementation (Isolated)
├─ Agent 1: .worktrees/feature-45-auth-service/ (Port 3103)
├─ Agent 2: .worktrees/feature-45-auth-ui/ (Port 3104)
└─ Agent 3: .worktrees/feature-45-auth-tests/ (Port 3105)

Phase 3: Integration (Back to Main)
├─ Merge agent-1 → main
├─ Merge agent-2 → main
├─ Merge agent-3 → main
├─ Run full test suite
└─ Delete all sub-work-trees
```

**Coordination Mechanism:**
- State tracking in `.claude/popkit/work-tree-state.json`
- File-level conflict detection
- Automatic merge coordination
- Cleanup verification

---

## Integration with Existing Commands

### `/popkit:dev work #N` Enhanced Flow

**Current (Before Implementation):**
```
1. Fetch issue
2. Parse PopKit Guidance
3. Route through orchestrator
4. Execute workflow
```

**Enhanced (After Implementation):**
```
1. Fetch issue
2. Parse Work Tree Context ← NEW
   - Extract app, type, safety level
3. Create work tree ← NEW
   - Generate name
   - Assign port
   - Set up environment
4. Parse PopKit Guidance
5. Route through orchestrator
6. Execute workflow IN WORK TREE ← ENHANCED
7. Cleanup on completion ← NEW
   - Push commits
   - Delete work tree
   - Update state tracking
```

### New `/popkit:worktree` Commands

Building on existing `pop-worktrees` skill:

| Command | Description |
|---------|-------------|
| `/popkit:worktree create <name>` | Create work tree manually |
| `/popkit:worktree list` | List all active work trees |
| `/popkit:worktree list --stale` | Show abandoned work trees |
| `/popkit:worktree analyze` | Find parallel work opportunities |
| `/popkit:worktree remove <name>` | Delete work tree safely |
| `/popkit:worktree prune` | Clean up stale work trees |

---

## Implementation Timeline

**Total Estimated Effort:** 12-14 hours

### Week 1: Parser & Functions (2-3 hours)
- [ ] Implement `parse_work_tree_context()`
- [ ] Implement `generate_worktree_name()`
- [ ] Implement `assign_work_tree_port()`
- [ ] Write unit tests

### Week 2: Work Tree Creation (3-4 hours)
- [ ] Add work tree creation to `/popkit:dev work`
- [ ] Implement environment setup
- [ ] Implement state tracking
- [ ] Write integration tests

### Week 3: Power Mode Integration (3-4 hours)
- [ ] Update Power Mode coordinator
- [ ] Implement sub-work-tree creation
- [ ] Implement merge coordination
- [ ] Write integration tests

### Week 4: Testing & Polish (2-3 hours)
- [ ] Manual testing of all scenarios
- [ ] Fix edge cases
- [ ] Update documentation
- [ ] Release preparation

---

## Success Criteria

### Functional Requirements
- [ ] `/popkit:dev work #N` creates work tree automatically
- [ ] Port assignments are automatic and conflict-free
- [ ] Power Mode agents work in parallel in isolated work trees
- [ ] Work trees are automatically cleaned up on completion
- [ ] State tracking works across sessions

### Quality Requirements
- [ ] Unit tests for all new functions (>90% coverage)
- [ ] Integration tests for end-to-end workflows
- [ ] Manual testing of 3 scenarios (feature, bug fix, epic)
- [ ] No regressions in existing PopKit functionality
- [ ] Clear error messages for edge cases

### Documentation Requirements
- [ ] CLAUDE.md updated with work tree section
- [ ] Issue templates in all 10 apps updated
- [ ] Changelog updated
- [ ] User-facing guide is clear and complete

---

## Files Modified/Created

### Documentation (Complete ✅)
- ✅ `docs/research/git-worktree-strategy.md`
- ✅ `docs/research/git-worktree-integration-guide.md`
- ✅ `docs/research/git-worktree-implementation-roadmap.md`
- ✅ `.github/ISSUE_TEMPLATE/feature_request.md`
- ✅ `.github/ISSUE_TEMPLATE/bug_report.md`
- ✅ `.github/ISSUE_TEMPLATE/architecture.md`
- ✅ `.github/ISSUE_TEMPLATE/research.md`

### Implementation (Pending ⏳)
- ⏳ `packages/popkit-dev/hooks/utils/github_issues.py` (add parsers)
- ⏳ `packages/popkit-dev/commands/dev.md` (update work mode)
- ⏳ `packages/popkit-core/power-mode/coordinator.py` (add coordination)
- ⏳ `.claude/popkit/work-tree-state.json` (create state file)
- ⏳ `packages/popkit-dev/tests/test_work_tree_context.py` (unit tests)
- ⏳ `packages/popkit-dev/tests/test_popkit_dev_work_integration.py` (integration tests)

### Configuration (Pending ⏳)
- ⏳ `CLAUDE.md` (add work tree integration section)
- ⏳ `CHANGELOG.md` (add version entry)
- ⏳ `README.md` (update quick start)

---

## Benefits of This Approach

### For Developers
1. **Zero Manual Overhead:** No more manual work tree creation, port configuration, or cleanup
2. **Automatic Isolation:** Each issue gets its own workspace, preventing interference
3. **Parallel Development:** Work on multiple issues simultaneously without conflicts
4. **Safety Guarantees:** Clean test baseline before starting, automatic cleanup on completion

### For Power Mode
1. **True Parallelization:** Agents work in completely isolated environments
2. **No File Conflicts:** Each agent has its own work tree during implementation
3. **Coordinated Integration:** Automatic merge-back with conflict detection
4. **Scalability:** Support for 10+ parallel agents with proper coordination

### For ElShaddai Monorepo
1. **Multi-App Support:** Work trees work across all 10 applications
2. **Port Management:** Automatic port assignment prevents dev server conflicts
3. **Cross-App Coordination:** Epic issues can coordinate changes across multiple apps
4. **Clean Repository:** Automatic cleanup keeps main branch pristine

---

## Known Limitations & Future Work

### Current Limitations
1. **Port Conflicts:** Voice Clone and AIProxy both use 8000
   - Workaround: Automatic conflict detection and alternative port assignment
   - Future: Smart port allocation algorithm

2. **Cross-App Work Trees:** Multi-app PRs need careful coordination
   - Current: Single work tree, multiple app changes
   - Future: Linked work trees with cross-app state tracking

3. **Power Mode Scaling:** Limited to ~5-10 agents per batch
   - Current: Tier-dependent (native/redis/file-based modes)
   - Future: Vertical scaling with better coordination

### Future Enhancements
- [ ] Automatic port conflict detection and resolution
- [ ] Visual dashboard of active work trees
- [ ] Work tree performance monitoring
- [ ] Automatic work tree suggestions based on code changes
- [ ] Work tree templates for common patterns
- [ ] Cross-IDE work tree synchronization

---

## Decision Log

### Port Assignment Algorithm
**Decision:** Use simple base + (index × 100) algorithm
**Rationale:** Predictable, easy to debug, allows manual override in .env
**Alternative Considered:** Dynamic port discovery (too complex for v1)

### Work Tree Cleanup
**Decision:** Automatic on completion with state tracking
**Rationale:** Reduces manual overhead, state file enables recovery
**Alternative Considered:** Manual approval (too much friction)

### Power Mode Batching
**Decision:** Dynamic per-phase batching
**Rationale:** Discovery shared, implementation isolated, integration shared
**Alternative Considered:** Fixed batch size (not flexible enough)

### State Persistence
**Decision:** JSON file in `.claude/popkit/`
**Rationale:** Simple, git-tracked, human-readable
**Alternative Considered:** SQLite database (overkill for v1)

---

## Conclusion

The Git Worktree Integration research is **complete and ready for implementation**. All design decisions have been made, documentation is written, and the implementation roadmap is detailed.

**Next Action:** Proceed to Phase 2 (Code Implementation) following the roadmap in `git-worktree-implementation-roadmap.md`.

**Estimated Timeline:** 3-4 weeks for full implementation and testing.

**Primary Benefit:** Developers can focus 100% on problem-solving instead of environment management. "The PopKit Way" becomes `/popkit:issue create` → `/popkit:dev work #N` → done.

---

## References

### Research Documents
- [Git Worktree Strategy](git-worktree-strategy.md)
- [Git Worktree Integration Guide](git-worktree-integration-guide.md)
- [Git Worktree Implementation Roadmap](git-worktree-implementation-roadmap.md)

### Related Issues
- #617 - Git Worktree Integration for Issue-Driven Development
- #39 - Original work tree integration request (if exists)

### Related Commands
- `/popkit:dev work #N` - Issue-driven development command
- `/popkit:worktree` - Work tree management commands
- `/popkit:power` - Power Mode orchestration

### Related Skills
- `pop-worktrees` - Git worktree creation skill
- `pop-finish-branch` - Branch completion workflow

---

**Created:** 2025-12-30
**Status:** Research Complete, Implementation Ready
**Owner:** PopKit Development Team
**Milestone:** v2.0.0 (Multi-Model Platform Expansion)
