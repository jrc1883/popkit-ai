#!/usr/bin/env python3
"""Tests for popkit_shared.providers.copilot -- GitHub Copilot provider adapter."""

import json
import os
from pathlib import Path
from unittest.mock import patch

from popkit_shared.providers.base import (
    ProviderInfo,
    ToolCategory,
    ToolMapping,
)
from popkit_shared.providers.copilot import CopilotAdapter
from popkit_shared.providers.registry import get_adapter, list_adapters
from popkit_shared.providers.tool_mapping import COPILOT_MAPPINGS

# =============================================================================
# Detection Tests
# =============================================================================


class TestCopilotDetection:
    """Tests for GitHub Copilot detection logic."""

    def test_name_and_display_name(self):
        adapter = CopilotAdapter()
        assert adapter.name == "copilot"
        assert adapter.display_name == "GitHub Copilot"

    def test_detect_returns_provider_info(self):
        adapter = CopilotAdapter()
        info = adapter.detect()
        assert isinstance(info, ProviderInfo)
        assert info.name == "copilot"

    def test_detect_with_copilot_home_dir(self, tmp_path):
        """Detected as available when ~/.copilot/ exists."""
        adapter = CopilotAdapter()
        copilot_dir = tmp_path / ".copilot"
        copilot_dir.mkdir()

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {}, clear=True),
        ):
            # Clear COPILOT_HOME so it falls back to ~/.copilot
            env = dict(os.environ)
            env.pop("COPILOT_HOME", None)
            with patch.dict(os.environ, env, clear=True):
                info = adapter.detect()
                assert info.is_available is True
                assert info.install_path == copilot_dir

    def test_detect_with_copilot_home_env(self, tmp_path):
        """Detected as available when COPILOT_HOME env var points to existing dir."""
        adapter = CopilotAdapter()
        custom_dir = tmp_path / "custom-copilot"
        custom_dir.mkdir()

        with patch.dict(os.environ, {"COPILOT_HOME": str(custom_dir)}):
            info = adapter.detect()
            assert info.is_available is True
            assert info.install_path == custom_dir

    def test_detect_with_vscode_dir(self, tmp_path, monkeypatch):
        """Detected as available when .vscode/ exists in cwd."""
        adapter = CopilotAdapter()
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()

        monkeypatch.chdir(tmp_path)

        with (
            patch.object(Path, "home", return_value=tmp_path / "empty_home"),
            patch.dict(os.environ, {}, clear=True),
        ):
            env = dict(os.environ)
            env.pop("COPILOT_HOME", None)
            with patch.dict(os.environ, env, clear=True):
                info = adapter.detect()
                assert info.is_available is True

    def test_detect_not_available(self, tmp_path, monkeypatch):
        """Not available when no .copilot/ dir and no .vscode/ dir."""
        adapter = CopilotAdapter()
        monkeypatch.chdir(tmp_path)

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {}, clear=True),
        ):
            env = dict(os.environ)
            env.pop("COPILOT_HOME", None)
            with patch.dict(os.environ, env, clear=True):
                info = adapter.detect()
                assert info.is_available is False
                assert info.install_path is None


# =============================================================================
# Config Generation Tests
# =============================================================================


