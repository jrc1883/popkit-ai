#!/usr/bin/env python3
"""Tests for dev_provider_resolver.py (Issue #218)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.dev_provider_resolver import (
    DevProvider,
    DevProviderResolver,
    ProviderAvailability,
    ProviderContext,
    detect_feature_dev_plugin,
)


def test_detect_feature_dev_plugin_from_plugin_manifest():
    plugins = [{"name": "feature-dev", "manifest": {"name": "feature-dev"}}]
    assert detect_feature_dev_plugin(plugins=plugins) is True


def test_detect_feature_dev_plugin_false_when_missing():
    plugins = [{"name": "popkit-dev", "manifest": {"name": "popkit-dev"}}]
    assert detect_feature_dev_plugin(plugins=plugins) is False


def test_explicit_upstream_falls_back_when_unavailable():
    resolver = DevProviderResolver()
    context = ProviderContext(requested_provider=DevProvider.FEATURE_DEV)
    availability = ProviderAvailability(feature_dev_available=False)

    decision = resolver.resolve(context, availability=availability)

    assert decision.selected_provider == DevProvider.POPKIT
    assert decision.fallback_from == DevProvider.FEATURE_DEV


def test_auto_prefers_popkit_when_popkit_only_capabilities_are_required():
    resolver = DevProviderResolver()
    context = ProviderContext(
        requested_provider=DevProvider.AUTO,
        required_capabilities={"power_mode"},
    )
    availability = ProviderAvailability(feature_dev_available=True)

    decision = resolver.resolve(context, availability=availability)

    assert decision.selected_provider == DevProvider.POPKIT


def test_auto_prefers_upstream_for_commodity_tasks():
    resolver = DevProviderResolver()
    context = ProviderContext(
        requested_provider=DevProvider.AUTO,
        required_capabilities={"feature_scaffold"},
        complexity=3,
        workflow_mode="quick",
    )
    availability = ProviderAvailability(feature_dev_available=True)

    decision = resolver.resolve(context, availability=availability)

    assert decision.selected_provider == DevProvider.FEATURE_DEV


def test_auto_uses_popkit_when_upstream_is_not_allowed():
    resolver = DevProviderResolver()
    context = ProviderContext(
        requested_provider=DevProvider.AUTO,
        allow_upstream=False,
    )
    availability = ProviderAvailability(feature_dev_available=True)

    decision = resolver.resolve(context, availability=availability)

    assert decision.selected_provider == DevProvider.POPKIT
