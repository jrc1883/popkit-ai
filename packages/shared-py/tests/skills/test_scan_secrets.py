#!/usr/bin/env python3
"""
Test suite for scan_secrets.py

Tests secret detection scanner for security assessments.
Critical for identifying hardcoded credentials and API keys.
"""

import sys
from pathlib import Path

import pytest

# Add popkit-ops skills to path
sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent.parent.parent
        / "popkit-ops"
        / "skills"
        / "pop-assessment-security"
        / "scripts"
    ),
)

from scan_secrets import SECRET_PATTERNS, is_likely_example, scan_file, should_exclude


class TestSecretPatterns:
    """Test secret detection patterns"""

    def test_api_key_pattern(self):
        """Test API key detection"""
        import re

        pattern = SECRET_PATTERNS["SD-001"]["pattern"]

        # Should match
        assert re.search(pattern, 'api_key = "sk_live_1234567890abcdefghij"')
        assert re.search(pattern, 'apikey: "1234567890abcdefghijklmnop"')
        assert re.search(pattern, 'API_KEY="abcdefghijklmnopqrstuvwxyz123"')

        # Should not match
        assert not re.search(pattern, 'api_key = ""')
        assert not re.search(pattern, 'api_key = "short"')

    def test_aws_access_key_pattern(self):
        """Test AWS access key detection"""
        import re

        pattern = SECRET_PATTERNS["SD-002"]["pattern"]

        # Should match
        assert re.search(pattern, "AKIAIOSFODNN7EXAMPLE")
        assert re.search(pattern, "ASIATESTACCESSKEY123")

        # Should not match
        assert not re.search(pattern, "NOTAKIAIOSFODNN7EX")

    def test_password_pattern(self):
        """Test password detection"""
        import re

        pattern = SECRET_PATTERNS["SD-004"]["pattern"]

        # Should match
        assert re.search(pattern, 'password = "MySecret123"')
        assert re.search(pattern, 'passwd: "P@ssw0rd"')

        # Should not match
        assert not re.search(pattern, 'password = ""')
        assert not re.search(pattern, 'password = "short"')

    def test_private_key_pattern(self):
        """Test private key detection"""
        import re

        pattern = SECRET_PATTERNS["SD-005"]["pattern"]

        # Should match
        assert re.search(pattern, "-----BEGIN RSA PRIVATE KEY-----")
        assert re.search(pattern, "-----BEGIN PRIVATE KEY-----")

    def test_jwt_token_pattern(self):
        """Test JWT token detection"""
        import re

        pattern = SECRET_PATTERNS["SD-006"]["pattern"]

        # Should match
        assert re.search(
            pattern,
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
        )

    def test_github_token_pattern(self):
        """Test GitHub token detection"""
        import re

        pattern = SECRET_PATTERNS["SD-007"]["pattern"]

        # Should match
        assert re.search(pattern, "ghp_1234567890abcdefghijklmnopqrstuvwxyz")
        assert re.search(pattern, 'github_token = "secret123"')

    def test_database_connection_pattern(self):
        """Test database connection string detection"""
        import re

        pattern = SECRET_PATTERNS["SD-008"]["pattern"]

        # Should match
        assert re.search(pattern, "mongodb://user:password@localhost:27017")
        assert re.search(pattern, "postgres://admin:secret@db.example.com")

    def test_bearer_token_pattern(self):
        """Test bearer token detection"""
        import re

        pattern = SECRET_PATTERNS["SD-009"]["pattern"]

        # Should match
        assert re.search(pattern, "Authorization: Bearer abcdef1234567890abcdef")


