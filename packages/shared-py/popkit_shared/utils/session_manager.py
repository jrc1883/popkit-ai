#!/usr/bin/env python3
"""
Session Manager - Shared state across hook invocations

Manages session state that persists across multiple tool calls within
a single conversation/command execution. Uses a lock file to coordinate
between hook invocations.

Architecture:
- Session starts when first tool is called with POPKIT_RECORD=true
- All subsequent tool calls append to the same recording file
- Session ends after timeout (5 minutes) or explicit end signal
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# File locking (Unix-only) - fcntl used locally where needed
try:
    __import__("fcntl")
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False


class SessionManager:
    """Manages shared session state across hook invocations."""

    def __init__(self):
        self.sessions_dir = Path.home() / ".claude" / "popkit" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Session timeout: 5 minutes of inactivity
        self.session_timeout_seconds = 300

    def get_or_create_session(self) -> Dict[str, Any]:
        """Get current active session or create a new one."""
        session_id = os.getenv("POPKIT_RECORD_ID")
        if session_id:
            # User specified a session ID
            return self._load_or_create_session(session_id)
        else:
            # Auto-detect or create session
            return self._get_active_session()

    def _get_active_session(self) -> Dict[str, Any]:
        """Get the currently active session or create new one."""
        # Look for recent session file
        session_files = sorted(
            self.sessions_dir.glob("session-*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )

        for session_file in session_files:
            session = self._load_session(session_file)
            if session and self._is_session_active(session):
                return session

        # No active session, create new one
        return self._create_new_session()

    def _load_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Load existing session by ID or create if doesn't exist."""
        session_file = self.sessions_dir / f"session-{session_id}.json"

        if session_file.exists():
            session = self._load_session(session_file)
            if session:
                return session

        return self._create_new_session(session_id)

    def _load_session(self, session_file: Path) -> Optional[Dict[str, Any]]:
        """Load session from file with lock."""
        try:
            with open(session_file, "r") as f:
                # Acquire shared lock for reading (Unix only)
                if HAS_FCNTL:
                    import fcntl

                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    session = json.load(f)
                    return session
                finally:
                    if HAS_FCNTL:
                        import fcntl

                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def _is_session_active(self, session: Dict[str, Any]) -> bool:
        """Check if session is still active (not timed out)."""
        last_activity = session.get("last_activity_timestamp")
        if not last_activity:
            return False

        try:
            last_time = datetime.fromisoformat(last_activity)
            now = datetime.now(timezone.utc)
            elapsed = (now - last_time).total_seconds()
            return elapsed < self.session_timeout_seconds
        except (ValueError, TypeError):
            return False

    def _create_new_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session."""
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]

        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        command_name = os.getenv("POPKIT_COMMAND", "session")

        session = {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity_timestamp": datetime.now(timezone.utc).isoformat(),
            "command": command_name,
            "working_directory": os.getcwd(),
            "recording_file": f"{timestamp}-{command_name}-{session_id}.json",
            "event_count": 0,
            "environment": {
                "POPKIT_RECORD": os.getenv("POPKIT_RECORD"),
                "POPKIT_RECORD_ID": os.getenv("POPKIT_RECORD_ID"),
                "TEST_MODE": os.getenv("TEST_MODE"),
            },
        }

        self._save_session(session)
        return session

    def _save_session(self, session: Dict[str, Any]) -> None:
        """Save session to file with lock."""
        session_id = session["session_id"]
        session_file = self.sessions_dir / f"session-{session_id}.json"

        with open(session_file, "w") as f:
            # Acquire exclusive lock for writing (Unix only)
            if HAS_FCNTL:
                import fcntl

                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(session, f, indent=2)
            finally:
                if HAS_FCNTL:
                    import fcntl

                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def update_session_activity(self, session_id: str) -> None:
        """Update session's last activity timestamp."""
        session = self._load_or_create_session(session_id)
        session["last_activity_timestamp"] = datetime.now(timezone.utc).isoformat()
        session["event_count"] = session.get("event_count", 0) + 1
        self._save_session(session)

    def end_session(self, session_id: str) -> None:
        """Mark session as ended."""
        session = self._load_or_create_session(session_id)
        session["ended_at"] = datetime.now(timezone.utc).isoformat()
        session["status"] = "completed"
        self._save_session(session)

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Remove session files older than max_age_hours."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        removed = 0

        for session_file in self.sessions_dir.glob("session-*.json"):
            if session_file.stat().st_mtime < cutoff_time:
                try:
                    session_file.unlink()
                    removed += 1
                except OSError:
                    pass

        return removed


# Global singleton
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def get_current_session() -> Dict[str, Any]:
    """Get the current active session."""
    return get_session_manager().get_or_create_session()


def update_session_activity(session_id: str) -> None:
    """Update session activity timestamp."""
    get_session_manager().update_session_activity(session_id)


def end_session(session_id: str) -> None:
    """End the current session."""
    get_session_manager().end_session(session_id)
