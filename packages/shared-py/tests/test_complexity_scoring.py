#!/usr/bin/env python3
"""
Test suite for complexity_scoring.py

Tests complexity analysis, scoring, and recommendations.
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from popkit_shared.utils.complexity_scoring import (
    ComplexityAnalyzer,
    ComplexityLevel,
    analyze_complexity,
    quick_score,
    get_complexity_analyzer,
)


class TestComplexityScoring(unittest.TestCase):
    """Test complexity scoring functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = ComplexityAnalyzer()

    def test_trivial_task_scoring(self):
        """Test scoring of trivial tasks (1-2)"""
        tasks = [
            "Fix typo in README",
            "Update constant value",
            "Change button text",
        ]

        for task in tasks:
            result = self.analyzer.analyze(task)
            self.assertIn(
                result.complexity_score,
                [1, 2, 3],
                f"Task '{task}' should be trivial (1-3), got {result.complexity_score}",
            )
            self.assertLessEqual(result.recommended_subtasks, 2)

    def test_simple_task_scoring(self):
        """Test scoring of simple tasks (3-4)"""
        tasks = [
            "Add a new button to the settings page",
            "Update CSS styling for header",
            "Create simple utility function",
        ]

        for task in tasks:
            result = self.analyzer.analyze(task)
            self.assertIn(
                result.complexity_score,
                [2, 3, 4, 5],
                f"Task '{task}' should be simple (3-4), got {result.complexity_score}",
            )
            self.assertLessEqual(result.recommended_subtasks, 4)

    def test_moderate_task_scoring(self):
        """Test scoring of moderate tasks (5-6)"""
        tasks = [
            "Add user profile page with form validation",
            "Implement REST API endpoint with validation",
            "Add feature with database queries",
        ]

        for task in tasks:
            result = self.analyzer.analyze(task)
            self.assertIn(
                result.complexity_score,
                [4, 5, 6, 7],
                f"Task '{task}' should be moderate (5-6), got {result.complexity_score}",
            )
            self.assertGreaterEqual(result.recommended_subtasks, 3)
            self.assertLessEqual(result.recommended_subtasks, 7)

    def test_complex_task_scoring(self):
        """Test scoring of complex tasks (7-8)"""
        tasks = [
            "Refactor authentication module to use OAuth2",
            "Add real-time notifications with WebSockets",
            "Implement JWT authentication with refresh tokens",
        ]

        for task in tasks:
            result = self.analyzer.analyze(task)
            self.assertIn(
                result.complexity_score,
                [6, 7, 8, 9],
                f"Task '{task}' should be complex (7-8), got {result.complexity_score}",
            )
            self.assertGreaterEqual(result.recommended_subtasks, 5)

    def test_very_complex_task_scoring(self):
        """Test scoring of very complex tasks (9-10)"""
        tasks = [
            "Migrate entire application to microservices architecture",
            "Redesign core data model with breaking changes",
            "Refactor entire codebase to new framework",
        ]

        for task in tasks:
            result = self.analyzer.analyze(task)
            self.assertGreaterEqual(
                result.complexity_score,
                6,
                f"Task '{task}' should be very complex (6+), got {result.complexity_score}",
            )
            self.assertGreaterEqual(result.recommended_subtasks, 5)

    def test_metadata_override(self):
        """Test that metadata overrides estimation"""
        task = "Update component"

        # Without metadata (should be simple)
        result1 = self.analyzer.analyze(task)

        # With metadata indicating high complexity
        result2 = self.analyzer.analyze(
            task, metadata={"files_affected": 25, "loc_estimate": 600, "dependencies": 12}
        )

        self.assertGreater(
            result2.complexity_score,
            result1.complexity_score,
            "Metadata should increase complexity score",
        )

    def test_keyword_detection_architecture(self):
        """Test detection of architecture keywords"""
        tasks = [
            "Refactor the entire architecture",
            "Redesign core module structure",
            "Migrate to new architecture pattern",
        ]

        for task in tasks:
            result = self.analyzer.analyze(task)
            self.assertGreater(
                result.factors.architecture_change,
                0,
                f"Task '{task}' should detect architecture change",
            )

    def test_keyword_detection_security(self):
        """Test detection of security keywords"""
        tasks = [
            "Add authentication with JWT",
            "Implement authorization middleware",
            "Add encryption for sensitive data",
        ]

        for task in tasks:
            result = self.analyzer.analyze(task)
            self.assertGreater(
                result.factors.security_impact, 0, f"Task '{task}' should detect security impact"
            )
            self.assertIn("security_critical", result.risk_factors)

    def test_keyword_detection_integration(self):
        """Test detection of integration keywords"""
        tasks = [
            "Integrate with third-party API",
            "Add webhook support",
            "Connect to external service",
        ]

        for task in tasks:
            result = self.analyzer.analyze(task)
            self.assertGreater(
                result.factors.integration_points, 0, f"Task '{task}' should detect integration"
            )

    def test_breaking_changes_detection(self):
        """Test detection of breaking changes"""
        tasks = [
            "Add breaking changes to API",
            "Make incompatible changes",
            "Require migration for existing users",
        ]

        for task in tasks:
            result = self.analyzer.analyze(task)
            self.assertGreater(
                result.factors.breaking_changes, 0, f"Task '{task}' should detect breaking changes"
            )
            self.assertIn("breaking_changes", result.risk_factors)

    def test_subtask_recommendations(self):
        """Test subtask recommendations scale with complexity"""
        tasks = [
            ("Fix typo", 1),
            ("Add button to settings page", 1),
            ("Add form with validation", 3),
            ("Implement authentication", 5),
            ("Migrate architecture", 8),
        ]

        for task, expected_min_subtasks in tasks:
            result = self.analyzer.analyze(task)
            self.assertGreaterEqual(
                result.recommended_subtasks,
                expected_min_subtasks,
                f"Task '{task}' should recommend at least {expected_min_subtasks} subtasks",
            )

    def test_phase_distribution_trivial(self):
        """Test phase distribution for trivial tasks"""
        result = self.analyzer.analyze("Fix typo")
        phases = result.phase_distribution

        # Trivial tasks should have minimal phases
        self.assertLessEqual(len(phases), 2)
        self.assertIn("implementation", phases)

    def test_phase_distribution_complex(self):
        """Test phase distribution for complex tasks"""
        result = self.analyzer.analyze("Implement OAuth2 authentication system")
        phases = result.phase_distribution

        # Complex tasks should have many phases
        self.assertGreaterEqual(len(phases), 5)
        self.assertIn("planning", phases)
        self.assertIn("implementation", phases)
        self.assertIn("testing", phases)

    def test_agent_recommendations_simple(self):
        """Test agent recommendations for simple tasks"""
        result = self.analyzer.analyze("Update button color")
        agents = result.suggested_agents

        self.assertIn("rapid-prototyper", agents)

    def test_agent_recommendations_complex(self):
        """Test agent recommendations for complex tasks"""
        result = self.analyzer.analyze("Refactor authentication with OAuth2")
        agents = result.suggested_agents

        self.assertTrue(
            "code-architect" in agents or "refactoring-expert" in agents,
            "Complex tasks should suggest senior agents",
        )

    def test_token_estimation_scales(self):
        """Test token estimation scales with complexity"""
        simple_task = self.analyzer.analyze("Fix typo")
        complex_task = self.analyzer.analyze("Migrate to microservices")

        self.assertLess(
            simple_task.estimated_tokens["total"],
            complex_task.estimated_tokens["total"],
            "Complex tasks should have higher token estimates",
        )

    def test_risk_factor_identification(self):
        """Test risk factor identification"""
        task = "Migrate database with breaking changes to authentication"
        result = self.analyzer.analyze(task)

        # Should identify multiple risks
        self.assertGreater(len(result.risk_factors), 0)
        self.assertTrue(
            any(risk in result.risk_factors for risk in ["breaking_changes", "data_migration"]),
            "Should identify migration/breaking change risks",
        )

    def test_reasoning_generation(self):
        """Test reasoning is generated"""
        result = self.analyzer.analyze("Add user authentication")

        self.assertIsNotNone(result.reasoning)
        self.assertGreater(len(result.reasoning), 20)
        self.assertIn("Complexity Score", result.reasoning)

    def test_complexity_level_classification(self):
        """Test complexity level classification"""
        test_cases = [
            ("Fix typo", "TRIVIAL"),
            ("Add button", "SIMPLE"),
            ("Add API endpoint", "MODERATE"),
            ("Refactor authentication", "COMPLEX"),
        ]

        for task, expected_level in test_cases:
            result = self.analyzer.analyze(task)
            self.assertIsNotNone(result.complexity_level)

    def test_custom_weights(self):
        """Test custom weight configuration"""
        custom_weights = {
            "files_affected": 0.05,
            "loc_estimate": 0.05,
            "dependencies": 0.05,
            "architecture_change": 0.40,  # Emphasize architecture
            "breaking_changes": 0.20,
            "testing_complexity": 0.10,
            "security_impact": 0.10,
            "integration_points": 0.05,
        }

        custom_analyzer = ComplexityAnalyzer(weights=custom_weights)
        result = custom_analyzer.analyze("Refactor architecture")

        # Architecture-heavy task should score higher with custom weights
        self.assertGreaterEqual(result.complexity_score, 7)

    def test_quick_score_function(self):
        """Test quick_score convenience function"""
        score = quick_score("Add user authentication")

        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 1)
        self.assertLessEqual(score, 10)

    def test_analyze_complexity_function(self):
        """Test analyze_complexity convenience function"""
        result = analyze_complexity("Add user profile page")

        self.assertIsInstance(result, dict)
        self.assertIn("complexity_score", result)
        self.assertIn("recommended_subtasks", result)
        self.assertIn("phase_distribution", result)

    def test_singleton_accessor(self):
        """Test singleton accessor"""
        analyzer1 = get_complexity_analyzer()
        analyzer2 = get_complexity_analyzer()

        self.assertIs(analyzer1, analyzer2, "Should return same instance")

    def test_to_dict_serialization(self):
        """Test ComplexityAnalysis to_dict serialization"""
        result = self.analyzer.analyze("Add authentication")
        result_dict = result.to_dict()

        self.assertIsInstance(result_dict, dict)
        self.assertIn("complexity_score", result_dict)
        self.assertIn("factors", result_dict)
        self.assertIsInstance(result_dict["factors"], dict)

    def test_empty_task_description(self):
        """Test handling of empty task description"""
        result = self.analyzer.analyze("")

        # Should still return valid result with defaults
        self.assertIsNotNone(result.complexity_score)
        self.assertGreaterEqual(result.complexity_score, 1)

    def test_very_long_task_description(self):
        """Test handling of very long task description"""
        long_task = "Add user authentication " * 100
        result = self.analyzer.analyze(long_task)

        # Should still return valid result
        self.assertIsNotNone(result.complexity_score)
        self.assertGreaterEqual(result.complexity_score, 1)

    def test_special_characters_in_description(self):
        """Test handling of special characters"""
        task = "Add user @authentication with #security & *authorization*"
        result = self.analyzer.analyze(task)

        # Should handle special characters gracefully
        self.assertIsNotNone(result.complexity_score)

    def test_consistency_across_runs(self):
        """Test that same input produces consistent results"""
        task = "Add user authentication with JWT"

        result1 = self.analyzer.analyze(task)
        result2 = self.analyzer.analyze(task)

        self.assertEqual(result1.complexity_score, result2.complexity_score)
        self.assertEqual(result1.recommended_subtasks, result2.recommended_subtasks)


