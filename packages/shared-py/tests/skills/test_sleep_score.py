#!/usr/bin/env python3
"""
Test suite for sleep_score.py

Tests Sleep Score calculation for nightly routine.
Critical for determining project health before shutdown.
"""

import sys
import pytest
from pathlib import Path
from datetime import datetime

# Add popkit-dev skills to path
sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent.parent.parent
        / "popkit-dev"
        / "skills"
        / "pop-nightly"
        / "scripts"
    ),
)

from sleep_score import calculate_sleep_score, get_score_interpretation, format_breakdown_table


class TestCalculateSleepScore:
    """Test sleep score calculation logic"""

    def test_perfect_score(self):
        """Test perfect score with all conditions met"""
        state = {
            "git": {"uncommitted_files": 0, "merged_branches": 0},
            "github": {"issues": [], "ci_status": {"conclusion": "success"}},
            "services": {"running_services": [], "log_files": 0},
            "timestamp": datetime.now().isoformat(),
        }

        score, breakdown = calculate_sleep_score(state)

        assert score == 100
        assert breakdown["uncommitted_work_saved"]["points"] == 25
        assert breakdown["branches_cleaned"]["points"] == 20
        assert breakdown["issues_updated"]["points"] == 20
        assert breakdown["ci_passing"]["points"] == 15
        assert breakdown["services_stopped"]["points"] == 10
        assert breakdown["logs_archived"]["points"] == 10

    def test_zero_score_worst_case(self):
        """Test worst case scenario"""
        state = {
            "git": {"uncommitted_files": 10, "merged_branches": 5},
            "github": {
                "issues": [{"number": 1, "title": "Issue 1", "updatedAt": "2020-01-01T00:00:00Z"}],
                "ci_status": {"conclusion": "failure"},
            },
            "services": {
                "running_services": ["postgres", "redis", "elasticsearch"],
                "log_files": 20,
            },
        }

        score, breakdown = calculate_sleep_score(state)

        # Only partial credit for issues (10) since not all checks completely fail
        assert score == 10
        assert breakdown["uncommitted_work_saved"]["points"] == 0
        assert breakdown["branches_cleaned"]["points"] == 0
        assert breakdown["issues_updated"]["points"] == 10  # Partial credit
        assert breakdown["ci_passing"]["points"] == 0
        assert breakdown["services_stopped"]["points"] == 0
        assert breakdown["logs_archived"]["points"] == 0

    def test_empty_state(self):
        """Test with empty state dict"""
        state = {}

        score, breakdown = calculate_sleep_score(state)

        # Should handle missing keys gracefully
        assert 0 <= score <= 100
        assert "uncommitted_work_saved" in breakdown
        assert "branches_cleaned" in breakdown

    def test_uncommitted_files_zero(self):
        """Test when no uncommitted files"""
        state = {"git": {"uncommitted_files": 0}, "github": {}, "services": {}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["uncommitted_work_saved"]["points"] == 25
        assert breakdown["uncommitted_work_saved"]["status"] == "✅"

    def test_uncommitted_files_present(self):
        """Test when uncommitted files exist"""
        state = {"git": {"uncommitted_files": 5}, "github": {}, "services": {}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["uncommitted_work_saved"]["points"] == 0
        assert breakdown["uncommitted_work_saved"]["status"] == "❌"
        assert "5 uncommitted files" in breakdown["uncommitted_work_saved"]["reason"]

    def test_branches_cleaned_no_merged(self):
        """Test when no merged branches"""
        state = {"git": {"merged_branches": 0}, "github": {}, "services": {}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["branches_cleaned"]["points"] == 20
        assert breakdown["branches_cleaned"]["status"] == "✅"

    def test_branches_cleaned_has_merged(self):
        """Test when merged branches exist"""
        state = {"git": {"merged_branches": 3}, "github": {}, "services": {}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["branches_cleaned"]["points"] == 0
        assert breakdown["branches_cleaned"]["status"] == "❌"
        assert "3 merged branches" in breakdown["branches_cleaned"]["reason"]

    def test_issues_no_open_issues(self):
        """Test when no open issues"""
        state = {"git": {}, "github": {"issues": []}, "services": {}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["issues_updated"]["points"] == 20
        assert breakdown["issues_updated"]["status"] == "✅"
        assert "No open issues" in breakdown["issues_updated"]["reason"]

    def test_issues_all_updated_today(self):
        """Test when all issues updated today"""
        today = datetime.now().strftime("%Y-%m-%d")
        state = {
            "git": {},
            "github": {
                "issues": [
                    {"number": 1, "title": "Issue 1", "updatedAt": f"{today}T10:00:00Z"},
                    {"number": 2, "title": "Issue 2", "updatedAt": f"{today}T11:00:00Z"},
                ]
            },
            "services": {},
        }

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["issues_updated"]["points"] == 20
        assert breakdown["issues_updated"]["status"] == "✅"

    def test_issues_some_not_updated_today(self):
        """Test when some issues not updated today"""
        today = datetime.now().strftime("%Y-%m-%d")
        state = {
            "git": {},
            "github": {
                "issues": [
                    {"number": 1, "title": "Issue 1", "updatedAt": f"{today}T10:00:00Z"},
                    {"number": 2, "title": "Issue 2", "updatedAt": "2020-01-01T10:00:00Z"},
                ]
            },
            "services": {},
        }

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["issues_updated"]["points"] == 10  # Partial credit
        assert breakdown["issues_updated"]["status"] == "⚠️"

    def test_ci_status_success(self):
        """Test when CI is passing"""
        state = {"git": {}, "github": {"ci_status": {"conclusion": "success"}}, "services": {}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["ci_passing"]["points"] == 15
        assert breakdown["ci_passing"]["status"] == "✅"

    def test_ci_status_failure(self):
        """Test when CI is failing"""
        state = {"git": {}, "github": {"ci_status": {"conclusion": "failure"}}, "services": {}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["ci_passing"]["points"] == 0
        assert breakdown["ci_passing"]["status"] == "❌"

    def test_ci_status_skipped(self):
        """Test when CI is skipped"""
        state = {"git": {}, "github": {"ci_status": {"conclusion": "skipped"}}, "services": {}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["ci_passing"]["points"] == 0
        assert breakdown["ci_passing"]["status"] == "❌"

    def test_ci_status_pending(self):
        """Test when CI status is pending/unknown"""
        state = {"git": {}, "github": {"ci_status": {"conclusion": "pending"}}, "services": {}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["ci_passing"]["points"] == 0
        assert breakdown["ci_passing"]["status"] == "⚠️"

    def test_services_stopped_none_running(self):
        """Test when no services running"""
        state = {"git": {}, "github": {}, "services": {"running_services": []}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["services_stopped"]["points"] == 10
        assert breakdown["services_stopped"]["status"] == "✅"

    def test_services_stopped_some_running(self):
        """Test when services still running"""
        state = {"git": {}, "github": {}, "services": {"running_services": ["postgres", "redis"]}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["services_stopped"]["points"] == 0
        assert breakdown["services_stopped"]["status"] == "❌"
        assert "2 services still running" in breakdown["services_stopped"]["reason"]

    def test_logs_archived_no_logs(self):
        """Test when no log files"""
        state = {"git": {}, "github": {}, "services": {"log_files": 0}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["logs_archived"]["points"] == 10
        assert breakdown["logs_archived"]["status"] == "✅"

    def test_logs_archived_few_logs(self):
        """Test with 1-5 log files (partial credit)"""
        state = {"git": {}, "github": {}, "services": {"log_files": 3}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["logs_archived"]["points"] == 5
        assert breakdown["logs_archived"]["status"] == "⚠️"

    def test_logs_archived_many_logs(self):
        """Test with many log files"""
        state = {"git": {}, "github": {}, "services": {"log_files": 10}}

        score, breakdown = calculate_sleep_score(state)

        assert breakdown["logs_archived"]["points"] == 0
        assert breakdown["logs_archived"]["status"] == "❌"


class TestScoreInterpretation:
    """Test score interpretation logic"""

    def test_interpretation_a_plus(self):
        """Test A+ grade (90-100)"""
        interp = get_score_interpretation(95)

        assert interp["grade"] == "A+"
        assert interp["emoji"] == "🌟"
        assert "Perfect shutdown" in interp["interpretation"]

    def test_interpretation_a(self):
        """Test A grade (80-89)"""
        interp = get_score_interpretation(85)

        assert interp["grade"] == "A"
        assert interp["emoji"] == "✅"
        assert "Excellent" in interp["interpretation"]

    def test_interpretation_b(self):
        """Test B grade (70-79)"""
        interp = get_score_interpretation(75)

        assert interp["grade"] == "B"
        assert interp["emoji"] == "👍"
        assert "Good" in interp["interpretation"]

    def test_interpretation_c(self):
        """Test C grade (60-69)"""
        interp = get_score_interpretation(65)

        assert interp["grade"] == "C"
        assert interp["emoji"] == "⚠️"
        assert "Fair" in interp["interpretation"]

    def test_interpretation_d(self):
        """Test D grade (50-59)"""
        interp = get_score_interpretation(55)

        assert interp["grade"] == "D"
        assert interp["emoji"] == "⚠️"
        assert "Below average" in interp["interpretation"]

    def test_interpretation_f(self):
        """Test F grade (0-49)"""
        interp = get_score_interpretation(30)

        assert interp["grade"] == "F"
        assert interp["emoji"] == "❌"
        assert "Poor" in interp["interpretation"]

    def test_interpretation_boundaries(self):
        """Test grade boundaries"""
        assert get_score_interpretation(90)["grade"] == "A+"
        assert get_score_interpretation(89)["grade"] == "A"
        assert get_score_interpretation(80)["grade"] == "A"
        assert get_score_interpretation(79)["grade"] == "B"
        assert get_score_interpretation(70)["grade"] == "B"
        assert get_score_interpretation(69)["grade"] == "C"


class TestFormatBreakdownTable:
    """Test breakdown table formatting"""

    def test_format_breakdown_basic(self):
        """Test basic table formatting"""
        breakdown = {
            "uncommitted_work_saved": {
                "points": 25,
                "max": 25,
                "status": "✅",
                "reason": "No uncommitted changes",
            },
            "branches_cleaned": {
                "points": 0,
                "max": 20,
                "status": "❌",
                "reason": "3 merged branches",
            },
        }

        table = format_breakdown_table(breakdown)

        assert "| Check | Points | Status |" in table
        assert "|-------|--------|--------|" in table
        assert "| Uncommitted work saved | 25/25 |" in table
        assert "| Branches cleaned | 0/20 |" in table

    def test_format_breakdown_all_checks(self):
        """Test table with all 6 checks"""
        breakdown = {
            "uncommitted_work_saved": {"points": 25, "max": 25, "status": "✅", "reason": "OK"},
            "branches_cleaned": {"points": 20, "max": 20, "status": "✅", "reason": "OK"},
            "issues_updated": {"points": 20, "max": 20, "status": "✅", "reason": "OK"},
            "ci_passing": {"points": 15, "max": 15, "status": "✅", "reason": "OK"},
            "services_stopped": {"points": 10, "max": 10, "status": "✅", "reason": "OK"},
            "logs_archived": {"points": 10, "max": 10, "status": "✅", "reason": "OK"},
        }

        table = format_breakdown_table(breakdown)

        assert "Uncommitted work saved" in table
        assert "Branches cleaned" in table
        assert "Issues updated" in table
        assert "CI passing" in table
        assert "Services stopped" in table
        assert "Logs archived" in table


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_missing_git_section(self):
        """Test when git section is missing"""
        state = {"github": {}, "services": {}}

        score, breakdown = calculate_sleep_score(state)

        assert 0 <= score <= 100
        assert "uncommitted_work_saved" in breakdown
        assert "branches_cleaned" in breakdown

    def test_missing_github_section(self):
        """Test when github section is missing"""
        state = {"git": {}, "services": {}}

        score, breakdown = calculate_sleep_score(state)

        assert 0 <= score <= 100
        assert "issues_updated" in breakdown
        assert "ci_passing" in breakdown

    def test_missing_services_section(self):
        """Test when services section is missing"""
        state = {"git": {}, "github": {}}

        score, breakdown = calculate_sleep_score(state)

        assert 0 <= score <= 100
        assert "services_stopped" in breakdown
        assert "logs_archived" in breakdown

    def test_negative_counts(self):
        """Test handling of negative counts"""
        state = {
            "git": {"uncommitted_files": -5, "merged_branches": -10},
            "github": {},
            "services": {"log_files": -3},
        }

        score, breakdown = calculate_sleep_score(state)

        # Should handle gracefully
        assert 0 <= score <= 100

    def test_very_large_counts(self):
        """Test handling of very large counts"""
        state = {
            "git": {"uncommitted_files": 1000000, "merged_branches": 1000000},
            "github": {},
            "services": {"running_services": list(range(1000)), "log_files": 1000000},
        }

        score, breakdown = calculate_sleep_score(state)

        # Score should still be in valid range
        assert 0 <= score <= 100

    def test_null_values(self):
        """Test handling of None values"""
        state = {"git": None, "github": None, "services": None}

        # Should handle None values gracefully or raise TypeError
        try:
            score, breakdown = calculate_sleep_score(state)
            assert 0 <= score <= 100
        except (TypeError, AttributeError):
            # Acceptable to fail with TypeError on None values
            pass

    def test_string_instead_of_numbers(self):
        """Test handling of string values where numbers expected"""
        state = {
            "git": {"uncommitted_files": "many", "merged_branches": "several"},
            "github": {},
            "services": {"log_files": "lots"},
        }

        # Should handle gracefully
        try:
            score, breakdown = calculate_sleep_score(state)
            assert 0 <= score <= 100
        except (TypeError, ValueError):
            # Acceptable to raise type error
            pass

    def test_malformed_issue_dates(self):
        """Test handling of malformed issue dates"""
        state = {
            "git": {},
            "github": {
                "issues": [
                    {"number": 1, "title": "Issue 1", "updatedAt": "invalid-date"},
                    {"number": 2, "title": "Issue 2", "updatedAt": None},
                ]
            },
            "services": {},
        }

        # Should handle gracefully
        score, breakdown = calculate_sleep_score(state)

        assert 0 <= score <= 100
        assert "issues_updated" in breakdown

    def test_missing_ci_status_fields(self):
        """Test when ci_status is present but conclusion is missing"""
        state = {"git": {}, "github": {"ci_status": {}}, "services": {}}

        score, breakdown = calculate_sleep_score(state)

        assert 0 <= score <= 100
        assert "ci_passing" in breakdown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
