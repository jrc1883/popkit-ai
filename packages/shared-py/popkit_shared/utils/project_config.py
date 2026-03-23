#!/usr/bin/env python3
"""
Project Configuration Manager

Handles .popkit/project.json caching and configuration for project detection.
Provides smart caching to avoid expensive re-detection on every routine run.

Issue #69: Generic Workspace Routine Templates - Caching & Configuration
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from .generic_project_detector import ProjectType

    HAS_PROJECT_DETECTOR = True
except ImportError:
    HAS_PROJECT_DETECTOR = False
    ProjectType = None


class ProjectConfig:
    """Manages project configuration and caching."""

    CONFIG_VERSION = "1.0"
    DEFAULT_TTL_HOURS = 24
    CONFIG_FILENAME = ".popkit/project.json"

    def __init__(self, project_path: str = "."):
        """
        Initialize project config manager.

        Args:
            project_path: Path to project root directory
        """
        self.project_path = Path(project_path).resolve()
        self.config_file = self.project_path / self.CONFIG_FILENAME

    def load(self) -> dict[str, Any] | None:
        """
        Load project configuration from disk.

        Returns:
            Configuration dict or None if not found or invalid
        """
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, encoding="utf-8") as f:
                config = json.load(f)

            # Validate version
            if config.get("version") != self.CONFIG_VERSION:
                print("[WARN] Config version mismatch, ignoring cache")
                return None

            return config

        except (OSError, json.JSONDecodeError) as e:
            print(f"[WARN] Failed to load project config: {e}")
            return None

    def save(self, config: dict[str, Any]) -> bool:
        """
        Save project configuration to disk.

        Args:
            config: Configuration dictionary to save

        Returns:
            True if saved successfully
        """
        try:
            # Ensure .popkit directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Add metadata
            config["version"] = self.CONFIG_VERSION
            config["updated_at"] = datetime.now().isoformat()

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True

        except (OSError, Exception) as e:
            print(f"[ERROR] Failed to save project config: {e}")
            return False

    def is_cache_valid(self, config: dict[str, Any] | None = None) -> bool:
        """
        Check if cached configuration is still valid.

        Args:
            config: Configuration to check (loads from disk if not provided)

        Returns:
            True if cache is valid and can be used
        """
        if config is None:
            config = self.load()

        if not config:
            return False

        # Check if auto-detect is disabled (use cache regardless of age)
        if not config.get("auto_detect", True):
            return True

        # Check cache age
        detected_at = config.get("detected_at")
        if not detected_at:
            return False

        try:
            detected_time = datetime.fromisoformat(detected_at)
            ttl_hours = config.get("cache_ttl_hours", self.DEFAULT_TTL_HOURS)
            expiry_time = detected_time + timedelta(hours=ttl_hours)

            return datetime.now() < expiry_time

        except (ValueError, TypeError):
            return False

    def get_cached_project_type(self) -> ProjectType | None:
        """
        Get cached project type if valid.

        Returns:
            ProjectType from cache or None if cache invalid/missing
        """
        if not HAS_PROJECT_DETECTOR:
            return None

        config = self.load()
        if not config or not self.is_cache_valid(config):
            return None

        # Build ProjectType from cache
        project_type_data = config.get("project_type", {})
        overrides = config.get("overrides", {})

        # Merge overrides into project type
        merged = {**project_type_data, **overrides}

        try:
            return ProjectType(
                primary_language=merged.get("language", "Unknown"),
                package_manager=merged.get("package_manager"),
                test_framework=merged.get("test_framework"),
                build_tool=merged.get("build_tool"),
                linter=merged.get("linter"),
                formatter=merged.get("formatter"),
                expected_services=merged.get("expected_services"),
                check_installed=merged.get("check_installed"),
                check_outdated=merged.get("check_outdated"),
                install_command=merged.get("install_command"),
            )
        except TypeError as e:
            print(f"[WARN] Failed to build ProjectType from cache: {e}")
            return None

    def cache_project_type(self, project_type: ProjectType) -> bool:
        """
        Cache detected project type to disk.

        Args:
            project_type: Detected ProjectType to cache

        Returns:
            True if cached successfully
        """
        config = self.load() or {}

        # Update project type data
        config["detected_at"] = datetime.now().isoformat()
        config["project_type"] = {
            "language": project_type.primary_language,
            "package_manager": project_type.package_manager,
            "test_framework": project_type.test_framework,
            "build_tool": project_type.build_tool,
            "linter": project_type.linter,
            "formatter": project_type.formatter,
        }

        # Preserve overrides and settings
        config.setdefault("auto_detect", True)
        config.setdefault("cache_ttl_hours", self.DEFAULT_TTL_HOURS)
        config.setdefault("overrides", {})

        # Only cache expected_services if not overridden
        if "expected_services" not in config["overrides"]:
            if project_type.expected_services:
                config["project_type"]["expected_services"] = project_type.expected_services

        # Only cache check commands if not overridden
        for field in ["check_installed", "check_outdated", "install_command"]:
            if field not in config["overrides"]:
                value = getattr(project_type, field, None)
                if value:
                    config["project_type"][field] = value

        return self.save(config)

    def update_overrides(self, overrides: dict[str, Any]) -> bool:
        """
        Update configuration overrides.

        Args:
            overrides: Dictionary of fields to override

        Returns:
            True if updated successfully
        """
        config = self.load() or {}

        # Merge new overrides
        current_overrides = config.get("overrides", {})
        current_overrides.update(overrides)
        config["overrides"] = current_overrides

        return self.save(config)

    def get_override(self, field: str) -> Any | None:
        """
        Get a specific override value.

        Args:
            field: Field name to get override for

        Returns:
            Override value or None if not set
        """
        config = self.load()
        if not config:
            return None

        return config.get("overrides", {}).get(field)

    def clear_cache(self) -> bool:
        """
        Clear cached project detection.

        Returns:
            True if cleared successfully
        """
        config = self.load()
        if not config:
            return True

        # Remove detected data but keep overrides
        config.pop("detected_at", None)
        config.pop("project_type", None)

        return self.save(config)


def get_project_type_with_cache(
    project_path: str = ".", force_refresh: bool = False
) -> ProjectType | None:
    """
    Get project type with smart caching.

    Flow:
    1. Check .popkit/project.json cache
    2. If cache valid and not force_refresh, use cache
    3. If cache invalid or force_refresh, detect fresh
    4. If detection fails, fall back to cache
    5. Save fresh detection to cache

    Args:
        project_path: Path to project directory
        force_refresh: Force fresh detection even if cache valid

    Returns:
        ProjectType or None if detection failed
    """
    if not HAS_PROJECT_DETECTOR:
        return None

    config_manager = ProjectConfig(project_path)

    # Try cache first (unless force refresh)
    if not force_refresh:
        cached = config_manager.get_cached_project_type()
        if cached:
            return cached

    # Perform fresh detection
    from .generic_project_detector import GenericProjectDetector

    detector = GenericProjectDetector(project_path)

    try:
        project_type = detector.detect()

        # Cache the fresh detection
        config_manager.cache_project_type(project_type)

        return project_type

    except Exception as e:
        print(f"[ERROR] Project detection failed: {e}")

        # Fall back to cache even if expired
        config = config_manager.load()
        if config:
            return config_manager.get_cached_project_type()

        # Last resort: return None
        return None
