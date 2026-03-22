#!/usr/bin/env python3
"""Tests for popkit_mcp.tool_registry — package scanning and registration."""

import sys
from pathlib import Path

import pytest

# Add popkit-mcp to path for testing
MCP_PKG = Path(__file__).parent.parent.parent / "popkit-mcp"
if str(MCP_PKG) not in sys.path:
    sys.path.insert(0, str(MCP_PKG))

from popkit_mcp.tool_registry import (
    _parse_frontmatter,
    build_registry,
    scan_agents,
    scan_commands,
    scan_skills,
)


class TestParseFrontmatter:
    """Tests for YAML frontmatter parsing."""

    def test_parses_valid_frontmatter(self, tmp_path):
        """Parses standard frontmatter correctly."""
        md = tmp_path / "test.md"
        md.write_text(
            "---\nname: test-skill\ndescription: A test\n---\n\n# Body content\n",
            encoding="utf-8",
        )
        fm, body = _parse_frontmatter(md)
        assert fm["name"] == "test-skill"
        assert fm["description"] == "A test"
        assert "Body content" in body

    def test_no_frontmatter(self, tmp_path):
        """Returns empty dict for files without frontmatter."""
        md = tmp_path / "test.md"
        md.write_text("# Just a heading\n\nSome content.", encoding="utf-8")
        fm, body = _parse_frontmatter(md)
        assert fm == {}
        assert "Just a heading" in body

    def test_invalid_yaml(self, tmp_path):
        """Returns empty dict for invalid YAML."""
        md = tmp_path / "test.md"
        md.write_text("---\n: : : invalid\n---\n\nBody", encoding="utf-8")
        fm, body = _parse_frontmatter(md)
        assert fm == {}

    def test_missing_file(self, tmp_path):
        """Returns empty for nonexistent files."""
        fm, body = _parse_frontmatter(tmp_path / "nonexistent.md")
        assert fm == {}
        assert body == ""


class TestScanSkills:
    """Tests for skill scanning."""

    def _create_skill(self, pkg_dir: Path, skill_name: str, description: str = "Test"):
        """Helper to create a skill directory structure."""
        skill_dir = pkg_dir / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f'---\nname: {skill_name}\ndescription: "{description}"\n---\n\n# {skill_name}\n',
            encoding="utf-8",
        )
        return skill_dir

    def _create_plugin_json(self, pkg_dir: Path, name: str = "test-pkg"):
        """Helper to create package marker."""
        plugin_dir = pkg_dir / ".claude-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            f'{{"name": "{name}", "version": "1.0.0"}}',
            encoding="utf-8",
        )

    def test_scans_skills_from_package(self, tmp_path):
        """Finds skills in a package directory."""
        pkg = tmp_path / "popkit-test"
        self._create_plugin_json(pkg, "popkit-test")
        self._create_skill(pkg, "my-skill", "Does things")
        self._create_skill(pkg, "other-skill", "Does other things")

        skills = scan_skills(tmp_path)
        assert len(skills) == 2
        names = {s.name for s in skills}
        assert "my-skill" in names
        assert "other-skill" in names

    def test_skill_definition_fields(self, tmp_path):
        """SkillDefinition has correct fields."""
        pkg = tmp_path / "popkit-test"
        self._create_plugin_json(pkg, "popkit-test")
        self._create_skill(pkg, "test-skill", "A description")

        skills = scan_skills(tmp_path)
        assert len(skills) == 1
        skill = skills[0]
        assert skill.name == "test-skill"
        assert skill.description == "A description"
        assert skill.package == "popkit-test"
        assert isinstance(skill.path, Path)

    def test_skips_non_package_dirs(self, tmp_path):
        """Skips directories without package markers."""
        random_dir = tmp_path / "random-dir"
        random_dir.mkdir()
        (random_dir / "skills" / "fake" / "SKILL.md").parent.mkdir(parents=True)

        skills = scan_skills(tmp_path)
        assert len(skills) == 0

    def test_skips_skills_without_name(self, tmp_path):
        """Skips SKILL.md without name in frontmatter."""
        pkg = tmp_path / "popkit-test"
        self._create_plugin_json(pkg, "popkit-test")
        skill_dir = pkg / "skills" / "unnamed"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\ndescription: no name field\n---\n\n# No Name\n",
            encoding="utf-8",
        )

        skills = scan_skills(tmp_path)
        assert len(skills) == 0


