---
name: pop-routine-measure
description: Measure context usage, duration, and tool breakdown during routine execution
invocation_pattern: "/popkit:routine (morning|nightly) --measure"
tier: 1
version: 1.0.0
---

# Routine Measurement

Tracks and reports context window usage, execution duration, tool call breakdown, and cost estimates during routine execution.

## When to Use

**CRITICAL**: This skill must be invoked AUTOMATICALLY when the user includes `--measure` flag in any `/popkit:routine` command:

```
/popkit:routine morning --measure
/popkit:routine morning run p-1 --measure
/popkit:routine nightly --measure
```

## How It Works

1. **Detect Flag**: Parse command for `--measure` flag
2. **Start Tracking**: Enable measurement via environment variable
3. **Initialize Tracker**: Start `RoutineMeasurementTracker`
4. **Execute Routine**: Run the routine normally (pk, p-1, etc.)
5. **Stop Tracking**: Collect measurement data
6. **Format Report**: Display detailed breakdown
7. **Save Data**: Store JSON for analysis

## Implementation Pattern

```python
import os
import sys
sys.path.insert(0, "packages/plugin/hooks/utils")

from routine_measurement import (
    RoutineMeasurementTracker,
    enable_measurement,
    disable_measurement,
    format_measurement_report,
    save_measurement
)

# 1. Enable measurement mode
enable_measurement()

# 2. Start tracker
tracker = RoutineMeasurementTracker()
tracker.start(routine_id="p-1", routine_name="PopKit Full Validation")

# 3. Execute routine
# Use Skill tool to invoke the actual routine
# Example: Skill(skill="pop-morning-routine", args="--routine p-1")

# 4. Stop tracker and get measurement
measurement = tracker.stop()

# 5. Disable measurement mode
disable_measurement()

# 6. Display report
if measurement:
    report = format_measurement_report(measurement)
    print(report)

    # Save measurement data
    saved_path = save_measurement(measurement)
    print(f"\nMeasurement data saved to: {saved_path}")
```

## Tool Call Tracking

The `post-tool-use.py` hook automatically tracks tool calls when `POPKIT_ROUTINE_MEASURE=true`:

- **Tracked Tools**: All tools (Bash, Read, Grep, Write, Edit, Skill, etc.)
- **Token Estimation**: ~4 chars per token (rough approximation)
- **Input/Output Split**: 20% input, 80% output (heuristic)
- **Duration**: Captured from hook execution time

## Output Format

```
======================================================================
Routine Measurement Report
======================================================================
Routine: PopKit Full Validation (p-1)
Duration: 12.34s
Tool Calls: 15

Context Usage:
  Input Tokens:  1,234 (~1k)
  Output Tokens: 6,789 (~6k)
  Total Tokens:  8,023 (~8k)
  Characters:    32,092

Cost Estimate (Claude Sonnet 4.5):
  Input:  $0.0037
  Output: $0.1018
  Total:  $0.1055

Tool Breakdown:
----------------------------------------------------------------------
Tool                 Calls    Tokens       Duration   Chars
----------------------------------------------------------------------
Bash                 8        3,456        2.34s      13,824
Read                 4        2,123        1.12s      8,492
Grep                 2        1,234        0.56s      4,936
Skill                1        1,210        8.32s      4,840
======================================================================
```

## Measurement Data Storage

Measurements are saved to `.claude/popkit/measurements/` as JSON:

```json
{
  "routine_id": "p-1",
  "routine_name": "PopKit Full Validation",
  "start_time": 1734567890.123,
  "end_time": 1734567902.456,
  "duration": 12.333,
  "total_tool_calls": 15,
  "total_tokens": 8023,
  "input_tokens": 1234,
  "output_tokens": 6789,
  "total_chars": 32092,
  "tool_breakdown": {
    "Bash": {
      "count": 8,
      "input_tokens": 691,
      "output_tokens": 2765,
      "duration": 2.34,
      "chars": 13824
    }
  },
  "cost_estimate": {
    "input": 0.0037,
    "output": 0.1018,
    "total": 0.1055
  }
}
```

