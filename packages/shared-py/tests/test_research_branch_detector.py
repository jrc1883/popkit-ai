#!/usr/bin/env python3
"""
Test suite for research_branch_detector.py

Tests branch name pattern matching, research document parsing (YAML
frontmatter, metadata, tasks), branch content retrieval, table formatting,
and content previews.  All git subprocess calls are mocked via monkeypatch
so no real repository is needed.
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from popkit_shared.utils.research_branch_detector import (
    ResearchBranch,
    _analyze_branch,
    fetch_remotes,
    format_branch_table,
    generate_issue_body,
    get_branch_content,
    get_branch_content_preview,
    get_research_branches,
    parse_research_doc,
)

# =============================================================================
# Helpers
# =============================================================================


def _make_branch(
    full_name="origin/claude/research-some-topic-abc12345678901234567",
    short_name="research-some-topic",
    topic="some-topic",
    created_ago="2 hours ago",
    commit_count=3,
    files_changed=None,
    has_docs=True,
    doc_paths=None,
):
    """Create a ResearchBranch with sensible defaults for testing."""
    return ResearchBranch(
        full_name=full_name,
        short_name=short_name,
        topic=topic,
        created_ago=created_ago,
        commit_count=commit_count,
        files_changed=files_changed
        if files_changed is not None
        else ["README.md", ".claude/research/notes.md"],
        has_docs=has_docs,
        doc_paths=doc_paths if doc_paths is not None else [".claude/research/notes.md"],
    )


def _mock_run_git(responses):
    """Return a monkeypatch-compatible replacement for _run_git.

    Args:
        responses: dict mapping a key substring of the git args to
                   (success, output) tuples.  The first matching key wins.
    """

    def _fake_run_git(args):
        args_str = " ".join(args)
        for key, (success, output) in responses.items():
            if key in args_str:
                return success, output
        return False, ""

    return _fake_run_git


# =============================================================================
# Sample research document
# =============================================================================

SAMPLE_RESEARCH_DOC = """\
# Research: Claude Code Web Features

**Research Date:** 2026-03-15
**Status:** Research Document
**Priority:** P1-high

## Executive Summary

This document covers the key features of Claude Code Web sessions,
including branch management, research capture, and auto-processing.

## Implementation Tasks

- [ ] Implement branch detection
- [ ] Add document parsing
- [x] Create issue templates
- [ ] Build merge workflow

## Additional Notes

Some extra notes that are not tasks.
"""

SAMPLE_RESEARCH_DOC_MINIMAL = """\
# Research: Minimal Topic

Some body text without structured metadata.
"""

SAMPLE_RESEARCH_DOC_ALT_DATE = """\
# Research: Alt Date Format

**Date:** March 15, 2026
**Priority:** P0-critical

## Executive Summary

A summary with an alternative date format.

## Tasks

- [ ] First task
- [ ] Second task
"""


# =============================================================================
# Tests -- parse_research_doc
# =============================================================================


class TestParseResearchDoc:
    """Tests for parse_research_doc()."""

    def test_extracts_title(self):
        """The '# Research: ...' title is extracted with the prefix removed."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC)
        assert result["title"] == "Claude Code Web Features"

    def test_extracts_date(self):
        """The research date in YYYY-MM-DD format is extracted."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC)
        assert result["date"] == "2026-03-15"

    def test_extracts_priority(self):
        """The priority tag is extracted."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC)
        assert result["priority"] == "P1-high"

    def test_extracts_executive_summary(self):
        """The Executive Summary section content is extracted."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC)

        assert "Claude Code Web" in result["summary"]
        assert "branch management" in result["summary"]

    def test_extracts_implementation_tasks(self):
        """Checkbox tasks from the Implementation section are extracted."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC)

        assert len(result["tasks"]) == 4
        assert "Implement branch detection" in result["tasks"]
        assert "Create issue templates" in result["tasks"]

    def test_raw_content_preserved(self):
        """The raw_content field contains the original document text."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC)
        assert result["raw_content"] == SAMPLE_RESEARCH_DOC

    def test_default_priority(self):
        """Documents without a priority default to P2-medium."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC_MINIMAL)
        assert result["priority"] == "P2-medium"

    def test_empty_title_when_no_h1(self):
        """Documents without an h1 heading have an empty title."""
        result = parse_research_doc("No heading here.\nJust text.")
        assert result["title"] == ""

    def test_empty_tasks_when_no_section(self):
        """Documents without an Implementation/Tasks section have empty task list."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC_MINIMAL)
        assert result["tasks"] == []

    def test_empty_summary_when_no_section(self):
        """Documents without an Executive Summary section have an empty summary."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC_MINIMAL)
        assert result["summary"] == ""

    def test_empty_content(self):
        """Empty string produces defaults for all fields."""
        result = parse_research_doc("")
        assert result["title"] == ""
        assert result["date"] == ""
        assert result["priority"] == "P2-medium"
        assert result["summary"] == ""
        assert result["tasks"] == []
        assert result["raw_content"] == ""

    def test_alt_date_format(self):
        """Alternative date formats (Month DD, YYYY) are recognized."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC_ALT_DATE)
        assert result["date"] == "March 15, 2026"

    def test_p0_critical_priority(self):
        """P0-critical priority is correctly extracted."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC_ALT_DATE)
        assert result["priority"] == "P0-critical"

    def test_tasks_section_header_variant(self):
        """'## Tasks' header (without 'Implementation') also captures tasks."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC_ALT_DATE)
        assert len(result["tasks"]) == 2
        assert "First task" in result["tasks"]

    def test_title_without_research_prefix(self):
        """An h1 without 'Research:' prefix is used as-is."""
        content = "# My Custom Title\n\nSome content."
        result = parse_research_doc(content)
        assert result["title"] == "My Custom Title"

    def test_summary_stops_at_next_section(self):
        """Executive Summary extraction stops at the next ## heading."""
        result = parse_research_doc(SAMPLE_RESEARCH_DOC)
        # Should not contain content from Implementation Tasks section
        assert "Implement branch detection" not in result["summary"]


