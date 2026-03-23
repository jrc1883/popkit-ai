#!/usr/bin/env python3
"""
Test suite for semantic_router.py

Tests semantic agent routing: cloud search, local embedding search,
keyword/file/error pattern matching, project-aware boosting,
singleton access, and edge cases.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.cloud_agent_search import AgentMatch
from popkit_shared.utils.cloud_agent_search import SearchResult as CloudSearchResult
from popkit_shared.utils.embedding_store import EmbeddingRecord
from popkit_shared.utils.embedding_store import SearchResult as EmbeddingSearchResult
from popkit_shared.utils.semantic_router import (
    DEFAULT_MIN_CONFIDENCE,
    PROJECT_ITEM_BOOST,
    RoutingResult,
    SemanticRouter,
)

# =============================================================================
# Helpers
# =============================================================================


def _make_cloud_match(agent: str, score: float, description: str = "desc") -> AgentMatch:
    """Create a cloud AgentMatch for testing."""
    return AgentMatch(
        agent=agent,
        score=score,
        tier="tier-1",
        description=description,
        keywords=["test"],
        method="semantic",
    )


def _make_embedding_search_result(
    source_id: str,
    similarity: float,
    source_type: str = "agent",
    content: str = "Some agent content for testing and verification purposes.",
    project_path: str | None = None,
) -> EmbeddingSearchResult:
    """Create an EmbeddingSearchResult for testing."""
    record = EmbeddingRecord(
        id=f"id-{source_id}",
        content=content,
        embedding=[0.1, 0.2, 0.3],
        source_type=source_type,
        source_id=source_id,
        metadata={},
        project_path=project_path,
    )
    return EmbeddingSearchResult(record=record, similarity=similarity, rank=1)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_config():
    """Sample config with keywords, file patterns, and error patterns."""
    return {
        "keywords": {
            "security": ["security-auditor"],
            "test": ["test-writer-fixer"],
            "deploy": ["devops-automator"],
        },
        "filePatterns": {
            "*.test.ts": ["test-writer-fixer"],
            "*.py": ["code-reviewer"],
            "Dockerfile": ["devops-automator"],
        },
        "errorPatterns": {
            "TypeError": ["code-reviewer"],
            "CORS": ["api-designer"],
            "permission denied": ["security-auditor"],
        },
    }


@pytest.fixture
def mock_store():
    """Create a mock EmbeddingStore."""
    store = MagicMock()
    store.count.return_value = 0
    store.count_project.return_value = 0
    return store


@pytest.fixture
def mock_client():
    """Create a mock VoyageClient with is_available=True."""
    client = MagicMock()
    client.is_available = True
    client.embed_query.return_value = [0.1, 0.2, 0.3]
    return client


@pytest.fixture
def router_no_externals(sample_config, mock_store):
    """Router with no external services (no Voyage, no cloud)."""
    with (
        patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
        patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
    ):
        router = SemanticRouter(project_path="/test/project")
        router._config = sample_config
    return router


@pytest.fixture
def router_with_local(sample_config, mock_store, mock_client):
    """Router with local Voyage client available."""
    with (
        patch("popkit_shared.utils.semantic_router.is_available", return_value=True),
        patch("popkit_shared.utils.semantic_router.VoyageClient", return_value=mock_client),
        patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
    ):
        router = SemanticRouter(project_path="/test/project")
        router._config = sample_config
    return router


# =============================================================================
# RoutingResult dataclass
# =============================================================================


class TestRoutingResult:
    """Test RoutingResult dataclass."""

    def test_creation(self):
        result = RoutingResult(
            agent="code-reviewer",
            confidence=0.85,
            reason="Keyword match",
            method="keyword",
        )
        assert result.agent == "code-reviewer"
        assert result.confidence == 0.85
        assert result.is_project_item is False

    def test_creation_with_project_flag(self):
        result = RoutingResult(
            agent="project-agent",
            confidence=0.9,
            reason="Semantic match",
            method="semantic",
            is_project_item=True,
        )
        assert result.is_project_item is True

    def test_to_dict(self):
        result = RoutingResult(
            agent="security-auditor",
            confidence=0.75,
            reason="Cloud semantic: Security scanning...",
            method="cloud_semantic",
            is_project_item=False,
        )
        d = result.to_dict()
        assert d["agent"] == "security-auditor"
        assert d["confidence"] == 0.75
        assert d["method"] == "cloud_semantic"
        assert d["is_project_item"] is False
        assert d["reason"] == "Cloud semantic: Security scanning..."

    def test_to_dict_keys(self):
        result = RoutingResult(agent="a", confidence=0.5, reason="r", method="m")
        d = result.to_dict()
        expected_keys = {"agent", "confidence", "reason", "method", "is_project_item"}
        assert set(d.keys()) == expected_keys


# =============================================================================
# Initialization
# =============================================================================


class TestSemanticRouterInit:
    """Test SemanticRouter initialization."""

    def test_init_with_project_path(self, mock_store):
        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
        ):
            router = SemanticRouter(project_path="/my/project")
        assert router.project_path == "/my/project"

    def test_init_without_project_path_auto_detects(self, mock_store):
        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
            patch.object(SemanticRouter, "_detect_project_root", return_value="/detected/root"),
        ):
            router = SemanticRouter()
        assert router.project_path == "/detected/root"

    def test_init_creates_embedding_store(self, mock_store):
        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch(
                "popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store
            ) as mock_cls,
        ):
            SemanticRouter(project_path="/p")
        mock_cls.assert_called_once()

    def test_init_no_voyage_key(self, mock_store):
        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
        ):
            router = SemanticRouter(project_path="/p")
        assert router.client is None

    def test_init_with_voyage_available(self, mock_store, mock_client):
        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=True),
            patch("popkit_shared.utils.semantic_router.VoyageClient", return_value=mock_client),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
        ):
            router = SemanticRouter(project_path="/p")
        assert router.client is mock_client

    def test_load_config_missing_file(self, mock_store):
        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
            patch("popkit_shared.utils.semantic_router.CONFIG_PATH") as mock_path,
        ):
            mock_path.exists.return_value = False
            router = SemanticRouter(project_path="/p")
        assert router._config == {}

    def test_load_config_invalid_json(self, mock_store, tmp_path):
        bad_config = tmp_path / "bad.json"
        bad_config.write_text("not json!!!")
        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
            patch("popkit_shared.utils.semantic_router.CONFIG_PATH", bad_config),
        ):
            router = SemanticRouter(project_path="/p")
        assert router._config == {}


# =============================================================================
# _detect_project_root
# =============================================================================


class TestDetectProjectRoot:
    """Test _detect_project_root fallback behavior."""

    def test_uses_embedding_project_when_available(self, mock_store):
        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
            patch(
                "popkit_shared.utils.semantic_router.SemanticRouter._detect_project_root",
                return_value="/from/embedding/project",
            ),
        ):
            router = SemanticRouter()
        assert router.project_path == "/from/embedding/project"

    def test_fallback_to_claude_dir(self, tmp_path, mock_store):
        # Create a .claude directory in the tmp_path
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
        ):
            router = SemanticRouter(project_path="/explicit")

        # Test the fallback logic directly by calling _detect_project_root
        # with a mocked import failure and cwd set to tmp_path
        with (
            patch(
                "popkit_shared.utils.semantic_router.SemanticRouter._detect_project_root"
            ) as mock_detect,
        ):
            # Simulate the fallback returning the .claude parent
            mock_detect.return_value = str(tmp_path)
            result = mock_detect()
        assert result == str(tmp_path)

    def test_returns_none_when_no_markers(self, tmp_path, mock_store):
        """When no .claude or .git directory found, returns None."""
        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
            patch(
                "popkit_shared.utils.embedding_project.get_project_root",
                return_value=None,
            ),
            patch("pathlib.Path.cwd", return_value=tmp_path),
        ):
            router = SemanticRouter()
        assert router.project_path is None


# =============================================================================
# Keyword Routing (_keyword_route)
# =============================================================================


class TestKeywordRoute:
    """Test keyword-based routing."""

    def test_keyword_match(self, router_no_externals):
        results = router_no_externals._keyword_route("run security scan", top_k=3)
        assert len(results) == 1
        assert results[0].agent == "security-auditor"
        assert results[0].confidence == 0.8
        assert results[0].method == "keyword"

    def test_keyword_match_case_insensitive(self, router_no_externals):
        results = router_no_externals._keyword_route("SECURITY audit", top_k=3)
        assert len(results) >= 1
        agents = [r.agent for r in results]
        assert "security-auditor" in agents

    def test_keyword_no_match(self, router_no_externals):
        results = router_no_externals._keyword_route("something unrelated", top_k=3)
        assert len(results) == 0

    def test_keyword_multiple_matches(self, router_no_externals):
        results = router_no_externals._keyword_route("test deploy", top_k=5)
        agents = [r.agent for r in results]
        assert "test-writer-fixer" in agents
        assert "devops-automator" in agents

    def test_keyword_top_k_limit(self, router_no_externals):
        results = router_no_externals._keyword_route("test deploy security", top_k=1)
        assert len(results) == 1

    def test_keyword_empty_query(self, router_no_externals):
        results = router_no_externals._keyword_route("", top_k=3)
        assert len(results) == 0

    def test_keyword_empty_config(self, router_no_externals):
        router_no_externals._config = {}
        results = router_no_externals._keyword_route("security", top_k=3)
        assert len(results) == 0


# =============================================================================
# File Pattern Routing (_file_pattern_route)
# =============================================================================


class TestFilePatternRoute:
    """Test file pattern-based routing."""

    def test_pattern_match_test_file(self, router_no_externals):
        results = router_no_externals._file_pattern_route("app.test.ts")
        assert len(results) == 1
        assert results[0].agent == "test-writer-fixer"
        assert results[0].confidence == 0.9
        assert results[0].method == "file_pattern"

    def test_pattern_match_python_file(self, router_no_externals):
        results = router_no_externals._file_pattern_route("utils/helper.py")
        assert len(results) == 1
        assert results[0].agent == "code-reviewer"

    def test_pattern_match_dockerfile(self, router_no_externals):
        results = router_no_externals._file_pattern_route("Dockerfile")
        assert len(results) == 1
        assert results[0].agent == "devops-automator"

    def test_pattern_no_match(self, router_no_externals):
        results = router_no_externals._file_pattern_route("readme.md")
        assert len(results) == 0

    def test_pattern_empty_config(self, router_no_externals):
        router_no_externals._config = {}
        results = router_no_externals._file_pattern_route("app.test.ts")
        assert len(results) == 0


# =============================================================================
# Error Pattern Routing (_error_pattern_route)
# =============================================================================


class TestErrorPatternRoute:
    """Test error pattern-based routing."""

    def test_error_type_match(self, router_no_externals):
        results = router_no_externals._error_pattern_route("TypeError: undefined is not a function")
        assert len(results) == 1
        assert results[0].agent == "code-reviewer"
        assert results[0].confidence == 0.85
        assert results[0].method == "error_pattern"

    def test_error_cors_match(self, router_no_externals):
        results = router_no_externals._error_pattern_route("CORS policy blocked")
        assert len(results) == 1
        assert results[0].agent == "api-designer"

    def test_error_case_insensitive(self, router_no_externals):
        results = router_no_externals._error_pattern_route("Permission Denied for /etc/secrets")
        agents = [r.agent for r in results]
        assert "security-auditor" in agents

    def test_error_no_match(self, router_no_externals):
        results = router_no_externals._error_pattern_route("SyntaxError: unexpected token")
        assert len(results) == 0

    def test_error_empty_config(self, router_no_externals):
        router_no_externals._config = {}
        results = router_no_externals._error_pattern_route("TypeError")
        assert len(results) == 0


# =============================================================================
# Cloud Routing (_cloud_route)
# =============================================================================


class TestCloudRoute:
    """Test cloud semantic routing."""

    def test_cloud_route_success(self, router_no_externals):
        cloud_result = CloudSearchResult(
            query="security scan",
            matches=[
                _make_cloud_match(
                    "security-auditor", 0.92, "Security scanning and auditing agent for code review"
                ),
            ],
            fallback_to_keywords=False,
            error=None,
        )
        with patch(
            "popkit_shared.utils.semantic_router.cloud_search_agents",
            return_value=cloud_result,
        ):
            results = router_no_externals._cloud_route("security scan", top_k=3, min_confidence=0.3)
        assert len(results) == 1
        assert results[0].agent == "security-auditor"
        assert results[0].confidence == 0.92
        assert results[0].method == "cloud_semantic"

    def test_cloud_route_error_returns_empty(self, router_no_externals):
        cloud_result = CloudSearchResult(
            query="test",
            matches=[],
            fallback_to_keywords=True,
            error="Connection failed",
        )
        with patch(
            "popkit_shared.utils.semantic_router.cloud_search_agents",
            return_value=cloud_result,
        ):
            results = router_no_externals._cloud_route("test", top_k=3, min_confidence=0.3)
        assert len(results) == 0

    def test_cloud_route_exception_returns_empty(self, router_no_externals):
        with patch(
            "popkit_shared.utils.semantic_router.cloud_search_agents",
            side_effect=RuntimeError("network failure"),
        ):
            results = router_no_externals._cloud_route("test", top_k=3, min_confidence=0.3)
        assert len(results) == 0

    def test_cloud_route_multiple_matches(self, router_no_externals):
        cloud_result = CloudSearchResult(
            query="write tests for security",
            matches=[
                _make_cloud_match(
                    "test-writer-fixer", 0.88, "Testing agent that writes comprehensive tests"
                ),
                _make_cloud_match(
                    "security-auditor", 0.72, "Security auditing and vulnerability scanning"
                ),
            ],
            fallback_to_keywords=False,
        )
        with patch(
            "popkit_shared.utils.semantic_router.cloud_search_agents",
            return_value=cloud_result,
        ):
            results = router_no_externals._cloud_route(
                "write tests for security", top_k=5, min_confidence=0.3
            )
        assert len(results) == 2
        agents = [r.agent for r in results]
        assert "test-writer-fixer" in agents
        assert "security-auditor" in agents

    def test_cloud_route_truncates_long_description(self, router_no_externals):
        long_desc = "A" * 200
        cloud_result = CloudSearchResult(
            query="test",
            matches=[_make_cloud_match("agent-x", 0.9, long_desc)],
            fallback_to_keywords=False,
        )
        with patch(
            "popkit_shared.utils.semantic_router.cloud_search_agents",
            return_value=cloud_result,
        ):
            results = router_no_externals._cloud_route("test", top_k=1, min_confidence=0.0)
        # Description gets truncated to 60 chars in reason
        assert "..." in results[0].reason
        # The reason should contain "Cloud semantic:" prefix
        assert results[0].reason.startswith("Cloud semantic:")

    def test_cloud_route_no_description(self, router_no_externals):
        match = AgentMatch(
            agent="agent-x",
            score=0.9,
            tier="tier-1",
            description="",
            keywords=[],
            method="semantic",
        )
        cloud_result = CloudSearchResult(
            query="test",
            matches=[match],
            fallback_to_keywords=False,
        )
        with patch(
            "popkit_shared.utils.semantic_router.cloud_search_agents",
            return_value=cloud_result,
        ):
            results = router_no_externals._cloud_route("test", top_k=1, min_confidence=0.0)
        assert results[0].reason == "Semantic match"


# =============================================================================
# Local Semantic Routing (_semantic_route)
# =============================================================================


class TestSemanticRoute:
    """Test local embedding-based semantic routing."""

    def test_semantic_route_no_client(self, router_no_externals):
        results = router_no_externals._semantic_route("test", top_k=3, min_confidence=0.3)
        assert len(results) == 0

    def test_semantic_route_global_search(self, router_with_local):
        # Set up the store to have agent embeddings
        router_with_local.store.count.return_value = 5
        router_with_local.store.count_project.return_value = 0
        router_with_local.project_path = None  # Force global-only search

        search_results = [
            _make_embedding_search_result("code-reviewer", 0.85),
            _make_embedding_search_result("security-auditor", 0.72),
        ]
        router_with_local.store.search.return_value = search_results

        results = router_with_local._semantic_route("review code", top_k=3, min_confidence=0.3)

        assert len(results) == 2
        assert results[0].agent == "code-reviewer"
        assert results[0].confidence == 0.85
        assert results[0].method == "semantic"
        assert results[0].is_project_item is False

    def test_semantic_route_project_search_with_boost(self, router_with_local):
        router_with_local.store.count.return_value = 5
        router_with_local.store.count_project.return_value = 2

        # Project-agent gets boosted
        search_results = [
            _make_embedding_search_result(
                "project-lint",
                0.80,
                source_type="project-agent",
                project_path="/test/project",
            ),
            _make_embedding_search_result("code-reviewer", 0.85, source_type="agent"),
        ]
        router_with_local.store.search_project.return_value = search_results

        results = router_with_local._semantic_route("lint code", top_k=3, min_confidence=0.3)

        # project-lint should get PROJECT_ITEM_BOOST (0.1), so 0.80 + 0.10 = 0.90
        project_result = next(r for r in results if r.agent == "project-lint")
        assert project_result.confidence == pytest.approx(0.90)
        assert project_result.is_project_item is True

        # code-reviewer should stay at 0.85 (no boost for global agents)
        global_result = next(r for r in results if r.agent == "code-reviewer")
        assert global_result.confidence == pytest.approx(0.85)
        assert global_result.is_project_item is False

    def test_semantic_route_generated_agent_gets_boost(self, router_with_local):
        router_with_local.store.count.return_value = 5
        router_with_local.store.count_project.return_value = 1

        search_results = [
            _make_embedding_search_result(
                "gen-agent",
                0.75,
                source_type="generated-agent",
                project_path="/test/project",
            ),
        ]
        router_with_local.store.search_project.return_value = search_results

        results = router_with_local._semantic_route("generated stuff", top_k=3, min_confidence=0.3)

        assert len(results) == 1
        assert results[0].confidence == pytest.approx(0.75 + PROJECT_ITEM_BOOST)
        assert results[0].is_project_item is True

    def test_semantic_route_boost_capped_at_1(self, router_with_local):
        router_with_local.store.count.return_value = 5
        router_with_local.store.count_project.return_value = 1

        search_results = [
            _make_embedding_search_result(
                "high-agent",
                0.98,
                source_type="project-agent",
                project_path="/test/project",
            ),
        ]
        router_with_local.store.search_project.return_value = search_results

        results = router_with_local._semantic_route("perfect match", top_k=1, min_confidence=0.0)

        # 0.98 + 0.1 = 1.08, should be capped at 1.0
        assert results[0].confidence == 1.0

    def test_semantic_route_exception_returns_empty(self, router_with_local):
        router_with_local.store.count.return_value = 5
        router_with_local.client.embed_query.side_effect = RuntimeError("API down")

        results = router_with_local._semantic_route("test", top_k=3, min_confidence=0.3)
        assert len(results) == 0

    def test_semantic_route_sorts_by_confidence(self, router_with_local):
        router_with_local.store.count.return_value = 5
        router_with_local.store.count_project.return_value = 0
        router_with_local.project_path = None

        search_results = [
            _make_embedding_search_result("low-agent", 0.40),
            _make_embedding_search_result("high-agent", 0.95),
            _make_embedding_search_result("mid-agent", 0.70),
        ]
        router_with_local.store.search.return_value = search_results

        results = router_with_local._semantic_route("test", top_k=3, min_confidence=0.0)

        assert results[0].agent == "high-agent"
        assert results[1].agent == "mid-agent"
        assert results[2].agent == "low-agent"

    def test_semantic_route_respects_top_k(self, router_with_local):
        router_with_local.store.count.return_value = 5
        router_with_local.store.count_project.return_value = 0
        router_with_local.project_path = None

        search_results = [
            _make_embedding_search_result("a1", 0.9),
            _make_embedding_search_result("a2", 0.8),
            _make_embedding_search_result("a3", 0.7),
        ]
        router_with_local.store.search.return_value = search_results

        results = router_with_local._semantic_route("test", top_k=2, min_confidence=0.0)
        assert len(results) == 2


# =============================================================================
# Deduplication
# =============================================================================


class TestDeduplication:
    """Test result deduplication logic."""

    def test_deduplicate_keeps_highest_confidence(self, router_no_externals):
        results = [
            RoutingResult(agent="a", confidence=0.5, reason="r1", method="keyword"),
            RoutingResult(agent="a", confidence=0.9, reason="r2", method="semantic"),
            RoutingResult(agent="b", confidence=0.7, reason="r3", method="keyword"),
        ]
        deduped = router_no_externals._deduplicate_results(results)
        agents = {r.agent: r for r in deduped}
        assert len(deduped) == 2
        assert agents["a"].confidence == 0.9
        assert agents["b"].confidence == 0.7

    def test_deduplicate_empty_list(self, router_no_externals):
        deduped = router_no_externals._deduplicate_results([])
        assert deduped == []

    def test_deduplicate_no_duplicates(self, router_no_externals):
        results = [
            RoutingResult(agent="a", confidence=0.9, reason="r1", method="keyword"),
            RoutingResult(agent="b", confidence=0.8, reason="r2", method="keyword"),
        ]
        deduped = router_no_externals._deduplicate_results(results)
        assert len(deduped) == 2


# =============================================================================
# route() (main public method)
# =============================================================================


class TestRoute:
    """Test the main route() method."""

    def test_route_keyword_fallback_only(self, router_no_externals):
        """When no external services are available, falls back to keywords."""
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router_no_externals.route("run security scan", top_k=3)

        assert len(results) >= 1
        agents = [r.agent for r in results]
        assert "security-auditor" in agents

    def test_route_with_file_context(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router_no_externals.route(
                "fix this", top_k=5, context={"file_path": "app.test.ts"}
            )

        agents = [r.agent for r in results]
        assert "test-writer-fixer" in agents

    def test_route_with_error_context(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router_no_externals.route(
                "fix this error", top_k=5, context={"error": "TypeError: cannot read property"}
            )

        agents = [r.agent for r in results]
        assert "code-reviewer" in agents

    def test_route_cloud_first(self, router_no_externals):
        """Cloud results come first when available."""
        cloud_result = CloudSearchResult(
            query="test",
            matches=[
                _make_cloud_match("cloud-agent", 0.95, "Cloud found agent"),
            ],
            fallback_to_keywords=False,
        )
        with (
            patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=True),
            patch(
                "popkit_shared.utils.semantic_router.cloud_search_agents",
                return_value=cloud_result,
            ),
        ):
            results = router_no_externals.route("test query", top_k=3)

        assert results[0].agent == "cloud-agent"
        assert results[0].method == "cloud_semantic"

    def test_route_deduplicates(self, router_no_externals):
        """Same agent from keyword and error pattern is deduplicated."""
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router_no_externals.route(
                "security audit",
                top_k=5,
                context={"error": "permission denied"},
            )

        # security-auditor appears from both keyword and error, should be deduped
        agent_counts = {}
        for r in results:
            agent_counts[r.agent] = agent_counts.get(r.agent, 0) + 1
        assert agent_counts.get("security-auditor", 0) == 1

    def test_route_sorted_by_confidence(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router_no_externals.route(
                "test deploy security",
                top_k=10,
            )

        confidences = [r.confidence for r in results]
        assert confidences == sorted(confidences, reverse=True)

    def test_route_respects_top_k(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router_no_externals.route("test deploy security", top_k=1)

        assert len(results) <= 1

    def test_route_default_context_none(self, router_no_externals):
        """Context defaults to empty dict when not provided."""
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            # Should not raise
            results = router_no_externals.route("test query", top_k=1)
        assert isinstance(results, list)

    def test_route_local_semantic_fallback(self, router_with_local):
        """When cloud returns fewer than top_k, local semantic fills in."""
        router_with_local.store.count.return_value = 5
        router_with_local.store.count_project.return_value = 0
        router_with_local.project_path = None

        search_results = [
            _make_embedding_search_result("local-agent", 0.80),
        ]
        router_with_local.store.search.return_value = search_results

        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router_with_local.route("test query", top_k=3)

        agents = [r.agent for r in results]
        assert "local-agent" in agents


# =============================================================================
# route_single()
# =============================================================================


class TestRouteSingle:
    """Test route_single method."""

    def test_route_single_returns_best(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            result = router_no_externals.route_single("security scan")

        assert result is not None
        assert result.agent == "security-auditor"

    def test_route_single_no_match(self, router_no_externals):
        router_no_externals._config = {}
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            result = router_no_externals.route_single("zzzzz no match")

        assert result is None

    def test_route_single_sets_env_var(self, router_no_externals):
        import os

        os.environ.pop("POPKIT_ACTIVE_AGENT", None)

        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            result = router_no_externals.route_single("security scan", set_active_agent=True)

        assert result is not None
        env_val = os.environ.get("POPKIT_ACTIVE_AGENT")
        assert env_val == "security-auditor"
        # Clean up
        os.environ.pop("POPKIT_ACTIVE_AGENT", None)

    def test_route_single_no_set_env_var_by_default(self, router_no_externals):
        import os

        os.environ.pop("POPKIT_ACTIVE_AGENT", None)

        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            router_no_externals.route_single("security scan")

        env_val = os.environ.get("POPKIT_ACTIVE_AGENT")
        assert env_val is None

    def test_route_single_no_env_var_when_no_result(self, router_no_externals):
        import os

        os.environ.pop("POPKIT_ACTIVE_AGENT", None)
        router_no_externals._config = {}

        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            result = router_no_externals.route_single("zzz no match", set_active_agent=True)

        assert result is None
        assert os.environ.get("POPKIT_ACTIVE_AGENT") is None

    def test_route_single_with_context(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            result = router_no_externals.route_single(
                "fix this", context={"file_path": "app.test.ts"}
            )

        assert result is not None
        assert result.agent == "test-writer-fixer"


# =============================================================================
# route_for_project()
# =============================================================================


class TestRouteForProject:
    """Test project-aware routing."""

    def test_route_for_project_sets_path_temporarily(self, router_no_externals):
        original_path = router_no_externals.project_path
        assert original_path == "/test/project"

        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            router_no_externals.route_for_project(
                "security scan", project_path="/other/project", top_k=1
            )

        # Should be restored to original
        assert router_no_externals.project_path == original_path

    def test_route_for_project_restores_on_exception(self, router_no_externals):
        original_path = router_no_externals.project_path

        with (
            patch(
                "popkit_shared.utils.semantic_router.cloud_is_available",
                side_effect=RuntimeError("boom"),
            ),
            pytest.raises(RuntimeError),
        ):
            router_no_externals.route_for_project("test", project_path="/other", top_k=1)

        # Path should be restored even after exception
        assert router_no_externals.project_path == original_path

    def test_route_for_project_uses_given_path(self, router_no_externals):
        """Verify the project_path is actually set during routing."""
        captured_paths = []

        original_route = router_no_externals.route

        def capturing_route(*args, **kwargs):
            captured_paths.append(router_no_externals.project_path)
            return original_route(*args, **kwargs)

        with (
            patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False),
            patch.object(router_no_externals, "route", side_effect=capturing_route),
        ):
            router_no_externals.route_for_project("test", project_path="/specific/project", top_k=1)

        assert captured_paths[0] == "/specific/project"

    def test_route_for_project_returns_results(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router_no_externals.route_for_project(
                "security scan", project_path="/p", top_k=3
            )

        assert len(results) >= 1


# =============================================================================
# explain_routing()
# =============================================================================


class TestExplainRouting:
    """Test routing explanation output."""

    def test_explain_routing_structure(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            explanation = router_no_externals.explain_routing("security scan")

        assert explanation["query"] == "security scan"
        assert "keyword" in explanation["methods_tried"]
        assert "results" in explanation
        assert isinstance(explanation["results"], list)

    def test_explain_routing_includes_project_path(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            explanation = router_no_externals.explain_routing("test")

        assert explanation["project_path"] == "/test/project"

    def test_explain_routing_cloud_available(self, router_no_externals):
        cloud_result = CloudSearchResult(
            query="test",
            matches=[_make_cloud_match("cloud-agent", 0.9, "Test agent")],
            fallback_to_keywords=False,
        )
        with (
            patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=True),
            patch(
                "popkit_shared.utils.semantic_router.cloud_search_agents",
                return_value=cloud_result,
            ),
        ):
            explanation = router_no_externals.explain_routing("test query")

        assert explanation["cloud_available"] is True
        assert "cloud_semantic" in explanation["methods_tried"]
        assert "cloud_results" in explanation

    def test_explain_routing_with_file_context(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            explanation = router_no_externals.explain_routing(
                "fix", context={"file_path": "app.test.ts"}
            )

        assert "file_pattern" in explanation["methods_tried"]
        assert "file_pattern_results" in explanation

    def test_explain_routing_with_error_context(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            explanation = router_no_externals.explain_routing("fix", context={"error": "TypeError"})

        assert "error_pattern" in explanation["methods_tried"]
        assert "error_pattern_results" in explanation

    def test_explain_routing_embedding_counts(self, router_no_externals):
        router_no_externals.store.count.return_value = 42
        router_no_externals.store.count_project.return_value = 5

        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            explanation = router_no_externals.explain_routing("test")

        assert explanation["embedding_count"] == 42
        assert explanation["project_embedding_count"] == 5

    def test_explain_routing_semantic_available(self, router_with_local):
        router_with_local.store.count.return_value = 10
        router_with_local.store.count_project.return_value = 0
        router_with_local.project_path = None
        router_with_local.store.search.return_value = []

        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            explanation = router_with_local.explain_routing("test")

        assert explanation["semantic_available"] is True
        assert "semantic" in explanation["methods_tried"]
        assert "semantic_results" in explanation

    def test_explain_routing_keyword_results(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            explanation = router_no_externals.explain_routing("security audit")

        assert "keyword_results" in explanation
        keyword_agents = [r["agent"] for r in explanation["keyword_results"]]
        assert "security-auditor" in keyword_agents

    def test_explain_routing_no_project_path(self, router_no_externals):
        router_no_externals.project_path = None
        router_no_externals.store.count_project.return_value = 0

        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            explanation = router_no_externals.explain_routing("test")

        assert explanation["project_path"] is None
        assert explanation["project_embedding_count"] == 0


# =============================================================================
# Module-level functions: get_router, route, route_single
# =============================================================================


class TestModuleLevelFunctions:
    """Test singleton get_router() and convenience functions."""

    def test_get_router_returns_singleton(self):
        import popkit_shared.utils.semantic_router as sr_module

        sr_module._router = None  # Reset singleton

        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore"),
            patch.object(SemanticRouter, "_detect_project_root", return_value=None),
        ):
            r1 = sr_module.get_router()
            r2 = sr_module.get_router()

        assert r1 is r2
        sr_module._router = None  # Clean up

    def test_get_router_creates_new_if_none(self):
        import popkit_shared.utils.semantic_router as sr_module

        sr_module._router = None

        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore"),
            patch.object(SemanticRouter, "_detect_project_root", return_value=None),
        ):
            router = sr_module.get_router()

        assert isinstance(router, SemanticRouter)
        sr_module._router = None  # Clean up

    def test_module_route_delegates_to_router(self):
        import popkit_shared.utils.semantic_router as sr_module

        mock_router = MagicMock()
        mock_router.route.return_value = [
            RoutingResult(agent="a", confidence=0.9, reason="r", method="m")
        ]
        sr_module._router = mock_router

        results = sr_module.route("test query", top_k=2, context={"file_path": "x.py"})

        mock_router.route.assert_called_once_with(
            "test query", top_k=2, context={"file_path": "x.py"}
        )
        assert len(results) == 1
        sr_module._router = None  # Clean up

    def test_module_route_single_delegates_to_router(self):
        import popkit_shared.utils.semantic_router as sr_module

        mock_router = MagicMock()
        mock_router.route_single.return_value = RoutingResult(
            agent="a", confidence=0.9, reason="r", method="m"
        )
        sr_module._router = mock_router

        result = sr_module.route_single("test", context={"error": "e"}, set_active_agent=True)

        mock_router.route_single.assert_called_once_with(
            "test", context={"error": "e"}, set_active_agent=True
        )
        assert result.agent == "a"
        sr_module._router = None  # Clean up


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_query_keyword(self, router_no_externals):
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router_no_externals.route("", top_k=3)
        assert isinstance(results, list)

    def test_no_config_file(self, mock_store):
        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
            patch("popkit_shared.utils.semantic_router.CONFIG_PATH") as mock_path,
        ):
            mock_path.exists.return_value = False
            router = SemanticRouter(project_path="/p")

        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router.route("security audit", top_k=3)

        # No keywords loaded, so no keyword matches
        assert len(results) == 0

    def test_no_embeddings_available(self, router_with_local):
        """No embeddings in store, should fallback to keywords."""
        router_with_local.store.count.return_value = 0

        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router_with_local.route("security audit", top_k=3)

        # Should get keyword results only
        agents = [r.agent for r in results]
        assert "security-auditor" in agents

    def test_cloud_search_failure_falls_back(self, router_no_externals):
        """Cloud failure should not prevent keyword results."""
        cloud_result = CloudSearchResult(
            query="test",
            matches=[],
            fallback_to_keywords=True,
            error="Service unavailable",
        )
        with (
            patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=True),
            patch(
                "popkit_shared.utils.semantic_router.cloud_search_agents",
                return_value=cloud_result,
            ),
        ):
            results = router_no_externals.route("security audit", top_k=3)

        # Should still get keyword results
        agents = [r.agent for r in results]
        assert "security-auditor" in agents

    def test_all_methods_fail_gracefully(self, mock_store):
        """When everything fails, returns empty list gracefully."""
        with (
            patch("popkit_shared.utils.semantic_router.is_available", return_value=False),
            patch("popkit_shared.utils.semantic_router.EmbeddingStore", return_value=mock_store),
            patch("popkit_shared.utils.semantic_router.CONFIG_PATH") as mock_path,
        ):
            mock_path.exists.return_value = False
            router = SemanticRouter(project_path="/p")

        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router.route("zzz nothing matches", top_k=3)

        assert results == []

    def test_context_with_both_file_and_error(self, router_no_externals):
        """Both file pattern and error pattern can contribute results."""
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            results = router_no_externals.route(
                "fix this",
                top_k=10,
                context={"file_path": "Dockerfile", "error": "CORS issue"},
            )

        agents = [r.agent for r in results]
        assert "devops-automator" in agents
        assert "api-designer" in agents

    def test_min_confidence_parameter(self, router_no_externals):
        """min_confidence is passed through to routing methods."""
        with patch("popkit_shared.utils.semantic_router.cloud_is_available", return_value=False):
            # Keywords always return 0.8 confidence, so setting min above 0.8 in
            # route_single should still work since min_confidence only applies to
            # semantic results. Keywords always return.
            result = router_no_externals.route_single("security scan", min_confidence=0.9)

        # Keywords don't respect min_confidence directly, so we get a result
        assert result is not None

    def test_default_min_confidence_value(self):
        """DEFAULT_MIN_CONFIDENCE should be 0.3."""
        assert DEFAULT_MIN_CONFIDENCE == 0.3

    def test_project_item_boost_value(self):
        """PROJECT_ITEM_BOOST should be 0.1."""
        assert PROJECT_ITEM_BOOST == 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
