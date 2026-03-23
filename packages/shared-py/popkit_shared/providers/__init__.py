"""PopKit Provider Abstraction Layer.

Enables PopKit to integrate with any AI coding tool through a unified adapter interface.
Each provider adapter handles config generation, tool mapping, and installation wiring.

Supported providers:
- claude-code: Native Claude Code plugin (passthrough)
- generic-mcp: Universal MCP server fallback (covers Cursor, Codex, Copilot, etc.)

Usage:
    from popkit_shared.providers import detect_providers, get_adapter

    # Auto-detect installed providers
    providers = detect_providers()

    # Get a specific adapter
    adapter = get_adapter("claude-code")
    adapter.generate_config(package_dir, output_dir)
"""

from .base import ProviderAdapter, ToolCategory, ToolMapping
from .registry import detect_providers, get_adapter, list_adapters

__all__ = [
    "ProviderAdapter",
    "ToolCategory",
    "ToolMapping",
    "detect_providers",
    "get_adapter",
    "list_adapters",
]
