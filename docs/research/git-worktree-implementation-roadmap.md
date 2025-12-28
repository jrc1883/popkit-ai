# PopKit Work Tree Integration - Implementation Roadmap

**Status:** Design Complete, Implementation Ready
**Target:** Fully Integrated Work Tree Workflow with Issue Metadata

---

## Executive Summary

The PopKit work tree integration enables:
- ✅ Issue templates with "Work Tree Context" metadata
- ✅ Monorepo work tree strategy documented
- ✅ Integrated workflow guide documented
- ⏳ **Implementation needed:** Code changes to make it automatic

**When complete:** Users will say `/popkit:dev work #N` and everything happens automatically.

---

## Phase 1: Design & Documentation ✅ COMPLETE

### Deliverables
- ✅ **WORK_TREE_STRATEGY.md** - Comprehensive work tree naming, structure, and best practices
- ✅ **POPKIT_WORK_INTEGRATION_GUIDE.md** - User-facing workflow guide
- ✅ **Issue Templates Updated:**
  - ✅ `feature_request.md` - Added Work Tree Context section
  - ✅ `bug_report.md` - Added Work Tree Context section
  - ✅ `architecture.md` - Added Work Tree Context section
  - ✅ `research.md` - Added Work Tree Context section

### What Users See
New issue creation template section:
```markdown
## Work Tree Context

### Application
- [ ] genesis
- [ ] optimus
- [etc.]

### Work Tree Type
- [ ] feature
- [ ] bugfix
- [etc.]

### Async Safety Level
- [ ] safe
- [ ] requires-lock
- [ ] sequential
```

---

## Phase 2: Code Implementation ⏳ READY

### 2.1: Update Issue Parser
**File:** `apps/popkit/packages/plugin/hooks/utils/github_issues.py`

**Task:** Add `parse_work_tree_context()` function

**Implementation Steps:**

```python
def parse_work_tree_context(issue_body: str) -> Dict[str, Any]:
    """
    Parse Work Tree Context section from issue body.

    Returns:
    {
        "app_name": str,              # e.g., "genesis"
        "work_tree_type": str,        # e.g., "feature"
        "async_safety": str,          # e.g., "safe"
        "worktree_name": str,         # e.g., "feature-142-dark-mode"
    }
    """
    config = {
        "app_name": None,
        "work_tree_type": None,
        "async_safety": "safe",      # default
        "worktree_name": None,
    }

    if not issue_body:
        return config

    # Find Work Tree Context section (similar to PopKit Guidance parsing)
    context_match = re.search(
        r'## Work Tree Context\s*\n(.*?)(?=\n## |\n---|\Z)',
        issue_body,
        re.DOTALL | re.IGNORECASE
    )

    if not context_match:
        return config

    context_text = context_match.group(1)

    # Parse Application
    # Look for: - [x] **genesis**
    app_patterns = [
        ("popkit", r'\[x\].*popkit'),
        ("genesis", r'\[x\].*genesis'),
        ("optimus", r'\[x\].*optimus'),
        ("reseller-central", r'\[x\].*reseller-central'),
        ("consensus", r'\[x\].*consensus'),
        ("daniel-son", r'\[x\].*daniel-son'),
        ("runtheworld", r'\[x\].*runtheworld'),
        ("aiproxy", r'\[x\].*aiproxy'),
        ("voice-clone-app", r'\[x\].*voice-clone-app'),
        ("scribemaster", r'\[x\].*scribemaster'),
        ("cross-app", r'\[x\].*cross-app'),
    ]
    for app_name, pattern in app_patterns:
        if re.search(pattern, context_text, re.IGNORECASE):
            config["app_name"] = app_name
            break

    # Parse Work Tree Type
    type_patterns = [
        ("feature", r'\[x\].*feature'),
        ("bugfix", r'\[x\].*bugfix'),
        ("refactor", r'\[x\].*refactor'),
        ("hotfix", r'\[x\].*hotfix'),
        ("experimental", r'\[x\].*experimental'),
        ("research", r'\[x\].*research'),
        ("docs", r'\[x\].*docs'),
    ]
    for type_name, pattern in type_patterns:
        if re.search(pattern, context_text, re.IGNORECASE):
            config["work_tree_type"] = type_name
            break

    # Parse Async Safety Level
    safety_patterns = [
        ("safe", r'\[x\].*safe'),
        ("requires-lock", r'\[x\].*requires-lock'),
        ("sequential", r'\[x\].*sequential'),
    ]
    for safety, pattern in safety_patterns:
        if re.search(pattern, context_text, re.IGNORECASE):
            config["async_safety"] = safety
            break

    return config
```

