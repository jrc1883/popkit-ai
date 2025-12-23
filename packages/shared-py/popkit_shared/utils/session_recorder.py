#!/usr/bin/env python3
"""
Session Recorder - Captures full command execution for analysis

Records all tool calls, decisions, and events during command execution
to enable post-hoc analysis and validation.

Usage:
    /popkit-dev:next --record
    /popkit-core:plugin test --record
    /popkit-dev:routine morning --record

Environment Variables:
    POPKIT_RECORD=true        - Enable recording
    POPKIT_RECORD_ID=<id>     - Session ID (auto-generated if not set)

Output:
    ~/.claude/popkit/recordings/<timestamp>-<command>-<id>.json
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid

# File locking (Unix-only)
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

try:
    from .session_manager import get_current_session, update_session_activity
    HAS_SESSION_MANAGER = True
except ImportError:
    HAS_SESSION_MANAGER = False


class SessionRecorder:
    """Records session activity for analysis."""

    def __init__(self):
        self.recording_enabled = self._check_recording_enabled()
        self.recordings_dir = Path.home() / '.claude' / 'popkit' / 'recordings'
        self.recording_file = None
        self.session_id = None
        self.events: List[Dict[str, Any]] = []

        if self.recording_enabled:
            self._init_recording()

    def _check_recording_enabled(self) -> bool:
        """Check if recording is enabled via env var, flag, or state file."""
        # Check environment variable first
        if os.getenv('POPKIT_RECORD', '').lower() == 'true':
            return True

        # Check for recording state file (persists across tool calls)
        state_file = Path.home() / '.claude' / 'popkit' / 'recording-state.json'
        if state_file.exists():
            try:
                import json
                state = json.loads(state_file.read_text())
                return state.get('active', False)
            except (json.JSONDecodeError, IOError):
                pass

        return False

    def _init_recording(self) -> None:
        """Initialize recording using session manager."""
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

        # Check for state file first (persists across tool calls)
        state_file = Path.home() / '.claude' / 'popkit' / 'recording-state.json'
        if state_file.exists():
            try:
                import json
                state = json.loads(state_file.read_text())
                if state.get('active'):
                    # Use session from state file
                    self.session_id = state.get('session_id', str(uuid.uuid4())[:8])
                    command_name = state.get('command', 'manual-session')
                    timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
                    filename = f"{timestamp}-{command_name}-{self.session_id}.json"
                    self.recording_file = self.recordings_dir / filename

                    # Load existing events if file exists
                    if self.recording_file.exists():
                        self._load_existing_events()
                    else:
                        # Initialize new recording file
                        self.record_event({
                            'type': 'session_start',
                            'timestamp': state.get('started_at', datetime.now(timezone.utc).isoformat()),
                            'session_id': self.session_id,
                            'command': command_name,
                            'working_directory': os.getcwd(),
                            'environment': {
                                'POPKIT_RECORD': 'true',
                                'source': 'state_file',
                            }
                        })
                    return
            except (json.JSONDecodeError, IOError):
                pass

        if HAS_SESSION_MANAGER:
            # Use session manager for unified sessions
            session = get_current_session()
            self.session_id = session['session_id']
            filename = session['recording_file']
            self.recording_file = self.recordings_dir / filename

            # Load existing events if file exists
            if self.recording_file.exists():
                self._load_existing_events()
            else:
                # Initialize new recording file
                self._write_initial_event(session)
        else:
            # Fallback: old behavior (one file per tool call)
            self.session_id = os.getenv('POPKIT_RECORD_ID', str(uuid.uuid4())[:8])
            timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            command_name = os.getenv('POPKIT_COMMAND', 'unknown')
            filename = f"{timestamp}-{command_name}-{self.session_id}.json"
            self.recording_file = self.recordings_dir / filename

            # Initialize with metadata
            self.record_event({
                'type': 'session_start',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'session_id': self.session_id,
                'command': command_name,
                'working_directory': os.getcwd(),
                'environment': {
                    'POPKIT_RECORD': os.getenv('POPKIT_RECORD'),
                    'POPKIT_RECORD_ID': os.getenv('POPKIT_RECORD_ID'),
                    'TEST_MODE': os.getenv('TEST_MODE'),
                }
            })

    def _load_existing_events(self) -> None:
        """Load existing events from recording file."""
        try:
            with open(self.recording_file, 'r') as f:
                if HAS_FCNTL:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                    self.events = data.get('events', [])
                finally:
                    if HAS_FCNTL:
                        import fcntl
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (json.JSONDecodeError, FileNotFoundError):
            self.events = []

    def _write_initial_event(self, session: Dict[str, Any]) -> None:
        """Write initial session_start event."""
        self.record_event({
            'type': 'session_start',
            'timestamp': session['created_at'],
            'session_id': session['session_id'],
            'command': session['command'],
            'working_directory': session['working_directory'],
            'environment': session['environment']
        })

    def record_event(self, event: Dict[str, Any]) -> None:
        """Record an event to the session log."""
        if not self.recording_enabled:
            return

        # Add sequence number
        event['sequence'] = len(self.events)

        # Add to in-memory buffer
        self.events.append(event)

        # Update session activity if using session manager
        if HAS_SESSION_MANAGER and self.session_id:
            update_session_activity(self.session_id)

        # Write to file with lock (if available)
        if self.recording_file:
            with open(self.recording_file, 'w') as f:
                if HAS_FCNTL:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump({
                        'session_id': self.session_id,
                        'events': self.events
                    }, f, indent=2)
                finally:
                    if HAS_FCNTL:
                        import fcntl
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def record_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Optional[Any] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> None:
        """Record a tool invocation."""
        self.record_event({
            'type': 'tool_call',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'tool_name': tool_name,
            'parameters': parameters,
            'result': result,
            'error': error,
            'duration_ms': duration_ms
        })

    def record_skill_invocation(
        self,
        skill_name: str,
        arguments: Optional[str] = None
    ) -> None:
        """Record a skill invocation."""
        self.record_event({
            'type': 'skill_invocation',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'skill_name': skill_name,
            'arguments': arguments
        })

    def record_file_read(
        self,
        file_path: str,
        content_summary: Optional[str] = None,
        relevant: bool = True
    ) -> None:
        """Record reading of an important context file."""
        self.record_event({
            'type': 'file_read',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'file_path': file_path,
            'content_summary': content_summary,
            'relevant': relevant
        })

    def record_reasoning(
        self,
        step: str,
        reasoning: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record reasoning/thinking step."""
        self.record_event({
            'type': 'reasoning',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'step': step,
            'reasoning': reasoning,
            'data': data or {}
        })

    def record_recommendation(
        self,
        recommendation_type: str,
        command: str,
        priority_score: int,
        reason: str
    ) -> None:
        """Record a recommendation being generated."""
        self.record_event({
            'type': 'recommendation',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'recommendation_type': recommendation_type,
            'command': command,
            'priority_score': priority_score,
            'reason': reason
        })

    def record_decision(
        self,
        decision_type: str,
        question: str,
        options: List[Dict[str, str]],
        selected: Optional[str] = None
    ) -> None:
        """Record an AskUserQuestion decision."""
        self.record_event({
            'type': 'decision',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'decision_type': decision_type,
            'question': question,
            'options': options,
            'selected': selected
        })

    def finalize_recording(
        self,
        status: str = 'completed',
        summary: Optional[Dict[str, Any]] = None
    ) -> Optional[Path]:
        """Finalize recording and return file path."""
        if not self.recording_enabled:
            return None

        self.record_event({
            'type': 'session_end',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': status,
            'total_events': len(self.events),
            'summary': summary or {}
        })

        return self.recording_file