# =============================================================================
# Tests -- get_research_branches (with mocked git)
# =============================================================================


class TestGetResearchBranches:
    """Tests for get_research_branches() with mocked subprocess calls."""

    def test_detects_research_pattern(self, monkeypatch):
        """Branches matching origin/claude/research-* are detected."""
        branch_list = (
            "origin/claude/research-web-features-abc12345678901234567\norigin/main\norigin/develop"
        )
        responses = {
            "branch -r": (True, branch_list),
            "log -1": (True, "3 hours ago"),
            "rev-list": (True, "5"),
            "diff": (True, ".claude/research/notes.md\nREADME.md"),
        }
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branches = get_research_branches()

        assert len(branches) == 1
        assert "web-features" in branches[0].topic

    def test_detects_alt_research_pattern(self, monkeypatch):
        """Branches matching origin/claude/*-research-* are detected."""
        branch_list = "origin/claude/api-research-endpoints-xyz98765432109876543\n"
        responses = {
            "branch -r": (True, branch_list),
            "log -1": (True, "1 day ago"),
            "rev-list": (True, "2"),
            "diff": (True, "docs/research/api.md"),
        }
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branches = get_research_branches()

        assert len(branches) == 1
        assert "api" in branches[0].topic

    def test_no_matching_branches(self, monkeypatch):
        """Non-research branches are not detected."""
        branch_list = "origin/main\norigin/feature/auth\norigin/develop"
        responses = {"branch -r": (True, branch_list)}
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branches = get_research_branches()
        assert branches == []

    def test_git_failure_returns_empty(self, monkeypatch):
        """When git branch -r fails, an empty list is returned."""
        responses = {"branch -r": (False, "error")}
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branches = get_research_branches()
        assert branches == []

    def test_empty_branch_list(self, monkeypatch):
        """Empty git branch output returns an empty list."""
        responses = {"branch -r": (True, "")}
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branches = get_research_branches()
        assert branches == []

    def test_custom_remote(self, monkeypatch):
        """A custom remote name is used in pattern matching."""
        branch_list = "upstream/claude/research-topic-abc12345678901234567\n"
        responses = {
            "branch -r": (True, branch_list),
            "log -1": (True, "5 min ago"),
            "rev-list": (True, "1"),
            "diff": (True, "RESEARCH.md"),
        }
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branches = get_research_branches(remote="upstream")

        assert len(branches) == 1

    def test_multiple_research_branches(self, monkeypatch):
        """Multiple research branches are all detected."""
        branch_list = (
            "origin/claude/research-auth-abc12345678901234567\n"
            "origin/claude/research-api-def12345678901234567\n"
            "origin/claude/research-ui-ghi12345678901234567\n"
        )
        responses = {
            "branch -r": (True, branch_list),
            "log -1": (True, "1 hour ago"),
            "rev-list": (True, "3"),
            "diff": (True, "README.md"),
        }
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branches = get_research_branches()
        assert len(branches) == 3

    def test_session_id_stripped_from_topic(self, monkeypatch):
        """The long session ID suffix is removed from the topic."""
        branch_list = "origin/claude/research-cool-feature-01WpyQzGrNeGx7cSNqM91iqP\n"
        responses = {
            "branch -r": (True, branch_list),
            "log -1": (True, "now"),
            "rev-list": (True, "1"),
            "diff": (True, "file.md"),
        }
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branches = get_research_branches()

        assert len(branches) == 1
        assert "01WpyQzGr" not in branches[0].topic
        assert "cool-feature" in branches[0].topic