class TestCopilotConfigGeneration:
    """Tests for Copilot config generation."""

    def test_generate_config_creates_copilot_cli_config(self, tmp_path):
        """Generate config creates mcp-config.json with mcpServers root key."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()
        output_dir = tmp_path / "output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.generate_config(package_dir, output_dir)

        # First file should be the Copilot CLI config
        config_path = result[0]
        assert config_path.name == "mcp-config.json"
        assert config_path.is_file()

        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)

        assert "mcpServers" in config
        assert "popkit" in config["mcpServers"]
        server = config["mcpServers"]["popkit"]
        assert server["type"] == "stdio"
        assert server["command"] == "python3"
        assert server["args"] == ["-m", "popkit_mcp.server"]
        assert "POPKIT_HOME" in server["env"]

    def test_generate_config_creates_vscode_config(self, tmp_path):
        """Generate config creates vscode-mcp.json with servers root key."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()
        output_dir = tmp_path / "output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.generate_config(package_dir, output_dir)

        # Second file should be the VS Code config
        config_path = result[1]
        assert config_path.name == "vscode-mcp.json"
        assert config_path.is_file()

        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)

        # VS Code uses "servers" root key, NOT "mcpServers"
        assert "servers" in config
        assert "mcpServers" not in config
        assert "popkit" in config["servers"]
        server = config["servers"]["popkit"]
        assert server["type"] == "stdio"
        assert server["command"] == "python3"
        assert server["args"] == ["-m", "popkit_mcp.server"]

    def test_copilot_and_vscode_configs_differ_in_root_key(self, tmp_path):
        """The two config formats use different root keys."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()
        output_dir = tmp_path / "output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.generate_config(package_dir, output_dir)

        with open(result[0], encoding="utf-8") as f:
            copilot_config = json.load(f)
        with open(result[1], encoding="utf-8") as f:
            vscode_config = json.load(f)

        # Root keys must be different
        assert "mcpServers" in copilot_config
        assert "servers" not in copilot_config
        assert "servers" in vscode_config
        assert "mcpServers" not in vscode_config

        # But the server entry content should be the same
        copilot_entry = copilot_config["mcpServers"]["popkit"]
        vscode_entry = vscode_config["servers"]["popkit"]
        assert copilot_entry == vscode_entry

    def test_generate_config_creates_copilot_instructions(self, tmp_path):
        """Generate config creates copilot-instructions.md from AGENT.md files."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"
        agents_dir = package_dir / "agents" / "researcher"
        agents_dir.mkdir(parents=True)

        agent_md = agents_dir / "AGENT.md"
        agent_md.write_text("You are a research agent.\n\nDo research tasks.", encoding="utf-8")

        output_dir = tmp_path / "output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.generate_config(package_dir, output_dir)

        # Should have mcp-config.json + vscode-mcp.json + copilot-instructions.md
        assert len(result) == 3
        instructions = [p for p in result if p.name == "copilot-instructions.md"]
        assert len(instructions) == 1

        content = instructions[0].read_text(encoding="utf-8")
        assert "Generated by PopKit" in content
        assert "You are a research agent." in content
        assert "agents/researcher" in content

    def test_generate_config_no_agent_md(self, tmp_path):
        """Generate config with no AGENT.md files produces only JSON configs."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()
        output_dir = tmp_path / "output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.generate_config(package_dir, output_dir)

        # Only the two JSON config files
        assert len(result) == 2
        names = {p.name for p in result}
        assert names == {"mcp-config.json", "vscode-mcp.json"}

    def test_generate_config_multiple_agents(self, tmp_path):
        """Multiple AGENT.md files produce sections in copilot-instructions.md."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"

        for agent_name in ["researcher", "deployer"]:
            agent_dir = package_dir / "agents" / agent_name
            agent_dir.mkdir(parents=True)
            (agent_dir / "AGENT.md").write_text(
                f"You are the {agent_name} agent.", encoding="utf-8"
            )

        output_dir = tmp_path / "output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = adapter.generate_config(package_dir, output_dir)

        instructions = [p for p in result if p.name == "copilot-instructions.md"]
        assert len(instructions) == 1

        content = instructions[0].read_text(encoding="utf-8")
        assert "researcher" in content
        assert "deployer" in content


# =============================================================================
# Tool Mapping Tests
# =============================================================================


