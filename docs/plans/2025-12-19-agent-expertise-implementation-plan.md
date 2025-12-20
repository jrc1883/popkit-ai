# Agent Expertise System - Implementation Plan (Phases 2-3)

> **For Claude:** Use `/popkit:dev execute` to implement this plan.

**Date:** 2025-12-19
**Issue:** #201
**Architecture:** See `2025-12-19-agent-expertise-system-architecture.md`

**Status:** Phase 1 complete ✅, Phases 2-3 pending

---

## Phase 1 Status (Complete)

✅ session-start.py: Added `ensure_pattern_learner_directories()` (creates Tier 1-3 directories)
✅ research_surfacer.py: Fixed import on line 117 (`from .research_index`)
✅ /popkit:research command: Already exists with full documentation
⏳ pop-research-manage skill: Not critical for Phase 2, defer to Phase 3

---

## Phase 2: Per-Agent Expertise System

**Goal:** Add YAML-based expertise files for agents with conservative 3+ occurrence threshold.

**Pilot Agents:** code-reviewer, bug-whisperer, security-auditor

---

### Task 1: Create expertise_manager.py

**File:** `packages/plugin/hooks/utils/expertise_manager.py`

**Architecture Reference:** Lines 552-1106 of architecture document

**Components:**

1. **Data Classes** (lines 588-693):
   - PatternExample
   - Pattern
   - Issue
   - ExpertiseFile

2. **PendingPatternsTracker** (lines 697-795):
   - Tracks occurrences before promotion
   - Requires 3+ occurrences
   - Storage: `.claude/expertise/{agent-id}/pending.json`

3. **ExpertiseManager** (lines 799-1082):
   - Load/create expertise YAML
   - Record pattern occurrences
   - Promote patterns when threshold met
   - Add preferences and common issues
   - Update statistics
   - Cleanup old patterns

**Step 1: Write test file first**

Create `packages/plugin/tests/hooks/test_expertise_manager.py`:

```python
#!/usr/bin/env python3
"""Tests for expertise_manager.py"""

import unittest
import tempfile
import shutil
from pathlib import Path
import yaml
import json

# Add utils to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks" / "utils"))

from expertise_manager import (
    ExpertiseManager,
    PendingPatternsTracker,
    Pattern,
    Issue,
    PatternExample,
    MIN_OCCURRENCES
)


class TestExpertiseManager(unittest.TestCase):
    def setUp(self):
        """Create temp directory for each test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.agent_id = "code-reviewer"
        self.manager = ExpertiseManager(self.agent_id, self.temp_dir)

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir)

    def test_creates_expertise_file(self):
        """Test that expertise file is created"""
        expertise_file = self.temp_dir / ".claude" / "expertise" / self.agent_id / "expertise.yaml"
        self.assertTrue(expertise_file.exists())

    def test_requires_three_occurrences(self):
        """Test that patterns require 3+ occurrences before promotion"""
        # Record pattern twice
        result1 = self.manager.record_pattern_occurrence(
            category="code-style",
            pattern="prefer async/await",
            trigger="callback hell detected"
        )
        self.assertIsNone(result1)  # Not promoted yet

        result2 = self.manager.record_pattern_occurrence(
            category="code-style",
            pattern="prefer async/await",
            trigger="callback hell detected"
        )
        self.assertIsNone(result2)  # Still not promoted

        # Third occurrence should promote
        result3 = self.manager.record_pattern_occurrence(
            category="code-style",
            pattern="prefer async/await",
            trigger="callback hell detected"
        )
        self.assertIsNotNone(result3)  # Now promoted!
        self.assertIsInstance(result3, Pattern)
        self.assertEqual(result3.occurrences, 3)

    def test_adds_preference(self):
        """Test adding preferences"""
        self.manager.add_preference("code_style", "use 2-space indentation")

        expertise = self.manager.expertise
        self.assertIn("code_style", expertise.preferences)
        self.assertIn("use 2-space indentation", expertise.preferences["code_style"])

    def test_records_issue(self):
        """Test recording common issues"""
        issue = self.manager.record_issue(
            pattern="missing null checks",
            severity="medium",
            solution="add optional chaining",
            file_path="src/api/users.ts"
        )

        self.assertIsNotNone(issue)
        self.assertEqual(issue.pattern, "missing null checks")
        self.assertEqual(issue.severity, "medium")


if __name__ == '__main__':
    unittest.main()
```

