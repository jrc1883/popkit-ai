#!/usr/bin/env python3
"""
Unit tests for error_codes module.

Tests error code registry, response formatting, and backward compatibility.
"""

from popkit_shared.utils.error_codes import (
    ErrorRegistry,
    ErrorResponse,
    ErrorCode,
    ErrorSeverity,
)


class TestErrorRegistry:
    """Test error code registry functionality."""

    def test_all_errors_returns_list(self):
        """Test that all_errors returns a list of ErrorCode objects."""
        errors = ErrorRegistry.all_errors()
        assert isinstance(errors, list)
        assert len(errors) > 0
        assert all(isinstance(e, ErrorCode) for e in errors)

    def test_all_errors_has_at_least_30_codes(self):
        """Test that registry has at least 30 error codes (Phase 2 requirement)."""
        errors = ErrorRegistry.all_errors()
        assert len(errors) >= 30

    def test_get_error_returns_error_code(self):
        """Test that get_error returns correct ErrorCode object."""
        error = ErrorRegistry.get_error("E001_JSON_PARSE")
        assert isinstance(error, ErrorCode)
        assert error.code == "E001_JSON_PARSE"
        assert error.category == "JSON/Input Parsing"

    def test_get_error_returns_none_for_unknown(self):
        """Test that get_error returns None for unknown error codes."""
        error = ErrorRegistry.get_error("E999_UNKNOWN")
        assert error is None

    def test_error_codes_follow_naming_convention(self):
        """Test that all error codes follow [PREFIX][NUMBER]_[NAME] format."""
        errors = ErrorRegistry.all_errors()
        for error in errors:
            # Check format: prefix (E/W/S/I) + number + underscore + name
            assert error.code[0] in ["E", "W", "S", "I"], f"Invalid prefix: {error.code}"
            parts = error.code.split("_", 1)
            assert len(parts) == 2, f"Invalid format: {error.code}"
            # Check number part (should be digits)
            assert parts[0][1:].isdigit(), f"Invalid number: {error.code}"

    def test_critical_errors_have_recovery_steps(self):
        """Test that critical errors have recovery suggestions."""
        errors = ErrorRegistry.all_errors()
        critical_errors = [e for e in errors if e.severity == ErrorSeverity.CRITICAL]
        for error in critical_errors:
            assert len(error.recovery) >= 3, f"{error.code} needs 3+ recovery steps"


class TestErrorResponse:
    """Test error response formatting."""

    def test_create_error_response_has_required_fields(self):
        """Test that error response contains all required fields."""
        error = ErrorResponse.create(ErrorRegistry.E001_JSON_PARSE)

        assert error["status"] == "error"
        assert error["code"] == "E001_JSON_PARSE"
        assert "message" in error
        assert "severity" in error
        assert "help_url" in error
        assert "recovery" in error
        assert "context" in error

    def test_create_error_response_has_help_url(self):
        """Test that error response includes GitHub documentation URL."""
        error = ErrorResponse.create(ErrorRegistry.E001_JSON_PARSE)

        assert "help_url" in error
        # Use startswith() for secure URL validation (CodeQL security check)
        assert error["help_url"].startswith("https://github.com/")
        assert "/errors/E001_JSON_PARSE.md" in error["help_url"]

    def test_create_error_response_includes_recovery(self):
        """Test that error response includes recovery suggestions."""
        error = ErrorResponse.create(ErrorRegistry.E001_JSON_PARSE)

        assert "recovery" in error
        assert isinstance(error["recovery"], list)
        assert len(error["recovery"]) > 0

    def test_create_error_response_with_context(self):
        """Test that additional context is included in response."""
        context = {"line": 42, "file": "config.json"}
        error = ErrorResponse.create(
            ErrorRegistry.E001_JSON_PARSE, context=context, hook_name="session-start"
        )

        assert error["context"]["hook"] == "session-start"
        assert error["context"]["line"] == 42
        assert error["context"]["file"] == "config.json"
        assert "timestamp" in error["context"]
        assert "category" in error["context"]

    def test_create_error_response_with_additional_recovery(self):
        """Test that additional recovery steps are appended."""
        additional = ["Custom recovery step"]
        error = ErrorResponse.create(ErrorRegistry.E001_JSON_PARSE, additional_recovery=additional)

        assert "Custom recovery step" in error["recovery"]
        # Original recovery steps should still be present
        assert len(error["recovery"]) > 1

    def test_create_warning_response(self):
        """Test that warning response has status='warning'."""
        warning = ErrorResponse.create_warning(
            ErrorRegistry.W201_NETWORK_TIMEOUT, hook_name="session-start"
        )

        assert warning["status"] == "warning"
        assert warning["code"] == "W201_NETWORK_TIMEOUT"
        assert warning["severity"] in ["medium", "low", "info"]

    def test_backward_compatibility_error_field(self):
        """Test that legacy 'error' field is present for backward compatibility."""
        error = ErrorResponse.create(ErrorRegistry.E001_JSON_PARSE)

        # Legacy field should exist
        assert "error" in error
        # Should contain the error message
        assert isinstance(error["error"], str)
        assert len(error["error"]) > 0


