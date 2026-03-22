#!/usr/bin/env python3
"""Tests for popkit_shared.providers.codex — Codex CLI provider adapter."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

from popkit_shared.providers.base import (
    ProviderInfo,
    ToolCategory,
    ToolMapping,
)
from popkit_shared.providers.codex import CodexAdapter, _format_toml_value, _serialize_toml
from popkit_shared.providers.registry import get_adapter, list_adapters
from popkit_shared.providers.tool_mapping import CODEX_MAPPINGS

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib  # type: ignore[import-not-found]
    except ImportError:
        import tomli as tomllib  # type: ignore[import-not-found, no-redef]

# =============================================================================
# TOML Serialization Tests
# =============================================================================


class TestTomlSerialization:
    """Tests for TOML serialization helpers."""

    def test_format_string(self):
        assert _format_toml_value("hello") == '"hello"'

    def test_format_string_with_quotes(self):
        assert _format_toml_value('say "hi"') == '"say \\"hi\\""'

    def test_format_string_with_backslash(self):
        assert _format_toml_value("C:\\Users") == '"C:\\\\Users"'

    def test_format_bool(self):
        assert _format_toml_value(True) == "true"
        assert _format_toml_value(False) == "false"

    def test_format_int(self):
        assert _format_toml_value(42) == "42"

    def test_format_list(self):
        assert _format_toml_value(["a", "b"]) == '["a", "b"]'

    def test_format_dict(self):
        result = _format_toml_value({"key": "val"})
        assert result == '{key = "val"}'

    def test_serialize_simple_table(self):
        data = {"mcp_servers": {"popkit": {"command": "python3", "enabled": True}}}
        result = _serialize_toml(data)
        assert "[mcp_servers.popkit]" in result
        assert 'command = "python3"' in result
        assert "enabled = true" in result

    def test_serialize_roundtrip(self):
        """TOML we generate can be parsed back by tomllib."""
        data = {
            "mcp_servers": {
                "popkit": {
                    "command": "python3",
                    "args": ["-m", "popkit_mcp.server"],
                    "env": {"POPKIT_HOME": "/tmp/popkit"},
                    "startup_timeout_sec": 30,
                    "tool_timeout_sec": 120,
                    "enabled": True,
                }
            }
        }
        toml_str = _serialize_toml(data)
        parsed = tomllib.loads(toml_str)
        assert parsed["mcp_servers"]["popkit"]["command"] == "python3"
        assert parsed["mcp_servers"]["popkit"]["args"] == ["-m", "popkit_mcp.server"]
        assert parsed["mcp_servers"]["popkit"]["startup_timeout_sec"] == 30
        assert parsed["mcp_servers"]["popkit"]["enabled"] is True


# =============================================================================
# Detection Tests
# =============================================================================


class TestCodexDetection:
    """Tests for Codex CLI detection logic."""

    def test_name_and_display_name(self):
        adapter = CodexAdapter()
        assert adapter.name == "codex"
        assert adapter.display_name == "Codex CLI"

    def test_detect_returns_provider_info(self):
        adapter = CodexAdapter()
        info = adapter.detect()
        assert isinstance(info, ProviderInfo)
        assert info.name == "codex"

    def test_detect_with_home_dir(self, tmp_path):
        """Detected as available when ~/.codex/ exists."""
        adapter = CodexAdapter()
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()

        with patch.object(Path, "home", return_value=tmp_path):
            info = adapter.detect()
            assert info.is_available is True
            assert info.install_path == codex_dir

    def test_detect_without_codex(self, tmp_path):
        """Not available when no .codex/ dir and no binary."""
        adapter = CodexAdapter()

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch("popkit_shared.providers.codex.shutil.which", return_value=None),
        ):
            info = adapter.detect()
            assert info.is_available is False
            assert info.install_path is None

    def test_detect_with_binary_on_path(self, tmp_path):
        """Detected as available when codex binary is on PATH."""
        adapter = CodexAdapter()

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch("popkit_shared.providers.codex.shutil.which", return_value="/usr/bin/codex"),
        ):
            info = adapter.detect()
            assert info.is_available is True


# =============================================================================
# Config Generation Tests
# =============================================================================


class TestCodexConfigGeneration:
    """Tests for Codex config generation."""

    def test_generate_config_creates_toml(self, tmp_path):
        """Generate config creates a valid config.toml."""
        adapter = CodexAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()
        output_dir = tmp_path / "output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.generate_config(package_dir, output_dir)

        assert len(result) >= 1
        config_path = result[0]
        assert config_path.name == "config.toml"
        assert config_path.is_file()

        content = config_path.read_text(encoding="utf-8")
        assert "[mcp_servers.popkit]" in content
        assert 'command = "python3"' in content
        assert "startup_timeout_sec = 30" in content
        assert "enabled = true" in content

    def test_generate_config_toml_is_parseable(self, tmp_path):
        """Generated TOML can be parsed by tomllib."""
        adapter = CodexAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()
        output_dir = tmp_path / "output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.generate_config(package_dir, output_dir)

        config_path = result[0]
        with open(config_path, "rb") as f:
            parsed = tomllib.loads(f.read().decode("utf-8"))

        assert "mcp_servers" in parsed
        assert "popkit" in parsed["mcp_servers"]
        server = parsed["mcp_servers"]["popkit"]
        assert server["command"] == "python3"
        assert server["args"] == ["-m", "popkit_mcp.server"]

    def test_generate_config_creates_agents_md(self, tmp_path):
        """Generate config creates AGENTS.md from AGENT.md files."""
        adapter = CodexAdapter()
        package_dir = tmp_path / "popkit-core"
        agents_dir = package_dir / "agents" / "researcher"
        agents_dir.mkdir(parents=True)

        agent_md = agents_dir / "AGENT.md"
        agent_md.write_text(
            "# Research Agent\n\nYou are a research agent.\n\nDo research tasks.",
            encoding="utf-8",
        )

        output_dir = tmp_path / "output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.generate_config(package_dir, output_dir)

        # Should have config.toml + AGENTS.md
        assert len(result) == 2
        agents_files = [p for p in result if p.name == "AGENTS.md"]
        assert len(agents_files) == 1

        content = agents_files[0].read_text(encoding="utf-8")
        assert "PopKit Agents" in content
        assert "agents/researcher" in content
        assert "Research Agent" in content
        assert "Do research tasks." in content

    def test_generate_config_no_agent_md(self, tmp_path):
        """Generate config with no AGENT.md files produces only config.toml."""
        adapter = CodexAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()
        output_dir = tmp_path / "output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.generate_config(package_dir, output_dir)

        assert len(result) == 1
        assert result[0].name == "config.toml"

    def test_agents_md_multiple_agents(self, tmp_path):
        """AGENTS.md includes all agents from the package."""
        adapter = CodexAdapter()
        package_dir = tmp_path / "popkit-core"

        for agent_name in ["coder", "reviewer", "deployer"]:
            agent_dir = package_dir / "agents" / agent_name
            agent_dir.mkdir(parents=True)
            (agent_dir / "AGENT.md").write_text(
                f"# {agent_name.title()} Agent\n\nHandles {agent_name} tasks.",
                encoding="utf-8",
            )

        output_dir = tmp_path / "output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.generate_config(package_dir, output_dir)

        agents_md = [p for p in result if p.name == "AGENTS.md"]
        assert len(agents_md) == 1
        content = agents_md[0].read_text(encoding="utf-8")
        assert "agents/coder" in content
        assert "agents/reviewer" in content
        assert "agents/deployer" in content


# =============================================================================
# Tool Mapping Tests
# =============================================================================


class TestCodexToolMappings:
    """Tests for Codex CLI tool mappings."""

    def test_tool_mappings_match_codex_mappings(self):
        """get_tool_mappings returns the CODEX_MAPPINGS list."""
        adapter = CodexAdapter()
        mappings = adapter.get_tool_mappings()
        assert mappings is CODEX_MAPPINGS

    def test_tool_mappings_have_correct_types(self):
        adapter = CodexAdapter()
        mappings = adapter.get_tool_mappings()
        assert len(mappings) > 0
        assert all(isinstance(m, ToolMapping) for m in mappings)

    def test_file_read_maps_to_read(self):
        adapter = CodexAdapter()
        mapping = adapter.map_tool(ToolCategory.FILE_READ)
        assert mapping is not None
        assert mapping.provider_name == "Read"

    def test_shell_maps_to_bash(self):
        adapter = CodexAdapter()
        mapping = adapter.map_tool(ToolCategory.SHELL)
        assert mapping is not None
        assert mapping.provider_name == "Bash"

    def test_code_search_maps_to_grep(self):
        adapter = CodexAdapter()
        mapping = adapter.map_tool(ToolCategory.CODE_SEARCH)
        assert mapping is not None
        assert mapping.provider_name == "Grep"

    def test_file_search_maps_to_glob(self):
        adapter = CodexAdapter()
        mapping = adapter.map_tool(ToolCategory.FILE_SEARCH)
        assert mapping is not None
        assert mapping.provider_name == "Glob"

    def test_supports_core_categories(self):
        adapter = CodexAdapter()
        assert adapter.supports_category(ToolCategory.FILE_READ)
        assert adapter.supports_category(ToolCategory.FILE_WRITE)
        assert adapter.supports_category(ToolCategory.FILE_EDIT)
        assert adapter.supports_category(ToolCategory.SHELL)
        assert adapter.supports_category(ToolCategory.CODE_SEARCH)
        assert adapter.supports_category(ToolCategory.CODE_EXECUTE)

    def test_no_agent_spawn_support(self):
        """Codex CLI does not have native agent spawning."""
        adapter = CodexAdapter()
        assert not adapter.supports_category(ToolCategory.AGENT_SPAWN)

    def test_no_notebook_support(self):
        """Codex CLI does not have native notebook editing."""
        adapter = CodexAdapter()
        assert not adapter.supports_category(ToolCategory.NOTEBOOK_EDIT)


# =============================================================================
# Install / Uninstall Tests
# =============================================================================


class TestCodexInstallUninstall:
    """Tests for Codex CLI install/uninstall operations."""

    def test_install_creates_config_toml(self, tmp_path):
        """Install creates ~/.codex/config.toml with popkit entry."""
        adapter = CodexAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}),
        ):
            result = adapter.install(package_dir)

        assert result is True
        config_toml = tmp_path / ".codex" / "config.toml"
        assert config_toml.is_file()

        with open(config_toml, "rb") as f:
            config = tomllib.loads(f.read().decode("utf-8"))

        assert "mcp_servers" in config
        assert "popkit" in config["mcp_servers"]
        assert config["mcp_servers"]["popkit"]["command"] == "python3"

    def test_install_merges_with_existing(self, tmp_path):
        """Install preserves existing MCP server entries."""
        adapter = CodexAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()

        # Create existing config.toml with another server
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        config_toml = codex_dir / "config.toml"
        config_toml.write_text(
            '[mcp_servers.other-server]\ncommand = "node"\nargs = ["server.js"]\n',
            encoding="utf-8",
        )

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}),
        ):
            result = adapter.install(package_dir)

        assert result is True

        with open(config_toml, "rb") as f:
            config = tomllib.loads(f.read().decode("utf-8"))

        # Both entries should exist
        assert "other-server" in config["mcp_servers"]
        assert "popkit" in config["mcp_servers"]

    def test_install_handles_malformed_existing_toml(self, tmp_path):
        """Install handles corrupted config.toml gracefully."""
        adapter = CodexAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()

        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        config_toml = codex_dir / "config.toml"
        config_toml.write_text("{invalid toml [[[", encoding="utf-8")

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}),
        ):
            result = adapter.install(package_dir)

        assert result is True

        with open(config_toml, "rb") as f:
            config = tomllib.loads(f.read().decode("utf-8"))

        assert "popkit" in config["mcp_servers"]

    def test_install_updates_existing_popkit_entry(self, tmp_path):
        """Install overwrites an existing popkit entry."""
        adapter = CodexAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()

        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        config_toml = codex_dir / "config.toml"
        config_toml.write_text(
            '[mcp_servers.popkit]\ncommand = "old-python"\nargs = ["old"]\n',
            encoding="utf-8",
        )

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}),
        ):
            result = adapter.install(package_dir)

        assert result is True

        with open(config_toml, "rb") as f:
            config = tomllib.loads(f.read().decode("utf-8"))

        assert config["mcp_servers"]["popkit"]["command"] == "python3"

    def test_uninstall_removes_popkit_entry(self, tmp_path):
        """Uninstall removes popkit from config.toml."""
        adapter = CodexAdapter()

        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        config_toml = codex_dir / "config.toml"
        config_toml.write_text(
            '[mcp_servers.popkit]\ncommand = "python3"\nargs = ["-m", "popkit_mcp.server"]\n\n'
            '[mcp_servers.other-server]\ncommand = "node"\nargs = ["server.js"]\n',
            encoding="utf-8",
        )

        with patch.object(Path, "home", return_value=tmp_path):
            result = adapter.uninstall("popkit")

        assert result is True

        with open(config_toml, "rb") as f:
            config = tomllib.loads(f.read().decode("utf-8"))

        assert "popkit" not in config["mcp_servers"]
        assert "other-server" in config["mcp_servers"]

    def test_uninstall_no_config_toml(self, tmp_path):
        """Uninstall returns False when no config.toml exists."""
        adapter = CodexAdapter()

        with patch.object(Path, "home", return_value=tmp_path):
            result = adapter.uninstall("popkit")

        assert result is False

    def test_uninstall_no_popkit_entry(self, tmp_path):
        """Uninstall returns False when popkit is not in config.toml."""
        adapter = CodexAdapter()

        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        config_toml = codex_dir / "config.toml"
        config_toml.write_text("[mcp_servers]\n", encoding="utf-8")

        with patch.object(Path, "home", return_value=tmp_path):
            result = adapter.uninstall("popkit")

        assert result is False


# =============================================================================
# Registry Integration Tests
# =============================================================================


class TestCodexRegistryIntegration:
    """Tests that CodexAdapter is properly registered."""

    def test_codex_in_list_adapters(self):
        """Codex adapter appears in the registry."""
        adapters = list_adapters()
        names = {a.name for a in adapters}
        assert "codex" in names

    def test_get_codex_adapter(self):
        """Can retrieve Codex adapter by name."""
        adapter = get_adapter("codex")
        assert adapter is not None
        assert adapter.name == "codex"
        assert isinstance(adapter, CodexAdapter)
