#!/usr/bin/env python3
"""
Unit tests for hooks/utils/xml_generator.py

Tests XML generation from plain text and context.
"""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks" / "utils"))

from xml_generator import (
    infer_category,
    infer_severity,
    generate_workflow_steps,
    generate_problem_xml,
    generate_project_context_xml,
    _escape_xml,
)


class TestCategoryInference(unittest.TestCase):
    """Test category inference from user messages."""

    def test_infer_bug_category(self):
        """Test bug category detection."""
        messages = [
            "Fix the login bug",
            "The app crashes when I click submit",
            "Error in the validation",
            "This is broken",
            "Login doesn't work"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                self.assertEqual(infer_category(msg), "bug")

    def test_infer_feature_category(self):
        """Test feature category detection."""
        messages = [
            "Add dark mode",
            "Implement OAuth",
            "Create new user profile page",
            "Build payment integration",
            "New feature for notifications"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                self.assertEqual(infer_category(msg), "feature")

    def test_infer_optimization_category(self):
        """Test optimization category detection."""
        messages = [
            "Optimize the database queries",
            "Improve page load performance",
            "Make it faster",
            "Reduce bundle size",
            "Speed up the API"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                self.assertEqual(infer_category(msg), "optimization")

    def test_infer_refactor_category(self):
        """Test refactor category detection."""
        messages = [
            "Refactor the auth module",
            "Restructure the components",
            "Clean up the code",
            "Simplify the logic"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                self.assertEqual(infer_category(msg), "refactor")

    def test_infer_investigation_category(self):
        """Test investigation category detection."""
        messages = [
            "Investigate the performance issue",
            "Debug the error",
            "Analyze why this happens",
            "Understand the codebase",
            "Research authentication patterns"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                self.assertEqual(infer_category(msg), "investigation")

    def test_infer_docs_category(self):
        """Test documentation category detection."""
        messages = [
            "Document the API",
            "Write documentation for the auth flow",
            "Update the README",
            "Describe how to use this"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                self.assertEqual(infer_category(msg), "docs")

    def test_infer_test_category(self):
        """Test testing category detection."""
        messages = [
            "Write tests for the auth module",
            "Add unit tests",
            "Improve test coverage",
            "Create integration tests"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                self.assertEqual(infer_category(msg), "test")

    def test_infer_default_category(self):
        """Test default category for unclear messages."""
        messages = [
            "Do something",
            "Handle this",
            "Process the data"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                self.assertEqual(infer_category(msg), "task")


class TestSeverityInference(unittest.TestCase):
    """Test severity inference from messages."""

    def test_infer_critical_severity(self):
        """Test critical severity detection."""
        messages = [
            "Critical production bug",
            "Urgent: app is down",
            "Production outage",
            "Emergency crash",
            "System is completely broken - blocker"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                self.assertEqual(infer_severity(msg), "critical")

    def test_infer_high_severity(self):
        """Test high severity detection."""
        messages = [
            "Important bug to fix",
            "High priority issue",
            "Major problem with auth",
            "Significant performance issue",
            "This is blocking deployment"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                self.assertEqual(infer_severity(msg), "high")

    def test_infer_low_severity(self):
        """Test low severity detection."""
        messages = [
            "Minor UI issue",
            "Low priority bug",
            "Trivial spacing problem",
            "Nice to have feature",
            "Cosmetic improvement"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                self.assertEqual(infer_severity(msg), "low")

    def test_infer_medium_severity_default(self):
        """Test default medium severity."""
        messages = [
            "Fix the validation",
            "Add dark mode",
            "Update the documentation"
        ]

        for msg in messages:
            with self.subTest(msg=msg):
                self.assertEqual(infer_severity(msg), "medium")


class TestWorkflowGeneration(unittest.TestCase):
    """Test workflow step generation."""

    def test_generate_bug_workflow(self):
        """Test bug workflow generation."""
        workflow = generate_workflow_steps("bug")

        # Verify it's valid XML
        root = ET.fromstring(f"<root>{workflow}</root>")

        # Verify structure
        self.assertIsNotNone(root.find(".//step[@id='1']"))
        self.assertIsNotNone(root.find(".//conditional"))
        self.assertTrue("search-existing-code" in workflow)

    def test_generate_feature_workflow(self):
        """Test feature workflow generation."""
        workflow = generate_workflow_steps("feature")

        # Verify it's valid XML
        root = ET.fromstring(f"<root>{workflow}</root>")

        # Verify structure
        self.assertIsNotNone(root.find(".//step[@id='1']"))
        self.assertTrue("check-github-project" in workflow)
        self.assertTrue("improve-existing-code" in workflow)
        self.assertTrue("implement-from-scratch" in workflow)

    def test_generate_optimization_workflow(self):
        """Test optimization workflow generation."""
        workflow = generate_workflow_steps("optimization")

        # Verify it's valid XML
        root = ET.fromstring(f"<root>{workflow}</root>")

        # Verify structure
        self.assertTrue("analyze-current-performance" in workflow)
        self.assertTrue("implement-optimizations" in workflow)

    def test_generate_refactor_workflow(self):
        """Test refactor workflow generation."""
        workflow = generate_workflow_steps("refactor")

        root = ET.fromstring(f"<root>{workflow}</root>")
        self.assertTrue("understand-existing-code" in workflow)
        self.assertTrue("refactor-with-tests" in workflow)

    def test_generate_investigation_workflow(self):
        """Test investigation workflow generation."""
        workflow = generate_workflow_steps("investigation")

        root = ET.fromstring(f"<root>{workflow}</root>")
        self.assertTrue("gather-information" in workflow)
        self.assertTrue("analyze-findings" in workflow)

    def test_generate_default_workflow(self):
        """Test default task workflow generation."""
        workflow = generate_workflow_steps("unknown")

        root = ET.fromstring(f"<root>{workflow}</root>")
        self.assertTrue("understand-requirements" in workflow)
        self.assertTrue("implement-task" in workflow)

    def test_all_workflows_valid_xml(self):
        """Test that all category workflows generate valid XML."""
        categories = ["bug", "feature", "optimization", "refactor",
                     "investigation", "docs", "test", "task"]

        for category in categories:
            with self.subTest(category=category):
                workflow = generate_workflow_steps(category)

                # Should parse without error
                try:
                    ET.fromstring(f"<root>{workflow}</root>")
                except ET.ParseError as e:
                    self.fail(f"Invalid XML for category {category}: {e}")


class TestProblemXMLGeneration(unittest.TestCase):
    """Test complete problem XML generation."""

    def test_generate_problem_xml_basic(self):
        """Test basic problem XML generation."""
        xml = generate_problem_xml("Fix the login bug")

        # Should be valid XML
        root = ET.fromstring(xml)

        # Verify structure
        self.assertEqual(root.tag, "problem-context")
        self.assertEqual(root.find("category").text, "bug")
        self.assertTrue("Fix the login bug" in root.find("description").text)
        self.assertIsNotNone(root.find("severity"))
        self.assertIsNotNone(root.find("workflow"))

    def test_generate_problem_xml_with_context(self):
        """Test problem XML generation with context."""
        context = {"project": "popkit"}
        xml = generate_problem_xml("Add dark mode", context)

        root = ET.fromstring(xml)
        self.assertEqual(root.find("category").text, "feature")

    def test_xml_escaping(self):
        """Test that special characters are escaped."""
        xml = generate_problem_xml("Fix bug with <script> tags & quotes")

        # Should be valid XML (no parsing errors)
        root = ET.fromstring(xml)

        # Verify escaping
        desc = root.find("description").text
        self.assertIn("&lt;script&gt;", xml)  # Raw XML has escapes
        self.assertNotIn("<script>", xml)      # Raw tag not present

    def test_long_description_truncation(self):
        """Test that long descriptions are truncated."""
        long_msg = "A" * 300  # 300 characters
        xml = generate_problem_xml(long_msg)

        root = ET.fromstring(xml)
        desc = root.find("description").text

        # Should be truncated with ellipsis
        self.assertTrue(len(desc) <= 200)
        self.assertTrue(desc.endswith("..."))

    def test_severity_inference_in_problem_xml(self):
        """Test that severity is correctly inferred."""
        critical_xml = generate_problem_xml("Critical production crash")
        low_xml = generate_problem_xml("Minor cosmetic issue")

        critical_root = ET.fromstring(critical_xml)
        low_root = ET.fromstring(low_xml)

        self.assertEqual(critical_root.find("severity").text, "critical")
        self.assertEqual(low_root.find("severity").text, "low")


class TestProjectContextXMLGeneration(unittest.TestCase):
    """Test project context XML generation."""

    def test_generate_project_context_basic(self):
        """Test basic project context generation."""
        context = {
            "name": "popkit",
            "stack": ["Next.js", "Supabase"]
        }

        xml = generate_project_context_xml(context)

        # Should be valid XML
        root = ET.fromstring(xml)

        # Verify structure
        self.assertEqual(root.tag, "project")
        self.assertEqual(root.find("name").text, "popkit")

        # Verify stack
        technologies = root.findall("stack/technology")
        self.assertEqual(len(technologies), 2)

    def test_generate_project_context_with_infrastructure(self):
        """Test project context with infrastructure."""
        context = {
            "name": "test",
            "stack": [],
            "infrastructure": {
                "redis": True,
                "postgres": False
            }
        }

        xml = generate_project_context_xml(context)
        root = ET.fromstring(xml)

        # Verify infrastructure
        redis = root.find("infrastructure/redis")
        postgres = root.find("infrastructure/postgres")

        self.assertEqual(redis.text, "true")
        self.assertEqual(postgres.text, "false")

    def test_generate_project_context_with_current_work(self):
        """Test project context with current work."""
        context = {
            "name": "test",
            "stack": [],
            "current_work": {
                "issue": "220",
                "branch": "feat/xml-integration"
            }
        }

        xml = generate_project_context_xml(context)
        root = ET.fromstring(xml)

        # Verify current work
        issue = root.find("current-work/issue")
        branch = root.find("current-work/branch")

        self.assertEqual(issue.text, "220")
        self.assertEqual(branch.text, "feat/xml-integration")

    def test_generate_project_context_empty(self):
        """Test project context with empty data."""
        context = {}
        xml = generate_project_context_xml(context)

        # Should be valid XML
        root = ET.fromstring(xml)
        self.assertEqual(root.find("name").text, "unknown")

    def test_xml_escaping_in_project_context(self):
        """Test that project context escapes XML characters."""
        context = {
            "name": "test & demo <project>",
            "stack": ["React & Redux"]
        }

        xml = generate_project_context_xml(context)

        # Should be valid XML (no parsing errors)
        root = ET.fromstring(xml)

        # Verify escaping in raw XML
        self.assertIn("&amp;", xml)
        self.assertIn("&lt;", xml)


class TestXMLEscaping(unittest.TestCase):
    """Test XML escaping utility."""

    def test_escape_ampersand(self):
        """Test escaping ampersand."""
        self.assertEqual(_escape_xml("a & b"), "a &amp; b")

    def test_escape_less_than(self):
        """Test escaping less-than."""
        self.assertEqual(_escape_xml("a < b"), "a &lt; b")

    def test_escape_greater_than(self):
        """Test escaping greater-than."""
        self.assertEqual(_escape_xml("a > b"), "a &gt; b")

    def test_escape_quotes(self):
        """Test escaping quotes."""
        self.assertEqual(_escape_xml('a "quote" b'), 'a &quot;quote&quot; b')
        self.assertEqual(_escape_xml("a 'quote' b"), "a &apos;quote&apos; b")

    def test_escape_multiple(self):
        """Test escaping multiple characters."""
        result = _escape_xml('a < b & c > d "e" \'f\'')
        self.assertEqual(result, 'a &lt; b &amp; c &gt; d &quot;e&quot; &apos;f&apos;')

    def test_escape_unicode(self):
        """Test that Unicode is preserved."""
        result = _escape_xml("Hello 世界 & émojis 🎉")
        # Unicode should be preserved, ampersand escaped
        self.assertIn("世界", result)
        self.assertIn("🎉", result)
        self.assertIn("&amp;", result)


if __name__ == '__main__':
    unittest.main()
