# Issue #603: SubagentStop Recording - Test Plan

## Problem Summary

Session recording was not capturing SubagentStop events because of a session ID mismatch:
- Recording used manual session ID: `YYYYMMDD-HHMMSS`
- SubagentStop hook received Claude's internal session ID: `<UUID>`

## Fix Implemented

1. **Updated `/popkit:record start`** to capture Claude's session_id from SessionStart log
2. **Modified recording state structure** to store both session IDs:
   ```json
   {
     "active": true,
     "session_id": "20251224-005642",           // Display ID
     "claude_session_id": "30fd59e3-...",        // Internal ID for matching
     "started_at": "...",
     "command": "...",
     "recording_file": "..."
   }
   ```
3. **Updated `record_subagent_completion()`** in `subagent-stop.py` to verify incoming session_id matches claude_session_id

## Test Procedure

### Prerequisites

1. Restart Claude Code to load updated hooks
   ```bash
   # Exit current session
   # Start Claude Code again with:
   .\start-popkit.cmd
   ```

### Test Steps

1. **Start Recording**
   ```
   /popkit:record start
   ```

   **Expected Output:**
   ```
   ✅ Recording ENABLED
   Session ID: 20251224-123456
   Claude Session: 30fd59e3...

   All tool calls will now be recorded.
   Status line will show: REC [●] <count>

   To stop: /popkit:record stop
   ```

   **Verify**: Check that both session IDs are displayed

2. **Trigger Sub-Agent Execution**
   ```
   /popkit:next
   ```

   This will launch a sub-agent (the `pop-next-action` skill uses the Task tool internally).

3. **Stop Recording**
   ```
   /popkit:record stop
   ```

   **Expected Output:**
   ```
   ✅ Recording STOPPED
   Session ID: 20251224-123456

   📊 Forensics Report Generated:

     file:///<USER_HOME>/.claude/popkit/recordings/2025-12-24-123456-manual-session-20251224-123456.html

   Click the link above to open in your browser.
   ```

4. **Verify Recording Captured SubagentStop Events**

   Open the HTML report and check for sub-agent events.

   **Alternative: Check JSON directly**
   ```bash
   cd ~/.claude/popkit/recordings
   cat <latest-recording>.json | python -m json.tool | findstr "subagent_stop"
   ```

   **Expected Result:**
   - At least 1 `subagent_stop` event present
   - Event should have:
     - `"type": "subagent_stop"`
     - `"agent_id": "a1b2c3d"`
     - `"session_id": "<Claude's UUID>"`
     - `"transcript_available": true`

### Success Criteria

✅ Recording state file contains `claude_session_id`
✅ SubagentStop events appear in recording JSON
✅ Events have correct session_id (Claude's UUID)
✅ HTML report shows sub-agent activity

### Failure Scenarios

If SubagentStop events still don't appear:

1. **Check Session ID Mismatch**
   ```bash
   # Compare session IDs
   cat ~/.claude/popkit/recording-state.json
   cat <PROJECT_ROOT>/logs/subagent_stop.json | python -m json.tool | findstr session_id
   ```

2. **Check Hook Execution**
   ```bash
   # Verify subagent-stop.py is being called
   cat <PROJECT_ROOT>/logs/subagent_stop.json | python -c "import sys, json; data=json.load(sys.stdin); print(f'Total events: {len(data)}')"
   ```

3. **Enable Debug Logging**
   Add temporary debug output to `record_subagent_completion()`:
   ```python
   print(f"DEBUG: Recording active, session match check...", file=sys.stderr)
   print(f"DEBUG: Expected claude_session_id: {claude_session_id}", file=sys.stderr)
   print(f"DEBUG: Incoming session_id: {incoming_session_id}", file=sys.stderr)
   ```

## Files Changed

- `packages/popkit-core/commands/record.md` - Updated start recording instructions
- `packages/popkit-core/hooks/subagent-stop.py` - Added session ID verification
- `~/.claude/popkit/recording-state.json` - Will contain `claude_session_id` field

## Related

- Issue #603: Session Recording: File Overwrite Bug Fixed + Sub-Agent Limitation Documented
- `/popkit:record` command documentation
- `packages/shared-py/popkit_shared/utils/session_recorder.py`