class TestCopilotToolMappings:
    """Tests for Copilot tool mappings."""

    def test_tool_mappings_match_copilot_mappings(self):
        """get_tool_mappings returns the COPILOT_MAPPINGS list."""
        adapter = CopilotAdapter()
        mappings = adapter.get_tool_mappings()
        assert mappings is COPILOT_MAPPINGS

    def test_tool_mappings_have_correct_types(self):
        adapter = CopilotAdapter()
        mappings = adapter.get_tool_mappings()
        assert len(mappings) > 0
        assert all(isinstance(m, ToolMapping) for m in mappings)

    def test_file_read_maps_to_read_file(self):
        adapter = CopilotAdapter()
        mapping = adapter.map_tool(ToolCategory.FILE_READ)
        assert mapping is not None
        assert mapping.provider_name == "read_file"

    def test_shell_maps_to_run_terminal_cmd(self):
        adapter = CopilotAdapter()
        mapping = adapter.map_tool(ToolCategory.SHELL)
        assert mapping is not None
        assert mapping.provider_name == "run_terminal_cmd"

    def test_supports_core_categories(self):
        adapter = CopilotAdapter()
        assert adapter.supports_category(ToolCategory.FILE_READ)
        assert adapter.supports_category(ToolCategory.FILE_WRITE)
        assert adapter.supports_category(ToolCategory.FILE_EDIT)
        assert adapter.supports_category(ToolCategory.SHELL)
        assert adapter.supports_category(ToolCategory.CODE_SEARCH)

    def test_no_agent_spawn_support(self):
        """Copilot does not have native agent spawning."""
        adapter = CopilotAdapter()
        assert not adapter.supports_category(ToolCategory.AGENT_SPAWN)


# =============================================================================
# Install / Uninstall Tests
# =============================================================================


