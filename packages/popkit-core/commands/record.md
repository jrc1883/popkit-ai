---
description: "start | stop | status - Control session recording"
argument-hint: "<subcommand>"
---

# /popkit-core:record

Control session recording for forensic analysis and command verification.

## Usage

```bash
/popkit-core:record start                 # Enable recording
/popkit-core:record stop                  # Disable and generate report
/popkit-core:record status                # Check recording state
```

## Instructions

### Start Recording

When user runs `/popkit-core:record start`:

1. **Create state file** to enable recording:

```python
from pathlib import Path
import json
from datetime import datetime
import uuid

# Create recording state
recordings_dir = Path.home() / '.claude' / 'popkit' / 'recordings'
recordings_dir.mkdir(parents=True, exist_ok=True)

state_file = recordings_dir.parent / 'recording-state.json'

# Generate unique session ID (add UUID suffix to prevent collisions)
timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
unique_suffix = str(uuid.uuid4())[:8]
session_id = f"{timestamp}-{unique_suffix}"

# Get Claude's internal session ID from SessionStart log
claude_session_id = None
session_log = Path('logs/session_start.json')
if session_log.exists():
    try:
        log_data = json.loads(session_log.read_text())
        if log_data:
            claude_session_id = log_data[-1].get('session_id')
    except:
        pass

state = {
    'active': True,
    'session_id': session_id,
    'claude_session_id': claude_session_id,  # For SubagentStop matching
    'started_at': datetime.now().isoformat(),
    'command': 'manual-session'
}

state_file.write_text(json.dumps(state, indent=2))

print(f"[OK] Recording ENABLED")
print(f"Session ID: {session_id}")
if claude_session_id:
    print(f"Claude Session: {claude_session_id[:8]}...")
print(f"")
print(f"All tool calls will now be recorded.")
print(f"Status line will show: REC [*] <count>")
print(f"")
print(f"To stop: /popkit-core:record stop")
```

2. **Enable the recording widget** in status line:

```python
from pathlib import Path
import json

config_file = Path.home() / '.claude' / 'popkit' / 'config.json'

# Load or create config
if config_file.exists():
    config = json.loads(config_file.read_text())
else:
    config = {}

# Add recording to status line widgets
statusline = config.get('statusline', {})
widgets = statusline.get('widgets', ['popkit', 'efficiency'])

if 'recording' not in widgets:
    widgets.insert(1, 'recording')  # Add after popkit branding
    statusline['widgets'] = widgets
    config['statusline'] = statusline

    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps(config, indent=2))

print("Status line widget enabled.")
```

### Stop Recording

When user runs `/popkit-core:record stop`:

