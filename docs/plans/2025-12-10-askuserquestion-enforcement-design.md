# AskUserQuestion Enforcement Design

**Issue:** #159
**Date:** 2025-12-10
**Status:** Ready for Implementation

## Problem Statement

Skills document AskUserQuestion decision points in their SKILL.md files, but agents don't reliably invoke them. This creates inconsistent UX where sometimes users get prompted for decisions and sometimes they don't.

Per Anthropic's Hooks Guide:
> "By encoding these rules as hooks rather than prompting instructions, you turn suggestions into app-level code that executes every time."

## Architecture Decision

**Store skill decisions in `agents/config.json`** under a new `skill_decisions` key.

### Why config.json (not YAML in SKILL.md)?

| Factor | config.json | YAML in SKILL.md |
|--------|-------------|------------------|
| Performance | No file I/O in hot path | Parse YAML on each invocation |
| Privacy | Stays private | SKILL.md goes public |
| Pattern | Follows existing config patterns | New pattern to maintain |
| Single source | Centralized | Scattered across skills |

## Design Details

### Trigger Types (Simplified)

Only two trigger types are enforced:

1. **`start`** - Before skill execution begins
2. **`completion`** - Before skill can complete successfully

Optional mid-flow decisions are left to skill implementations to handle contextually.

### Config Schema

```json
{
  "skill_decisions": {
    "description": "Required AskUserQuestion decision points per skill",
    "enforcement": "require",
    "skills": {
      "pop-project-init": {
        "completion_decisions": [
          {
            "id": "next_action",
            "question": "Project initialized. What would you like to do next?",
            "header": "Next Step",
            "options": [
              {"label": "Analyze codebase", "description": "Run /popkit:project analyze"},
              {"label": "Setup quality gates", "description": "Run /popkit:project setup"},
              {"label": "View issues", "description": "Run /popkit:issue list"},
              {"label": "Done for now", "description": "I'll explore on my own"}
            ]
          }
        ]
      },
      "pop-brainstorming": {
        "completion_decisions": [
          {
            "id": "implementation_choice",
            "question": "Design complete. Would you like to continue to implementation?",
            "header": "Next Step",
            "options": [
              {"label": "Create plan", "description": "Use pop-writing-plans to create detailed plan"},
              {"label": "Create worktree", "description": "Set up isolated workspace first"},
              {"label": "Done for now", "description": "I'll review the design first"}
            ]
          }
        ]
      }
    }
  }
}
```

### Implementation Components

#### 1. `hooks/utils/skill_state.py`

```python
class SkillStateTracker:
    """Tracks active skill and whether required decisions were made."""

    def __init__(self):
        self.active_skill: Optional[str] = None
        self.decisions_made: Set[str] = set()
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load skill_decisions from config.json."""
        config_path = Path(__file__).parent.parent.parent / "agents" / "config.json"
        if config_path.exists():
            return json.loads(config_path.read_text()).get("skill_decisions", {})
        return {}

    def start_skill(self, skill_name: str):
        """Called when a skill is invoked."""
        self.active_skill = skill_name
        self.decisions_made.clear()

    def record_decision(self, decision_id: str):
        """Called when AskUserQuestion is used."""
        self.decisions_made.add(decision_id)

    def get_pending_completion_decisions(self) -> List[dict]:
        """Get completion decisions not yet made."""
        if not self.active_skill:
            return []

        skill_config = self.config.get("skills", {}).get(self.active_skill, {})
        completion_decisions = skill_config.get("completion_decisions", [])

        return [d for d in completion_decisions if d["id"] not in self.decisions_made]

    def end_skill(self):
        """Called when skill completes."""
        self.active_skill = None
        self.decisions_made.clear()
```

#### 2. `hooks/pre-tool-use.py` Integration

```python
def check_skill_completion_decisions(self, tool_name: str) -> dict:
    """Check if skill has pending completion decisions before allowing completion."""

    # Only check on tools that indicate completion (Write to final file, etc.)
    # For now, check when returning to parent agent
    if tool_name in ["Task"]:  # Task tool means spawning another agent
        return {"requires_decision": False}

    tracker = get_skill_tracker()
    pending = tracker.get_pending_completion_decisions()

    if pending:
        first_pending = pending[0]
        return {
            "requires_decision": True,
            "decision_id": first_pending["id"],
            "question": first_pending["question"],
            "header": first_pending.get("header", "Decision"),
            "options": first_pending["options"]
        }

    return {"requires_decision": False}
```

#### 3. `hooks/post-tool-use.py` Integration

```python
def track_ask_user_question(self, tool_name: str, tool_output: dict):
    """Record when AskUserQuestion is used."""
    if tool_name == "AskUserQuestion":
        tracker = get_skill_tracker()
        # Extract decision ID from the question or header
        questions = tool_output.get("questions", [])
        if questions:
            header = questions[0].get("header", "")
            # Map header to decision ID
            tracker.record_decision(header.lower().replace(" ", "_"))
```

### Enforcement Flow

```
1. Skill tool invoked → start_skill("pop-project-init")
2. Skill executes, makes various tool calls
3. Agent tries to complete (stop responding)
4. post-tool-use checks pending_completion_decisions
5. If pending → inject reminder message
6. Agent must call AskUserQuestion with matching question
7. AskUserQuestion recorded → decision marked complete
8. Skill can complete
```

## Migration Path

### Phase 1: Core Skills (This PR)

Add `completion_decisions` for:
- `pop-project-init` - "What would you like to do next?"
- `pop-brainstorming` - "Continue to implementation?"
- `pop-writing-plans` - "Ready to execute?"
- `pop-executing-plans` - "Implementation complete. What's next?"
- `pop-finish-branch` - "How would you like to integrate?"

### Phase 2: Rollout

Add to remaining skills as needed based on usage patterns.

## Testing

1. **Unit tests** for `skill_state.py` tracking logic
2. **Integration test**: Invoke skill, verify completion blocked without decision
3. **E2E test on Daniel-Son**: Run `/popkit:project init`, verify prompts appear

## Files Changed

| File | Change |
|------|--------|
| `packages/plugin/agents/config.json` | Add `skill_decisions` section |
| `packages/plugin/hooks/utils/skill_state.py` | New file - state tracking |
| `packages/plugin/hooks/pre-tool-use.py` | Import and use skill tracker |
| `packages/plugin/hooks/post-tool-use.py` | Track AskUserQuestion calls |
| `CLAUDE.md` | Document the enforcement mechanism |

## Version Impact

This is a **minor version bump** (1.1.x → 1.2.0) because:
- New feature (enforcement mechanism)
- No breaking changes to existing behavior
- Backward compatible (skills without decisions work as before)
