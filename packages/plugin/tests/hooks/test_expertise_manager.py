#!/usr/bin/env python3
"""Tests for expertise_manager.py

Tests the three-tier agent expertise system (Issue #201).
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import yaml
import json

# Add utils to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks" / "utils"))

from expertise_manager import (
    ExpertiseManager,
    PendingPatternsTracker,
    Pattern,
    Issue,
    PatternExample,
    MIN_OCCURRENCES
)


class TestExpertiseManager(unittest.TestCase):
    """Test suite for ExpertiseManager"""

    def setUp(self):
        """Create temp directory for each test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.agent_id = "code-reviewer"
        self.manager = ExpertiseManager(self.agent_id, self.temp_dir)

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir)

    def test_creates_expertise_file(self):
        """Test that expertise file is created on initialization"""
        expertise_file = self.temp_dir / ".claude" / "expertise" / self.agent_id / "expertise.yaml"
        self.assertTrue(expertise_file.exists(), "Expertise YAML file should be created")

        # Verify it's valid YAML
        with open(expertise_file) as f:
            data = yaml.safe_load(f)
            self.assertEqual(data['agent_id'], self.agent_id)
            self.assertEqual(data['version'], '1.0.0')

    def test_requires_three_occurrences(self):
        """Test that patterns require 3+ occurrences before promotion (conservative threshold)"""
        # Record pattern once
        result1 = self.manager.record_pattern_occurrence(
            category="code-style",
            pattern="prefer async/await",
            trigger="callback hell detected"
        )
        self.assertIsNone(result1, "First occurrence should not promote")

        # Record pattern twice
        result2 = self.manager.record_pattern_occurrence(
            category="code-style",
            pattern="prefer async/await",
            trigger="callback hell detected"
        )
        self.assertIsNone(result2, "Second occurrence should not promote")

        # Third occurrence should promote
        result3 = self.manager.record_pattern_occurrence(
            category="code-style",
            pattern="prefer async/await",
            trigger="callback hell detected"
        )
        self.assertIsNotNone(result3, "Third occurrence should promote to expertise")
        self.assertIsInstance(result3, Pattern)
        self.assertEqual(result3.occurrences, 3)
        self.assertEqual(result3.category, "code-style")
        self.assertEqual(result3.pattern, "prefer async/await")

    def test_pending_patterns_persisted(self):
        """Test that pending patterns are saved to disk"""
        # Record pattern twice (not enough to promote)
        self.manager.record_pattern_occurrence(
            category="error-handling",
            pattern="use try/catch",
            trigger="unhandled error"
        )
        self.manager.record_pattern_occurrence(
            category="error-handling",
            pattern="use try/catch",
            trigger="unhandled error"
        )

        # Check pending.json exists
        pending_file = self.temp_dir / ".claude" / "expertise" / self.agent_id / "pending.json"
        self.assertTrue(pending_file.exists(), "Pending patterns should be persisted")

        # Verify content
        with open(pending_file) as f:
            data = json.load(f)
            key = "error-handling:use try/catch"
            self.assertIn(key, data)
            self.assertEqual(data[key]['occurrences'], 2)

    def test_adds_preference(self):
        """Test adding preferences to expertise"""
        self.manager.add_preference("code_style", "use 2-space indentation")
        self.manager.add_preference("code_style", "prefer const over let")

        expertise = self.manager.expertise
        self.assertIn("code_style", expertise.preferences)
        self.assertIn("use 2-space indentation", expertise.preferences["code_style"])
        self.assertIn("prefer const over let", expertise.preferences["code_style"])

    def test_records_issue(self):
        """Test recording common issues with conservative threshold"""
        # Record issue once - should not promote
        result1 = self.manager.record_issue(
            pattern="missing null checks",
            severity="medium",
            solution="add optional chaining",
            file_path="src/api/users.ts"
        )
        self.assertIsNone(result1, "First occurrence should not promote")

        # Record issue twice - should not promote
        result2 = self.manager.record_issue(
            pattern="missing null checks",
            severity="medium",
            solution="add optional chaining",
            file_path="src/api/users.ts"
        )
        self.assertIsNone(result2, "Second occurrence should not promote")

        # Third occurrence should promote
        issue = self.manager.record_issue(
            pattern="missing null checks",
            severity="medium",
            solution="add optional chaining",
            file_path="src/api/users.ts"
        )

        self.assertIsNotNone(issue, "Third occurrence should promote to expertise")
        self.assertEqual(issue.pattern, "missing null checks")
        self.assertEqual(issue.severity, "medium")
        self.assertEqual(issue.occurrences, 3)
        self.assertIn("src/api/users.ts", issue.files_affected)
        self.assertEqual(issue.solution, "add optional chaining")
        self.assertIn("src/api/users.ts", issue.files_affected)

    def test_updates_statistics(self):
        """Test that statistics are updated correctly"""
        initial_reviews = self.manager.expertise.stats.get('reviews_conducted', 0)

        self.manager.update_stats(
            reviews_conducted=5,
            suggestions_accepted=3,
            suggestions_rejected=2
        )

        self.assertEqual(
            self.manager.expertise.stats['reviews_conducted'],
            initial_reviews + 5
        )
        self.assertEqual(self.manager.expertise.stats['suggestions_accepted'], 3)
        self.assertEqual(self.manager.expertise.stats['suggestions_rejected'], 2)

    def test_get_summary(self):
        """Test getting expertise summary"""
        # Add some data
        for i in range(3):
            self.manager.record_pattern_occurrence(
                category="test",
                pattern=f"pattern {i}",
                trigger="test"
            )

        self.manager.add_preference("testing", "use Jest")

        summary = self.manager.get_summary()

        self.assertEqual(summary['agent_id'], self.agent_id)
        self.assertIn('total_patterns', summary)
        self.assertIn('total_preferences', summary)
        self.assertIn('last_updated', summary)


