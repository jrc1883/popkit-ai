#!/usr/bin/env python3
"""
Session Context State Management

Manages session context state with atomic writes and hash-based change detection.
Used by hooks to track what context has been sent to Claude across messages.

Storage: .claude/popkit/sessions/<session-id>-context.json
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict

# Constants
POPKIT_DIR = ".claude/popkit"
SESSIONS_SUBDIR = "sessions"


def get_popkit_sessions_dir() -> Path:
    """
    Get the .claude/popkit/sessions directory path.

    Searches upward from current directory to find project root,
    then returns .claude/popkit/sessions directory path.

    Returns:
        Path to .claude/popkit/sessions directory
    """
    current = Path.cwd()

    # Search upward for project root (.git directory)
    for parent in [current] + list(current.parents):
        git_dir = parent / ".git"
        if git_dir.exists():
            sessions_dir = parent / POPKIT_DIR / SESSIONS_SUBDIR
            sessions_dir.mkdir(parents=True, exist_ok=True)
            return sessions_dir

    # Fallback: create in current directory
    sessions_dir = current / POPKIT_DIR / SESSIONS_SUBDIR
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def get_session_context_path(session_id: str) -> Path:
    """
    Get path to session context file.

    Args:
        session_id: Unique session identifier

    Returns:
        Path to session context JSON file

    Example:
        >>> path = get_session_context_path("sess_abc123")
        >>> str(path)
        '.claude/popkit/sessions/sess_abc123-context.json'
    """
    sessions_dir = get_popkit_sessions_dir()
    return sessions_dir / f"{session_id}-context.json"


def load_context_state(session_id: str) -> Dict[str, Any]:
    """
    Load context state from file, return empty dict if not found.

    Args:
        session_id: Unique session identifier

    Returns:
        Context state dict with structure:
        {
            "context_sent": {
                "field_name": {
                    "hash": "abc123",
                    "sent_at_message": 1
                },
                ...
            },
            "message_count": 0,
            "last_full_context_message": 0
        }

    Example:
        >>> state = load_context_state("sess_abc123")
        >>> state["message_count"]
        0
    """
    path = get_session_context_path(session_id)

    if not path.exists():
        # Return empty state structure
        return {"context_sent": {}, "message_count": 0, "last_full_context_message": 0}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # If file is corrupted, return empty state
        # Log warning but don't crash
        print(f"Warning: Failed to load context state: {e}", file=__import__("sys").stderr)
        return {"context_sent": {}, "message_count": 0, "last_full_context_message": 0}


def save_context_state(session_id: str, state: Dict[str, Any]) -> None:
    """
    Atomically save context state to file.

    Uses atomic write pattern: write to temp file, then rename.
    This ensures no partial writes on crash.

    Args:
        session_id: Unique session identifier
        state: Context state dict to save

    Raises:
        IOError: If unable to write to file

    Example:
        >>> state = {
        ...     "context_sent": {"project": {"hash": "abc123", "sent_at_message": 1}},
        ...     "message_count": 1,
        ...     "last_full_context_message": 1
        ... }
        >>> save_context_state("sess_abc123", state)
    """
    path = get_session_context_path(session_id)

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: write to temp file, then rename
    temp_path = path.with_suffix(".tmp")

    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        # Atomic rename (overwrites existing file)
        # On Windows, need to remove destination first
        if os.name == "nt" and path.exists():
            path.unlink()

        temp_path.rename(path)

    except Exception as e:
        # Clean up temp file if something went wrong
        if temp_path.exists():
            temp_path.unlink()
        raise IOError(f"Failed to save context state: {e}")


def compute_hash(data: Any) -> str:
    """
    Compute hash of context data for change detection.

    Converts data to JSON (with sorted keys for consistency),
    then computes SHA256 hash. Returns first 8 characters.

    Args:
        data: Any JSON-serializable data

    Returns:
        8-character hash string

    Example:
        >>> compute_hash({"stack": ["Next.js", "Supabase"]})
        'a1b2c3d4'
        >>> compute_hash({"stack": ["Next.js", "Supabase"]})  # Same input
        'a1b2c3d4'  # Same hash
        >>> compute_hash({"stack": ["React", "PostgreSQL"]})  # Different input
        'e5f6g7h8'  # Different hash
    """
    # Convert to JSON with sorted keys for consistent hashing
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)

    # Compute SHA256 hash
    hash_obj = hashlib.sha256(serialized.encode("utf-8"))

    # Return first 8 characters (sufficient for collision detection)
    return hash_obj.hexdigest()[:8]


def clear_context_state(session_id: str) -> None:
    """
    Clear session context (called on SessionStart).

    Removes the session context file if it exists.
    This ensures each session starts with a clean slate.

    Args:
        session_id: Unique session identifier

    Example:
        >>> clear_context_state("sess_abc123")
    """
    path = get_session_context_path(session_id)

    if path.exists():
        try:
            path.unlink()
        except OSError as e:
            # Log warning but don't crash
            print(f"Warning: Failed to clear context state: {e}", file=__import__("sys").stderr)


# Public API
__all__ = [
    "get_session_context_path",
    "load_context_state",
    "save_context_state",
    "compute_hash",
    "clear_context_state",
]
