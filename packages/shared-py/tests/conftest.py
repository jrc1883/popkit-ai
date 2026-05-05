#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for popkit_shared tests

Provides common test fixtures, utilities, and configuration.
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# Fixtures - Temporary Directories
# =============================================================================


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_project_dir(temp_dir):
    """Create a temporary project directory with .claude structure"""
    claude_dir = temp_dir / ".claude"
    claude_dir.mkdir(parents=True)
    popkit_dir = claude_dir / "popkit"
    popkit_dir.mkdir(parents=True)
    yield temp_dir


# =============================================================================
# Fixtures - Sample Data
# =============================================================================


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing"""
    return {
        "string": "value",
        "number": 42,
        "boolean": True,
        "null": None,
        "array": [1, 2, 3],
        "nested": {"key": "value"},
    }


@pytest.fixture
def sample_sensitive_content():
    """Sample content with sensitive data for privacy testing"""
    return """
    const apiKey = "sk_live_abc123def456";
    const email = "user@example.com";
    const path = "/Users/john/myproject/src/auth.ts";
    const dbUrl = "postgres://user:pass@localhost:5432/db";
    const phone = "(555) 123-4567";
    """


@pytest.fixture
def sample_code_content():
    """Sample code content for testing"""
    return """
    function handleUserAuth(credentials) {
        const token = getAuthToken();
        return validateCredentials(credentials);
    }

    function fetchUserData(userId) {
        return fetch(`/api/users/${userId}`);
    }
    """


# =============================================================================
# Fixtures - Command Arguments
# =============================================================================


@pytest.fixture
def work_command_samples():
    """Sample /popkit:work command arguments"""
    return [
        ("#4", {"issue_number": 4, "force_power": False}),
        ("#4 -p", {"issue_number": 4, "force_power": True}),
        ("#4 --solo", {"issue_number": 4, "force_solo": True}),
        ("gh-10", {"issue_number": 10, "force_power": False}),
    ]


@pytest.fixture
def issues_command_samples():
    """Sample /popkit:issues command arguments"""
    return [
        ("", {"filter_power": False, "state": "open"}),
        ("-p", {"filter_power": True}),
        ("--label bug", {"label": "bug"}),
        ("--state closed -n 10", {"state": "closed", "limit": 10}),
    ]


# =============================================================================
# Fixtures - Privacy Settings
# =============================================================================


@pytest.fixture
def default_privacy_settings():
    """Default privacy settings"""
    from popkit_shared.utils.privacy import PrivacySettings

    return PrivacySettings()


@pytest.fixture
def strict_privacy_settings():
    """Strict privacy settings"""
    from popkit_shared.utils.privacy import PrivacySettings

    return PrivacySettings(anonymization_level="strict", sharing_enabled=False)


# =============================================================================
# Fixtures - XML Test Data
# =============================================================================


@pytest.fixture
def sample_problem_xml():
    """Valid problem context XML for testing"""
    return """
    <problem-context version="1.0">
      <category>bug</category>
      <description>User authentication fails intermittently</description>
      <severity>high</severity>
    </problem-context>
    """


@pytest.fixture
def sample_problem_xml_with_workflow():
    """Problem context XML with workflow"""
    return """
    <problem-context version="1.0">
      <category>feature</category>
      <description>Add dark mode support</description>
      <severity>medium</severity>
      <workflow>
        <step id="1">
          <action>Design UI mockups</action>
          <agent>pop-design</agent>
        </step>
        <step id="2">
          <action>Implement theme switching</action>
          <dependencies>
            <dependency>step1</dependency>
          </dependencies>
        </step>
      </workflow>
    </problem-context>
    """


@pytest.fixture
def sample_project_xml():
    """Valid project context XML for testing"""
    return """
    <project version="1.0">
      <name>popkit-ai</name>
      <stack>
        <technology>Python</technology>
        <technology>TypeScript</technology>
        <technology>Markdown</technology>
      </stack>
      <infrastructure>
        <redis>false</redis>
        <postgres>true</postgres>
        <docker>true</docker>
      </infrastructure>
      <current-work>
        <focus>XML testing strategy</focus>
        <issue>Security hardening</issue>
      </current-work>
    </project>
    """


@pytest.fixture
def sample_findings_xml():
    """Valid findings XML for testing"""
    return """
    <findings version="1.0">
      <tool>Write</tool>
      <status>success</status>
      <quality_score>0.85</quality_score>
      <issues>
        <issue>Missing error handling</issue>
        <issue>Potential security issue</issue>
      </issues>
      <suggestions>
        <suggestion>Add try-catch block</suggestion>
        <suggestion>Run security scan</suggestion>
      </suggestions>
      <followup_agents>
        <agent>security-auditor</agent>
        <agent>test-generator</agent>
      </followup_agents>
    </findings>
    """


@pytest.fixture
def sample_findings_xml_error():
    """Findings XML with error status"""
    return """
    <findings version="1.0">
      <tool>Read</tool>
      <status>error</status>
      <quality_score>0.0</quality_score>
      <error_message>File not found: config.json</error_message>
    </findings>
    """


@pytest.fixture
def invalid_problem_xml():
    """Invalid XML for negative testing"""
    return """
    <problem-context>
      <category>invalid_category</category>
      <severity>ultra-mega-critical</severity>
    </problem-context>
    """


@pytest.fixture
def malformed_xml():
    """Malformed XML for error handling tests"""
    return "<problem-context><category>bug</category>"  # Unclosed tag


@pytest.fixture
def xml_with_html_markers():
    """XML wrapped in HTML comment markers (as used in conversation)"""
    return """
    <!-- XML Context (Invisible) -->
    <problem-context version="1.0">
      <category>bug</category>
      <description>Test issue</description>
      <severity>medium</severity>
    </problem-context>
    <!-- End XML Context -->
    """


# =============================================================================
# Fixtures - Platform Detection Mocks
# =============================================================================


@pytest.fixture
def mock_linux_platform(monkeypatch):
    """Mock Linux platform detection"""
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("SHELL", "/bin/bash")
    yield


@pytest.fixture
def mock_windows_platform(monkeypatch):
    """Mock Windows platform detection"""
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("COMSPEC", "C:\\Windows\\System32\\cmd.exe")
    yield


@pytest.fixture
def mock_macos_platform(monkeypatch):
    """Mock macOS platform detection"""
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setenv("SHELL", "/bin/zsh")
    yield


# =============================================================================
# Utility Functions
# =============================================================================


def create_test_file(directory: Path, filename: str, content: str = "") -> Path:
    """
    Create a test file with content

    Args:
        directory: Directory to create file in
        filename: Name of the file
        content: Content to write to file

    Returns:
        Path to created file
    """
    file_path = directory / filename
    file_path.write_text(content)
    return file_path


def assert_no_sensitive_data(content: str):
    """
    Assert that content contains no sensitive data

    Args:
        content: Content to check

    Raises:
        AssertionError: If sensitive patterns are found
    """
    from popkit_shared.utils.privacy import detect_sensitive_data

    detections = detect_sensitive_data(content)
    assert len(detections) == 0, f"Found sensitive data: {detections}"


# =============================================================================
# Pytest Configuration
# =============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "security: marks tests related to security features")


# =============================================================================
# Pytest Hooks
# =============================================================================


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Add 'unit' marker to all tests by default
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)

        # Add markers based on test file location
        if "test_privacy" in str(item.fspath):
            item.add_marker(pytest.mark.security)

        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
