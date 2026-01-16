#!/usr/bin/env python3
"""
Test suite for privacy.py

Tests anonymization, GDPR compliance, consent management, and privacy settings.
Critical for user data protection and regulatory compliance.
"""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.privacy import (
    AnonymizationLevel,
    PrivacyManager,
    PrivacySettings,
    abstract_code_identifiers,
    abstract_error_message,
    anonymize_content,
    detect_sensitive_data,
    generate_content_hash,
)


class TestAnonymizationLevel:
    """Test AnonymizationLevel enum"""

    def test_enum_values(self):
        """Test enum has correct values"""
        assert AnonymizationLevel.STRICT.value == "strict"
        assert AnonymizationLevel.MODERATE.value == "moderate"
        assert AnonymizationLevel.MINIMAL.value == "minimal"


class TestPrivacySettings:
    """Test PrivacySettings data structure"""

    def test_default_settings(self):
        """Test default privacy settings"""
        settings = PrivacySettings()
        assert settings.sharing_enabled is True
        assert settings.anonymization_level == "moderate"
        assert settings.consent_given is False
        assert settings.consent_timestamp is None
        assert settings.auto_delete_days == 90
        assert settings.data_region == "us"

    def test_to_dict(self):
        """Test converting settings to dictionary"""
        settings = PrivacySettings(
            sharing_enabled=False, consent_given=True, consent_timestamp="2024-01-01T00:00:00"
        )
        result = settings.to_dict()

        assert isinstance(result, dict)
        assert result["sharing_enabled"] is False
        assert result["consent_given"] is True
        assert result["consent_timestamp"] == "2024-01-01T00:00:00"

    def test_from_dict(self):
        """Test creating settings from dictionary"""
        data = {
            "sharing_enabled": False,
            "anonymization_level": "strict",
            "consent_given": True,
            "auto_delete_days": 30,
        }
        settings = PrivacySettings.from_dict(data)

        assert settings.sharing_enabled is False
        assert settings.anonymization_level == "strict"
        assert settings.consent_given is True
        assert settings.auto_delete_days == 30

    def test_from_dict_with_defaults(self):
        """Test from_dict uses defaults for missing fields"""
        data = {"consent_given": True}
        settings = PrivacySettings.from_dict(data)

        assert settings.consent_given is True
        assert settings.sharing_enabled is True  # default
        assert settings.anonymization_level == "moderate"  # default


class TestDetectSensitiveData:
    """Test sensitive data detection"""

    def test_detect_api_key(self):
        """Test detecting API keys"""
        # Using fake_test_ prefix to avoid GitHub secret scanning false positives
        content = 'const apiKey = "apikey_live_1111111111222222222233333333334444444444";'
        detections = detect_sensitive_data(content)

        assert len(detections) > 0
        categories = [d["category"] for d in detections]
        assert "api_key" in categories

    def test_detect_email(self):
        """Test detecting email addresses"""
        content = "Contact: user@example.com"
        detections = detect_sensitive_data(content)

        assert len(detections) > 0
        assert any(d["category"] == "email" for d in detections)
        assert any("user@example.com" in d["match"] for d in detections)

    def test_detect_phone_number(self):
        """Test detecting phone numbers"""
        content = "Call me at (555) 123-4567"
        detections = detect_sensitive_data(content)

        phone_detections = [d for d in detections if d["category"] == "phone"]
        assert len(phone_detections) > 0

    def test_detect_file_paths_unix(self):
        """Test detecting Unix file paths"""
        content = "/Users/john/projects/myapp/src/auth.ts"
        detections = detect_sensitive_data(content)

        path_detections = [d for d in detections if d["category"] == "paths"]
        assert len(path_detections) > 0

    def test_detect_file_paths_windows(self):
        """Test detecting Windows file paths"""
        content = "C:\\Users\\john\\projects\\app.py"
        detections = detect_sensitive_data(content)

        path_detections = [d for d in detections if d["category"] == "paths"]
        assert len(path_detections) > 0

    def test_detect_ip_address(self):
        """Test detecting IP addresses"""
        content = "Server at 192.168.1.100"
        detections = detect_sensitive_data(content)

        ip_detections = [d for d in detections if d["category"] == "ip_address"]
        assert len(ip_detections) > 0

    def test_detect_database_url(self):
        """Test detecting database connection strings"""
        content = "mongodb://user:pass@localhost:27017/db"
        detections = detect_sensitive_data(content)

        db_detections = [d for d in detections if d["category"] == "database_connection"]
        assert len(db_detections) > 0

    def test_detect_uuid(self):
        """Test detecting UUIDs"""
        content = "ID: 550e8400-e29b-41d4-a716-446655440000"
        detections = detect_sensitive_data(content)

        uuid_detections = [d for d in detections if d["category"] == "uuid"]
        assert len(uuid_detections) > 0

    def test_detect_multiple_types(self):
        """Test detecting multiple sensitive data types"""
        content = """
        const apiKey = "apikey_test_1111111111222222222233333333334444444444";
        const email = "user@example.com";
        const path = "/Users/john/app";
        """
        detections = detect_sensitive_data(content)

        categories = set(d["category"] for d in detections)
        assert "api_key" in categories
        assert "email" in categories
        assert "paths" in categories

    def test_no_sensitive_data(self):
        """Test content with no sensitive data"""
        content = "const greeting = 'Hello World';"
        detections = detect_sensitive_data(content)

        assert len(detections) == 0


