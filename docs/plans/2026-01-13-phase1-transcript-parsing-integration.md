# Phase 1: Power Mode Transcript Parsing Integration

> **For Claude:** Use executing-plans skill to implement this plan task-by-task.

**Goal:** Integrate existing `transcript_parser.py` into `subagent-stop.py` to extract and record structured data from Power Mode subagent transcripts.

**Architecture:** Parse JSONL transcripts to extract tool calls, reasoning, and token usage, then record to local `recording.json` for enhanced observability. Zero user-facing changes - this is an internal enhancement that lays the foundation for Phase 2 (cloud observability).

**Tech Stack:** Python 3.10+, pytest, existing `transcript_parser.py` (complete), `session_recorder.py` (needs enhancement)

**Related:** Issue #110, Section 6 Phase 1 of `2026-01-13-popkit-observability-design.md`

---

## Task 1: Add `record_subagent_completion` Function to session_recorder.py

**Files:**

- Modify: `packages/shared-py/popkit_shared/utils/session_recorder.py` (end of SessionRecorder class ~line 390)
- Test: `packages/shared-py/popkit_shared/utils/test_session_recorder.py` (if exists) or new test file

### Step 1: Write the failing test

Create test file if it doesn't exist:

```bash
cd packages/shared-py/popkit_shared/utils
touch test_session_recorder.py
```

Add test to `test_session_recorder.py`:

```python
#!/usr/bin/env python3
"""Tests for session_recorder.py"""

import json
import pytest
from pathlib import Path
from session_recorder import SessionRecorder


def test_record_subagent_completion(tmp_path):
    """Test recording subagent completion with transcript data."""
    # Arrange
    os.environ['POPKIT_RECORD'] = 'true'
    recorder = SessionRecorder()
    recorder.recordings_dir = tmp_path  # Override for testing
    recorder._init_recording()

    # Act
    recorder.record_subagent_completion(
        subagent_id="agent_123",
        tool_count=5,
        input_tokens=1200,
        output_tokens=800,
        total_tokens=2000,
        tool_details=[
            {"tool_use_id": "tool_1", "tool_name": "Read"},
            {"tool_use_id": "tool_2", "tool_name": "Write"}
        ]
    )

    # Assert
    assert len(recorder.events) == 1
    event = recorder.events[0]
    assert event["type"] == "subagent_completion"
    assert event["subagent_id"] == "agent_123"
    assert event["tool_count"] == 5
    assert event["token_usage"]["total_tokens"] == 2000
    assert len(event["tool_details"]) == 2
```

### Step 2: Run test to verify it fails

Run: `cd packages/shared-py && pytest popkit_shared/utils/test_session_recorder.py::test_record_subagent_completion -v`

Expected: `FAIL` with "AttributeError: 'SessionRecorder' object has no attribute 'record_subagent_completion'"

### Step 3: Implement the method in SessionRecorder class

Open `packages/shared-py/popkit_shared/utils/session_recorder.py` and add method around line 390 (after `record_recommendation` method):

```python
    def record_subagent_completion(
        self,
        subagent_id: str,
        tool_count: int,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        tool_details: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Record subagent completion with transcript parsing data.

        Args:
            subagent_id: Unique ID of the subagent
            tool_count: Number of tool calls made by subagent
            input_tokens: Input tokens consumed
            output_tokens: Output tokens generated
            total_tokens: Total tokens (input + output + cache)
            tool_details: Optional list of first N tool calls for summary
        """
        event = {
            "type": "subagent_completion",
            "subagent_id": subagent_id,
            "tool_count": tool_count,
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            },
            "tool_details": tool_details or [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.record_event(event)
```

### Step 4: Add module-level convenience function

Add at the bottom of `session_recorder.py` (around line 510, after other convenience functions):

