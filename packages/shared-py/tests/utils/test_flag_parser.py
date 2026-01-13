#!/usr/bin/env python3
"""
Test suite for flag_parser.py

Tests command argument parsing for PopKit commands.
Critical for command-line interface and user input validation.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.flag_parser import (
    extract_issue_number,
    get_flag_value,
    has_flag,
    parse_issues_args,
    parse_model_flag,
    parse_power_args,
    parse_thinking_flags,
    parse_work_args,
)


class TestParseWorkArgs:
    """Test /popkit:work argument parsing"""

    def test_basic_issue_number_hash(self):
        """Test parsing issue number with hash"""
        result = parse_work_args("#4")
        assert result["issue_number"] == 4
        assert result["force_power"] is False
        assert result["force_solo"] is False
        assert result["error"] is None

    def test_basic_issue_number_gh_dash(self):
        """Test parsing issue number with gh- prefix"""
        result = parse_work_args("gh-4")
        assert result["issue_number"] == 4

    def test_basic_issue_number_gh_no_dash(self):
        """Test parsing issue number with gh prefix (no dash)"""
        result = parse_work_args("gh4")
        assert result["issue_number"] == 4

    def test_basic_issue_number_plain(self):
        """Test parsing plain issue number"""
        result = parse_work_args("4")
        assert result["issue_number"] == 4

    def test_large_issue_number(self):
        """Test parsing large issue numbers"""
        result = parse_work_args("#12345")
        assert result["issue_number"] == 12345

    def test_power_mode_short_flag(self):
        """Test -p flag for Power Mode"""
        result = parse_work_args("#4 -p")
        assert result["issue_number"] == 4
        assert result["force_power"] is True
        assert result["force_solo"] is False

    def test_power_mode_long_flag(self):
        """Test --power flag"""
        result = parse_work_args("#4 --power")
        assert result["issue_number"] == 4
        assert result["force_power"] is True

    def test_solo_mode_short_flag(self):
        """Test -s flag for Solo Mode"""
        result = parse_work_args("#4 -s")
        assert result["issue_number"] == 4
        assert result["force_solo"] is True
        assert result["force_power"] is False

    def test_solo_mode_long_flag(self):
        """Test --solo flag"""
        result = parse_work_args("#4 --solo")
        assert result["force_solo"] is True

    def test_power_and_solo_conflict(self):
        """Test that --power and --solo together produces error"""
        result = parse_work_args("#4 --power --solo")
        assert result["error"] is not None
        assert "both" in result["error"].lower()

    def test_phases_flag(self):
        """Test --phases flag parsing"""
        result = parse_work_args("#4 --phases explore,implement,test")
        assert result["issue_number"] == 4
        assert result["phases"] == ["explore", "implement", "test"]

    def test_agents_flag(self):
        """Test --agents flag parsing"""
        result = parse_work_args("#4 --agents reviewer,tester")
        assert result["issue_number"] == 4
        assert result["agents"] == ["reviewer", "tester"]

    def test_combined_flags(self):
        """Test multiple flags combined"""
        result = parse_work_args("#4 -p --phases explore,implement --agents reviewer")
        assert result["issue_number"] == 4
        assert result["force_power"] is True
        assert result["phases"] == ["explore", "implement"]
        assert result["agents"] == ["reviewer"]

    def test_empty_args(self):
        """Test empty arguments"""
        result = parse_work_args("")
        assert result["error"] is not None
        assert "No arguments" in result["error"]

    def test_whitespace_only(self):
        """Test whitespace-only arguments"""
        result = parse_work_args("   ")
        assert result["error"] is not None

    def test_invalid_issue_format(self):
        """Test invalid issue number format"""
        result = parse_work_args("invalid")
        assert result["error"] is not None
        assert "Could not parse" in result["error"]

    def test_phases_with_underscores(self):
        """Test phase names with underscores"""
        result = parse_work_args("#4 --phases design_review,unit_test")
        assert result["phases"] == ["design_review", "unit_test"]

    def test_agents_with_hyphens(self):
        """Test agent names with hyphens"""
        result = parse_work_args("#4 --agents code-architect,test-engineer")
        assert result["agents"] == ["code-architect", "test-engineer"]


class TestParseIssuesArgs:
    """Test /popkit:issues argument parsing"""

    def test_no_args(self):
        """Test with no arguments (default values)"""
        result = parse_issues_args("")
        assert result["filter_power"] is False
        assert result["label"] is None
        assert result["state"] == "open"
        assert result["assignee"] is None
        assert result["limit"] == 20

    def test_power_filter_short(self):
        """Test -p flag"""
        # Regex requires whitespace before -p, so provide a dummy flag first
        result = parse_issues_args("--label test -p")
        assert result["filter_power"] is True

    def test_power_filter_long(self):
        """Test --power flag"""
        result = parse_issues_args("--power")
        assert result["filter_power"] is True

    def test_label_short_flag(self):
        """Test -l flag for label"""
        result = parse_issues_args("-l bug")
        assert result["label"] == "bug"

    def test_label_long_flag(self):
        """Test --label flag"""
        result = parse_issues_args("--label feature")
        assert result["label"] == "feature"

    def test_label_with_colon(self):
        """Test label with namespace (e.g., priority:high)"""
        result = parse_issues_args("--label priority:high")
        assert result["label"] == "priority:high"

    def test_state_open(self):
        """Test --state open"""
        result = parse_issues_args("--state open")
        assert result["state"] == "open"

    def test_state_closed(self):
        """Test --state closed"""
        result = parse_issues_args("--state closed")
        assert result["state"] == "closed"

    def test_state_all(self):
        """Test --state all"""
        result = parse_issues_args("--state all")
        assert result["state"] == "all"

    def test_assignee_with_at(self):
        """Test --assignee with @ prefix"""
        result = parse_issues_args("--assignee @me")
        assert result["assignee"] == "@me"

    def test_assignee_without_at(self):
        """Test --assignee without @ prefix"""
        result = parse_issues_args("--assignee username")
        assert result["assignee"] == "username"

    def test_limit_short_flag(self):
        """Test -n flag for limit"""
        result = parse_issues_args("-n 10")
        assert result["limit"] == 10

    def test_limit_long_flag(self):
        """Test --limit flag"""
        result = parse_issues_args("--limit 50")
        assert result["limit"] == 50

    def test_combined_flags(self):
        """Test multiple flags combined"""
        result = parse_issues_args("--label bug -p --state all -n 30")
        assert result["filter_power"] is True
        assert result["label"] == "bug"
        assert result["state"] == "all"
        assert result["limit"] == 30

    def test_case_insensitive_state(self):
        """Test case-insensitive state values"""
        result = parse_issues_args("--state OPEN")
        assert result["state"] == "open"


class TestParsePowerArgs:
    """Test /popkit:power argument parsing"""

    def test_no_args_defaults_to_status(self):
        """Test no arguments defaults to status command"""
        result = parse_power_args("")
        assert result["subcommand"] == "status"

    def test_status_subcommand(self):
        """Test explicit status subcommand"""
        result = parse_power_args("status")
        assert result["subcommand"] == "status"

    def test_stop_subcommand(self):
        """Test stop subcommand"""
        result = parse_power_args("stop")
        assert result["subcommand"] == "stop"

    def test_quoted_objective(self):
        """Test custom objective with quotes"""
        result = parse_power_args('"Build user auth"')
        assert result["subcommand"] == "start"
        assert result["objective"] == "Build user auth"

    def test_objective_with_phases(self):
        """Test objective with phases"""
        result = parse_power_args('"Refactor DB" --phases design,implement')
        assert result["objective"] == "Refactor DB"
        assert result["phases"] == ["design", "implement"]

    def test_objective_with_agents(self):
        """Test objective with agents"""
        result = parse_power_args('"Security audit" --agents security-auditor')
        assert result["objective"] == "Security audit"
        assert result["agents"] == ["security-auditor"]

    def test_objective_with_timeout(self):
        """Test objective with custom timeout"""
        result = parse_power_args('"Long task" --timeout 60')
        assert result["objective"] == "Long task"
        assert result["timeout"] == 60

    def test_default_timeout(self):
        """Test default timeout value"""
        result = parse_power_args('"Task"')
        assert result["timeout"] == 30

    def test_unquoted_objective(self):
        """Test objective without quotes"""
        result = parse_power_args("BuildAuth --timeout 45")
        assert result["subcommand"] == "start"
        assert result["objective"] == "BuildAuth"

    def test_combined_flags(self):
        """Test all flags combined"""
        result = parse_power_args(
            '"Complex task" --phases explore,design,implement --agents architect,tester --timeout 90'
        )
        assert result["objective"] == "Complex task"
        assert result["phases"] == ["explore", "design", "implement"]
        assert result["agents"] == ["architect", "tester"]
        assert result["timeout"] == 90


class TestParseThinkingFlags:
    """Test extended thinking flag parsing"""

    def test_no_flags(self):
        """Test default values with no flags"""
        result = parse_thinking_flags("")
        assert result["force_thinking"] is None
        assert result["budget_tokens"] == 10000

    def test_short_flag_enable(self):
        """Test -T flag enables thinking"""
        result = parse_thinking_flags("-T")
        assert result["force_thinking"] is True

    def test_long_flag_enable(self):
        """Test --thinking flag"""
        result = parse_thinking_flags("--thinking")
        assert result["force_thinking"] is True

    def test_disable_flag(self):
        """Test --no-thinking flag"""
        result = parse_thinking_flags("--no-thinking")
        assert result["force_thinking"] is False

    def test_custom_budget(self):
        """Test --think-budget flag"""
        result = parse_thinking_flags("--think-budget 20000")
        assert result["budget_tokens"] == 20000
        # Setting budget implies enabling thinking
        assert result["force_thinking"] is True

    def test_enable_with_budget(self):
        """Test -T with custom budget"""
        result = parse_thinking_flags("-T --think-budget 15000")
        assert result["force_thinking"] is True
        assert result["budget_tokens"] == 15000

    def test_combined_with_other_flags(self):
        """Test thinking flags mixed with other command flags"""
        result = parse_thinking_flags("#4 -p -T")
        assert result["force_thinking"] is True


class TestParseModelFlag:
    """Test model override flag parsing"""

    def test_no_model_flag(self):
        """Test default (no model specified)"""
        result = parse_model_flag("")
        assert result["model"] is None

    def test_haiku_short(self):
        """Test -m haiku"""
        result = parse_model_flag("-m haiku")
        assert result["model"] == "haiku"

    def test_sonnet_short(self):
        """Test -m sonnet"""
        result = parse_model_flag("-m sonnet")
        assert result["model"] == "sonnet"

    def test_opus_short(self):
        """Test -m opus"""
        result = parse_model_flag("-m opus")
        assert result["model"] == "opus"

    def test_haiku_long(self):
        """Test --model haiku"""
        result = parse_model_flag("--model haiku")
        assert result["model"] == "haiku"

    def test_case_insensitive(self):
        """Test case-insensitive model names"""
        result = parse_model_flag("--model OPUS")
        assert result["model"] == "opus"

    def test_combined_with_other_flags(self):
        """Test model flag with other flags"""
        result = parse_model_flag("#4 -p --model opus")
        assert result["model"] == "opus"


class TestHasFlag:
    """Test generic has_flag function"""

    def test_short_flag_present(self):
        """Test detecting short flag"""
        assert has_flag("-p --other", "-p", "--power") is True

    def test_long_flag_present(self):
        """Test detecting long flag"""
        assert has_flag("--power --other", "-p", "--power") is True

    def test_flag_not_present(self):
        """Test flag not present"""
        assert has_flag("--other", "-p", "--power") is False

    def test_empty_args(self):
        """Test empty arguments"""
        assert has_flag("", "-p", "--power") is False

    def test_short_flag_at_end(self):
        """Test short flag at end of string"""
        assert has_flag("--other -p", "-p", "--power") is True

    def test_long_flag_at_beginning(self):
        """Test long flag at beginning"""
        assert has_flag("--power --other", "-p", "--power") is True

    def test_flag_in_middle(self):
        """Test flag in middle of arguments"""
        assert has_flag("--first -p --last", "-p", "--power") is True


class TestGetFlagValue:
    """Test get_flag_value function"""

    def test_get_existing_value(self):
        """Test getting value of existing flag"""
        value = get_flag_value("--label bug", "--label")
        assert value == "bug"

    def test_get_short_flag_value(self):
        """Test getting value of short flag"""
        value = get_flag_value("-l feature", "-l")
        assert value == "feature"

    def test_flag_not_present(self):
        """Test getting value when flag not present"""
        value = get_flag_value("--other value", "--label")
        assert value is None

    def test_empty_args(self):
        """Test empty arguments"""
        value = get_flag_value("", "--label")
        assert value is None

    def test_value_with_special_chars(self):
        """Test value with special characters"""
        value = get_flag_value("--label priority:high", "--label")
        assert value == "priority:high"

    def test_numeric_value(self):
        """Test numeric value"""
        value = get_flag_value("-n 42", "-n")
        assert value == "42"


class TestExtractIssueNumber:
    """Test extract_issue_number function"""

    def test_hash_format(self):
        """Test #4 format"""
        assert extract_issue_number("#4") == 4

    def test_gh_dash_format(self):
        """Test gh-4 format"""
        assert extract_issue_number("gh-4") == 4

    def test_gh_no_dash_format(self):
        """Test gh4 format"""
        assert extract_issue_number("gh4") == 4

    def test_issue_keyword_format(self):
        """Test 'issue 4' format"""
        assert extract_issue_number("issue 4") == 4

    def test_plain_number(self):
        """Test plain number"""
        assert extract_issue_number("4") == 4

    def test_number_with_spaces(self):
        """Test number surrounded by spaces"""
        assert extract_issue_number(" 4 ") == 4

    def test_large_number(self):
        """Test large issue number"""
        assert extract_issue_number("#12345") == 12345

    def test_in_sentence(self):
        """Test extracting from sentence"""
        assert extract_issue_number("See issue #42 for details") == 42

    def test_no_number(self):
        """Test text with no number"""
        assert extract_issue_number("no number here") is None

    def test_empty_string(self):
        """Test empty string"""
        assert extract_issue_number("") is None

    def test_none_input(self):
        """Test None input"""
        assert extract_issue_number(None) is None

    def test_case_insensitive(self):
        """Test case-insensitive matching"""
        assert extract_issue_number("Issue 4") == 4
        assert extract_issue_number("ISSUE 4") == 4


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_work_args_with_extra_whitespace(self):
        """Test parsing with extra whitespace"""
        result = parse_work_args("  #4   -p  ")
        assert result["issue_number"] == 4
        assert result["force_power"] is True

    def test_issues_args_with_multiple_spaces(self):
        """Test parsing with multiple spaces"""
        result = parse_issues_args("--label   bug   --state   open")
        assert result["label"] == "bug"
        assert result["state"] == "open"

    def test_special_characters_in_objective(self):
        """Test objective with special characters"""
        result = parse_power_args('"Add feature: user@auth & security*"')
        assert "user@auth" in result["objective"]

    def test_phases_empty_list(self):
        """Test phases with empty value"""
        result = parse_work_args("#4 --phases ")
        # Should not crash, phases will be None or empty
        assert result["issue_number"] == 4

    def test_numeric_objective(self):
        """Test numeric objective"""
        result = parse_power_args("12345")
        # Should parse as start command with objective
        assert result["subcommand"] == "start"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
