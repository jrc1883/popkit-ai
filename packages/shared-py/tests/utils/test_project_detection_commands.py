#!/usr/bin/env python3
"""Tests for project detector dependency command selection."""

from popkit_shared.utils.generic_project_detector import GenericProjectDetector
from popkit_shared.utils.project_config import ProjectConfig


def test_python_repo_with_npm_package_manager_uses_npm_outdated():
    """Mixed Python/Node repos should not use `npm show --outdated`."""
    detector = GenericProjectDetector(".")

    project_type = detector._build_project_type(
        "Python",
        "npm",
        "pytest",
        None,
        "ruff",
        "prettier",
    )

    assert project_type.check_installed == "npm list --depth=0"
    assert project_type.check_outdated == "npm outdated"
    assert project_type.install_command == "npm install"


def test_cached_npm_show_outdated_command_is_normalized(tmp_path):
    """Older .popkit/project.json caches should not preserve bad npm commands."""
    config_dir = tmp_path / ".popkit"
    config_dir.mkdir()
    config_path = config_dir / "project.json"
    config_path.write_text(
        """
{
  "version": "1.0",
  "detected_at": "2999-01-01T00:00:00",
  "project_type": {
    "language": "Python",
    "package_manager": "npm",
    "test_framework": "pytest",
    "build_tool": null,
    "linter": "ruff",
    "formatter": "prettier",
    "check_installed": "npm list",
    "check_outdated": "npm show --outdated",
    "install_command": "npm install"
  },
  "auto_detect": true,
  "cache_ttl_hours": 24,
  "overrides": {}
}
""".strip()
    )

    project_type = ProjectConfig(str(tmp_path)).get_cached_project_type()

    assert project_type is not None
    assert project_type.check_installed == "npm list --depth=0"
    assert project_type.check_outdated == "npm outdated"