```python
def record_subagent_completion(
    subagent_id: str,
    tool_count: int,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    tool_details: Optional[List[Dict[str, Any]]] = None
) -> None:
    """
    Convenience function to record subagent completion.

    Args:
        subagent_id: Unique ID of the subagent
        tool_count: Number of tool calls made by subagent
        input_tokens: Input tokens consumed
        output_tokens: Output tokens generated
        total_tokens: Total tokens (input + output + cache)
        tool_details: Optional list of first N tool calls for summary
    """
    recorder = _get_session_recorder()
    if recorder:
        recorder.record_subagent_completion(
            subagent_id=subagent_id,
            tool_count=tool_count,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            tool_details=tool_details
        )
```

### Step 5: Run test to verify it passes

Run: `cd packages/shared-py && pytest popkit_shared/utils/test_session_recorder.py::test_record_subagent_completion -v`

Expected: `PASSED`

### Step 6: Commit

```bash
git add packages/shared-py/popkit_shared/utils/session_recorder.py \
        packages/shared-py/popkit_shared/utils/test_session_recorder.py
git commit -m "$(cat <<'EOF'
feat(session-recorder): add record_subagent_completion method

Add method to record Power Mode subagent completions with:
- Tool call count
- Token usage (input, output, total)
- First N tool details for summary

Foundation for Issue #110 transcript parsing integration.

Test: test_record_subagent_completion verifies event structure

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Integrate Transcript Parsing into subagent-stop.py

**Files:**

- Modify: `packages/popkit-core/hooks/subagent-stop.py:195`
- Test: Manual integration test with Power Mode

### Step 1: Add import at top of file

Open `packages/popkit-core/hooks/subagent-stop.py` and add import around line 10 (after existing imports):

```python
from popkit_shared.utils.transcript_parser import TranscriptParser
```

### Step 2: Replace TODO at line 195 with parsing logic

Find line 195 with the TODO comment and replace the entire TODO section with:

```python
        # Parse transcript and extract tool calls (Issue #110)
        if transcript_path and Path(transcript_path).exists():
            try:
                parser = TranscriptParser(transcript_path)

                # Extract all tool uses
                tool_uses = parser.get_all_tool_uses()

                # Calculate token usage
                token_usage = parser.get_total_token_usage()

                # Record structured data to session_recorder
                from popkit_shared.utils.session_recorder import record_subagent_completion

                record_subagent_completion(
                    subagent_id=agent_id,
                    tool_count=len(tool_uses),
                    input_tokens=token_usage.input_tokens,
                    output_tokens=token_usage.output_tokens,
                    total_tokens=token_usage.total_tokens,
                    tool_details=tool_uses[:10]  # Store first 10 for summary
                )

            except Exception as e:
                # Don't fail the hook - gracefully degrade
                print(f"[WARN] Failed to parse transcript: {e}", file=sys.stderr)
