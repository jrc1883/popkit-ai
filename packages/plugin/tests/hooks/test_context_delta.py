#!/usr/bin/env python3
"""
Unit tests for hooks/utils/context_delta.py

Tests context delta computation and context extraction from user messages.
"""

import unittest
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks" / "utils"))

from context_delta import (
    compute_context_delta,
    extract_new_context,
    should_send_full_context,
)


class TestComputeContextDelta(unittest.TestCase):
    """Test context delta computation."""

    def test_added_field(self):
        """Test detecting added fields."""
        previous = {"project": {"name": "popkit"}}
        current = {
            "project": {"name": "popkit"},
            "infrastructure": {"redis": True}
        }

        delta = compute_context_delta(previous, current)

        self.assertIn("infrastructure", delta)
        self.assertEqual(delta["infrastructure"]["type"], "added")
        self.assertEqual(delta["infrastructure"]["value"], {"redis": True})

    def test_changed_field(self):
        """Test detecting changed fields."""
        previous = {"project": {"name": "old"}}
        current = {"project": {"name": "new"}}

        delta = compute_context_delta(previous, current)

        self.assertIn("project", delta)
        self.assertEqual(delta["project"]["type"], "changed")
        self.assertEqual(delta["project"]["value"], {"name": "new"})

    def test_removed_field(self):
        """Test detecting removed fields."""
        previous = {
            "project": {"name": "popkit"},
            "infrastructure": {"redis": True}
        }
        current = {"project": {"name": "popkit"}}

        delta = compute_context_delta(previous, current)

        self.assertIn("infrastructure", delta)
        self.assertEqual(delta["infrastructure"]["type"], "removed")
        self.assertNotIn("value", delta["infrastructure"])

    def test_unchanged_field_omitted(self):
        """Test that unchanged fields are not in delta."""
        previous = {"project": {"name": "popkit"}}
        current = {"project": {"name": "popkit"}}

        delta = compute_context_delta(previous, current)

        # Unchanged fields should not appear in delta
        self.assertEqual(len(delta), 0)

    def test_multiple_changes(self):
        """Test detecting multiple types of changes simultaneously."""
        previous = {
            "project": {"name": "old"},
            "infrastructure": {"redis": True},
            "stack": ["Next.js"]
        }
        current = {
            "project": {"name": "new"},  # Changed
            "infrastructure": {"redis": True},  # Unchanged
            "team": ["Alice", "Bob"]  # Added
            # stack removed
        }

        delta = compute_context_delta(previous, current)

        # Should have 3 changes: project changed, team added, stack removed
        self.assertEqual(len(delta), 3)
        self.assertEqual(delta["project"]["type"], "changed")
        self.assertEqual(delta["team"]["type"], "added")
        self.assertEqual(delta["stack"]["type"], "removed")

    def test_empty_contexts(self):
        """Test with empty contexts."""
        delta = compute_context_delta({}, {})
        self.assertEqual(len(delta), 0)

    def test_nested_structure_change(self):
        """Test detecting changes in nested structures."""
        previous = {
            "infrastructure": {
                "redis": True,
                "postgres": False
            }
        }
        current = {
            "infrastructure": {
                "redis": True,
                "postgres": True  # Changed from False to True
            }
        }

        delta = compute_context_delta(previous, current)

        # Entire infrastructure field should be marked as changed
        self.assertIn("infrastructure", delta)
        self.assertEqual(delta["infrastructure"]["type"], "changed")


