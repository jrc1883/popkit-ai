# Next Action Example

After completing a branch (via Options 1 or 2), present context-aware next actions:

```
Use AskUserQuestion tool with:
- question: "What would you like to do next?"
- header: "Next Action"
- options: [dynamically generated]
- multiSelect: false
```

## Generating Options

1. Fetch prioritized issues:

   ```bash
   gh issue list --state open --milestone v1.0.0 --json number,title,labels --limit 5
   ```

2. Sort by: P1 > P2 > P3, then phase:now > phase:next

3. Build 4 options:
   - Top 3 prioritized issues as "Work on #N: [title]"
   - "Session capture and exit" as final option

## Example Output

```
What would you like to do next?

1. Work on #108: Power Mode Metrics (P1-high)
   → Continue v1.0.0 milestone work

2. Work on #109: QStash Pub/Sub (P2-medium)
   → Add inter-agent messaging

3. Work on #93: Multi-Project Dashboard (P2-medium)
   → Build project visibility

4. Session capture and exit
   → Save state for later
```

**If user selects an issue**, immediately invoke `/popkit:dev work #N`.