**Integration:** Update `get_workflow_config()` to call this:

```python
def get_workflow_config(issue_number: int) -> Dict[str, Any]:
    # ... existing code ...

    # NEW: Parse work tree context
    work_tree_context = parse_work_tree_context(issue.get("body", ""))
    result["work_tree_context"] = work_tree_context

    # ... rest of existing code ...
    return result
```

**Testing:**
```python
# Test case 1: Parse valid work tree context
test_body = """
## Work Tree Context

### Application
- [x] genesis

### Work Tree Type
- [x] feature

### Async Safety Level
- [x] safe
"""
result = parse_work_tree_context(test_body)
assert result["app_name"] == "genesis"
assert result["work_tree_type"] == "feature"
assert result["async_safety"] == "safe"
```

---

### 2.2: Add Work Tree Naming Function
**File:** `apps/popkit/packages/plugin/hooks/utils/github_issues.py` (same file)

**Task:** Create work tree name from issue metadata

```python
def generate_worktree_name(
    issue_number: int,
    issue_title: str,
    work_tree_type: str,
    app_name: str = None
) -> str:
    """
    Generate work tree name from issue context.

    Format: <type>-<number>-<slugified-title>
    Example: feature-142-dark-mode
    Max length: 50 characters

    Returns: str (work tree name)
    """
    # Slugify title: lowercase, remove punctuation, replace spaces with hyphens
    slugified = re.sub(r'[^\w\s-]', '', issue_title.lower())
    slugified = re.sub(r'[-\s]+', '-', slugified).strip('-')

    # Build name
    name = f"{work_tree_type}-{issue_number}-{slugified}"

    # Enforce max length
    if len(name) > 50:
        # Keep type and number, truncate title
        base = f"{work_tree_type}-{issue_number}-"
        title_max = 50 - len(base)
        name = base + slugified[:title_max].rstrip('-')

    return name
```

**Testing:**
```python
# Test case 1
name = generate_worktree_name(
    issue_number=142,
    issue_title="Add dark mode toggle to settings",
    work_tree_type="feature"
)
assert name == "feature-142-dark-mode-toggle"

# Test case 2: Long title truncation
name = generate_worktree_name(
    issue_number=456,
    issue_title="Implement a very long feature name that is extremely verbose and descriptive",
    work_tree_type="refactor"
)
assert len(name) <= 50
```

---

### 2.3: Add Port Assignment Function
**File:** `apps/popkit/packages/plugin/hooks/utils/github_issues.py` (same file)

**Task:** Calculate port based on app and work tree index

```python
def get_app_base_port(app_name: str) -> int:
    """Get base port for app."""
    port_map = {
        "popkit": 3007,
        "genesis": 3002,
        "optimus": 3050,
        "reseller-central": 5000,
        "consensus": 3003,
        "daniel-son": 5173,
        "runtheworld": 3009,
        "aiproxy": 8000,
        "voice-clone-app": 5173,  # Conflict with daniel-son
        "scribemaster": None,      # CLI, no port
    }
    return port_map.get(app_name)


def assign_work_tree_port(
    app_name: str,
    work_tree_index: int = 1
) -> int:
    """
    Assign port for work tree.

    Strategy:
    - Main branch uses base port
    - Work tree 1 uses base + 100
    - Work tree 2 uses base + 200
    - etc.

    Args:
        app_name: Name of app
        work_tree_index: Which parallel work tree (1-indexed)

    Returns:
        int: Port number

    Raises:
        ValueError: If app has no dev port
    """
    base_port = get_app_base_port(app_name)

    if base_port is None:
        raise ValueError(f"App '{app_name}' has no dev port")

    # First work tree gets index 1 = offset 100
    offset = work_tree_index * 100
    assigned_port = base_port + offset

    # Validate port is in valid range
    if assigned_port < 1024 or assigned_port > 65535:
        raise ValueError(f"Port {assigned_port} out of valid range")

    return assigned_port
```

