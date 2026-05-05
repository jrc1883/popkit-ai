#!/usr/bin/env python3
"""
Test suite for xml_parser.py

Tests ElementTree-based XML parsing for PopKit context system.
Critical for robust XML handling and backward compatibility.
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.xml_parser import (
    extract_xml_from_conversation,
    parse_findings,
    parse_problem_context,
    parse_project_context,
)


class TestParseProblemContext:
    """Test problem context parsing"""

    def test_parse_complete_problem_context(self):
        """Test parsing problem context with all fields"""
        xml = """
        <problem-context version="1.0">
            <category>bug</category>
            <description>User authentication fails intermittently</description>
            <severity>high</severity>
            <workflow>
                <step id="1">
                    <action>search-existing-code</action>
                    <agent>pop-search</agent>
                </step>
            </workflow>
        </problem-context>
        """
        result = parse_problem_context(xml)

        assert result is not None
        assert result["category"] == "bug"
        assert result["description"] == "User authentication fails intermittently"
        assert result["severity"] == "high"
        assert result["workflow"] is not None
        assert len(result["workflow"]["steps"]) == 1
        assert result["workflow"]["steps"][0]["id"] == "1"
        assert result["workflow"]["steps"][0]["action"] == "search-existing-code"

    def test_parse_minimal_problem_context(self):
        """Test parsing problem context without optional fields"""
        xml = """
        <problem-context>
            <category>feature</category>
            <description>Add dark mode</description>
            <severity>medium</severity>
        </problem-context>
        """
        result = parse_problem_context(xml)

        assert result is not None
        assert result["category"] == "feature"
        assert result["description"] == "Add dark mode"
        assert result["severity"] == "medium"
        assert result["workflow"] is None

    def test_parse_all_categories(self):
        """Test parsing all valid category types"""
        categories = [
            "bug",
            "feature",
            "optimization",
            "refactor",
            "investigation",
            "docs",
            "test",
            "task",
        ]

        for cat in categories:
            xml = f"<problem-context><category>{cat}</category><description>Test</description><severity>low</severity></problem-context>"
            result = parse_problem_context(xml)
            assert result is not None
            assert result["category"] == cat

    def test_parse_all_severities(self):
        """Test parsing all valid severity levels"""
        severities = ["critical", "high", "medium", "low"]

        for sev in severities:
            xml = f"<problem-context><category>bug</category><description>Test</description><severity>{sev}</severity></problem-context>"
            result = parse_problem_context(xml)
            assert result is not None
            assert result["severity"] == sev

    def test_parse_malformed_xml(self):
        """Test handling of malformed XML"""
        xml = "<problem-context><category>bug</category>"  # Unclosed tag
        result = parse_problem_context(xml)
        assert result is None

    def test_parse_wrong_root_element(self):
        """Test handling of wrong root element"""
        xml = "<project><name>test</name></project>"
        result = parse_problem_context(xml)
        assert result is None

    def test_parse_empty_elements(self):
        """Test handling of empty XML elements"""
        xml = "<problem-context><category></category><description></description><severity></severity></problem-context>"
        result = parse_problem_context(xml)
        assert result is not None
        assert result["category"] is None
        assert result["description"] is None
        assert result["severity"] is None

    def test_parse_unicode_description(self):
        """Test parsing Unicode characters in description"""
        xml = "<problem-context><category>bug</category><description>Fix emoji support 🚀 and 世界</description><severity>low</severity></problem-context>"
        result = parse_problem_context(xml)
        assert result is not None
        assert "🚀" in result["description"]
        assert "世界" in result["description"]

    def test_parse_escaped_xml_characters(self):
        """Test parsing escaped XML special characters"""
        xml = "<problem-context><category>bug</category><description>&lt;html&gt; &amp; &quot;test&quot;</description><severity>low</severity></problem-context>"
        result = parse_problem_context(xml)
        assert result is not None
        assert "<html>" in result["description"]
        assert "&" in result["description"]
        assert '"test"' in result["description"]


class TestParseProjectContext:
    """Test project context parsing"""

    def test_parse_complete_project_context(self):
        """Test parsing project context with all fields"""
        xml = """
        <project version="1.0">
            <name>popkit-ai</name>
            <stack>
                <technology>Python</technology>
                <technology>TypeScript</technology>
                <technology>Markdown</technology>
            </stack>
            <infrastructure>
                <redis>false</redis>
                <postgres>true</postgres>
                <docker>true</docker>
            </infrastructure>
            <current-work>
                <focus>XML testing strategy</focus>
                <issue>Security hardening</issue>
            </current-work>
        </project>
        """
        result = parse_project_context(xml)

        assert result is not None
        assert result["name"] == "popkit-ai"
        assert len(result["stack"]) == 3
        assert "Python" in result["stack"]
        assert "TypeScript" in result["stack"]
        assert result["infrastructure"]["redis"] is False
        assert result["infrastructure"]["postgres"] is True
        assert result["infrastructure"]["docker"] is True
        assert result["current_work"]["focus"] == "XML testing strategy"

    def test_parse_minimal_project_context(self):
        """Test parsing project with only name"""
        xml = "<project><name>test-project</name></project>"
        result = parse_project_context(xml)

        assert result is not None
        assert result["name"] == "test-project"
        assert result["stack"] == []
        assert result["infrastructure"] == {}
        assert result["current_work"] == {}

    def test_parse_empty_stack(self):
        """Test parsing project with empty stack"""
        xml = "<project><name>test</name><stack></stack></project>"
        result = parse_project_context(xml)

        assert result is not None
        assert result["stack"] == []

    def test_parse_multiple_work_items(self):
        """Test parsing multiple current work items"""
        xml = """
        <project>
            <name>test</name>
            <current-work>
                <issue>Issue 1</issue>
                <issue>Issue 2</issue>
                <issue>Issue 3</issue>
            </current-work>
        </project>
        """
        result = parse_project_context(xml)

        assert result is not None
        assert isinstance(result["current_work"]["issue"], list)
        assert len(result["current_work"]["issue"]) == 3

    def test_parse_malformed_project_xml(self):
        """Test handling of malformed project XML"""
        xml = "<project><name>test</project>"  # Unclosed name tag
        result = parse_project_context(xml)
        assert result is None

    def test_parse_wrong_root_element_project(self):
        """Test handling of wrong root element"""
        xml = "<problem-context><category>bug</category></problem-context>"
        result = parse_project_context(xml)
        assert result is None


class TestParseFindings:
    """Test findings parsing"""

    def test_parse_complete_findings_success(self):
        """Test parsing complete findings with success status"""
        xml = """
        <findings version="1.0">
            <tool>Write</tool>
            <status>success</status>
            <quality_score>0.85</quality_score>
            <issues>
                <issue>Missing error handling</issue>
                <issue>Potential security issue</issue>
            </issues>
            <suggestions>
                <suggestion>Add try-catch blocks</suggestion>
                <suggestion>Run security scan</suggestion>
            </suggestions>
            <followup_agents>
                <agent>security-auditor</agent>
                <agent>test-generator</agent>
            </followup_agents>
        </findings>
        """
        result = parse_findings(xml)

        assert result is not None
        assert result["tool"] == "Write"
        assert result["status"] == "success"
        assert result["quality_score"] == 0.85
        assert len(result["issues"]) == 2
        assert "Missing error handling" in result["issues"]
        assert len(result["suggestions"]) == 2
        assert "Add try-catch blocks" in result["suggestions"]
        assert len(result["followup_agents"]) == 2
        assert "security-auditor" in result["followup_agents"]
        assert result["error_message"] is None

    def test_parse_findings_with_error(self):
        """Test parsing findings with error status"""
        xml = """
        <findings>
            <tool>Read</tool>
            <status>error</status>
            <quality_score>0.0</quality_score>
            <error_message>File not found: config.json</error_message>
        </findings>
        """
        result = parse_findings(xml)

        assert result is not None
        assert result["tool"] == "Read"
        assert result["status"] == "error"
        assert result["quality_score"] == 0.0
        assert result["error_message"] == "File not found: config.json"

    def test_parse_minimal_findings(self):
        """Test parsing minimal findings"""
        xml = """
        <findings>
            <tool>Bash</tool>
            <status>success</status>
            <quality_score>1.0</quality_score>
        </findings>
        """
        result = parse_findings(xml)

        assert result is not None
        assert result["tool"] == "Bash"
        assert result["status"] == "success"
        assert result["quality_score"] == 1.0
        assert result["issues"] == []
        assert result["suggestions"] == []
        assert result["followup_agents"] == []

    def test_parse_invalid_quality_score(self):
        """Test handling of invalid quality score"""
        xml = """
        <findings>
            <tool>Test</tool>
            <status>success</status>
            <quality_score>invalid</quality_score>
        </findings>
        """
        result = parse_findings(xml)

        assert result is not None
        assert result["quality_score"] == 0.0  # Should default to 0.0

    def test_parse_malformed_findings_xml(self):
        """Test handling of malformed findings XML"""
        xml = "<findings><tool>Test</tool>"  # Unclosed tag
        result = parse_findings(xml)
        assert result is None

    def test_parse_wrong_root_element_findings(self):
        """Test handling of wrong root element"""
        xml = "<project><name>test</name></project>"
        result = parse_findings(xml)
        assert result is None


class TestExtractXmlFromConversation:
    """Test XML extraction from conversation history"""

    def test_extract_xml_with_markers(self):
        """Test extracting XML with HTML comment markers"""
        messages = [
            "User message",
            "<!-- XML Context (Invisible) --><problem-context><category>bug</category><description>Test</description><severity>high</severity></problem-context><!-- End XML Context -->",
            "Another message",
        ]
        xml = extract_xml_from_conversation(messages)

        assert xml is not None
        assert "<problem-context>" in xml
        assert "<category>bug</category>" in xml

    def test_extract_xml_from_last_messages(self):
        """Test extracting XML from most recent messages"""
        messages = [
            "Old message 1",
            "Old message 2",
            "Old message 3",
            "<!-- XML Context (Invisible) --><findings><tool>Test</tool><status>success</status><quality_score>0.9</quality_score></findings><!-- End XML Context -->",
        ]
        xml = extract_xml_from_conversation(messages, search_last_n=2)

        assert xml is not None
        assert "<findings>" in xml

    def test_extract_no_xml_found(self):
        """Test when no XML is found in messages"""
        messages = ["Just a regular message", "Another message without XML", "No markers here"]
        xml = extract_xml_from_conversation(messages)

        assert xml is None

    def test_extract_xml_incomplete_markers(self):
        """Test handling of incomplete markers"""
        messages = ["<!-- XML Context (Invisible) --><problem-context>test</problem-context>"]
        xml = extract_xml_from_conversation(messages)

        assert xml is None

    def test_extract_xml_multiple_occurrences(self):
        """Test extraction with multiple XML occurrences (should get most recent)"""
        messages = [
            "<!-- XML Context (Invisible) --><problem-context><category>bug</category><description>Old</description><severity>low</severity></problem-context><!-- End XML Context -->",
            "<!-- XML Context (Invisible) --><problem-context><category>feature</category><description>New</description><severity>high</severity></problem-context><!-- End XML Context -->",
        ]
        xml = extract_xml_from_conversation(messages)

        assert xml is not None
        assert "<category>feature</category>" in xml  # Should get most recent
        assert "New" in xml

    def test_extract_xml_with_whitespace(self):
        """Test extraction with whitespace around XML"""
        messages = [
            "<!-- XML Context (Invisible) -->   \n  <problem-context><category>test</category><description>Test</description><severity>low</severity></problem-context>  \n  <!-- End XML Context -->"
        ]
        xml = extract_xml_from_conversation(messages)

        assert xml is not None
        assert xml.startswith("<problem-context>")

    def test_extract_empty_messages_list(self):
        """Test handling of empty messages list"""
        messages = []
        xml = extract_xml_from_conversation(messages)

        assert xml is None

    def test_extract_with_limit_exceeding_list(self):
        """Test when search limit exceeds list length"""
        messages = ["msg1", "msg2"]
        xml = extract_xml_from_conversation(messages, search_last_n=10)

        assert xml is None  # No XML in messages


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_parse_very_long_description(self):
        """Test parsing very long description"""
        long_desc = "A" * 5000
        xml = f"<problem-context><category>bug</category><description>{long_desc}</description><severity>low</severity></problem-context>"
        result = parse_problem_context(xml)

        assert result is not None
        assert len(result["description"]) == 5000

    def test_parse_nested_workflow(self):
        """Test parsing complex nested workflow"""
        xml = """
        <problem-context>
            <category>feature</category>
            <description>Complex feature</description>
            <severity>high</severity>
            <workflow>
                <step id="1">
                    <action>First step</action>
                    <dependencies>
                        <dependency>step0</dependency>
                    </dependencies>
                </step>
                <step id="2">
                    <action>Second step</action>
                    <agent>test-agent</agent>
                    <dependencies>
                        <dependency>step1</dependency>
                    </dependencies>
                </step>
            </workflow>
        </problem-context>
        """
        result = parse_problem_context(xml)

        assert result is not None
        assert result["workflow"] is not None
        assert len(result["workflow"]["steps"]) == 2
        assert len(result["workflow"]["steps"][0]["dependencies"]) == 1
        assert result["workflow"]["steps"][0]["dependencies"][0] == "step0"

    def test_parse_cdata_sections(self):
        """Test parsing XML with CDATA sections"""
        xml = """
        <problem-context>
            <category>bug</category>
            <description><![CDATA[Code with <special> & "characters"]]></description>
            <severity>high</severity>
        </problem-context>
        """
        result = parse_problem_context(xml)

        assert result is not None
        assert "<special>" in result["description"]

    def test_parse_xml_with_comments(self):
        """Test parsing XML with comments"""
        xml = """
        <findings>
            <!-- This is a comment -->
            <tool>Write</tool>
            <status>success</status>
            <!-- Another comment -->
            <quality_score>0.8</quality_score>
        </findings>
        """
        result = parse_findings(xml)

        assert result is not None
        assert result["tool"] == "Write"

    def test_parse_mixed_content(self):
        """Test parsing with mixed text and element content"""
        xml = """
        <project>
            <name>test-project</name>
            <stack>
                <technology>Python</technology>
                Some random text here
                <technology>JavaScript</technology>
            </stack>
        </project>
        """
        result = parse_project_context(xml)

        assert result is not None
        assert "Python" in result["stack"]
        assert "JavaScript" in result["stack"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
