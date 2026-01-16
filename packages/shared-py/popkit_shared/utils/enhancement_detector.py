#!/usr/bin/env python3
"""
Enhancement Detector

Detects if API key is configured to enable semantic intelligence enhancements.
All features work without API key - this only detects enhancement opportunities.

Replaces the old tier-based premium_checker.py (Epic #580, Issue #581)
"""

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

POPKIT_API_URL = os.environ.get("POPKIT_API_URL", "https://api.thehouseofdeals.com")

# Cache API key validation for 5 minutes to reduce API calls
API_KEY_CACHE_TTL = 300


# =============================================================================
# TYPES
# =============================================================================


@dataclass
class EnhancementInfo:
    """Information about an enhancement opportunity."""

    name: str
    description: str
    current_mode: str
    enhanced_mode: str
    benefit: str


@dataclass
class EnhancementResult:
    """Result of an enhancement check."""

    has_api_key: bool
    enhancement_name: str
    current_mode: str
    enhanced_mode: str
    message: Optional[str] = None


# =============================================================================
# ENHANCEMENT REGISTRY
# =============================================================================

# Registry of enhancement opportunities (not feature gates!)
ENHANCEMENTS: Dict[str, EnhancementInfo] = {
    # Agent Routing Enhancement
    "agent-routing": EnhancementInfo(
        name="Semantic Agent Routing",
        description="Smarter agent selection via embeddings",
        current_mode="Keyword-based matching",
        enhanced_mode="Embedding-based similarity search",
        benefit="More accurate agent selection for complex queries",
    ),
    # Pattern Learning Enhancement
    "pattern-learning": EnhancementInfo(
        name="Community Pattern Learning",
        description="Shared knowledge across projects",
        current_mode="Local pattern storage",
        enhanced_mode="Cloud-backed shared knowledge",
        benefit="Learn from community patterns and discoveries",
    ),
    # Knowledge Base Enhancement
    "knowledge-base": EnhancementInfo(
        name="Cloud Knowledge Base",
        description="Semantic search across projects",
        current_mode="File-based knowledge storage",
        enhanced_mode="Vector DB with semantic search",
        benefit="Cross-project insights and faster discovery",
    ),
    # Project Embeddings Enhancement
    "project-embeddings": EnhancementInfo(
        name="Project Embeddings",
        description="Semantic understanding of codebase",
        current_mode="Text-based search",
        enhanced_mode="Embedding-based semantic search",
        benefit="Find relevant code by meaning, not just keywords",
    ),
    # Power Mode Enhancement
    "power-mode": EnhancementInfo(
        name="Power Mode Coordination",
        description="Multi-agent orchestration",
        current_mode="File-based coordination (2-3 agents)",
        enhanced_mode="Cloud coordination (10+ agents)",
        benefit="Parallel agent execution with shared state",
    ),
}


# =============================================================================
# API KEY VALIDATION CACHE
# =============================================================================

_api_key_cache: Dict[str, tuple[bool, float]] = {}


def _get_cached_api_key_status(api_key: str) -> Optional[bool]:
    """Get cached API key status if still valid."""
    import time

    if api_key in _api_key_cache:
        is_valid, cached_at = _api_key_cache[api_key]
        if time.time() - cached_at < API_KEY_CACHE_TTL:
            return is_valid
    return None


def _cache_api_key_status(api_key: str, is_valid: bool) -> None:
    """Cache API key validation result."""
    import time

    _api_key_cache[api_key] = (is_valid, time.time())


# =============================================================================
# CORE FUNCTIONS
# =============================================================================


def has_api_key(api_key: Optional[str] = None) -> bool:
    """
    Check if user has a valid API key configured.

    Args:
        api_key: PopKit API key (or from POPKIT_API_KEY env)

    Returns:
        True if API key is configured and valid
    """
    key = api_key or os.environ.get("POPKIT_API_KEY")

    if not key:
        return False

    # Check cache first
    cached = _get_cached_api_key_status(key)
    if cached is not None:
        return cached

    # Validate with API
    # Security: Catch all exceptions to prevent API key leakage in logs
    try:
        url = f"{POPKIT_API_URL}/v1/health"
        request = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        )

        with urllib.request.urlopen(request, timeout=5) as response:
            is_valid = response.status == 200
            _cache_api_key_status(key, is_valid)
            return is_valid

    except Exception:
        # Security: Don't log exception details (could contain API key)
        _cache_api_key_status(key, False)
        return False


def get_enhancement_info(enhancement_name: str) -> Optional[EnhancementInfo]:
    """
    Get information about an enhancement.

    Args:
        enhancement_name: Name of the enhancement

    Returns:
        EnhancementInfo or None
    """
    return ENHANCEMENTS.get(enhancement_name)


def check_enhancement(enhancement_name: str, api_key: Optional[str] = None) -> EnhancementResult:
    """
    Check if an enhancement is available.

    This does NOT gate features - all features work without API key.
    This is purely informational.

    Args:
        enhancement_name: Name of the enhancement to check
        api_key: PopKit API key (or from POPKIT_API_KEY env)

    Returns:
        EnhancementResult with API key status and enhancement info
    """
    has_key = has_api_key(api_key)
    enhancement = ENHANCEMENTS.get(enhancement_name)

    if not enhancement:
        return EnhancementResult(
            has_api_key=has_key,
            enhancement_name=enhancement_name,
            current_mode="Standard mode",
            enhanced_mode="Enhanced mode",
            message=None,
        )

    return EnhancementResult(
        has_api_key=has_key,
        enhancement_name=enhancement.name,
        current_mode=enhancement.current_mode,
        enhanced_mode=enhancement.enhanced_mode,
        message=None if has_key else _get_enhancement_message(enhancement),
    )


