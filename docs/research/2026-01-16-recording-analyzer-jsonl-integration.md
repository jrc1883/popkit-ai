# RecordingAnalyzer JSONL Integration

**Date**: 2026-01-16
**Status**: Implemented
**Related Issues**: Benchmark Suite Phase 3, User requirement for JSONL support

## Overview

Extended `RecordingAnalyzer` to support **both recording formats**:

1. **PopKit JSON format** - Aggregated event stream from SessionRecorder hooks
2. **Claude Code JSONL format** - Native transcript files from Claude Code

This enables:
- **WITH PopKit trials**: Use PopKit JSON recordings (hooks capture everything)
- **WITHOUT PopKit baseline trials**: Use Claude Code JSONL transcripts (no hooks available)

## Architecture

### Format Detection

```python
def _detect_format(self) -> str:
    """Detect recording format: 'popkit_json' or 'claude_jsonl'"""
    if self.recording_file.suffix == ".jsonl":
        return "claude_jsonl"
    else:
        return "popkit_json"
```

File extension determines format automatically.

### JSONL Conversion Pipeline

```
Claude Code JSONL → TranscriptParser → PopKit Event Structure → RecordingAnalyzer
```

**Steps**:

1. `TranscriptParser` reads JSONL file line-by-line
2. Extracts:
   - Token usage (input, output, cache creation, cache read)
   - Tool uses (name, parameters, timestamps)
   - Assistant messages (for reasoning)
3. Converts to PopKit event structure:
   - `session_start` event
   - `tool_call` events (one per tool use)
   - `session_end` event
4. Builds metadata with actual token counts
5. RecordingAnalyzer processes events normally

### Key Changes

#### 1. `_load_recording()` - Format Dispatcher

```python
def _load_recording(self) -> Dict[str, Any]:
    """Load recording from file - handles both PopKit JSON and Claude JSONL formats."""
    if self.recording_file.suffix == ".jsonl":
        return self._load_claude_jsonl()
    else:
        return self._load_popkit_json()
```

#### 2. `_load_claude_jsonl()` - JSONL Parser

```python
def _load_claude_jsonl(self) -> Dict[str, Any]:
    """
    Load Claude Code's native JSONL transcript and convert to PopKit-compatible format.

    Uses TranscriptParser to extract:
    - Token usage (for context_usage metric)
    - Tool uses (for tool_calls metric)
    - Performance data (for time_to_complete metric)
    """
    parser = TranscriptParser(str(self.recording_file))

    # Extract data
    tool_uses = parser.get_all_tool_uses()
    total_usage = parser.get_total_token_usage()

    # Convert to PopKit event structure
    events = [...]

    # Build metadata with actual token counts
    metadata = {
        "total_input_tokens": total_usage.input_tokens,
        "total_output_tokens": total_usage.output_tokens,
        "cache_creation_input_tokens": total_usage.cache_creation_input_tokens,
        "cache_read_input_tokens": total_usage.cache_read_input_tokens,
        "total_tokens": total_usage.total_tokens,
        "format": "claude_jsonl",
    }

    return {...}
```

#### 3. `get_token_count()` - Format-Aware Token Extraction

```python
def get_token_count(self) -> int:
    """Get total token count from session.

    For Claude JSONL format: Uses actual token counts from TranscriptParser.
    For PopKit JSON format: Uses metadata from Claude Code 2.1.6+ or estimates.
    """
    # For JSONL format, metadata.total_tokens is pre-calculated
    if self.format_type == "claude_jsonl" and self.metadata:
        total = self.metadata.get("total_tokens", 0)
        if total > 0:
            return total

    # Try PopKit metadata sources...
    # Fallback to estimation...
```

#### 4. `get_tool_usage_breakdown()` - Handle Missing Fields

JSONL format doesn't track per-tool durations or errors, so:

```python
# Duration may be None for JSONL format
duration = call.get("duration_ms")
if duration is not None:
    tools[tool_name]["total_duration_ms"] += duration

# Error may be None for JSONL format
error = call.get("error")
if error:
    tools[tool_name]["errors"] += 1
```

#### 5. `get_performance_metrics()` - Calculate Session Duration

For JSONL format (no per-tool durations), calculate session duration from timestamps:

```python
# Calculate session duration if timestamps available (for JSONL format)
session_duration_ms = None
if start_time and end_time:
    try:
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        session_duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
    except Exception:
        pass

return {
    "total_tool_calls": len(tool_calls),
    "total_duration_ms": sum(durations) if durations else (session_duration_ms or 0),
    # ... other metrics
    "session_duration_ms": session_duration_ms,  # Total session time (JSONL)
}
```

## Usage Examples

### With PopKit JSON (Current Default)

```python
from pathlib import Path
from popkit_shared.utils.recording_analyzer import RecordingAnalyzer

# Analyze PopKit recording
analyzer = RecordingAnalyzer(Path("~/.claude/popkit/recordings/session-abc123.json"))

print(f"Format: {analyzer.format_type}")  # "popkit_json"
print(f"Tokens: {analyzer.get_token_count()}")
print(f"Tool calls: {len(analyzer.get_tool_usage_breakdown())}")
```

### With Claude Code JSONL (Baseline)