# Global singleton instance
_recorder: Optional[SessionRecorder] = None


def get_recorder() -> SessionRecorder:
    """Get or create the global recorder instance."""
    global _recorder
    if _recorder is None:
        _recorder = SessionRecorder()
    return _recorder


def record_tool_call(
    tool_name: str,
    parameters: Dict[str, Any],
    result: Optional[Any] = None,
    error: Optional[str] = None,
    duration_ms: Optional[int] = None
) -> None:
    """Convenience function to record a tool call."""
    get_recorder().record_tool_call(tool_name, parameters, result, error, duration_ms)


def record_skill_invocation(skill_name: str, arguments: Optional[str] = None) -> None:
    """Convenience function to record a skill invocation."""
    get_recorder().record_skill_invocation(skill_name, arguments)


def record_decision(
    decision_type: str,
    question: str,
    options: List[Dict[str, str]],
    selected: Optional[str] = None
) -> None:
    """Convenience function to record a decision."""
    get_recorder().record_decision(decision_type, question, options, selected)


def finalize_recording(
    status: str = 'completed',
    summary: Optional[Dict[str, Any]] = None
) -> Optional[Path]:
    """Convenience function to finalize recording."""
    return get_recorder().finalize_recording(status, summary)


def is_recording_enabled() -> bool:
    """Check if recording is currently enabled."""
    return get_recorder().recording_enabled


def record_file_read(
    file_path: str,
    content_summary: Optional[str] = None,
    relevant: bool = True
) -> None:
    """Convenience function to record a file read."""
    get_recorder().record_file_read(file_path, content_summary, relevant)


def record_reasoning(
    step: str,
    reasoning: str,
    data: Optional[Dict[str, Any]] = None
) -> None:
    """Convenience function to record reasoning."""
    get_recorder().record_reasoning(step, reasoning, data)


def record_recommendation(
    recommendation_type: str,
    command: str,
    priority_score: int,
    reason: str
) -> None:
    """Convenience function to record a recommendation."""
    get_recorder().record_recommendation(recommendation_type, command, priority_score, reason)
