---
description: "start | stop | status - Control session recording"
argument-hint: "<subcommand>"
---

# /popkit:record

Control session recording for forensic analysis and command verification.

## Usage

```bash
/popkit:record start                 # Enable recording
/popkit:record stop                  # Disable and generate report
/popkit:record status                # Check recording state
```

## Instructions

### Start Recording

When user runs `/popkit:record start`:

1. **Create state file** to enable recording:

```python
from pathlib import Path
import json
from datetime import datetime

# Create recording state
recordings_dir = Path.home() / '.claude' / 'popkit' / 'recordings'
recordings_dir.mkdir(parents=True, exist_ok=True)

state_file = recordings_dir.parent / 'recording-state.json'
session_id = datetime.now().strftime('%Y%m%d-%H%M%S')

state = {
    'active': True,
    'session_id': session_id,
    'started_at': datetime.now().isoformat(),
    'command': 'manual-session'
}

state_file.write_text(json.dumps(state, indent=2))

print(f"✅ Recording ENABLED")
print(f"Session ID: {session_id}")
print(f"")
print(f"All tool calls will now be recorded.")
print(f"Status line will show: REC [●] <count>")
print(f"")
print(f"To stop: /popkit:record stop")
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

When user runs `/popkit:record stop`:

1. **Disable recording state**:

```python
from pathlib import Path
import json

state_file = Path.home() / '.claude' / 'popkit' / 'recording-state.json'

if not state_file.exists():
    print("❌ Recording is not active")
    exit(1)

# Load state
state = json.loads(state_file.read_text())
session_id = state.get('session_id', 'unknown')

# Mark as stopped
state['active'] = False
state['stopped_at'] = datetime.now().isoformat()
state_file.write_text(json.dumps(state, indent=2))

print(f"✅ Recording STOPPED")
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
    print("⚠️ No recording file found")
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
    'packages/shared-py/popkit_shared/utils/html_report_generator.py',
    str(recording_file),
    str(html_file)
], capture_output=True, text=True)

if result.returncode == 0:
    print(f"")
    print(f"📊 Forensics Report Generated:")
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
    print(f"⚠️ Failed to generate HTML report: {result.stderr}")
```

### Check Status

When user runs `/popkit:record status`:

```python
from pathlib import Path
import json

state_file = Path.home() / '.claude' / 'popkit' / 'recording-state.json'

if not state_file.exists():
    print("Recording: INACTIVE")
    print("")
    print("To start: /popkit:record start")
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

    print(f"Recording: ACTIVE ●")
    print(f"")
    print(f"Session ID: {session_id}")
    print(f"Started: {started_at}")
    print(f"Events captured: {event_count}")
    print(f"")
    print(f"To stop: /popkit:record stop")
else:
    print("Recording: STOPPED")
    print(f"Last session: {state.get('session_id', 'unknown')}")
    print("")
    print("To start new: /popkit:record start")
```

## Examples

### Full Recording Workflow

```bash
# Start recording
/popkit:record start
# → Recording ENABLED (session: 20251223-142530)

# Run commands (all tool calls are recorded)
/popkit-dev:next
/popkit:routine morning
/popkit:git status

# Stop and generate report
/popkit:record stop
# → Recording STOPPED
# → Report: file:///C:/Users/Josep/.claude/popkit/recordings/20251223-142530.html
```

### Check Recording Status

```bash
/popkit:record status
# → Recording: ACTIVE ●
# → Events captured: 47
```

## Sub-Agent Recording (In Development)

**Status**: Sub-agent recording support is being implemented via the `SubagentStop` hook.

**How it works**: Claude Code fires a `SubagentStop` hook event when any sub-agent (launched via `Skill` or `Task` tools) completes execution. This hook provides:
- `agent_id`: Unique identifier for the sub-agent
- `agent_transcript_path`: Full conversation transcript of the sub-agent
- `session_id`: Parent session ID (shared across main agent and sub-agents)

**Current limitation**: The `SubagentStop` hook handler is not yet implemented in PopKit's recording infrastructure.

**Expected after implementation**:
```bash
/popkit:record start

# All tool calls will be captured:
git status                    # ✓ Main agent tool call
/popkit:next                  # ✓ Skill invocation + sub-agent transcript
  ├─ git status --porcelain   # ✓ Sub-agent tool call (from transcript)
  ├─ git branch -vv           # ✓ Sub-agent tool call (from transcript)
  └─ gh issue list            # ✓ Sub-agent tool call (from transcript)

/popkit:record stop
# → Report will show hierarchical view of main + sub-agent activity
```

**Implementation tracking**: Issue #603 (was originally documented as architectural limitation, now being implemented)

## Related

- **Recording Infrastructure**: `packages/shared-py/popkit_shared/utils/session_recorder.py`
- **HTML Report Generator**: `packages/shared-py/popkit_shared/utils/html_report_generator.py`
- **Status Line Widget**: `packages/popkit-core/power-mode/statusline.py`
- **Hooks Integration**: `packages/popkit-core/hooks/post-tool-use.py`