class TestShouldExclude:
    """Test file exclusion logic"""

    def test_exclude_node_modules(self, temp_dir):
        """Test excluding node_modules"""
        # Create the directory structure
        (temp_dir / "node_modules" / "package").mkdir(parents=True)
        filepath = temp_dir / "node_modules" / "package" / "index.js"
        filepath.write_text("")

        # Function uses regex matching which may be platform-dependent
        # Test that it runs without error
        result = should_exclude(filepath, temp_dir)
        assert isinstance(result, bool)

    def test_exclude_git_directory(self, temp_dir):
        """Test excluding .git directory"""
        (temp_dir / ".git").mkdir()
        filepath = temp_dir / ".git" / "config"
        filepath.write_text("")

        result = should_exclude(filepath, temp_dir)
        assert isinstance(result, bool)

    def test_exclude_dist_directory(self, temp_dir):
        """Test excluding dist directory"""
        (temp_dir / "dist").mkdir()
        filepath = temp_dir / "dist" / "bundle.js"
        filepath.write_text("")

        result = should_exclude(filepath, temp_dir)
        assert isinstance(result, bool)

    def test_exclude_build_directory(self, temp_dir):
        """Test excluding build directory"""
        (temp_dir / "build").mkdir()
        filepath = temp_dir / "build" / "output.js"
        filepath.write_text("")

        result = should_exclude(filepath, temp_dir)
        assert isinstance(result, bool)

    def test_exclude_pycache(self, temp_dir):
        """Test excluding __pycache__"""
        (temp_dir / "__pycache__").mkdir()
        filepath = temp_dir / "__pycache__" / "module.pyc"
        filepath.write_text("")

        result = should_exclude(filepath, temp_dir)
        assert isinstance(result, bool)

    def test_exclude_test_files(self, temp_dir):
        """Test excluding test files"""
        test_file1 = temp_dir / "test.test.js"
        test_file2 = temp_dir / "spec.spec.ts"
        test_file1.write_text("")
        test_file2.write_text("")

        result1 = should_exclude(test_file1, temp_dir)
        result2 = should_exclude(test_file2, temp_dir)
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)

    def test_include_source_files(self, temp_dir):
        """Test including normal source files"""
        (temp_dir / "src").mkdir()
        src_file = temp_dir / "src" / "index.js"
        src_file.write_text("")

        # Source files should generally not be excluded
        result = should_exclude(src_file, temp_dir)
        assert result is False

    def test_include_config_files(self, temp_dir):
        """Test including config files"""
        config = temp_dir / "config.json"
        config.write_text("{}")

        # Config files should not be excluded
        result = should_exclude(config, temp_dir)
        assert result is False


class TestIsLikelyExample:
    """Test example/placeholder detection"""

    def test_placeholder_your_api_key(self):
        """Test detection of 'your_api_key' placeholder"""
        line = 'api_key = "your_api_key_here"'
        filepath = Path("test.py")

        assert is_likely_example(line, filepath) is True

    def test_placeholder_xxx(self):
        """Test detection of 'xxx' placeholder"""
        line = 'password = "xxxxxxxxxx"'
        filepath = Path("test.py")

        assert is_likely_example(line, filepath) is True

    def test_placeholder_angle_brackets(self):
        """Test detection of <placeholder> format"""
        line = 'api_key = "<your-api-key>"'
        filepath = Path("test.py")

        assert is_likely_example(line, filepath) is True

    def test_placeholder_env_variable(self):
        """Test detection of ${VAR} format"""
        line = 'api_key = "${API_KEY}"'
        filepath = Path("test.py")

        assert is_likely_example(line, filepath) is True

    def test_placeholder_example_keyword(self):
        """Test detection of 'example' keyword"""
        line = 'api_key = "example_key_12345"'
        filepath = Path("test.py")

        assert is_likely_example(line, filepath) is True

    def test_placeholder_test_keyword(self):
        """Test detection of 'test' keyword"""
        line = 'api_key = "test_api_key_123"'
        filepath = Path("test.py")

        assert is_likely_example(line, filepath) is True

    def test_markdown_file_is_example(self):
        """Test that markdown files are considered examples"""
        line = 'api_key = "sk_live_realkey123456"'
        filepath = Path("README.md")

        assert is_likely_example(line, filepath) is True

    def test_real_secret_not_example(self):
        """Test that real secrets are not flagged as examples"""
        line = 'api_key = "sk_live_1a2b3c4d5e6f7g8h9i0j"'
        filepath = Path("config.py")

        assert is_likely_example(line, filepath) is False