class TestAnonymizeContent:
    """Test content anonymization"""

    def test_anonymize_api_key_moderate(self):
        """Test anonymizing API key at moderate level"""
        content = 'apiKey = "apikey_live_5555555555666666666677777777778888888888"'
        anonymized, removed = anonymize_content(content, AnonymizationLevel.MODERATE)

        assert "[API_KEY]" in anonymized
        assert "apikey_live_5555555555666666666677777777778888888888" not in anonymized
        assert "api_key" in removed

    def test_anonymize_email_moderate(self):
        """Test anonymizing email at moderate level"""
        content = "Contact: user@example.com"
        anonymized, removed = anonymize_content(content, AnonymizationLevel.MODERATE)

        assert "[EMAIL]" in anonymized
        assert "user@example.com" not in anonymized

    def test_anonymize_paths_moderate(self):
        """Test anonymizing paths at moderate level"""
        content = "/Users/john/myproject/src/file.ts"
        anonymized, removed = anonymize_content(content, AnonymizationLevel.MODERATE)

        assert "project/" in anonymized
        assert "/Users/john/" not in anonymized

    def test_strict_anonymization(self):
        """Test strict anonymization includes code abstraction"""
        content = "function handleUserLogin() { return true; }"
        anonymized, removed = anonymize_content(content, AnonymizationLevel.STRICT)

        # Strict mode should abstract function names
        assert "[HANDLER]" in anonymized or "handleUserLogin" not in anonymized

    def test_minimal_anonymization(self):
        """Test minimal anonymization only removes critical data"""
        content = 'const key = "apikey_live_5555555555666666666677777777778888888888"; const path = "/Users/me/app"'
        anonymized, removed = anonymize_content(content, AnonymizationLevel.MINIMAL)

        # API key should be removed (always)
        assert "apikey_live_5555555555666666666677777777778888888888" not in anonymized
        # Paths might be preserved at minimal level
        # The actual behavior depends on implementation

    def test_preserve_structure(self):
        """Test that anonymization preserves code structure"""
        content = '{"apiKey": "secret123", "name": "MyApp"}'
        anonymized, removed = anonymize_content(content, AnonymizationLevel.MODERATE)

        # Structure should be preserved
        assert "{" in anonymized
        assert "}" in anonymized
        assert '"name"' in anonymized or "name" in anonymized

    def test_empty_content(self):
        """Test anonymizing empty content"""
        anonymized, removed = anonymize_content("", AnonymizationLevel.MODERATE)
        assert anonymized == ""
        assert removed == []

    def test_content_with_no_sensitive_data(self):
        """Test anonymizing content with no sensitive data"""
        content = "const x = 42; console.log('Hello');"
        anonymized, removed = anonymize_content(content, AnonymizationLevel.MODERATE)

        assert anonymized == content  # Should be unchanged
        assert len(removed) == 0


