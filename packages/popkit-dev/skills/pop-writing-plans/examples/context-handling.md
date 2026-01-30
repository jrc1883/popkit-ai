# Context Handling Examples

## Check Upstream Context

**BEFORE creating a plan**, check for context from previous skills:

```python
from popkit_shared.utils.skill_context import load_skill_context, get_artifact

# Check for design context from brainstorming
ctx = load_skill_context()

if ctx and ctx.previous_skill == "pop-brainstorming":
    # Use design document as input
    design_doc = get_artifact("design_document") or ctx.artifacts.get("design_document")
    topic = ctx.previous_output.get("topic")
    approach = ctx.previous_output.get("approach")

    # Don't re-ask decisions that were already made
    existing_decisions = ctx.shared_decisions

    print(f"Using design from brainstorming: {design_doc}")
    print(f"Topic: {topic}, Approach: {approach}")
else:
    # No upstream context - need to gather information
    # Check for existing design docs
    design_doc = None
```

## Save Context Output

```python
from popkit_shared.utils.skill_context import save_skill_context, SkillOutput, link_workflow_to_issue

# Save plan context for executing-plans or subagent-driven
save_skill_context(SkillOutput(
    skill_name="pop-writing-plans",
    status="completed",
    output={
        "plan_file": "docs/plans/YYYY-MM-DD-<feature>.md",
        "task_count": <number of tasks>,
        "github_issue": <issue number if created>
    },
    artifacts=["docs/plans/YYYY-MM-DD-<feature>.md"],
    next_suggested="pop-executing-plans",
    decisions_made=[<list of AskUserQuestion results>]
))

# Link to GitHub issue
if issue_number:
    link_workflow_to_issue(issue_number)
```

## GitHub Issue Creation

```bash
# Search for existing issue
gh issue list --search "<topic>" --state open --json number,title --limit 5

# Create issue with plan summary
gh issue create --title "[Feature] <topic>" --body "$(cat <<'EOF'
## Summary
<brief description>

## Implementation Plan
See: `docs/plans/YYYY-MM-DD-<feature>.md`

## Tasks
- [ ] Task 1
- [ ] Task 2
...

---
*Plan created by PopKit*
EOF
)"
```
