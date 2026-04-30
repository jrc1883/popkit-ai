#!/usr/bin/env python3
"""End-to-end integration tests for the PopKit MCP + provider flow.

Tests the full workflow:
1. Scan real packages → build registry
2. Create MCP server with real packages
3. All provider adapters detect/generate/install correctly
4. MCP tools return valid content from real skills/agents
5. Provider wiring produces correct configs for each tool
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add popkit-mcp to path
MCP_PKG = Path(__file__).parent.parent.parent / "popkit-mcp"
if str(MCP_PKG) not in sys.path:
    sys.path.insert(0, str(MCP_PKG))

PACKAGES_DIR = Path(__file__).parent.parent.parent
HAS_REAL_PACKAGES = (PACKAGES_DIR / "popkit-core").is_dir()


@pytest.mark.skipif(not HAS_REAL_PACKAGES, reason="Real packages not available")
class TestEndToEndRegistryToServer:
    """Test: packages → registry → server tools."""

    def test_registry_scans_all_packages(self):
        """Registry finds all skills, agents, commands from real packages."""
        from popkit_mcp.tool_registry import build_registry

        registry = build_registry(PACKAGES_DIR)
        assert registry["counts"]["skills"] >= 50
        assert registry["counts"]["agents"] >= 24
        assert registry["counts"]["commands"] >= 25

    def test_server_creates_with_real_packages(self):
        """MCP server initializes successfully with real packages."""
        from popkit_mcp.server import create_server

        server = create_server(PACKAGES_DIR)
        assert server is not None

    def test_every_skill_has_loadable_content(self):
        """Every skill's SKILL.md file is readable."""
        from popkit_mcp.tool_registry import scan_skills

        skills = scan_skills(PACKAGES_DIR)
        for skill in skills:
            content = skill.path.read_text(encoding="utf-8")
            assert len(content) > 50, f"Skill {skill.name} content too short"
            assert "---" in content, f"Skill {skill.name} missing frontmatter"

    def test_every_agent_has_loadable_content(self):
        """Every agent's AGENT.md file is readable."""
        from popkit_mcp.tool_registry import scan_agents

        agents = scan_agents(PACKAGES_DIR)
        for agent in agents:
            content = agent.path.read_text(encoding="utf-8")
            assert len(content) > 50, f"Agent {agent.name} content too short"
            assert "---" in content, f"Agent {agent.name} missing frontmatter"

    def test_skill_names_are_unique(self):
        """No duplicate skill names across packages."""
        from popkit_mcp.tool_registry import scan_skills

        skills = scan_skills(PACKAGES_DIR)
        names = [s.name for s in skills]
        assert len(names) == len(set(names)), (
            f"Duplicate skills: {[n for n in names if names.count(n) > 1]}"
        )

    def test_agent_names_are_unique(self):
        """No duplicate agent names across packages."""
        from popkit_mcp.tool_registry import scan_agents

        agents = scan_agents(PACKAGES_DIR)
        names = [a.name for a in agents]
        assert len(names) == len(set(names)), (
            f"Duplicate agents: {[n for n in names if names.count(n) > 1]}"
        )


@pytest.mark.skipif(not HAS_REAL_PACKAGES, reason="Real packages not available")
class TestEndToEndProviderDetection:
    """Test: provider detection across all adapters."""

    def test_all_adapters_detect_without_crash(self):
        """Every registered adapter can run detect() without errors."""
        from popkit_shared.providers import list_adapters

        adapters = list_adapters()
        assert len(adapters) >= 5  # claude-code, cursor, codex, copilot, generic-mcp

        for adapter in adapters:
            info = adapter.detect()
            assert info.name == adapter.name
            assert isinstance(info.display_name, str)
            assert isinstance(info.is_available, bool)

    def test_generic_mcp_always_available(self):
        """Generic MCP is always available as fallback."""
        from popkit_shared.providers import detect_providers

        providers = detect_providers()
        names = {p.name for p in providers}
        assert "generic-mcp" in names

    def test_provider_names_are_unique(self):
        """No duplicate provider names."""
        from popkit_shared.providers import list_adapters

        adapters = list_adapters()
        names = [a.name for a in adapters]
        assert len(names) == len(set(names))


