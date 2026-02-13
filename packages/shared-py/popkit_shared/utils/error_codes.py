#!/usr/bin/env python3
"""
PopKit Error Code System

Provides standardized error codes, messages, and recovery suggestions.

This module implements Issue #104 to provide consistent error handling across
all PopKit hooks with clear error codes, contextual information, and actionable
recovery suggestions.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


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
    help_doc: str  # Legacy per-code doc path (kept for compatibility)
    recovery: List[str]  # Recovery suggestions


class ErrorRegistry:
    """Central registry of all PopKit error codes."""

    # JSON/Input Errors (001-099)
    E001_JSON_PARSE = ErrorCode(
        code="E001_JSON_PARSE",
        category="JSON/Input Parsing",
        message="Invalid JSON syntax in input",
        severity=ErrorSeverity.CRITICAL,
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
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
        help_doc="errors/README.md",
        recovery=[
            "Update plugin to compatible version",
            "Check plugin documentation for version requirements",
            "Plugin may work with limited functionality",
        ],
    )

    # Additional JSON/Input Errors (001-099) - Phase 3
    E004_ENCODING_ERROR = ErrorCode(
        code="E004_ENCODING_ERROR",
        category="JSON/Input Parsing",
        message="Input encoding error (invalid UTF-8 or character set)",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Verify input is valid UTF-8 encoding",
            "Check for byte order marks (BOM)",
            "Convert input to UTF-8 before processing",
        ],
    )

    W005_DEPRECATED_FORMAT = ErrorCode(
        code="W005_DEPRECATED_FORMAT",
        category="JSON/Input Parsing",
        message="Input uses deprecated format",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/README.md",
        recovery=[
            "Update to current format specification",
            "See migration guide in documentation",
            "Legacy format will be removed in future version",
        ],
    )

    # Additional File I/O Errors (100-199) - Phase 3
    E106_DIRECTORY_NOT_FOUND = ErrorCode(
        code="E106_DIRECTORY_NOT_FOUND",
        category="File I/O",
        message="Required directory not found",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Create directory with 'mkdir -p <path>'",
            "Verify directory path is correct",
            "Check parent directory permissions",
        ],
    )

    W107_DISK_SPACE_LOW = ErrorCode(
        code="W107_DISK_SPACE_LOW",
        category="File I/O",
        message="Low disk space detected",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/README.md",
        recovery=[
            "Free up disk space",
            "Check with 'df -h' command",
            "Operation may continue but could fail if space runs out",
        ],
    )

    E108_FILE_LOCKED = ErrorCode(
        code="E108_FILE_LOCKED",
        category="File I/O",
        message="File is locked by another process",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Close other applications using the file",
            "Wait for other processes to release the file",
            "Check with 'lsof <file>' (Unix) or Task Manager (Windows)",
        ],
    )

    # Additional Network/API Errors (200-299) - Phase 3
    E205_DNS_RESOLUTION_FAILED = ErrorCode(
        code="E205_DNS_RESOLUTION_FAILED",
        category="Network/API",
        message="Failed to resolve hostname",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Check DNS server configuration",
            "Verify hostname is correct",
            "Try using IP address directly as workaround",
        ],
    )

    W206_SSL_CERTIFICATE_WARNING = ErrorCode(
        code="W206_SSL_CERTIFICATE_WARNING",
        category="Network/API",
        message="SSL certificate verification issue",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/README.md",
        recovery=[
            "Verify certificate is valid and not expired",
            "Check system time is correct",
            "Update certificate authority bundle if needed",
        ],
    )

    # Additional Git Operations (300-399) - Phase 3
    E305_BRANCH_NOT_FOUND = ErrorCode(
        code="E305_BRANCH_NOT_FOUND",
        category="Git Operations",
        message="Git branch not found",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "List branches with 'git branch -a'",
            "Create branch with 'git checkout -b <branch-name>'",
            "Fetch remote branches with 'git fetch'",
        ],
    )

    W306_BEHIND_REMOTE = ErrorCode(
        code="W306_BEHIND_REMOTE",
        category="Git Operations",
        message="Local branch is behind remote",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/README.md",
        recovery=[
            "Pull latest changes with 'git pull'",
            "Check commits with 'git log origin/<branch>..<branch>'",
            "Operation may continue but conflicts possible",
        ],
    )

    E307_PUSH_REJECTED = ErrorCode(
        code="E307_PUSH_REJECTED",
        category="Git Operations",
        message="Git push rejected by remote",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Pull latest changes first with 'git pull'",
            "Resolve any conflicts",
            "Use 'git push --force' only if you're certain (destructive)",
        ],
    )

    # Additional Safety/Security (400-499) - Phase 3
    S405_UNVERIFIED_SOURCE = ErrorCode(
        code="S405_UNVERIFIED_SOURCE",
        category="Safety/Security",
        message="Operation involves unverified or untrusted source",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Verify source is trusted and legitimate",
            "Check signatures and checksums",
            "Use official sources when possible",
        ],
    )

    W406_DEPRECATED_SECURITY = ErrorCode(
        code="W406_DEPRECATED_SECURITY",
        category="Safety/Security",
        message="Using deprecated security method",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/README.md",
        recovery=[
            "Update to modern security practices",
            "See security documentation for alternatives",
            "Deprecated method will be removed in future",
        ],
    )

    # Additional Database Errors (500-599) - Phase 3
    E503_TRANSACTION_FAILED = ErrorCode(
        code="E503_TRANSACTION_FAILED",
        category="Database",
        message="Database transaction failed or rolled back",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Check transaction logs for details",
            "Verify data constraints are satisfied",
            "Retry transaction if appropriate",
        ],
    )

    W504_SLOW_QUERY = ErrorCode(
        code="W504_SLOW_QUERY",
        category="Database",
        message="Database query is running slowly",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/README.md",
        recovery=[
            "Add database indexes for frequently queried fields",
            "Optimize query structure",
            "Operation will continue but performance impacted",
        ],
    )

    E505_SCHEMA_MISMATCH = ErrorCode(
        code="E505_SCHEMA_MISMATCH",
        category="Database",
        message="Database schema doesn't match expected structure",
        severity=ErrorSeverity.CRITICAL,
        help_doc="errors/README.md",
        recovery=[
            "Run database migrations",
            "Verify database version matches application",
            "Check migration logs for failures",
        ],
    )

    # Additional Tool Execution (600-699) - Phase 3
    E604_TOOL_NOT_FOUND = ErrorCode(
        code="E604_TOOL_NOT_FOUND",
        category="Tool Execution",
        message="Required tool or command not found",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Install required tool",
            "Add tool to system PATH",
            "Verify tool name is spelled correctly",
        ],
    )

    W605_TOOL_VERSION_OLD = ErrorCode(
        code="W605_TOOL_VERSION_OLD",
        category="Tool Execution",
        message="Tool version is outdated",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/README.md",
        recovery=[
            "Update tool to latest version",
            "Check compatibility requirements",
            "Tool may work with limited functionality",
        ],
    )

    E606_TOOL_CRASHED = ErrorCode(
        code="E606_TOOL_CRASHED",
        category="Tool Execution",
        message="Tool crashed or terminated unexpectedly",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Check tool logs for crash details",
            "Verify system resources are sufficient",
            "Report crash to tool maintainers if reproducible",
        ],
    )

    # Additional Configuration (700-799) - Phase 3
    E703_CONFIG_PARSE_ERROR = ErrorCode(
        code="E703_CONFIG_PARSE_ERROR",
        category="Configuration",
        message="Failed to parse configuration file",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Check configuration file syntax (YAML/JSON/TOML)",
            "Validate with appropriate linter",
            "Compare with example configuration",
        ],
    )

    W704_CONFIG_OVERRIDE = ErrorCode(
        code="W704_CONFIG_OVERRIDE",
        category="Configuration",
        message="Configuration value overridden by environment variable",
        severity=ErrorSeverity.LOW,
        help_doc="errors/README.md",
        recovery=[
            "This is informational - environment variables take precedence",
            "Unset environment variable to use config file value",
            "See documentation for configuration precedence order",
        ],
    )

    E705_CONFIG_VALIDATION_FAILED = ErrorCode(
        code="E705_CONFIG_VALIDATION_FAILED",
        category="Configuration",
        message="Configuration validation failed",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Review validation error details",
            "Ensure all required fields have valid values",
            "Check value ranges and constraints",
        ],
    )

    # Additional Plugin/Extension Errors (800-899) - Phase 3
    E803_PLUGIN_CONFLICT = ErrorCode(
        code="E803_PLUGIN_CONFLICT",
        category="Plugin/Extension",
        message="Plugin conflict detected",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Disable conflicting plugins",
            "Check plugin compatibility matrix",
            "Update plugins to compatible versions",
        ],
    )

    W804_PLUGIN_DEPRECATED = ErrorCode(
        code="W804_PLUGIN_DEPRECATED",
        category="Plugin/Extension",
        message="Plugin is deprecated",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/README.md",
        recovery=[
            "Migrate to recommended alternative",
            "See deprecation notice for timeline",
            "Plugin will be removed in future version",
        ],
    )

    E805_PLUGIN_INIT_FAILED = ErrorCode(
        code="E805_PLUGIN_INIT_FAILED",
        category="Plugin/Extension",
        message="Plugin initialization failed",
        severity=ErrorSeverity.HIGH,
        help_doc="errors/README.md",
        recovery=[
            "Check plugin configuration",
            "Verify dependencies are installed",
            "Review plugin initialization logs",
        ],
    )

    # System/Internal Errors (900-999) - Phase 3
    E901_ASSERTION_FAILED = ErrorCode(
        code="E901_ASSERTION_FAILED",
        category="System/Internal",
        message="Internal assertion failed",
        severity=ErrorSeverity.CRITICAL,
        help_doc="errors/README.md",
        recovery=[
            "This indicates an internal error",
            "Please report this issue with full context",
            "Check for known issues in issue tracker",
        ],
    )

    E902_UNEXPECTED_STATE = ErrorCode(
        code="E902_UNEXPECTED_STATE",
        category="System/Internal",
        message="System reached unexpected state",
        severity=ErrorSeverity.CRITICAL,
        help_doc="errors/README.md",
        recovery=[
            "Restart the application",
            "Check system logs for details",
            "Report issue if reproducible",
        ],
    )

    W903_RESOURCE_WARNING = ErrorCode(
        code="W903_RESOURCE_WARNING",
        category="System/Internal",
        message="System resource usage warning",
        severity=ErrorSeverity.MEDIUM,
        help_doc="errors/README.md",
        recovery=[
            "Monitor resource usage (CPU/memory/disk)",
            "Close unnecessary applications",
            "Operation will continue with potential slowdown",
        ],
    )

    E904_RESOURCE_EXHAUSTED = ErrorCode(
        code="E904_RESOURCE_EXHAUSTED",
        category="System/Internal",
        message="System resources exhausted",
        severity=ErrorSeverity.CRITICAL,
        help_doc="errors/README.md",
        recovery=[
            "Free up system resources (memory/disk/file handles)",
            "Restart application",
            "Check for resource leaks",
        ],
    )

    I905_MAINTENANCE_MODE = ErrorCode(
        code="I905_MAINTENANCE_MODE",
        category="System/Internal",
        message="System is in maintenance mode",
        severity=ErrorSeverity.INFO,
        help_doc="errors/README.md",
        recovery=[
            "Wait for maintenance to complete",
            "Check status page for updates",
            "Some features may be temporarily unavailable",
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
            https://github.com/jrc1883/popkit-claude/blob/main/docs/errors/README.md
        """
        recovery = error_code.recovery.copy()
        if additional_recovery:
            recovery.extend(additional_recovery)

        base_url = "https://github.com/jrc1883/popkit-claude/blob/main/docs/errors/README.md"

        response = {
            "status": "error",
            "code": error_code.code,
            "message": error_code.message,
            "severity": error_code.severity.value,
            "help_url": base_url,
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
