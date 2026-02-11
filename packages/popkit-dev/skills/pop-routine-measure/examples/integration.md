# Integration Details

## Command Integration

The `commands/routine.md` documents the `--measure` flag. When Claude sees this flag:

1. **Invoke this skill** before executing the routine
2. **Wrap execution** with measurement tracking
3. **Display results** after routine completion

## Hook Integration

The `post-tool-use.py` hook checks for `POPKIT_ROUTINE_MEASURE=true`:

```python
if ROUTINE_MEASUREMENT_AVAILABLE and check_measure_flag():
    tracker = RoutineMeasurementTracker()
    if tracker.is_active():
        tracker.track_tool_call(tool_name, content, execution_time)
```

## Tool Call Tracking

The hook automatically tracks tool calls when measurement is enabled:

- **Tracked Tools**: All tools (Bash, Read, Grep, Write, Edit, Skill, etc.)
- **Token Estimation**: ~4 chars per token (rough approximation)
- **Input/Output Split**: 20% input, 80% output (heuristic)
- **Duration**: Captured from hook execution time

## Storage Location

```
.claude/popkit/measurements/
├── pk_20251219_080000.json       # Universal routine
├── p-1_20251219_143022.json      # Custom routine
└── rc-1_20251219_180000.json     # Project routine
```

## Architecture Files

| File                                 | Purpose                      |
| ------------------------------------ | ---------------------------- |
| `hooks/utils/routine_measurement.py` | Measurement tracking classes |
| `hooks/post-tool-use.py`             | Tool call capture hook       |
| `commands/routine.md`                | Command specification        |
| `.claude/popkit/measurements/`       | Measurement data storage     |