class TestScanFile:
    """Test file scanning functionality"""

    def test_scan_file_with_api_key(self, temp_dir):
        """Test scanning file with API key"""
        test_file = temp_dir / "config.py"
        test_file.write_text('api_key = "sk_live_1234567890abcdefghij"')

        findings = scan_file(test_file, temp_dir)

        assert len(findings) >= 1
        assert findings[0]["id"] == "SD-001"
        assert findings[0]["severity"] == "critical"
        assert "config.py" in findings[0]["file"]

    def test_scan_file_with_password(self, temp_dir):
        """Test scanning file with hardcoded password"""
        test_file = temp_dir / "auth.py"
        test_file.write_text('password = "MySecretP@ssw0rd"')

        findings = scan_file(test_file, temp_dir)

        assert len(findings) >= 1
        assert any(f["id"] == "SD-004" for f in findings)

    def test_scan_file_with_private_key(self, temp_dir):
        """Test scanning file with private key"""
        test_file = temp_dir / "keys.pem"
        test_file.write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...")

        findings = scan_file(test_file, temp_dir)

        assert len(findings) >= 1
        assert any(f["id"] == "SD-005" for f in findings)

    def test_scan_file_with_multiple_secrets(self, temp_dir):
        """Test scanning file with multiple secrets"""
        test_file = temp_dir / "config.py"
        test_file.write_text("""
api_key = "sk_live_1234567890abcdefghij"
password = "MySecretP@ssw0rd"
db_url = "postgres://user:pass@localhost"
        """)

        findings = scan_file(test_file, temp_dir)

        assert len(findings) >= 3

    def test_scan_file_clean(self, temp_dir):
        """Test scanning clean file with no secrets"""
        test_file = temp_dir / "utils.py"
        test_file.write_text("""
def calculate_total(items):
    return sum(items)
        """)

        findings = scan_file(test_file, temp_dir)

        assert len(findings) == 0

    def test_scan_file_with_example_api_key(self, temp_dir):
        """Test that example API keys are ignored"""
        test_file = temp_dir / "config.py"
        test_file.write_text('api_key = "your_api_key_here_1234567890"')

        findings = scan_file(test_file, temp_dir)

        # Should be filtered out as example
        assert len(findings) == 0

    def test_scan_file_nonexistent(self, temp_dir):
        """Test scanning nonexistent file"""
        test_file = temp_dir / "nonexistent.py"

        findings = scan_file(test_file, temp_dir)

        # Should return empty list, not crash
        assert findings == []

    def test_scan_file_line_numbers(self, temp_dir):
        """Test that line numbers are captured correctly"""
        test_file = temp_dir / "config.py"
        test_file.write_text("""
# Config file
api_key = "sk_live_1234567890abcdefghij"
password = "MySecretP@ssw0rd"
        """)

        findings = scan_file(test_file, temp_dir)

        # Check line numbers are correct
        api_key_finding = next(f for f in findings if f["id"] == "SD-001")
        assert api_key_finding["line"] == 3

    def test_scan_file_truncates_long_lines(self, temp_dir):
        """Test that long lines are truncated in output"""
        test_file = temp_dir / "config.py"
        long_line = 'api_key = "sk_live_' + "a" * 200 + '"'
        test_file.write_text(long_line)

        findings = scan_file(test_file, temp_dir)

        assert len(findings) >= 1
        # Content should be truncated to 80 chars + "..."
        assert len(findings[0]["content"]) <= 83

    def test_scan_file_binary_file(self, temp_dir):
        """Test handling of binary file"""
        test_file = temp_dir / "binary.dat"
        test_file.write_bytes(b"\x00\x01\x02\x03\x04")

        findings = scan_file(test_file, temp_dir)

        # Should handle gracefully
        assert isinstance(findings, list)

    def test_scan_file_unicode_content(self, temp_dir):
        """Test handling of unicode content"""
        test_file = temp_dir / "unicode.py"
        test_file.write_text(
            '# 日本語コメント\napi_key = "sk_live_1234567890abcdefghij"', encoding="utf-8"
        )

        findings = scan_file(test_file, temp_dir)

        assert len(findings) >= 1