class TestPendingPatternsTracker(unittest.TestCase):
    """Test suite for PendingPatternsTracker"""

    def setUp(self):
        """Create temp directory for each test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.agent_id = "test-agent"
        self.tracker = PendingPatternsTracker(self.agent_id, self.temp_dir)

    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir)

    def test_tracks_occurrences(self):
        """Test that occurrences are tracked correctly"""
        count1 = self.tracker.record_occurrence(
            pattern_key="test:pattern1",
            category="test",
            pattern="test pattern",
            trigger="test trigger"
        )
        self.assertEqual(count1, 1)

        count2 = self.tracker.record_occurrence(
            pattern_key="test:pattern1",
            category="test",
            pattern="test pattern",
            trigger="test trigger"
        )
        self.assertEqual(count2, 2)

    def test_get_ready_patterns(self):
        """Test getting patterns ready for promotion"""
        # Record below threshold
        for i in range(2):
            self.tracker.record_occurrence(
                pattern_key="test:pattern1",
                category="test",
                pattern="test pattern 1",
                trigger="trigger"
            )

        # Record above threshold
        for i in range(3):
            self.tracker.record_occurrence(
                pattern_key="test:pattern2",
                category="test",
                pattern="test pattern 2",
                trigger="trigger"
            )

        ready = self.tracker.get_ready_patterns()
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0]['key'], "test:pattern2")
        self.assertEqual(ready[0]['occurrences'], 3)

    def test_clear_pattern(self):
        """Test clearing a pending pattern"""
        self.tracker.record_occurrence(
            pattern_key="test:pattern1",
            category="test",
            pattern="test pattern",
            trigger="trigger"
        )

        self.assertIn("test:pattern1", self.tracker.pending)

        self.tracker.clear_pattern("test:pattern1")

        self.assertNotIn("test:pattern1", self.tracker.pending)


if __name__ == '__main__':
    unittest.main()
