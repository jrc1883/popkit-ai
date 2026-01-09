#!/usr/bin/env python3
"""
XML Parser for PopKit Context System

Provides robust ElementTree-based parsing for PopKit's XML context structures.
Replaces fragile regex-based parsing with proper XML parsing.
"""

import xml.etree.ElementTree as ET
import re
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


def parse_problem_context(xml_string: str) -> Optional[Dict[str, Any]]:
    """
    Parses problem-context XML using ElementTree.

    Extracts category, description, severity, and workflow information
    from problem-context XML structure.

    Args:
        xml_string: XML string containing problem-context element

    Returns:
        Dictionary with parsed fields:
            - category: str
            - description: str
            - severity: str
            - workflow: Optional[Dict] with workflow structure
        Returns None if parsing fails

    Example:
        >>> xml = '<problem-context><category>bug</category><description>Test</description><severity>high</severity></problem-context>'
        >>> result = parse_problem_context(xml)
        >>> result['category']
        'bug'
    """
    try:
        root = ET.fromstring(xml_string)

        # Verify root element
        if root.tag != 'problem-context':
            logger.warning(f"Expected root element 'problem-context', got '{root.tag}'")
            return None

        result = {}

        # Extract required fields
        category = root.find('category')
        result['category'] = category.text if category is not None and category.text else None

        description = root.find('description')
        result['description'] = description.text if description is not None and description.text else None

        severity = root.find('severity')
        result['severity'] = severity.text if severity is not None and severity.text else None

        # Extract optional workflow
        workflow = root.find('workflow')
        if workflow is not None:
            result['workflow'] = _parse_workflow(workflow)
        else:
            result['workflow'] = None

        return result

    except ET.ParseError as e:
        logger.error(f"XML parsing error in parse_problem_context: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in parse_problem_context: {e}")
        return None


def parse_project_context(xml_string: str) -> Optional[Dict[str, Any]]:
    """
    Parses project context XML using ElementTree.

    Extracts project name, technology stack, infrastructure components,
    and current work information.

    Args:
        xml_string: XML string containing project element

    Returns:
        Dictionary with parsed fields:
            - name: str
            - stack: List[str] of technologies
            - infrastructure: Dict[str, bool] of infrastructure flags
            - current_work: Dict[str, Any] with current work details
        Returns None if parsing fails

    Example:
        >>> xml = '<project><name>test</name><stack><technology>Python</technology></stack></project>'
        >>> result = parse_project_context(xml)
        >>> result['name']
        'test'
    """
    try:
        root = ET.fromstring(xml_string)

        # Verify root element
        if root.tag != 'project':
            logger.warning(f"Expected root element 'project', got '{root.tag}'")
            return None

        result = {}

        # Extract name
        name = root.find('name')
        result['name'] = name.text if name is not None and name.text else 'unknown'

        # Extract stack
        stack = root.find('stack')
        if stack is not None:
            technologies = []
            for tech in stack.findall('technology'):
                if tech.text:
                    technologies.append(tech.text)
            result['stack'] = technologies
        else:
            result['stack'] = []

        # Extract infrastructure
        infrastructure = root.find('infrastructure')
        if infrastructure is not None:
            infra_dict = {}
            for child in infrastructure:
                if child.text:
                    # Convert string boolean to bool
                    if child.text.lower() in ('true', 'false'):
                        infra_dict[child.tag] = child.text.lower() == 'true'
                    else:
                        infra_dict[child.tag] = child.text
            result['infrastructure'] = infra_dict
        else:
            result['infrastructure'] = {}

        # Extract current work
        current_work = root.find('current-work')
        if current_work is not None:
            work_dict = {}
            for child in current_work:
                if child.text:
                    # Collect multiple elements with same tag as list
                    if child.tag in work_dict:
                        if isinstance(work_dict[child.tag], list):
                            work_dict[child.tag].append(child.text)
                        else:
                            work_dict[child.tag] = [work_dict[child.tag], child.text]
                    else:
                        work_dict[child.tag] = child.text
            result['current_work'] = work_dict
        else:
            result['current_work'] = {}

        return result

    except ET.ParseError as e:
        logger.error(f"XML parsing error in parse_project_context: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in parse_project_context: {e}")
        return None