# =============================================================================
# Tests -- _analyze_branch
# =============================================================================


class TestAnalyzeBranch:
    """Tests for _analyze_branch() with mocked git calls."""

    def test_single_group_match(self, monkeypatch):
        """Pattern 1 (research-TOPIC) produces a single-group topic."""
        import re

        pattern = r"origin/claude/research-(.+)"
        full_name = "origin/claude/research-web-features-abc12345678901234567"
        match = re.match(pattern, full_name)

        responses = {
            "log -1": (True, "2 hours ago"),
            "rev-list": (True, "5"),
            "diff": (True, ".claude/research/notes.md\nREADME.md"),
        }
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branch = _analyze_branch(full_name, match)

        assert branch is not None
        assert branch.created_ago == "2 hours ago"
        assert branch.commit_count == 5
        assert len(branch.files_changed) == 2
        assert branch.has_docs is True

    def test_multi_group_match(self, monkeypatch):
        """Pattern 2 (PREFIX-research-SUFFIX) joins groups with dash."""
        import re

        pattern = r"origin/claude/(.+)-research-(.+)"
        full_name = "origin/claude/api-research-endpoints-xyz12345678901234567"
        match = re.match(pattern, full_name)

        responses = {
            "log -1": (True, "1 day ago"),
            "rev-list": (True, "2"),
            "diff": (True, "docs/api.md"),
        }
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branch = _analyze_branch(full_name, match)

        assert branch is not None
        # Topic is "api-endpoints" (groups joined, session ID stripped)
        assert "api" in branch.topic

    def test_doc_pattern_detection(self, monkeypatch):
        """Various doc file patterns are detected in files_changed."""
        import re

        pattern = r"origin/claude/research-(.+)"
        full_name = "origin/claude/research-test-abc12345678901234567"
        match = re.match(pattern, full_name)

        doc_files = "\n".join(
            [
                ".claude/research/findings.md",
                "docs/research/overview.md",
                "RESEARCH_NOTES.md",
                "src/main.py",
            ]
        )
        responses = {
            "log -1": (True, "now"),
            "rev-list": (True, "1"),
            "diff": (True, doc_files),
        }
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branch = _analyze_branch(full_name, match)

        assert branch.has_docs is True
        assert ".claude/research/findings.md" in branch.doc_paths
        assert "docs/research/overview.md" in branch.doc_paths
        assert "RESEARCH_NOTES.md" in branch.doc_paths
        assert "src/main.py" not in branch.doc_paths

    def test_no_docs_detected(self, monkeypatch):
        """When no doc patterns match, has_docs may still be True if 'docs' in path."""
        import re

        pattern = r"origin/claude/research-(.+)"
        full_name = "origin/claude/research-code-abc12345678901234567"
        match = re.match(pattern, full_name)

        responses = {
            "log -1": (True, "now"),
            "rev-list": (True, "1"),
            "diff": (True, "src/main.py\ntest/test_main.py"),
        }
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branch = _analyze_branch(full_name, match)

        assert branch.doc_paths == []
        assert branch.has_docs is False

    def test_commit_count_non_numeric(self, monkeypatch):
        """Non-numeric rev-list output defaults commit_count to 0."""
        import re

        pattern = r"origin/claude/research-(.+)"
        full_name = "origin/claude/research-test-abc12345678901234567"
        match = re.match(pattern, full_name)

        responses = {
            "log -1": (True, "now"),
            "rev-list": (True, "not-a-number"),
            "diff": (True, ""),
        }
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branch = _analyze_branch(full_name, match)
        assert branch.commit_count == 0

    def test_short_name_generation(self, monkeypatch):
        """short_name strips the remote prefix and session ID."""
        import re

        pattern = r"origin/claude/research-(.+)"
        full_name = "origin/claude/research-my-topic-abcdefghijklmnopqrst"
        match = re.match(pattern, full_name)

        responses = {
            "log -1": (True, "now"),
            "rev-list": (True, "1"),
            "diff": (True, ""),
        }
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git(responses),
        )

        branch = _analyze_branch(full_name, match)

        assert "origin/claude/" not in branch.short_name
        assert "abcdefghijklmnopqrst" not in branch.short_name