1. **Record final events BEFORE disabling** (Solution A - fixes Issue #603):

```python
from pathlib import Path
import json
from datetime import datetime
import sys

# Add shared-py to path for session_recorder
sys.path.insert(0, str(Path.home() / '.claude' / 'popkit' / 'packages' / 'shared-py'))

state_file = Path.home() / '.claude' / 'popkit' / 'recording-state.json'

if not state_file.exists():
    print("[ERROR] Recording is not active")
    exit(1)

# Load state
state = json.loads(state_file.read_text())
session_id = state.get('session_id', 'unknown')

# CRITICAL: Record final events BEFORE disabling
try:
    from popkit_shared.utils.session_recorder import get_recorder

    recorder = get_recorder()

    # Record Bash tool completion for stop command
    recorder.record_event({
        "type": "tool_call_complete",
        "timestamp": datetime.now().isoformat(),
        "tool_name": "Bash",
        "result": f"Recording stopped successfully. Session ID: {session_id}",
        "error": None,
        "duration_ms": None
    })

    # Record session end
    recorder.record_event({
        "type": "session_end",
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id
    })

except Exception as e:
    print(f"[WARN] Could not record final events: {e}", file=sys.stderr)

# NOW disable recording
state['active'] = False
state['stopped_at'] = datetime.now().isoformat()
state_file.write_text(json.dumps(state, indent=2))

print(f"[OK] Recording STOPPED")
print(f"Session ID: {session_id}")
```

2. **Find the recording file**:

```python
from pathlib import Path

recordings_dir = Path.home() / '.claude' / 'popkit' / 'recordings'

# Find latest recording matching session ID
recordings = list(recordings_dir.glob(f'*-{session_id}.json'))

if not recordings:
    # Fallback: find most recent recording
    recordings = sorted(
        recordings_dir.glob('*.json'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

if recordings:
    recording_file = recordings[0]
    print(f"Recording file: {recording_file.name}")
else:
    print("[WARN] No recording file found")
    exit(0)
```

3. **Generate HTML report**:

```python
from pathlib import Path
import subprocess

# Generate HTML report
html_file = recording_file.with_suffix('.html')

result = subprocess.run([
    'python',
    'packages/shared-py/popkit_shared/utils/html_report_generator_v9.py',
    str(recording_file),
    str(html_file)
], capture_output=True, text=True)

if result.returncode == 0:
    print(f"")
    print(f"[REPORT] Forensics Report Generated:")
    print(f"")
    print(f"  file:///{html_file.as_posix()}")
    print(f"")
    print(f"Click the link above to open in your browser.")
    print(f"")
    print(f"Report includes:")
    print(f"  - Tool execution timeline")
    print(f"  - Decision flow visualization")
    print(f"  - Context files read")
    print(f"  - Recommendation scoring")
    print(f"  - Performance analysis")
else:
    print(f"[WARN] Failed to generate HTML report: {result.stderr}")
```

### Check Status

When user runs `/popkit-core:record status`:

```python
from pathlib import Path
import json

state_file = Path.home() / '.claude' / 'popkit' / 'recording-state.json'

if not state_file.exists():
    print("Recording: INACTIVE")
    print("")
    print("To start: /popkit-core:record start")
    exit(0)

state = json.loads(state_file.read_text())

if state.get('active'):
    session_id = state.get('session_id', 'unknown')
    started_at = state.get('started_at', 'unknown')

    # Get event count
    recordings_dir = Path.home() / '.claude' / 'popkit' / 'recordings'
    recordings = list(recordings_dir.glob(f'*{session_id}*.json'))

    event_count = 0
    if recordings:
        try:
            data = json.loads(recordings[0].read_text())
            event_count = len(data.get('events', []))
        except:
            pass

    print(f"Recording: ACTIVE [*]")
    print(f"")
    print(f"Session ID: {session_id}")
    print(f"Started: {started_at}")
    print(f"Events captured: {event_count}")
    print(f"")
    print(f"To stop: /popkit-core:record stop")
else:
    print("Recording: STOPPED")
    print(f"Last session: {state.get('session_id', 'unknown')}")
    print("")
    print("To start new: /popkit-core:record start")
```

## Examples

### Full Recording Workflow

```bash
# Start recording
/popkit-core:record start
# → Recording ENABLED (session: 20251223-142530)

# Run commands (all tool calls are recorded)
/popkit-dev:next
/popkit-dev:routine morning
/popkit-dev:git status

# Stop and generate report
/popkit-core:record stop
# → Recording STOPPED
# → Report: file:///<USER_HOME>/.claude/popkit/recordings/20251223-142530.html
```

### Check Recording Status

```bash
/popkit-core:record status
# → Recording: ACTIVE ●
# → Events captured: 47
```

## Sub-Agent Recording (Working)

**Status**: ✅ Fully implemented and working (Issue #603 resolved)

**How it works**: Claude Code fires a `SubagentStop` hook event when any sub-agent (launched via `Skill` or `Task` tools) completes execution. PopKit's recording system now captures these events by:

1. **Session ID Correlation**: Recording state stores BOTH a display session ID (`YYYYMMDD-HHMMSS`) and Claude's internal session ID (UUID)
2. **Hook Verification**: `SubagentStop` hook verifies incoming events match the current recording session
3. **Event Capture**: Sub-agent completion events are recorded with:
   - `agent_id`: Unique identifier for the sub-agent
   - `session_id`: Claude's internal session ID
   - `transcript_available`: Whether the full transcript exists

**What gets captured**:

```bash
/popkit-core:record start

# All tool calls will be captured:
git status                    # ✓ Main agent tool call
/popkit-dev:next                  # ✓ Skill invocation + sub-agent transcript
  ├─ git status --porcelain   # ✓ Sub-agent tool call (from transcript)
  ├─ git branch -vv           # ✓ Sub-agent tool call (from transcript)
  └─ gh issue list            # ✓ Sub-agent tool call (from transcript)

/popkit-core:record stop
# → Report will show hierarchical view of main + sub-agent activity
```

**Resolution**: Issue #603 resolved - session ID correlation fix implemented (2025-12-24)

**Testing**: See `docs/testing/issue-603-subagent-recording-test.md` for verification procedure

## Related

- **Recording Infrastructure**: `packages/shared-py/popkit_shared/utils/session_recorder.py`
- **HTML Report Generator**: `packages/shared-py/popkit_shared/utils/html_report_generator.py`
- **Status Line Widget**: `packages/popkit-core/power-mode/statusline.py`
- **Hooks Integration**: `packages/popkit-core/hooks/post-tool-use.py`
