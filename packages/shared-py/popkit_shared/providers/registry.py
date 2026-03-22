#!/usr/bin/env python3
"""
Provider Registry

Auto-detects installed AI coding tools and provides access to their adapters.
The registry lazily loads adapters and caches detection results.

Part of the PopKit v2.0 provider-agnostic architecture.
"""

from typing import Dict, List, Optional

from .base import ProviderAdapter, ProviderInfo

# Registry of all known provider adapter classes
_ADAPTER_CLASSES: Dict[str, type] = {}
_ADAPTER_INSTANCES: Dict[str, ProviderAdapter] = {}


def _ensure_registered() -> None:
    """Ensure built-in adapters are registered."""
    if _ADAPTER_CLASSES:
        return

    from .claude_code import ClaudeCodeAdapter
    from .generic_mcp import GenericMCPAdapter

    register_adapter(ClaudeCodeAdapter)
    register_adapter(GenericMCPAdapter)


def register_adapter(adapter_class: type) -> None:
    """Register a provider adapter class.

    Args:
        adapter_class: A class that extends ProviderAdapter
    """
    instance = adapter_class()
    _ADAPTER_CLASSES[instance.name] = adapter_class
    _ADAPTER_INSTANCES[instance.name] = instance


def get_adapter(provider_name: str) -> Optional[ProviderAdapter]:
    """Get a provider adapter by name.

    Args:
        provider_name: Provider identifier (e.g., "claude-code")

    Returns:
        ProviderAdapter instance or None if not found
    """
    _ensure_registered()
    return _ADAPTER_INSTANCES.get(provider_name)


def list_adapters() -> List[ProviderAdapter]:
    """List all registered provider adapters.

    Returns:
        List of ProviderAdapter instances
    """
    _ensure_registered()
    return list(_ADAPTER_INSTANCES.values())


def detect_providers() -> List[ProviderInfo]:
    """Auto-detect all installed providers.

    Runs detection for each registered adapter and returns
    information about available providers.

    Returns:
        List of ProviderInfo for detected providers
    """
    _ensure_registered()
    results = []

    for adapter in _ADAPTER_INSTANCES.values():
        try:
            info = adapter.detect()
            if info.is_available:
                results.append(info)
        except Exception:
            # Detection should never crash — skip failed adapters
            continue

    return results


def detect_available_providers() -> Dict[str, ProviderAdapter]:
    """Detect and return only available provider adapters.

    Returns:
        Dict mapping provider name to adapter for available providers
    """
    _ensure_registered()
    available = {}

    for name, adapter in _ADAPTER_INSTANCES.items():
        try:
            info = adapter.detect()
            if info.is_available:
                available[name] = adapter
        except Exception:
            continue

    return available
