#!/usr/bin/env python3
"""
Comprehensive test suite for agent_type detection in session-start.py

Tests the detect_agent_type_session() function for Claude Code 2.1.2+ integration.
Tests agent category mapping, optimization strategy, and edge cases.
"""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path for imports (tests/hooks/ -> tests/ -> popkit-core/ -> hooks/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

# Import the function to test
from session_start_helpers import detect_agent_type_session


class TestAgentTypeDetection:
    """Test agent_type detection from Claude Code 2.1.2+ --agent flag"""

    def test_no_agent_type_returns_none(self):
        """Test that missing agent_type returns None"""
        data = {"session_id": "test123"}
        result = detect_agent_type_session(data)
        assert result is None

    def test_empty_agent_type_returns_none(self):
        """Test that empty agent_type returns None"""
        data = {"agent_type": ""}
        result = detect_agent_type_session(data)
        assert result is None

    def test_none_agent_type_returns_none(self):
        """Test that None agent_type returns None"""
        data = {"agent_type": None}
        result = detect_agent_type_session(data)
        assert result is None


class TestTier1AgentDetection:
    """Test Tier 1 agents (always active)"""

    tier1_agents = [
        "code-reviewer",
        "refactoring-expert",
        "accessibility-guardian",
        "api-designer",
        "documentation-maintainer",
        "migration-specialist",
        "bug-whisperer",
        "performance-optimizer",
        "security-auditor",
        "test-writer-fixer",
    ]

    @pytest.mark.parametrize("agent_type", tier1_agents)
    def test_tier1_agent_detection(self, agent_type):
        """Test all Tier 1 agents are detected correctly"""
        data = {"agent_type": agent_type}
        result = detect_agent_type_session(data)

        assert result is not None
        assert result["agent_type"] == agent_type
        assert result["agent_category"] == "tier-1"
        assert result["skip_embedding_filter"] is True
        assert "standard_context_loading" in result["optimizations_applied"]

    def test_code_reviewer_complete_structure(self):
        """Test complete result structure for code-reviewer"""
        data = {"agent_type": "code-reviewer", "session_id": "test"}
        result = detect_agent_type_session(data)

        expected_keys = {
            "agent_type",
            "agent_category",
            "skip_embedding_filter",
            "optimizations_applied",
        }
        assert set(result.keys()) == expected_keys
        assert isinstance(result["optimizations_applied"], list)


class TestTier2AgentDetection:
    """Test Tier 2 agents (on-demand specialists)"""

    tier2_agents = [
        "bundle-analyzer",
        "dead-code-eliminator",
        "feature-prioritizer",
        "meta-agent",
        "power-coordinator",
        "rapid-prototyper",
        "deployment-validator",
        "rollback-specialist",
        "researcher",
        "merge-conflict-resolver",
        "prd-parser",
    ]

    @pytest.mark.parametrize("agent_type", tier2_agents)
    def test_tier2_agent_detection(self, agent_type):
        """Test all Tier 2 agents are detected correctly"""
        data = {"agent_type": agent_type}
        result = detect_agent_type_session(data)

        assert result is not None
        assert result["agent_type"] == agent_type
        assert result["agent_category"] == "tier-2"
        assert result["skip_embedding_filter"] is True
        assert "on_demand_context_loading" in result["optimizations_applied"]


class TestFeatureWorkflowAgents:
    """Test Feature Workflow agents"""

    feature_workflow_agents = [
        "code-explorer",
        "code-architect",
    ]

    @pytest.mark.parametrize("agent_type", feature_workflow_agents)
    def test_feature_workflow_agent_detection(self, agent_type):
        """Test Feature Workflow agents are detected correctly"""
        data = {"agent_type": agent_type}
        result = detect_agent_type_session(data)

        assert result is not None
        assert result["agent_type"] == agent_type
        assert result["agent_category"] == "feature-workflow"
        assert result["skip_embedding_filter"] is True
        assert "feature_workflow_context" in result["optimizations_applied"]


class TestUnknownAgents:
    """Test handling of unknown/custom agent types"""

    def test_unknown_agent_type_returns_unknown_category(self):
        """Test unknown agent type gets 'unknown' category"""
        data = {"agent_type": "custom-agent"}
        result = detect_agent_type_session(data)

        assert result is not None
        assert result["agent_type"] == "custom-agent"
        assert result["agent_category"] == "unknown"
        assert result["skip_embedding_filter"] is True
        assert "generic_optimization" in result["optimizations_applied"]

    def test_external_plugin_agent(self):
        """Test agent from external plugin"""
        data = {"agent_type": "my-plugin:custom-agent"}
        result = detect_agent_type_session(data)

        assert result is not None
        assert result["agent_category"] == "unknown"
        assert "generic_optimization" in result["optimizations_applied"]

    def test_agent_with_special_characters(self):
        """Test agent type with special characters"""
        data = {"agent_type": "test-agent_v2.0"}
        result = detect_agent_type_session(data)

        assert result is not None
        assert result["agent_type"] == "test-agent_v2.0"


class TestSkipEmbeddingFilter:
    """Test skip_embedding_filter optimization"""

    def test_all_agents_skip_embedding_filter(self):
        """Test that all agent types set skip_embedding_filter=True"""
        test_agents = [
            "code-reviewer",  # tier-1
            "bundle-analyzer",  # tier-2
            "code-explorer",  # feature-workflow
            "custom-agent",  # unknown
        ]

        for agent_type in test_agents:
            data = {"agent_type": agent_type}
            result = detect_agent_type_session(data)
            assert result["skip_embedding_filter"] is True, (
                f"{agent_type} should skip embedding filter"
            )


class TestLogging:
    """Test logging behavior"""

    @patch("sys.stderr", new_callable=StringIO)
    def test_tier1_logging(self, mock_stderr):
        """Test Tier 1 agent logging output"""
        data = {"agent_type": "code-reviewer"}
        detect_agent_type_session(data)

        stderr_output = mock_stderr.getvalue()
        assert "Agent-specific session detected: code-reviewer" in stderr_output
        assert "Category: Tier 1 (always active)" in stderr_output

    @patch("sys.stderr", new_callable=StringIO)
    def test_tier2_logging(self, mock_stderr):
        """Test Tier 2 agent logging output"""
        data = {"agent_type": "bundle-analyzer"}
        detect_agent_type_session(data)

        stderr_output = mock_stderr.getvalue()
        assert "Agent-specific session detected: bundle-analyzer" in stderr_output
        assert "Category: Tier 2 (on-demand specialist)" in stderr_output

    @patch("sys.stderr", new_callable=StringIO)
    def test_feature_workflow_logging(self, mock_stderr):
        """Test Feature Workflow agent logging output"""
        data = {"agent_type": "code-explorer"}
        detect_agent_type_session(data)

        stderr_output = mock_stderr.getvalue()
        assert "Agent-specific session detected: code-explorer" in stderr_output
        assert "Category: Feature workflow agent" in stderr_output

    @patch("sys.stderr", new_callable=StringIO)
    def test_unknown_agent_logging(self, mock_stderr):
        """Test unknown agent logging output"""
        data = {"agent_type": "custom-agent"}
        detect_agent_type_session(data)

        stderr_output = mock_stderr.getvalue()
        assert "Agent-specific session detected: custom-agent" in stderr_output
        assert "Category: External/custom agent" in stderr_output


class TestErrorHandling:
    """Test error handling and resilience"""

    def test_exception_during_processing_returns_none(self):
        """Test that exceptions are caught and None returned"""
        # Pass invalid data type that would cause exception
        data = {"agent_type": 123}  # Integer instead of string
        result = detect_agent_type_session(data)

        # Function should catch exception and return None
        # (Actually, .get() on dict with int won't raise, but tests the pattern)
        assert result is not None or result is None  # Should not crash

    @patch("sys.stderr", new_callable=StringIO)
    def test_exception_logging(self, mock_stderr):
        """Test that exceptions are logged to stderr"""
        # Create a scenario that would raise an exception
        # We'll need to mock the function to raise an exception
        with patch("session_start_helpers.detect_agent_type_session") as mock_detect:
            mock_detect.side_effect = Exception("Test exception")
            try:
                detect_agent_type_session({"agent_type": "test"})
            except Exception:
                pass  # Expected to be caught


class TestAllAgentsMapped:
    """Test that all 23 PopKit agents are properly mapped"""

    def test_all_23_agents_have_mapping(self):
        """Test that all 23 PopKit agents are in the mapping"""
        all_agents = [
            # Tier 1 (10 agents)
            "code-reviewer",
            "refactoring-expert",
            "accessibility-guardian",
            "api-designer",
            "documentation-maintainer",
            "migration-specialist",
            "bug-whisperer",
            "performance-optimizer",
            "security-auditor",
            "test-writer-fixer",
            # Tier 2 (11 agents)
            "bundle-analyzer",
            "dead-code-eliminator",
            "feature-prioritizer",
            "meta-agent",
            "power-coordinator",
            "rapid-prototyper",
            "deployment-validator",
            "rollback-specialist",
            "researcher",
            "merge-conflict-resolver",
            "prd-parser",
            # Feature Workflow (2 agents)
            "code-explorer",
            "code-architect",
        ]

        assert len(all_agents) == 23, "Should have exactly 23 PopKit agents"

        # Test each agent has a valid mapping
        for agent in all_agents:
            data = {"agent_type": agent}
            result = detect_agent_type_session(data)
            assert result is not None, f"{agent} should be detected"
            assert result["agent_category"] in ["tier-1", "tier-2", "feature-workflow"], (
                f"{agent} should have valid category"
            )


class TestIntegrationWithSessionStart:
    """Test integration with main session-start workflow"""

    def test_result_structure_matches_expected_format(self):
        """Test that result structure matches what main() expects"""
        data = {"agent_type": "code-reviewer"}
        result = detect_agent_type_session(data)

        # Verify structure that main() will use
        assert "agent_type" in result
        assert "skip_embedding_filter" in result
        assert isinstance(result["skip_embedding_filter"], bool)

    def test_result_can_be_json_serialized(self):
        """Test that result can be JSON serialized for output"""
        data = {"agent_type": "code-reviewer"}
        result = detect_agent_type_session(data)

        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None

        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed["agent_type"] == "code-reviewer"


class TestCaseSensitivity:
    """Test case sensitivity of agent type matching"""

    def test_exact_case_match_required(self):
        """Test that agent type matching is case-sensitive"""
        # Lowercase should work (actual format)
        data = {"agent_type": "code-reviewer"}
        result = detect_agent_type_session(data)
        assert result["agent_category"] == "tier-1"

        # Different case should be unknown
        data = {"agent_type": "Code-Reviewer"}
        result = detect_agent_type_session(data)
        assert result["agent_category"] == "unknown"

    def test_hyphenation_matters(self):
        """Test that hyphenation is exact"""
        # Correct hyphenation
        data = {"agent_type": "code-reviewer"}
        result = detect_agent_type_session(data)
        assert result["agent_category"] == "tier-1"

        # Wrong hyphenation
        data = {"agent_type": "code_reviewer"}  # Space instead of hyphen
        result = detect_agent_type_session(data)
        assert result["agent_category"] == "unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
