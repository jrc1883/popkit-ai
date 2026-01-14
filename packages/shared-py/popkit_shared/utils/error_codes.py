#!/usr/bin/env python3
"""
PopKit Error Code System

Provides standardized error codes, messages, and recovery suggestions.

This module implements Issue #104 to provide consistent error handling across
all PopKit hooks with clear error codes, contextual information, and actionable
recovery suggestions.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


class ErrorSeverity(Enum):
    """Error severity levels."""

    CRITICAL = "critical"  # Blocks execution
    HIGH = "high"  # Blocks but may have workaround
    MEDIUM = "medium"  # Warning, doesn't block
    LOW = "low"  # Informational
    INFO = "info"  # Just information


@dataclass
class ErrorCode:
    """Represents a standard error code."""

    code: str  # E001_JSON_PARSE
    category: str  # "JSON/Input Parsing"
    message: str  # Human-readable description
    severity: ErrorSeverity
    help_doc: str  # Relative path to docs/errors/E001.md
    recovery: List[str]  # Recovery suggestions


class ErrorRegistry:
    """Central registry of all PopKit error codes."""

    # JSON/Input Errors (001-099)
    E001_JSON_PARSE = ErrorCode(
        code="E001_JSON_PARSE",
        category="JSON/Input Parsing",
        message="Invalid JSON syntax in input",
        severity=ErrorSeverity.CRITICAL,
        help_doc="errors/E001_JSON_PARSE.md",
        recovery=[
            "Validate JSON with 'jq' or online validator",
            "Check for trailing commas (not allowed in JSON)",
            "Ensure proper escaping of quotes and backslashes",
        ],
    )

    E002_INVALID_SCHEMA = ErrorCode(
        code="E002_INVALID_SCHEMA",
        category="JSON/Input Parsing",
        message="JSON structure doesn't match expected schema",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E002_INVALID_SCHEMA.md",
        recovery=[
            "Check required fields are present",
            "Verify field types match schema",
            "See schema documentation in CLAUDE.md",
        ],
    )

    # File I/O Errors (100-199)
    E101_FILE_NOT_FOUND = ErrorCode(
        code="E101_FILE_NOT_FOUND",
        category="File I/O",
        message="Required file not found",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E101_FILE_NOT_FOUND.md",
        recovery=[
            "Check file path is correct",
            "Verify file exists with 'ls' or 'find'",
            "Ensure proper working directory",
        ],
    )

    E102_PERMISSION_DENIED = ErrorCode(
        code="E102_PERMISSION_DENIED",
        category="File I/O",
        message="Permission denied accessing file or directory",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E102_PERMISSION_DENIED.md",
        recovery=[
            "Check file permissions with 'ls -la'",
            "Ensure you have read/write access",
            "Run with appropriate user permissions",
        ],
    )

    # Network/API Warnings (200-299)
    W201_NETWORK_TIMEOUT = ErrorCode(
        code="W201_NETWORK_TIMEOUT",
        category="Network/API",
        message="Network request timed out",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/W201_NETWORK_TIMEOUT.md",
        recovery=[
            "Check internet connection",
            "Retry with increased timeout",
            "Feature will continue without this data (graceful degradation)",
        ],
    )

    # Git Operations (300-399)
    E301_REPO_NOT_FOUND = ErrorCode(
        code="E301_REPO_NOT_FOUND",
        category="Git Operations",
        message="Git repository not found",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E301_REPO_NOT_FOUND.md",
        recovery=[
            "Verify you're in a git repository with 'git status'",
            "Initialize repository with 'git init' if needed",
            "Check working directory is correct",
        ],
    )

    # Safety/Security (400-499)
    S401_DESTRUCTIVE_CMD = ErrorCode(
        code="S401_DESTRUCTIVE_CMD",
        category="Safety/Security",
        message="Potentially destructive command blocked",
        severity=ErrorSeverity.CRITICAL,
        help_doc="errors/S401_DESTRUCTIVE_CMD.md",
        recovery=[
            "Review command for unintended consequences",
            "Use safer alternative if available",
            "Explicitly approve if command is intentional",
        ],
    )

    # Tool Execution (600-699)
    E601_TOOL_FAILED = ErrorCode(
        code="E601_TOOL_FAILED",
        category="Tool Execution",
        message="Tool execution failed",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E601_TOOL_FAILED.md",
        recovery=[
            "Check tool output for specific error messages",
            "Verify tool is installed and accessible",
            "Review tool arguments for correctness",
        ],
    )

    # Configuration (700-799)
    E701_INVALID_CONFIG = ErrorCode(
        code="E701_INVALID_CONFIG",
        category="Configuration",
        message="Invalid configuration",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E701_INVALID_CONFIG.md",
        recovery=[
            "Check configuration file syntax",
            "Verify all required fields are present",
            "See configuration documentation",
        ],
    )

    W702_MISSING_FIELD = ErrorCode(
        code="W702_MISSING_FIELD",
        category="Configuration",
        message="Optional configuration field missing",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/W702_MISSING_FIELD.md",
        recovery=[
            "Add missing field to configuration",
            "Feature will use default value (graceful degradation)",
            "See configuration documentation for field details",
        ],
    )

    @classmethod
    def get_error(cls, code: str) -> Optional[ErrorCode]:
        """
        Get error by code string.

        Args:
            code: Error code string (e.g., 'E001_JSON_PARSE')

        Returns:
            ErrorCode if found, None otherwise

        Example:
            >>> error = ErrorRegistry.get_error('E001_JSON_PARSE')
            >>> print(error.message)
            Invalid JSON syntax in input
        """
        return getattr(cls, code.upper(), None)

    @classmethod
    def all_errors(cls) -> List[ErrorCode]:
        """
        Get all registered error codes.

        Returns:
            List of all ErrorCode objects in the registry

        Example:
            >>> errors = ErrorRegistry.all_errors()
            >>> len(errors)
            10
        """
        return [
            getattr(cls, attr)
            for attr in dir(cls)
            if isinstance(getattr(cls, attr), ErrorCode)
        ]


class ErrorResponse:
    """Builder for standardized error responses."""

    @staticmethod
    def create(
        error_code: ErrorCode,
        context: Optional[Dict[str, Any]] = None,
        additional_recovery: Optional[List[str]] = None,
        hook_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized error response.

        This method creates a consistent error response format that includes:
        - Error code and message
        - Severity level
        - Help URL for documentation
        - Recovery suggestions
        - Contextual information (timestamp, hook, etc.)
        - Legacy 'error' field for backward compatibility

        Args:
            error_code: The error code from ErrorRegistry
            context: Additional context (line numbers, file names, etc.)
            additional_recovery: Extra recovery suggestions beyond defaults
            hook_name: Name of the hook reporting the error

        Returns:
            Standardized error response dict suitable for JSON output

        Example:
            >>> from popkit_shared.utils.error_codes import ErrorRegistry, ErrorResponse
            >>> error = ErrorResponse.create(
            ...     ErrorRegistry.E001_JSON_PARSE,
            ...     context={"line": 42, "file": "config.json"},
            ...     hook_name="session-start"
            ... )
            >>> print(error["code"])
            E001_JSON_PARSE
            >>> print(error["help_url"])
            https://github.com/jrc1883/popkit-claude/blob/main/docs/errors/E001_JSON_PARSE.md
        """
        recovery = error_code.recovery.copy()
        if additional_recovery:
            recovery.extend(additional_recovery)

        base_url = "https://github.com/jrc1883/popkit-claude/blob/main/docs"

        response = {
            "status": "error",
            "code": error_code.code,
            "message": error_code.message,
            "severity": error_code.severity.value,
            "help_url": f"{base_url}/{error_code.help_doc}",
            "recovery": recovery,
            "context": {
                "timestamp": datetime.now().isoformat(),
                "hook": hook_name or "unknown",
                "category": error_code.category,
                **(context or {}),
            },
        }

        # Add legacy 'error' field for backward compatibility
        response["error"] = error_code.message

        return response

    @staticmethod
    def create_warning(
        warning_code: ErrorCode,
        context: Optional[Dict[str, Any]] = None,
        hook_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized warning response (non-blocking).

        Warnings use the same structure as errors but with status='warning'
        to indicate they don't block execution.

        Args:
            warning_code: The warning code from ErrorRegistry
            context: Additional context information
            hook_name: Name of the hook reporting the warning

        Returns:
            Standardized warning response dict

        Example:
            >>> warning = ErrorResponse.create_warning(
            ...     ErrorRegistry.W201_NETWORK_TIMEOUT,
            ...     context={"url": "https://api.example.com"},
            ...     hook_name="session-start"
            ... )
            >>> print(warning["status"])
            warning
        """
        response = ErrorResponse.create(warning_code, context, hook_name=hook_name)
        response["status"] = "warning"
        return response