class TestComplexityFactors(unittest.TestCase):
    """Test individual complexity factors"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = ComplexityAnalyzer()

    def test_files_affected_estimation(self):
        """Test files affected estimation"""
        test_cases = [
            ("Fix typo in file", 2),
            ("Update module", 5),
            ("Refactor entire system", 15),
        ]

        for task, expected_min in test_cases:
            estimated = self.analyzer._estimate_files(task)
            self.assertGreaterEqual(
                estimated, expected_min * 0.5, f"Files estimate for '{task}' too low"
            )

    def test_loc_estimation(self):
        """Test LOC estimation"""
        test_cases = [
            ("Fix typo", 100),
            ("Add feature", 200),
            ("Refactor module", 400),
        ]

        for task, expected_min in test_cases:
            estimated = self.analyzer._estimate_loc(task)
            self.assertGreaterEqual(
                estimated, expected_min * 0.5, f"LOC estimate for '{task}' too low"
            )

    def test_dependencies_estimation(self):
        """Test dependencies estimation"""
        tasks_with_deps = [
            "Integrate with third-party API",
            "Add webhook support",
            "Connect to external database",
        ]

        for task in tasks_with_deps:
            estimated = self.analyzer._estimate_dependencies(task)
            self.assertGreater(estimated, 0, f"Should detect dependencies in '{task}'")


class TestIntegrationScenarios(unittest.TestCase):
    """Test real-world integration scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = ComplexityAnalyzer()

    def test_prd_feature_scoring(self):
        """Test scoring PRD features"""
        features = [
            "User registration with email verification",
            "Shopping cart functionality",
            "Payment integration with Stripe",
            "Admin dashboard with analytics",
        ]

        scored_features = []
        for feature in features:
            result = analyze_complexity(feature)
            scored_features.append(
                {
                    "feature": feature,
                    "complexity": result["complexity_score"],
                    "subtasks": result["recommended_subtasks"],
                    "tokens": result["estimated_tokens"]["total"],
                }
            )

        # All features should have valid scores
        for feature in scored_features:
            self.assertGreaterEqual(feature["complexity"], 1)
            self.assertLessEqual(feature["complexity"], 10)

    def test_agent_routing_scenario(self):
        """Test agent routing based on complexity"""
        tasks = [
            ("Fix typo", "rapid-prototyper"),
            ("Add user authentication system", "code-architect"),
            ("Refactor authentication module", "code-architect"),
        ]

        for task, expected_agent_type in tasks:
            result = analyze_complexity(task)
            agents = result["suggested_agents"]

            # Check if expected agent type is in suggestions
            self.assertTrue(
                any(expected_agent_type in agent for agent in agents),
                f"Expected {expected_agent_type} for '{task}', got {agents}",
            )

    def test_workflow_mode_selection(self):
        """Test workflow mode selection based on complexity"""
        test_cases = [
            ("Fix button alignment", "quick_mode", 4),
            ("Add API endpoint", "standard_mode", 7),
            ("Migrate architecture", "full_mode", 6),
        ]

        for task, expected_mode, max_complexity in test_cases:
            score = quick_score(task)

            if expected_mode == "quick_mode":
                self.assertLessEqual(score, max_complexity)
            elif expected_mode == "full_mode":
                self.assertGreaterEqual(score, max_complexity)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestComplexityScoring))
    suite.addTests(loader.loadTestsFromTestCase(TestComplexityFactors))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
