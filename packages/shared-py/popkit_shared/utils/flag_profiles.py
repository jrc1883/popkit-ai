#!/usr/bin/env python3
"""
Flag Profiles System

Maps profile names to flag combinations for PopKit commands.

This module provides a centralized system for managing command flag presets,
reducing cognitive load by grouping common flag combinations into named profiles.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class FlagProfile:
    """Represents a flag profile with its flag settings."""

    name: str
    description: str
    flags: Dict[str, Any]  # flag_name -> value
    use_case: str


class ProfileManager:
    """Manages flag profiles for PopKit commands."""

    # Profile definitions for routine commands
    ROUTINE_PROFILES = {
        "minimal": FlagProfile(
            name="minimal",
            description="Quick health check, skip heavy operations",
            flags={
                "quick": True,
                "skip_tests": True,
                "skip_services": True,
                "skip_deployments": True,
                "simple": True,
            },
            use_case="Fast morning check (< 10 seconds)",
        ),
        "standard": FlagProfile(
            name="standard",
            description="Default behavior, balanced checks",
            flags={},  # All defaults
            use_case="Normal daily routine (~20 seconds)",
        ),
        "thorough": FlagProfile(
            name="thorough",
            description="All checks including optional validations",
            flags={"full": True, "measure": True},
            use_case="Deep analysis with metrics (~60 seconds)",
        ),
        "ci": FlagProfile(
            name="ci",
            description="Optimized for CI/CD environments",
            flags={"optimized": True, "no_cache": True, "measure": True, "simple": True},
            use_case="CI/CD pipelines, JSON output",
        ),
    }

    @classmethod
    def get_profile(cls, profile_name: str, command_type: str = "routine") -> Optional[FlagProfile]:
        """
        Get profile by name for a given command type.

        Args:
            profile_name: Name of the profile to retrieve
            command_type: Type of command (default: 'routine')

        Returns:
            FlagProfile if found, None otherwise

        Example:
            >>> profile = ProfileManager.get_profile('minimal', 'routine')
            >>> print(profile.name)
            minimal
        """
        if command_type == "routine":
            return cls.ROUTINE_PROFILES.get(profile_name)
        return None

    @classmethod
    def list_profiles(cls, command_type: str = "routine") -> List[FlagProfile]:
        """
        List all available profiles for a command type.

        Args:
            command_type: Type of command (default: 'routine')

        Returns:
            List of FlagProfile objects

        Example:
            >>> profiles = ProfileManager.list_profiles('routine')
            >>> len(profiles)
            4
        """
        if command_type == "routine":
            return list(cls.ROUTINE_PROFILES.values())
        return []

    @classmethod
    def apply_profile(
        cls, profile_name: str, current_flags: Dict[str, Any], command_type: str = "routine"
    ) -> Dict[str, Any]:
        """
        Apply a profile to current flags.

        Profile flags are applied first, then overridden by explicit command-line flags.
        This allows users to use profiles as defaults while still customizing specific flags.

        Args:
            profile_name: Name of the profile to apply
            current_flags: Current flag values from command line
            command_type: Type of command (default: 'routine')

        Returns:
            Merged flag dictionary with profile + overrides

        Raises:
            ValueError: If profile_name is not found

        Example:
            >>> flags = {'measure': True}
            >>> merged = ProfileManager.apply_profile('minimal', flags)
            >>> merged['quick']  # From profile
            True
            >>> merged['measure']  # From command line
            True
        """
        profile = cls.get_profile(profile_name, command_type)
        if not profile:
            raise ValueError(f"Unknown profile: {profile_name}")

        # Start with profile flags
        merged = profile.flags.copy()

        # Override with explicit command-line flags
        # Only override if the flag was explicitly set (not just default False)
        for key, value in current_flags.items():
            if value is not None and value is not False:  # Only override if explicitly set
                merged[key] = value

        return merged

    @classmethod
    def apply_smart_defaults(cls, flags: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply smart default implications.

        Smart defaults reduce cognitive load by inferring flag combinations:
        - --measure implies --simple (for parseable output)
        - --full overrides --optimized (thorough checks can't be cached)

        Args:
            flags: Current flag dictionary

        Returns:
            Flag dictionary with smart defaults applied

        Example:
            >>> flags = {'measure': True}
            >>> defaults = ProfileManager.apply_smart_defaults(flags)
            >>> defaults['simple']  # Implied by measure
            True
        """
        # --measure implies --simple for parseable output
        if flags.get("measure") and not flags.get("simple"):
            flags["simple"] = True

        # --full overrides --optimized (can't cache thorough checks)
        if flags.get("full") and flags.get("optimized"):
            flags["optimized"] = False

        return flags