## Usage Examples

### Measure Morning Routine (Default)

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

### Measure Specific Routine

```
User: /popkit:routine morning run pk --measure

Claude: I'll measure the universal PopKit routine.

[Measurement report shows metrics for pk routine]
```

### Compare Routines (Manual)

```bash
# Run each routine with --measure
/popkit:routine morning run pk --measure
/popkit:routine morning run p-1 --measure

# Compare JSON files
cat .claude/popkit/measurements/pk_*.json
cat .claude/popkit/measurements/p-1_*.json
```

## Integration

### Command Integration

The `commands/routine.md` documents the `--measure` flag. When Claude sees this flag:

1. **Invoke this skill** before executing the routine
2. **Wrap execution** with measurement tracking
3. **Display results** after routine completion

### Hook Integration

The `post-tool-use.py` hook checks for `POPKIT_ROUTINE_MEASURE=true`:

```python
if ROUTINE_MEASUREMENT_AVAILABLE and check_measure_flag():
    tracker = RoutineMeasurementTracker()
    if tracker.is_active():
        tracker.track_tool_call(tool_name, content, execution_time)
```

### Storage Location

```
.claude/popkit/measurements/
├── pk_20251219_080000.json       # Universal routine
├── p-1_20251219_143022.json      # Custom routine
└── rc-1_20251219_180000.json     # Project routine
```

## Metrics Collected

| Metric | Description | Source |
|--------|-------------|--------|
| **Duration** | Total execution time in seconds | Tracker start/stop |
| **Tool Calls** | Number of tools invoked | Hook tracking |
| **Input Tokens** | Estimated input tokens (~20% of total) | Content length / 4 |
| **Output Tokens** | Estimated output tokens (~80% of total) | Content length / 4 |
| **Total Tokens** | Input + Output | Sum |
| **Characters** | Raw character count | Content length |
| **Cost** | Estimated API cost (Sonnet 4.5 pricing) | Token count * price |

## Token Estimation

Uses rough heuristic: **~4 characters per token**

This is an approximation. Actual tokenization varies by:
- Language (code vs natural language)
- Repetition and patterns
- Special characters

For more accurate counts, use Claude API's token counting endpoint (future enhancement).

## Cost Calculation

Based on Claude Sonnet 4.5 pricing (as of Dec 2025):
- **Input:** $3.00 per million tokens
- **Output:** $15.00 per million tokens

Costs are **estimates only** - actual costs depend on caching, context reuse, and other factors.

## Future Enhancements

### Phase 2: Comparison Mode
```
/popkit:routine morning --measure --compare pk,p-1
```

### Phase 3: Trend Analysis
```
/popkit:routine morning --measure --trend 7d
```

### Phase 4: Optimization Suggestions
```
Tool breakdown shows Bash taking 60% of tokens.
Suggestion: Cache git status results to reduce redundant calls.
```

## Related Skills

| Skill | Purpose |
|-------|---------|
| `pop-morning-routine` | Execute morning routine |
| `pop-nightly-routine` | Execute nightly routine |
| `pop-routine-generator` | Create custom routines |
| `pop-assessment-performance` | Analyze performance metrics |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:routine` | Execute routines |
| `/popkit:assess performance` | Performance assessment |
| `/popkit:stats` | Session statistics |

## Architecture Files

| File | Purpose |
|------|---------|
| `hooks/utils/routine_measurement.py` | Measurement tracking classes |
| `hooks/post-tool-use.py` | Tool call capture hook |
| `commands/routine.md` | Command specification |
| `.claude/popkit/measurements/` | Measurement data storage |

## Testing

Test measurement functionality:

```bash
# Enable measurement manually
export POPKIT_ROUTINE_MEASURE=true

# Run a routine
/popkit:routine morning

# Verify measurement file created
ls -la .claude/popkit/measurements/

# Inspect JSON
cat .claude/popkit/measurements/*.json | jq '.'
```

---

**Version:** 1.0.0
**Author:** PopKit Development Team
**Last Updated:** 2025-12-19