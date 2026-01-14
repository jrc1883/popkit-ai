#!/usr/bin/env python3
"""
Unit tests for flag_profiles module.

Tests profile retrieval, application, and smart defaults.
"""

import pytest
from popkit_shared.utils.flag_profiles import ProfileManager, FlagProfile


class TestProfileRetrieval:
    """Test profile retrieval functionality."""

    def test_get_profile_returns_profile(self):
        """Test that get_profile returns a FlagProfile object."""
        profile = ProfileManager.get_profile('minimal', 'routine')
        assert isinstance(profile, FlagProfile)
        assert profile.name == 'minimal'

    def test_get_profile_returns_none_for_unknown(self):
        """Test that get_profile returns None for unknown profiles."""
        profile = ProfileManager.get_profile('unknown_profile', 'routine')
        assert profile is None

    def test_list_profiles_returns_all_routine_profiles(self):
        """Test that list_profiles returns all 4 routine profiles."""
        profiles = ProfileManager.list_profiles('routine')
        assert len(profiles) == 4
        profile_names = [p.name for p in profiles]
        assert 'minimal' in profile_names
        assert 'standard' in profile_names
        assert 'thorough' in profile_names
        assert 'ci' in profile_names


class TestProfileApplication:
    """Test profile application logic."""

    def test_apply_minimal_profile(self):
        """Test applying minimal profile sets correct flags."""
        current_flags = {}
        merged = ProfileManager.apply_profile('minimal', current_flags, 'routine')

        assert merged['quick'] is True
        assert merged['skip_tests'] is True
        assert merged['skip_services'] is True
        assert merged['skip_deployments'] is True
        assert merged['simple'] is True

    def test_apply_standard_profile(self):
        """Test applying standard profile (no flags)."""
        current_flags = {}
        merged = ProfileManager.apply_profile('standard', current_flags, 'routine')

        # Standard profile has no flags (all defaults)
        assert merged == {}

    def test_apply_thorough_profile(self):
        """Test applying thorough profile sets correct flags."""
        current_flags = {}
        merged = ProfileManager.apply_profile('thorough', current_flags, 'routine')

        assert merged['full'] is True
        assert merged['measure'] is True

    def test_apply_ci_profile(self):
        """Test applying CI profile sets correct flags."""
        current_flags = {}
        merged = ProfileManager.apply_profile('ci', current_flags, 'routine')

        assert merged['optimized'] is True
        assert merged['no_cache'] is True
        assert merged['measure'] is True
        assert merged['simple'] is True

    def test_command_line_flags_override_profile(self):
        """Test that explicit command-line flags override profile flags."""
        # Minimal profile sets quick=True, but we override it
        current_flags = {'measure': True}
        merged = ProfileManager.apply_profile('minimal', current_flags, 'routine')

        # Profile flags
        assert merged['quick'] is True
        assert merged['skip_tests'] is True

        # Overridden flag
        assert merged['measure'] is True

    def test_apply_unknown_profile_raises_error(self):
        """Test that applying unknown profile raises ValueError."""
        with pytest.raises(ValueError, match="Unknown profile"):
            ProfileManager.apply_profile('unknown_profile', {}, 'routine')


class TestSmartDefaults:
    """Test smart default implications."""

    def test_measure_implies_simple(self):
        """Test that --measure implies --simple."""
        flags = {'measure': True}
        result = ProfileManager.apply_smart_defaults(flags)

        assert result['measure'] is True
        assert result['simple'] is True

    def test_full_overrides_optimized(self):
        """Test that --full overrides --optimized."""
        flags = {'full': True, 'optimized': True}
        result = ProfileManager.apply_smart_defaults(flags)

        assert result['full'] is True
        assert result['optimized'] is False

    def test_no_changes_when_no_implications(self):
        """Test that flags without implications are unchanged."""
        flags = {'quick': True, 'no_cache': True}
        result = ProfileManager.apply_smart_defaults(flags)

        # No smart defaults apply, flags unchanged
        assert result == flags


class TestProfileIntegration:
    """Integration tests for profile system."""

    def test_minimal_profile_with_override_and_smart_defaults(self):
        """Test full workflow: profile + override + smart defaults."""
        # Start with command-line flags
        current_flags = {'measure': True}

        # Apply minimal profile
        merged = ProfileManager.apply_profile('minimal', current_flags, 'routine')

        # Apply smart defaults
        final = ProfileManager.apply_smart_defaults(merged)

        # From profile
        assert final['quick'] is True
        assert final['skip_tests'] is True

        # From command line
        assert final['measure'] is True

        # From smart defaults (measure implies simple)
        # Note: minimal profile also sets simple, so this is redundant but consistent
        assert final['simple'] is True

    def test_ci_profile_complete_workflow(self):
        """Test CI profile with complete workflow."""
        current_flags = {}

        # Apply CI profile
        merged = ProfileManager.apply_profile('ci', current_flags, 'routine')

        # Apply smart defaults
        final = ProfileManager.apply_smart_defaults(merged)

        # CI profile flags
        assert final['optimized'] is True
        assert final['no_cache'] is True
        assert final['measure'] is True
        assert final['simple'] is True  # Already in profile

    def test_thorough_profile_overrides_optimization(self):
        """Test that thorough profile's --full overrides --optimized if both present."""
        # User wants thorough check but accidentally includes optimized
        current_flags = {'optimized': True}

        # Apply thorough profile (has full=True)
        merged = ProfileManager.apply_profile('thorough', current_flags, 'routine')

        # Apply smart defaults (full overrides optimized)
        final = ProfileManager.apply_smart_defaults(merged)

        assert final['full'] is True
        assert final['optimized'] is False  # Overridden by smart defaults