class TestScanAgents:
    """Tests for agent scanning."""

    def _create_agent(self, pkg_dir: Path, tier: str, agent_name: str):
        """Helper to create an agent directory structure."""
        agent_dir = pkg_dir / "agents" / tier / agent_name
        agent_dir.mkdir(parents=True)
        (agent_dir / "AGENT.md").write_text(
            f'---\nname: {agent_name}\ndescription: "Agent desc"\n'
            f"tools:\n  - Read\n  - Write\n---\n\n# {agent_name}\n",
            encoding="utf-8",
        )

    def _create_plugin_json(self, pkg_dir: Path, name: str = "test-pkg"):
        plugin_dir = pkg_dir / ".claude-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            f'{{"name": "{name}", "version": "1.0.0"}}',
            encoding="utf-8",
        )

    def test_scans_agents_from_tiers(self, tmp_path):
        """Finds agents in tier directories."""
        pkg = tmp_path / "popkit-test"
        self._create_plugin_json(pkg, "popkit-test")
        self._create_agent(pkg, "tier-1-always-active", "my-agent")
        self._create_agent(pkg, "tier-2-on-demand", "other-agent")

        agents = scan_agents(tmp_path)
        assert len(agents) == 2

    def test_tier_classification(self, tmp_path):
        """Agents in tier-1 get 'always-active', tier-2 get 'on-demand'."""
        pkg = tmp_path / "popkit-test"
        self._create_plugin_json(pkg, "popkit-test")
        self._create_agent(pkg, "tier-1-always-active", "active-agent")
        self._create_agent(pkg, "tier-2-on-demand", "demand-agent")

        agents = scan_agents(tmp_path)
        agent_map = {a.name: a for a in agents}
        assert agent_map["active-agent"].tier == "always-active"
        assert agent_map["demand-agent"].tier == "on-demand"

    def test_agent_tools_parsed(self, tmp_path):
        """Agent tools list is parsed from frontmatter."""
        pkg = tmp_path / "popkit-test"
        self._create_plugin_json(pkg, "popkit-test")
        self._create_agent(pkg, "tier-1-always-active", "tool-agent")

        agents = scan_agents(tmp_path)
        assert agents[0].tools == ["Read", "Write"]


class TestScanCommands:
    """Tests for command scanning."""

    def _create_plugin_json(self, pkg_dir: Path, name: str = "test-pkg"):
        plugin_dir = pkg_dir / ".claude-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            f'{{"name": "{name}", "version": "1.0.0"}}',
            encoding="utf-8",
        )

    def test_scans_command_files(self, tmp_path):
        """Finds .md files in commands/ directory."""
        pkg = tmp_path / "popkit-test"
        self._create_plugin_json(pkg, "popkit-test")
        cmd_dir = pkg / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "deploy.md").write_text(
            '---\ndescription: "Deploy app"\n---\n\n# Deploy\n',
            encoding="utf-8",
        )
        (cmd_dir / "status.md").write_text(
            '---\ndescription: "Show status"\n---\n\n# Status\n',
            encoding="utf-8",
        )

        commands = scan_commands(tmp_path)
        assert len(commands) == 2
        names = {c.name for c in commands}
        assert "deploy" in names
        assert "status" in names


class TestBuildRegistry:
    """Tests for the complete registry builder."""

    def test_builds_complete_registry(self, tmp_path):
        """build_registry returns counts and all items."""
        # Create a minimal package
        pkg = tmp_path / "popkit-test"
        plugin_dir = pkg / ".claude-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text('{"name": "popkit-test", "version": "1.0.0"}')

        # Add a skill
        skill_dir = pkg / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text('---\nname: test-skill\ndescription: "test"\n---\n')

        # Add an agent
        agent_dir = pkg / "agents" / "tier-1-always-active" / "test-agent"
        agent_dir.mkdir(parents=True)
        (agent_dir / "AGENT.md").write_text('---\nname: test-agent\ndescription: "test"\n---\n')

        registry = build_registry(tmp_path)
        assert registry["counts"]["skills"] == 1
        assert registry["counts"]["agents"] == 1
        assert registry["counts"]["total"] >= 2


class TestRealPackages:
    """Tests against the actual PopKit packages (integration tests)."""

    PACKAGES_DIR = Path(__file__).parent.parent.parent

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent.parent / "popkit-core").is_dir(),
        reason="Real packages not available",
    )
    def test_scan_real_skills(self):
        """Scan actual PopKit packages for skills."""
        skills = scan_skills(self.PACKAGES_DIR)
        assert len(skills) >= 50  # 50 skills documented

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent.parent / "popkit-core").is_dir(),
        reason="Real packages not available",
    )
    def test_scan_real_agents(self):
        """Scan actual PopKit packages for agents."""
        agents = scan_agents(self.PACKAGES_DIR)
        assert len(agents) >= 24  # 24 agents documented

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent.parent / "popkit-core").is_dir(),
        reason="Real packages not available",
    )
    def test_scan_real_commands(self):
        """Scan actual PopKit packages for commands."""
        commands = scan_commands(self.PACKAGES_DIR)
        assert len(commands) >= 25  # 25 commands documented
