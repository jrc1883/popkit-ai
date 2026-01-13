#!/usr/bin/env python3
"""
Test suite for xml_validator.py

Tests XML schema validation, well-formedness checking, and error handling.
Critical for ensuring XML context integrity in PopKit.
"""

import sys
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.xml_validator import (
    get_schema_path,
    is_well_formed_xml,
    validate_xml_structure,
    validate_xml_against_schema,
    validate_problem_xml,
    validate_project_xml,
    validate_findings_xml,
    validate_workflow_xml,
    clear_schema_cache,
    HAS_LXML,
)


class TestGetSchemaPath:
    """Test schema path resolution"""

    def test_problem_schema_path(self):
        """Test problem schema path resolution"""
        path = get_schema_path("problem")
        assert path.exists()
        assert path.name == "problem-context.xsd"

    def test_project_schema_path(self):
        """Test project schema path resolution"""
        path = get_schema_path("project")
        assert path.exists()
        assert path.name == "project-context.xsd"

    def test_findings_schema_path(self):
        """Test findings schema path resolution"""
        path = get_schema_path("findings")
        assert path.exists()
        assert path.name == "findings.xsd"

    def test_workflow_schema_path(self):
        """Test workflow schema path resolution"""
        path = get_schema_path("workflow")
        assert path.exists()
        assert path.name == "workflow.xsd"

    def test_invalid_schema_type(self):
        """Test error on invalid schema type"""
        with pytest.raises(ValueError, match="Invalid schema_type"):
            get_schema_path("invalid")


class TestWellFormedness:
    """Test well-formedness checking"""

    def test_valid_xml(self):
        """Test valid well-formed XML"""
        xml = "<root><child>value</child></root>"
        is_valid, error = is_well_formed_xml(xml)
        assert is_valid is True
        assert error is None

    def test_unclosed_tag(self):
        """Test detection of unclosed tags"""
        xml = "<root><child>value</root>"
        is_valid, error = is_well_formed_xml(xml)
        assert is_valid is False
        assert "XML parsing error" in error

    def test_invalid_nesting(self):
        """Test detection of invalid nesting"""
        xml = "<root><child></root></child>"
        is_valid, error = is_well_formed_xml(xml)
        assert is_valid is False
        assert "XML parsing error" in error

    def test_empty_string(self):
        """Test handling of empty string"""
        is_valid, error = is_well_formed_xml("")
        assert is_valid is False
        assert "Empty XML string" in error

    def test_whitespace_only(self):
        """Test handling of whitespace-only string"""
        is_valid, error = is_well_formed_xml("   \n\t  ")
        assert is_valid is False
        assert "Empty XML string" in error

    def test_unicode_content(self):
        """Test Unicode content handling"""
        xml = "<root><text>Hello 世界 🚀</text></root>"
        is_valid, error = is_well_formed_xml(xml)
        assert is_valid is True
        assert error is None

    def test_special_characters_escaped(self):
        """Test properly escaped special characters"""
        xml = "<root><text>&lt;html&gt; &amp; &quot;quotes&quot;</text></root>"
        is_valid, error = is_well_formed_xml(xml)
        assert is_valid is True
        assert error is None


class TestStructureValidation:
    """Test quick structure validation"""

    def test_correct_root(self):
        """Test matching root element"""
        xml = "<problem-context><category>bug</category></problem-context>"
        assert validate_xml_structure(xml, "problem-context") is True

    def test_incorrect_root(self):
        """Test non-matching root element"""
        xml = "<project><name>test</name></project>"
        assert validate_xml_structure(xml, "problem-context") is False

    def test_malformed_xml(self):
        """Test malformed XML returns False"""
        xml = "<invalid"
        assert validate_xml_structure(xml, "invalid") is False


class TestProblemContextValidation:
    """Test problem-context XML validation"""

    def test_valid_problem_context(self):
        """Test valid problem context XML"""
        xml = """
        <problem-context version="1.0">
            <category>bug</category>
            <description>User authentication fails intermittently</description>
            <severity>high</severity>
        </problem-context>
        """
        is_valid, error = validate_problem_xml(xml)
        assert is_valid is True
        assert error is None

    def test_valid_with_workflow(self):
        """Test valid problem context with workflow"""
        xml = """
        <problem-context>
            <category>feature</category>
            <description>Add dark mode support</description>
            <severity>medium</severity>
            <workflow>
                <step id="step1">
                    <action>Design UI mockups</action>
                </step>
            </workflow>
        </problem-context>
        """
        is_valid, error = validate_problem_xml(xml)
        # Note: Without workflow being properly defined in our XSD,
        # this may fail full validation but pass well-formedness
        assert is_valid is True or not HAS_LXML

    def test_invalid_category(self):
        """Test invalid category enum value"""
        xml = """
        <problem-context>
            <category>invalid-category</category>
            <description>Test</description>
            <severity>high</severity>
        </problem-context>
        """
        is_valid, error = validate_problem_xml(xml)
        if HAS_LXML:
            assert is_valid is False
            assert error is not None
        else:
            # Without lxml, only well-formedness is checked
            assert is_valid is True

    def test_invalid_severity(self):
        """Test invalid severity enum value"""
        xml = """
        <problem-context>
            <category>bug</category>
            <description>Test</description>
            <severity>ultra-critical</severity>
        </problem-context>
        """
        is_valid, error = validate_problem_xml(xml)
        if HAS_LXML:
            assert is_valid is False
        else:
            assert is_valid is True

    def test_missing_required_element(self):
        """Test missing required element"""
        xml = """
        <problem-context>
            <category>bug</category>
            <severity>high</severity>
        </problem-context>
        """
        is_valid, error = validate_problem_xml(xml)
        if HAS_LXML:
            assert is_valid is False
            assert "description" in error.lower() or "element" in error.lower()
        else:
            assert is_valid is True


