---
name: pop-routine-measure
description: Display routine measurement dashboard with metrics, costs, trends, and visualization
invocation_pattern: "/popkit:routine (morning|nightly) --measure|show routine measurements|routine performance|routine metrics dashboard"
tier: 1
version: 1.1.0
---

# Routine Measurement Dashboard

Tracks, visualizes, and reports context window usage, execution duration, tool call breakdown, and cost estimates during routine execution.

## When to Use

**Primary Use Cases:**

1. **Auto-Measurement**: Invoked AUTOMATICALLY when user includes `--measure` flag in `/popkit:routine` commands
2. **Dashboard Display**: Invoked when user requests viewing existing measurements
3. **Trend Analysis**: Invoked when comparing measurements across multiple runs

```bash
# Auto-measurement during routine execution
/popkit:routine morning --measure
/popkit:routine morning run p-1 --measure
/popkit:routine nightly --measure

# Viewing existing measurements
show routine measurements
show measurements for morning routine
routine performance dashboard
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

## Metrics Collected

See [examples/metrics-reference.md](examples/metrics-reference.md) for complete metrics documentation.

**Key metrics:**
- Duration (total execution time)
- Tool calls (count per tool type)
- Token usage (input/output split with ~4 chars/token estimation)
- Cost estimates (Claude Sonnet 4.5 pricing: $3/million input, $15/million output)
- Character counts (raw content length)

## Measurement Data

See [examples/data-format.md](examples/data-format.md) for complete JSON schema.

Measurements saved to `.claude/popkit/measurements/{routine_id}_{YYYYMMDD}_{HHMMSS}.json`

**Key fields:**
- `routine_id`, `routine_name`: Routine identification
- `duration`, `start_time`, `end_time`: Timing data
- `total_tokens`, `input_tokens`, `output_tokens`: Token counts
- `tool_breakdown`: Per-tool statistics
- `cost_estimate`: Estimated API costs

## Usage Examples

See [examples/usage.md](examples/usage.md) for complete usage scenarios.

**Quick examples:**
```bash
# Measure default morning routine
/popkit:routine morning --measure

# Measure specific routine
/popkit:routine morning run pk --measure

# View dashboard
show routine measurements
```

## Dashboard Visualization (NEW in v1.1.0)

See [examples/dashboard-implementation.md](examples/dashboard-implementation.md) for complete Python implementation.

**Dashboard features:**
- Summary metrics (duration, tokens, cost)
- Token usage breakdown (input/output split with percentages)
- Tool breakdown table (calls, tokens, duration per tool)
- Comparison with previous run (trend indicators)
- Aggregate statistics across multiple runs

**View dashboard:**
```bash
python examples/dashboard-implementation.py
python examples/dashboard-implementation.py --routine morning
python examples/dashboard-implementation.py --all
```

## Integration

See [examples/integration.md](examples/integration.md) for detailed integration documentation.

**Hook integration:**
- `post-tool-use.py` hook automatically tracks tool calls when `POPKIT_ROUTINE_MEASURE=true`
- Tracks all tools: Bash, Read, Grep, Write, Edit, Skill, etc.
- Estimates tokens using ~4 chars/token heuristic
- Captures duration from hook execution time

**Command integration:**
- `/popkit:routine` command supports `--measure` flag
- This skill wraps routine execution with measurement tracking
- Results displayed after routine completion

## Future Enhancements

See [examples/roadmap.md](examples/roadmap.md) for complete roadmap.

**Planned features:**
- **Phase 2**: Comparison mode for side-by-side routine comparison
- **Phase 3**: Trend analysis with visualization over time periods
- **Phase 4**: Optimization suggestions based on measurement data
- **Phase 5**: Token budget alerts and cost tracking

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

## Testing

See [examples/testing.md](examples/testing.md) for complete testing instructions.

**Quick test:**
```bash
# Enable measurement manually
export POPKIT_ROUTINE_MEASURE=true

# Run a routine
/popkit:routine morning

# Verify measurement file created
ls -la .claude/popkit/measurements/
cat .claude/popkit/measurements/*.json | jq '.'
```

---

**Version:** 1.1.0
**Author:** PopKit Development Team
**Last Updated:** 2025-12-19