def parse_findings(xml_string: str) -> Optional[Dict[str, Any]]:
    """
    Parses findings XML using ElementTree.

    Extracts tool execution results including status, quality score,
    issues, suggestions, and follow-up agents.

    Args:
        xml_string: XML string containing findings element

    Returns:
        Dictionary with parsed fields:
            - tool: str
            - status: str (success/error)
            - quality_score: float (0.0-1.0)
            - issues: List[str]
            - suggestions: List[str]
            - followup_agents: List[str]
            - error_message: Optional[str]
        Returns None if parsing fails

    Example:
        >>> xml = '<findings><tool>Write</tool><status>success</status><quality_score>0.85</quality_score></findings>'
        >>> result = parse_findings(xml)
        >>> result['tool']
        'Write'
    """
    try:
        root = ET.fromstring(xml_string)

        # Verify root element
        if root.tag != 'findings':
            logger.warning(f"Expected root element 'findings', got '{root.tag}'")
            return None

        result = {}

        # Extract tool
        tool = root.find('tool')
        result['tool'] = tool.text if tool is not None and tool.text else 'unknown'

        # Extract status
        status = root.find('status')
        result['status'] = status.text if status is not None and status.text else 'unknown'

        # Extract quality score
        quality_score = root.find('quality_score')
        if quality_score is not None and quality_score.text:
            try:
                result['quality_score'] = float(quality_score.text)
            except ValueError:
                result['quality_score'] = 0.0
        else:
            result['quality_score'] = 0.0

        # Extract issues
        issues_elem = root.find('issues')
        issues = []
        if issues_elem is not None:
            for issue in issues_elem.findall('issue'):
                if issue.text:
                    issues.append(issue.text)
        result['issues'] = issues

        # Extract suggestions
        suggestions_elem = root.find('suggestions')
        suggestions = []
        if suggestions_elem is not None:
            for suggestion in suggestions_elem.findall('suggestion'):
                if suggestion.text:
                    suggestions.append(suggestion.text)
        result['suggestions'] = suggestions

        # Extract follow-up agents
        agents_elem = root.find('followup_agents')
        agents = []
        if agents_elem is not None:
            for agent in agents_elem.findall('agent'):
                if agent.text:
                    agents.append(agent.text)
        result['followup_agents'] = agents

        # Extract error message
        error_message = root.find('error_message')
        result['error_message'] = error_message.text if error_message is not None else None

        return result

    except ET.ParseError as e:
        logger.error(f"XML parsing error in parse_findings: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in parse_findings: {e}")
        return None


def extract_xml_from_conversation(messages: List[str],
                                  search_last_n: int = 5) -> Optional[str]:
    """
    Extracts XML content from HTML comment markers in conversation history.

    Searches for XML wrapped in HTML comments:
    <!-- XML Context (Invisible) --> ... <!-- End XML Context -->

    Args:
        messages: List of message strings to search
        search_last_n: Number of recent messages to search (default: 5)

    Returns:
        Extracted XML string, or None if not found

    Example:
        >>> messages = ["Some text", "<!-- XML Context (Invisible) --><problem-context>...</problem-context><!-- End XML Context -->"]
        >>> xml = extract_xml_from_conversation(messages)
        >>> xml is not None
        True
    """
    # Search last N messages (most recent first)
    messages_to_search = messages[-search_last_n:] if len(messages) > search_last_n else messages

    for message in reversed(messages_to_search):
        # Look for HTML comment markers
        start_marker = "<!-- XML Context (Invisible) -->"
        end_marker = "<!-- End XML Context -->"

        if start_marker in message and end_marker in message:
            start_idx = message.find(start_marker) + len(start_marker)
            end_idx = message.find(end_marker)

            if start_idx < end_idx:
                xml_content = message[start_idx:end_idx].strip()
                return xml_content

    return None


def _parse_workflow(workflow_elem: ET.Element) -> Dict[str, Any]:
    """
    Helper function to parse workflow element.

    Args:
        workflow_elem: ElementTree Element for workflow

    Returns:
        Dictionary with workflow structure
    """
    workflow = {
        'steps': []
    }

    for step in workflow_elem.findall('step'):
        step_data = {
            'id': step.get('id'),
            'action': None,
            'agent': None,
            'dependencies': []
        }

        # Extract action
        action = step.find('action')
        if action is not None and action.text:
            step_data['action'] = action.text

        # Extract agent
        agent = step.find('agent')
        if agent is not None and agent.text:
            step_data['agent'] = agent.text

        # Extract dependencies
        deps = step.find('dependencies')
        if deps is not None:
            for dep in deps.findall('dependency'):
                if dep.text:
                    step_data['dependencies'].append(dep.text)

        workflow['steps'].append(step_data)

    # Handle conditional branches (simplified parsing)
    conditionals = workflow_elem.findall('conditional')
    if conditionals:
        workflow['conditionals'] = len(conditionals)

    return workflow


# Public API
__all__ = [
    'parse_problem_context',
    'parse_project_context',
    'parse_findings',
    'extract_xml_from_conversation',
]
