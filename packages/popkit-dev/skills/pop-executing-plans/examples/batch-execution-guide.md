# Batch Execution Guide

## The Process

### Step 1: Load and Review Plan

1. Read plan file (supports Markdown and PDF)
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Batch

**Default batch size: First 3 tasks**

For each task:

1. Mark as in_progress in TodoWrite
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed in TodoWrite

### Step 3: Report and Get Feedback

When batch complete, use AskUserQuestion:

```
question: "Batch complete. How should I proceed?"
header: "Feedback"
options:
  - label: "Continue"
    description: "Looks good, proceed to next batch"
  - label: "Revise"
    description: "I have feedback on this batch first"
  - label: "Pause"
    description: "Stop here, I'll review more carefully"
multiSelect: false
```

Show:

- What was implemented
- Verification output
- Any issues encountered

### Step 4: Continue Based on Feedback

**If "Continue"**: Execute next batch (repeat Step 2)

**If "Revise"**:

- Wait for user feedback
- Apply changes to current batch
- Re-run verifications
- Then continue

**If "Pause"**:

- Stop execution
- Save progress via pop-session-capture
- Preserve current state for later resumption

### Step 5: Complete Development

After all tasks complete and verified:

1. Announce: "I'm using the finishing-a-development-branch skill to complete this work."
2. Use pop-finishing-a-development-branch skill
3. Follow that skill's workflow

### Step 6: Next Action Loop (CRITICAL - Issue #118)

**ALWAYS present next actions after completion:**

```
question: "What would you like to do next?"
header: "Next Action"
options:
  - label: "Work on another issue"
    description: "Continue with another GitHub issue"
  - label: "Run tests/checks"
    description: "Run test suite or quality checks"
  - label: "Session capture and exit"
    description: "Save state for later continuation"
multiSelect: false
```

**NEVER end execution without presenting next step options.**

If user selects "Work on another issue":

```bash
gh issue list --state open --milestone v1.0.0 --json number,title,labels --limit 5
```

Then present specific issue options via AskUserQuestion.

## When to Stop and Ask for Help

**STOP executing immediately when:**

- Hit a blocker mid-batch (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**

- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.