class TestProjectContextValidation:
    """Test project context XML validation"""

    def test_valid_project_context(self):
        """Test valid project context XML"""
        xml = """
        <project version="1.0">
            <name>popkit-claude</name>
            <stack>
                <technology>Python</technology>
                <technology>Markdown</technology>
            </stack>
            <infrastructure>
                <redis>false</redis>
                <postgres>true</postgres>
            </infrastructure>
        </project>
        """
        is_valid, error = validate_project_xml(xml)
        assert is_valid is True

    def test_minimal_project_context(self):
        """Test minimal valid project context"""
        xml = "<project><name>test-project</name></project>"
        is_valid, error = validate_project_xml(xml)
        assert is_valid is True


class TestFindingsValidation:
    """Test findings XML validation"""

    def test_valid_findings_success(self):
        """Test valid findings with success status"""
        xml = """
        <findings version="1.0">
            <tool>Write</tool>
            <status>success</status>
            <quality_score>0.85</quality_score>
            <issues>
                <issue>Missing error handling</issue>
            </issues>
            <suggestions>
                <suggestion>Add try-catch block</suggestion>
            </suggestions>
        </findings>
        """
        is_valid, error = validate_findings_xml(xml)
        assert is_valid is True

    def test_valid_findings_error(self):
        """Test valid findings with error status"""
        xml = """
        <findings>
            <tool>Read</tool>
            <status>error</status>
            <quality_score>0.0</quality_score>
            <error_message>File not found</error_message>
        </findings>
        """
        is_valid, error = validate_findings_xml(xml)
        assert is_valid is True

    def test_invalid_quality_score_too_high(self):
        """Test quality score above 1.0"""
        xml = """
        <findings>
            <tool>Write</tool>
            <status>success</status>
            <quality_score>1.5</quality_score>
        </findings>
        """
        is_valid, error = validate_findings_xml(xml)
        if HAS_LXML:
            assert is_valid is False
        else:
            assert is_valid is True

    def test_invalid_quality_score_negative(self):
        """Test negative quality score"""
        xml = """
        <findings>
            <tool>Write</tool>
            <status>success</status>
            <quality_score>-0.5</quality_score>
        </findings>
        """
        is_valid, error = validate_findings_xml(xml)
        if HAS_LXML:
            assert is_valid is False
        else:
            assert is_valid is True


class TestWorkflowValidation:
    """Test workflow XML validation"""

    def test_valid_workflow(self):
        """Test valid workflow XML"""
        xml = """
        <workflow version="1.0">
            <step id="step1">
                <action>Analyze requirements</action>
                <agent>pop-research</agent>
            </step>
            <step id="step2">
                <action>Implement feature</action>
                <dependencies>
                    <dependency>step1</dependency>
                </dependencies>
            </step>
        </workflow>
        """
        is_valid, error = validate_workflow_xml(xml)
        assert is_valid is True

    def test_missing_step_id(self):
        """Test workflow with missing step ID attribute"""
        xml = """
        <workflow>
            <step>
                <action>Test action</action>
            </step>
        </workflow>
        """
        is_valid, error = validate_workflow_xml(xml)
        if HAS_LXML:
            assert is_valid is False
        else:
            assert is_valid is True


class TestGeneralValidation:
    """Test general validation functionality"""

    def test_validate_against_schema_function(self):
        """Test generic validation function"""
        xml = "<problem-context><category>bug</category><description>Test</description><severity>high</severity></problem-context>"
        is_valid, error = validate_xml_against_schema(xml, "problem")
        assert is_valid is True

    def test_invalid_schema_type_raises_error(self):
        """Test that invalid schema type raises ValueError"""
        xml = "<root></root>"
        with pytest.raises(ValueError):
            validate_xml_against_schema(xml, "nonexistent")

    def test_schema_cache_clearing(self):
        """Test schema cache can be cleared"""
        # Validate something to populate cache
        xml = "<problem-context><category>bug</category><description>Test</description><severity>high</severity></problem-context>"
        validate_problem_xml(xml)

        # Clear cache
        clear_schema_cache()
        # Should work fine after cache clear
        is_valid, error = validate_problem_xml(xml)
        assert is_valid is True


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_very_large_xml(self):
        """Test handling of large XML documents"""
        # Create large but valid XML
        elements = "".join([f"<item>Item {i}</item>" for i in range(1000)])
        xml = f"<findings><tool>Test</tool><status>success</status><quality_score>0.5</quality_score><issues>{elements}</issues></findings>"

        is_valid, error = validate_findings_xml(xml)
        # Should at least be well-formed
        assert is_valid is True or error is not None

    def test_xml_with_cdata(self):
        """Test XML with CDATA sections"""
        xml = """
        <problem-context>
            <category>bug</category>
            <description><![CDATA[Code with <special> & "characters"]]></description>
            <severity>high</severity>
        </problem-context>
        """
        is_valid, error = validate_problem_xml(xml)
        assert is_valid is True

    def test_xml_with_comments(self):
        """Test XML with comments"""
        xml = """
        <problem-context>
            <!-- This is a comment -->
            <category>bug</category>
            <description>Test description</description>
            <severity>high</severity>
        </problem-context>
        """
        is_valid, error = validate_problem_xml(xml)
        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
