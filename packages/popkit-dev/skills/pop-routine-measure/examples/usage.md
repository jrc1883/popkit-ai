# Usage Examples

## Measure Morning Routine (Default)

```
User: /popkit:routine morning --measure

Claude: I'll measure the context usage for your morning routine.

[Enables measurement and runs p-1 routine]
[Morning routine output displays normally]

======================================================================
Routine Measurement Report
======================================================================
Routine: PopKit Full Validation (p-1)
Duration: 12.34s
Tool Calls: 15
...

Measurement data saved to: .claude/popkit/measurements/p-1_20251219_143022.json
```

## Measure Specific Routine

```
User: /popkit:routine morning run pk --measure

Claude: I'll measure the universal PopKit routine.

[Measurement report shows metrics for pk routine]
```

## Compare Routines (Manual)

```bash
# Run each routine with --measure
/popkit:routine morning run pk --measure
/popkit:routine morning run p-1 --measure

# Compare JSON files
cat .claude/popkit/measurements/pk_*.json
cat .claude/popkit/measurements/p-1_*.json
```

## View Dashboard

```
User: show routine measurements

Claude: [Displays dashboard with latest measurement]

User: show measurements for morning routine

Claude: [Filters dashboard to morning routine measurements]

User: routine performance dashboard

Claude: [Shows full dashboard with trends and comparisons]
```