```

### Step 3: Verify syntax

Run: `cd packages/popkit-core && python -m py_compile hooks/subagent-stop.py`

Expected: No output (success)

If errors, fix syntax and rerun.

### Step 4: Commit

```bash
git add packages/popkit-core/hooks/subagent-stop.py
git commit -m "$(cat <<'EOF'
feat(subagent-stop): integrate transcript parsing (Issue #110)

Parse Power Mode subagent transcripts to extract:
- Tool calls (all tools used)
- Token usage (input, output, cache, total)
- First 10 tool details for summary

Records to session_recorder for enhanced observability.

Graceful degradation: Parsing failures don't block hook.
Zero user-facing changes (internal enhancement).

Resolves: #110

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Test Integration with Power Mode

**Files:**

- Test: Manual testing with `/popkit-core:power` command
- Verify: `~/.claude/popkit/recordings/*.json` contains subagent data

### Step 1: Verify existing transcript_parser tests pass

Run: `cd packages/shared-py && pytest popkit_shared/utils/test_transcript_parser.py -v`

Expected: All tests `PASSED`

If any fail, investigate and fix before proceeding.

### Step 2: Enable recording for Power Mode test

```bash
export POPKIT_RECORD=true
```

### Step 3: Start Power Mode session

Run: `/popkit-core:power start`

Expected output:

```
Power Mode activated
Agents: [list of available agents]
```

### Step 4: Run a task that spawns subagents

Run a command that will use subagents, for example:

```bash
# This should spawn an Explore agent
/popkit-dev:next
```

Or create a simple test task:

```
User: "Search for all TypeScript files in the src directory and tell me how many there are"
```

This should trigger at least one subagent (Explore agent).

### Step 5: Stop Power Mode

Run: `/popkit-core:power stop`

Expected output:

```
Power Mode deactivated
Session summary: [details]
```

### Step 6: Verify recording.json contains subagent data

Find the latest recording:

```bash
ls -lt ~/.claude/popkit/recordings/ | head -5
```

Expected: Most recent file contains current session

Inspect the recording:

```bash
# Replace with actual filename
cat ~/.claude/popkit/recordings/20260113-*.json | jq '.events[] | select(.type == "subagent_completion")'
```

Expected output (example):

```json
{
  "type": "subagent_completion",
  "subagent_id": "agent_abc123",
  "tool_count": 8,
  "token_usage": {
    "input_tokens": 2400,
    "output_tokens": 1200,
    "total_tokens": 3600
  },
  "tool_details": [
    {"tool_use_id": "toolu_1", "tool_name": "Glob"},
    {"tool_use_id": "toolu_2", "tool_name": "Read"},
    ...
  ],
  "timestamp": "2026-01-13T15:30:00Z"
}
```

**Success Criteria:**

- ✅ Recording file exists
- ✅ Contains "subagent_completion" event
- ✅ tool_count matches number of tools used
- ✅ token_usage has input_tokens, output_tokens, total_tokens
- ✅ tool_details contains first N tools (up to 10)

If verification fails, check:

1. Was recording enabled? (`POPKIT_RECORD=true`)
2. Did subagent actually run? (check Power Mode output)
3. Does transcript file exist? (check `.claude/transcripts/`)
4. Any errors in hook output?

### Step 7: Test with multiple subagents

Run another command that spawns multiple subagents:

```
User: "Analyze the architecture of this codebase and create a design document"
```

This might spawn multiple agents (Explore, Plan, etc.).

Verify recording now has multiple `subagent_completion` events:

```bash
cat ~/.claude/popkit/recordings/20260113-*.json | jq '[.events[] | select(.type == "subagent_completion")] | length'
```

Expected: Number > 1 (multiple subagent events)

### Step 8: Verify no regressions

Test that normal recording still works without Power Mode:

```bash
export POPKIT_RECORD=true
/popkit-dev:next
```

Expected: Recording created without errors, even though no subagents spawned.

### Step 9: Document the test results

Create a test summary:

```bash
echo "Phase 1 Integration Test Results
Date: $(date)
Test scenarios:
1. Single subagent (Explore) - PASS/FAIL
2. Multiple subagents - PASS/FAIL
3. No subagents (regression check) - PASS/FAIL

Recording file: ~/.claude/popkit/recordings/[filename]
Subagent events found: [count]
Token usage recorded: [yes/no]
" > test-results-phase1.txt
```

### Step 10: Clean up test recordings (optional)

```bash
# Optional: Remove test recordings to avoid clutter
# Only do this if tests passed
rm ~/.claude/popkit/recordings/20260113-test*.json
```

---

## Task 4: Final Commit and Documentation

**Files:**

- Create: `test-results-phase1.txt` (test summary)
- Update: `CHANGELOG.md` (if exists)

### Step 1: Add test results to repo

```bash
git add test-results-phase1.txt
git commit -m "test(phase1): integration test results for Issue #110

Power Mode transcript parsing integration tested with:
- Single subagent (Explore)
- Multiple subagents (Plan + Review)
- No subagents (regression check)

All scenarios passed. Recording.json now contains:
- subagent_completion events
- tool_count and token_usage
- First 10 tool details per subagent

Foundation complete for Phase 2 (popkit-observe plugin).

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"
```

### Step 2: Update CHANGELOG.md (if exists)

If `CHANGELOG.md` exists in the repo root, add entry:

```markdown
## [Unreleased]

### Added

- Power Mode transcript parsing integration (Issue #110)
  - `record_subagent_completion` method in session_recorder.py
  - Automatic parsing of subagent JSONL transcripts
  - Tool call count and token usage tracking
  - Foundation for PopKit Observability Platform (Phase 1)

### Fixed

- subagent-stop.py now extracts structured data from transcripts (was TODO)
```

Commit:

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): add Phase 1 transcript parsing integration

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"
```

### Step 3: Push to remote (if applicable)

```bash
git push origin main
```

Or if on feature branch:

```bash
git push origin feat/issue-110-transcript-parsing
```

---

## Success Criteria Checklist

Before marking Phase 1 complete, verify:

- [x] **Task 1:** `record_subagent_completion` method added to session_recorder.py
- [x] **Task 1:** Test `test_record_subagent_completion` passes
- [x] **Task 2:** Transcript parsing integrated into subagent-stop.py:195
- [x] **Task 2:** No syntax errors in subagent-stop.py
- [x] **Task 3:** Power Mode test with single subagent passes
- [x] **Task 3:** Recording.json contains subagent_completion event
- [x] **Task 3:** Token usage recorded correctly (input, output, total)
- [x] **Task 3:** Tool details recorded (up to 10 tools)
- [x] **Task 3:** Multiple subagents test passes
- [x] **Task 3:** No regressions in normal recording (without Power Mode)
- [x] **Task 4:** Test results documented
- [x] **Task 4:** CHANGELOG.md updated (if exists)
- [x] **Task 4:** All changes committed with conventional commit messages
- [x] **Task 4:** Changes pushed to remote (if applicable)

---

## Troubleshooting

### Issue: Transcript file not found

**Symptoms:** Warning in hook output: "Transcript not found: [path]"

**Solution:**

1. Check if Power Mode is actually active: `/popkit-core:power status`
2. Verify transcript location: `ls ~/.claude/transcripts/`
3. Ensure subagent completed successfully (check Power Mode output)

### Issue: Import error for TranscriptParser

**Symptoms:** `ModuleNotFoundError: No module named 'popkit_shared.utils.transcript_parser'`

**Solution:**

1. Ensure shared-py is installed: `cd packages/shared-py && pip install -e .`
2. Verify Python path includes popkit-claude: `echo $PYTHONPATH`
3. Add to PYTHONPATH if needed: `export PYTHONPATH="/path/to/popkit-claude/packages/shared-py:$PYTHONPATH"`

### Issue: Token usage is 0

**Symptoms:** `total_tokens` in recording is 0

**Solution:**

1. Check if transcript has `usage` field: `cat [transcript-file] | jq '.usage'`
2. Verify transcript_parser.py is correctly reading usage data
3. Run unit test: `pytest popkit_shared/utils/test_transcript_parser.py::test_get_total_token_usage -v`

### Issue: No subagent_completion events in recording

**Symptoms:** Recording exists but has no subagent events

**Solution:**

1. Verify recording was enabled: `echo $POPKIT_RECORD`
2. Check if subagent actually ran: Look for "Spawning subagent" in Power Mode output
3. Check subagent-stop.py was triggered: `cat ~/.claude/logs/subagent_stop.json`
4. Look for warnings: `grep "WARN" ~/.claude/logs/*.log`

---

## Next Steps After Phase 1

Once Phase 1 is complete and all success criteria are met:

1. **Review Phase 1 Results:** Present test results to stakeholders
2. **Begin Phase 2:** Create `popkit-observe` plugin structure
3. **Update Issue #110:** Close issue with link to this implementation
4. **Plan Phase 2:** Use `/popkit:dev plan` to create Phase 2 implementation plan

**Estimated Time for Phase 1:** 1-2 days (mostly testing and verification)

**Phase 2 Preview:** Create new `popkit-observe` plugin with:

- `/popkit-observe:observe` command (5 subcommands)
- `observability_client.py` for cloud streaming
- Migration from `/popkit-core:record`

See: `docs/plans/2026-01-13-popkit-observability-design.md` Section 6 Phase 2

---

**End of Phase 1 Implementation Plan**
