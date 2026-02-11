#!/usr/bin/env python3
"""
Unit tests for Ready to Code Score calculation.

Tests all scoring dimensions, edge cases, and report generation.
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ready_to_code_score import (
    calculate_ready_to_code_score,
    format_breakdown_table,
    get_score_interpretation,
)


class TestReadyToCodeScore(unittest.TestCase):
    """Test Ready to Code Score calculation."""

    def test_perfect_score(self):
        """Test perfect state returns 100/100."""
        state = {
            "session": {"restored": True},
            "services": {
                "required_services": ["postgres", "redis"],
                "running_services": ["postgres", "redis"],
            },
            "dependencies": {"outdated_count": 0},
            "git": {"behind_remote": 0},
            "github": {"prs_needing_review": [], "issues_needing_triage": []},
        }

        score, breakdown = calculate_ready_to_code_score(state)

        self.assertEqual(score, 100)
        self.assertEqual(breakdown["session_restored"]["points"], 20)
        self.assertEqual(breakdown["services_healthy"]["points"], 20)
        self.assertEqual(breakdown["dependencies_updated"]["points"], 15)
        self.assertEqual(breakdown["branches_synced"]["points"], 15)
        self.assertEqual(breakdown["prs_reviewed"]["points"], 15)
        self.assertEqual(breakdown["issues_triaged"]["points"], 15)

    def test_worst_score(self):
        """Test worst state returns minimal score (10 from partial service credit)."""
        state = {
            "session": {"restored": False},
            "services": {
                "required_services": ["postgres", "redis", "supabase"],
                "running_services": [],
            },
            "dependencies": {"outdated_count": 50},
            "git": {"behind_remote": 100},
            "github": {
                "prs_needing_review": [{"number": i} for i in range(10)],
                "issues_needing_triage": [{"number": i} for i in range(20)],
            },
        }

        score, breakdown = calculate_ready_to_code_score(state)

        self.assertEqual(score, 10)  # Only partial credit from services
        self.assertEqual(breakdown["session_restored"]["points"], 0)
        self.assertEqual(breakdown["services_healthy"]["points"], 10)  # Partial credit
        self.assertEqual(breakdown["dependencies_updated"]["points"], 0)
        self.assertEqual(breakdown["branches_synced"]["points"], 0)
        self.assertEqual(breakdown["prs_reviewed"]["points"], 0)
        self.assertEqual(breakdown["issues_triaged"]["points"], 0)

    def test_partial_credit_scenarios(self):
        """Test partial credit for intermediate states."""
        # Services: Some running
        state = {
            "session": {"restored": True},
            "services": {
                "required_services": ["postgres", "redis"],
                "running_services": ["postgres"],  # 1 of 2
            },
            "dependencies": {"outdated_count": 2},  # Few outdated
            "git": {"behind_remote": 3},  # Few commits behind
            "github": {
                "prs_needing_review": [{"number": 1}, {"number": 2}],  # 2 PRs
                "issues_needing_triage": [{"number": 1}],  # 1 issue
            },
        }

        score, breakdown = calculate_ready_to_code_score(state)

        # Should get partial credit for most dimensions
        self.assertEqual(breakdown["session_restored"]["points"], 20)  # Full
        self.assertEqual(breakdown["services_healthy"]["points"], 10)  # Partial
        self.assertEqual(breakdown["dependencies_updated"]["points"], 10)  # Partial
        self.assertEqual(breakdown["branches_synced"]["points"], 10)  # Partial
        self.assertEqual(breakdown["prs_reviewed"]["points"], 10)  # Partial
        self.assertEqual(breakdown["issues_triaged"]["points"], 10)  # Partial (1-3 issues range)

        expected_score = 20 + 10 + 10 + 10 + 10 + 10
        self.assertEqual(score, expected_score)

    def test_no_services_required(self):
        """Test that no required services gives full points."""
        state = {
            "session": {"restored": True},
            "services": {
                "required_services": [],  # No services required
                "running_services": [],
            },
            "dependencies": {"outdated_count": 0},
            "git": {"behind_remote": 0},
            "github": {"prs_needing_review": [], "issues_needing_triage": []},
        }

        score, breakdown = calculate_ready_to_code_score(state)

        # Should get full points for services even though none running
        self.assertEqual(breakdown["services_healthy"]["points"], 20)
        self.assertEqual(score, 100)

    def test_missing_data_handling(self):
        """Test graceful handling of missing data."""
        # Empty state
        state = {}

        score, breakdown = calculate_ready_to_code_score(state)

        # Should not crash and should return some score
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

        # Check all dimensions exist in breakdown
        expected_keys = [
            "session_restored",
            "services_healthy",
            "dependencies_updated",
            "branches_synced",
            "prs_reviewed",
            "issues_triaged",
        ]

        for key in expected_keys:
            self.assertIn(key, breakdown)
            self.assertIn("points", breakdown[key])
            self.assertIn("max", breakdown[key])
            self.assertIn("status", breakdown[key])
            self.assertIn("reason", breakdown[key])

    def test_score_interpretation(self):
        """Test score interpretation grades."""
        # Test each grade range
        test_cases = [
            (95, "A+", "🌟"),
            (85, "A", "✅"),
            (75, "B", "👍"),
            (65, "C", "⚠️"),
            (55, "D", "🔧"),
            (30, "F", "❌"),
        ]

        for score, expected_grade, expected_emoji in test_cases:
            result = get_score_interpretation(score)
            self.assertEqual(result["grade"], expected_grade, f"Failed for score {score}")
            self.assertEqual(result["emoji"], expected_emoji, f"Failed for score {score}")
            self.assertIn("interpretation", result)
            self.assertIn("recommendation", result)

    def test_breakdown_table_formatting(self):
        """Test breakdown table markdown formatting."""
        breakdown = {
            "session_restored": {
                "points": 20,
                "max": 20,
                "status": "✅",
                "reason": "Session restored",
            },
            "services_healthy": {
                "points": 10,
                "max": 20,
                "status": "⚠️",
                "reason": "Missing: redis",
            },
            "dependencies_updated": {
                "points": 15,
                "max": 15,
                "status": "✅",
                "reason": "All up to date",
            },
            "branches_synced": {
                "points": 0,
                "max": 15,
                "status": "❌",
                "reason": "10 commits behind",
            },
            "prs_reviewed": {"points": 15, "max": 15, "status": "✅", "reason": "No PRs pending"},
            "issues_triaged": {
                "points": 10,
                "max": 15,
                "status": "⚠️",
                "reason": "3 issues need triage",
            },
        }

        table = format_breakdown_table(breakdown)

        # Check table structure
        lines = table.split("\n")
        self.assertEqual(len(lines), 8)  # Header + separator + 6 dimensions

        # Check header
        self.assertIn("| Check | Points | Status |", lines[0])
        self.assertIn("|-------|--------|--------|", lines[1])

        # Check all dimensions present
        self.assertIn("Session Restored", table)
        self.assertIn("Services Healthy", table)
        self.assertIn("Dependencies Updated", table)
        self.assertIn("Branches Synced", table)
        self.assertIn("PRs Reviewed", table)
        self.assertIn("Issues Triaged", table)

        # Check scoring displayed correctly
        self.assertIn("20/20", table)
        self.assertIn("10/20", table)
        self.assertIn("0/15", table)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Exactly at partial credit thresholds
        state = {
            "session": {"restored": True},
            "services": {"required_services": [], "running_services": []},
            "dependencies": {"outdated_count": 3},  # Exactly at threshold
            "git": {"behind_remote": 5},  # Exactly at threshold
            "github": {
                "prs_needing_review": [{"number": 1}, {"number": 2}],  # Exactly 2
                "issues_needing_triage": [{"number": i} for i in range(3)],  # Exactly 3
            },
        }

        score, breakdown = calculate_ready_to_code_score(state)

        # Should get partial credit at thresholds
        self.assertEqual(breakdown["dependencies_updated"]["points"], 10)
        self.assertEqual(breakdown["branches_synced"]["points"], 10)
        self.assertEqual(breakdown["prs_reviewed"]["points"], 10)
        self.assertEqual(breakdown["issues_triaged"]["points"], 10)


if __name__ == "__main__":
    unittest.main()
