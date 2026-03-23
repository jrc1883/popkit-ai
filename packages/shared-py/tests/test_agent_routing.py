#!/usr/bin/env python3
"""
Tests for agent routing accuracy (Issue #10).

Tests keyword routing, file pattern routing, error pattern routing,
combined routing, false positive prevention, config loading, and
fallback behavior.
"""

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from popkit_shared.utils.agent_loader import (
    _ROUTING_CONFIG_PATH,
    ERROR_PATTERN_SIMILARITY,
    FILE_PATTERN_SIMILARITY,
    KEYWORD_SIMILARITY,
    TIER_MAP,
    AgentLoader,
    _load_routing_config,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def config_path():
    """Return the path to the routing config file."""
    return _ROUTING_CONFIG_PATH


@pytest.fixture
def routing_config(config_path):
    """Load the routing config."""
    config = _load_routing_config(config_path)
    assert config is not None, f"routing_config.json not found at {config_path}"
    return config


@pytest.fixture
def loader():
    """Create an AgentLoader with embeddings disabled (keyword-only mode)."""
    return AgentLoader(use_embeddings=False, always_include_tier1=False)


@pytest.fixture
def loader_with_tier1():
    """Create an AgentLoader with embeddings disabled and tier1 enabled."""
    return AgentLoader(use_embeddings=False, always_include_tier1=True)


def _agent_ids(results: list[dict[str, Any]]) -> set[str]:
    """Extract agent IDs from results as a set."""
    return {r["agent_id"] for r in results}


# =============================================================================
# CONFIG LOADING TESTS
# =============================================================================


class TestConfigLoading:
    """Tests for routing_config.json loading and structure."""

    def test_config_file_exists(self, config_path):
        """routing_config.json must exist."""
        assert config_path.exists(), f"Config file not found: {config_path}"

    def test_config_is_valid_json(self, config_path):
        """routing_config.json must be valid JSON."""
        content = config_path.read_text(encoding="utf-8")
        config = json.loads(content)
        assert isinstance(config, dict)

    def test_config_has_required_sections(self, routing_config):
        """Config must have keywords, file_patterns, and error_patterns."""
        assert "keywords" in routing_config
        assert "file_patterns" in routing_config
        assert "error_patterns" in routing_config

    def test_config_keywords_has_all_24_agents(self, routing_config):
        """Keywords section must cover all 24 agents."""
        expected_agents = set(TIER_MAP.keys())
        config_agents = set(routing_config["keywords"].keys())
        missing = expected_agents - config_agents
        assert not missing, f"Missing agents in keywords config: {missing}"

    def test_config_keywords_are_lists(self, routing_config):
        """All keyword values must be lists of strings."""
        for agent, keywords in routing_config["keywords"].items():
            assert isinstance(keywords, list), f"{agent} keywords is not a list"
            assert len(keywords) > 0, f"{agent} has no keywords"
            for kw in keywords:
                assert isinstance(kw, str), f"{agent} keyword {kw!r} is not a string"

    def test_config_file_patterns_are_lists(self, routing_config):
        """All file pattern values must be lists of strings."""
        for agent, patterns in routing_config["file_patterns"].items():
            assert isinstance(patterns, list), f"{agent} file_patterns is not a list"
            for p in patterns:
                assert isinstance(p, str), f"{agent} pattern {p!r} is not a string"

    def test_config_error_patterns_are_lists(self, routing_config):
        """All error pattern values must be lists of strings."""
        for agent, patterns in routing_config["error_patterns"].items():
            assert isinstance(patterns, list), f"{agent} error_patterns is not a list"
            for p in patterns:
                assert isinstance(p, str), f"{agent} pattern {p!r} is not a string"

    def test_load_config_returns_none_for_missing_file(self, tmp_path):
        """Config loader returns None for missing file."""
        result = _load_routing_config(tmp_path / "nonexistent.json")
        assert result is None

    def test_load_config_returns_none_for_invalid_json(self, tmp_path):
        """Config loader returns None for invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json {{{", encoding="utf-8")
        result = _load_routing_config(bad_file)
        assert result is None


# =============================================================================
# KEYWORD ROUTING TESTS
# =============================================================================


class TestKeywordRouting:
    """Tests for keyword-based agent routing across all 24 agents."""

    @pytest.mark.parametrize(
        "query,expected_agent",
        [
            ("I found a bug in the login flow", "bug-whisperer"),
            ("debug this crash in production", "bug-whisperer"),
            ("fix this broken endpoint", "bug-whisperer"),
            ("there is an error in the parser", "bug-whisperer"),
        ],
    )
    def test_bug_whisperer_keywords(self, loader, query, expected_agent):
        results = loader.load(query, top_k=10)
        assert expected_agent in _agent_ids(results)

    @pytest.mark.parametrize(
        "query,expected_agent",
        [
            ("run a security audit on this code", "security-auditor"),
            ("check for vulnerability in auth module", "security-auditor"),
            ("fix the csrf protection", "security-auditor"),
            ("add xss sanitization", "security-auditor"),
            ("oauth integration is broken", "security-auditor"),
        ],
    )
    def test_security_auditor_keywords(self, loader, query, expected_agent):
        results = loader.load(query, top_k=10)
        assert expected_agent in _agent_ids(results)

    @pytest.mark.parametrize(
        "query,expected_agent",
        [
            ("write a test for the user service", "test-writer-fixer"),
            ("increase test coverage for auth", "test-writer-fixer"),
            ("the jest spec is failing", "test-writer-fixer"),
            ("fix the pytest fixture", "test-writer-fixer"),
        ],
    )
    def test_test_writer_fixer_keywords(self, loader, query, expected_agent):
        results = loader.load(query, top_k=10)
        assert expected_agent in _agent_ids(results)

    @pytest.mark.parametrize(
        "query,expected_agent",
        [
            ("optimize the slow database query", "performance-optimizer"),
            ("improve performance of the search", "performance-optimizer"),
            ("add caching to reduce latency", "performance-optimizer"),
            ("profiling shows memory bottleneck", "performance-optimizer"),
        ],
    )
    def test_performance_optimizer_keywords(self, loader, query, expected_agent):
        results = loader.load(query, top_k=10)
        assert expected_agent in _agent_ids(results)

    @pytest.mark.parametrize(
        "query,expected_agent",
        [
            ("review this code for quality", "code-reviewer"),
            ("run lint on the project", "code-reviewer"),
            ("check code quality standards", "code-reviewer"),
        ],
    )
    def test_code_reviewer_keywords(self, loader, query, expected_agent):
        results = loader.load(query, top_k=10)
        assert expected_agent in _agent_ids(results)

    @pytest.mark.parametrize(
        "query,expected_agent",
        [
            ("refactor the authentication module", "refactoring-expert"),
            ("restructure the project layout", "refactoring-expert"),
            ("simplify this complex function", "refactoring-expert"),
            ("extract a reusable helper", "refactoring-expert"),
        ],
    )
    def test_refactoring_expert_keywords(self, loader, query, expected_agent):
        results = loader.load(query, top_k=10)
        assert expected_agent in _agent_ids(results)

    @pytest.mark.parametrize(
        "query,expected_agent",
        [
            ("design a new api endpoint", "api-designer"),
            ("add a rest endpoint for users", "api-designer"),
            ("the graphql schema needs updating", "api-designer"),
            ("create swagger documentation", "api-designer"),
        ],
    )
    def test_api_designer_keywords(self, loader, query, expected_agent):
        results = loader.load(query, top_k=10)
        assert expected_agent in _agent_ids(results)

    @pytest.mark.parametrize(
        "query,expected_agent",
        [
            ("update the docs for the new feature", "documentation-maintainer"),
            ("add documentation for the api", "documentation-maintainer"),
            ("update the readme with examples", "documentation-maintainer"),
            ("add jsdoc comments to functions", "documentation-maintainer"),
        ],
    )
    def test_documentation_maintainer_keywords(self, loader, query, expected_agent):
        results = loader.load(query, top_k=10)
        assert expected_agent in _agent_ids(results)

    @pytest.mark.parametrize(
        "query,expected_agent",
        [
            ("fix accessibility issues on the form", "accessibility-guardian"),
            ("add a11y support to the nav", "accessibility-guardian"),
            ("check wcag compliance", "accessibility-guardian"),
            ("add aria labels to buttons", "accessibility-guardian"),
        ],
    )
    def test_accessibility_guardian_keywords(self, loader, query, expected_agent):
        results = loader.load(query, top_k=10)
        assert expected_agent in _agent_ids(results)

    @pytest.mark.parametrize(
        "query,expected_agent",
        [
            ("migrate the database to v2", "migration-specialist"),
            ("upgrade react to the latest version", "migration-specialist"),
            ("handle the breaking change in the api", "migration-specialist"),
        ],
    )
    def test_migration_specialist_keywords(self, loader, query, expected_agent):
        results = loader.load(query, top_k=10)
        assert expected_agent in _agent_ids(results)

    @pytest.mark.parametrize(
        "query,expected_agent",
        [
            ("analyze the bundle size", "bundle-analyzer"),
            ("configure webpack for code splitting", "bundle-analyzer"),
            ("reduce the chunk size with vite", "bundle-analyzer"),
        ],
    )
    def test_bundle_analyzer_keywords(self, loader, query, expected_agent):
        results = loader.load(query, top_k=10)
        assert expected_agent in _agent_ids(results)

    def test_dead_code_eliminator_keyword(self, loader):
        results = loader.load("remove unused imports and dead code", top_k=10)
        assert "dead-code-eliminator" in _agent_ids(results)

    def test_deployment_validator_keyword(self, loader):
        results = loader.load("deploy the app to production", top_k=10)
        assert "deployment-validator" in _agent_ids(results)

    def test_rollback_specialist_keyword(self, loader):
        results = loader.load("rollback the last release", top_k=10)
        assert "rollback-specialist" in _agent_ids(results)

    def test_merge_conflict_resolver_keyword(self, loader):
        results = loader.load("resolve the merge conflict", top_k=10)
        assert "merge-conflict-resolver" in _agent_ids(results)

    def test_rapid_prototyper_keyword(self, loader):
        results = loader.load("scaffold a prototype for the new feature", top_k=10)
        assert "rapid-prototyper" in _agent_ids(results)

    def test_prd_parser_keyword(self, loader):
        results = loader.load("parse the prd and extract requirements", top_k=10)
        assert "prd-parser" in _agent_ids(results)

    def test_feature_prioritizer_keyword(self, loader):
        results = loader.load("prioritize the backlog items", top_k=10)
        assert "feature-prioritizer" in _agent_ids(results)

    def test_researcher_keyword(self, loader):
        results = loader.load("research alternatives for the cache layer", top_k=10)
        assert "researcher" in _agent_ids(results)

    def test_code_explorer_keyword(self, loader):
        results = loader.load("explore the codebase to find auth logic", top_k=10)
        assert "code-explorer" in _agent_ids(results)

    def test_code_architect_keyword(self, loader):
        results = loader.load("design the architecture for the new service", top_k=10)
        assert "code-architect" in _agent_ids(results)

    def test_meta_agent_keyword(self, loader):
        results = loader.load("create a new agent for code analysis", top_k=10)
        assert "meta-agent" in _agent_ids(results)

    def test_power_coordinator_keyword(self, loader):
        results = loader.load("run parallel analysis in power mode", top_k=10)
        assert "power-coordinator" in _agent_ids(results)

    def test_keyword_similarity_score(self, loader):
        """Keyword matches should have KEYWORD_SIMILARITY score."""
        results = loader.load("debug the crash", top_k=10)
        bug_results = [r for r in results if r["agent_id"] == "bug-whisperer"]
        assert len(bug_results) == 1
        assert bug_results[0]["similarity"] == KEYWORD_SIMILARITY


# =============================================================================
# FILE PATTERN ROUTING TESTS
# =============================================================================


class TestFilePatternRouting:
    """Tests for file pattern-based agent routing."""

    def test_test_file_ts(self, loader):
        """*.test.ts should route to test-writer-fixer."""
        results = loader.load("fix the issue in user.test.ts", top_k=10)
        assert "test-writer-fixer" in _agent_ids(results)

    def test_test_file_js(self, loader):
        """*.test.js should route to test-writer-fixer."""
        results = loader.load("update auth.test.js with new cases", top_k=10)
        assert "test-writer-fixer" in _agent_ids(results)

    def test_spec_file(self, loader):
        """*.spec.ts should route to test-writer-fixer."""
        results = loader.load("the file api.spec.ts needs updating", top_k=10)
        assert "test-writer-fixer" in _agent_ids(results)

    def test_pytest_file(self, loader):
        """test_*.py should route to test-writer-fixer."""
        results = loader.load("check test_user.py for failures", top_k=10)
        assert "test-writer-fixer" in _agent_ids(results)

    def test_conftest(self, loader):
        """conftest.py should route to test-writer-fixer."""
        results = loader.load("add a fixture to conftest.py", top_k=10)
        assert "test-writer-fixer" in _agent_ids(results)

    def test_jest_config(self, loader):
        """jest.config.ts should route to test-writer-fixer."""
        results = loader.load("update jest.config.ts coverage settings", top_k=10)
        assert "test-writer-fixer" in _agent_ids(results)

    def test_dockerfile(self, loader):
        """Dockerfile should route to deployment-validator."""
        results = loader.load("optimize the Dockerfile for production", top_k=10)
        assert "deployment-validator" in _agent_ids(results)

    def test_github_workflow(self, loader):
        """*.yml files should route to deployment-validator."""
        results = loader.load("fix ci.yml pipeline failures", top_k=10)
        assert "deployment-validator" in _agent_ids(results)

    def test_security_file(self, loader):
        """Files with 'auth' in name should route to security-auditor."""
        results = loader.load("review src/auth.ts for issues", top_k=10)
        assert "security-auditor" in _agent_ids(results)

    def test_eslint_config(self, loader):
        """.eslintrc.json should route to code-reviewer."""
        results = loader.load("update .eslintrc.json rules", top_k=10)
        assert "code-reviewer" in _agent_ids(results)

    def test_webpack_config(self, loader):
        """webpack.config.js should route to bundle-analyzer."""
        results = loader.load("optimize webpack.config.js splitting", top_k=10)
        assert "bundle-analyzer" in _agent_ids(results)

    def test_migration_file(self, loader):
        """Files with 'migration' should route to migration-specialist."""
        results = loader.load("review 001_migration.sql changes", top_k=10)
        assert "migration-specialist" in _agent_ids(results)

    def test_readme_file(self, loader):
        """README.md should route to documentation-maintainer."""
        results = loader.load("update README.md with new instructions", top_k=10)
        assert "documentation-maintainer" in _agent_ids(results)

    def test_prisma_schema(self, loader):
        """schema.prisma should route to migration-specialist."""
        results = loader.load("add new model to schema.prisma", top_k=10)
        assert "migration-specialist" in _agent_ids(results)

    def test_graphql_file(self, loader):
        """*.graphql should route to api-designer."""
        results = loader.load("update schema.graphql types", top_k=10)
        assert "api-designer" in _agent_ids(results)

    def test_file_pattern_similarity_score(self, loader):
        """File pattern matches should have FILE_PATTERN_SIMILARITY score."""
        results = loader.load("look at conftest.py", top_k=10)
        test_results = [r for r in results if r["agent_id"] == "test-writer-fixer"]
        assert len(test_results) >= 1
        # File pattern match score should be FILE_PATTERN_SIMILARITY
        # (may be higher if keyword also matched)
        assert test_results[0]["similarity"] >= FILE_PATTERN_SIMILARITY


# =============================================================================
# ERROR PATTERN ROUTING TESTS
# =============================================================================


class TestErrorPatternRouting:
    """Tests for error pattern-based agent routing."""

    def test_type_error(self, loader):
        """TypeError should route to bug-whisperer."""
        results = loader.load("getting TypeError: undefined is not a function", top_k=10)
        assert "bug-whisperer" in _agent_ids(results)

    def test_reference_error(self, loader):
        """ReferenceError should route to bug-whisperer."""
        results = loader.load("ReferenceError: x is not defined", top_k=10)
        assert "bug-whisperer" in _agent_ids(results)

    def test_attribute_error(self, loader):
        """AttributeError should route to bug-whisperer."""
        results = loader.load("AttributeError: 'NoneType' has no attribute 'foo'", top_k=10)
        assert "bug-whisperer" in _agent_ids(results)

    def test_cannot_read_property(self, loader):
        """'Cannot read propert' should route to bug-whisperer."""
        results = loader.load("Cannot read properties of null (reading 'map')", top_k=10)
        assert "bug-whisperer" in _agent_ids(results)

    def test_cors_error(self, loader):
        """CORS error should route to security-auditor."""
        results = loader.load("CORS policy blocked the request", top_k=10)
        assert "security-auditor" in _agent_ids(results)

    def test_401_unauthorized(self, loader):
        """401 status should route to security-auditor."""
        results = loader.load("API returns 401 unauthorized for valid token", top_k=10)
        assert "security-auditor" in _agent_ids(results)

    def test_timeout_error(self, loader):
        """TimeoutError should route to performance-optimizer."""
        results = loader.load("TimeoutError: request took too long", top_k=10)
        assert "performance-optimizer" in _agent_ids(results)

    def test_memory_error(self, loader):
        """MemoryError should route to performance-optimizer."""
        results = loader.load("MemoryError: heap out of memory during build", top_k=10)
        assert "performance-optimizer" in _agent_ids(results)

    def test_assertion_error(self, loader):
        """AssertionError should route to test-writer-fixer."""
        results = loader.load("AssertionError: expected 3 to equal 5", top_k=10)
        assert "test-writer-fixer" in _agent_ids(results)

    def test_test_failed(self, loader):
        """'test failed' should route to test-writer-fixer."""
        results = loader.load("3 of 15 test failed in the suite", top_k=10)
        assert "test-writer-fixer" in _agent_ids(results)

    def test_module_not_found(self, loader):
        """ModuleNotFoundError should route to migration-specialist."""
        results = loader.load("ModuleNotFoundError: No module named 'flask'", top_k=10)
        assert "migration-specialist" in _agent_ids(results)

    def test_cannot_find_module(self, loader):
        """'Cannot find module' should route to migration-specialist."""
        results = loader.load("Error: Cannot find module '@/utils/auth'", top_k=10)
        assert "migration-specialist" in _agent_ids(results)

    def test_build_failed(self, loader):
        """'build failed' should route to deployment-validator."""
        results = loader.load("CI pipeline: build failed at step 3", top_k=10)
        assert "deployment-validator" in _agent_ids(results)

    def test_merge_conflict_markers(self, loader):
        """'<<<<<<' should route to merge-conflict-resolver."""
        results = loader.load("File contains <<<<<< conflict markers", top_k=10)
        assert "merge-conflict-resolver" in _agent_ids(results)

    def test_404_error(self, loader):
        """404 should route to api-designer."""
        results = loader.load("GET /api/users returns 404 not found", top_k=10)
        assert "api-designer" in _agent_ids(results)

    def test_econnrefused(self, loader):
        """ECONNREFUSED should route to api-designer."""
        results = loader.load("Error: connect ECONNREFUSED 127.0.0.1:3000", top_k=10)
        assert "api-designer" in _agent_ids(results)

    def test_error_pattern_similarity_score(self, loader):
        """Error pattern matches should have ERROR_PATTERN_SIMILARITY score."""
        results = loader.load("getting TypeError in production", top_k=10)
        bug_results = [r for r in results if r["agent_id"] == "bug-whisperer"]
        assert len(bug_results) >= 1
        # Should have at least error pattern similarity (may be boosted by keyword)
        assert bug_results[0]["similarity"] >= ERROR_PATTERN_SIMILARITY


# =============================================================================
# COMBINED ROUTING TESTS
# =============================================================================


class TestCombinedRouting:
    """Tests for combined routing (keyword + file + error patterns)."""

    def test_keyword_plus_file_pattern(self, loader):
        """Query with both keyword and file path should match correctly."""
        results = loader.load("fix the bug in user.test.ts", top_k=10)
        ids = _agent_ids(results)
        # Should match bug-whisperer (keyword: bug, fix) AND test-writer-fixer (file pattern)
        assert "bug-whisperer" in ids
        assert "test-writer-fixer" in ids

    def test_keyword_plus_error_pattern(self, loader):
        """Query with keyword and error pattern should match correctly."""
        results = loader.load("debug the TypeError in the parser", top_k=10)
        ids = _agent_ids(results)
        # Both keyword "debug" and error "TypeError" should match bug-whisperer
        assert "bug-whisperer" in ids

    def test_file_pattern_plus_error_pattern(self, loader):
        """Query with file and error pattern should match correctly."""
        results = loader.load("CORS error when calling auth.ts endpoint", top_k=10)
        ids = _agent_ids(results)
        # security-auditor should match via both file pattern (*auth*) and error (CORS)
        assert "security-auditor" in ids

    def test_three_signal_match(self, loader):
        """Query with keyword + file + error should match strongly."""
        results = loader.load("test failed in user.test.ts with AssertionError", top_k=10)
        ids = _agent_ids(results)
        # test-writer-fixer: keyword "test", file "*.test.ts", error "AssertionError"
        assert "test-writer-fixer" in ids

    def test_multiple_agents_from_combined(self, loader):
        """Complex query should activate multiple relevant agents."""
        results = loader.load(
            "deploy failed: build error in Dockerfile, security audit needed",
            top_k=10,
        )
        ids = _agent_ids(results)
        # deployment-validator: keyword "deploy", file "Dockerfile", error "build failed"
        assert "deployment-validator" in ids
        # security-auditor: keyword "security"
        assert "security-auditor" in ids

    def test_merged_results_sorted_by_similarity(self, loader):
        """Merged results should be sorted by similarity descending."""
        results = loader.load("debug the TypeError in auth.test.ts", top_k=10)
        for i in range(len(results) - 1):
            assert results[i]["similarity"] >= results[i + 1]["similarity"]

    def test_keyword_match_scores_higher_than_file_pattern(self, loader):
        """Keyword match (0.7) should score higher than file pattern (0.6)."""
        assert KEYWORD_SIMILARITY > FILE_PATTERN_SIMILARITY

    def test_error_pattern_scores_between_keyword_and_file(self, loader):
        """Error pattern (0.65) should score between keyword (0.7) and file (0.6)."""
        assert KEYWORD_SIMILARITY > ERROR_PATTERN_SIMILARITY > FILE_PATTERN_SIMILARITY


# =============================================================================
# FALSE POSITIVE TESTS
# =============================================================================


class TestFalsePositives:
    """Tests to ensure unrelated queries don't trigger wrong agents."""

    def test_unrelated_query_no_security(self, loader):
        """Query about cooking should not trigger security-auditor."""
        results = loader.load("how to make pasta carbonara", top_k=10)
        ids = _agent_ids(results)
        assert "security-auditor" not in ids

    def test_unrelated_query_no_test_writer(self, loader):
        """Query about weather should not trigger test-writer-fixer."""
        results = loader.load("what is the weather forecast for tomorrow", top_k=10)
        ids = _agent_ids(results)
        assert "test-writer-fixer" not in ids

    def test_unrelated_query_no_deployment(self, loader):
        """Generic coding question should not trigger deployment-validator."""
        results = loader.load("how do I sort an array in python", top_k=10)
        ids = _agent_ids(results)
        assert "deployment-validator" not in ids

    def test_version_number_not_file_path(self, loader):
        """Version numbers like 3.2.1 should not be treated as file paths."""
        # If version numbers were treated as files, they might match unexpected patterns
        results = loader.load("update to version 3.2.1 please", top_k=10)
        # Should only match migration-specialist via "update" keyword, not file patterns
        ids = _agent_ids(results)
        assert "migration-specialist" in ids  # keyword: "update"

    def test_url_not_treated_as_file(self, loader):
        """URLs should not be extracted as file paths."""
        paths = AgentLoader._extract_file_paths("visit https://example.com/auth.ts for docs")
        # The http-prefixed path should be filtered out
        assert not any(p.startswith("http") for p in paths)

    def test_empty_query_returns_default(self, loader):
        """Empty query should return default agent (code-reviewer)."""
        results = loader.load("", top_k=5)
        assert len(results) > 0
        # Should have at least code-reviewer as default
        assert "code-reviewer" in _agent_ids(results)

    def test_no_duplicate_agents(self, loader):
        """Results should not contain duplicate agent IDs."""
        results = loader.load("debug the TypeError in auth.test.ts", top_k=20)
        ids = [r["agent_id"] for r in results]
        assert len(ids) == len(set(ids)), f"Duplicate agents found: {ids}"


# =============================================================================
# FALLBACK BEHAVIOR TESTS
# =============================================================================


class TestFallbackBehavior:
    """Tests for fallback behavior when config is missing."""

    def test_loader_works_without_config(self, tmp_path):
        """AgentLoader should work with missing config (fallback to hardcoded)."""
        loader = AgentLoader(
            use_embeddings=False,
            always_include_tier1=False,
            config_path=tmp_path / "missing.json",
        )
        results = loader.load("debug this bug", top_k=10)
        assert "bug-whisperer" in _agent_ids(results)

    def test_fallback_keyword_mapping_covers_main_agents(self, tmp_path):
        """Fallback keywords should cover core agents."""
        loader = AgentLoader(
            use_embeddings=False,
            always_include_tier1=False,
            config_path=tmp_path / "missing.json",
        )
        # Test several key agents with fallback
        test_cases = [
            ("security audit needed", "security-auditor"),
            ("write a test for the service", "test-writer-fixer"),
            ("refactor the auth module", "refactoring-expert"),
            ("deploy to production", "deployment-validator"),
            ("explore the codebase", "code-explorer"),
        ]
        for query, expected in test_cases:
            results = loader.load(query, top_k=10)
            assert expected in _agent_ids(results), (
                f"Fallback failed for query='{query}', expected={expected}"
            )

    def test_fallback_no_file_patterns(self, tmp_path):
        """Without config, file patterns should return empty."""
        loader = AgentLoader(
            use_embeddings=False,
            always_include_tier1=False,
            config_path=tmp_path / "missing.json",
        )
        results = loader._match_file_patterns(["auth.test.ts"])
        assert results == []

    def test_fallback_no_error_patterns(self, tmp_path):
        """Without config, error patterns should return empty."""
        loader = AgentLoader(
            use_embeddings=False,
            always_include_tier1=False,
            config_path=tmp_path / "missing.json",
        )
        results = loader._match_error_patterns("TypeError: undefined")
        assert results == []

    def test_tier1_enforcement(self, loader_with_tier1):
        """When tier1 is enabled and no matches, code-reviewer should be default."""
        results = loader_with_tier1.load("the sky is blue", top_k=5)
        assert "code-reviewer" in _agent_ids(results)


# =============================================================================
# EXTRACT FILE PATHS TESTS
# =============================================================================


class TestExtractFilePaths:
    """Tests for file path extraction from query strings."""

    def test_simple_file_path(self):
        paths = AgentLoader._extract_file_paths("check src/auth.ts")
        assert "src/auth.ts" in paths

    def test_test_file_path(self):
        paths = AgentLoader._extract_file_paths("update user.test.js")
        assert "user.test.js" in paths

    def test_python_file_path(self):
        paths = AgentLoader._extract_file_paths("fix test_user.py")
        assert "test_user.py" in paths

    def test_config_file(self):
        paths = AgentLoader._extract_file_paths("update jest.config.ts")
        assert "jest.config.ts" in paths

    def test_dockerfile_detection(self):
        paths = AgentLoader._extract_file_paths("optimize the Dockerfile")
        assert "Dockerfile" in paths

    def test_no_paths_in_plain_text(self):
        paths = AgentLoader._extract_file_paths("how to sort an array")
        assert len(paths) == 0

    def test_version_number_excluded(self):
        paths = AgentLoader._extract_file_paths("update to version 3.2.1")
        assert "3.2.1" not in paths

    def test_multiple_paths(self):
        paths = AgentLoader._extract_file_paths("compare auth.ts and user.test.ts")
        assert "auth.ts" in paths
        assert "user.test.ts" in paths


# =============================================================================
# MERGE RESULTS TESTS
# =============================================================================


class TestMergeResults:
    """Tests for the result merging logic."""

    def test_merge_deduplicates(self):
        """Merging should deduplicate by agent_id."""
        list_a = [{"agent_id": "bug-whisperer", "similarity": 0.7, "match_source": "keyword"}]
        list_b = [
            {"agent_id": "bug-whisperer", "similarity": 0.65, "match_source": "error_pattern"}
        ]
        merged = AgentLoader._merge_results(list_a, list_b)
        assert len(merged) == 1
        assert merged[0]["agent_id"] == "bug-whisperer"

    def test_merge_keeps_highest_similarity(self):
        """Merging should keep the highest similarity score."""
        list_a = [{"agent_id": "bug-whisperer", "similarity": 0.7, "match_source": "keyword"}]
        list_b = [
            {"agent_id": "bug-whisperer", "similarity": 0.65, "match_source": "error_pattern"}
        ]
        merged = AgentLoader._merge_results(list_a, list_b)
        assert merged[0]["similarity"] == 0.7

    def test_merge_tracks_sources(self):
        """Merging should track all match sources."""
        list_a = [{"agent_id": "test-writer-fixer", "similarity": 0.7, "match_source": "keyword"}]
        list_b = [
            {"agent_id": "test-writer-fixer", "similarity": 0.6, "match_source": "file_pattern"}
        ]
        merged = AgentLoader._merge_results(list_a, list_b)
        assert "keyword" in merged[0]["match_source"]
        assert "file_pattern" in merged[0]["match_source"]

    def test_merge_sorts_by_similarity(self):
        """Merged results should be sorted by similarity descending."""
        list_a = [
            {"agent_id": "code-reviewer", "similarity": 0.5, "match_source": "default"},
        ]
        list_b = [
            {"agent_id": "bug-whisperer", "similarity": 0.7, "match_source": "keyword"},
        ]
        merged = AgentLoader._merge_results(list_a, list_b)
        assert merged[0]["agent_id"] == "bug-whisperer"
        assert merged[1]["agent_id"] == "code-reviewer"

    def test_merge_empty_lists(self):
        """Merging empty lists should return empty list."""
        merged = AgentLoader._merge_results([], [], [])
        assert merged == []

    def test_merge_three_lists(self):
        """Merging three lists should work correctly."""
        list_a = [
            {"agent_id": "a", "similarity": 0.7, "match_source": "keyword"},
        ]
        list_b = [
            {"agent_id": "b", "similarity": 0.65, "match_source": "error_pattern"},
        ]
        list_c = [
            {"agent_id": "c", "similarity": 0.6, "match_source": "file_pattern"},
        ]
        merged = AgentLoader._merge_results(list_a, list_b, list_c)
        assert len(merged) == 3
        assert merged[0]["agent_id"] == "a"
        assert merged[1]["agent_id"] == "b"
        assert merged[2]["agent_id"] == "c"


# =============================================================================
# TIER MAP TESTS
# =============================================================================


class TestTierMap:
    """Tests for tier assignments."""

    def test_tier_map_has_24_agents(self):
        """TIER_MAP should have all 24 agents."""
        assert len(TIER_MAP) == 24

    def test_tier1_count(self):
        """Should have 10 Tier 1 agents."""
        tier1 = [a for a, t in TIER_MAP.items() if t == "tier-1-always-active"]
        assert len(tier1) == 10

    def test_tier2_count(self):
        """Should have 12 Tier 2 agents."""
        tier2 = [a for a, t in TIER_MAP.items() if t == "tier-2-on-demand"]
        assert len(tier2) == 12

    def test_feature_workflow_count(self):
        """Should have 2 Feature Workflow agents."""
        fw = [a for a, t in TIER_MAP.items() if t == "feature-workflow"]
        assert len(fw) == 2

    def test_all_agents_present(self):
        """All 24 expected agents should be in TIER_MAP."""
        expected = {
            "accessibility-guardian",
            "api-designer",
            "documentation-maintainer",
            "migration-specialist",
            "code-reviewer",
            "refactoring-expert",
            "bug-whisperer",
            "performance-optimizer",
            "security-auditor",
            "test-writer-fixer",
            "bundle-analyzer",
            "dead-code-eliminator",
            "devops-automator",
            "feature-prioritizer",
            "meta-agent",
            "power-coordinator",
            "merge-conflict-resolver",
            "prd-parser",
            "rapid-prototyper",
            "deployment-validator",
            "rollback-specialist",
            "researcher",
            "code-explorer",
            "code-architect",
        }
        assert set(TIER_MAP.keys()) == expected