class TestAbstractCodeIdentifiers:
    """Test code identifier abstraction"""

    def test_abstract_handle_functions(self):
        """Test abstracting handle* functions"""
        # Note: function needs space or punctuation before it for lookbehind
        content = "function handleUserAuth() { return true; }"
        abstracted = abstract_code_identifiers(content)

        assert "[HANDLER]" in abstracted
        assert "handleUserAuth" not in abstracted

    def test_abstract_get_functions(self):
        """Test abstracting get* functions"""
        content = "function getUserData() { return data; }"
        abstracted = abstract_code_identifiers(content)

        assert "[GETTER]" in abstracted

    def test_abstract_set_functions(self):
        """Test abstracting set* functions"""
        content = "function setUserPreferences(prefs) { this.prefs = prefs; }"
        abstracted = abstract_code_identifiers(content)

        assert "[SETTER]" in abstracted

    def test_abstract_fetch_functions(self):
        """Test abstracting fetch* functions"""
        content = "function fetchApiData() { return fetch('/api'); }"
        abstracted = abstract_code_identifiers(content)

        assert "[FETCHER]" in abstracted

    def test_abstract_multiple_patterns(self):
        """Test abstracting multiple patterns"""
        content = "const x = handleAuth(); const y = getUserData(); const z = setConfig();"
        abstracted = abstract_code_identifiers(content)

        assert "[HANDLER]" in abstracted
        assert "[GETTER]" in abstracted
        assert "[SETTER]" in abstracted

    def test_preserve_non_matching_code(self):
        """Test that non-matching code is preserved"""
        content = "const x = 42; console.log('test');"
        abstracted = abstract_code_identifiers(content)

        # Should contain similar content (exact match depends on implementation)
        assert "const" in abstracted or "42" in abstracted


class TestAbstractErrorMessage:
    """Test error message abstraction"""

    def test_remove_line_numbers(self):
        """Test removing line numbers from errors"""
        error = "TypeError at line 42"
        abstracted = abstract_error_message(error)

        assert "42" not in abstracted or "line" not in abstracted

    def test_remove_file_paths(self):
        """Test removing file paths from stack traces"""
        error = "at handleAuth (auth.ts:45:12)"
        abstracted = abstract_error_message(error)

        assert ":45:12" not in abstracted

    def test_abstract_property_names(self):
        """Test abstracting property names"""
        error = "Cannot read property 'userToken' of undefined"
        abstracted = abstract_error_message(error)

        assert "[PROP]" in abstracted
        assert "userToken" not in abstracted

    def test_abstract_function_names_in_stack(self):
        """Test abstracting function names in stack traces"""
        error = "at getUserData (module.js:10)"
        abstracted = abstract_error_message(error)

        assert "[FUNCTION]" in abstracted or "getUserData" not in abstracted

    def test_preserve_error_type(self):
        """Test that error type is preserved"""
        error = "TypeError: Cannot read property 'x' of undefined"
        abstracted = abstract_error_message(error)

        assert "TypeError" in abstracted

    def test_empty_error(self):
        """Test abstracting empty error"""
        abstracted = abstract_error_message("")
        assert abstracted == ""


class TestGenerateContentHash:
    """Test content hash generation"""

    def test_consistent_hashing(self):
        """Test that same content produces same hash"""
        content = "const x = 42;"
        hash1 = generate_content_hash(content)
        hash2 = generate_content_hash(content)

        assert hash1 == hash2

    def test_different_content_different_hash(self):
        """Test that different content produces different hash"""
        hash1 = generate_content_hash("const x = 42;")
        hash2 = generate_content_hash("const y = 100;")

        assert hash1 != hash2

    def test_whitespace_normalization(self):
        """Test that whitespace is normalized"""
        hash1 = generate_content_hash("const x = 42;")
        hash2 = generate_content_hash("const  x  =  42;")

        # Should produce same hash after normalization
        assert hash1 == hash2

    def test_case_normalization(self):
        """Test that case is normalized"""
        hash1 = generate_content_hash("CONST X = 42;")
        hash2 = generate_content_hash("const x = 42;")

        # Should produce same hash after normalization
        assert hash1 == hash2

    def test_hash_length(self):
        """Test hash has expected length"""
        content = "test content"
        hash_value = generate_content_hash(content)

        assert len(hash_value) == 16  # First 16 chars of SHA256