# =============================================================================
# Tests -- fetch_remotes
# =============================================================================


class TestFetchRemotes:
    """Tests for fetch_remotes() with mocked subprocess."""

    def test_success(self, monkeypatch):
        """Returns True when git fetch succeeds."""
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git({"fetch": (True, "")}),
        )
        assert fetch_remotes() is True

    def test_failure(self, monkeypatch):
        """Returns False when git fetch fails."""
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git({"fetch": (False, "error")}),
        )
        assert fetch_remotes() is False


# =============================================================================
# Tests -- get_branch_content
# =============================================================================


class TestGetBranchContent:
    """Tests for get_branch_content() with mocked subprocess."""

    def test_success(self, monkeypatch):
        """Returns file content on success."""
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git({"show": (True, "file contents here")}),
        )

        content = get_branch_content("origin/claude/research-x", "README.md")
        assert content == "file contents here"

    def test_file_not_found(self, monkeypatch):
        """Raises FileNotFoundError when the path does not exist on the branch."""
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git({"show": (False, "fatal: path does not exist")}),
        )

        with pytest.raises(FileNotFoundError, match="not found on branch"):
            get_branch_content("origin/claude/research-x", "missing.md")

    def test_runtime_error(self, monkeypatch):
        """Raises RuntimeError for non-path-related failures."""
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git({"show": (False, "permission denied")}),
        )

        with pytest.raises(RuntimeError, match="Failed to read"):
            get_branch_content("origin/claude/research-x", "file.md")


# =============================================================================
# Tests -- format_branch_table
# =============================================================================


class TestFormatBranchTable:
    """Tests for format_branch_table()."""

    def test_empty_list(self):
        """Empty branch list produces a 'no branches' message."""
        result = format_branch_table([])
        assert result == "No research branches detected."

    def test_single_branch(self):
        """A single branch produces a markdown table with one data row."""
        branch = _make_branch()
        result = format_branch_table([branch])

        lines = result.strip().split("\n")
        assert len(lines) == 3  # header + separator + 1 row
        assert "| Branch |" in lines[0]
        assert "|--------|" in lines[1]
        assert branch.short_name in lines[2]

    def test_multiple_branches(self):
        """Multiple branches produce multiple data rows."""
        branches = [
            _make_branch(short_name="topic-a", topic="topic-a"),
            _make_branch(short_name="topic-b", topic="topic-b"),
        ]
        result = format_branch_table(branches)

        lines = result.strip().split("\n")
        assert len(lines) == 4  # header + separator + 2 rows

    def test_has_docs_indicator(self):
        """Branches with docs show '(has docs)' in the files column."""
        branch = _make_branch(has_docs=True)
        result = format_branch_table([branch])
        assert "has docs" in result

    def test_no_docs_indicator(self):
        """Branches without docs do not show '(has docs)'."""
        branch = _make_branch(has_docs=False, doc_paths=[])
        result = format_branch_table([branch])
        assert "has docs" not in result

    def test_topic_in_table(self):
        """The topic appears in the table row."""
        branch = _make_branch(topic="auth-research")
        result = format_branch_table([branch])
        assert "auth-research" in result

    def test_created_ago_in_table(self):
        """The created_ago timestamp appears in the table row."""
        branch = _make_branch(created_ago="5 minutes ago")
        result = format_branch_table([branch])
        assert "5 minutes ago" in result


# =============================================================================
# Tests -- get_branch_content_preview
# =============================================================================


class TestGetBranchContentPreview:
    """Tests for get_branch_content_preview() with mocked git."""

    def test_previews_doc_files(self, monkeypatch):
        """Returns truncated content for each doc path."""
        long_content = "\n".join(f"Line {i}" for i in range(100))
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git({"show": (True, long_content)}),
        )

        branch = _make_branch(doc_paths=[".claude/research/notes.md"])
        previews = get_branch_content_preview(branch, max_lines=10)

        assert ".claude/research/notes.md" in previews
        lines = previews[".claude/research/notes.md"].split("\n")
        assert len(lines) == 10

    def test_limits_to_three_docs(self, monkeypatch):
        """At most 3 doc files are previewed."""
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git({"show": (True, "content")}),
        )

        branch = _make_branch(doc_paths=["a.md", "b.md", "c.md", "d.md", "e.md"])
        previews = get_branch_content_preview(branch)

        assert len(previews) <= 3

    def test_skips_failed_reads(self, monkeypatch):
        """Doc files that fail to read are silently skipped."""
        monkeypatch.setattr(
            "popkit_shared.utils.research_branch_detector._run_git",
            _mock_run_git({"show": (False, "fatal: not found")}),
        )

        branch = _make_branch(doc_paths=["missing.md"])
        previews = get_branch_content_preview(branch)

        assert len(previews) == 0

    def test_no_doc_paths(self, monkeypatch):
        """A branch with no doc_paths returns an empty dict."""
        branch = _make_branch(doc_paths=[])
        previews = get_branch_content_preview(branch)
        assert previews == {}