class TestExtractNewContext(unittest.TestCase):
    """Test context extraction from user messages."""

    def test_extract_redis(self):
        """Test detecting Redis mention."""
        message = "Use Redis for caching"
        context = extract_new_context(message, {})

        self.assertIn("infrastructure", context)
        self.assertIn("redis", context["infrastructure"])
        self.assertEqual(context["infrastructure"]["redis"], {"discovered": True})

    def test_extract_postgres(self):
        """Test detecting PostgreSQL mentions."""
        messages = [
            "Use Postgres for the database",
            "Set up PostgreSQL"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                context = extract_new_context(msg, {})
                self.assertIn("infrastructure", context)
                self.assertIn("postgres", context["infrastructure"])

    def test_extract_multiple_infrastructure(self):
        """Test detecting multiple infrastructure components."""
        message = "Use Redis and MongoDB for caching and data storage"
        context = extract_new_context(message, {})

        self.assertIn("infrastructure", context)
        self.assertIn("redis", context["infrastructure"])
        self.assertIn("mongodb", context["infrastructure"])

    def test_skip_existing_infrastructure(self):
        """Test that existing infrastructure is not re-added."""
        message = "Use Redis for caching"
        existing = {
            "infrastructure": {
                "redis": {"discovered": True}
            }
        }

        context = extract_new_context(message, existing)

        # Should not add redis again
        self.assertNotIn("infrastructure", context)

    def test_extract_issue_references(self):
        """Test extracting issue references (#123)."""
        message = "Fix the bug from #123 and #456"
        context = extract_new_context(message, {})

        self.assertIn("issues", context)
        self.assertIn("#123", context["issues"])
        self.assertIn("#456", context["issues"])

    def test_skip_existing_issues(self):
        """Test that existing issues are not re-added."""
        message = "Work on #123 and #456"
        existing = {"issues": ["#123"]}

        context = extract_new_context(message, existing)

        # Should only add #456 (new)
        self.assertIn("issues", context)
        self.assertEqual(context["issues"], ["#456"])

    def test_extract_branch_mention(self):
        """Test extracting branch mentions."""
        messages = [
            "Create branch feat/user-auth",
            "Work on feat/dark-mode",
            "Fix bug in fix/login-error"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                context = extract_new_context(msg, {})
                self.assertIn("branch", context)

    def test_extract_tech_stack(self):
        """Test extracting technology stack mentions."""
        message = "Use Next.js with Supabase and Redis"
        context = extract_new_context(message, {})

        self.assertIn("stack", context)
        self.assertIn("Next.js", context["stack"])
        self.assertIn("Supabase", context["stack"])

    def test_skip_existing_tech(self):
        """Test that existing tech is not re-added."""
        message = "Use Next.js and React"
        existing = {"stack": ["Next.js"]}

        context = extract_new_context(message, existing)

        # Should only add React (new)
        self.assertIn("stack", context)
        self.assertIn("React", context["stack"])
        self.assertNotIn("Next.js", context["stack"])

    def test_extract_python_frameworks(self):
        """Test extracting Python framework mentions."""
        messages = [
            "Build API with FastAPI",
            "Use Django for the backend",
            "Flask is lightweight"
        ]

        expected_tech = ["FastAPI", "Django", "Flask"]

        for msg, tech in zip(messages, expected_tech):
            with self.subTest(msg=msg):
                context = extract_new_context(msg, {})
                self.assertIn("stack", context)
                self.assertIn(tech, context["stack"])

    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive."""
        messages = [
            "Use REDIS for caching",
            "Setup PostgreSQL database",
            "Build with NEXT.JS"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                context = extract_new_context(msg, {})
                # Should detect despite uppercase
                self.assertTrue(
                    "infrastructure" in context or "stack" in context,
                    f"Failed to detect in: {msg}"
                )

    def test_empty_message(self):
        """Test with empty message."""
        context = extract_new_context("", {})
        self.assertEqual(len(context), 0)

    def test_no_context_found(self):
        """Test message with no detectable context."""
        message = "Hello, how are you?"
        context = extract_new_context(message, {})
        self.assertEqual(len(context), 0)

    def test_combined_extraction(self):
        """Test extracting multiple types of context."""
        message = "Working on #123 in branch feat/redis-cache to add Redis support with Next.js"
        context = extract_new_context(message, {})

        # Should detect issue, branch, infrastructure, and stack
        self.assertIn("issues", context)
        self.assertIn("#123", context["issues"])

        self.assertIn("branch", context)

        self.assertIn("infrastructure", context)
        self.assertIn("redis", context["infrastructure"])

        self.assertIn("stack", context)
        self.assertIn("Next.js", context["stack"])


class TestShouldSendFullContext(unittest.TestCase):
    """Test full context trigger logic."""

    def test_first_message(self):
        """Test that first message always gets full context."""
        self.assertTrue(should_send_full_context(1, 0))

    def test_second_message(self):
        """Test that second message gets delta."""
        self.assertFalse(should_send_full_context(2, 1))

    def test_messages_2_through_20(self):
        """Test that messages 2-20 get delta."""
        for msg_num in range(2, 21):
            with self.subTest(message_number=msg_num):
                self.assertFalse(should_send_full_context(msg_num, 1))

    def test_message_21_refresh(self):
        """Test periodic refresh at message 21."""
        self.assertTrue(should_send_full_context(21, 1))

    def test_periodic_refresh_every_20(self):
        """Test that refresh happens every 20 messages."""
        # After refresh at 21, next refresh at 41
        self.assertTrue(should_send_full_context(41, 21))
        self.assertTrue(should_send_full_context(61, 41))
        self.assertTrue(should_send_full_context(81, 61))

    def test_no_refresh_between_periods(self):
        """Test no refresh between 20-message periods."""
        # After refresh at 21, messages 22-40 should be delta
        for msg_num in range(22, 41):
            with self.subTest(message_number=msg_num):
                self.assertFalse(should_send_full_context(msg_num, 21))

    def test_exactly_20_messages_since_last(self):
        """Test that exactly 20 messages triggers refresh."""
        # If last full context was at 1, then 21 is exactly 20 messages later
        self.assertTrue(should_send_full_context(21, 1))

        # If last full context was at 21, then 41 is exactly 20 messages later
        self.assertTrue(should_send_full_context(41, 21))


if __name__ == '__main__':
    unittest.main()
