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

    # Additional JSON/Input Errors (001-099) - Phase 2
    E003_MALFORMED_INPUT = ErrorCode(
        code="E003_MALFORMED_INPUT",
        category="JSON/Input Parsing",
        message="Input data is malformed or corrupted",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E003_MALFORMED_INPUT.md",
        recovery=[
            "Verify input format matches expected structure",
            "Check for encoding issues (UTF-8 expected)",
            "Try regenerating the input data",
        ],
    )

    # Additional File I/O Errors (100-199) - Phase 2
    E103_FILE_READ_ERROR = ErrorCode(
        code="E103_FILE_READ_ERROR",
        category="File I/O",
        message="Failed to read file contents",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E103_FILE_READ_ERROR.md",
        recovery=[
            "Check file is not locked by another process",
            "Verify file is not corrupted",
            "Ensure sufficient system resources available",
        ],
    )

    E104_FILE_WRITE_ERROR = ErrorCode(
        code="E104_FILE_WRITE_ERROR",
        category="File I/O",
        message="Failed to write to file",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E104_FILE_WRITE_ERROR.md",
        recovery=[
            "Check available disk space",
            "Verify write permissions on target directory",
            "Ensure file is not locked by another process",
        ],
    )

    W105_FILE_TOO_LARGE = ErrorCode(
        code="W105_FILE_TOO_LARGE",
        category="File I/O",
        message="File size exceeds recommended limits",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/W105_FILE_TOO_LARGE.md",
        recovery=[
            "Consider processing file in chunks",
            "Use streaming approach for large files",
            "Operation will continue with potential performance impact",
        ],
    )

    # Additional Network/API Errors (200-299) - Phase 2
    E202_CONNECTION_REFUSED = ErrorCode(
        code="E202_CONNECTION_REFUSED",
        category="Network/API",
        message="Connection refused by remote server",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E202_CONNECTION_REFUSED.md",
        recovery=[
            "Verify server is running and accessible",
            "Check firewall and network settings",
            "Confirm correct hostname and port",
        ],
    )

    E203_API_ERROR = ErrorCode(
        code="E203_API_ERROR",
        category="Network/API",
        message="API request failed with error response",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E203_API_ERROR.md",
        recovery=[
            "Check API error message for details",
            "Verify API credentials and permissions",
            "Review API documentation for correct usage",
        ],
    )

    W204_RATE_LIMIT = ErrorCode(
        code="W204_RATE_LIMIT",
        category="Network/API",
        message="API rate limit exceeded",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/W204_RATE_LIMIT.md",
        recovery=[
            "Wait before retrying (check Retry-After header)",
            "Reduce request frequency",
            "Consider implementing exponential backoff",
        ],
    )

    # Additional Git Operations (300-399) - Phase 2
    E302_MERGE_CONFLICT = ErrorCode(
        code="E302_MERGE_CONFLICT",
        category="Git Operations",
        message="Git merge conflict detected",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E302_MERGE_CONFLICT.md",
        recovery=[
            "Resolve conflicts manually in affected files",
            "Use 'git status' to see conflicted files",
            "After resolving, run 'git add' and 'git commit'",
        ],
    )

    E303_DETACHED_HEAD = ErrorCode(
        code="E303_DETACHED_HEAD",
        category="Git Operations",
        message="Git repository is in detached HEAD state",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E303_DETACHED_HEAD.md",
        recovery=[
            "Create a new branch with 'git checkout -b <branch-name>'",
            "Return to branch with 'git checkout <branch-name>'",
            "Commit changes before switching branches",
        ],
    )

    W304_UNCOMMITTED_CHANGES = ErrorCode(
        code="W304_UNCOMMITTED_CHANGES",
        category="Git Operations",
        message="Uncommitted changes detected",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/W304_UNCOMMITTED_CHANGES.md",
        recovery=[
            "Commit changes with 'git commit'",
            "Stash changes with 'git stash'",
            "Operation may continue but changes could be lost",
        ],
    )

    # Additional Safety/Security (400-499) - Phase 2
    S402_CREDENTIAL_LEAK = ErrorCode(
        code="S402_CREDENTIAL_LEAK",
        category="Safety/Security",
        message="Potential credential or secret detected",
        severity=ErrorSeverity.CRITICAL,
        help_doc="errors/S402_CREDENTIAL_LEAK.md",
        recovery=[
            "Remove credentials from code immediately",
            "Use environment variables or secure vault",
            "Rotate compromised credentials if already committed",
        ],
    )

    S403_INSECURE_OPERATION = ErrorCode(
        code="S403_INSECURE_OPERATION",
        category="Safety/Security",
        message="Operation uses insecure method or protocol",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/S403_INSECURE_OPERATION.md",
        recovery=[
            "Use secure alternative (HTTPS instead of HTTP)",
            "Enable encryption for sensitive data",
            "Review security best practices",
        ],
    )

    W404_SECURITY_WARNING = ErrorCode(
        code="W404_SECURITY_WARNING",
        category="Safety/Security",
        message="Potential security concern detected",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/W404_SECURITY_WARNING.md",
        recovery=[
            "Review security implications",
            "Consider safer alternative approach",
            "Operation will continue but requires attention",
        ],
    )

    # Database Errors (500-599) - Phase 2
    E501_DB_CONNECTION_FAILED = ErrorCode(
        code="E501_DB_CONNECTION_FAILED",
        category="Database",
        message="Failed to connect to database",
        severity=ErrorSeverity.CRITICAL,
        help_doc="errors/E501_DB_CONNECTION_FAILED.md",
        recovery=[
            "Check database server is running",
            "Verify connection string and credentials",
            "Ensure network connectivity to database",
        ],
    )

    E502_QUERY_ERROR = ErrorCode(
        code="E502_QUERY_ERROR",
        category="Database",
        message="Database query execution failed",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E502_QUERY_ERROR.md",
        recovery=[
            "Check query syntax",
            "Verify table and column names exist",
            "Review database error message for details",
        ],
    )

    # Additional Tool Execution (600-699) - Phase 2
    W602_TOOL_TIMEOUT = ErrorCode(
        code="W602_TOOL_TIMEOUT",
        category="Tool Execution",
        message="Tool execution timed out",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/W602_TOOL_TIMEOUT.md",
        recovery=[
            "Increase timeout value if appropriate",
            "Check if operation is stuck or hanging",
            "Consider breaking into smaller operations",
        ],
    )

    E603_INVALID_ARGS = ErrorCode(
        code="E603_INVALID_ARGS",
        category="Tool Execution",
        message="Invalid arguments provided to tool",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E603_INVALID_ARGS.md",
        recovery=[
            "Review tool documentation for correct argument format",
            "Check argument types and values",
            "Verify all required arguments are provided",
        ],
    )

    # Additional Configuration (700-799) - Phase 2
    E702_CONFIG_NOT_FOUND = ErrorCode(
        code="E702_CONFIG_NOT_FOUND",
        category="Configuration",
        message="Configuration file not found",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E702_CONFIG_NOT_FOUND.md",
        recovery=[
            "Create configuration file with required settings",
            "Check configuration file path",
            "Copy from template if available",
        ],
    )

    # Plugin/Extension Errors (800-899) - Phase 2
    E801_PLUGIN_LOAD_FAILED = ErrorCode(
        code="E801_PLUGIN_LOAD_FAILED",
        category="Plugin/Extension",
        message="Failed to load plugin or extension",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/E801_PLUGIN_LOAD_FAILED.md",
        recovery=[
            "Verify plugin is installed correctly",
            "Check plugin compatibility with current version",
            "Review plugin error logs for details",
        ],
    )

    W802_VERSION_MISMATCH = ErrorCode(
        code="W802_VERSION_MISMATCH",
        category="Plugin/Extension",
        message="Plugin version incompatibility detected",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/W802_VERSION_MISMATCH.md",
        recovery=[
            "Update plugin to compatible version",
            "Check plugin documentation for version requirements",
            "Plugin may work with limited functionality",
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
            getattr(cls, attr) for attr in dir(cls) if isinstance(getattr(cls, attr), ErrorCode)
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