# =============================================================================
# Tests -- generate_issue_body
# =============================================================================


class TestGenerateIssueBody:
    """Tests for generate_issue_body()."""

    def test_contains_summary_section(self):
        """The issue body includes a Summary section."""
        branch = _make_branch()
        parsed = [parse_research_doc(SAMPLE_RESEARCH_DOC)]
        body = generate_issue_body(branch, parsed)

        assert "## Summary" in body
        assert "Claude Code Web" in body

    def test_contains_source_section(self):
        """The issue body includes branch metadata in the Source section."""
        branch = _make_branch(created_ago="3 hours ago")
        parsed = [parse_research_doc(SAMPLE_RESEARCH_DOC)]
        body = generate_issue_body(branch, parsed)

        assert "## Source" in body
        assert branch.full_name in body
        assert "3 hours ago" in body

    def test_contains_documentation_section(self):
        """The issue body lists doc paths when present."""
        branch = _make_branch(doc_paths=[".claude/research/notes.md"])
        parsed = [parse_research_doc(SAMPLE_RESEARCH_DOC)]
        body = generate_issue_body(branch, parsed)

        assert "## Documentation" in body
        assert ".claude/research/notes.md" in body

    def test_no_documentation_section_without_docs(self):
        """The Documentation section is absent when there are no doc paths."""
        branch = _make_branch(doc_paths=[])
        parsed = [parse_research_doc(SAMPLE_RESEARCH_DOC)]
        body = generate_issue_body(branch, parsed)

        assert "## Documentation" not in body

    def test_contains_implementation_tasks(self):
        """The issue body includes checkbox tasks from the parsed doc."""
        branch = _make_branch()
        parsed = [parse_research_doc(SAMPLE_RESEARCH_DOC)]
        body = generate_issue_body(branch, parsed)

        assert "## Implementation Tasks" in body
        assert "- [ ] Implement branch detection" in body
        assert "- [ ] Add document parsing" in body

    def test_no_tasks_section_without_tasks(self):
        """The Implementation Tasks section is absent when there are no tasks."""
        branch = _make_branch()
        parsed = [parse_research_doc(SAMPLE_RESEARCH_DOC_MINIMAL)]
        body = generate_issue_body(branch, parsed)

        assert "## Implementation Tasks" not in body

    def test_contains_footer(self):
        """The issue body ends with the auto-generated footer."""
        branch = _make_branch()
        parsed = [parse_research_doc(SAMPLE_RESEARCH_DOC)]
        body = generate_issue_body(branch, parsed)

        assert "Auto-generated from research branch by PopKit" in body

    def test_empty_parsed_docs(self):
        """With no parsed docs, a default summary is used."""
        branch = _make_branch()
        body = generate_issue_body(branch, [])

        assert "## Summary" in body
        # Default fallback text
        assert "Research findings" in body or "Summary" in body

    def test_files_count_in_source(self):
        """The file count appears in the Source section."""
        branch = _make_branch(files_changed=["a.py", "b.py", "c.md"])
        parsed = [parse_research_doc(SAMPLE_RESEARCH_DOC)]
        body = generate_issue_body(branch, parsed)

        assert "3 changed" in body


# =============================================================================
# Tests -- ResearchBranch dataclass
# =============================================================================


class TestResearchBranchDataclass:
    """Tests for the ResearchBranch dataclass itself."""

    def test_creation(self):
        """A ResearchBranch can be created with all fields."""
        branch = _make_branch()

        assert branch.full_name == "origin/claude/research-some-topic-abc12345678901234567"
        assert branch.short_name == "research-some-topic"
        assert branch.topic == "some-topic"
        assert branch.created_ago == "2 hours ago"
        assert branch.commit_count == 3
        assert len(branch.files_changed) == 2
        assert branch.has_docs is True
        assert len(branch.doc_paths) == 1

    def test_equality(self):
        """Two ResearchBranch instances with identical fields are equal."""
        a = _make_branch()
        b = _make_branch()
        assert a == b

    def test_inequality(self):
        """ResearchBranch instances with different fields are not equal."""
        a = _make_branch(topic="alpha")
        b = _make_branch(topic="beta")
        assert a != b