**Testing:**
```python
# Test case 1: Genesis work tree 1
port = assign_work_tree_port("genesis", work_tree_index=1)
assert port == 3102  # 3002 + 100

# Test case 2: Optimus work tree 2
port = assign_work_tree_port("optimus", work_tree_index=2)
assert port == 3250  # 3050 + 200

# Test case 3: ScribeMaster (no port)
with pytest.raises(ValueError):
    assign_work_tree_port("scribemaster")
```

---

### 2.4: Update `/popkit:dev work #N` Command
**File:** `apps/popkit/packages/plugin/commands/dev.md`

**Task:** Add work tree creation steps to mode documentation

**Update `work` mode section:**

```markdown
## Mode: work

Issue-driven development with automatic work tree creation.

### Process

1. **Fetch Issue**
   ```bash
   gh issue view <number> --json number,title,body,labels,state,author
   ```

2. **[NEW] Parse Work Tree Context**
   - Extract app_name, work_tree_type, async_safety
   - Use: github_issues.py::parse_work_tree_context()

3. **[NEW] Generate Work Tree Name**
   - Use: generate_worktree_name(issue_number, title, type)
   - Example: "feature-142-dark-mode"

4. **[NEW] Assign Port**
   - Use: assign_work_tree_port(app_name, index)
   - Create .env.local with PORT=<assigned>

5. **[NEW] Create Work Tree**
   ```bash
   git worktree add .worktrees/<name> \
       -b <branch-name> \
       main
   cd .worktrees/<name>
   ```

6. **[NEW] Set Up Environment**
   - Create .env.local with PORT and other config
   - Run npm install if needed
   - Run baseline tests

7. **Parse PopKit Guidance**
   - Use: github_issues.py::parse_popkit_guidance()
   - Extract workflow, phases, agents, power mode

8. **Route Through Orchestrator**
   - Analyze complexity → quick or full mode
   - Check if Power Mode should activate
   - Determine if brainstorming needed

9. **Execute Workflow**
   - Follow orchestrator path (quick/full/power)
   - All execution happens in work tree
   - Agents execute based on power mode (sequential/parallel)

10. **[NEW] Track State**
    - Add to .claude/popkit/work-tree-state.json
    - Mark as "in_progress"

11. **On Completion**
    - Verify all commits pushed to feature branch
    - Delete work tree: `git worktree remove <name>`
    - Prune git: `git worktree prune`
    - Update state: mark as "completed"
    - Clean up .env.local

12. **Present Next Actions**
    - Use AskUserQuestion to suggest next issues
    - Link to related issues
```

---

### 2.5: Update Power Mode Coordinator
**File:** `apps/popkit/packages/plugin/power-mode/coordinator.py`

**Task:** Add work tree coordination for parallel agents

**New functionality:**

```python
class WorkTreeCoordinator:
    """Manage work tree isolation for parallel agents."""

    def __init__(self, issue_number: int, app_name: str):
        self.issue_number = issue_number
        self.app_name = app_name
        self.state_file = Path(".claude/popkit/work-tree-state.json")
        self.main_worktree = None
        self.agent_worktrees = {}

    def create_main_worktree(self, work_tree_name: str) -> str:
        """Create main work tree for issue."""
        # git worktree add
        # Set up environment
        # Return path

    def create_agent_worktrees(
        self,
        agents: List[str],
        work_tree_type: str
    ) -> Dict[str, str]:
        """
        Create isolated work tree for each agent.

        Returns:
            {
                "agent-1": "/path/to/worktree-1",
                "agent-2": "/path/to/worktree-2",
            }
        """
        # Create sub-work-trees
        # Assign ports for each
        # Set up environments
        # Return mapping

    def coordinate_merge(self) -> bool:
        """Merge all agent work trees back to main."""
        # Merge agent-1 → main
        # Merge agent-2 → main
        # Handle conflicts
        # Run tests
        # Return success

    def cleanup(self) -> bool:
        """Delete all work trees and clean up."""
        # Delete all agent work trees
        # Delete main work tree
        # Prune git
        # Update state file
        # Return success
```

