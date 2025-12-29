#!/usr/bin/env python3
"""
Unit tests for Sleep Score calculation

Tests all scoring dimensions and edge cases.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.sleep_score import (
    calculate_sleep_score,
    get_score_interpretation,
    format_breakdown_table
)


class TestSleepScore(unittest.TestCase):
    """Test cases for sleep_score.py"""

    def test_perfect_score(self):
        """Test perfect 100/100 score."""
        state = {
            'git': {
                'uncommitted_files': 0,
                'merged_branches': 0
            },
            'github': {
                'issues': [],
                'ci_status': {'conclusion': 'success'}
            },
            'services': {
                'running_services': [],
                'log_files': 0
            }
        }

        score, breakdown = calculate_sleep_score(state)

        self.assertEqual(score, 100)
        self.assertEqual(breakdown['uncommitted_work_saved']['points'], 25)
        self.assertEqual(breakdown['branches_cleaned']['points'], 20)
        self.assertEqual(breakdown['issues_updated']['points'], 20)
        self.assertEqual(breakdown['ci_passing']['points'], 15)
        self.assertEqual(breakdown['services_stopped']['points'], 10)
        self.assertEqual(breakdown['logs_archived']['points'], 10)

    def test_baseline_scenario(self):
        """Test baseline scenario from manual workflow (60/100)."""
        state = {
            'git': {
                'uncommitted_files': 3,
                'merged_branches': 0,
                'stashes': 8
            },
            'github': {
                'issues': [
                    {'updatedAt': '2025-12-28T10:00:00Z'},
                    {'updatedAt': '2025-12-28T11:00:00Z'}
                ],
                'ci_status': {'conclusion': 'skipped'}
            },
            'services': {
                'running_services': [],
                'log_files': 0
            }
        }

        score, breakdown = calculate_sleep_score(state)

        # Expected: 0 + 20 + 20 + 0 + 10 + 10 = 60
        self.assertEqual(score, 60)
        self.assertEqual(breakdown['uncommitted_work_saved']['points'], 0)
        self.assertEqual(breakdown['branches_cleaned']['points'], 20)
        self.assertEqual(breakdown['issues_updated']['points'], 20)
        self.assertEqual(breakdown['ci_passing']['points'], 0)

    def test_worst_score(self):
        """Test worst possible score (0/100)."""
        state = {
            'git': {
                'uncommitted_files': 10,
                'merged_branches': 5
            },
            'github': {
                'issues': [
                    {'updatedAt': '2025-12-20T10:00:00Z'}  # Old update
                ],
                'ci_status': {'conclusion': 'failure'}
            },
            'services': {
                'running_services': ['node', 'redis', 'postgres'],
                'log_files': 15
            }
        }

        score, breakdown = calculate_sleep_score(state)

        # Some partial credit for issues (10)
        self.assertLessEqual(score, 10)

    def test_partial_credit_scenarios(self):
        """Test scenarios with partial credit."""
        # Partial credit for logs (5 points for <= 5 logs)
        state = {
            'git': {'uncommitted_files': 0, 'merged_branches': 0},
            'github': {'issues': [], 'ci_status': {'conclusion': 'success'}},
            'services': {'running_services': [], 'log_files': 3}
        }

        score, breakdown = calculate_sleep_score(state)
        self.assertEqual(breakdown['logs_archived']['points'], 5)
        self.assertEqual(score, 95)  # Lost 5 points for logs

    def test_score_interpretation(self):
        """Test score interpretation function."""
        # Perfect score
        interp = get_score_interpretation(95)
        self.assertEqual(interp['grade'], 'A+')
        self.assertEqual(interp['emoji'], '🌟')

        # Good score
        interp = get_score_interpretation(75)
        self.assertEqual(interp['grade'], 'B')

        # Poor score
        interp = get_score_interpretation(40)
        self.assertEqual(interp['grade'], 'F')

    def test_breakdown_table_formatting(self):
        """Test markdown table generation."""
        _, breakdown = calculate_sleep_score({
            'git': {'uncommitted_files': 0, 'merged_branches': 0},
            'github': {'issues': [], 'ci_status': {'conclusion': 'success'}},
            'services': {'running_services': [], 'log_files': 0}
        })

        table = format_breakdown_table(breakdown)

        self.assertIn('| Check | Points | Status |', table)
        self.assertIn('Uncommitted work saved', table)
        self.assertIn('25/25', table)
        self.assertIn('✅', table)

    def test_missing_data_handling(self):
        """Test graceful handling of missing data."""
        # Minimal state
        state = {
            'git': {},
            'github': {},
            'services': {}
        }

        score, breakdown = calculate_sleep_score(state)

        # Should not crash and should give full credit for missing data
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_edge_cases(self):
        """Test edge cases."""
        # No issues = good (should get full 20 points)
        state = {
            'git': {'uncommitted_files': 0, 'merged_branches': 0},
            'github': {'issues': [], 'ci_status': {'conclusion': 'success'}},
            'services': {'running_services': [], 'log_files': 0}
        }

        score, breakdown = calculate_sleep_score(state)
        self.assertEqual(breakdown['issues_updated']['points'], 20)

        # Issues not updated today (should get partial 10 points)
        state['github']['issues'] = [
            {'updatedAt': '2025-12-20T10:00:00Z'}  # Old
        ]

        score, breakdown = calculate_sleep_score(state)
        self.assertEqual(breakdown['issues_updated']['points'], 10)


if __name__ == '__main__':
    unittest.main()
