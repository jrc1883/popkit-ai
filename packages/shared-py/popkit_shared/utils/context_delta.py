#!/usr/bin/env python3
"""
Context Delta Computation

Computes context deltas between messages to minimize context window usage.
Detects added/changed/removed fields and extracts new context from user messages.

Used by: user-prompt-submit.py hook
"""

import re
from typing import Dict, Any, Optional

# Import compute_hash from context_state
try:
    from .context_state import compute_hash
except ImportError:
    from context_state import compute_hash


def compute_context_delta(
    previous: Dict[str, Any], current: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Compute what changed between previous and current context.

    Analyzes each top-level field and detects:
    - added: New fields that didn't exist before
    - changed: Fields with different content (via hash comparison)
    - removed: Fields that existed before but don't now

    Args:
        previous: Previous context dict
        current: Current context dict

    Returns:
        Delta dict with structure:
        {
            "field_name": {
                "type": "added"|"changed"|"removed",
                "value": <field value> (not included for removed)
            },
            ...
        }

    Example:
        >>> prev = {"project": {"name": "old"}}
        >>> curr = {"project": {"name": "new"}, "infrastructure": {"redis": True}}
        >>> delta = compute_context_delta(prev, curr)
        >>> delta["project"]["type"]
        'changed'
        >>> delta["infrastructure"]["type"]
        'added'
    """
    delta = {}

    # Check each field in current context
    for key in current:
        if key not in previous:
            # New field
            delta[key] = {"type": "added", "value": current[key]}
        elif compute_hash(current[key]) != compute_hash(previous.get(key, {})):
            # Changed field (hash differs)
            delta[key] = {"type": "changed", "value": current[key]}
        # Unchanged fields are omitted from delta

    # Check for removed fields
    for key in previous:
        if key not in current:
            delta[key] = {
                "type": "removed"
                # No value included for removed fields
            }

    return delta


def extract_new_context(
    message: str, existing_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract new context information from user message.

    Detects mentions of:
    - Infrastructure (redis, postgres, mongodb, etc.)
    - Issue references (#123)
    - Branch mentions (feat/branch-name)
    - Technology stack (Next.js, React, etc.)

    Args:
        message: User message text
        existing_context: Optional existing context to check against

    Returns:
        Dict with newly discovered context

    Example:
        >>> ctx = extract_new_context("Use Redis for caching", {})
        >>> "infrastructure" in ctx
        True
        >>> ctx["infrastructure"]["redis"]
        {'discovered': True}
    """
    if existing_context is None:
        existing_context = {}

    new_context = {}
    message_lower = message.lower()

    # Extract infrastructure mentions
    infrastructure_keywords = {
        "redis": ["redis"],
        "postgres": ["postgres", "postgresql"],
        "mongodb": ["mongodb", "mongo"],
        "mysql": ["mysql"],
        "elasticsearch": ["elasticsearch", "elastic"],
        "rabbitmq": ["rabbitmq", "rabbit"],
        "kafka": ["kafka"],
        "docker": ["docker"],
        "kubernetes": ["kubernetes", "k8s"],
    }

    existing_infra = existing_context.get("infrastructure", {})

    for infra_name, keywords in infrastructure_keywords.items():
        # Check if mentioned in message and not already in context
        if any(kw in message_lower for kw in keywords):
            if infra_name not in existing_infra:
                if "infrastructure" not in new_context:
                    new_context["infrastructure"] = {}
                new_context["infrastructure"][infra_name] = {"discovered": True}

    # Extract issue references (#123)
    issue_refs = re.findall(r"#(\d+)", message)
    if issue_refs:
        # Convert to list of strings
        issues = [f"#{num}" for num in issue_refs]

        # Only add if not already in context
        existing_issues = existing_context.get("issues", [])
        new_issues = [issue for issue in issues if issue not in existing_issues]

        if new_issues:
            new_context["issues"] = new_issues

    # Extract branch mentions (feat/branch-name, fix/branch-name, etc.)
    branch_pattern = r"(?:branch|on|in)\s+([a-z-]+/[a-z0-9-]+)"
    branch_match = re.search(branch_pattern, message_lower)

    if branch_match:
        branch_name = branch_match.group(1)

        # Only add if different from existing branch
        existing_branch = existing_context.get("branch")
        if branch_name != existing_branch:
            new_context["branch"] = branch_name

    # Extract technology stack mentions
    tech_keywords = {
        "Next.js": ["next.js", "nextjs"],
        "React": ["react"],
        "Vue": ["vue.js", "vue"],
        "Angular": ["angular"],
        "Node.js": ["node.js", "nodejs", "node"],
        "Python": ["python"],
        "FastAPI": ["fastapi"],
        "Django": ["django"],
        "Flask": ["flask"],
        "Express": ["express.js", "express"],
        "Supabase": ["supabase"],
        "Firebase": ["firebase"],
        "Cloudflare": ["cloudflare"],
    }

    existing_stack = existing_context.get("stack", [])

    for tech_name, keywords in tech_keywords.items():
        if any(kw in message_lower for kw in keywords):
            if tech_name not in existing_stack:
                if "stack" not in new_context:
                    new_context["stack"] = []
                if tech_name not in new_context["stack"]:
                    new_context["stack"].append(tech_name)

    return new_context


def should_send_full_context(message_number: int, last_full_context_message: int) -> bool:
    """
    Determine if we should send full context (vs delta).

    Full context is sent:
    - On first message (message_number == 1)
    - Every 20 messages (periodic refresh)

    Args:
        message_number: Current message number (1-indexed)
        last_full_context_message: Message number when full context was last sent

    Returns:
        True if should send full context, False for delta

    Example:
        >>> should_send_full_context(1, 0)
        True
        >>> should_send_full_context(2, 1)
        False
        >>> should_send_full_context(21, 1)
        True
        >>> should_send_full_context(22, 21)
        False
    """
    # First message always gets full context
    if message_number == 1:
        return True

    # Periodic refresh every 20 messages
    if message_number - last_full_context_message >= 20:
        return True

    return False


# Public API
__all__ = [
    "compute_context_delta",
    "extract_new_context",
    "should_send_full_context",
]
