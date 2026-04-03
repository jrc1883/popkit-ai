#!/usr/bin/env python3
"""
Project Registration Client

Client for PopKit Cloud project registry API.
Enables cross-project observability and multi-project dashboard.

Part of Issue #93 (Multi-Project Dashboard).
"""

import hashlib
import json
import os
import platform
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .cloud_config import DEFAULT_API_URL, resolve_cloud_config
from .onboarding import (
    OnboardingManager,
    TelemetryMode,
    telemetry_allows_project_identity,
    telemetry_allows_remote,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

POPKIT_API_URL = DEFAULT_API_URL
POPKIT_VERSION = "1.0.0"

# Network timeouts (in seconds)
# Session-start should be fast and non-blocking
DEFAULT_TIMEOUT = 2  # For background operations (session-start, auto-registration)
INTERACTIVE_TIMEOUT = 10  # For user-initiated commands (/popkit:project observe)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class ProjectInfo:
    """Local project information for registration."""

    project_id: str
    name: str | None
    path_hint: str | None
    platform: str = field(default_factory=lambda: platform.system().lower())
    popkit_version: str = POPKIT_VERSION
    health_score: int = 0


@dataclass
class ProjectRegistration:
    """Response from project registration."""

    status: str
    project_id: str
    session_count: int


@dataclass
class ProjectActivity:
    """Activity update for a project."""

    tool_name: str | None = None
    agent_name: str | None = None
    command_name: str | None = None
    health_score: int | None = None
    power_mode_active: bool = False
    power_mode_agents: int = 0


@dataclass
class ProjectSummary:
    """Summary statistics across all projects."""

    total_projects: int
    active_projects_24h: int
    total_tool_calls: int
    total_sessions: int
    avg_health_score: int
    power_mode_active: int


# =============================================================================
# PROJECT CLIENT
# =============================================================================


class ProjectClient:
    """
    Client for PopKit Cloud project registry.

    Features:
    - Project registration on session start
    - Activity tracking for tool calls
    - Cross-project observability
    - Multi-project dashboard support
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        onboarding_manager: OnboardingManager | None = None,
    ):
        """
        Initialize project client.

        Args:
            api_key: PopKit API key (defaults to env var or saved login config)
            api_url: PopKit Cloud API URL (defaults to env var or saved login config)
        """
        resolved_key, resolved_url = resolve_cloud_config()
        self.api_key = api_key or resolved_key
        self.api_url = (api_url or resolved_url).rstrip("/")
        self.onboarding = onboarding_manager or OnboardingManager()
        self._current_project_id: str | None = None

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def register_project(
        self, project_path: str | None = None, name: str | None = None, health_score: int = 0
    ) -> ProjectRegistration | None:
        """
        Register a project with PopKit Cloud.

        Called at session start to track project usage.

        Args:
            project_path: Path to project root (defaults to cwd)
            name: Project name (defaults to directory name or package.json name)
            health_score: Initial health score from morning routine

        Returns:
            ProjectRegistration or None if registration failed
        """
        if not self.is_available:
            return None

        project_path = project_path or os.getcwd()
        project_info = self._get_project_info(project_path, name, health_score)
        request_body = self._build_registration_payload(project_info)

        try:
            response = self._post(
                "/v1/projects/register",
                request_body,
            )

            self._current_project_id = project_info.project_id

            return ProjectRegistration(
                status=response.get("status", "unknown"),
                project_id=response.get("project_id", project_info.project_id),
                session_count=response.get("session_count", 0),
            )

        except Exception:
            return None

    def record_activity(self, activity: ProjectActivity, project_id: str | None = None) -> bool:
        """
        Record activity for a project.

        Called during tool use to track activity.

        Args:
            activity: Activity update
            project_id: Project ID (defaults to current registered project)

        Returns:
            True if activity was recorded
        """
        if not self.is_available:
            return False

        project_id = project_id or self._current_project_id
        if not project_id:
            return False

        body: dict[str, Any] = {}

        if activity.tool_name:
            body["tool_name"] = activity.tool_name
        if activity.agent_name:
            body["agent_name"] = activity.agent_name
        if activity.command_name:
            body["command_name"] = activity.command_name
        if activity.health_score is not None:
            body["health_score"] = activity.health_score
        if activity.power_mode_active:
            body["power_mode"] = {
                "active": activity.power_mode_active,
                "agent_count": activity.power_mode_agents,
            }

        try:
            self._post(f"/v1/projects/{project_id}/activity", body)
            return True
        except Exception:
            return False

    def list_projects(self, active_only: bool = False) -> list[dict[str, Any]]:
        """
        List all registered projects.

        Args:
            active_only: Only return projects active in last 24h

        Returns:
            List of project info dicts
        """
        if not self.api_key:
            return []

        try:
            params = "?active_only=true" if active_only else ""
            # User-initiated command - can wait longer
            response = self._get(f"/v1/projects{params}", timeout=INTERACTIVE_TIMEOUT)
            return response.get("projects", [])
        except Exception:
            return []

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        """
        Get details for a specific project.

        Args:
            project_id: Project ID

        Returns:
            Project info dict or None
        """
        if not self.api_key:
            return None

        try:
            return self._get(f"/v1/projects/{project_id}")
        except Exception:
            return None

    def get_summary(self) -> ProjectSummary | None:
        """
        Get summary statistics across all projects.

        Returns:
            ProjectSummary or None if unavailable
        """
        if not self.api_key:
            return None

        try:
            # User-initiated command - can wait longer
            response = self._get("/v1/projects/summary", timeout=INTERACTIVE_TIMEOUT)
            return ProjectSummary(
                total_projects=response.get("total_projects", 0),
                active_projects_24h=response.get("active_projects_24h", 0),
                total_tool_calls=response.get("total_tool_calls", 0),
                total_sessions=response.get("total_sessions", 0),
                avg_health_score=response.get("avg_health_score", 0),
                power_mode_active=response.get("power_mode_active", 0),
            )
        except Exception:
            return None

    def unregister_project(self, project_id: str) -> bool:
        """
        Unregister a project.

        Args:
            project_id: Project ID to unregister

        Returns:
            True if unregistered successfully
        """
        if not self.api_key:
            return False

        try:
            self._delete(f"/v1/projects/{project_id}")
            if self._current_project_id == project_id:
                self._current_project_id = None
            return True
        except Exception:
            return False

    # =========================================================================
    # PROPERTIES
    # =========================================================================

    @property
    def is_available(self) -> bool:
        """Check if remote telemetry is configured and enabled."""
        return bool(self.api_key) and telemetry_allows_remote(self.telemetry_mode)

    @property
    def current_project_id(self) -> str | None:
        """Get the current registered project ID."""
        return self._current_project_id

    @property
    def telemetry_mode(self) -> TelemetryMode:
        """Get the current machine-level telemetry mode."""
        return self.onboarding.get_telemetry_mode()

    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================

    def _get_project_info(
        self, project_path: str, name: str | None, health_score: int
    ) -> ProjectInfo:
        """Extract project information from path."""
        path = Path(project_path).resolve()

        # Generate project ID from absolute path
        project_id = hashlib.sha256(str(path).encode()).hexdigest()[:16]

        # Get project name
        if not name:
            # Try package.json
            package_json = path / "package.json"
            if package_json.exists():
                try:
                    with open(package_json) as f:
                        pkg = json.load(f)
                        name = pkg.get("name", "")
                except Exception:
                    # Best-effort fallback: ignore optional failure.
                    pass

            # Fallback to directory name
            if not name:
                name = path.name

        # Create anonymized path hint (last 2 segments)
        path_parts = path.parts
        if len(path_parts) >= 2:
            path_hint = f".../{'/'.join(path_parts[-2:])}"
        else:
            path_hint = f".../{path.name}"

        return ProjectInfo(
            project_id=project_id, name=name, path_hint=path_hint, health_score=health_score
        )

    def _build_registration_payload(self, project_info: ProjectInfo) -> dict[str, Any]:
        """Build the registration payload for the current telemetry mode."""
        body: dict[str, Any] = {
            "project_id": project_info.project_id,
            "health_score": project_info.health_score,
            "popkit_version": project_info.popkit_version,
            "platform": project_info.platform,
        }

        if telemetry_allows_project_identity(self.telemetry_mode):
            if project_info.name is not None:
                body["name"] = project_info.name
            if project_info.path_hint is not None:
                body["path_hint"] = project_info.path_hint

        return body

    def _get(self, endpoint: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
        """Make GET request to API."""
        return self._request("GET", endpoint, timeout=timeout)

    def _post(
        self, endpoint: str, body: dict[str, Any], timeout: int = DEFAULT_TIMEOUT
    ) -> dict[str, Any]:
        """Make POST request to API."""
        return self._request("POST", endpoint, body, timeout=timeout)

    def _delete(self, endpoint: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
        """Make DELETE request to API."""
        return self._request("DELETE", endpoint, timeout=timeout)

    def _request(
        self,
        method: str,
        endpoint: str,
        body: dict[str, Any] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            body: Request body (JSON-serializable)
            timeout: Request timeout in seconds (default: 2s for background ops)
        """
        url = f"{self.api_url}{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-PopKit-Version": POPKIT_VERSION,
        }

        data = json.dumps(body).encode("utf-8") if body else None

        request = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"API error {e.code}: {e.reason}\n{body_text}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

