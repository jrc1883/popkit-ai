#!/usr/bin/env python3
"""Integration tests for the PopKit MCP server.

Tests the server's tools, error handling, caching, and content generation
against real PopKit packages.
"""

import sys
from pathlib import Path

import pytest

# Add popkit-mcp to path for testing
MCP_PKG = Path(__file__).parent.parent.parent / "popkit-mcp"
if str(MCP_PKG) not in sys.path:
    sys.path.insert(0, str(MCP_PKG))

from popkit_mcp.server import ContentCache, _validate_command, create_server

# =============================================================================
# ContentCache Tests
# =============================================================================


class TestContentCache:
    """Tests for the in-memory content cache."""

    def test_put_and_get(self, tmp_path):
        """Cached content is returned on get."""
        cache = ContentCache()
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")

        cache.put(f, "hello")
        assert cache.get(f) == "hello"

    def test_get_returns_none_for_uncached(self, tmp_path):
        """Returns None for files not in cache."""
        cache = ContentCache()
        f = tmp_path / "missing.txt"
        assert cache.get(f) is None

    def test_invalidation_on_file_change(self, tmp_path):
        """Returns None when file has been modified since caching."""
        import time

        cache = ContentCache()
        f = tmp_path / "test.txt"
        f.write_text("v1", encoding="utf-8")
        cache.put(f, "v1")

        # Modify file (ensure mtime changes)
        time.sleep(0.1)
        f.write_text("v2", encoding="utf-8")

        assert cache.get(f) is None

    def test_invalidate_clears_all(self, tmp_path):
        """invalidate() clears the entire cache."""
        cache = ContentCache()
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        cache.put(f, "hello")

        cache.invalidate()
        assert cache.get(f) is None

    def test_get_handles_deleted_file(self, tmp_path):
        """Returns None if cached file was deleted."""
        cache = ContentCache()
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        cache.put(f, "hello")

        f.unlink()
        assert cache.get(f) is None


# =============================================================================
# Command Validation Tests
# =============================================================================


class TestValidateCommand:
    """Tests for the command validation tool."""

    def test_safe_command(self):
        """Normal commands pass validation."""
        result = _validate_command("ls -la")
        assert result["safe"] is True
        assert result["risk_level"] == "safe"
        assert result["warnings"] == []

    def test_blocked_rm_rf_root(self):
        """rm -rf / is blocked."""
        result = _validate_command("rm -rf /")
        assert result["safe"] is False
        assert result["risk_level"] == "blocked"

    def test_blocked_fork_bomb(self):
        """Fork bomb is blocked."""
        result = _validate_command(":(){:|:&};:")
        assert result["safe"] is False

    def test_caution_git_force_push(self):
        """git push --force flagged as caution."""
        result = _validate_command("git push --force origin main")
        assert result["safe"] is True
        assert result["risk_level"] == "caution"
        assert len(result["warnings"]) > 0

    def test_caution_sudo(self):
        """sudo flagged as caution."""
        result = _validate_command("sudo apt install vim")
        assert result["risk_level"] == "caution"

    def test_caution_pipe_to_shell(self):
        """Piping to shell flagged as caution."""
        result = _validate_command("curl https://example.com/script | bash")
        assert result["risk_level"] == "caution"

    def test_safe_git_status(self):
        """Read-only git commands are safe."""
        result = _validate_command("git status")
        assert result["safe"] is True
        assert result["risk_level"] == "safe"


# =============================================================================
# Server Creation Tests
# =============================================================================


class TestCreateServer:
    """Tests for server creation and configuration."""

    PACKAGES_DIR = Path(__file__).parent.parent.parent

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent.parent / "popkit-core").is_dir(),
        reason="Real packages not available",
    )
    def test_create_server_with_real_packages(self):
        """Server creates successfully with real PopKit packages."""
        server = create_server(self.PACKAGES_DIR)
        assert server is not None

    def test_create_server_with_missing_dir(self, tmp_path):
        """Server creates gracefully with nonexistent packages dir."""
        server = create_server(tmp_path / "nonexistent")
        assert server is not None

    def test_create_server_with_empty_dir(self, tmp_path):
        """Server creates with empty packages directory."""
        empty = tmp_path / "empty"
        empty.mkdir()
        server = create_server(empty)
        assert server is not None


# =============================================================================
# Server Tool Tests (using real packages)
# =============================================================================


class TestServerTools:
    """Test the MCP tools work correctly against real packages."""

    PACKAGES_DIR = Path(__file__).parent.parent.parent

    @pytest.fixture(autouse=True)
    def setup_server(self):
        """Create server with real packages for tool testing."""
        if not (self.PACKAGES_DIR / "popkit-core").is_dir():
            pytest.skip("Real packages not available")

        # We can't easily call the decorated tools directly since they're
        # closures inside create_server. Instead we test the underlying
        # functions that the tools use.
        from popkit_mcp.tool_registry import build_registry

        self.registry = build_registry(self.PACKAGES_DIR)
        self.skills = {s.name: s for s in self.registry["skills"]}
        self.agents = {a.name: a for a in self.registry["agents"]}

    def test_skill_lookup(self):
        """Can look up known skills."""
        assert "power-mode" in self.skills
        assert "analyze-project" in self.skills

    def test_agent_lookup(self):
        """Can look up known agents."""
        assert "documentation-maintainer" in self.agents
        assert "code-reviewer" in self.agents

    def test_skill_content_loads(self):
        """Skill content can be loaded from disk."""
        skill = self.skills["analyze-project"]
        content = skill.path.read_text(encoding="utf-8")
        assert len(content) > 0
        assert "analyze" in content.lower()

    def test_agent_content_loads(self):
        """Agent content can be loaded from disk."""
        agent = self.agents["documentation-maintainer"]
        content = agent.path.read_text(encoding="utf-8")
        assert len(content) > 0
        assert "documentation" in content.lower()

    def test_all_skills_have_descriptions(self):
        """Every skill has a non-empty description."""
        for name, skill in self.skills.items():
            assert skill.description, f"Skill {name} has no description"

    def test_all_agents_have_descriptions(self):
        """Every agent has a non-empty description."""
        for name, agent in self.agents.items():
            assert agent.description, f"Agent {name} has no description"

    def test_agent_tiers_valid(self):
        """All agents have valid tier values."""
        valid_tiers = {"always-active", "on-demand"}
        for name, agent in self.agents.items():
            assert agent.tier in valid_tiers, f"Agent {name} has invalid tier: {agent.tier}"