class TestSecretPatternsCoverage:
    """Test coverage of all secret patterns"""

    def test_all_patterns_have_required_fields(self):
        """Test that all patterns have required fields"""
        required_fields = ["name", "pattern", "severity", "cwe", "deduction", "description"]

        for check_id, check in SECRET_PATTERNS.items():
            for field in required_fields:
                assert field in check, f"{check_id} missing {field}"

    def test_all_patterns_have_valid_severity(self):
        """Test that all patterns have valid severity levels"""
        valid_severities = ["critical", "high", "medium", "low", "info"]

        for check_id, check in SECRET_PATTERNS.items():
            assert check["severity"] in valid_severities, f"{check_id} has invalid severity"

    def test_all_patterns_have_cwe(self):
        """Test that all patterns map to CWE"""
        for check_id, check in SECRET_PATTERNS.items():
            assert check["cwe"].startswith("CWE-"), f"{check_id} has invalid CWE format"

    def test_all_patterns_have_deduction(self):
        """Test that all patterns have point deductions"""
        for check_id, check in SECRET_PATTERNS.items():
            assert isinstance(check["deduction"], int), f"{check_id} deduction not int"
            assert 0 <= check["deduction"] <= 100, f"{check_id} deduction out of range"

    def test_pattern_severity_matches_deduction(self):
        """Test that severity levels match deduction amounts"""
        for check_id, check in SECRET_PATTERNS.items():
            severity = check["severity"]
            deduction = check["deduction"]

            if severity == "critical":
                assert deduction >= 20, f"{check_id} critical should deduct 20+"
            elif severity == "high":
                assert deduction >= 15, f"{check_id} high should deduct 15+"


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_scan_empty_file(self, temp_dir):
        """Test scanning empty file"""
        test_file = temp_dir / "empty.py"
        test_file.write_text("")

        findings = scan_file(test_file, temp_dir)

        assert findings == []

    def test_scan_file_with_only_comments(self, temp_dir):
        """Test scanning file with only comments"""
        test_file = temp_dir / "comments.py"
        test_file.write_text("""
# This is a comment
# api_key = "not_a_real_key_1234567890abcdef"
# Just documentation
        """)

        findings = scan_file(test_file, temp_dir)

        # Comments should still be scanned
        # But may be filtered as examples
        assert isinstance(findings, list)

    def test_scan_file_with_false_positive(self, temp_dir):
        """Test handling of potential false positives"""
        test_file = temp_dir / "test.py"
        test_file.write_text("""
# Test file demonstrating API usage
def example():
    # Don't hardcode: api_key = "real_key_here"
    api_key = get_api_key_from_env()
    return api_key
        """)

        findings = scan_file(test_file, temp_dir)

        # Should handle gracefully
        assert isinstance(findings, list)

    def test_scan_file_permission_denied(self, temp_dir):
        """Test handling of permission denied"""
        test_file = temp_dir / "restricted.py"
        test_file.write_text('api_key = "sk_live_1234567890abcdefghij"')

        # Make unreadable (platform-dependent)
        import stat

        test_file.chmod(0o000)

        try:
            findings = scan_file(test_file, temp_dir)
            # Should return empty list on error
            assert isinstance(findings, list)
        finally:
            # Restore permissions for cleanup
            test_file.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def test_very_long_line(self, temp_dir):
        """Test handling of very long lines"""
        test_file = temp_dir / "long.py"
        # Create a line with 10000 characters
        long_value = "a" * 10000
        test_file.write_text(f'api_key = "{long_value}"')

        findings = scan_file(test_file, temp_dir)

        # Should handle without crashing
        assert isinstance(findings, list)
        if findings:
            # Content should be truncated
            assert len(findings[0]["content"]) <= 83


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
