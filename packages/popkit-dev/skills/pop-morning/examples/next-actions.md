# Next Actions (The PopKit Way)

**CRITICAL**: Always end with AskUserQuestion to keep PopKit in control.

## Option 1: If services are down or sync needed (Score < 80)

```
What would you like to do next?
├─ Fix environment issues (Recommended)
│ └─ Start redis, pull 3 commits, etc.
├─ Start work anyway (skip setup)
├─ Review what changed overnight
└─ Other
```

## Option 2: If environment is healthy (Score >= 80)

```
Ready to code! What's your focus today?
├─ Work on highest priority issue
├─ Review open PRs (X pending)
├─ Continue yesterday's work: [last task]
└─ Other
```

## Option 3: If issues need triage

```
You have X issues needing attention. What would you like to do?
├─ Triage issues now (Recommended)
├─ Review issue #Y (highest priority)
├─ Skip triage, start coding
└─ Other
```

## Implementation

After generating the morning report, invoke AskUserQuestion based on score and context:

```python
# After generating report
questions = generate_next_action_questions(score, breakdown, state)
# Returns AskUserQuestion tool invocation

# Example output to Claude:
{
    "type": "ask_user_question",
    "questions": [{
        "question": "What would you like to do next?",
        "header": "Next Action",
        "multiSelect": false,
        "options": [
            {
                "label": "Fix environment issues (Recommended)",
                "description": "Start redis, sync with remote (3 commits behind)"
            },
            {
                "label": "Work on #42: Fix critical build blockers",
                "description": "Continue yesterday's work (highest priority)"
            },
            {
                "label": "Review open PRs",
                "description": "2 PRs waiting for review"
            }
        ]
    }]
}
```

## Why This Matters (The PopKit Way)

- ✅ Keeps PopKit in control of the workflow
- ✅ Forces intentional user decisions
- ✅ Enables context-aware next actions
- ✅ Prevents "report dump and done" anti-pattern
- ✅ Maintains continuous workflow loop

**Never just show a report and end the session!**