class TestCopilotInstallUninstall:
    """Tests for Copilot install/uninstall operations."""

    def test_install_creates_copilot_cli_config(self, tmp_path):
        """Install creates ~/.copilot/mcp-config.json with popkit entry."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}),
        ):
            env = dict(os.environ)
            env.pop("COPILOT_HOME", None)
            env["POPKIT_HOME"] = str(tmp_path)
            with patch.dict(os.environ, env, clear=True):
                result = adapter.install(package_dir)

        assert result is True
        mcp_json = tmp_path / ".copilot" / "mcp-config.json"
        assert mcp_json.is_file()

        with open(mcp_json, encoding="utf-8") as f:
            config = json.load(f)

        assert "mcpServers" in config
        assert "popkit" in config["mcpServers"]
        assert config["mcpServers"]["popkit"]["type"] == "stdio"

    def test_install_creates_vscode_config_when_vscode_exists(self, tmp_path, monkeypatch):
        """Install creates .vscode/mcp.json when .vscode/ dir exists."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()

        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()

        monkeypatch.chdir(tmp_path)

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}),
        ):
            env = dict(os.environ)
            env.pop("COPILOT_HOME", None)
            env["POPKIT_HOME"] = str(tmp_path)
            with patch.dict(os.environ, env, clear=True):
                result = adapter.install(package_dir)

        assert result is True

        vscode_mcp = vscode_dir / "mcp.json"
        assert vscode_mcp.is_file()

        with open(vscode_mcp, encoding="utf-8") as f:
            config = json.load(f)

        # VS Code uses "servers" root key
        assert "servers" in config
        assert "popkit" in config["servers"]

    def test_install_skips_vscode_when_no_vscode_dir(self, tmp_path, monkeypatch):
        """Install does not create .vscode/mcp.json when .vscode/ does not exist."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()

        monkeypatch.chdir(tmp_path)

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}),
        ):
            env = dict(os.environ)
            env.pop("COPILOT_HOME", None)
            env["POPKIT_HOME"] = str(tmp_path)
            with patch.dict(os.environ, env, clear=True):
                result = adapter.install(package_dir)

        assert result is True
        # Copilot CLI config should exist
        assert (tmp_path / ".copilot" / "mcp-config.json").is_file()
        # VS Code config should NOT exist
        assert not (tmp_path / ".vscode" / "mcp.json").exists()

    def test_install_merges_with_existing_copilot_config(self, tmp_path):
        """Install preserves existing MCP server entries in Copilot CLI config."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()

        copilot_dir = tmp_path / ".copilot"
        copilot_dir.mkdir()
        mcp_json = copilot_dir / "mcp-config.json"
        existing = {
            "mcpServers": {
                "other-server": {"type": "stdio", "command": "node", "args": ["server.js"]},
            }
        }
        with open(mcp_json, "w", encoding="utf-8") as f:
            json.dump(existing, f)

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}),
        ):
            env = dict(os.environ)
            env.pop("COPILOT_HOME", None)
            env["POPKIT_HOME"] = str(tmp_path)
            with patch.dict(os.environ, env, clear=True):
                result = adapter.install(package_dir)

        assert result is True

        with open(mcp_json, encoding="utf-8") as f:
            config = json.load(f)

        assert "other-server" in config["mcpServers"]
        assert "popkit" in config["mcpServers"]

    def test_install_merges_with_existing_vscode_config(self, tmp_path, monkeypatch):
        """Install preserves existing entries in .vscode/mcp.json."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()

        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        vscode_mcp = vscode_dir / "mcp.json"
        existing = {
            "servers": {
                "other-tool": {"type": "stdio", "command": "node", "args": ["tool.js"]},
            }
        }
        with open(vscode_mcp, "w", encoding="utf-8") as f:
            json.dump(existing, f)

        monkeypatch.chdir(tmp_path)

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}),
        ):
            env = dict(os.environ)
            env.pop("COPILOT_HOME", None)
            env["POPKIT_HOME"] = str(tmp_path)
            with patch.dict(os.environ, env, clear=True):
                result = adapter.install(package_dir)

        assert result is True

        with open(vscode_mcp, encoding="utf-8") as f:
            config = json.load(f)

        assert "other-tool" in config["servers"]
        assert "popkit" in config["servers"]

    def test_install_handles_malformed_existing_json(self, tmp_path):
        """Install handles corrupted config JSON gracefully."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()

        copilot_dir = tmp_path / ".copilot"
        copilot_dir.mkdir()
        mcp_json = copilot_dir / "mcp-config.json"
        mcp_json.write_text("{invalid json", encoding="utf-8")

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}),
        ):
            env = dict(os.environ)
            env.pop("COPILOT_HOME", None)
            env["POPKIT_HOME"] = str(tmp_path)
            with patch.dict(os.environ, env, clear=True):
                result = adapter.install(package_dir)

        assert result is True

        with open(mcp_json, encoding="utf-8") as f:
            config = json.load(f)

        assert "popkit" in config["mcpServers"]

    def test_uninstall_removes_popkit_from_copilot_config(self, tmp_path):
        """Uninstall removes popkit from ~/.copilot/mcp-config.json."""
        adapter = CopilotAdapter()

        copilot_dir = tmp_path / ".copilot"
        copilot_dir.mkdir()
        mcp_json = copilot_dir / "mcp-config.json"
        config = {
            "mcpServers": {
                "popkit": {
                    "type": "stdio",
                    "command": "python3",
                    "args": ["-m", "popkit_mcp.server"],
                },
                "other-server": {"type": "stdio", "command": "node", "args": ["server.js"]},
            }
        }
        with open(mcp_json, "w", encoding="utf-8") as f:
            json.dump(config, f)

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {}, clear=True),
        ):
            result = adapter.uninstall("popkit")

        assert result is True

        with open(mcp_json, encoding="utf-8") as f:
            config = json.load(f)

        assert "popkit" not in config["mcpServers"]
        assert "other-server" in config["mcpServers"]

    def test_uninstall_removes_popkit_from_vscode_config(self, tmp_path, monkeypatch):
        """Uninstall removes popkit from .vscode/mcp.json."""
        adapter = CopilotAdapter()

        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        vscode_mcp = vscode_dir / "mcp.json"
        config = {
            "servers": {
                "popkit": {
                    "type": "stdio",
                    "command": "python3",
                    "args": ["-m", "popkit_mcp.server"],
                },
                "other-tool": {"type": "stdio", "command": "node", "args": ["tool.js"]},
            }
        }
        with open(vscode_mcp, "w", encoding="utf-8") as f:
            json.dump(config, f)

        monkeypatch.chdir(tmp_path)

        with patch.object(Path, "home", return_value=tmp_path / "empty_home"):
            result = adapter.uninstall("popkit")

        assert result is True

        with open(vscode_mcp, encoding="utf-8") as f:
            config = json.load(f)

        assert "popkit" not in config["servers"]
        assert "other-tool" in config["servers"]

    def test_uninstall_no_config_files(self, tmp_path, monkeypatch):
        """Uninstall returns False when no config files exist."""
        adapter = CopilotAdapter()
        monkeypatch.chdir(tmp_path)

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {}, clear=True),
        ):
            result = adapter.uninstall("popkit")

        assert result is False

    def test_uninstall_no_popkit_entry(self, tmp_path):
        """Uninstall returns False when popkit is not in config."""
        adapter = CopilotAdapter()

        copilot_dir = tmp_path / ".copilot"
        copilot_dir.mkdir()
        mcp_json = copilot_dir / "mcp-config.json"
        with open(mcp_json, "w", encoding="utf-8") as f:
            json.dump({"mcpServers": {}}, f)

        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, {}, clear=True),
        ):
            result = adapter.uninstall("popkit")

        assert result is False


