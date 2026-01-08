#!/usr/bin/env python3
"""
Conventional Commit Message Validator

Validates commit messages follow the conventional commit format:
  type(scope): description

Part of PopKit plugin - Quick Win from Issue #27 (Auto Claude Competitive Features)

Usage:
    python validate_commit.py "feat: add new feature"
    python validate_commit.py "fix(api): correct rate limit"
    echo "feat: add feature" | python validate_commit.py
"""

import re
import sys


# Valid conventional commit types
VALID_TYPES = {
    "feat",      # New feature
    "fix",       # Bug fix
    "docs",      # Documentation only
    "style",     # Formatting, no code change
    "refactor",  # Code refactoring
    "perf",      # Performance improvement
    "test",      # Test additions/updates
    "build",     # Build system changes
    "ci",        # CI/CD changes
    "chore",     # Maintenance tasks
    "revert"     # Revert previous commit
}


def validate_commit_message(message: str, strict: bool = False) -> tuple[bool, str]:
    """
    Validate a commit message follows conventional commit format.

    Args:
        message: Commit message to validate
        strict: If True, enforce strict validation (scope required, etc.)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not message or not message.strip():
        return False, "Commit message is empty"

    # Get first line (subject)
    subject = message.split("\n")[0].strip()

    # Pattern: type(scope): description
    # Scope is optional unless strict=True
    if strict:
        pattern = r'^(\w+)\(([^)]+)\):\s+(.{1,72})$'
    else:
        pattern = r'^(\w+)(?:\(([^)]*)\))?:\s+(.{1,72})$'

    match = re.match(pattern, subject)

    if not match:
        # Check common mistakes
        if ":" not in subject:
            return False, "Missing colon (:) after type. Format: type(scope): description"

        if not subject[0].islower():
            return False, "Type must be lowercase. Example: feat(api): add endpoint"

        # Check if description is too long
        if len(subject) > 100:
            return False, "Subject line is too long (max 100 characters)"

        return False, "Invalid format. Expected: type(scope): description"

    commit_type = match.group(1).lower()
    scope = match.group(2) if match.group(2) else None
    description = match.group(3)

    # Validate type
    if commit_type not in VALID_TYPES:
        valid_types_str = ", ".join(sorted(VALID_TYPES))
        return False, f"Invalid type '{commit_type}'. Valid types: {valid_types_str}"

    # Validate description
    if not description or len(description.strip()) < 3:
        return False, "Description is too short (minimum 3 characters)"

    if description[0].isupper():
        return False, "Description should start with lowercase letter"

    if description.endswith("."):
        return False, "Description should not end with a period"

    # In strict mode, scope is required
    if strict and not scope:
        return False, "Scope is required in strict mode. Example: feat(api): add endpoint"

    # All checks passed
    return True, ""


def main():
    """CLI entry point."""
    import argparse
    import io

    # Handle Windows encoding for emoji output
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description="Validate conventional commit messages")
    parser.add_argument("message", nargs="?", help="Commit message to validate (or read from stdin)")
    parser.add_argument("--strict", "-s", action="store_true", help="Enforce strict validation")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output (exit code only)")
    args = parser.parse_args()

    # Get message from args or stdin
    if args.message:
        message = args.message
    else:
        # Read from stdin
        message = sys.stdin.read().strip()

    # Validate
    is_valid, error = validate_commit_message(message, strict=args.strict)

    if not args.quiet:
        if is_valid:
            print("✅ Valid conventional commit message")
        else:
            print(f"❌ Invalid commit message: {error}")
            print()
            print("Expected format:")
            print("  type(scope): description")
            print()
            print("Examples:")
            print("  feat: add user authentication")
            print("  fix(api): correct rate limit calculation")
            print("  docs: update README with installation steps")
            print()
            print(f"Valid types: {', '.join(sorted(VALID_TYPES))}")

    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