**Integration with Power Mode flow:**

```python
# In existing Power Mode coordinator:

if power_mode_active:
    # Create work tree coordinator
    wt_coord = WorkTreeCoordinator(issue_number, app_name)

    # Phase 1: Discovery (shared work tree)
    wt_coord.create_main_worktree(work_tree_name)
    execute_agents_in_worktree(agents, wt_coord.main_worktree)

    # Phase 2: Implementation (isolated work trees)
    agent_wts = wt_coord.create_agent_worktrees(agent_list, work_tree_type)
    execute_agents_parallel(agents, agent_wts)

    # Phase 3: Integration (back to main)
    wt_coord.coordinate_merge()

    # Cleanup
    wt_coord.cleanup()
```

---

### 2.6: Create State Tracking File
**File:** `.claude/popkit/work-tree-state.json`

**Task:** Initialize and maintain work tree state

**Schema:**

```json
{
  "version": "1.0.0",
  "active_worktrees": [
    {
      "id": "wt-001",
      "name": "feature-142-dark-mode",
      "issue_number": 142,
      "issue_title": "Add dark mode toggle",
      "app_name": "genesis",
      "work_tree_type": "feature",
      "async_safety": "safe",
      "branch_name": "feature/142-dark-mode",
      "port": 3102,
      "path": ".worktrees/feature-142-dark-mode",
      "created_at": "2025-12-20T10:30:00Z",
      "created_by_session": "claude-haiku-session-abc123",
      "status": "in_progress",
      "parent_worktree": null,
      "sub_worktrees": []
    }
  ],
  "completed_worktrees": [
    {
      "id": "wt-000",
      "name": "bugfix-140-validation",
      "issue_number": 140,
      "app_name": "genesis",
      "completed_at": "2025-12-19T15:45:00Z",
      "merged_to_main": true,
      "cleanup_status": "success"
    }
  ],
  "failed_worktrees": [
    {
      "id": "wt-002",
      "name": "feature-141-auth",
      "issue_number": 141,
      "failure_reason": "Merge conflict during integration",
      "failed_at": "2025-12-20T11:00:00Z",
      "manual_cleanup_needed": true
    }
  ]
}
```

**Functions:**

```python
def load_work_tree_state() -> Dict[str, Any]:
    """Load state from file."""
    state_file = Path(".claude/popkit/work-tree-state.json")
    if not state_file.exists():
        return {"version": "1.0.0", "active_worktrees": [], "completed_worktrees": [], "failed_worktrees": []}
    with open(state_file) as f:
        return json.load(f)

def save_work_tree_state(state: Dict[str, Any]) -> None:
    """Save state to file."""
    state_file = Path(".claude/popkit/work-tree-state.json")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def add_active_worktree(
    name: str,
    issue_number: int,
    issue_title: str,
    app_name: str,
    work_tree_type: str,
    branch_name: str,
    port: int
) -> str:
    """Add active work tree to state."""
    state = load_work_tree_state()
    wt_id = f"wt-{len(state['completed_worktrees']) + len(state['active_worktrees']):03d}"

    worktree = {
        "id": wt_id,
        "name": name,
        "issue_number": issue_number,
        "issue_title": issue_title,
        "app_name": app_name,
        "work_tree_type": work_tree_type,
        "branch_name": branch_name,
        "port": port,
        "path": f".worktrees/{name}",
        "created_at": datetime.now().isoformat() + "Z",
        "created_by_session": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
        "status": "in_progress",
        "parent_worktree": None,
        "sub_worktrees": []
    }

    state["active_worktrees"].append(worktree)
    save_work_tree_state(state)
    return wt_id

def mark_worktree_completed(wt_id: str, merged: bool = True) -> None:
    """Move work tree from active to completed."""
    state = load_work_tree_state()

    # Find active work tree
    active = next((w for w in state["active_worktrees"] if w["id"] == wt_id), None)
    if not active:
        return

    # Move to completed
    completed = {
        **active,
        "status": "completed",
        "completed_at": datetime.now().isoformat() + "Z",
        "merged_to_main": merged,
        "cleanup_status": "success"
    }

    state["active_worktrees"] = [w for w in state["active_worktrees"] if w["id"] != wt_id]
    state["completed_worktrees"].append(completed)
    save_work_tree_state(state)
```

