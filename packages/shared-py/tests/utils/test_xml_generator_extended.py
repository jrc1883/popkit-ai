#!/usr/bin/env python3
"""
Extended test suite for xml_generator.py

Tests coverage for functions missing direct unit tests:
- generate_project_context_xml()
- infer_category()
- infer_severity()
- Validation parameter behavior
- Edge cases and error handling
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.xml_generator import (
    generate_findings_xml,
    generate_problem_xml,
    generate_project_context_xml,
    generate_workflow_steps,
    infer_category,
    infer_severity,
)


class TestInferCategory:
    """Test category inference from user messages"""

    def test_infer_bug_category(self):
        """Test bug category inference"""
        test_cases = [
            "Fix the login bug",
            "There's an error in the authentication",
            "The app crashes when I click submit",
            "Something is broken in the UI",
            "This doesn't work anymore",
        ]
        for message in test_cases:
            assert infer_category(message) == "bug"

    def test_infer_feature_category(self):
        """Test feature category inference"""
        test_cases = [
            "Add dark mode support",
            "Implement user registration",
            "Create a new dashboard",
            "Build the payment system",
            "Add feature for export",
        ]
        for message in test_cases:
            assert infer_category(message) == "feature"

    def test_infer_optimization_category(self):
        """Test optimization category inference"""
        test_cases = [
            "Optimize the database queries",
            "Improve page load performance",
            "Make the app faster",
            "Speed up the search",
            "Reduce memory usage",
        ]
        for message in test_cases:
            assert infer_category(message) == "optimization"

    def test_infer_refactor_category(self):
        """Test refactor category inference"""
        test_cases = [
            "Refactor the authentication module",
            "Restructure the components",
            "Clean up the code",
            "Simplify the API",
            "Rewrite the parser",
        ]
        for message in test_cases:
            assert infer_category(message) == "refactor"

    def test_infer_investigation_category(self):
        """Test investigation category inference"""
        test_cases = [
            "Investigate why the deployment fails",
            "Debug the memory leak",
            "Analyze the performance issues",
            "Understand how the auth works",
            "Research best practices for caching",
        ]
        for message in test_cases:
            assert infer_category(message) == "investigation"

    def test_infer_docs_category(self):
        """Test docs category inference"""
        test_cases = [
            "Write documentation for the API",
            "Update the README",
            "Document the new features",
            "Explain how the system works",
            "Describe the architecture",
        ]
        for message in test_cases:
            assert infer_category(message) == "docs"

    def test_infer_test_category(self):
        """Test test category inference"""
        test_cases = [
            "Write tests for the login",
            "Add unit tests",
            "Improve test coverage",
            "Create integration tests",
            "Test the new feature",
        ]
        for message in test_cases:
            assert infer_category(message) == "test"

    def test_infer_default_task_category(self):
        """Test default task category"""
        test_cases = ["Do something", "Handle this", "Process the request", "Deploy to production"]
        for message in test_cases:
            assert infer_category(message) == "task"

    def test_category_priority_order(self):
        """Test that more specific categories take precedence"""
        # "test" should match before "bug" even if "error" is present
        assert infer_category("Write tests for error handling") == "test"

        # "docs" should match before "feature"
        assert infer_category("Document the new feature") == "docs"


class TestInferSeverity:
    """Test severity inference from user messages"""

    def test_infer_critical_severity(self):
        """Test critical severity inference"""
        test_cases = [
            "CRITICAL: Production is down",
            "Urgent bug in payment system",
            "System crash affecting all users",
            "Emergency: Data loss detected",
            "Blocker: Can't deploy",
        ]
        for message in test_cases:
            assert infer_severity(message) == "critical"

    def test_infer_high_severity(self):
        """Test high severity inference"""
        test_cases = [
            "Important fix needed",
            "High priority task",
            "Major bug in authentication",
            "Serious security issue",
            "Significant performance problem",
        ]
        for message in test_cases:
            assert infer_severity(message) == "high"

    def test_infer_low_severity(self):
        """Test low severity inference"""
        test_cases = [
            "Minor UI tweak",
            "Low priority enhancement",
            "Trivial bug fix",
            "Nice to have feature",
            "Cosmetic improvement",
        ]
        for message in test_cases:
            assert infer_severity(message) == "low"

    def test_infer_default_medium_severity(self):
        """Test default medium severity"""
        test_cases = ["Fix the login", "Add dark mode", "Update dependencies", "Refactor code"]
        for message in test_cases:
            assert infer_severity(message) == "medium"

    def test_severity_with_context(self):
        """Test severity inference with context parameter"""
        message = "Fix the issue"
        # Context doesn't currently affect severity, but parameter should be accepted
        context = {"priority": "high"}
        severity = infer_severity(message, context)
        assert severity in ["critical", "high", "medium", "low"]


class TestGenerateProjectContextXml:
    """Test project context XML generation"""

    def test_generate_complete_project_context(self):
        """Test generating complete project context"""
        context = {
            "name": "popkit-ai",
            "stack": ["Python", "TypeScript", "Markdown"],
            "infrastructure": {"redis": False, "postgres": True, "docker": True},
            "current_work": {"focus": "XML testing strategy", "issue": "Security hardening"},
        }

        xml = generate_project_context_xml(context)

        assert '<project version="1.0">' in xml
        assert "<name>popkit-ai</name>" in xml
        assert "<technology>Python</technology>" in xml
        assert "<technology>TypeScript</technology>" in xml
        assert "<redis>false</redis>" in xml
        assert "<postgres>true</postgres>" in xml
        assert "<docker>true</docker>" in xml
        assert "<focus>XML testing strategy</focus>" in xml

    def test_generate_minimal_project_context(self):
        """Test generating minimal project context"""
        context = {"name": "test-project"}

        xml = generate_project_context_xml(context)

        assert "<name>test-project</name>" in xml
        assert "<stack>" in xml
        assert "<infrastructure>" in xml
        assert "<current-work>" in xml

    def test_generate_with_empty_collections(self):
        """Test generating with empty stack and infrastructure"""
        context = {"name": "test", "stack": [], "infrastructure": {}, "current_work": {}}

        xml = generate_project_context_xml(context)

        assert "<name>test</name>" in xml
        assert xml.count("<stack>") == 1
        assert xml.count("</stack>") == 1

    def test_generate_with_dict_stack(self):
        """Test generating with dict-based stack"""
        context = {"name": "test", "stack": {"frontend": "React", "backend": "Node.js"}}

        xml = generate_project_context_xml(context)

        assert "<frontend>React</frontend>" in xml
        assert "<backend>Node.js</backend>" in xml

    def test_generate_with_nested_infrastructure(self):
        """Test generating with nested infrastructure"""
        context = {
            "name": "test",
            "infrastructure": {"database": {"type": "postgres", "version": "14"}},
        }

        xml = generate_project_context_xml(context)

        assert "<database>" in xml
        assert "<type>postgres</type>" in xml
        assert "<version>14</version>" in xml

    def test_generate_with_multiple_current_work_items(self):
        """Test generating with list of current work items"""
        context = {"name": "test", "current_work": {"issues": ["Issue 1", "Issue 2", "Issue 3"]}}

        xml = generate_project_context_xml(context)

        assert "<issues>Issue 1</issues>" in xml
        assert "<issues>Issue 2</issues>" in xml
        assert "<issues>Issue 3</issues>" in xml

    def test_generate_with_special_characters(self):
        """Test XML escaping in project context"""
        context = {"name": 'test & "special" <chars>', "stack": ["Node.js & Express"]}

        xml = generate_project_context_xml(context)

        assert "&amp;" in xml
        assert "&quot;" in xml
        assert "&lt;" in xml
        assert "&gt;" in xml


class TestValidationParameter:
    """Test optional validation parameter"""

    def test_generate_problem_with_validation(self):
        """Test problem XML generation with validation enabled"""
        xml = generate_problem_xml("Fix bug", validate=True)
        assert '<problem-context version="1.0">' in xml
        assert "<category>bug</category>" in xml

    def test_generate_project_with_validation(self):
        """Test project XML generation with validation enabled"""
        context = {"name": "test"}
        xml = generate_project_context_xml(context, validate=True)
        assert '<project version="1.0">' in xml
        assert "<name>test</name>" in xml

    def test_generate_findings_with_validation(self):
        """Test findings XML generation with validation enabled"""
        findings = {"tool": "Write", "status": "success", "quality_score": 0.85}
        xml = generate_findings_xml(findings, validate=True)
        assert '<findings version="1.0">' in xml
        assert "<tool>Write</tool>" in xml

    def test_validation_without_lxml(self):
        """Test validation parameter without lxml available"""
        # This should not crash even if lxml is not available
        xml = generate_problem_xml("Test", validate=True)
        assert "<problem-context" in xml


class TestQualityScoreClamping:
    """Test quality score clamping in findings generation"""

    def test_quality_score_above_max(self):
        """Test quality score clamped to 1.0"""
        findings = {"tool": "Test", "status": "success", "quality_score": 1.5}
        xml = generate_findings_xml(findings)
        assert "<quality_score>1.00</quality_score>" in xml

    def test_quality_score_below_min(self):
        """Test quality score clamped to 0.0"""
        findings = {"tool": "Test", "status": "success", "quality_score": -0.5}
        xml = generate_findings_xml(findings)
        assert "<quality_score>0.00</quality_score>" in xml

    def test_quality_score_valid_range(self):
        """Test quality scores within valid range"""
        for score in [0.0, 0.25, 0.5, 0.75, 1.0]:
            findings = {"tool": "Test", "status": "success", "quality_score": score}
            xml = generate_findings_xml(findings)
            assert f"<quality_score>{score:.2f}</quality_score>" in xml


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_user_message(self):
        """Test handling of empty user message"""
        xml = generate_problem_xml("")
        assert "<description></description>" in xml
        assert "<category>task</category>" in xml  # Default category

    def test_very_long_description(self):
        """Test truncation of very long descriptions"""
        long_message = "A" * 500
        xml = generate_problem_xml(long_message)

        # Should be truncated to 200 chars (197 + "...")
        assert len(long_message) > 200
        assert "..." in xml
        assert "AAAA" in xml  # Should still have the start

    def test_unicode_in_message(self):
        """Test Unicode characters in messages"""
        xml = generate_problem_xml("Fix emoji support 🚀 and 世界")
        assert "🚀" in xml or "&#" in xml  # Either raw or escaped
        assert "世界" in xml or "&#" in xml

    def test_xml_special_characters_escaped(self):
        """Test XML special characters are escaped"""
        xml = generate_problem_xml('Test <script> & "quotes"')
        assert "&lt;script&gt;" in xml
        assert "&amp;" in xml
        assert "&quot;" in xml

    def test_none_context_handling(self):
        """Test handling of None context parameter"""
        xml = generate_problem_xml("Test", context=None)
        assert "<problem-context" in xml

    def test_missing_findings_fields(self):
        """Test findings with missing optional fields"""
        findings = {"tool": "Bash"}
        xml = generate_findings_xml(findings)

        assert "<tool>Bash</tool>" in xml
        assert "<status>unknown</status>" in xml
        assert "<quality_score>0.00</quality_score>" in xml


class TestWorkflowGeneration:
    """Test workflow generation for different categories"""

    def test_workflow_for_all_categories(self):
        """Test workflow generation for all category types"""
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

        for category in categories:
            workflow = generate_workflow_steps(category)
            assert "<workflow>" in workflow
            assert "</workflow>" in workflow
            assert "<step" in workflow
            assert "<action>" in workflow

    def test_workflow_contains_required_step(self):
        """Test all workflows contain blocking first step"""
        workflow = generate_workflow_steps("bug")
        assert 'required="true"' in workflow
        assert 'blocking="true"' in workflow


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