**Run:** `python packages/plugin/tests/hooks/test_expertise_manager.py`
**Expected:** ALL FAIL (file doesn't exist yet)

**Step 2: Create minimal expertise_manager.py**

Copy implementation from architecture document lines 552-1106:
- All imports
- Configuration constants (lines 576-584)
- Data classes (lines 588-693)
- PendingPatternsTracker class (lines 697-795)
- ExpertiseManager class (lines 799-1082)
- Helper functions (lines 1087-1106)

**Step 3: Run test to verify it passes**

**Run:** `python packages/plugin/tests/hooks/test_expertise_manager.py`
**Expected:** ALL PASS

**Step 4: Commit**

```bash
git add packages/plugin/hooks/utils/expertise_manager.py packages/plugin/tests/hooks/test_expertise_manager.py
git commit -m "feat(expertise): add expertise_manager.py with 3+ occurrence threshold

- Creates YAML expertise files per agent
- PendingPatternsTracker requires 3 occurrences before promotion
- Supports patterns, preferences, common issues
- Conservative update logic
- Full test coverage

Part of Issue #201 (Agent Expertise System)"
```

---

### Task 2: Integrate expertise loading into session-start.py

**File:** `packages/plugin/hooks/session-start.py`

**Architecture Reference:** Lines 1108-1165 of architecture document

**Step 1: Add load_agent_expertise() function**

After the `ensure_pattern_learner_directories()` function (around line 303), add:

```python
def load_agent_expertise():
    """Load expertise files for relevant agents.

    This is non-blocking - any errors are silently ignored.

    Returns:
        dict: Loaded expertise info, or None on error
    """
    try:
        from utils.expertise_manager import ExpertiseManager

        cwd = Path(os.getcwd())
        expertise_dir = cwd / ".claude" / "expertise"

        if not expertise_dir.exists():
            return None

        loaded = []
        for agent_dir in expertise_dir.iterdir():
            if agent_dir.is_dir():
                expertise_file = agent_dir / "expertise.yaml"
                if expertise_file.exists():
                    agent_id = agent_dir.name
                    manager = ExpertiseManager(agent_id, cwd)
                    summary = manager.get_summary()
                    loaded.append({
                        'agent_id': agent_id,
                        'patterns': summary['total_patterns'],
                        'preferences': summary['total_preferences'],
                    })

        if loaded:
            print(f"Agent expertise loaded: {len(loaded)} agents", file=sys.stderr)
            return {'agents': loaded}

        return None

    except Exception:
        pass  # Silent failure

    return None
```

**Step 2: Call in main()**

After line 392 (agent loading), add:

```python
# Load agent expertise files (Phase 2, non-blocking)
expertise_loading = load_agent_expertise()
```

**Step 3: Add to response**

After line 423 (agent_loading response), add:

```python
# Include expertise loading info if available (Issue #201, Phase 2)
if expertise_loading:
    response["expertise_loading"] = expertise_loading
```

**Step 4: Test**

Run session-start hook manually:

```bash
echo '{}' | python packages/plugin/hooks/session-start.py
```

**Expected output (stderr):**
```
Learning systems initialized: directories: 4, research index
Session started - hooks system active
```

**Expected output (stdout JSON):**
```json
{
  "status": "success",
  "learning_init": {
    "directories_created": [...],
    "index_created": true
  }
}
```

**Step 5: Commit**

```bash
git add packages/plugin/hooks/session-start.py
git commit -m "feat(expertise): integrate expertise loading into session-start

- Loads expertise files for all agents
- Non-blocking, silent failures
- Reports loaded agent count to stderr
- Includes in session response

Part of Issue #201 (Agent Expertise System)"
```

---

### Task 3: Add expertise updates to post-tool-use.py

**File:** `packages/plugin/hooks/post-tool-use.py`

**Architecture Reference:** Lines 1167-1230 of architecture document

**Step 1: Add update_agent_expertise() method**

Add method to `PostToolUseHook` class (around line 200):

```python
def update_agent_expertise(self, tool_name: str, tool_input: dict, tool_output: str):
    """Update agent expertise based on tool usage.

    This is the self-improvement mechanism.
    Looks for patterns in tool results and records them.

    Part of Agent Expertise System (Issue #201).
    """
    try:
        from utils.expertise_manager import ExpertiseManager, PatternExample

        # Determine which agent is active
        # (This would come from context or agent routing)
        agent_id = os.environ.get('POPKIT_ACTIVE_AGENT')
        if not agent_id:
            return  # No active agent

        manager = ExpertiseManager(agent_id)

        # Pattern detection logic
        # Example: code-reviewer notices repeated issue
        if agent_id == 'code-reviewer':
            # Look for common review comments
            if 'missing error handling' in tool_output.lower():
                manager.record_pattern_occurrence(
                    category='error-handling',
                    pattern='wrap async functions in try/catch',
                    trigger='unhandled promise rejection',
                    file_path=tool_input.get('file_path'),
                )

            if 'console.log' in tool_output:
                manager.record_pattern_occurrence(
                    category='code-style',
                    pattern='remove console.log from production',
                    trigger='console.log detected in code',
                    file_path=tool_input.get('file_path'),
                )

        # Example: security-auditor notices patterns
        elif agent_id == 'security-auditor':
            if 'password' in tool_output.lower() and 'log' in tool_output.lower():
                manager.record_issue(
                    pattern='logging sensitive data',
                    severity='high',
                    solution='remove password from log statements',
                    file_path=tool_input.get('file_path'),
                )

    except Exception:
        pass  # Silent failure - never block on expertise updates
```

**Step 2: Call in process()**

After processing tool use (around line 200), add:

```python
# Update agent expertise (Issue #201, Phase 2, non-blocking)
self.update_agent_expertise(tool_name, tool_input, tool_output)
```

**Step 3: Test**

Create test scenario:

```bash
# Set active agent
export POPKIT_ACTIVE_AGENT=code-reviewer

# Simulate tool use with pattern trigger
echo '{
  "tool_name": "Read",
  "tool_input": {"file_path": "src/api/auth.ts"},
  "tool_output": "Found console.log statement"
}' | python packages/plugin/hooks/post-tool-use.py
```

**Expected:**
- pending.json created with 1 occurrence
- After 3 tool uses with same pattern → promoted to expertise.yaml

**Step 4: Commit**

```bash
git add packages/plugin/hooks/post-tool-use.py
git commit -m "feat(expertise): add self-improvement to post-tool-use hook

- Detects patterns in tool output
- Records occurrences for pilot agents
- Promotes to expertise after 3+ occurrences
- Silent failures, non-blocking

Pilot agents: code-reviewer, security-auditor

Part of Issue #201 (Agent Expertise System)"
```

---

## Phase 3: Integration and Metrics

**Goal:** Add metrics visualization and management commands.

---

### Task 4: Add metrics to /popkit:stats

**File:** `packages/plugin/skills/pop-stats-display/SKILL.md`

**Step 1: Read current stats skill**

```bash
cat packages/plugin/skills/pop-stats-display/SKILL.md
```

**Step 2: Add learning systems metrics section**

After existing metrics, add new section:

```markdown
## Learning Systems Stats

Display statistics for the three-tier learning system.

### Tier 1: Global Patterns

```bash
# Check if command_patterns.db exists
if [ -f ~/.claude/config/command_patterns.db ]; then
  sqlite3 ~/.claude/config/command_patterns.db "SELECT COUNT(*) FROM patterns"
  sqlite3 ~/.claude/config/command_patterns.db "SELECT AVG(confidence) FROM patterns"
fi
```

### Tier 2: Research Index

```python
import json
from pathlib import Path

research_index = Path(".claude/research/index.json")
if research_index.exists():
    data = json.loads(research_index.read_text())
    print(f"Total entries: {len(data.get('entries', []))}")
    print(f"Decisions: {data['metadata']['entry_types']['decision']}")
    print(f"Findings: {data['metadata']['entry_types']['finding']}")
```

### Tier 3: Agent Expertise

```python
from pathlib import Path
import yaml

expertise_dir = Path(".claude/expertise")
if expertise_dir.exists():
    for agent_dir in expertise_dir.iterdir():
        if agent_dir.is_dir():
            expertise_file = agent_dir / "expertise.yaml"
            if expertise_file.exists():
                data = yaml.safe_load(expertise_file.read_text())
                print(f"{data['agent_id']}: {data['stats']['total_patterns']} patterns")
```

### Output Format

```
┌─────────────────────────────────────────────────────────┐
│                  LEARNING SYSTEMS STATS                  │
├─────────────────────────────────────────────────────────┤
│ Global Patterns (Tier 1)                                │
│   Total corrections: 156                                │
│   Success rate: 87%                                     │
│   Last learning: 2 hours ago                            │
│                                                          │
│ Research Index (Tier 2)                                 │
│   Total entries: 42                                     │
│   Decisions: 15  Findings: 12                           │
│   Learnings: 8   Spikes: 7                              │
│   Auto-surfaced: 23 times                               │
│                                                          │
│ Agent Expertise (Tier 3)                                │
│   code-reviewer:    18 patterns, 34 preferences         │
│   bug-whisperer:    12 patterns, 21 preferences         │
│   security-auditor: 15 patterns, 29 preferences         │
└─────────────────────────────────────────────────────────┘
```
```

**Step 3: Test**

```bash
/popkit:stats
```

**Expected:** See learning systems section if any data exists

**Step 4: Commit**

```bash
git add packages/plugin/skills/pop-stats-display/SKILL.md
git commit -m "feat(expertise): add learning systems metrics to /popkit:stats

- Shows Tier 1 (global patterns) stats
- Shows Tier 2 (research index) stats
- Shows Tier 3 (agent expertise) stats
- Cross-tier flow metrics

Part of Issue #201 (Agent Expertise System)"
```

---

### Task 5: Create /popkit:expertise command

**File:** `packages/plugin/commands/expertise.md`

**Step 1: Create command file**

```markdown
---
name: expertise
category: Development
description: Manage agent expertise files and patterns
usage: |
  /popkit:expertise list [agent]        - List expertise for agent(s)
  /popkit:expertise show <agent>        - Show full expertise for agent
  /popkit:expertise export <agent>      - Export expertise to JSON
  /popkit:expertise clear <agent>       - Clear pending patterns
  /popkit:expertise stats               - Show expertise statistics
examples:
  - /popkit:expertise list
  - /popkit:expertise show code-reviewer
  - /popkit:expertise export security-auditor
---

# Expertise Management

Manage per-agent expertise files in the three-tier learning system.

## Commands

### List

```
/popkit:expertise list [agent]
```

Shows expertise summary for all agents (or specific agent).

**Output:**
```
Agent Expertise Summary:

| Agent | Patterns | Preferences | Issues | Last Updated |
|-------|----------|-------------|--------|--------------|
| code-reviewer | 18 | 34 | 5 | 2 hours ago |
| bug-whisperer | 12 | 21 | 3 | 1 day ago |
| security-auditor | 15 | 29 | 8 | 4 hours ago |
```

### Show

```
/popkit:expertise show <agent>
```

Display full expertise YAML for an agent.

### Export

```
/popkit:expertise export <agent>
```

Export expertise to JSON file for sharing or backup.

### Clear

```
/popkit:expertise clear <agent>
```

Clear pending patterns (patterns with < 3 occurrences).

### Stats

```
/popkit:expertise stats
```

Show detailed statistics across all agents.
```

**Step 2: Create skill**

**File:** `packages/plugin/skills/pop-expertise-manage/SKILL.md`

```markdown
---
name: pop-expertise-manage
category: Development
description: Manage agent expertise files
required_tools:
  - Read
  - Write
parameters:
  action:
    type: string
    description: Action (list|show|export|clear|stats)
  agent:
    type: string
    description: Agent ID (optional)
---

# Expertise Management Skill

Uses expertise_manager.py to manage agent expertise.

## Implementation

```python
from hooks.utils.expertise_manager import ExpertiseManager
from pathlib import Path

expertise_dir = Path(".claude/expertise")

if action == "list":
    # List all agents with expertise
    for agent_dir in expertise_dir.iterdir():
        if agent_dir.is_dir():
            manager = ExpertiseManager(agent_dir.name)
            summary = manager.get_summary()
            # Display summary

elif action == "show":
    # Show full expertise YAML
    manager = ExpertiseManager(agent)
    with open(expertise_file) as f:
        print(f.read())

elif action == "export":
    # Export to JSON
    manager = ExpertiseManager(agent)
    manager.export_json(Path(f"{agent}-expertise.json"))
```
```

**Step 3: Test**

```bash
/popkit:expertise list
/popkit:expertise show code-reviewer
```

**Step 4: Commit**

```bash
git add packages/plugin/commands/expertise.md packages/plugin/skills/pop-expertise-manage/
git commit -m "feat(expertise): add /popkit:expertise command

- List expertise for agents
- Show full expertise YAML
- Export to JSON
- Clear pending patterns
- Statistics display

Part of Issue #201 (Agent Expertise System)"
```

---

## Final Integration Testing

### Test 1: Directory Initialization

```bash
# Start new session
# Check directories created
ls -la .claude/
# Expected:
# .claude/research/
# .claude/expertise/
# ~/.claude/config/
```

### Test 2: Pattern Learning Flow

```bash
# Simulate 3 occurrences of same pattern
export POPKIT_ACTIVE_AGENT=code-reviewer

# First occurrence
# (simulate via hook or manual manager call)
# Expected: Recorded in pending.json

# Second occurrence
# Expected: Still in pending.json

# Third occurrence
# Expected: Promoted to expertise.yaml
```

### Test 3: Research Command

```bash
/popkit:research add decision "Use Upstash for Redis"
/popkit:research list
/popkit:research show dec-001
```

### Test 4: Expertise Command

```bash
/popkit:expertise list
/popkit:expertise show code-reviewer
# Expected: See patterns, preferences, stats
```

### Test 5: Stats Display

```bash
/popkit:stats
# Expected: See learning systems section
```

---

## Success Criteria

**Phase 2:**
- [ ] expertise_manager.py created with full tests
- [ ] Expertise files created on first agent use
- [ ] Patterns require 3+ occurrences before promotion
- [ ] session-start.py loads expertise files
- [ ] post-tool-use.py records pattern occurrences

**Phase 3:**
- [ ] /popkit:stats shows learning metrics
- [ ] /popkit:expertise command works
- [ ] Full integration test passes

**Overall:**
- [ ] No breaking changes to existing hooks
- [ ] Silent failures (never block session)
- [ ] Documentation updated
- [ ] Tests pass

---

## Rollback Plan

If issues arise:

```bash
# Revert session-start.py changes
git checkout HEAD~3 packages/plugin/hooks/session-start.py

# Revert post-tool-use.py changes
git checkout HEAD~2 packages/plugin/hooks/post-tool-use.py

# Remove expertise_manager.py
git rm packages/plugin/hooks/utils/expertise_manager.py
```

---

## Post-Implementation Tasks

1. Update CHANGELOG.md
2. Update issue #201 with status
3. Create GitHub release notes
4. Update documentation in CLAUDE.md
5. Announce in team chat (if applicable)

---

**END OF IMPLEMENTATION PLAN**