@pytest.mark.skipif(not HAS_REAL_PACKAGES, reason="Real packages not available")
class TestEndToEndProviderConfigGeneration:
    """Test: each provider generates valid config for real packages."""

    def test_cursor_generates_valid_mcp_json(self, tmp_path):
        """Cursor adapter generates valid mcp-config.json."""
        from popkit_shared.providers.cursor import CursorAdapter

        adapter = CursorAdapter()
        output = tmp_path / "cursor-output"
        generated = adapter.generate_config(PACKAGES_DIR, output)

        assert len(generated) > 0
        # Check mcp config is valid JSON
        mcp_files = [f for f in generated if "mcp" in f.name]
        for f in mcp_files:
            data = json.loads(f.read_text(encoding="utf-8"))
            assert "mcpServers" in data
            assert "popkit" in data["mcpServers"]

    def test_codex_generates_valid_toml(self, tmp_path):
        """Codex adapter generates parseable TOML config."""
        import tomllib

        from popkit_shared.providers.codex import CodexAdapter

        adapter = CodexAdapter()
        output = tmp_path / "codex-output"
        generated = adapter.generate_config(PACKAGES_DIR, output)

        toml_files = [f for f in generated if f.suffix == ".toml"]
        assert len(toml_files) > 0

        for f in toml_files:
            data = tomllib.loads(f.read_text(encoding="utf-8"))
            assert "mcp_servers" in data
            assert "popkit" in data["mcp_servers"]

    def test_codex_generates_agents_md(self, tmp_path):
        """Codex adapter generates AGENTS.md with real agent content."""
        from popkit_shared.providers.codex import CodexAdapter

        adapter = CodexAdapter()
        output = tmp_path / "codex-output"
        adapter.generate_config(PACKAGES_DIR, output)

        agents_md = output / "AGENTS.md"
        assert agents_md.is_file()
        content = agents_md.read_text(encoding="utf-8")
        assert "documentation-maintainer" in content or "code-reviewer" in content

    def test_copilot_generates_both_json_formats(self, tmp_path):
        """Copilot adapter generates both mcpServers and servers format."""
        from popkit_shared.providers.copilot import CopilotAdapter

        adapter = CopilotAdapter()
        output = tmp_path / "copilot-output"
        generated = adapter.generate_config(PACKAGES_DIR, output)

        json_files = [f for f in generated if f.suffix == ".json"]
        assert len(json_files) >= 2

        # Check both formats exist
        contents = {f.name: json.loads(f.read_text(encoding="utf-8")) for f in json_files}

        copilot_config = [c for c in contents.values() if "mcpServers" in c]
        vscode_config = [c for c in contents.values() if "servers" in c]

        assert len(copilot_config) >= 1, "Missing Copilot CLI format (mcpServers)"
        assert len(vscode_config) >= 1, "Missing VS Code format (servers)"

    def test_generic_mcp_generates_all_files(self, tmp_path):
        """Generic MCP adapter generates all deployment artifacts."""
        from popkit_shared.providers.generic_mcp import GenericMCPAdapter

        adapter = GenericMCPAdapter()
        output = tmp_path / "generic-output"

        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            generated = adapter.generate_config(PACKAGES_DIR, output)

        assert len(generated) == 6
        names = {f.name for f in generated}
        assert "mcp-config.json" in names
        assert "start-mcp-server.sh" in names
        assert "start-mcp-server.bat" in names
        assert "popkit-mcp.service" in names
        assert "com.popkit.mcp.plist" in names
        assert "Dockerfile" in names

    def test_codex_plan_launch_round_trips_to_request_user_input(self):
        """Codex launch env should resolve back to the plan-capable surface."""
        from popkit_shared.providers.codex import CodexAdapter
        from popkit_shared.utils.interaction_surface import (
            InteractionSurface,
            resolve_runtime_capabilities,
        )

        adapter = CodexAdapter()
        launch_spec = adapter.build_launch_spec(
            mode="plan",
            env={},
            host_plan_supported=True,
        )
        capabilities = resolve_runtime_capabilities(env=launch_spec.env)

        assert launch_spec.actual_mode == "plan"
        assert capabilities.provider == "codex"
        assert capabilities.interaction_surface == InteractionSurface.REQUEST_USER_INPUT
        assert capabilities.can_request_user_input is True


