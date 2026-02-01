#!/usr/bin/env python3
"""
Secure Logger Utility

Provides safe logging that automatically redacts sensitive information
like API keys, tokens, passwords, and other credentials.

Usage:
    from popkit_shared.utils.secure_logger import secure_print, redact_sensitive

    # Drop-in replacement for print()
    secure_print("Token: sk-abc123xyz")  # Output: "Token: [REDACTED]"

    # Redact a string
    safe_text = redact_sensitive("API_KEY=secret123")  # "API_KEY=[REDACTED]"

Features:
- Automatically detects and redacts common sensitive patterns
- Case-insensitive pattern matching
- Custom pattern support
- Drop-in replacement for print()
- Works with environment variables, JSON, and plain text

Part of PopKit Issue #19 (Security Hardening).
"""

import re
from typing import List, Optional, Tuple

# =============================================================================
# SENSITIVE DATA PATTERNS
# =============================================================================

# Patterns for common sensitive data (compiled for performance)
_SENSITIVE_PATTERNS: List[Tuple[str, str]] = [
    # API Keys and Tokens
    (r"(bearer\s+)[\w\-\.]+", r"\1[REDACTED]"),
    (r"(api[_\-]?key\s*[=:]\s*)[\w\-]+", r"\1[REDACTED]"),
    (r"(token\s*[=:]\s*)[\w\-\.]+", r"\1[REDACTED]"),
    (r"(sk\-[\w]{20,})", r"[REDACTED]"),
    (r"(AKIA[0-9A-Z]{16})", r"[REDACTED]"),  # AWS access keys
    # Voyage AI API keys
    (r"(pa-[\w\-]{32,})", r"[REDACTED]"),
    # Upstash REST tokens
    (r"(A[a-z0-9]{20,})", r"[REDACTED]"),
    # Cloudflare tokens
    (r"([A-Za-z0-9\-_]{40})", r"[REDACTED]"),
    # Passwords
    (r"(password\s*[=:]\s*)[\w\-\.@!#$%^&*]+", r"\1[REDACTED]"),
    (r"(passwd\s*[=:]\s*)[\w\-\.@!#$%^&*]+", r"\1[REDACTED]"),
    (r"(pwd\s*[=:]\s*)[\w\-\.@!#$%^&*]+", r"\1[REDACTED]"),
    # Environment variables
    (r"(export\s+\w*KEY\s*=\s*)[\w\-\.]+", r"\1[REDACTED]"),
    (r"(export\s+\w*TOKEN\s*=\s*)[\w\-\.]+", r"\1[REDACTED]"),
    (r"(export\s+\w*SECRET\s*=\s*)[\w\-\.]+", r"\1[REDACTED]"),
    # URLs with credentials
    (r"(https?://)[^:]+:[^@]+@", r"\1[REDACTED]:[REDACTED]@"),
]

# Compile patterns for better performance
_COMPILED_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(pattern, re.IGNORECASE), replacement)
    for pattern, replacement in _SENSITIVE_PATTERNS
]


# =============================================================================
# PUBLIC API
# =============================================================================


def secure_print(
    *args, sep: str = " ", end: str = "\n", extra_patterns: Optional[List[str]] = None, **kwargs
) -> None:
    """
    Print with automatic redaction of sensitive data.

    Drop-in replacement for print() that sanitizes output.

    Args:
        *args: Values to print (same as print())
        sep: Separator between values (default: " ")
        end: End character (default: "\\n")
        extra_patterns: Additional regex patterns to redact
        **kwargs: Additional print() arguments (file, flush, etc.)

    Example:
        secure_print("Token:", os.environ.get("API_TOKEN"))
        # Output: Token: [REDACTED]
    """
    text = sep.join(str(arg) for arg in args)
    safe_text = redact_sensitive(text, extra_patterns)
    print(safe_text, end=end, **kwargs)


def redact_sensitive(
    text: str, extra_patterns: Optional[List[str]] = None, case_sensitive: bool = False
) -> str:
    """
    Redact sensitive information from text.

    Args:
        text: Text to sanitize
        extra_patterns: Additional regex patterns to redact (as strings)
        case_sensitive: Whether pattern matching is case-sensitive

    Returns:
        Sanitized text with sensitive data replaced by [REDACTED]

    Example:
        safe = redact_sensitive("API_KEY=sk-abc123")
        # Returns: "API_KEY=[REDACTED]"
    """
    if not text:
        return text

    result = text

    # Apply built-in patterns
    for pattern, replacement in _COMPILED_PATTERNS:
        result = pattern.sub(replacement, result)

    # Apply extra patterns if provided
    if extra_patterns:
        flags = 0 if case_sensitive else re.IGNORECASE
        for pattern_str in extra_patterns:
            try:
                pattern = re.compile(pattern_str, flags)
                result = pattern.sub("[REDACTED]", result)
            except re.error:
                # Skip invalid patterns
                continue

    return result


# =============================================================================
# CLI INTERFACE (for testing)
# =============================================================================

if __name__ == "__main__":
    print("Secure Logger Test")
    print("=" * 40)

    # Test cases
    test_cases = [
        "API_KEY=sk-abc123xyz",
        "Bearer abcdef1234567890",
        "token=pa-voyage-key-here",
        "password=MySecret123!",
        "export VOYAGE_API_KEY=test-key-123",
        "https://user:pass@example.com/api",
        "Normal text without secrets",
    ]

    for test in test_cases:
        print(f"\nOriginal: {test}")
        secure_print(f"Redacted: {test}")

    print("\n" + "=" * 40)
    print("All tests completed!")
