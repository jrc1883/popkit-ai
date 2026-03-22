#!/usr/bin/env python3
"""Tests for popkit_shared.providers — provider abstraction layer."""

import os
from pathlib import Path
from unittest.mock import patch

from popkit_shared.providers.base import (
    ProviderInfo,
    ToolCategory,
    ToolMapping,
)
from popkit_shared.providers.claude_code import ClaudeCodeAdapter
from popkit_shared.providers.generic_mcp import GenericMCPAdapter
from popkit_shared.providers.hook_protocol import (
    HookAction,
    HookResponse,
    create_ask,
    create_continue,
    create_deny,
    create_error,
)
from popkit_shared.providers.registry import (
    detect_providers,
    get_adapter,
    list_adapters,
)
from popkit_shared.providers.tool_mapping import (
    get_mappings_for_provider,
    translate_tools,
)

# =============================================================================
# ToolCategory Tests
# =============================================================================


class TestToolCategory:
    """Tests for ToolCategory enum."""

    def test_all_categories_are_strings(self):
        """All categories have string values."""
        for cat in ToolCategory:
            assert isinstance(cat.value, str)

    def test_key_categories_exist(self):
        """Critical categories are defined."""
        assert ToolCategory.FILE_READ.value == "file_read"
        assert ToolCategory.SHELL.value == "shell"
        assert ToolCategory.AGENT_SPAWN.value == "agent_spawn"
        assert ToolCategory.WEB_FETCH.value == "web_fetch"


# =============================================================================
# ToolMapping Tests
# =============================================================================


class TestToolMapping:
    """Tests for tool mapping functions."""

    def test_claude_code_mappings(self):
        """Claude Code has mappings for core categories."""
        mappings = get_mappings_for_provider("claude-code")
        assert len(mappings) > 0

        names = {m.provider_name for m in mappings}
        assert "Read" in names
        assert "Write" in names
        assert "Bash" in names
        assert "Grep" in names
        assert "Agent" in names

    def test_generic_mcp_mappings(self):
        """Generic MCP has popkit/ prefixed tool names."""
        mappings = get_mappings_for_provider("generic-mcp")
        assert len(mappings) > 0
        for m in mappings:
            assert m.provider_name.startswith("popkit/")

    def test_translate_tools_claude_code(self):
        """Translate abstract tools to Claude Code names."""
        result = translate_tools(["file_read", "shell", "web_fetch"], "claude-code")
        assert "Read" in result
        assert "Bash" in result
        assert "WebFetch" in result

    def test_translate_tools_passthrough(self):
        """Unknown tools pass through unchanged."""
        result = translate_tools(["file_read", "CustomTool"], "claude-code")
        assert "Read" in result
        assert "CustomTool" in result

    def test_translate_tools_deduplicates(self):
        """Duplicate mappings are deduplicated."""
        # shell and code_execute both map to Bash in Claude Code
        result = translate_tools(["shell", "code_execute"], "claude-code")
        assert result.count("Bash") == 1

    def test_unknown_provider_returns_empty(self):
        """Unknown provider returns empty mappings list."""
        mappings = get_mappings_for_provider("unknown-tool")
        assert mappings == []


# =============================================================================
# ClaudeCodeAdapter Tests
# =============================================================================


class TestClaudeCodeAdapter:
    """Tests for ClaudeCodeAdapter."""

    def test_name_and_display_name(self):
        adapter = ClaudeCodeAdapter()
        assert adapter.name == "claude-code"
        assert adapter.display_name == "Claude Code"

    def test_detect_returns_provider_info(self):
        adapter = ClaudeCodeAdapter()
        info = adapter.detect()
        assert isinstance(info, ProviderInfo)
        assert info.name == "claude-code"

    def test_tool_mappings(self):
        adapter = ClaudeCodeAdapter()
        mappings = adapter.get_tool_mappings()
        assert len(mappings) > 0
        assert all(isinstance(m, ToolMapping) for m in mappings)

    def test_map_tool(self):
        adapter = ClaudeCodeAdapter()
        mapping = adapter.map_tool(ToolCategory.FILE_READ)
        assert mapping is not None
        assert mapping.provider_name == "Read"

    def test_supports_category(self):
        adapter = ClaudeCodeAdapter()
        assert adapter.supports_category(ToolCategory.FILE_READ)
        assert adapter.supports_category(ToolCategory.SHELL)

    def test_generate_config_empty(self, tmp_path):
        """Claude Code needs no generated config — passthrough."""
        adapter = ClaudeCodeAdapter()
        result = adapter.generate_config(tmp_path, tmp_path / "output")
        assert result == []

    def test_install_creates_symlink(self, tmp_path):
        """Install creates symlink in ~/.claude/plugins/."""
        adapter = ClaudeCodeAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()

        plugins_dir = tmp_path / ".claude" / "plugins"

        with patch.object(Path, "home", return_value=tmp_path):
            result = adapter.install(package_dir)
            assert result is True
            link = plugins_dir / "popkit-core"
            assert link.is_symlink()

    def test_uninstall_removes_symlink(self, tmp_path):
        """Uninstall removes symlink from ~/.claude/plugins/."""
        adapter = ClaudeCodeAdapter()

        plugins_dir = tmp_path / ".claude" / "plugins"
        plugins_dir.mkdir(parents=True)
        link = plugins_dir / "popkit-test"
        link.symlink_to(tmp_path, target_is_directory=True)

        with patch.object(Path, "home", return_value=tmp_path):
            result = adapter.uninstall("popkit-test")
            assert result is True
            assert not link.exists()