@pytest.mark.skipif(not HAS_REAL_PACKAGES, reason="Real packages not available")
class TestEndToEndPopkitPackageYaml:
    """Test: popkit-package.yaml manifests are accurate."""

    def test_all_packages_have_manifests(self):
        """Every plugin package has a popkit-package.yaml."""
        for pkg in ["popkit-core", "popkit-dev", "popkit-ops", "popkit-research"]:
            manifest = PACKAGES_DIR / pkg / "popkit-package.yaml"
            assert manifest.is_file(), f"Missing manifest: {manifest}"

    def test_manifests_parse_valid_yaml(self):
        """All manifests are valid YAML."""
        import yaml

        for pkg in ["popkit-core", "popkit-dev", "popkit-ops", "popkit-research"]:
            manifest = PACKAGES_DIR / pkg / "popkit-package.yaml"
            data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            assert data["name"] == pkg
            assert "version" in data
            assert "agents" in data or "skills" in data

    def test_manifest_skill_paths_exist(self):
        """All skill paths declared in manifests point to real SKILL.md files."""
        import yaml

        for pkg in ["popkit-core", "popkit-dev", "popkit-ops", "popkit-research"]:
            manifest = PACKAGES_DIR / pkg / "popkit-package.yaml"
            data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            for skill in data.get("skills", []):
                skill_file = PACKAGES_DIR / pkg / skill["path"] / "SKILL.md"
                assert skill_file.is_file(), f"Missing skill: {skill_file}"

    def test_manifest_agent_paths_exist(self):
        """All agent paths declared in manifests point to real AGENT.md files."""
        import yaml

        for pkg in ["popkit-core", "popkit-dev", "popkit-ops", "popkit-research"]:
            manifest = PACKAGES_DIR / pkg / "popkit-package.yaml"
            data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            for agent in data.get("agents", []):
                agent_file = PACKAGES_DIR / pkg / agent["path"] / "AGENT.md"
                assert agent_file.is_file(), f"Missing agent: {agent_file}"

    def test_manifest_command_paths_exist(self):
        """All command paths declared in manifests point to real .md files."""
        import yaml

        for pkg in ["popkit-core", "popkit-dev", "popkit-ops", "popkit-research"]:
            manifest = PACKAGES_DIR / pkg / "popkit-package.yaml"
            data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            for cmd in data.get("commands", []):
                cmd_file = PACKAGES_DIR / pkg / cmd["path"]
                assert cmd_file.is_file(), f"Missing command: {cmd_file}"


@pytest.mark.skipif(not HAS_REAL_PACKAGES, reason="Real packages not available")
class TestEndToEndToolMappingConsistency:
    """Test: tool mappings are consistent across providers."""

    def test_all_providers_map_file_read(self):
        """Every provider has a mapping for file_read."""
        from popkit_shared.providers import list_adapters
        from popkit_shared.providers.base import ToolCategory

        for adapter in list_adapters():
            mapping = adapter.map_tool(ToolCategory.FILE_READ)
            assert mapping is not None, f"{adapter.name} missing file_read mapping"

    def test_all_providers_map_shell(self):
        """Every provider has a mapping for shell."""
        from popkit_shared.providers import list_adapters
        from popkit_shared.providers.base import ToolCategory

        for adapter in list_adapters():
            mapping = adapter.map_tool(ToolCategory.SHELL)
            assert mapping is not None, f"{adapter.name} missing shell mapping"

    def test_translate_tools_works_for_all_providers(self):
        """translate_tools produces non-empty results for all providers."""
        from popkit_shared.providers import list_adapters
        from popkit_shared.providers.tool_mapping import translate_tools

        abstract = ["file_read", "file_write", "shell"]
        for adapter in list_adapters():
            result = translate_tools(abstract, adapter.name)
            assert len(result) >= 2, f"{adapter.name} translated too few tools: {result}"


@pytest.mark.skipif(not HAS_REAL_PACKAGES, reason="Real packages not available")
class TestEndToEndHookProtocol:
    """Test: hook protocol works across providers."""

    def test_hook_response_formats_for_all_providers(self):
        """HookResponse.for_provider works for every registered provider."""
        from popkit_shared.providers import list_adapters
        from popkit_shared.providers.hook_protocol import create_deny

        resp = create_deny("Test denial")
        for adapter in list_adapters():
            formatted = resp.for_provider(adapter.name)
            assert "action" in formatted
            assert formatted["action"] == "deny"

    def test_stateless_hook_backward_compatible(self):
        """Old-style hooks still work with the v2 protocol."""
        from popkit_shared.utils.stateless_hook import StatelessHook, run_hook

        class LegacyHook(StatelessHook):
            def process(self, ctx):
                return self.update_context(ctx, tool_result="legacy works")

        output = run_hook(
            LegacyHook,
            json.dumps({"session_id": "e2e", "tool_name": "Test", "tool_input": {}}),
        )
        result = json.loads(output)
        assert result["action"] == "continue"
        assert result["context"]["tool_result"] == "legacy works"