# =============================================================================
# COPILOT_HOME Environment Variable Tests
# =============================================================================


class TestCopilotHomeEnvVar:
    """Tests for COPILOT_HOME environment variable support."""

    def test_copilot_home_overrides_default(self, tmp_path):
        """COPILOT_HOME env var overrides ~/.copilot/ default."""
        adapter = CopilotAdapter()
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()

        with patch.dict(os.environ, {"COPILOT_HOME": str(custom_dir)}):
            copilot_home = adapter._get_copilot_home()
            assert copilot_home == custom_dir

    def test_default_copilot_home(self, tmp_path):
        """Without COPILOT_HOME, falls back to ~/.copilot/."""
        adapter = CopilotAdapter()

        env = dict(os.environ)
        env.pop("COPILOT_HOME", None)
        with (
            patch.object(Path, "home", return_value=tmp_path),
            patch.dict(os.environ, env, clear=True),
        ):
            copilot_home = adapter._get_copilot_home()
            assert copilot_home == tmp_path / ".copilot"

    def test_install_respects_copilot_home(self, tmp_path):
        """Install writes to COPILOT_HOME instead of ~/.copilot/ when set."""
        adapter = CopilotAdapter()
        package_dir = tmp_path / "popkit-core"
        package_dir.mkdir()

        custom_dir = tmp_path / "custom-copilot"

        with patch.dict(
            os.environ,
            {"COPILOT_HOME": str(custom_dir), "POPKIT_HOME": str(tmp_path)},
        ):
            result = adapter.install(package_dir)

        assert result is True
        assert (custom_dir / "mcp-config.json").is_file()
        # Default location should NOT have been written
        assert not (tmp_path / ".copilot" / "mcp-config.json").exists()


# =============================================================================
# Registry Integration Tests
# =============================================================================


class TestCopilotRegistryIntegration:
    """Tests that CopilotAdapter is properly registered."""

    def test_copilot_in_list_adapters(self):
        """Copilot adapter appears in the registry."""
        adapters = list_adapters()
        names = {a.name for a in adapters}
        assert "copilot" in names

    def test_get_copilot_adapter(self):
        """Can retrieve Copilot adapter by name."""
        adapter = get_adapter("copilot")
        assert adapter is not None
        assert adapter.name == "copilot"
        assert isinstance(adapter, CopilotAdapter)
