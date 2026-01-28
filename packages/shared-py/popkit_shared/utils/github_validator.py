#!/usr/bin/env python3
"""
GitHub Validator - "Check First" Pattern
Validates GitHub metadata BEFORE making API calls to prevent errors.

Features:
- Label validation with suggestions
- Milestone validation
- Branch validation
- Fuzzy matching for typos

Part of the popkit plugin system - Issue #96
"""

from typing import Any, Dict, List, Optional, Tuple

# Handle both relative and absolute imports
try:
    from .github_cache import GitHubCache
except ImportError:
    from github_cache import GitHubCache

# =============================================================================
# Validation Functions
# =============================================================================


def validate_labels(
    requested_labels: List[str],
    cache: Optional[GitHubCache] = None,
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """Validate label names against repository labels.

    Implements "Check First" pattern - validates BEFORE GitHub API call.

    Args:
        requested_labels: List of label names to validate
        cache: GitHubCache instance (creates new if None)

    Returns:
        Tuple of (valid_labels, invalid_labels, suggestions)
        - valid_labels: Labels that exist in repo
        - invalid_labels: Labels that don't exist
        - suggestions: List of {invalid: str, suggestions: List[str]}
    """
    if cache is None:
        cache = GitHubCache()

    # Get cached labels
    repo_labels = cache.get_labels()
    if not repo_labels:
        # No labels available - can't validate
        return (requested_labels, [], [])

    repo_label_names = {label["name"] for label in repo_labels}

    valid = []
    invalid = []

    for label in requested_labels:
        if label in repo_label_names:
            valid.append(label)
        else:
            invalid.append(label)

    # Generate suggestions for invalid labels
    suggestions = []
    for invalid_label in invalid:
        matches = _find_similar_labels(invalid_label, repo_label_names)
        if matches:
            suggestions.append({"invalid": invalid_label, "suggestions": matches})

    return (valid, invalid, suggestions)


def validate_milestone(
    milestone_title: str,
    cache: Optional[GitHubCache] = None,
) -> Tuple[bool, Optional[int], List[str]]:
    """Validate milestone title against repository milestones.

    Implements "Check First" pattern - validates BEFORE GitHub API call.

    Args:
        milestone_title: Milestone title to validate
        cache: GitHubCache instance (creates new if None)

    Returns:
        Tuple of (exists, milestone_number, suggestions)
        - exists: True if milestone exists
        - milestone_number: Milestone number if found, None otherwise
        - suggestions: List of similar milestone titles
    """
    if cache is None:
        cache = GitHubCache()

    milestones = cache.get_milestones()
    if not milestones:
        # No milestones available - can't validate
        return (False, None, [])

    # Check for exact match
    for milestone in milestones:
        if milestone["title"] == milestone_title:
            return (True, milestone["number"], [])

    # Not found - generate suggestions
    milestone_titles = [m["title"] for m in milestones]
    suggestions = _find_similar_labels(milestone_title, milestone_titles)

    return (False, None, suggestions)


def validate_branch(
    branch_name: str,
    allow_creation: bool = True,
) -> Tuple[bool, bool, Optional[str]]:
    """Validate branch name against local git branches.

    Implements "Check First" pattern - validates BEFORE git operations.

    Args:
        branch_name: Branch name to validate
        allow_creation: If True, suggest creation for missing branches

    Returns:
        Tuple of (exists, should_create, suggestion)
        - exists: True if branch exists locally
        - should_create: True if branch doesn't exist but can be created
        - suggestion: Alternative branch name if similar match found
    """
    import subprocess

    try:
        # Get local branches
        result = subprocess.run(
            ["git", "branch", "--list", branch_name],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            if result.stdout.strip():
                return (True, False, None)

        # Branch doesn't exist - check for similar branches
        result = subprocess.run(
            ["git", "branch", "--list"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            branches = [b.strip().replace("* ", "") for b in result.stdout.splitlines()]
            suggestions = _find_similar_labels(branch_name, branches)

            if suggestions:
                return (False, allow_creation, suggestions[0])

        return (False, allow_creation, None)

    except Exception:
        # Can't validate - assume creation is OK
        return (False, allow_creation, None)


def get_label_suggestions(
    partial: str, max_suggestions: int = 5, cache: Optional[GitHubCache] = None
) -> List[str]:
    """Get label suggestions for autocomplete or user prompts.

    Args:
        partial: Partial label name
        max_suggestions: Maximum suggestions to return
        cache: GitHubCache instance (creates new if None)

    Returns:
        List of matching label names
    """
    if cache is None:
        cache = GitHubCache()

    labels = cache.get_labels()
    if not labels:
        return []

    partial_lower = partial.lower()
    matches = []

    for label in labels:
        name = label["name"]
        if partial_lower in name.lower():
            matches.append(name)

    return matches[:max_suggestions]


# =============================================================================
# Fuzzy Matching Helpers
# =============================================================================


def _find_similar_labels(target: str, options: List[str], max_suggestions: int = 3) -> List[str]:
    """Find similar labels using Levenshtein distance.

    Args:
        target: Target string to match
        options: List of available options
        max_suggestions: Maximum suggestions to return

    Returns:
        List of similar strings, sorted by similarity
    """
    if not options:
        return []

    # Calculate Levenshtein distance for all options
    distances = []
    for option in options:
        dist = _levenshtein_distance(target.lower(), option.lower())
        distances.append((dist, option))

    # Sort by distance
    distances.sort(key=lambda x: x[0])

    # Only return if reasonably close (distance < 5 or < half of target length)
    max_distance = min(5, len(target) // 2)
    return [s for d, s in distances if d <= max_distance][:max_suggestions]


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Edit distance (number of changes needed)
    """
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)

    for i, c1 in enumerate(s1):
        current_row = [i + 1]

        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)

            current_row.append(min(insertions, deletions, substitutions))

        previous_row = current_row

    return previous_row[-1]


# =============================================================================
# Validation Report Generators
# =============================================================================


def generate_label_validation_report(
    requested_labels: List[str],
    cache: Optional[GitHubCache] = None,
) -> Dict[str, Any]:
    """Generate comprehensive label validation report.

    Args:
        requested_labels: List of label names to validate
        cache: GitHubCache instance (creates new if None)

    Returns:
        Dict with:
        - valid: List of valid labels
        - invalid: List of invalid labels
        - suggestions: Dict mapping invalid -> [suggestions]
        - can_proceed: Boolean - can we proceed with valid labels only?
        - message: Human-readable message
    """
    valid, invalid, suggestions = validate_labels(requested_labels, cache=cache)

    report = {
        "valid": valid,
        "invalid": invalid,
        "suggestions": {s["invalid"]: s["suggestions"] for s in suggestions},
        "can_proceed": len(valid) > 0,
    }

    # Generate message
    if not invalid:
        report["message"] = f"✅ All {len(valid)} labels are valid"
    elif not valid:
        report["message"] = f"❌ All {len(invalid)} labels are invalid"
        if suggestions:
            report["message"] += "\n\n💡 Suggestions:\n"
            for s in suggestions:
                report["message"] += f"  - '{s['invalid']}' → {', '.join(s['suggestions'])}\n"
    else:
        report["message"] = f"⚠️  {len(valid)} valid, {len(invalid)} invalid labels"
        report["message"] += f"\n\nValid: {', '.join(valid)}"
        report["message"] += f"\nInvalid: {', '.join(invalid)}"
        if suggestions:
            report["message"] += "\n\n💡 Suggestions:\n"
            for s in suggestions:
                report["message"] += f"  - '{s['invalid']}' → {', '.join(s['suggestions'])}\n"

    return report


def generate_milestone_validation_report(
    milestone_title: str,
    cache: Optional[GitHubCache] = None,
) -> Dict[str, Any]:
    """Generate comprehensive milestone validation report.

    Args:
        milestone_title: Milestone title to validate
        cache: GitHubCache instance (creates new if None)

    Returns:
        Dict with:
        - exists: Boolean
        - milestone_number: Int or None
        - suggestions: List of similar milestones
        - can_proceed: Boolean
        - message: Human-readable message
    """
    exists, number, suggestions = validate_milestone(milestone_title, cache=cache)

    report = {
        "exists": exists,
        "milestone_number": number,
        "suggestions": suggestions,
        "can_proceed": exists,
    }

    if exists:
        report["message"] = f"✅ Milestone '{milestone_title}' exists (#{number})"
    else:
        report["message"] = f"❌ Milestone '{milestone_title}' not found"
        if suggestions:
            report["message"] += f"\n\n💡 Did you mean: {', '.join(suggestions)}?"

    return report


# =============================================================================
# CLI Test Interface
# =============================================================================


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        cmd = sys.argv[1]

        if cmd == "labels":
            requested = sys.argv[2].split(",")
            print(f"Validating labels: {requested}")
            report = generate_label_validation_report(requested)
            print("\nResults:")
            print(f"  Valid: {report['valid']}")
            print(f"  Invalid: {report['invalid']}")
            print(f"  Can proceed: {report['can_proceed']}")
            print("\nMessage:")
            print(report["message"])

        elif cmd == "milestone":
            milestone = sys.argv[2]
            print(f"Validating milestone: {milestone}")
            report = generate_milestone_validation_report(milestone)
            print("\nResults:")
            print(f"  Exists: {report['exists']}")
            print(f"  Number: {report['milestone_number']}")
            print(f"  Can proceed: {report['can_proceed']}")
            print("\nMessage:")
            print(report["message"])

        elif cmd == "branch":
            branch = sys.argv[2]
            print(f"Validating branch: {branch}")
            exists, should_create, suggestion = validate_branch(branch)
            print("\nResults:")
            print(f"  Exists: {exists}")
            print(f"  Should create: {should_create}")
            print(f"  Suggestion: {suggestion}")

        else:
            print(f"Unknown command: {cmd}")
            print("\nUsage:")
            print("  python github_validator.py labels bug,feature   # Validate labels")
            print("  python github_validator.py milestone v1.0.0     # Validate milestone")
            print("  python github_validator.py branch feature/auth  # Validate branch")
    else:
        print("GitHub Validator Test")
        print("\nUsage:")
        print("  python github_validator.py labels bug,feature   # Validate labels")
        print("  python github_validator.py milestone v1.0.0     # Validate milestone")
        print("  python github_validator.py branch feature/auth  # Validate branch")
