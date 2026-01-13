"""
Agent routing test utilities for PopKit plugin testing.

Tests agent activation logic based on keywords, file patterns, and error patterns.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set


def test_keyword_routing(
    config_path: Path, user_query: str, expected_agents: List[str]
) -> Dict[str, Any]:
    """
    Test keyword-based agent routing.

    Args:
        config_path: Path to agents/config.json
        user_query: User query string
        expected_agents: List of agent names expected to be activated

    Returns:
        Test result with activated agents
    """
    result = {
        "valid": False,
        "activated_agents": [],
        "expected_agents": expected_agents,
        "matched": False,
        "missing": [],
        "unexpected": [],
    }

    if not config_path.exists():
        result["error"] = f"Config file not found: {config_path}"
        return result

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError as e:
        result["error"] = f"Invalid JSON in config: {e}"
        return result

    # Extract routing configuration
    routing = config.get("routing", {})
    keywords_map = routing.get("keywords", {})

    # Normalize query for matching
    query_lower = user_query.lower()
    query_words = set(re.findall(r"\w+", query_lower))

    # Find matching agents
    activated = set()

    for agent_name, agent_keywords in keywords_map.items():
        if not isinstance(agent_keywords, list):
            agent_keywords = [agent_keywords]

        for keyword in agent_keywords:
            keyword_lower = keyword.lower()

            # Check if keyword appears in query
            if keyword_lower in query_lower or keyword_lower in query_words:
                activated.add(agent_name)
                break

    result["activated_agents"] = sorted(list(activated))

    # Compare with expected
    expected_set = set(expected_agents)
    activated_set = set(result["activated_agents"])

    result["matched"] = expected_set == activated_set
    result["missing"] = sorted(list(expected_set - activated_set))
    result["unexpected"] = sorted(list(activated_set - expected_set))
    result["valid"] = result["matched"]

    return result


def test_file_pattern_routing(
    config_path: Path, file_path: str, expected_agents: List[str]
) -> Dict[str, Any]:
    """
    Test file pattern-based agent routing.

    Args:
        config_path: Path to agents/config.json
        file_path: File path to match against patterns
        expected_agents: Expected agents to be activated

    Returns:
        Test result
    """
    result = {
        "valid": False,
        "activated_agents": [],
        "expected_agents": expected_agents,
        "matched": False,
    }

    if not config_path.exists():
        result["error"] = f"Config file not found: {config_path}"
        return result

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError as e:
        result["error"] = f"Invalid JSON in config: {e}"
        return result

    # Extract file pattern routing
    routing = config.get("routing", {})
    file_patterns = routing.get("file_patterns", {})

    # Find matching agents
    activated = set()

    for agent_name, patterns in file_patterns.items():
        if not isinstance(patterns, list):
            patterns = [patterns]

        for pattern in patterns:
            # Convert glob pattern to regex
            pattern_regex = pattern.replace(".", r"\.").replace("*", ".*")

            if re.search(pattern_regex, file_path):
                activated.add(agent_name)
                break

    result["activated_agents"] = sorted(list(activated))
    result["matched"] = set(result["activated_agents"]) == set(expected_agents)
    result["valid"] = result["matched"]

    return result


def test_confidence_threshold(config_path: Path, min_confidence: float = 0.8) -> Dict[str, Any]:
    """
    Test confidence threshold configuration.

    Args:
        config_path: Path to agents/config.json
        min_confidence: Minimum expected confidence threshold

    Returns:
        Test result
    """
    result = {"valid": False, "agents_checked": 0, "below_threshold": [], "errors": []}

    if not config_path.exists():
        result["errors"].append(f"Config file not found: {config_path}")
        return result

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError as e:
        result["errors"].append(f"Invalid JSON in config: {e}")
        return result

    # Check confidence thresholds
    routing = config.get("routing", {})
    confidence_thresholds = routing.get("confidence_thresholds", {})

    for agent_name, threshold in confidence_thresholds.items():
        result["agents_checked"] += 1

        if threshold < min_confidence:
            result["below_threshold"].append(
                {"agent": agent_name, "threshold": threshold, "min_required": min_confidence}
            )

    result["valid"] = len(result["below_threshold"]) == 0

    return result


def test_tier_assignment(config_path: Path) -> Dict[str, Any]:
    """
    Test agent tier assignment (Tier 1 always active, Tier 2 on-demand).

    Args:
        config_path: Path to agents/config.json

    Returns:
        Test result with tier statistics
    """
    result = {
        "valid": False,
        "tier_1_count": 0,
        "tier_2_count": 0,
        "tier_1_agents": [],
        "tier_2_agents": [],
        "unassigned": [],
        "errors": [],
    }

    if not config_path.exists():
        result["errors"].append(f"Config file not found: {config_path}")
        return result

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError as e:
        result["errors"].append(f"Invalid JSON in config: {e}")
        return result

    # Check tier assignments
    agents = config.get("agents", {})

    for agent_name, agent_config in agents.items():
        tier = agent_config.get("tier")

        if tier == 1:
            result["tier_1_count"] += 1
            result["tier_1_agents"].append(agent_name)
        elif tier == 2:
            result["tier_2_count"] += 1
            result["tier_2_agents"].append(agent_name)
        else:
            result["unassigned"].append(agent_name)

    # Valid if all agents are assigned to a tier
    result["valid"] = len(result["unassigned"]) == 0

    return result


def test_agent_definitions_exist(config_path: Path, agents_dir: Path) -> Dict[str, Any]:
    """
    Test that all registered agents have corresponding definition files.

    Args:
        config_path: Path to agents/config.json
        agents_dir: Path to agents directory

    Returns:
        Test result
    """
    result = {
        "valid": False,
        "agents_registered": 0,
        "agents_found": 0,
        "missing_definitions": [],
        "orphaned_definitions": [],
        "errors": [],
    }

    if not config_path.exists():
        result["errors"].append(f"Config file not found: {config_path}")
        return result

    if not agents_dir.exists():
        result["errors"].append(f"Agents directory not found: {agents_dir}")
        return result

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError as e:
        result["errors"].append(f"Invalid JSON in config: {e}")
        return result

    # Get registered agents
    agents = config.get("agents", {})
    registered_agents = set(agents.keys())
    result["agents_registered"] = len(registered_agents)

    # Find agent definition files
    agent_files = set()
    for agent_file in agents_dir.rglob("*.md"):
        agent_name = agent_file.stem
        agent_files.add(agent_name)

    result["agents_found"] = len(agent_files)

    # Check for missing and orphaned
    result["missing_definitions"] = sorted(list(registered_agents - agent_files))
    result["orphaned_definitions"] = sorted(list(agent_files - registered_agents))

    result["valid"] = len(result["missing_definitions"]) == 0

    return result


def get_routing_statistics(config_path: Path) -> Dict[str, Any]:
    """
    Get comprehensive routing statistics from config.

    Args:
        config_path: Path to agents/config.json

    Returns:
        Statistics dictionary
    """
    stats = {
        "total_agents": 0,
        "tier_1_agents": 0,
        "tier_2_agents": 0,
        "agents_with_keywords": 0,
        "agents_with_file_patterns": 0,
        "agents_with_error_patterns": 0,
        "total_keywords": 0,
        "total_file_patterns": 0,
        "total_error_patterns": 0,
    }

    if not config_path.exists():
        return stats

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError:
        return stats

    # Agent counts
    agents = config.get("agents", {})
    stats["total_agents"] = len(agents)

    for agent_config in agents.values():
        tier = agent_config.get("tier")
        if tier == 1:
            stats["tier_1_agents"] += 1
        elif tier == 2:
            stats["tier_2_agents"] += 1

    # Routing counts
    routing = config.get("routing", {})

    keywords_map = routing.get("keywords", {})
    stats["agents_with_keywords"] = len(keywords_map)
    stats["total_keywords"] = sum(
        len(kw) if isinstance(kw, list) else 1 for kw in keywords_map.values()
    )

    file_patterns = routing.get("file_patterns", {})
    stats["agents_with_file_patterns"] = len(file_patterns)
    stats["total_file_patterns"] = sum(
        len(fp) if isinstance(fp, list) else 1 for fp in file_patterns.values()
    )

    error_patterns = routing.get("error_patterns", {})
    stats["agents_with_error_patterns"] = len(error_patterns)
    stats["total_error_patterns"] = sum(
        len(ep) if isinstance(ep, list) else 1 for ep in error_patterns.values()
    )

    return stats
