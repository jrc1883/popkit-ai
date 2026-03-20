#!/usr/bin/env python3
"""
Test suite for merge_findings.py

Tests YAML frontmatter parsing, section extraction, bullet point extraction,
deduplication via Jaccard similarity, tag merging, merged document generation,
and multi-file merge orchestration.

The script lives in a skills/scripts/ directory and is loaded via importlib
to keep sys.path clean.
"""

import importlib.util
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Dynamic import of the script module
# ---------------------------------------------------------------------------

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "popkit-research"
    / "skills"
    / "pop-research-merge"
    / "scripts"
    / "merge_findings.py"
)


def _load_module():
    """Load merge_findings.py as a module without executing __main__."""
    spec = importlib.util.spec_from_file_location("merge_findings", _SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    mod.__name__ = "merge_findings"
    spec.loader.exec_module(mod)
    return mod


_mod = _load_module()

parse_frontmatter = _mod.parse_frontmatter
extract_metadata = _mod.extract_metadata
extract_sections = _mod.extract_sections
extract_bullet_points = _mod.extract_bullet_points
dedupe_points = _mod.dedupe_points
merge_research_notes = _mod.merge_research_notes
generate_merged_document = _mod.generate_merged_document


# =============================================================================
# Sample content
# =============================================================================

SAMPLE_NOTE_A = """\
---
title: "Auth Research"
date: 2026-01-15
tags: [security, auth, tokens]
status: complete
---

# Auth Research

## Key Findings

- JWT tokens expire after 24 hours by default
- Refresh tokens must be stored securely
- OAuth2 is the recommended protocol

## Questions & Follow-ups

- How do we handle token revocation?
- What is the impact on mobile clients?

## References

- [OAuth2 RFC](https://tools.ietf.org/html/rfc6749)
- [JWT Best Practices](https://auth0.com/blog/jwt-best-practices)
"""

SAMPLE_NOTE_B = """\
---
title: "API Design"
date: 2026-01-20
tags: [api, design, rest]
status: draft
---

# API Design

## Key Findings

- REST endpoints should use plural nouns
- JWT tokens expire after 24 hours by default
- Rate limiting is essential for public APIs
- Versioning via URL prefix is most common

## Questions & Follow-ups

- Should we use GraphQL for some endpoints?
- How do we handle token revocation?

## References

- [REST API Guidelines](https://restfulapi.net)
- [API Versioning](https://semver.org)
"""

SAMPLE_NOTE_NO_FRONTMATTER = """\
# Plain Document

## Key Findings

- No frontmatter here
- Just plain markdown

## References

- [Example](https://example.com)
"""


# =============================================================================
# Tests -- parse_frontmatter
# =============================================================================


class TestParseFrontmatter:
    """Tests for parse_frontmatter()."""

    def test_extracts_frontmatter_and_body(self):
        """Standard YAML frontmatter between --- delimiters is split out."""
        fm, body = parse_frontmatter(SAMPLE_NOTE_A)

        assert "title:" in fm
        assert "tags:" in fm
        assert "# Auth Research" in body

    def test_no_frontmatter(self):
        """Content without frontmatter returns empty frontmatter string."""
        fm, body = parse_frontmatter(SAMPLE_NOTE_NO_FRONTMATTER)

        assert fm == ""
        assert "# Plain Document" in body

    def test_empty_content(self):
        """Empty string returns empty frontmatter and empty body."""
        fm, body = parse_frontmatter("")

        assert fm == ""
        assert body == ""

    def test_only_frontmatter(self):
        """Content that is only frontmatter with no body after it."""
        content = "---\ntitle: Test\n---"
        fm, body = parse_frontmatter(content)

        assert "title: Test" in fm
        assert body == ""

    def test_frontmatter_preserves_content_after_second_delimiter(self):
        """Body content after the closing --- is preserved verbatim."""
        content = "---\nkey: value\n---\nBody text here.\nSecond line."
        fm, body = parse_frontmatter(content)

        assert fm == "key: value"
        assert body == "Body text here.\nSecond line."

    def test_triple_dash_inside_body_not_split(self):
        """A --- inside the body (after frontmatter) does not cause a second split."""
        content = "---\ntitle: T\n---\nBody with --- in it"
        fm, body = parse_frontmatter(content)

        assert "title: T" in fm
        assert "---" in body

    def test_content_starting_with_non_dash(self):
        """Content not starting with --- is entirely body."""
        content = "Hello\n---\nstuff\n---"
        fm, body = parse_frontmatter(content)

        assert fm == ""
        assert content == body


# =============================================================================
# Tests -- extract_metadata
# =============================================================================


class TestExtractMetadata:
    """Tests for extract_metadata()."""

    def test_simple_key_value(self):
        """Scalar key: value pairs are extracted."""
        fm = "title: Auth Research\ndate: 2026-01-15\nstatus: complete"
        meta = extract_metadata(fm)

        assert meta["title"] == "Auth Research"
        assert meta["date"] == "2026-01-15"
        assert meta["status"] == "complete"

    def test_array_values(self):
        """Values in [a, b, c] format are parsed as lists."""
        fm = "tags: [security, auth, tokens]"
        meta = extract_metadata(fm)

        assert isinstance(meta["tags"], list)
        assert "security" in meta["tags"]
        assert "auth" in meta["tags"]
        assert "tokens" in meta["tags"]

    def test_empty_frontmatter(self):
        """Empty frontmatter string produces an empty dict."""
        assert extract_metadata("") == {}

    def test_value_with_colon(self):
        """A value containing a colon is handled (first colon is the delimiter)."""
        fm = "url: https://example.com"
        meta = extract_metadata(fm)

        assert meta["url"] == "https://example.com"

    def test_quoted_array_values(self):
        """Quoted strings inside arrays have quotes stripped."""
        fm = 'tags: ["security", "auth"]'
        meta = extract_metadata(fm)

        assert isinstance(meta["tags"], list)
        assert "security" in meta["tags"]
        assert "auth" in meta["tags"]

    def test_whitespace_handling(self):
        """Leading/trailing whitespace in keys and values is stripped."""
        fm = "  title  :  My Title  "
        meta = extract_metadata(fm)

        assert meta["title"] == "My Title"


# =============================================================================
# Tests -- extract_sections
# =============================================================================


class TestExtractSections:
    """Tests for extract_sections()."""

    def test_extracts_h2_sections(self):
        """Level-2 headings define section boundaries."""
        sections = extract_sections("## Section A\nContent A\n\n## Section B\nContent B")

        assert "Section A" in sections
        assert "Section B" in sections
        assert "Content A" in sections["Section A"]
        assert "Content B" in sections["Section B"]

    def test_ignores_h1_headings(self):
        """Level-1 headings are not treated as section delimiters."""
        sections = extract_sections("# Title\n\n## Real Section\nContent")

        assert "Title" not in sections
        assert "Real Section" in sections

    def test_no_sections_returns_empty(self):
        """Content with no h2 headings produces an empty dict."""
        sections = extract_sections("Just some text.\nAnother line.")

        assert sections == {}

    def test_empty_content(self):
        """Empty string produces an empty dict."""
        assert extract_sections("") == {}

    def test_last_section_captured(self):
        """The final section (no closing heading) is included."""
        content = "## Only Section\nLine 1\nLine 2"
        sections = extract_sections(content)

        assert "Only Section" in sections
        assert "Line 1" in sections["Only Section"]
        assert "Line 2" in sections["Only Section"]

    def test_section_content_stripped(self):
        """Section content has leading/trailing whitespace stripped."""
        content = "## Padded\n\n  Content here  \n\n"
        sections = extract_sections(content)

        assert sections["Padded"] == "Content here"

    def test_sample_note_sections(self):
        """The sample note fixture produces the expected sections."""
        _, body = parse_frontmatter(SAMPLE_NOTE_A)
        sections = extract_sections(body)

        assert "Key Findings" in sections
        assert "Questions & Follow-ups" in sections
        assert "References" in sections


# =============================================================================
# Tests -- extract_bullet_points
# =============================================================================


class TestExtractBulletPoints:
    """Tests for extract_bullet_points()."""

    def test_dash_bullets(self):
        """Lines starting with '- ' are captured."""
        content = "- Point one\n- Point two\n- Point three"
        points = extract_bullet_points(content)

        assert len(points) == 3
        assert points[0] == "Point one"

    def test_asterisk_bullets(self):
        """Lines starting with '* ' are captured."""
        content = "* Star one\n* Star two"
        points = extract_bullet_points(content)

        assert len(points) == 2
        assert points[0] == "Star one"

    def test_indented_bullets(self):
        """Indented bullet lines are also captured (strip removes leading spaces)."""
        content = "  - Indented one\n  - Indented two"
        points = extract_bullet_points(content)

        assert len(points) == 2
        assert points[0] == "Indented one"

    def test_no_bullets_returns_empty(self):
        """Content without bullet lines returns an empty list."""
        assert extract_bullet_points("No bullets here.") == []

    def test_empty_content(self):
        """Empty string returns an empty list."""
        assert extract_bullet_points("") == []

    def test_mixed_content(self):
        """Only bullet lines are extracted, non-bullet lines are skipped."""
        content = "Paragraph text.\n- A bullet\nMore text.\n- Another bullet"
        points = extract_bullet_points(content)

        assert len(points) == 2
        assert "Paragraph text." not in points


# =============================================================================
# Tests -- dedupe_points
# =============================================================================


class TestDedupePoints:
    """Tests for dedupe_points() using Jaccard similarity."""

    def test_exact_duplicates_removed(self):
        """Identical strings are deduplicated to one."""
        points = ["hello world", "hello world", "hello world"]
        result = dedupe_points(points)

        assert len(result) == 1
        assert result[0] == "hello world"

    def test_near_duplicates_removed(self):
        """Strings with high Jaccard similarity are deduplicated."""
        points = [
            "JWT tokens expire after 24 hours by default",
            "JWT tokens expire after 24 hours",
        ]
        result = dedupe_points(points, threshold=0.7)

        assert len(result) == 1

    def test_keeps_longer_version(self):
        """When deduplicating, the longer string is kept."""
        # Words: {jwt,tokens,expire,after,24,hours} vs {jwt,tokens,expire,after,24,hours,by,default}
        # Jaccard: intersection=6, union=8, similarity=6/8=0.75 > 0.7
        points = [
            "JWT tokens expire after 24 hours",
            "JWT tokens expire after 24 hours by default",
        ]
        result = dedupe_points(points, threshold=0.7)

        assert len(result) == 1
        assert result[0] == "JWT tokens expire after 24 hours by default"

    def test_distinct_points_preserved(self):
        """Points with low similarity are all kept."""
        points = [
            "REST endpoints should use plural nouns",
            "Rate limiting is essential for public APIs",
            "Versioning via URL prefix is most common",
        ]
        result = dedupe_points(points)

        assert len(result) == 3

    def test_empty_list(self):
        """Empty input returns an empty list."""
        assert dedupe_points([]) == []

    def test_single_item(self):
        """A single item is returned unchanged."""
        result = dedupe_points(["only one"])
        assert result == ["only one"]

    def test_threshold_zero_keeps_all(self):
        """With threshold=0, only exact duplicates are removed (similarity > 0)."""
        points = ["a b c", "a b c"]
        result = dedupe_points(points, threshold=0)
        # Exact duplicates have similarity 1.0 which is > 0
        assert len(result) == 1

    def test_threshold_one_keeps_all_non_identical(self):
        """With threshold=1.0, even very similar (but not identical) items are kept."""
        points = [
            "almost the same string here",
            "almost the same string there",
        ]
        result = dedupe_points(points, threshold=1.0)

        # Similarity < 1.0 so both are kept
        assert len(result) == 2

    def test_empty_string_handling(self):
        """Empty strings in the list are handled gracefully."""
        points = ["", "valid point", ""]
        result = dedupe_points(points)

        # Empty strings should not cause errors
        assert "valid point" in result

    def test_case_insensitive_comparison(self):
        """Jaccard comparison lowercases words, so case differences increase similarity."""
        points = [
            "JWT Tokens Are Important",
            "jwt tokens are important",
        ]
        result = dedupe_points(points, threshold=0.8)

        # Same words after lowercasing -> similarity = 1.0 -> deduplicated
        assert len(result) == 1


# =============================================================================
# Tests -- merge_research_notes (file-based orchestrator)
# =============================================================================


class TestMergeResearchNotes:
    """Tests for merge_research_notes() with tmp_path file fixtures."""

    @pytest.fixture
    def note_a(self, tmp_path):
        """Write sample note A to a temp file."""
        p = tmp_path / "note_a.md"
        p.write_text(SAMPLE_NOTE_A)
        return p

    @pytest.fixture
    def note_b(self, tmp_path):
        """Write sample note B to a temp file."""
        p = tmp_path / "note_b.md"
        p.write_text(SAMPLE_NOTE_B)
        return p

    @pytest.fixture
    def note_no_fm(self, tmp_path):
        """Write a note without frontmatter to a temp file."""
        p = tmp_path / "note_plain.md"
        p.write_text(SAMPLE_NOTE_NO_FRONTMATTER)
        return p

    def test_merges_sources(self, note_a, note_b):
        """Both file paths appear in the sources list."""
        merged = merge_research_notes([note_a, note_b])

        assert len(merged["sources"]) == 2
        assert str(note_a) in merged["sources"]
        assert str(note_b) in merged["sources"]

    def test_merges_tags(self, note_a, note_b):
        """Tags from all notes are combined (union)."""
        merged = merge_research_notes([note_a, note_b])

        tags = set(merged["tags"])
        assert "security" in tags
        assert "auth" in tags
        assert "api" in tags
        assert "design" in tags

    def test_deduplicates_findings(self, note_a, note_b):
        """Duplicate findings across notes are deduplicated."""
        merged = merge_research_notes([note_a, note_b])

        # "JWT tokens expire after 24 hours by default" appears in both notes
        jwt_findings = [f for f in merged["findings"] if "JWT" in f]
        assert len(jwt_findings) == 1

    def test_deduplicates_questions(self, note_a, note_b):
        """Duplicate questions across notes are deduplicated."""
        merged = merge_research_notes([note_a, note_b])

        # "How do we handle token revocation?" appears in both
        revocation_qs = [q for q in merged["questions"] if "revocation" in q]
        assert len(revocation_qs) == 1

    def test_deduplicates_references(self, note_a, note_b):
        """References from both notes are merged and deduplicated."""
        merged = merge_research_notes([note_a, note_b])

        assert len(merged["references"]) >= 3  # 2 from A + 2 from B, all unique

    def test_nonexistent_file_skipped(self, note_a, tmp_path):
        """A non-existent file in the list is silently skipped."""
        missing = tmp_path / "does_not_exist.md"
        merged = merge_research_notes([note_a, missing])

        assert len(merged["sources"]) == 1
        assert str(note_a) in merged["sources"]

    def test_single_file(self, note_a):
        """Merging a single file works without errors."""
        merged = merge_research_notes([note_a])

        assert len(merged["sources"]) == 1
        assert len(merged["findings"]) >= 3

    def test_empty_file_list(self):
        """Merging an empty file list produces empty results."""
        merged = merge_research_notes([])

        assert merged["sources"] == []
        assert merged["findings"] == []
        assert merged["tags"] == []

    def test_note_without_frontmatter(self, note_no_fm):
        """A note without frontmatter still has its sections extracted."""
        merged = merge_research_notes([note_no_fm])

        assert len(merged["findings"]) >= 2
        assert len(merged["tags"]) == 0

    def test_tags_converted_to_list(self, note_a):
        """The merged tags set is converted to a list for serialization."""
        merged = merge_research_notes([note_a])

        assert isinstance(merged["tags"], list)

    def test_findings_from_key_findings_section(self, note_a, note_b):
        """Only bullet points from '## Key Findings' sections are merged as findings."""
        merged = merge_research_notes([note_a, note_b])

        # Findings should include content from Key Findings sections
        all_text = " ".join(merged["findings"])
        assert "REST endpoints" in all_text or "Refresh tokens" in all_text

    def test_three_file_merge(self, note_a, note_b, note_no_fm):
        """Merging three files produces combined results from all."""
        merged = merge_research_notes([note_a, note_b, note_no_fm])

        assert len(merged["sources"]) == 3
        assert len(merged["findings"]) >= 5  # deduplicated across 3 notes


# =============================================================================
# Tests -- generate_merged_document
# =============================================================================


class TestGenerateMergedDocument:
    """Tests for generate_merged_document()."""

    @pytest.fixture
    def merged_data(self, tmp_path):
        """Create merged data from the two sample notes."""
        note_a = tmp_path / "a.md"
        note_a.write_text(SAMPLE_NOTE_A)
        note_b = tmp_path / "b.md"
        note_b.write_text(SAMPLE_NOTE_B)
        return merge_research_notes([note_a, note_b])

    def test_contains_frontmatter(self, merged_data):
        """Generated document starts with YAML frontmatter."""
        doc = generate_merged_document(merged_data)

        assert doc.startswith("---")
        assert "status: draft" in doc

    def test_uses_custom_title(self, merged_data):
        """When a title is provided, it appears in the frontmatter and heading."""
        doc = generate_merged_document(merged_data, title="Auth & API Research")

        assert 'title: "Auth & API Research"' in doc
        assert "# Auth & API Research" in doc

    def test_default_title(self, merged_data):
        """Without a title, 'Merged Research' is used."""
        doc = generate_merged_document(merged_data)

        assert "Merged Research" in doc

    def test_contains_overview_section(self, merged_data):
        """The Overview section mentions the source count."""
        doc = generate_merged_document(merged_data)

        assert "## Overview" in doc
        assert "2 source(s)" in doc

    def test_contains_key_findings_section(self, merged_data):
        """The Key Findings section lists the merged findings."""
        doc = generate_merged_document(merged_data)

        assert "## Key Findings" in doc
        # At least one bullet
        lines = doc.split("\n")
        findings_section = False
        finding_bullets = 0
        for line in lines:
            if line.strip() == "## Key Findings":
                findings_section = True
                continue
            if findings_section and line.startswith("## "):
                break
            if findings_section and line.startswith("- "):
                finding_bullets += 1

        assert finding_bullets >= 3

    def test_contains_questions_section(self, merged_data):
        """The Questions section includes checkbox items."""
        doc = generate_merged_document(merged_data)

        assert "## Questions & Follow-ups" in doc
        assert "- [ ] " in doc

    def test_contains_references_section(self, merged_data):
        """The References section lists reference links."""
        doc = generate_merged_document(merged_data)

        assert "## References" in doc

    def test_contains_sources_merged_section(self, merged_data):
        """The Sources Merged section lists all input file paths."""
        doc = generate_merged_document(merged_data)

        assert "## Sources Merged" in doc
        for source in merged_data["sources"]:
            assert source in doc

    def test_frontmatter_tags(self, merged_data):
        """The frontmatter includes merged tags."""
        doc = generate_merged_document(merged_data)

        # Tags line in frontmatter
        for line in doc.split("\n"):
            if line.startswith("tags:"):
                assert "security" in line or "api" in line
                break

    def test_frontmatter_date(self, merged_data):
        """The frontmatter includes today's date."""
        from datetime import datetime

        doc = generate_merged_document(merged_data)
        today = datetime.now().strftime("%Y-%m-%d")

        assert f"date: {today}" in doc

    def test_empty_findings(self):
        """Document with no findings still renders correctly."""
        merged = {
            "title": "",
            "sources": ["source.md"],
            "tags": [],
            "findings": [],
            "code_examples": [],
            "references": [],
            "questions": [],
        }
        doc = generate_merged_document(merged)

        assert "## Key Findings" in doc
        # No bullet points under Key Findings
        assert "## Sources Merged" in doc

    def test_no_questions_section_when_empty(self):
        """The Questions section is absent when there are no questions."""
        merged = {
            "title": "",
            "sources": ["s.md"],
            "tags": [],
            "findings": ["A finding"],
            "code_examples": [],
            "references": [],
            "questions": [],
        }
        doc = generate_merged_document(merged)

        assert "## Questions & Follow-ups" not in doc

    def test_no_references_section_when_empty(self):
        """The References section is absent when there are no references."""
        merged = {
            "title": "",
            "sources": ["s.md"],
            "tags": [],
            "findings": ["A finding"],
            "code_examples": [],
            "references": [],
            "questions": [],
        }
        doc = generate_merged_document(merged)

        assert "## References" not in doc