```python
# Analyze Claude Code transcript
analyzer = RecordingAnalyzer(Path("~/.claude/projects/[encoded]/session-xyz789.jsonl"))

print(f"Format: {analyzer.format_type}")  # "claude_jsonl"
print(f"Tokens: {analyzer.get_token_count()}")  # Actual from TranscriptParser
print(f"Tool calls: {len(analyzer.get_tool_usage_breakdown())}")
```

### In Benchmark Suite

```python
# benchmark_analyzer.py
def _extract_context_usage(self, recording_path: Path, analyzer: Any) -> float:
    """Extract context usage (total tokens)."""
    # Works with BOTH formats automatically
    return float(analyzer.get_token_count())

def _extract_tool_calls(self, analyzer: Any) -> float:
    """Extract tool call count."""
    # Works with BOTH formats automatically
    tool_usage = analyzer.get_tool_usage_breakdown()
    return float(sum(data["count"] for data in tool_usage.values()))
```

## Benchmark Integration

### WITH PopKit Trials

```bash
# PopKit enabled - uses hooks
POPKIT_RECORD=true claude -p "Fix the authentication bug"

# Recording saved to: ~/.claude/popkit/recordings/session-abc123.json
# Format: PopKit JSON with complete event stream
```

### WITHOUT PopKit Baseline Trials

```bash
# PopKit disabled - no hooks
claude plugin disable popkit-core
claude -p "Fix the authentication bug"

# Recording saved to: ~/.claude/projects/[encoded]/session-xyz789.jsonl
# Format: Claude Code JSONL (native transcript)
```

### Benchmark Analysis

```python
# benchmark_runner.py
def _collect_recordings(self, trial_type: str) -> List[Path]:
    """Collect recordings for analysis."""
    if trial_type == "with_popkit":
        # PopKit JSON recordings
        return list(popkit_recordings_dir.glob("*.json"))
    else:
        # Claude Code JSONL transcripts
        return list(claude_projects_dir.glob("*/*.jsonl"))

# benchmark_analyzer.py automatically detects format and extracts metrics
```

## Benefits

1. **Complete Forensics**: Synthesizes ALL available information
   - PopKit hooks capture real-time events
   - Claude JSONL provides complete transcript
   - Together = comprehensive analysis

2. **Baseline Support**: Can analyze sessions WITHOUT PopKit installed
   - Critical for benchmarking
   - Compare WITH vs WITHOUT PopKit fairly

3. **Backwards Compatible**: Existing PopKit JSON recordings still work
   - No changes required to existing code
   - Format detection is automatic

4. **Accurate Metrics**: Uses actual token counts from Claude API
   - No more estimation fallbacks (for JSONL)
   - Includes cache tokens (read + write)

## Limitations

### JSONL Format Limitations

1. **No per-tool durations**: JSONL doesn't track individual tool execution time
   - Workaround: Calculate session duration from timestamps
   - Affects: `get_performance_metrics()` - returns 0 for avg/min/max

2. **No error tracking**: JSONL doesn't capture tool errors directly
   - Workaround: Would need to parse tool_result blocks
   - Affects: `get_error_summary()` - may undercount errors

3. **No backtracking detection**: JSONL doesn't track file modifications explicitly
   - Workaround: Count Write/Edit/MultiEdit tool uses
   - Affects: `get_file_modifications()` - works but less precise

### These limitations are acceptable for benchmarking because:
- **Context usage (tokens)**: ✅ Fully accurate from TranscriptParser
- **Tool call count**: ✅ Fully accurate from tool_use blocks
- **Time to complete**: ✅ Session duration from timestamps
- **Backtracking**: ✅ Count file modification tools
- **Error recovery**: ⚠️ Limited error tracking (acceptable for baseline)

## Testing

### Unit Tests

```bash
# Test RecordingAnalyzer with both formats
cd packages/popkit-ops/skills/pop-benchmark-runner
python tests/test_recording_analyzer_jsonl.py  # New test file needed
```

### Integration Tests

```bash
# Test full benchmark pipeline with JSONL
python scripts/benchmark_runner.py --test-jsonl-format
```

## Next Steps

1. ✅ **DONE**: Integrate TranscriptParser with RecordingAnalyzer
2. ✅ **DONE**: Update `get_token_count()` for JSONL format
3. ✅ **DONE**: Update `get_tool_usage_breakdown()` for JSONL format
4. ✅ **DONE**: Update `get_performance_metrics()` for JSONL format
5. 🚧 **TODO**: Write unit tests for JSONL support
6. 🚧 **TODO**: Update benchmark_runner.py to use both formats
7. 🚧 **TODO**: Test end-to-end benchmark with real JSONL files
8. 🚧 **TODO**: Document Claude Code automation (`claude -p` flag)

## Files Modified

- `packages/shared-py/popkit_shared/utils/recording_analyzer.py`
  - Added JSONL format detection
  - Added `_load_claude_jsonl()` method
  - Updated `get_token_count()` for format awareness
  - Updated `get_tool_usage_breakdown()` for None-safe duration/error handling
  - Updated `get_performance_metrics()` to calculate session duration

## Dependencies

- `popkit_shared.utils.transcript_parser.TranscriptParser` (required for JSONL)
- Python 3.8+ (datetime.fromisoformat with timezone support)

## References

- TranscriptParser: `packages/shared-py/popkit_shared/utils/transcript_parser.py`
- Claude Code JSONL format: `~/.claude/projects/[encoded]/[session-uuid].jsonl`
- PopKit JSON format: `~/.claude/popkit/recordings/[timestamp]-[command]-[session].json`
