#!/usr/bin/env python3
"""
Helper functions for session-start.py hook

Extracted for testability and maintainability.
"""

import sys
from typing import Dict, Optional, Any


def detect_agent_type_session(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Detect and optimize session for agent_type from --agent flag.

    New in Claude Code 2.1.2: SessionStart hook input includes 'agent_type'
    when the user runs Claude Code with the --agent flag.

    Example: `claude --agent code-reviewer` will set agent_type='code-reviewer'

    This allows PopKit to:
    1. Skip embedding-based agent filtering (agent already selected)
    2. Pre-load agent-specific configurations
    3. Set appropriate defaults for the agent context
    4. Improve logging and analytics

    Args:
        data: Session input data from Claude Code

    Returns:
        dict: Agent type optimization info, or None if no agent_type specified
    """
    agent_type = data.get("agent_type")

    if not agent_type:
        return None  # No --agent flag used, normal session

    try:
        # Log agent-specific session start
        print(f"Agent-specific session detected: {agent_type}", file=sys.stderr)

        # Map known agent types to PopKit agent categories
        # This helps optimize context loading and Power Mode configuration
        agent_category_map = {
            # Tier 1 agents (always active)
            "code-reviewer": "tier-1",
            "refactoring-expert": "tier-1",
            "accessibility-guardian": "tier-1",
            "api-designer": "tier-1",
            "documentation-maintainer": "tier-1",
            "migration-specialist": "tier-1",
            "bug-whisperer": "tier-1",
            "performance-optimizer": "tier-1",
            "security-auditor": "tier-1",
            "test-writer-fixer": "tier-1",
            # Tier 2 agents (on-demand)
            "bundle-analyzer": "tier-2",
            "dead-code-eliminator": "tier-2",
            "feature-prioritizer": "tier-2",
            "meta-agent": "tier-2",
            "power-coordinator": "tier-2",
            "rapid-prototyper": "tier-2",
            "deployment-validator": "tier-2",
            "rollback-specialist": "tier-2",
            "researcher": "tier-2",
            "merge-conflict-resolver": "tier-2",
            "prd-parser": "tier-2",
            # Feature workflow agents
            "code-explorer": "feature-workflow",
            "code-architect": "feature-workflow",
        }

        category = agent_category_map.get(agent_type, "unknown")

        # Determine optimization strategy
        optimization = {
            "agent_type": agent_type,
            "agent_category": category,
            "skip_embedding_filter": True,  # Agent already selected by user
            "optimizations_applied": [],
        }

        # Category-specific optimizations
        if category == "tier-1":
            optimization["optimizations_applied"].append("standard_context_loading")
            print("  Category: Tier 1 (always active)", file=sys.stderr)
        elif category == "tier-2":
            optimization["optimizations_applied"].append("on_demand_context_loading")
            print("  Category: Tier 2 (on-demand specialist)", file=sys.stderr)
        elif category == "feature-workflow":
            optimization["optimizations_applied"].append("feature_workflow_context")
            print("  Category: Feature workflow agent", file=sys.stderr)
        else:
            # Unknown agent type - might be custom or from another plugin
            optimization["optimizations_applied"].append("generic_optimization")
            print("  Category: External/custom agent", file=sys.stderr)

        return optimization

    except Exception as e:
        # Silent failure - don't block session start
        print(f"Warning: Agent type detection failed: {e}", file=sys.stderr)
        return None
