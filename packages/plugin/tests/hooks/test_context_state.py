#!/usr/bin/env python3
"""
Unit tests for hooks/utils/context_state.py

Tests session context state management with atomic writes and hash-based change detection.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks" / "utils"))

from context_state import (
    get_session_context_path,
    load_context_state,
    save_context_state,
    compute_hash,
    clear_context_state,
    get_popkit_sessions_dir,
)


class TestContextState(unittest.TestCase):
    """Test suite for context_state module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # Change to test directory
        os.chdir(self.test_dir)

        # Create .git directory to simulate project root
        git_dir = Path(self.test_dir) / ".git"
        git_dir.mkdir()

    def tearDown(self):
        """Clean up after tests."""
        # Change back to original directory
        os.chdir(self.original_cwd)

        # Clean up test directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_popkit_sessions_dir_creates_directory(self):
        """Test that get_popkit_sessions_dir creates directory structure."""
        sessions_dir = get_popkit_sessions_dir()

        # Verify directory was created
        self.assertTrue(sessions_dir.exists())
        self.assertTrue(sessions_dir.is_dir())

        # Verify correct path structure (platform-independent)
        expected_parts = [".claude", "popkit", "sessions"]
        path_parts = sessions_dir.parts
        self.assertTrue(all(part in path_parts for part in expected_parts))

    def test_get_session_context_path(self):
        """Test getting session context file path."""
        session_id = "sess_test123"
        path = get_session_context_path(session_id)

        # Verify path format
        self.assertTrue(str(path).endswith(f"{session_id}-context.json"))

        # Verify path contains required directories (platform-independent)
        expected_parts = [".claude", "popkit", "sessions"]
        path_parts = path.parts
        self.assertTrue(all(part in path_parts for part in expected_parts))

    def test_load_empty_state(self):
        """Test loading non-existent state returns empty dict."""
        session_id = "sess_nonexistent"
        state = load_context_state(session_id)

        # Verify empty state structure
        self.assertEqual(state["context_sent"], {})
        self.assertEqual(state["message_count"], 0)
        self.assertEqual(state["last_full_context_message"], 0)

    def test_save_load_roundtrip(self):
        """Test that saved state can be loaded back correctly."""
        session_id = "sess_roundtrip"
        test_state = {
            "context_sent": {
                "project": {
                    "hash": "abc123",
                    "sent_at_message": 1
                },
                "infrastructure": {
                    "hash": "def456",
                    "sent_at_message": 5
                }
            },
            "message_count": 10,
            "last_full_context_message": 1
        }

        # Save state
        save_context_state(session_id, test_state)

        # Load it back
        loaded_state = load_context_state(session_id)

        # Verify it matches
        self.assertEqual(loaded_state, test_state)

    def test_save_overwrites_existing(self):
        """Test that saving overwrites existing state."""
        session_id = "sess_overwrite"

        # Save initial state
        initial_state = {
            "context_sent": {},
            "message_count": 5,
            "last_full_context_message": 1
        }
        save_context_state(session_id, initial_state)

        # Save new state
        new_state = {
            "context_sent": {"project": {"hash": "xyz"}},
            "message_count": 10,
            "last_full_context_message": 1
        }
        save_context_state(session_id, new_state)

        # Load and verify new state
        loaded_state = load_context_state(session_id)
        self.assertEqual(loaded_state, new_state)
        self.assertEqual(loaded_state["message_count"], 10)

    def test_atomic_write(self):
        """Test that saves are atomic (temp file pattern)."""
        session_id = "sess_atomic"
        test_state = {
            "context_sent": {},
            "message_count": 1,
            "last_full_context_message": 1
        }

        # Save state
        save_context_state(session_id, test_state)

        # Verify temp file doesn't exist (cleaned up after rename)
        path = get_session_context_path(session_id)
        temp_path = path.with_suffix('.tmp')
        self.assertFalse(temp_path.exists())

        # Verify final file exists
        self.assertTrue(path.exists())

    def test_load_corrupted_file(self):
        """Test that loading corrupted file returns empty state."""
        session_id = "sess_corrupted"
        path = get_session_context_path(session_id)

        # Create directory
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write corrupted JSON
        with open(path, 'w') as f:
            f.write("{invalid json}")

        # Load should return empty state (with warning)
        state = load_context_state(session_id)

        self.assertEqual(state["context_sent"], {})
        self.assertEqual(state["message_count"], 0)

    def test_compute_hash_consistency(self):
        """Test that same data produces same hash."""
        data1 = {"stack": ["Next.js", "Supabase"]}
        data2 = {"stack": ["Next.js", "Supabase"]}

        hash1 = compute_hash(data1)
        hash2 = compute_hash(data2)

        self.assertEqual(hash1, hash2)

    def test_compute_hash_different_data(self):
        """Test that different data produces different hash."""
        data1 = {"stack": ["Next.js", "Supabase"]}
        data2 = {"stack": ["React", "PostgreSQL"]}

        hash1 = compute_hash(data1)
        hash2 = compute_hash(data2)

        self.assertNotEqual(hash1, hash2)

    def test_compute_hash_order_independence(self):
        """Test that dict key order doesn't affect hash."""
        data1 = {"a": 1, "b": 2, "c": 3}
        data2 = {"c": 3, "a": 1, "b": 2}

        hash1 = compute_hash(data1)
        hash2 = compute_hash(data2)

        self.assertEqual(hash1, hash2)

    def test_compute_hash_nested_data(self):
        """Test hash computation with nested structures."""
        data = {
            "project": {
                "name": "popkit",
                "stack": ["Next.js", "Supabase"]
            },
            "infrastructure": {
                "redis": True,
                "postgres": False
            }
        }

        hash_value = compute_hash(data)

        # Verify hash is 8 characters
        self.assertEqual(len(hash_value), 8)

        # Verify hash is consistent
        self.assertEqual(hash_value, compute_hash(data))

    def test_clear_context_state(self):
        """Test clearing session context removes file."""
        session_id = "sess_clear"
        test_state = {
            "context_sent": {},
            "message_count": 5,
            "last_full_context_message": 1
        }

        # Save state
        save_context_state(session_id, test_state)

        # Verify file exists
        path = get_session_context_path(session_id)
        self.assertTrue(path.exists())

        # Clear state
        clear_context_state(session_id)

        # Verify file is gone
        self.assertFalse(path.exists())

    def test_clear_nonexistent_state(self):
        """Test that clearing non-existent state doesn't error."""
        session_id = "sess_nonexistent_clear"

        # Should not raise exception
        try:
            clear_context_state(session_id)
        except Exception as e:
            self.fail(f"clear_context_state raised exception: {e}")

    def test_multiple_sessions(self):
        """Test handling multiple concurrent sessions."""
        session1 = "sess_multi1"
        session2 = "sess_multi2"

        state1 = {
            "context_sent": {"project": {"hash": "aaa"}},
            "message_count": 5,
            "last_full_context_message": 1
        }

        state2 = {
            "context_sent": {"project": {"hash": "bbb"}},
            "message_count": 10,
            "last_full_context_message": 1
        }

        # Save both
        save_context_state(session1, state1)
        save_context_state(session2, state2)

        # Load and verify both
        loaded1 = load_context_state(session1)
        loaded2 = load_context_state(session2)

        self.assertEqual(loaded1, state1)
        self.assertEqual(loaded2, state2)
        self.assertNotEqual(loaded1, loaded2)

    def test_unicode_handling(self):
        """Test that Unicode data is handled correctly."""
        session_id = "sess_unicode"
        state = {
            "context_sent": {
                "description": "Fix bug with émojis 🎉 and ünicode"
            },
            "message_count": 1,
            "last_full_context_message": 1
        }

        # Save and load
        save_context_state(session_id, state)
        loaded = load_context_state(session_id)

        # Verify Unicode preserved
        self.assertEqual(loaded, state)
        self.assertEqual(
            loaded["context_sent"]["description"],
            "Fix bug with émojis 🎉 and ünicode"
        )

    def test_hash_with_unicode(self):
        """Test hash computation with Unicode data."""
        data1 = {"text": "Hello 世界"}
        data2 = {"text": "Hello 世界"}
        data3 = {"text": "Hello World"}

        hash1 = compute_hash(data1)
        hash2 = compute_hash(data2)
        hash3 = compute_hash(data3)

        # Same Unicode should hash the same
        self.assertEqual(hash1, hash2)

        # Different text should hash differently
        self.assertNotEqual(hash1, hash3)


if __name__ == '__main__':
    unittest.main()