def _get_enhancement_message(enhancement: EnhancementInfo) -> str:
    """Generate informational message about an enhancement."""
    msg = f"""
💡 Enhancement Available: {enhancement.name}

{enhancement.description}

**Currently using:** {enhancement.current_mode} (fully functional)
**With API key:** {enhancement.enhanced_mode}
**Benefit:** {enhancement.benefit}

Get a free API key: /popkit:cloud signup

**Cost:** Free for now, usage-based pricing coming soon
**Important:** All features work without API key - it just adds semantic intelligence.
"""
    return msg.strip()


def get_enhancement_prompt_options(enhancement_name: str) -> Dict[str, Any]:
    """
    Get AskUserQuestion options for an enhancement prompt.

    Args:
        enhancement_name: Name of the enhancement

    Returns:
        Dict with question, header, options for AskUserQuestion
    """
    enhancement = ENHANCEMENTS.get(enhancement_name)

    if not enhancement:
        return {}

    return {
        "question": "Would you like to get an API key for enhanced intelligence?",
        "header": "Enhancement",
        "options": [
            {
                "label": "Get free API key",
                "description": f"Enable {enhancement.name} (free for now)",
            },
            {
                "label": "Continue without enhancements",
                "description": f"Keep using {enhancement.current_mode} (fully functional)",
            },
            {"label": "Learn more", "description": "Show details about enhancements"},
        ],
        "multiSelect": False,
    }


def list_enhancements() -> List[EnhancementInfo]:
    """
    List all available enhancements.

    Returns:
        List of all enhancements
    """
    return list(ENHANCEMENTS.values())


# =============================================================================
# USAGE TRACKING (Optional - for analytics)
# =============================================================================


@dataclass
class UsageEvent:
    """A tracked usage event for analytics."""

    enhancement: str
    has_api_key: bool
    timestamp: str
    project_id: str
    success: bool


def _get_project_id() -> str:
    """Generate a privacy-respecting project identifier (hash of path)."""
    import hashlib

    cwd = os.getcwd()
    return hashlib.sha256(cwd.encode()).hexdigest()[:16]


def track_enhancement_usage(
    enhancement_name: str, success: bool = True, api_key: Optional[str] = None
) -> bool:
    """
    Track usage of an enhancement (for analytics only).

    Args:
        enhancement_name: Name of the enhancement used
        success: Whether the operation succeeded
        api_key: PopKit API key (or from POPKIT_API_KEY env)

    Returns:
        True if tracking was successful
    """
    from datetime import datetime

    key = api_key or os.environ.get("POPKIT_API_KEY")
    has_key = has_api_key(key)

    event = UsageEvent(
        enhancement=enhancement_name,
        has_api_key=has_key,
        timestamp=datetime.utcnow().isoformat() + "Z",
        project_id=_get_project_id(),
        success=success,
    )

    # Only track if API key is configured
    if not key:
        return False

    # Security: Catch all exceptions to prevent API key leakage in logs
    try:
        url = f"{POPKIT_API_URL}/v1/usage/track"
        data = json.dumps(
            {
                "enhancement": event.enhancement,
                "has_api_key": event.has_api_key,
                "timestamp": event.timestamp,
                "project_id": event.project_id,
                "success": event.success,
            }
        ).encode()

        request = urllib.request.Request(
            url,
            data=data,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status == 200

    except Exception:
        # Security: Don't log exception details (could contain API key)
        return False  # Don't fail if tracking fails


def get_usage_summary(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get usage summary for the current user.

    Args:
        api_key: PopKit API key (or from POPKIT_API_KEY env)

    Returns:
        Dict with usage statistics
    """
    key = api_key or os.environ.get("POPKIT_API_KEY")
    if not key:
        return {"error": "No API key configured"}

    # Security: Catch all exceptions to prevent API key leakage in logs
    try:
        url = f"{POPKIT_API_URL}/v1/usage/summary"
        request = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        )

        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode())

    except Exception:
        # Security: Don't log exception details (could contain API key)
        return {"error": "Failed to fetch usage summary"}


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: enhancement_detector.py <command> [args]")
        print("Commands: check <enhancement>, list, has-key, usage, track <enhancement>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "check":
        enhancement = sys.argv[2] if len(sys.argv) > 2 else "agent-routing"
        result = check_enhancement(enhancement)
        print(f"Enhancement: {result.enhancement_name}")
        print(f"Has API key: {result.has_api_key}")
        print(f"Current mode: {result.current_mode}")
        print(f"Enhanced mode: {result.enhanced_mode}")
        if result.message:
            print(f"\n{result.message}")

    elif command == "list":
        print("Available Enhancements:")
        for enhancement in list_enhancements():
            print(f"  • {enhancement.name}")
            print(f"    Current: {enhancement.current_mode}")
            print(f"    Enhanced: {enhancement.enhanced_mode}")
            print()

    elif command == "has-key":
        has_key = has_api_key()
        print(f"API key configured: {'Yes ✅' if has_key else 'No ❌'}")
        if not has_key:
            print("\nGet a free API key: /popkit:cloud signup")

    elif command == "usage":
        summary = get_usage_summary()
        if "error" in summary:
            print(f"Error: {summary['error']}")
        else:
            print("Usage Summary:")
            print(json.dumps(summary, indent=2))

    elif command == "track":
        enhancement = sys.argv[2] if len(sys.argv) > 2 else "agent-routing"
        success = track_enhancement_usage(enhancement)
        print(f"Tracked {enhancement}: {'success' if success else 'failed'}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
