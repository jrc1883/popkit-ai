#!/usr/bin/env python3
"""
XML Generator for Session Context

Generates XML structures from plain text and context for enhanced Claude understanding.
Transforms user messages into structured XML with category, severity, and workflow steps.

Used by: user-prompt-submit.py hook
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import validator (optional for validation)
try:
    from popkit_shared.utils.xml_validator import (
        validate_findings_xml,
        validate_problem_xml,
        validate_project_xml,
    )

    HAS_VALIDATOR = True
except ImportError:
    HAS_VALIDATOR = False
    logger.debug("xml_validator not available, validation will be skipped")


def infer_category(message: str) -> str:
    """
    Infer problem category from message text.

    Analyzes keywords to determine the type of task or problem.

    Args:
        message: User message text

    Returns:
        Category string: bug, feature, optimization, refactor, investigation, docs, or task

    Example:
        >>> infer_category("Fix the login bug")
        'bug'
        >>> infer_category("Add dark mode")
        'feature'
        >>> infer_category("Optimize the database queries")
        'optimization'
    """
    message_lower = message.lower()

    # Define keyword categories (order matters - more specific first)
    # Check docs, test, and investigation before more general categories
    categories = {
        "docs": ["document", "documentation", "readme", "doc", "explain", "describe", "write docs"],
        "test": ["test", "testing", "coverage", "unit test", "integration test", "write tests"],
        "investigation": [
            "investigate",
            "debug",
            "trace",
            "analyze",
            "why",
            "understand",
            "explore",
            "research",
        ],
        "bug": [
            "bug",
            "error",
            "crash",
            "broken",
            "fails",
            "doesn't work",
            "not working",
            "issue",
            "problem",
            "wrong",
            "incorrect",
            "fix",
        ],
        "optimization": [
            "optimize",
            "improve",
            "faster",
            "performance",
            "slow",
            "speed up",
            "efficiency",
            "reduce",
        ],
        "refactor": [
            "refactor",
            "restructure",
            "clean up",
            "reorganize",
            "simplify",
            "rewrite",
            "cleanup",
        ],
        "feature": ["add", "implement", "create", "build", "new", "feature", "support"],
    }

    # Check each category's keywords
    for category, keywords in categories.items():
        if any(keyword in message_lower for keyword in keywords):
            return category

    # Default category
    return "task"


def infer_severity(message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Infer severity level from message and context.

    Analyzes urgency keywords and context to determine priority.

    Args:
        message: User message text
        context: Optional context dict (not currently used, reserved for future)

    Returns:
        Severity string: critical, high, medium, or low

    Example:
        >>> infer_severity("Critical production bug")
        'critical'
        >>> infer_severity("Minor UI issue")
        'low'
        >>> infer_severity("Add feature")
        'medium'
    """
    message_lower = message.lower()

    # Critical severity keywords
    if any(
        word in message_lower
        for word in [
            "critical",
            "urgent",
            "production",
            "crash",
            "down",
            "outage",
            "emergency",
            "blocker",
        ]
    ):
        return "critical"

    # High severity keywords
    if any(
        word in message_lower
        for word in ["important", "high", "major", "blocking", "serious", "significant"]
    ):
        return "high"

    # Low severity keywords
    if any(
        word in message_lower
        for word in ["minor", "low", "trivial", "nice to have", "cosmetic", "polish"]
    ):
        return "low"

    # Default to medium
    return "medium"