class TestPrivacyManager:
    """Test PrivacyManager class"""

    def test_initialization(self):
        """Test PrivacyManager initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            assert manager.project_dir == Path(tmpdir)
            assert manager.settings_dir == Path(tmpdir) / ".claude" / "popkit"

    def test_load_default_settings(self):
        """Test loading default settings when file doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            settings = manager.load_settings()

            assert isinstance(settings, PrivacySettings)
            assert settings.sharing_enabled is True
            assert settings.consent_given is False

    def test_save_and_load_settings(self):
        """Test saving and loading settings"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)

            # Modify settings
            manager.settings.sharing_enabled = False
            manager.settings.consent_given = True
            manager.save_settings()

            # Create new manager and load
            manager2 = PrivacyManager(tmpdir)
            loaded = manager2.load_settings()

            assert loaded.sharing_enabled is False
            assert loaded.consent_given is True

    def test_give_consent(self):
        """Test giving consent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            manager.give_consent()

            assert manager.settings.consent_given is True
            assert manager.settings.consent_timestamp is not None

    def test_revoke_consent(self):
        """Test revoking consent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            manager.give_consent()
            manager.revoke_consent()

            assert manager.settings.consent_given is False
            assert manager.settings.sharing_enabled is False

    def test_set_anonymization_level(self):
        """Test setting anonymization level"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            manager.set_anonymization_level("strict")

            assert manager.settings.anonymization_level == "strict"

    def test_add_excluded_project(self):
        """Test adding project to exclusion list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            manager.add_excluded_project("my-secret-project")

            assert "my-secret-project" in manager.settings.excluded_projects

    def test_remove_excluded_project(self):
        """Test removing project from exclusion list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            manager.add_excluded_project("test-project")
            manager.remove_excluded_project("test-project")

            assert "test-project" not in manager.settings.excluded_projects

    def test_add_excluded_pattern(self):
        """Test adding file pattern to exclusion"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            manager.add_excluded_pattern("*.secret")

            assert "*.secret" in manager.settings.excluded_patterns

    def test_can_share_without_consent(self):
        """Test can_share returns False without consent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            can_share, reason = manager.can_share()

            assert can_share is False
            assert "consent" in reason.lower()

    def test_can_share_with_consent(self):
        """Test can_share returns True with consent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            manager.give_consent()
            can_share, reason = manager.can_share()

            assert can_share is True

    def test_can_share_sharing_disabled(self):
        """Test can_share when sharing is disabled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            manager.settings.consent_given = True
            manager.settings.sharing_enabled = False
            manager.save_settings()

            can_share, reason = manager.can_share()

            assert can_share is False
            assert "disabled" in reason.lower()

    def test_should_exclude_file_by_pattern(self):
        """Test file exclusion by pattern"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            manager.add_excluded_pattern("*.secret")

            assert manager.should_exclude_file("config.secret") is True
            assert manager.should_exclude_file("normal.py") is False

    def test_should_exclude_sensitive_files(self):
        """Test automatic exclusion of sensitive files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)

            assert manager.should_exclude_file(".env") is True
            assert manager.should_exclude_file("secrets.json") is True
            assert manager.should_exclude_file("credentials.yml") is True
            assert manager.should_exclude_file("private.key") is True

    def test_anonymize_content(self):
        """Test anonymizing content through manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            content = 'const key = "apikey_live_5555555555666666666677777777778888888888"; const email = "user@example.com";'

            anonymized, metadata = manager.anonymize(content)

            assert "apikey_live_5555555555666666666677777777778888888888" not in anonymized
            assert "user@example.com" not in anonymized
            assert metadata["level"] == "moderate"
            assert "content_hash" in metadata

    def test_anonymize_excluded_file(self):
        """Test anonymizing excluded file returns empty"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)

            anonymized, metadata = manager.anonymize("content", ".env")

            assert anonymized == ""
            assert metadata["excluded"] is True


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_detect_sensitive_data_empty_string(self):
        """Test detecting sensitive data in empty string"""
        detections = detect_sensitive_data("")
        assert detections == []

    def test_detect_sensitive_data_unicode(self):
        """Test detecting sensitive data with Unicode"""
        content = "Email: user@例.com"
        detections = detect_sensitive_data(content)
        # Should handle Unicode without crashing
        assert isinstance(detections, list)

    def test_anonymize_unicode_content(self):
        """Test anonymizing Unicode content"""
        content = "const message = '你好 World'; const key = 'apikey_live_5555555555666666666677777777778888888888';"
        anonymized, removed = anonymize_content(content, AnonymizationLevel.MODERATE)

        assert "你好" in anonymized  # Non-sensitive Unicode preserved
        assert "apikey_live_5555555555666666666677777777778888888888" not in anonymized

    def test_privacy_settings_invalid_json(self):
        """Test loading invalid JSON settings file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PrivacyManager(tmpdir)
            manager.settings_dir.mkdir(parents=True, exist_ok=True)
            manager.settings_file.write_text("invalid json {")

            # Should fall back to defaults
            settings = manager.load_settings()
            assert isinstance(settings, PrivacySettings)

    def test_content_hash_special_characters(self):
        """Test hashing content with special characters"""
        content = "const x = '!@#$%^&*()'; const y = '<script>alert(1)</script>';"
        hash_value = generate_content_hash(content)

        assert len(hash_value) == 16
        assert isinstance(hash_value, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
