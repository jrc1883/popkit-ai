#!/usr/bin/env python3
"""
Test script for XML parsing and agent routing (Issue #516)
Tests parse_xml_context() and suggest_agent_from_context() functions
"""

import re
import sys
from typing import Any, Dict, List, Optional


def parse_xml_context(conversation_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Parse XML context from recent messages for agent routing (Phase 1: XML Integration #516).
    """
    try:
        # Search recent messages for XML context (check last 5 messages)
        for message in reversed(conversation_history[-5:]):
            content = message.get("content", "")

            # Look for XML context markers
            if "<!-- XML Context (Invisible) -->" not in content:
                continue

            # Extract XML content between markers
            xml_start = content.find("<!-- XML Context (Invisible) -->")
            xml_end = content.find("<!-- End XML Context -->")

            if xml_start == -1 or xml_end == -1:
                continue

            xml_content = content[xml_start:xml_end]

            # Parse problem context
            problem_match = re.search(r"<problem>(.*?)</problem>", xml_content, re.DOTALL)
            if not problem_match:
                continue

            problem_xml = problem_match.group(1)

            # Extract fields from problem XML
            parsed_context = {}

            # Category (required)
            category_match = re.search(r"<category>(.*?)</category>", problem_xml)
            if category_match:
                parsed_context["category"] = category_match.group(1).strip()

            # Severity (optional)
            severity_match = re.search(r"<severity>(.*?)</severity>", problem_xml)
            if severity_match:
                parsed_context["severity"] = severity_match.group(1).strip()

            # Workflow (optional)
            workflow_match = re.search(r"<workflow>(.*?)</workflow>", problem_xml, re.DOTALL)
            if workflow_match:
                parsed_context["workflow"] = workflow_match.group(1).strip()

            # Parse project context for stack and infrastructure
            project_match = re.search(
                r"<project-context>(.*?)</project-context>", xml_content, re.DOTALL
            )
            if project_match:
                project_xml = project_match.group(1)

                # Extract stack
                stack_items = re.findall(r"<item>(.*?)</item>", project_xml)
                if stack_items:
                    parsed_context["stack"] = stack_items

                # Extract infrastructure
                infra_match = re.search(
                    r"<infrastructure>(.*?)</infrastructure>", project_xml, re.DOTALL
                )
                if infra_match:
                    infra_xml = infra_match.group(1)
                    infrastructure = {}

                    # Parse each infrastructure item
                    for service in [
                        "redis",
                        "postgres",
                        "mongodb",
                        "mysql",
                        "elasticsearch",
                        "rabbitmq",
                        "kafka",
                        "docker",
                        "kubernetes",
                    ]:
                        service_match = re.search(f"<{service}>(.*?)</{service}>", infra_xml)
                        if service_match:
                            infrastructure[service] = (
                                service_match.group(1).strip().lower() == "true"
                            )

                    parsed_context["infrastructure"] = infrastructure

            # Return parsed context if we found at least a category
            if "category" in parsed_context:
                return parsed_context

        # No XML context found
        return None

    except Exception as e:
        print(f"Warning: XML context parsing failed: {e}", file=sys.stderr)
        return None


def suggest_agent_from_context(xml_context: Dict[str, Any]) -> Optional[str]:
    """
    Suggest appropriate agent based on XML context category and severity.
    """
    if not xml_context or "category" not in xml_context:
        return None

    category = xml_context.get("category", "").lower()
    severity = xml_context.get("severity", "medium").lower()

    # Category-to-agent mapping
    agent_map = {
        "bug": "bug-whisperer" if severity in ["critical", "high"] else "code-reviewer",
        "feature": "refactoring-expert",
        "optimization": "performance-optimizer",
        "refactor": "refactoring-expert",
        "security": "security-auditor",
        "test": "test-writer-fixer",
        "docs": "documentation-maintainer",
        "documentation": "documentation-maintainer",
        "investigation": "code-reviewer",
        "task": None,
    }

    suggested_agent = agent_map.get(category)

    # Additional logic based on infrastructure context
    infrastructure = xml_context.get("infrastructure", {})

    # If database-heavy task, consider query-optimizer
    if category == "optimization" and any(
        db in infrastructure for db in ["postgres", "mysql", "mongodb"]
    ):
        suggested_agent = "query-optimizer"

    return suggested_agent


def test_bug_high_severity():
    """Test XML parsing with bug category and high severity"""
    print("\n=== Test 1: Bug with High Severity ===")

    conversation = [
        {
            "role": "user",
            "content": """Fix the login bug using Redis for caching

<!-- XML Context (Invisible) -->
<problem>
<category>bug</category>
<severity>high</severity>
<description>Login session not persisting</description>
<workflow>
<step>Reproduce the bug</step>
<step>Identify root cause</step>
<step>Write failing test</step>
<step>Implement fix</step>
<step>Verify fix passes test</step>
</workflow>
</problem>

<project-context>
<project>
<name>elshaddai</name>
<stack>
<item>Next.js</item>
<item>React</item>
<item>Supabase</item>
</stack>
<infrastructure>
<redis>true</redis>
<postgres>true</postgres>
</infrastructure>
</project>
</project-context>
<!-- End XML Context -->""",
        }
    ]

    xml_context = parse_xml_context(conversation)
    print(f"Parsed Context: {xml_context}")

    if xml_context:
        suggested_agent = suggest_agent_from_context(xml_context)
        print(f"Suggested Agent: {suggested_agent}")

        # Verify
        assert xml_context["category"] == "bug", "Category should be 'bug'"
        assert xml_context["severity"] == "high", "Severity should be 'high'"
        assert suggested_agent == "bug-whisperer", (
            f"Expected 'bug-whisperer', got '{suggested_agent}'"
        )
        assert "Next.js" in xml_context["stack"], "Stack should include Next.js"
        assert xml_context["infrastructure"]["redis"], "Redis should be detected"

        print("[PASS] Test 1 PASSED")
    else:
        print("[FAIL] Test 1 FAILED: No XML context parsed")


def test_feature_category():
    """Test XML parsing with feature category"""
    print("\n=== Test 2: Feature Request ===")

    conversation = [
        {
            "role": "user",
            "content": """Add dark mode feature

<!-- XML Context (Invisible) -->
<problem>
<category>feature</category>
<severity>medium</severity>
<description>Implement dark mode toggle</description>
</problem>

<project-context>
<project>
<name>elshaddai</name>
<stack>
<item>React</item>
</stack>
</project>
</project-context>
<!-- End XML Context -->""",
        }
    ]

    xml_context = parse_xml_context(conversation)
    print(f"Parsed Context: {xml_context}")

    if xml_context:
        suggested_agent = suggest_agent_from_context(xml_context)
        print(f"Suggested Agent: {suggested_agent}")

        # Verify
        assert xml_context["category"] == "feature", "Category should be 'feature'"
        assert suggested_agent == "refactoring-expert", (
            f"Expected 'refactoring-expert', got '{suggested_agent}'"
        )

        print("[PASS] Test 2 PASSED")
    else:
        print("[FAIL] Test 2 FAILED: No XML context parsed")


def test_optimization_with_database():
    """Test optimization category with database infrastructure"""
    print("\n=== Test 3: Optimization with Database ===")

    conversation = [
        {
            "role": "user",
            "content": """Optimize database queries

<!-- XML Context (Invisible) -->
<problem>
<category>optimization</category>
<severity>medium</severity>
<description>Slow query performance</description>
</problem>

<project-context>
<project>
<name>elshaddai</name>
<infrastructure>
<postgres>true</postgres>
</infrastructure>
</project>
</project-context>
<!-- End XML Context -->""",
        }
    ]

    xml_context = parse_xml_context(conversation)
    print(f"Parsed Context: {xml_context}")

    if xml_context:
        suggested_agent = suggest_agent_from_context(xml_context)
        print(f"Suggested Agent: {suggested_agent}")

        # Verify
        assert xml_context["category"] == "optimization", "Category should be 'optimization'"
        assert suggested_agent == "query-optimizer", (
            f"Expected 'query-optimizer', got '{suggested_agent}'"
        )

        print("[PASS] Test 3 PASSED")
    else:
        print("[FAIL] Test 3 FAILED: No XML context parsed")


def test_no_xml_context():
    """Test graceful fallback when no XML context is present"""
    print("\n=== Test 4: No XML Context (Graceful Fallback) ===")

    conversation = [{"role": "user", "content": "Fix the login bug"}]

    xml_context = parse_xml_context(conversation)
    print(f"Parsed Context: {xml_context}")

    if xml_context is None:
        print("[PASS] Test 4 PASSED: Gracefully handled missing XML")
    else:
        print("[FAIL] Test 4 FAILED: Should return None when no XML present")


def test_security_category():
    """Test security category routing"""
    print("\n=== Test 5: Security Issue ===")

    conversation = [
        {
            "role": "user",
            "content": """Fix XSS vulnerability

<!-- XML Context (Invisible) -->
<problem>
<category>security</category>
<severity>critical</severity>
<description>XSS in user input</description>
</problem>
<!-- End XML Context -->""",
        }
    ]

    xml_context = parse_xml_context(conversation)
    print(f"Parsed Context: {xml_context}")

    if xml_context:
        suggested_agent = suggest_agent_from_context(xml_context)
        print(f"Suggested Agent: {suggested_agent}")

        # Verify
        assert xml_context["category"] == "security", "Category should be 'security'"
        assert suggested_agent == "security-auditor", (
            f"Expected 'security-auditor', got '{suggested_agent}'"
        )

        print("[PASS] Test 5 PASSED")
    else:
        print("[FAIL] Test 5 FAILED: No XML context parsed")


if __name__ == "__main__":
    print("Testing XML Parsing and Agent Routing (Issue #516)")
    print("=" * 60)

    test_bug_high_severity()
    test_feature_category()
    test_optimization_with_database()
    test_no_xml_context()
    test_security_category()

    print("\n" + "=" * 60)
    print("All tests completed!")