def generate_workflow_steps(category: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate workflow XML based on category and context.

    Creates structured workflow steps appropriate for the task category.
    Each workflow includes mandatory first step to check existing code.

    Args:
        category: Task category (bug, feature, optimization, etc.)
        context: Optional context dict (reserved for future use)

    Returns:
        XML string with workflow steps

    Example:
        >>> xml = generate_workflow_steps("bug")
        >>> "<step id" in xml
        True
        >>> "search-existing-code" in xml
        True
    """
    if category == "bug":
        return """  <workflow>
    <step id="1" required="true" blocking="true">
      <action>search-existing-code</action>
      <target>bug location and related code</target>
      <success-criteria>
        <criterion>Located problematic code</criterion>
        <criterion>Identified root cause</criterion>
      </success-criteria>
    </step>
    <conditional on-step="1">
      <branch condition="existing-code-found">
        <step id="2a" required="true">
          <action>fix-existing-code</action>
          <constraint>No breaking changes</constraint>
          <verification>Run existing tests</verification>
        </step>
      </branch>
      <branch condition="no-code-found">
        <step id="2b" required="true">
          <action>implement-missing-functionality</action>
          <constraint>Follow project patterns</constraint>
          <verification>Add tests for new code</verification>
        </step>
      </branch>
    </conditional>
  </workflow>"""

    elif category == "feature":
        return """  <workflow>
    <step id="1" required="true" blocking="true">
      <action>check-github-project</action>
      <target>existing implementations and related features</target>
      <success-criteria>
        <criterion>Searched for similar features</criterion>
        <criterion>Reviewed existing patterns</criterion>
      </success-criteria>
    </step>
    <conditional on-step="1">
      <branch condition="existing-code-found">
        <step id="2a" required="true">
          <action>improve-existing-code</action>
          <constraint>Maintain backward compatibility</constraint>
          <verification>Extend existing tests</verification>
        </step>
      </branch>
      <branch condition="no-code-found">
        <step id="2b" required="true">
          <action>implement-from-scratch</action>
          <constraint>Follow project architecture</constraint>
          <verification>Write comprehensive tests</verification>
        </step>
      </branch>
    </conditional>
  </workflow>"""

    elif category == "optimization":
        return """  <workflow>
    <step id="1" required="true" blocking="true">
      <action>analyze-current-performance</action>
      <target>bottlenecks and metrics</target>
      <success-criteria>
        <criterion>Established baseline metrics</criterion>
        <criterion>Identified optimization targets</criterion>
      </success-criteria>
    </step>
    <step id="2" required="true">
      <action>implement-optimizations</action>
      <constraint>Maintain correctness</constraint>
      <verification>Benchmark before/after</verification>
    </step>
  </workflow>"""

    elif category == "refactor":
        return """  <workflow>
    <step id="1" required="true" blocking="true">
      <action>understand-existing-code</action>
      <target>code to be refactored</target>
      <success-criteria>
        <criterion>Identified all dependencies</criterion>
        <criterion>Understood current behavior</criterion>
      </success-criteria>
    </step>
    <step id="2" required="true">
      <action>refactor-with-tests</action>
      <constraint>No behavior changes</constraint>
      <verification>All existing tests still pass</verification>
    </step>
  </workflow>"""

    elif category == "investigation":
        return """  <workflow>
    <step id="1" required="true" blocking="true">
      <action>gather-information</action>
      <target>codebase, logs, documentation</target>
      <success-criteria>
        <criterion>Located relevant code</criterion>
        <criterion>Collected necessary context</criterion>
      </success-criteria>
    </step>
    <step id="2" required="true">
      <action>analyze-findings</action>
      <verification>Document conclusions</verification>
    </step>
  </workflow>"""

    elif category == "docs":
        return """  <workflow>
    <step id="1" required="true" blocking="true">
      <action>review-existing-docs</action>
      <target>current documentation</target>
      <success-criteria>
        <criterion>Identified gaps or outdated content</criterion>
      </success-criteria>
    </step>
    <step id="2" required="true">
      <action>write-or-update-docs</action>
      <verification>Review for clarity and accuracy</verification>
    </step>
  </workflow>"""

    elif category == "test":
        return """  <workflow>
    <step id="1" required="true" blocking="true">
      <action>analyze-test-coverage</action>
      <target>existing tests and coverage gaps</target>
      <success-criteria>
        <criterion>Identified untested code paths</criterion>
      </success-criteria>
    </step>
    <step id="2" required="true">
      <action>write-tests</action>
      <verification>All new tests passing</verification>
    </step>
  </workflow>"""

    else:  # task or unknown
        return """  <workflow>
    <step id="1" required="true" blocking="true">
      <action>understand-requirements</action>
      <target>task objectives and constraints</target>
      <success-criteria>
        <criterion>Clear understanding of goal</criterion>
      </success-criteria>
    </step>
    <step id="2" required="true">
      <action>implement-task</action>
      <verification>Verify completion</verification>
    </step>
  </workflow>"""


def generate_problem_xml(
    user_message: str, context: Optional[Dict[str, Any]] = None, validate: bool = False
) -> str:
    """
    Generate <problem> XML from user message.

    Analyzes the message and generates structured XML with category,
    description, severity, and workflow steps.

    Args:
        user_message: Plain text user message
        context: Optional context dict for additional information
        validate: If True, validates XML against schema (requires lxml)

    Returns:
        XML string with problem structure

    Example:
        >>> xml = generate_problem_xml("Fix the login bug")
        >>> "<category>bug</category>" in xml
        True
        >>> "<workflow>" in xml
        True
    """
    if context is None:
        context = {}

    # Analyze message
    category = infer_category(user_message)
    severity = infer_severity(user_message, context)

    # Extract description (clean up the message)
    description = user_message.strip()

    # Limit description length
    if len(description) > 200:
        description = description[:197] + "..."

    # Escape XML special characters
    description = _escape_xml(description)

    # Generate workflow
    workflow = generate_workflow_steps(category, context)

    xml = f"""<problem-context version="1.0">
  <category>{category}</category>
  <description>{description}</description>
  <severity>{severity}</severity>
{workflow}
</problem-context>"""

    # Optional validation
    if validate and HAS_VALIDATOR:
        is_valid, error = validate_problem_xml(xml)
        if not is_valid:
            logger.warning(f"Generated invalid problem XML: {error}")
            # Continue anyway (graceful degradation)

    return xml


def generate_project_context_xml(context: Dict[str, Any], validate: bool = False) -> str:
    """
    Generate <project> XML from detected project info.

    Structures project information like stack, infrastructure, and current work.

    Args:
        context: Dict with project information:
            - name: Project name
            - stack: List of technologies
            - infrastructure: Dict of infrastructure components
            - current_work: Dict with issues, branch, etc.
        validate: If True, validates XML against schema (requires lxml)

    Returns:
        XML string with project context

    Example:
        >>> context = {"name": "popkit", "stack": ["Next.js", "Supabase"]}
        >>> xml = generate_project_context_xml(context)
        >>> "<name>popkit</name>" in xml
        True
    """
    name = context.get("name", "unknown")
    stack = context.get("stack", [])
    infrastructure = context.get("infrastructure", {})
    current_work = context.get("current_work", {})

    # Generate stack XML
    stack_xml = ""
    if stack:
        if isinstance(stack, list):
            for tech in stack:
                stack_xml += f"\n    <technology>{_escape_xml(str(tech))}</technology>"
        elif isinstance(stack, dict):
            for key, value in stack.items():
                stack_xml += f"\n    <{key}>{_escape_xml(str(value))}</{key}>"

    # Generate infrastructure XML
    infra_xml = ""
    if infrastructure:
        for key, value in infrastructure.items():
            if isinstance(value, bool):
                infra_xml += f"\n    <{key}>{str(value).lower()}</{key}>"
            elif isinstance(value, dict):
                infra_xml += f"\n    <{key}>"
                for k, v in value.items():
                    infra_xml += f"\n      <{k}>{_escape_xml(str(v))}</{k}>"
                infra_xml += f"\n    </{key}>"
            else:
                infra_xml += f"\n    <{key}>{_escape_xml(str(value))}</{key}>"

    # Generate current work XML
    work_xml = ""
    if current_work:
        for key, value in current_work.items():
            if isinstance(value, list):
                for item in value:
                    work_xml += f"\n    <{key}>{_escape_xml(str(item))}</{key}>"
            else:
                work_xml += f"\n    <{key}>{_escape_xml(str(value))}</{key}>"

    xml = f"""<project version="1.0">
  <name>{_escape_xml(name)}</name>
  <stack>{stack_xml}
  </stack>
  <infrastructure>{infra_xml}
  </infrastructure>
  <current-work>{work_xml}
  </current-work>
</project>"""

    # Optional validation
    if validate and HAS_VALIDATOR:
        is_valid, error = validate_project_xml(xml)
        if not is_valid:
            logger.warning(f"Generated invalid project XML: {error}")
            # Continue anyway (graceful degradation)

    return xml


def generate_findings_xml(findings: Dict[str, Any], validate: bool = False) -> str:
    """
    Generate <findings> XML from tool execution results (Phase 1: XML Integration #517).

    Creates structured XML output that next agents can parse to understand
    tool execution context, success/error status, and recommended actions.

    Args:
        findings: Dict with tool results:
            - tool: Tool name
            - status: "success" or "error"
            - quality_score: Float 0.0-1.0
            - issues: List of issue descriptions
            - suggestions: List of suggestions
            - followup_agents: List of recommended agents
            - error_message: Optional error message (if status is "error")
        validate: If True, validates XML against schema (requires lxml)

    Returns:
        XML string with findings structure

    Example:
        >>> findings = {
        ...     "tool": "Write",
        ...     "status": "success",
        ...     "quality_score": 0.8,
        ...     "issues": ["Potential secret exposed"],
        ...     "suggestions": ["Run security review"],
        ...     "followup_agents": ["security-auditor"]
        ... }
        >>> xml = generate_findings_xml(findings)
        >>> "<tool>Write</tool>" in xml
        True
        >>> "<status>success</status>" in xml
        True
    """
    tool = findings.get("tool", "unknown")
    status = findings.get("status", "unknown")
    quality_score = findings.get("quality_score", 0.0)

    # Clamp quality_score to 0.0-1.0 range
    quality_score = max(0.0, min(1.0, float(quality_score)))

    issues = findings.get("issues", [])
    suggestions = findings.get("suggestions", [])
    followup_agents = findings.get("followup_agents", [])
    error_message = findings.get("error_message")

    # Generate issues XML
    issues_xml = ""
    if issues:
        for issue in issues:
            issues_xml += f"\n    <issue>{_escape_xml(str(issue))}</issue>"

    # Generate suggestions XML
    suggestions_xml = ""
    if suggestions:
        for suggestion in suggestions:
            suggestions_xml += f"\n    <suggestion>{_escape_xml(str(suggestion))}</suggestion>"

    # Generate follow-up agents XML
    agents_xml = ""
    if followup_agents:
        for agent in followup_agents:
            agents_xml += f"\n    <agent>{_escape_xml(str(agent))}</agent>"

    # Generate error message XML if present
    error_xml = ""
    if error_message:
        error_xml = f"\n  <error_message>{_escape_xml(str(error_message))}</error_message>"

    xml = f"""<findings version="1.0">
  <tool>{_escape_xml(tool)}</tool>
  <status>{status}</status>
  <quality_score>{quality_score:.2f}</quality_score>
  <issues>{issues_xml}
  </issues>
  <suggestions>{suggestions_xml}
  </suggestions>
  <followup_agents>{agents_xml}
  </followup_agents>{error_xml}
</findings>"""

    # Optional validation
    if validate and HAS_VALIDATOR:
        is_valid, error = validate_findings_xml(xml)
        if not is_valid:
            logger.warning(f"Generated invalid findings XML: {error}")
            # Continue anyway (graceful degradation)

    return xml


def _escape_xml(text: str) -> str:
    """
    Escape XML special characters.

    Args:
        text: Text to escape

    Returns:
        XML-escaped text

    Example:
        >>> _escape_xml("a < b & c > d")
        'a &lt; b &amp; c &gt; d'
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


# Public API
__all__ = [
    "generate_problem_xml",
    "generate_project_context_xml",
    "generate_workflow_steps",
    "generate_findings_xml",
    "infer_category",
    "infer_severity",
]
