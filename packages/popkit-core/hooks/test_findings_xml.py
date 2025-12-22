#!/usr/bin/env python3
"""
Test script for XML findings generation (Issue #517)
Tests generate_findings_xml() function and post-tool-use hook integration
"""

import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from xml_generator import generate_findings_xml


def test_successful_tool_use():
    """Test XML generation for successful tool execution"""
    print("\n=== Test 1: Successful Tool Use (Write) ===")

    findings = {
        "tool": "Write",
        "status": "success",
        "quality_score": 0.8,
        "issues": ["Potential secret exposed in code"],
        "suggestions": ["Consider running code review and linting"],
        "followup_agents": ["code-reviewer", "security-auditor"]
    }

    xml = generate_findings_xml(findings)
    print(f"Generated XML:\n{xml}")

    # Verify
    assert "<tool>Write</tool>" in xml, "Tool name should be present"
    assert "<status>success</status>" in xml, "Status should be success"
    assert "<quality_score>0.80</quality_score>" in xml, "Quality score should be formatted"
    assert "<issue>Potential secret exposed in code</issue>" in xml, "Issues should be present"
    assert "<suggestion>Consider running code review and linting</suggestion>" in xml, "Suggestions should be present"
    assert "<agent>code-reviewer</agent>" in xml, "Follow-up agents should be present"
    assert "<agent>security-auditor</agent>" in xml, "Multiple agents should be present"
    assert "<error_message>" not in xml, "No error message for successful execution"

    print("[PASS] Test 1 PASSED")


def test_failed_tool_use():
    """Test XML generation for failed tool execution"""
    print("\n=== Test 2: Failed Tool Use (Bash) ===")

    findings = {
        "tool": "Bash",
        "status": "error",
        "quality_score": 0.3,
        "issues": ["Command execution failed: permission denied"],
        "suggestions": ["Check file permissions", "Use sudo if necessary"],
        "followup_agents": ["bug-whisperer"],
        "error_message": "bash: ./script.sh: Permission denied"
    }

    xml = generate_findings_xml(findings)
    print(f"Generated XML:\n{xml}")

    # Verify
    assert "<tool>Bash</tool>" in xml, "Tool name should be present"
    assert "<status>error</status>" in xml, "Status should be error"
    assert "<quality_score>0.30</quality_score>" in xml, "Low quality score for errors"
    assert "<issue>Command execution failed: permission denied</issue>" in xml, "Error issues present"
    assert "<error_message>bash: ./script.sh: Permission denied</error_message>" in xml, "Error message should be present"
    assert "<agent>bug-whisperer</agent>" in xml, "Debug agent recommended"

    print("[PASS] Test 2 PASSED")


def test_no_issues_or_suggestions():
    """Test XML generation with no issues or suggestions"""
    print("\n=== Test 3: Clean Tool Use (Read) ===")

    findings = {
        "tool": "Read",
        "status": "success",
        "quality_score": 0.9,
        "issues": [],
        "suggestions": [],
        "followup_agents": []
    }

    xml = generate_findings_xml(findings)
    print(f"Generated XML:\n{xml}")

    # Verify
    assert "<tool>Read</tool>" in xml, "Tool name should be present"
    assert "<status>success</status>" in xml, "Status should be success"
    assert "<quality_score>0.90</quality_score>" in xml, "High quality score"
    assert "<issues>\n  </issues>" in xml, "Empty issues section"
    assert "<suggestions>\n  </suggestions>" in xml, "Empty suggestions section"
    assert "<followup_agents>\n  </followup_agents>" in xml, "Empty agents section"

    print("[PASS] Test 3 PASSED")


def test_special_characters_escaping():
    """Test XML escaping of special characters"""
    print("\n=== Test 4: Special Characters Escaping ===")

    findings = {
        "tool": "Edit",
        "status": "success",
        "quality_score": 0.75,
        "issues": ["Code contains <div> & other HTML"],
        "suggestions": ["Use proper & escaping"],
        "followup_agents": ["code-reviewer"],
        "error_message": "Warning: <tag> not escaped"
    }

    xml = generate_findings_xml(findings)
    print(f"Generated XML:\n{xml}")

    # Verify escaping
    assert "&lt;div&gt;" in xml, "< and > should be escaped"
    assert "&amp;" in xml, "& should be escaped"
    assert "&lt;tag&gt;" in xml, "Tags in error message should be escaped"
    assert "<div>" not in xml, "Unescaped HTML should not appear"

    print("[PASS] Test 4 PASSED")


def test_xml_structure_validity():
    """Test that generated XML has proper structure"""
    print("\n=== Test 5: XML Structure Validity ===")

    findings = {
        "tool": "MultiEdit",
        "status": "success",
        "quality_score": 0.85,
        "issues": ["Large refactoring with 10 changes"],
        "suggestions": ["Comprehensive review recommended", "Run all tests"],
        "followup_agents": ["code-reviewer", "test-writer-fixer"]
    }

    xml = generate_findings_xml(findings)
    print(f"Generated XML:\n{xml}")

    # Verify structure
    assert xml.startswith("<findings>"), "Should start with <findings>"
    assert xml.endswith("</findings>"), "Should end with </findings>"
    assert xml.count("<tool>") == 1, "Should have one tool element"
    assert xml.count("<status>") == 1, "Should have one status element"
    assert xml.count("<quality_score>") == 1, "Should have one quality_score element"
    assert xml.count("<issues>") == 1, "Should have one issues container"
    assert xml.count("</issues>") == 1, "Should close issues container"
    assert xml.count("<suggestions>") == 1, "Should have one suggestions container"
    assert xml.count("</suggestions>") == 1, "Should close suggestions container"
    assert xml.count("<followup_agents>") == 1, "Should have one agents container"
    assert xml.count("</followup_agents>") == 1, "Should close agents container"

    print("[PASS] Test 5 PASSED")


if __name__ == "__main__":
    print("Testing XML Findings Generation (Issue #517)")
    print("=" * 60)

    test_successful_tool_use()
    test_failed_tool_use()
    test_no_issues_or_suggestions()
    test_special_characters_escaping()
    test_xml_structure_validity()

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