class TestErrorCodeStructure:
    """Test ErrorCode dataclass structure."""

    def test_error_code_has_all_fields(self):
        """Test that ErrorCode has all required fields."""
        error = ErrorRegistry.E001_JSON_PARSE

        assert hasattr(error, "code")
        assert hasattr(error, "category")
        assert hasattr(error, "message")
        assert hasattr(error, "severity")
        assert hasattr(error, "help_doc")
        assert hasattr(error, "recovery")

    def test_error_severity_enum(self):
        """Test ErrorSeverity enum values."""
        assert ErrorSeverity.CRITICAL.value == "critical"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.INFO.value == "info"


class TestSpecificErrorCodes:
    """Test specific error codes from Phase 1."""

    def test_json_parse_error(self):
        """Test E001_JSON_PARSE error code."""
        error = ErrorRegistry.E001_JSON_PARSE
        assert error.code == "E001_JSON_PARSE"
        assert error.severity == ErrorSeverity.CRITICAL
        assert "JSON" in error.message

    def test_invalid_schema_error(self):
        """Test E002_INVALID_SCHEMA error code."""
        error = ErrorRegistry.E002_INVALID_SCHEMA
        assert error.code == "E002_INVALID_SCHEMA"
        assert error.severity == ErrorSeverity.HIGH
        assert "schema" in error.message.lower()

    def test_file_not_found_error(self):
        """Test E101_FILE_NOT_FOUND error code."""
        error = ErrorRegistry.E101_FILE_NOT_FOUND
        assert error.code == "E101_FILE_NOT_FOUND"
        assert error.severity == ErrorSeverity.HIGH
        assert "file" in error.message.lower()

    def test_network_timeout_warning(self):
        """Test W201_NETWORK_TIMEOUT warning code."""
        error = ErrorRegistry.W201_NETWORK_TIMEOUT
        assert error.code == "W201_NETWORK_TIMEOUT"
        assert error.severity == ErrorSeverity.MEDIUM
        assert "timeout" in error.message.lower() or "timed out" in error.message.lower()

    def test_destructive_cmd_safety(self):
        """Test S401_DESTRUCTIVE_CMD safety violation."""
        error = ErrorRegistry.S401_DESTRUCTIVE_CMD
        assert error.code == "S401_DESTRUCTIVE_CMD"
        assert error.severity == ErrorSeverity.CRITICAL
        assert "destructive" in error.message.lower()


class TestErrorResponseIntegration:
    """Integration tests for error response creation."""

    def test_complete_error_workflow(self):
        """Test complete error creation workflow."""
        # Create error with full context
        context = {"parse_error": "unexpected comma at line 42", "line": 42}
        error = ErrorResponse.create(
            ErrorRegistry.E001_JSON_PARSE,
            context=context,
            additional_recovery=["Check syntax with linter"],
            hook_name="pre-tool-use",
        )

        # Verify all components
        assert error["status"] == "error"
        assert error["code"] == "E001_JSON_PARSE"
        assert error["message"] == "Invalid JSON syntax in input"
        assert error["help_url"].startswith("https://github.com/")
        assert "github.com" in error["help_url"]
        assert len(error["recovery"]) >= 4  # 3 default + 1 additional
        assert error["context"]["hook"] == "pre-tool-use"
        assert error["context"]["line"] == 42
        assert "timestamp" in error["context"]

        # Verify backward compatibility
        assert error["error"] == error["message"]

    def test_warning_workflow(self):
        """Test complete warning creation workflow."""
        context = {"url": "https://api.example.com", "timeout_seconds": 30}
        warning = ErrorResponse.create_warning(
            ErrorRegistry.W201_NETWORK_TIMEOUT,
            context=context,
            hook_name="session-start",
        )

        # Verify warning-specific behavior
        assert warning["status"] == "warning"
        assert warning["severity"] == "medium"
        assert "graceful degradation" in " ".join(warning["recovery"]).lower()