---

### 2.7: Update CLAUDE.md

**File:** `/home/user/elshaddai/CLAUDE.md`

**Task:** Add work tree integration section

**Add to PopKit Integration section:**

```markdown
### Work Tree Integration

PopKit automatically creates and manages git work trees for every issue:

**Workflow:**
1. Create issue with Work Tree Context (app, type, safety level)
2. Run `/popkit:dev work #N`
3. PopKit:
   - Parses Work Tree Context metadata
   - Creates isolated work tree: `.worktrees/<type>-<N>-<title>/`
   - Assigns dev server port
   - Sets up environment
   - Executes workflow in isolation
   - Cleans up on completion

**Key Features:**
- **Automatic Isolation** - Each issue gets its own work tree
- **Port Management** - Auto-assigned dev ports prevent conflicts
- **Parallel Agents** - Power Mode agents work in isolated sub-work-trees
- **Safe Cleanup** - Automatic cleanup of stale work trees
- **Monorepo Support** - Works across all 10 apps

**See Also:**
- `docs/WORK_TREE_STRATEGY.md` - Detailed work tree strategy
- `docs/POPKIT_WORK_INTEGRATION_GUIDE.md` - User workflow guide
```

---

## Phase 3: Testing ⏳ READY

### 3.1: Unit Tests

**File:** `apps/popkit/packages/plugin/tests/test_work_tree_context.py`

```python
import pytest
from hooks.utils.github_issues import (
    parse_work_tree_context,
    generate_worktree_name,
    assign_work_tree_port,
    get_app_base_port
)

class TestParseWorkTreeContext:
    def test_parse_valid_context(self):
        body = """
        ## Work Tree Context
        ### Application
        - [x] genesis
        ### Work Tree Type
        - [x] feature
        ### Async Safety Level
        - [x] safe
        """
        result = parse_work_tree_context(body)
        assert result["app_name"] == "genesis"
        assert result["work_tree_type"] == "feature"
        assert result["async_safety"] == "safe"

    def test_parse_missing_context(self):
        body = "No work tree context here"
        result = parse_work_tree_context(body)
        assert result["app_name"] is None
        assert result["async_safety"] == "safe"  # Default

class TestGenerateWorktreeName:
    def test_valid_name_generation(self):
        name = generate_worktree_name(
            issue_number=142,
            issue_title="Add dark mode toggle",
            work_tree_type="feature"
        )
        assert name == "feature-142-add-dark-mode-toggle"

    def test_max_length_enforcement(self):
        name = generate_worktree_name(
            issue_number=999,
            issue_title="This is an extremely long issue title that should be truncated",
            work_tree_type="refactor"
        )
        assert len(name) <= 50

class TestAssignWorkTreePort:
    def test_genesis_port_assignment(self):
        port = assign_work_tree_port("genesis", work_tree_index=1)
        assert port == 3102  # 3002 + 100

    def test_optimus_port_assignment(self):
        port = assign_work_tree_port("optimus", work_tree_index=2)
        assert port == 3250  # 3050 + 200

    def test_invalid_app_raises_error(self):
        with pytest.raises(ValueError):
            assign_work_tree_port("scribemaster")

class TestGetAppBasePort:
    def test_all_apps_have_ports(self):
        apps_with_ports = [
            "genesis", "optimus", "popkit", "reseller-central",
            "consensus", "daniel-son", "runtheworld", "aiproxy"
        ]
        for app in apps_with_ports:
            port = get_app_base_port(app)
            assert port is not None
            assert port > 0