_client: ProjectClient | None = None


def get_client() -> ProjectClient:
    """Get or create the singleton project client."""
    global _client
    if _client is None:
        _client = ProjectClient()
    return _client


def register_project(
    project_path: str | None = None, name: str | None = None, health_score: int = 0
) -> ProjectRegistration | None:
    """Convenience function to register a project."""
    return get_client().register_project(project_path, name, health_score)


def record_activity(activity: ProjectActivity) -> bool:
    """Convenience function to record activity."""
    return get_client().record_activity(activity)


def list_projects(active_only: bool = False) -> list[dict[str, Any]]:
    """Convenience function to list projects."""
    return get_client().list_projects(active_only)


def get_summary() -> ProjectSummary | None:
    """Convenience function to get summary."""
    return get_client().get_summary()


def is_available() -> bool:
    """Check if project tracking is available."""
    return get_client().is_available


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys

    print("Project Client Test")
    print("=" * 40)

    client = ProjectClient()

    if not client.is_available:
        print("ERROR: POPKIT_API_KEY not set")
        print("Set: export POPKIT_API_KEY=your-key-here")
        sys.exit(1)

    print("API Key: [REDACTED]")
    print(f"API URL: {client.api_url}")

    # Test project registration
    print("\nTesting project registration...")
    result = client.register_project()
    if result:
        print(f"Status: {result.status}")
        print(f"Project ID: {result.project_id}")
        print(f"Session Count: {result.session_count}")
    else:
        print("Registration failed")

    # Test activity recording
    print("\nTesting activity recording...")
    success = client.record_activity(ProjectActivity(tool_name="Read", agent_name="code-reviewer"))
    print(f"Activity recorded: {success}")

    # Test listing projects
    print("\nTesting project listing...")
    projects = client.list_projects()
    print(f"Found {len(projects)} projects")
    for proj in projects[:3]:
        print(f"  - {proj.get('name', 'Unknown')}: {proj.get('last_active', 'never')}")

    # Test summary
    print("\nTesting summary...")
    summary = client.get_summary()
    if summary:
        print(f"Total projects: {summary.total_projects}")
        print(f"Active (24h): {summary.active_projects_24h}")
        print(f"Total tool calls: {summary.total_tool_calls}")
        print(f"Avg health score: {summary.avg_health_score}")
    else:
        print("Summary unavailable")

    print("\nAll tests completed!")