# =============================================================================
# GenericMCPAdapter Tests
# =============================================================================


class TestGenericMCPAdapter:
    """Tests for GenericMCPAdapter."""

    def test_name_and_display_name(self):
        adapter = GenericMCPAdapter()
        assert adapter.name == "generic-mcp"
        assert adapter.display_name == "MCP Server (Universal)"

    def test_always_available(self):
        """MCP adapter is always available."""
        adapter = GenericMCPAdapter()
        info = adapter.detect()
        assert info.is_available is True

    def test_generate_config_creates_files(self, tmp_path):
        """Generate config creates mcp-config.json and startup script."""
        adapter = GenericMCPAdapter()
        output_dir = tmp_path / "output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.generate_config(tmp_path / "packages", output_dir)

        assert len(result) == 6  # mcp-config, sh, bat, systemd, launchd, dockerfile
        assert any("mcp-config.json" in str(p) for p in result)
        assert any("start-mcp-server.sh" in str(p) for p in result)
        assert any("start-mcp-server.bat" in str(p) for p in result)
        assert any("popkit-mcp.service" in str(p) for p in result)
        assert any("com.popkit.mcp.plist" in str(p) for p in result)
        assert any("Dockerfile" in str(p) for p in result)

    def test_install_creates_symlink(self, tmp_path):
        """Install creates symlink in POPKIT_HOME/packages/."""
        adapter = GenericMCPAdapter()
        source = tmp_path / "source" / "popkit-core"
        source.mkdir(parents=True)

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.install(source)
            assert result is True
            link = tmp_path / "packages" / "popkit-core"
            assert link.is_symlink()


# =============================================================================
# HookProtocol Tests
# =============================================================================


class TestHookProtocol:
    """Tests for provider-agnostic hook protocol."""

    def test_create_continue(self):
        resp = create_continue("All good")
        assert resp.action == HookAction.CONTINUE
        assert resp.message == "All good"

    def test_create_deny(self):
        resp = create_deny("Not allowed")
        assert resp.action == HookAction.DENY
        assert resp.message == "Not allowed"

    def test_create_ask(self):
        resp = create_ask("Confirm?")
        assert resp.action == HookAction.ASK

    def test_create_error(self):
        resp = create_error("Something broke")
        assert resp.action == HookAction.ERROR
        assert resp.error == "Something broke"

    def test_to_claude_code_format(self):
        """Claude Code format matches expected shape."""
        resp = HookResponse(
            action=HookAction.DENY,
            message="Blocked by policy",
        )
        result = resp.to_claude_code()
        assert result == {"action": "deny", "message": "Blocked by policy"}

    def test_to_generic_format(self):
        """Generic format includes provider and version."""
        resp = create_continue()
        result = resp.to_generic()
        assert result["action"] == "continue"
        assert result["provider"] == "popkit"
        assert result["version"] == "2.0"

    def test_for_provider_routing(self):
        """for_provider routes to correct formatter."""
        resp = create_deny("No")
        cc_result = resp.for_provider("claude-code")
        assert "provider" not in cc_result  # Claude Code format is minimal

        generic_result = resp.for_provider("cursor")
        assert generic_result["provider"] == "popkit"

    def test_modified_input(self):
        """Modified input is included in response."""
        resp = HookResponse(
            action=HookAction.CONTINUE,
            modified_input={"file_path": "/safe/path"},
        )
        cc = resp.to_claude_code()
        assert cc["tool_input"] == {"file_path": "/safe/path"}

        generic = resp.to_generic()
        assert generic["modified_input"] == {"file_path": "/safe/path"}


# =============================================================================
# Registry Tests
# =============================================================================


class TestRegistry:
    """Tests for provider registry."""

    def test_list_adapters(self):
        """Registry has built-in adapters."""
        adapters = list_adapters()
        assert len(adapters) >= 2
        names = {a.name for a in adapters}
        assert "claude-code" in names
        assert "generic-mcp" in names

    def test_get_adapter(self):
        """Can retrieve adapter by name."""
        adapter = get_adapter("claude-code")
        assert adapter is not None
        assert adapter.name == "claude-code"

    def test_get_unknown_adapter(self):
        """Unknown adapter returns None."""
        adapter = get_adapter("nonexistent-tool")
        assert adapter is None

    def test_detect_providers(self):
        """detect_providers returns at least generic-mcp (always available)."""
        providers = detect_providers()
        assert len(providers) >= 1
        names = {p.name for p in providers}
        assert "generic-mcp" in names
