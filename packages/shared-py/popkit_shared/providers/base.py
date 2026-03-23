#!/usr/bin/env python3
"""
Provider Adapter Base Interface

Defines the abstract interface every provider adapter must implement.
Adapters handle the translation between PopKit's universal manifest format
and provider-specific configuration formats.

Part of the PopKit v2.0 provider-agnostic architecture.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ToolCategory(str, Enum):
    """Abstract tool categories that map to provider-specific tool names.

    These categories are used in popkit-package.yaml to declare capabilities
    without coupling to any specific provider's tool naming.
    """

    # File operations
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_EDIT = "file_edit"
    FILE_SEARCH = "file_search"

    # Code operations
    CODE_SEARCH = "code_search"
    CODE_EXECUTE = "code_execute"

    # Shell operations
    SHELL = "shell"
    SHELL_BACKGROUND = "shell_background"

    # Agent operations
    AGENT_SPAWN = "agent_spawn"
    AGENT_MESSAGE = "agent_message"
    TASK_MANAGE = "task_manage"

    # Web operations
    WEB_FETCH = "web_fetch"
    WEB_SEARCH = "web_search"

    # MCP operations
    MCP_TOOL = "mcp_tool"

    # Notebook operations
    NOTEBOOK_EDIT = "notebook_edit"


@dataclass(frozen=True)
class ToolMapping:
    """Maps an abstract tool category to a provider-specific tool name.

    Attributes:
        category: Abstract tool category
        provider_name: Provider-specific tool name (e.g., "Read", "cat", "file_read")
        provider_args: Default arguments or config for the provider tool
    """

    category: ToolCategory
    provider_name: str
    provider_args: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderInfo:
    """Information about a detected provider.

    Attributes:
        name: Provider identifier (e.g., "claude-code", "cursor")
        display_name: Human-readable name
        version: Detected version (if available)
        install_path: Path to the provider's installation
        is_available: Whether the provider is currently usable
    """

    name: str
    display_name: str
    version: str | None = None
    install_path: Path | None = None
    is_available: bool = True


class ProviderAdapter(ABC):
    """Abstract base class for provider adapters.

    Each adapter handles the translation between PopKit's universal format
    and a specific AI coding tool's configuration and execution model.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'claude-code', 'cursor')."""
        raise NotImplementedError

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""
        raise NotImplementedError

    @abstractmethod
    def detect(self) -> ProviderInfo:
        """Detect if this provider is installed and available.

        Returns:
            ProviderInfo with detection results
        """
        raise NotImplementedError

    @abstractmethod
    def generate_config(self, package_dir: Path, output_dir: Path) -> list[Path]:
        """Generate provider-specific configuration from a PopKit package.

        Reads the package's popkit-package.yaml (or plugin.json) and generates
        the configuration files the provider needs.

        Args:
            package_dir: Path to the PopKit package (contains popkit-package.yaml)
            output_dir: Path to write generated configs (e.g., ~/.popkit/providers/cursor/)

        Returns:
            List of generated file paths
        """
        raise NotImplementedError

    @abstractmethod
    def get_tool_mappings(self) -> list[ToolMapping]:
        """Get this provider's tool name mappings.

        Maps abstract ToolCategory values to provider-specific tool names.

        Returns:
            List of ToolMapping instances
        """
        raise NotImplementedError

    @abstractmethod
    def install(self, package_dir: Path) -> bool:
        """Wire a PopKit package into this provider.

        Creates symlinks, copies configs, or performs whatever integration
        the provider needs to recognize PopKit packages.

        Args:
            package_dir: Path to the PopKit package to install

        Returns:
            True if installation succeeded
        """
        raise NotImplementedError

    @abstractmethod
    def uninstall(self, package_name: str) -> bool:
        """Remove a PopKit package from this provider.

        Removes symlinks, configs, or other integration artifacts.

        Args:
            package_name: Name of the package to uninstall

        Returns:
            True if uninstallation succeeded
        """
        raise NotImplementedError

    def map_tool(self, category: ToolCategory) -> ToolMapping | None:
        """Map an abstract tool category to this provider's tool.

        Args:
            category: Abstract tool category

        Returns:
            ToolMapping if supported, None if not
        """
        for mapping in self.get_tool_mappings():
            if mapping.category == category:
                return mapping
        return None

    def supports_category(self, category: ToolCategory) -> bool:
        """Check if this provider supports a tool category.

        Args:
            category: Abstract tool category

        Returns:
            True if the provider has a mapping for this category
        """
        return self.map_tool(category) is not None
