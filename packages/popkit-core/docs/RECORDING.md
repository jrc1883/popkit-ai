# Session Recording Feature

Record full command execution for post-hoc analysis and validation.

## Quick Start

### Enable Recording

Set environment variables before running a command:

```bash
export POPKIT_RECORD=true
export POPKIT_COMMAND="plugin-test"  # Optional: name the recording

# Run any PopKit command
/popkit-core:plugin test

# Recording saved to: ~/.claude/popkit/recordings/<timestamp>-<command>-<id>.json
```

### Analyze Recording

```bash
python packages/shared-py/popkit_shared/utils/recording_analyzer.py \
  ~/.claude/popkit/recordings/2025-12-23-*.json
```

## What Gets Recorded

Every session recording captures:

1. **Tool Calls**
   - Tool name (Bash, Read, Grep, Edit, etc.)
   - Parameters passed
   - Results returned (truncated to 1000 chars)
   - Errors encountered
   - Duration in milliseconds

2. **Skill Invocations**
   - Skill name
   - Arguments passed

3. **User Decisions**
   - Question asked
   - Options presented
   - User's selection

4. **Session Metadata**
   - Start/end timestamps
   - Working directory
   - Environment variables
   - Session ID

## Recording File Format

```json
{
  "session_id": "abc123",
  "events": [
    {
      "sequence": 0,
      "type": "session_start",
      "timestamp": "2025-12-23T10:00:00Z",
      "command": "plugin-test",
      "working_directory": "/path/to/project"
    },
    {
      "sequence": 1,
      "type": "tool_call",
      "timestamp": "2025-12-23T10:00:01Z",
      "tool_name": "Bash",
      "parameters": {"command": "git status"},
      "result": "M file1.py\nM file2.py",
      "error": null,
      "duration_ms": 150
    },
    {
      "sequence": 2,
      "type": "session_end",
      "timestamp": "2025-12-23T10:00:05Z",
      "status": "completed",
      "total_events": 3
    }
  ]
}
```

## Analysis Reports

The analyzer generates comprehensive reports showing:

### Performance Summary
- Total tool calls
- Total/average/min/max duration
- Session start/end times

### Tool Usage Breakdown
- Call counts per tool
- Duration statistics
- Error rates

### Error Summary
- Total errors
- Error rate percentage
- Error types and frequencies

### Event Timeline
- Chronological list of all events
- Visual indicators for success/failure
- Duration for each operation

## Usage Examples

### Record a Plugin Test

```bash
export POPKIT_RECORD=true POPKIT_COMMAND="plugin-test"
/popkit-core:plugin test
```

### Record a Morning Routine

```bash
export POPKIT_RECORD=true POPKIT_COMMAND="morning-routine"
/popkit-dev:routine morning
```

### Record Next Action Analysis

```bash
export POPKIT_RECORD=true POPKIT_COMMAND="next-action"
/popkit-dev:next
```

### Analyze Multiple Recordings

```bash
# List recent recordings
ls -lh ~/.claude/popkit/recordings/*.json | tail -5

# Analyze specific recording
python packages/shared-py/popkit_shared/utils/recording_analyzer.py \
  ~/.claude/popkit/recordings/2025-12-23-105710-plugin-test-abc123.json

# Generate JSON report instead of Markdown
python packages/shared-py/popkit_shared/utils/recording_analyzer.py \
  ~/.claude/popkit/recordings/2025-12-23-*.json json
```

## Integration with Tests

Recordings can validate that commands behave according to specifications:

1. **Record expected behavior** - Run command with `--record`
2. **Compare against spec** - Verify tool calls match documentation
3. **Detect regressions** - Compare recordings before/after changes
4. **Performance tracking** - Track duration trends over time

## Advanced Usage

### Custom Session IDs

```bash
export POPKIT_RECORD_ID="my-custom-id"
export POPKIT_RECORD=true
/popkit-dev:next
# Saves to: ~/.claude/popkit/recordings/<timestamp>-<command>-my-custom-id.json
```

### Programmatic Analysis

```python
from popkit_shared.utils.recording_analyzer import RecordingAnalyzer

analyzer = RecordingAnalyzer('path/to/recording.json')

# Get tool usage
tools = analyzer.get_tool_usage_breakdown()
print(f"Bash called {tools['Bash']['count']} times")

# Get errors
errors = analyzer.get_error_summary()
print(f"Error rate: {errors['error_rate']:.1%}")

# Generate report
report = analyzer.generate_report(format='markdown')
print(report)
```

## Troubleshooting

### Recording Not Created

Check that:
1. `POPKIT_RECORD=true` is set
2. Directory `~/.claude/popkit/recordings/` exists (created automatically)
3. Hook is enabled and imports succeeded

### Empty Recording

If recording file exists but has no events:
- Verify hook is being called (check stderr output)
- Check for import errors in `post-tool-use.py`
- Ensure `popkit_shared` package is installed

### Analyzer Errors

Common issues:
- **UnicodeEncodeError**: Windows console encoding issue (fixed in latest version)
- **File not found**: Check file path, use absolute path
- **Invalid JSON**: Recording may be corrupted, check file contents

## Architecture

### Components

| Component | Purpose |
|-----------|---------|
| `session_recorder.py` | Core recording logic, event capture |
| `recording_analyzer.py` | Analysis and report generation |
| `post-tool-use.py` | Hook integration for auto-capture |
| Environment vars | Enable/configure recording |

### Flow

```
Command Execution
    ↓
post-tool-use.py hook fires
    ↓
Check if POPKIT_RECORD=true
    ↓
session_recorder.record_tool_call()
    ↓
Write to ~/.claude/popkit/recordings/<timestamp>.json
    ↓
Analyze with recording_analyzer.py
    ↓
Generate Markdown/JSON report
```

## Future Enhancements

Planned features:
- [ ] Automatic recording via `--record` flag on commands
- [ ] Web UI for browsing recordings
- [ ] Comparison tool for before/after recordings
- [ ] Performance regression detection
- [ ] Integration with CI/CD for automated testing
- [ ] Export to trace format (OpenTelemetry, Jaeger)

## Related

- `/popkit-core:plugin test` - Test plugin components
- `/popkit-dev:routine morning --measure` - Track routine performance
- Test telemetry (`TEST_MODE=true`) - Similar but for tests
