#!/usr/bin/env python3
"""
Test suite for ready_to_code_score.py

Tests Ready to Code Score calculation for morning routine.
Critical for determining if development environment is ready.
"""

import sys
import pytest
from pathlib import Path

# Add popkit-dev skills to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "popkit-dev" / "skills" / "pop-morning" / "scripts"))

from ready_to_code_score import (
    calculate_ready_to_code_score,
    get_score_interpretation,
    format_breakdown_table
)


class TestCalculateReadyToCodeScore:
    """Test score calculation logic"""

    def test_perfect_score(self):
        """Test perfect score with all conditions met"""
        state = {
            'session': {'restored': True},
            'services': {'required_services': [], 'running_services': []},
            'dependencies': {'outdated_count': 0},
            'git': {'behind_remote': 0},
            'github': {'prs_needing_review': [], 'issues_needing_triage': []}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert score == 100
        assert breakdown['session_restored']['points'] == 20
        assert breakdown['services_healthy']['points'] == 20
        assert breakdown['dependencies_updated']['points'] == 15
        assert breakdown['branches_synced']['points'] == 15
        assert breakdown['prs_reviewed']['points'] == 15
        assert breakdown['issues_triaged']['points'] == 15

    def test_zero_score(self):
        """Test worst case scenario with all checks failing"""
        state = {
            'session': {'restored': False},
            'services': {
                'required_services': ['postgres', 'redis'],
                'running_services': []
            },
            'dependencies': {'outdated_count': 10},
            'git': {'behind_remote': 20},
            'github': {
                'prs_needing_review': [1, 2, 3, 4],
                'issues_needing_triage': [1, 2, 3, 4, 5]
            }
        }

        score, breakdown = calculate_ready_to_code_score(state)

        # Only services gets 10 (partial credit)
        assert score == 10
        assert breakdown['session_restored']['points'] == 0
        assert breakdown['services_healthy']['points'] == 10
        assert breakdown['dependencies_updated']['points'] == 0
        assert breakdown['branches_synced']['points'] == 0
        assert breakdown['prs_reviewed']['points'] == 0
        assert breakdown['issues_triaged']['points'] == 0

    def test_empty_state(self):
        """Test with completely empty state"""
        state = {}

        score, breakdown = calculate_ready_to_code_score(state)

        # Should handle missing keys gracefully
        assert 0 <= score <= 100
        assert 'session_restored' in breakdown
        assert 'services_healthy' in breakdown

    def test_session_restored_true(self):
        """Test session restored grants full points"""
        state = {
            'session': {'restored': True},
            'services': {},
            'dependencies': {},
            'git': {},
            'github': {}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['session_restored']['points'] == 20
        assert breakdown['session_restored']['status'] == '✅'

    def test_session_not_restored(self):
        """Test missing session grants no points"""
        state = {
            'session': {'restored': False},
            'services': {},
            'dependencies': {},
            'git': {},
            'github': {}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['session_restored']['points'] == 0
        assert breakdown['session_restored']['status'] == '❌'

    def test_services_no_required_services(self):
        """Test when no services are required"""
        state = {
            'session': {},
            'services': {'required_services': [], 'running_services': []},
            'dependencies': {},
            'git': {},
            'github': {}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['services_healthy']['points'] == 20
        assert 'No dev services required' in breakdown['services_healthy']['reason']

    def test_services_all_running(self):
        """Test when all required services are running"""
        state = {
            'session': {},
            'services': {
                'required_services': ['postgres', 'redis'],
                'running_services': ['postgres', 'redis']
            },
            'dependencies': {},
            'git': {},
            'github': {}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['services_healthy']['points'] == 20
        assert breakdown['services_healthy']['status'] == '✅'

    def test_services_missing_some(self):
        """Test when some required services are missing"""
        state = {
            'session': {},
            'services': {
                'required_services': ['postgres', 'redis', 'elasticsearch'],
                'running_services': ['postgres']
            },
            'dependencies': {},
            'git': {},
            'github': {}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['services_healthy']['points'] == 10
        assert breakdown['services_healthy']['status'] == '⚠️'
        assert 'redis' in breakdown['services_healthy']['reason']

    def test_dependencies_all_updated(self):
        """Test when all dependencies are current"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {'outdated_count': 0},
            'git': {},
            'github': {}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['dependencies_updated']['points'] == 15
        assert breakdown['dependencies_updated']['status'] == '✅'

    def test_dependencies_few_outdated(self):
        """Test with 1-3 outdated dependencies"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {'outdated_count': 2},
            'git': {},
            'github': {}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['dependencies_updated']['points'] == 10
        assert breakdown['dependencies_updated']['status'] == '⚠️'

    def test_dependencies_many_outdated(self):
        """Test with many outdated dependencies"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {'outdated_count': 10},
            'git': {},
            'github': {}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['dependencies_updated']['points'] == 0
        assert breakdown['dependencies_updated']['status'] == '❌'

    def test_branches_synced(self):
        """Test when branch is up to date"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {},
            'git': {'behind_remote': 0},
            'github': {}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['branches_synced']['points'] == 15
        assert breakdown['branches_synced']['status'] == '✅'

    def test_branches_few_commits_behind(self):
        """Test when 1-5 commits behind"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {},
            'git': {'behind_remote': 3},
            'github': {}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['branches_synced']['points'] == 10
        assert breakdown['branches_synced']['status'] == '⚠️'

    def test_branches_many_commits_behind(self):
        """Test when many commits behind"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {},
            'git': {'behind_remote': 20},
            'github': {}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['branches_synced']['points'] == 0
        assert breakdown['branches_synced']['status'] == '❌'

    def test_prs_no_reviews_needed(self):
        """Test when no PRs need review"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {},
            'git': {},
            'github': {'prs_needing_review': []}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['prs_reviewed']['points'] == 15
        assert breakdown['prs_reviewed']['status'] == '✅'

    def test_prs_few_reviews_needed(self):
        """Test with 1-2 PRs needing review"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {},
            'git': {},
            'github': {'prs_needing_review': [1, 2]}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['prs_reviewed']['points'] == 10
        assert breakdown['prs_reviewed']['status'] == '⚠️'

    def test_prs_many_reviews_needed(self):
        """Test with many PRs needing review"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {},
            'git': {},
            'github': {'prs_needing_review': [1, 2, 3, 4, 5]}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['prs_reviewed']['points'] == 0
        assert breakdown['prs_reviewed']['status'] == '❌'

    def test_issues_all_triaged(self):
        """Test when all issues are triaged"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {},
            'git': {},
            'github': {'issues_needing_triage': []}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['issues_triaged']['points'] == 15
        assert breakdown['issues_triaged']['status'] == '✅'

    def test_issues_few_need_triage(self):
        """Test with 1-3 issues needing triage"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {},
            'git': {},
            'github': {'issues_needing_triage': [1, 2, 3]}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['issues_triaged']['points'] == 10
        assert breakdown['issues_triaged']['status'] == '⚠️'

    def test_issues_many_need_triage(self):
        """Test with many issues needing triage"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {},
            'git': {},
            'github': {'issues_needing_triage': [1, 2, 3, 4, 5, 6]}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert breakdown['issues_triaged']['points'] == 0
        assert breakdown['issues_triaged']['status'] == '❌'


class TestScoreInterpretation:
    """Test score interpretation logic"""

    def test_interpretation_a_plus(self):
        """Test A+ grade (90-100)"""
        interp = get_score_interpretation(95)

        assert interp['grade'] == 'A+'
        assert interp['emoji'] == '🌟'
        assert 'Excellent' in interp['interpretation']
        assert 'immediately' in interp['recommendation'].lower()

    def test_interpretation_a(self):
        """Test A grade (80-89)"""
        interp = get_score_interpretation(85)

        assert interp['grade'] == 'A'
        assert interp['emoji'] == '✅'
        assert 'Very Good' in interp['interpretation']

    def test_interpretation_b(self):
        """Test B grade (70-79)"""
        interp = get_score_interpretation(75)

        assert interp['grade'] == 'B'
        assert interp['emoji'] == '👍'
        assert 'Good' in interp['interpretation']

    def test_interpretation_c(self):
        """Test C grade (60-69)"""
        interp = get_score_interpretation(65)

        assert interp['grade'] == 'C'
        assert interp['emoji'] == '⚠️'
        assert 'Fair' in interp['interpretation']

    def test_interpretation_d(self):
        """Test D grade (50-59)"""
        interp = get_score_interpretation(55)

        assert interp['grade'] == 'D'
        assert interp['emoji'] == '🔧'
        assert 'Poor' in interp['interpretation']

    def test_interpretation_f(self):
        """Test F grade (0-49)"""
        interp = get_score_interpretation(30)

        assert interp['grade'] == 'F'
        assert interp['emoji'] == '❌'
        assert 'Not Ready' in interp['interpretation']

    def test_interpretation_boundary_90(self):
        """Test boundary at 90"""
        assert get_score_interpretation(90)['grade'] == 'A+'
        assert get_score_interpretation(89)['grade'] == 'A'

    def test_interpretation_boundary_80(self):
        """Test boundary at 80"""
        assert get_score_interpretation(80)['grade'] == 'A'
        assert get_score_interpretation(79)['grade'] == 'B'

    def test_interpretation_boundary_50(self):
        """Test boundary at 50"""
        assert get_score_interpretation(50)['grade'] == 'D'
        assert get_score_interpretation(49)['grade'] == 'F'

    def test_interpretation_zero(self):
        """Test score of 0"""
        interp = get_score_interpretation(0)
        assert interp['grade'] == 'F'

    def test_interpretation_hundred(self):
        """Test score of 100"""
        interp = get_score_interpretation(100)
        assert interp['grade'] == 'A+'


class TestFormatBreakdownTable:
    """Test breakdown table formatting"""

    def test_format_breakdown_basic(self):
        """Test basic table formatting"""
        breakdown = {
            'session_restored': {
                'points': 20,
                'max': 20,
                'status': '✅',
                'reason': 'Session restored'
            },
            'services_healthy': {
                'points': 10,
                'max': 20,
                'status': '⚠️',
                'reason': 'Some services down'
            }
        }

        table = format_breakdown_table(breakdown)

        assert '| Check | Points | Status |' in table
        assert '|-------|--------|--------|' in table
        assert '| Session Restored | 20/20 |' in table
        assert '| Services Healthy | 10/20 |' in table
        assert '✅ Session restored' in table
        assert '⚠️ Some services down' in table

    def test_format_breakdown_all_dimensions(self):
        """Test table with all 6 dimensions"""
        breakdown = {
            'session_restored': {'points': 20, 'max': 20, 'status': '✅', 'reason': 'OK'},
            'services_healthy': {'points': 20, 'max': 20, 'status': '✅', 'reason': 'OK'},
            'dependencies_updated': {'points': 15, 'max': 15, 'status': '✅', 'reason': 'OK'},
            'branches_synced': {'points': 15, 'max': 15, 'status': '✅', 'reason': 'OK'},
            'prs_reviewed': {'points': 15, 'max': 15, 'status': '✅', 'reason': 'OK'},
            'issues_triaged': {'points': 15, 'max': 15, 'status': '✅', 'reason': 'OK'}
        }

        table = format_breakdown_table(breakdown)

        # All 6 checks should be present
        assert table.count('|') >= 24  # Header + separator + 6 rows
        assert 'Session Restored' in table
        assert 'Services Healthy' in table
        assert 'Dependencies Updated' in table
        assert 'Branches Synced' in table
        assert 'PRs Reviewed' in table
        assert 'Issues Triaged' in table

    def test_format_breakdown_empty(self):
        """Test with empty breakdown"""
        breakdown = {}

        table = format_breakdown_table(breakdown)

        # Should still have header
        assert '| Check | Points | Status |' in table
        assert '|-------|--------|--------|' in table

    def test_format_breakdown_preserves_order(self):
        """Test that table preserves defined order"""
        breakdown = {
            'issues_triaged': {'points': 15, 'max': 15, 'status': '✅', 'reason': 'Last'},
            'session_restored': {'points': 20, 'max': 20, 'status': '✅', 'reason': 'First'}
        }

        table = format_breakdown_table(breakdown)
        lines = table.split('\n')

        # Session Restored should appear before Issues Triaged
        session_idx = next(i for i, line in enumerate(lines) if 'Session Restored' in line)
        issues_idx = next(i for i, line in enumerate(lines) if 'Issues Triaged' in line)

        assert session_idx < issues_idx


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_missing_github_section(self):
        """Test when github section is missing entirely"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {},
            'git': {}
            # No 'github' key
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert 0 <= score <= 100
        assert 'prs_reviewed' in breakdown
        assert 'issues_triaged' in breakdown

    def test_missing_git_section(self):
        """Test when git section is missing"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {},
            'github': {}
            # No 'git' key
        }

        score, breakdown = calculate_ready_to_code_score(state)

        assert 0 <= score <= 100
        assert 'branches_synced' in breakdown

    def test_negative_counts(self):
        """Test handling of negative counts (should not crash)"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {'outdated_count': -5},
            'git': {'behind_remote': -10},
            'github': {}
        }

        score, breakdown = calculate_ready_to_code_score(state)

        # Should handle gracefully, likely treat as 0
        assert 0 <= score <= 100

    def test_very_large_counts(self):
        """Test handling of very large counts"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {'outdated_count': 1000000},
            'git': {'behind_remote': 1000000},
            'github': {
                'prs_needing_review': list(range(10000)),
                'issues_needing_triage': list(range(10000))
            }
        }

        score, breakdown = calculate_ready_to_code_score(state)

        # Should cap at 0 points, not go negative
        assert 0 <= score <= 100

    def test_null_values(self):
        """Test handling of None values"""
        state = {
            'session': None,
            'services': None,
            'dependencies': None,
            'git': None,
            'github': None
        }

        # Should handle None values gracefully or raise TypeError
        try:
            score, breakdown = calculate_ready_to_code_score(state)
            assert 0 <= score <= 100
        except (TypeError, AttributeError):
            # Acceptable to fail with TypeError on None values
            pass

    def test_string_instead_of_numbers(self):
        """Test handling of string values where numbers expected"""
        state = {
            'session': {},
            'services': {},
            'dependencies': {'outdated_count': 'many'},
            'git': {'behind_remote': 'lots'},
            'github': {}
        }

        # Should handle gracefully (likely default to 0)
        try:
            score, breakdown = calculate_ready_to_code_score(state)
            assert 0 <= score <= 100
        except (TypeError, ValueError):
            # Acceptable to raise type error if strict validation
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