```

### 3.2: Integration Tests

**File:** `apps/popkit/packages/plugin/tests/test_popkit_dev_work_integration.py`

```python
@pytest.mark.integration
class TestPopkitDevWorkIntegration:
    """Test /popkit:dev work #N with work tree creation."""

    def test_work_tree_creation_for_feature(self, github_api, temp_repo):
        """Test complete feature work tree creation."""
        # Create mock issue
        issue = {
            "number": 142,
            "title": "Add dark mode toggle",
            "body": """
## Work Tree Context
### Application
- [x] genesis
### Work Tree Type
- [x] feature
### Async Safety Level
- [x] safe

## PopKit Guidance
### Power Mode
- [ ] Recommended
- [x] Not Needed
            """,
            "labels": ["enhancement"]
        }

        # Execute: /popkit:dev work #142
        result = simulate_popkit_dev_work(issue)

        # Verify
        assert result["success"] is True
        assert result["work_tree_created"] is True
        assert result["work_tree_name"] == "feature-142-add-dark-mode-toggle"
        assert result["port_assigned"] == 3102
        assert result["state_tracked"] is True

        # Verify work tree exists
        assert Path(".worktrees/feature-142-add-dark-mode-toggle").exists()

        # Verify .env.local created
        env_file = Path(".worktrees/feature-142-add-dark-mode-toggle/.env.local")
        assert env_file.exists()
        assert "PORT=3102" in env_file.read_text()
```

### 3.3: Manual Testing Checklist

**Scenario 1: Simple Feature**
```bash
# [ ] Create issue #150 "Add dark mode"
/popkit:issue create "Add dark mode"
# [ ] Select: genesis, feature, safe

# [ ] Work on it
/popkit:dev work #150

# [ ] Verify:
# - [ ] Work tree created: .worktrees/feature-150-add-dark-mode/
# - [ ] Port assigned: 3102
# - [ ] .env.local exists with PORT=3102
# - [ ] Branch created: feature/150-add-dark-mode
# - [ ] Workflow executed
# - [ ] On completion: Work tree cleaned up
```

**Scenario 2: Power Mode Feature**
```bash
# [ ] Create issue #151 "Add authentication"
/popkit:issue create "Add authentication"
# [ ] Select: genesis, feature, safe, Complexity: large
# [ ] Power Mode: Recommended

# [ ] Work with Power Mode
/popkit:dev work #151 -p

# [ ] Verify:
# - [ ] Main work tree created
# - [ ] 3 agent sub-work-trees created
# - [ ] Ports assigned: 3102, 3103, 3104
# - [ ] Agents execute in parallel
# - [ ] On completion: All work trees cleaned up, merged properly
```

**Scenario 3: Multi-App Epic**
```bash
# [ ] Create epic issue #152 "Refactor auth"
/popkit:issue create "Refactor auth system"
# [ ] Select: genesis, optimus, popkit (multiple apps)
# [ ] Type: refactor
# [ ] Safety: requires-lock

# [ ] Work on it
/popkit:dev work #152

# [ ] Verify:
# - [ ] Main work tree created
# - [ ] State file tracks multi-app coordination
# - [ ] Can reference/update types across apps
```

---

## Phase 4: Deployment & Documentation ⏳ READY

### 4.1: Update Release Notes

**File:** `apps/popkit/CHANGELOG.md`

```markdown
## [Unreleased]

### Added
- **Work Tree Integration**: `/popkit:dev work #N` now automatically creates and manages git work trees
  - Issue templates now include "Work Tree Context" section
  - Automatic port assignment prevents dev server conflicts
  - Power Mode agents work in isolated sub-work-trees
  - Automatic cleanup of stale work trees

- **New Documentation**:
  - `docs/WORK_TREE_STRATEGY.md` - Complete work tree strategy and best practices
  - `docs/POPKIT_WORK_INTEGRATION_GUIDE.md` - User-facing workflow guide

### Changed
- `github_issues.py` - Enhanced to parse Work Tree Context
- `/popkit:dev work` command - Now handles work tree creation automatically
- Issue templates - Updated with new Work Tree Context section

### See Also
- GitHub Issue #39: Work Tree Integration
```

### 4.2: Update Main README

**File:** `apps/popkit/README.md`

Add to Quick Start section:

```markdown
### Issue-Driven Development with Work Trees

All work is organized around GitHub issues with automatic work tree management:

```bash
# Create an issue with Work Tree Context
/popkit:issue create "Add real-time notifications"

# Work on it (PopKit handles all setup/cleanup)
/popkit:dev work #150

# PopKit automatically:
# ✅ Creates isolated work tree
# ✅ Assigns dev server port
# ✅ Sets up environment
# ✅ Executes workflow
# ✅ Cleans up on completion
```

See [Work Tree Strategy](docs/WORK_TREE_STRATEGY.md) for detailed guide.
```

---

## Implementation Timeline

### Week 1: Parser & Functions
- [ ] Implement `parse_work_tree_context()` function
- [ ] Implement `generate_worktree_name()` function
- [ ] Implement `assign_work_tree_port()` functions
- [ ] Write unit tests
- [ ] **Estimate: 2-3 hours**

### Week 2: Work Tree Creation
- [ ] Add work tree creation to `/popkit:dev work` command
- [ ] Implement environment setup (.env.local, npm install, etc.)
- [ ] Implement state tracking (.claude/popkit/work-tree-state.json)
- [ ] Write integration tests
- [ ] **Estimate: 3-4 hours**

### Week 3: Power Mode Integration
- [ ] Update Power Mode coordinator for work tree isolation
- [ ] Implement sub-work-tree creation for parallel agents
- [ ] Implement merge-back coordination
- [ ] Write integration tests
- [ ] **Estimate: 3-4 hours**

### Week 4: Testing & Polish
- [ ] Manual testing of all scenarios
- [ ] Fix edge cases
- [ ] Update documentation
- [ ] Release preparation
- [ ] **Estimate: 2-3 hours**

**Total: ~12-14 hours of development**

---

## Success Criteria

### Functional
- [ ] `/popkit:dev work #N` creates work tree automatically
- [ ] Port assignments are automatic and conflict-free
- [ ] Power Mode agents can work in parallel in isolated work trees
- [ ] Work trees are automatically cleaned up on completion
- [ ] State tracking works across sessions

### Quality
- [ ] Unit tests for all new functions (>90% coverage)
- [ ] Integration tests for end-to-end workflows
- [ ] Manual testing of 3 scenarios (feature, bug fix, epic)
- [ ] No regressions in existing PopKit functionality
- [ ] Clear error messages for edge cases

### Documentation
- [ ] Update CLAUDE.md with work tree section
- [ ] Update issue templates in all 10 apps
- [ ] Update changelog
- [ ] User-facing guide is clear and complete

---

## Known Limitations & Future Work

### Current Limitations
1. **Port conflicts across apps** - Voice Clone and AIProxy both use 8000
   - *Workaround:* Configure different ports in .env.local
   - *Future:* Automatic conflict detection and resolution

2. **Cross-app work trees** - Multi-app PRs need careful coordination
   - *Current approach:* Single work tree, multiple app changes
   - *Future:* Linked work trees with cross-app state tracking

3. **Power Mode max agents** - Limited to ~5-10 agents per batch
   - *Current:* Tier-dependent (native, redis, file-based modes)
   - *Future:* Vertical scaling with better coordination

### Future Enhancements
- [ ] Automatic port conflict detection
- [ ] Visual dashboard of active work trees
- [ ] Work tree performance monitoring
- [ ] Automatic work tree suggestions based on code changes
- [ ] Work tree templates for common patterns (feature, hotfix, etc.)
- [ ] Cross-IDE work tree synchronization

---

## Questions for Implementation

1. **Port Assignment Algorithm:**
   - Current: base + (index * 100)
   - Alternative: Use dynamic port discovery
   - **Decision: Use simple algorithm, allow override in .env**

2. **Work Tree Cleanup:**
   - Automatic on completion?
   - Prompt for manual approval?
   - **Decision: Automatic, with state tracking for recovery**

3. **Power Mode Batching:**
   - Fixed batch size?
   - Dynamic based on agents?
   - **Decision: Dynamic per-phase batching (discovery shared, implementation isolated)**

4. **State Persistence:**
   - JSON file (.claude/popkit/work-tree-state.json)?
   - SQLite database?
   - **Decision: JSON for simplicity, git-tracked in .claude/**

---

**Created:** 2025-12-20
**Status:** Ready for Implementation
**Owner:** Claude Code
**Related Issues:** #39 (Work Tree Integration)
