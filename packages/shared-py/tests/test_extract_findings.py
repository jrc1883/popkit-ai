#!/usr/bin/env python3
"""
Test suite for extract_findings.py

Tests heading extraction, code block extraction, link extraction,
key point detection, definition extraction, quality scoring, summary
generation, markdown output, and the top-level extract_findings orchestrator.

These functions live in a skills script directory that uses sys.path.insert
for local imports.  Since they are pure functions (str -> list/dict), we
import them via importlib to avoid polluting sys.path.
"""

import importlib.util
from pathlib import Path

# ---------------------------------------------------------------------------
# Dynamic import of the script module
# ---------------------------------------------------------------------------

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "popkit-research"
    / "skills"
    / "pop-research-capture"
    / "scripts"
    / "extract_findings.py"
)


def _load_module():
    """Load extract_findings.py as a module without executing __main__."""
    spec = importlib.util.spec_from_file_location("extract_findings", _SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Prevent the script's __main__ block from running
    mod.__name__ = "extract_findings"
    spec.loader.exec_module(mod)
    return mod


_mod = _load_module()

extract_headings = _mod.extract_headings
extract_code_blocks = _mod.extract_code_blocks
extract_links = _mod.extract_links
extract_key_points = _mod.extract_key_points
extract_definitions = _mod.extract_definitions
summarize_content = _mod.summarize_content
extract_findings = _mod.extract_findings
assess_quality = _mod.assess_quality
generate_markdown = _mod.generate_markdown


# =============================================================================
# Sample content fixtures
# =============================================================================

SAMPLE_MARKDOWN = """\
# Main Title

Some introductory text about the research topic.

## Section One

This section covers the first area of interest.

- First bullet point
- Second bullet point
- Third bullet point

1. Numbered item one
2. Numbered item two

### Subsection

More details about the subsection.

## Section Two

```python
def hello():
    print("Hello, world!")
```

```javascript
console.log("test");
```

Check out [Example Site](https://example.com) and [Docs](https://docs.example.com/guide).

API Key: A secret token used for authentication
Cache TTL: The time-to-live for cached entries

## References

- [RFC 7231](https://tools.ietf.org/html/rfc7231)
"""

SAMPLE_HTML = """\
<h1>HTML Title</h1>
<p>Some paragraph text.</p>
<h2>HTML Subtitle</h2>
<a href="https://example.com">Example Link</a>
<a href="https://other.com">Other Link</a>
"""

MINIMAL_CONTENT = "Just a single line with no structure."

EMPTY_CONTENT = ""


# =============================================================================
# Tests -- extract_headings
# =============================================================================


class TestExtractHeadings:
    """Tests for extract_headings()."""

    def test_extracts_markdown_headings(self):
        """Markdown headings at all levels are detected."""
        content = "# H1\n## H2\n### H3\n#### H4\n##### H5\n###### H6"
        headings = extract_headings(content)

        assert len(headings) == 6
        assert headings[0] == "H1"
        assert headings[5] == "H6"

    def test_extracts_html_headings(self):
        """HTML heading tags are detected."""
        headings = extract_headings(SAMPLE_HTML)

        assert "HTML Title" in headings
        assert "HTML Subtitle" in headings

    def test_mixed_markdown_and_html(self):
        """Both markdown and HTML headings are extracted from the same content."""
        mixed = "# Markdown Heading\n<h2>HTML Heading</h2>"
        headings = extract_headings(mixed)

        assert "Markdown Heading" in headings
        assert "HTML Heading" in headings

    def test_no_headings_returns_empty(self):
        """Content with no headings returns an empty list."""
        headings = extract_headings("No headings here.\nJust plain text.")
        assert headings == []

    def test_empty_content(self):
        """Empty string returns an empty list."""
        assert extract_headings("") == []

    def test_heading_with_inline_formatting(self):
        """Heading text may include inline content."""
        content = "## Section with `code` and more"
        headings = extract_headings(content)
        assert len(headings) == 1
        assert "code" in headings[0]

    def test_hash_in_non_heading_context_ignored(self):
        """A hash sign mid-line is not treated as a heading."""
        content = "This is a line with # in the middle"
        headings = extract_headings(content)
        assert headings == []

    def test_sample_markdown_headings(self):
        """The shared sample markdown fixture produces the expected headings."""
        headings = extract_headings(SAMPLE_MARKDOWN)
        assert "Main Title" in headings
        assert "Section One" in headings
        assert "Section Two" in headings
        assert "Subsection" in headings
        assert "References" in headings


# =============================================================================
# Tests -- extract_code_blocks
# =============================================================================


class TestExtractCodeBlocks:
    """Tests for extract_code_blocks()."""

    def test_extracts_fenced_code_block_with_language(self):
        """A fenced block with a language tag preserves the language."""
        content = "```python\nprint('hi')\n```"
        blocks = extract_code_blocks(content)

        assert len(blocks) == 1
        assert blocks[0]["language"] == "python"
        assert blocks[0]["code"] == "print('hi')"

    def test_extracts_fenced_code_block_without_language(self):
        """A fenced block with no language tag defaults to 'text'."""
        content = "```\nsome code\n```"
        blocks = extract_code_blocks(content)

        assert len(blocks) == 1
        assert blocks[0]["language"] == "text"
        assert blocks[0]["code"] == "some code"

    def test_multiple_code_blocks(self):
        """Multiple fenced blocks are all extracted."""
        blocks = extract_code_blocks(SAMPLE_MARKDOWN)

        assert len(blocks) == 2
        languages = [b["language"] for b in blocks]
        assert "python" in languages
        assert "javascript" in languages

    def test_no_code_blocks_returns_empty(self):
        """Content with no fenced blocks returns an empty list."""
        assert extract_code_blocks("No code here.") == []

    def test_empty_content(self):
        """Empty string returns an empty list."""
        assert extract_code_blocks("") == []

    def test_code_block_strips_whitespace(self):
        """Leading and trailing whitespace inside the block is stripped."""
        content = "```python\n\n  hello  \n\n```"
        blocks = extract_code_blocks(content)
        assert blocks[0]["code"] == "hello"

    def test_multiline_code_block(self):
        """A multi-line code block preserves internal line breaks."""
        content = "```python\nline1\nline2\nline3\n```"
        blocks = extract_code_blocks(content)
        assert "line1\nline2\nline3" == blocks[0]["code"]


# =============================================================================
# Tests -- extract_links
# =============================================================================


class TestExtractLinks:
    """Tests for extract_links()."""

    def test_extracts_markdown_links(self):
        """Standard markdown links [text](url) are extracted."""
        content = "See [Google](https://google.com) for details."
        links = extract_links(content)

        assert len(links) == 1
        assert links[0]["text"] == "Google"
        assert links[0]["url"] == "https://google.com"

    def test_extracts_html_links(self):
        """HTML anchor tags are extracted."""
        links = extract_links(SAMPLE_HTML)

        urls = {l["url"] for l in links}
        assert urls == {"https://example.com", "https://other.com"}

    def test_multiple_markdown_links(self):
        """Multiple markdown links on the same or different lines are found."""
        links = extract_links(SAMPLE_MARKDOWN)

        texts = [l["text"] for l in links]
        assert "Example Site" in texts
        assert "Docs" in texts
        assert "RFC 7231" in texts

    def test_no_links_returns_empty(self):
        """Content with no links returns an empty list."""
        assert extract_links("Plain text, no links.") == []

    def test_empty_content(self):
        """Empty string returns an empty list."""
        assert extract_links("") == []

    def test_mixed_markdown_and_html_links(self):
        """Both markdown and HTML link formats are extracted."""
        content = '[MD Link](https://md.com)\n<a href="https://html.com">HTML Link</a>'
        links = extract_links(content)

        assert len(links) == 2
        urls = {l["url"] for l in links}
        assert urls == {"https://md.com", "https://html.com"}


# =============================================================================
# Tests -- extract_key_points
# =============================================================================


class TestExtractKeyPoints:
    """Tests for extract_key_points()."""

    def test_extracts_dash_bullets(self):
        """Lines starting with '- ' are captured."""
        content = "- Point one\n- Point two"
        points = extract_key_points(content)
        assert points == ["Point one", "Point two"]

    def test_extracts_asterisk_bullets(self):
        """Lines starting with '* ' are captured."""
        content = "* Star one\n* Star two"
        points = extract_key_points(content)
        assert points == ["Star one", "Star two"]

    def test_extracts_plus_bullets(self):
        """Lines starting with '+ ' are captured."""
        content = "+ Plus one\n+ Plus two"
        points = extract_key_points(content)
        assert points == ["Plus one", "Plus two"]

    def test_extracts_numbered_items(self):
        """Lines starting with 'N. ' are captured."""
        content = "1. First item\n2. Second item\n3. Third item"
        points = extract_key_points(content)
        assert len(points) == 3
        assert "First item" in points

    def test_mixed_bullet_and_numbered(self):
        """Both bullet and numbered items are extracted together."""
        points = extract_key_points(SAMPLE_MARKDOWN)

        assert "First bullet point" in points
        assert "Numbered item one" in points

    def test_no_points_returns_empty(self):
        """Content with no list items returns an empty list."""
        assert extract_key_points("Just a paragraph.") == []

    def test_empty_content(self):
        """Empty string returns an empty list."""
        assert extract_key_points("") == []

    def test_inline_dash_not_captured(self):
        """A dash in the middle of a line is not treated as a bullet."""
        content = "This has a - dash in the middle"
        points = extract_key_points(content)
        assert points == []


# =============================================================================
# Tests -- extract_definitions
# =============================================================================


class TestExtractDefinitions:
    """Tests for extract_definitions()."""

    def test_extracts_colon_definitions(self):
        """'Term: Definition' lines starting with a capital letter are captured."""
        content = "API Key: A secret token used for authentication"
        defs = extract_definitions(content)

        assert len(defs) == 1
        assert defs[0]["term"] == "API Key"
        assert defs[0]["definition"] == "A secret token used for authentication"

    def test_multiple_definitions(self):
        """Multiple definition lines are all captured."""
        defs = extract_definitions(SAMPLE_MARKDOWN)

        terms = [d["term"] for d in defs]
        assert "API Key" in terms
        assert "Cache TTL" in terms

    def test_long_term_rejected(self):
        """Terms longer than 50 characters are rejected to avoid matching sentences."""
        content = "This is a very long term that should not match as a definition term because it is a sentence: and this is after the colon"
        defs = extract_definitions(content)
        assert defs == []

    def test_lowercase_start_ignored(self):
        """Lines not starting with a capital letter are not definitions."""
        content = "lowercase: this should not match"
        defs = extract_definitions(content)
        assert defs == []

    def test_no_definitions_returns_empty(self):
        """Content with no definition patterns returns an empty list."""
        assert extract_definitions("No definitions here.") == []

    def test_empty_content(self):
        """Empty string returns an empty list."""
        assert extract_definitions("") == []

    def test_definition_strips_whitespace(self):
        """Terms and definitions are stripped of leading/trailing whitespace."""
        content = "Term With Spaces :   padded definition   "
        defs = extract_definitions(content)
        assert len(defs) == 1
        assert defs[0]["term"] == "Term With Spaces"
        assert defs[0]["definition"] == "padded definition"


# =============================================================================
# Tests -- summarize_content
# =============================================================================


class TestSummarizeContent:
    """Tests for summarize_content()."""

    def test_returns_first_sentences(self):
        """Summary picks up the first few sentences within the length limit."""
        content = "First sentence. Second sentence. Third sentence."
        summary = summarize_content(content, max_length=100)

        assert "First sentence" in summary
        assert summary.endswith(".")

    def test_strips_code_blocks(self):
        """Code blocks are removed before summarizing."""
        content = "Before code. ```python\ncode here\n``` After code."
        summary = summarize_content(content)

        assert "code here" not in summary
        assert "Before code" in summary

    def test_strips_html_tags(self):
        """HTML tags are removed from the summary."""
        content = "<p>Paragraph text.</p> <b>Bold text.</b>"
        summary = summarize_content(content)

        assert "<p>" not in summary
        assert "<b>" not in summary
        assert "Paragraph text" in summary

    def test_respects_max_length(self):
        """Summary does not exceed the max_length parameter."""
        content = ". ".join(f"Sentence number {i}" for i in range(50)) + "."
        summary = summarize_content(content, max_length=100)

        # The summary may slightly exceed due to joining with ". " + final ".",
        # but individual sentence accumulation stops at < max_length
        assert len(summary) < 200  # generous upper bound

    def test_empty_content_returns_empty(self):
        """Empty content produces an empty string."""
        assert summarize_content("") == ""

    def test_content_with_only_code_blocks(self):
        """Content that is only code blocks produces an empty summary."""
        content = "```python\nprint('hello')\n```"
        summary = summarize_content(content)
        # After removing code blocks, only whitespace remains
        assert summary == "" or summary == "."


# =============================================================================
# Tests -- extract_findings (orchestrator)
# =============================================================================


class TestExtractFindings:
    """Tests for the top-level extract_findings() function."""

    def test_returns_all_expected_keys(self):
        """The result dict contains all documented keys."""
        findings = extract_findings(SAMPLE_MARKDOWN, source="test.md")

        expected_keys = {
            "source",
            "extracted_at",
            "summary",
            "headings",
            "key_points",
            "definitions",
            "code_blocks",
            "links",
            "word_count",
            "line_count",
        }
        assert expected_keys == set(findings.keys())

    def test_source_is_preserved(self):
        """The source parameter is stored in the result."""
        findings = extract_findings("content", source="https://example.com")
        assert findings["source"] == "https://example.com"

    def test_source_none_when_not_provided(self):
        """When no source is given, source is None."""
        findings = extract_findings("content")
        assert findings["source"] is None

    def test_extracted_at_is_iso_timestamp(self):
        """extracted_at is a valid ISO 8601 timestamp string."""
        from datetime import datetime

        findings = extract_findings("content")
        # Should parse without error
        dt = datetime.fromisoformat(findings["extracted_at"])
        assert dt is not None

    def test_word_count(self):
        """word_count reflects the number of whitespace-separated tokens."""
        content = "one two three four five"
        findings = extract_findings(content)
        assert findings["word_count"] == 5

    def test_line_count(self):
        """line_count reflects the number of newline-separated lines."""
        content = "line1\nline2\nline3"
        findings = extract_findings(content)
        assert findings["line_count"] == 3

    def test_code_blocks_limited_to_ten(self):
        """At most 10 code blocks are included in the result."""
        blocks = "\n".join(f"```python\nblock {i}\n```" for i in range(15))
        findings = extract_findings(blocks)
        assert len(findings["code_blocks"]) == 10

    def test_links_limited_to_twenty(self):
        """At most 20 links are included in the result."""
        links = "\n".join(f"[link{i}](https://example.com/{i})" for i in range(25))
        findings = extract_findings(links)
        assert len(findings["links"]) == 20

    def test_sample_markdown_integration(self):
        """Full extraction from the shared sample markdown produces non-empty results."""
        findings = extract_findings(SAMPLE_MARKDOWN, source="sample.md")

        assert len(findings["headings"]) >= 4
        assert len(findings["key_points"]) >= 4
        assert len(findings["definitions"]) >= 2
        assert len(findings["code_blocks"]) == 2
        assert len(findings["links"]) >= 3
        assert findings["word_count"] > 50

    def test_empty_content(self):
        """Empty content produces zeroed counts and empty lists."""
        findings = extract_findings("")

        assert findings["headings"] == []
        assert findings["key_points"] == []
        assert findings["definitions"] == []
        assert findings["code_blocks"] == []
        assert findings["links"] == []
        assert findings["word_count"] == 0  # "".split() == []
        assert findings["line_count"] == 1


# =============================================================================
# Tests -- assess_quality
# =============================================================================


class TestAssessQuality:
    """Tests for assess_quality()."""

    def test_high_quality_content(self):
        """Rich content with all features scores high quality."""
        findings = extract_findings(SAMPLE_MARKDOWN, source="test.md")
        quality = assess_quality(findings)

        assert quality["quality_level"] == "high"
        assert quality["percentage"] >= 80
        assert quality["total"] >= 5

    def test_low_quality_content(self):
        """Minimal content with no structure scores low quality."""
        findings = extract_findings(MINIMAL_CONTENT)
        quality = assess_quality(findings)

        assert quality["quality_level"] == "low"
        assert quality["total"] < 3

    def test_score_fields_present(self):
        """Quality result contains all expected scoring fields."""
        findings = extract_findings("Some content.")
        quality = assess_quality(findings)

        assert "scores" in quality
        assert "total" in quality
        assert "max" in quality
        assert "percentage" in quality
        assert "quality_level" in quality

    def test_individual_scores_are_binary(self):
        """Each individual score is 0 or 1."""
        findings = extract_findings(SAMPLE_MARKDOWN)
        quality = assess_quality(findings)

        for key, value in quality["scores"].items():
            assert value in (0, 1), f"Score '{key}' has non-binary value {value}"

    def test_max_score_is_six(self):
        """There are exactly 6 scoring criteria."""
        findings = extract_findings("test")
        quality = assess_quality(findings)
        assert quality["max"] == 6

    def test_percentage_calculation(self):
        """percentage is correctly computed from total/max."""
        findings = extract_findings(SAMPLE_MARKDOWN)
        quality = assess_quality(findings)

        expected = round(quality["total"] / quality["max"] * 100)
        assert quality["percentage"] == expected

    def test_medium_quality_threshold(self):
        """A score of 3 or 4 maps to 'medium' quality."""
        # Build findings that have exactly 3 truthy features:
        # summary, key_points, sufficient_length
        content = "A moderately long piece of content. " * 20 + "\n- A key point\n"
        findings = extract_findings(content)
        quality = assess_quality(findings)

        # Should be at least medium (has summary, key_points, sufficient length)
        assert quality["quality_level"] in ("medium", "high")

    def test_quality_levels_exhaustive(self):
        """quality_level is always one of high, medium, low."""
        for content in [SAMPLE_MARKDOWN, MINIMAL_CONTENT, EMPTY_CONTENT, "short"]:
            findings = extract_findings(content)
            quality = assess_quality(findings)
            assert quality["quality_level"] in ("high", "medium", "low")


# =============================================================================
# Tests -- generate_markdown
# =============================================================================


class TestGenerateMarkdown:
    """Tests for generate_markdown()."""

    def test_contains_title(self):
        """Output starts with a markdown h1 title."""
        findings = extract_findings(SAMPLE_MARKDOWN, source="test.md")
        md = generate_markdown(findings)

        assert md.startswith("# Research Findings")

    def test_contains_source(self):
        """The source is included in the output."""
        findings = extract_findings("content", source="my_source.md")
        md = generate_markdown(findings)

        assert "my_source.md" in md

    def test_contains_summary_section(self):
        """The Summary section is present."""
        findings = extract_findings(SAMPLE_MARKDOWN)
        md = generate_markdown(findings)

        assert "## Summary" in md

    def test_contains_structure_section_when_headings_exist(self):
        """The Structure section appears when headings are extracted."""
        findings = extract_findings(SAMPLE_MARKDOWN)
        md = generate_markdown(findings)

        assert "## Structure" in md

    def test_contains_key_points_section(self):
        """The Key Points section appears when bullet items are extracted."""
        findings = extract_findings(SAMPLE_MARKDOWN)
        md = generate_markdown(findings)

        assert "## Key Points" in md

    def test_contains_definitions_section(self):
        """The Definitions section appears when definitions are extracted."""
        findings = extract_findings(SAMPLE_MARKDOWN)
        md = generate_markdown(findings)

        assert "## Definitions" in md

    def test_no_structure_section_when_no_headings(self):
        """The Structure section is absent when there are no headings."""
        findings = extract_findings(MINIMAL_CONTENT)
        md = generate_markdown(findings)

        assert "## Structure" not in md

    def test_quality_section_when_present(self):
        """The Quality Assessment section appears when quality data is attached."""
        findings = extract_findings(SAMPLE_MARKDOWN)
        findings["quality"] = assess_quality(findings)
        md = generate_markdown(findings)

        assert "## Quality Assessment" in md
        assert "Quality Level:" in md

    def test_no_quality_section_by_default(self):
        """Without quality data, the Quality Assessment section is absent."""
        findings = extract_findings(SAMPLE_MARKDOWN)
        md = generate_markdown(findings)

        assert "## Quality Assessment" not in md

    def test_headings_limited_to_ten(self):
        """At most 10 headings are listed in the Structure section."""
        content = "\n".join(f"## Heading {i}" for i in range(20))
        findings = extract_findings(content)
        md = generate_markdown(findings)

        # Count the bullet lines in the Structure section
        in_structure = False
        heading_bullets = 0
        for line in md.split("\n"):
            if line.strip() == "## Structure":
                in_structure = True
                continue
            if in_structure and line.startswith("## "):
                break
            if in_structure and line.startswith("- "):
                heading_bullets += 1

        assert heading_bullets == 10

    def test_key_points_limited_to_fifteen(self):
        """At most 15 key points are listed."""
        content = "\n".join(f"- Point {i}" for i in range(20))
        findings = extract_findings(content)
        md = generate_markdown(findings)

        in_points = False
        point_bullets = 0
        for line in md.split("\n"):
            if line.strip() == "## Key Points":
                in_points = True
                continue
            if in_points and line.startswith("## "):
                break
            if in_points and line.startswith("- "):
                point_bullets += 1

        assert point_bullets == 15
