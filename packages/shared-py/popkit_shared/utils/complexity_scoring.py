#!/usr/bin/env python3
"""
Complexity Scoring - Task/Feature Complexity Analysis

Provides 1-10 complexity scoring for tasks and features based on multiple
factors including code volume, architecture impact, dependencies, and risk.

Part of PopKit's foundational analysis system - used by:
- PRD parser for feature scoring
- Merge conflict resolver for prioritization
- Agent router for agent selection
- Planning workflows for task breakdown

Usage:
    from popkit_shared.utils.complexity_scoring import analyze_complexity, get_complexity_analyzer

    # Analyze a task/feature
    result = analyze_complexity("Add user authentication with JWT")

    # Access detailed breakdown
    score = result["complexity_score"]  # 1-10
    subtasks = result["recommended_subtasks"]  # int
    phases = result["phase_distribution"]  # dict
    reasoning = result["reasoning"]  # str
"""

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class ComplexityLevel(Enum):
    """Complexity level classifications"""

    TRIVIAL = (1, 2, "Single file, minimal changes")
    SIMPLE = (3, 4, "Few files, straightforward logic")
    MODERATE = (5, 6, "Multiple files, some complexity")
    COMPLEX = (7, 8, "Architecture changes, high impact")
    VERY_COMPLEX = (9, 10, "System-wide changes, high risk")

    def __init__(self, min_score, max_score, description):
        self.min_score = min_score
        self.max_score = max_score
        self.description = description


@dataclass
class ComplexityFactors:
    """Individual complexity factor scores"""

    files_affected: float = 0.0  # 0-100
    loc_estimate: float = 0.0  # 0-100
    dependencies: float = 0.0  # 0-100
    architecture_change: float = 0.0  # 0-100
    breaking_changes: float = 0.0  # 0-100
    testing_complexity: float = 0.0  # 0-100
    security_impact: float = 0.0  # 0-100
    integration_points: float = 0.0  # 0-100

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ComplexityAnalysis:
    """Complete complexity analysis result"""

    complexity_score: int  # 1-10 final score
    complexity_level: str  # TRIVIAL, SIMPLE, etc.
    recommended_subtasks: int  # Suggested subtask count
    phase_distribution: dict[str, int]  # Phase breakdown
    risk_factors: list[str]  # Risk categories
    reasoning: str  # Human-readable explanation
    factors: ComplexityFactors  # Detailed factor breakdown
    estimated_tokens: dict[str, int]  # Token usage estimates
    suggested_agents: list[str]  # Recommended agents

    def to_dict(self) -> dict:
        return {
            "complexity_score": self.complexity_score,
            "complexity_level": self.complexity_level,
            "recommended_subtasks": self.recommended_subtasks,
            "phase_distribution": self.phase_distribution,
            "risk_factors": self.risk_factors,
            "reasoning": self.reasoning,
            "factors": self.factors.to_dict(),
            "estimated_tokens": self.estimated_tokens,
            "suggested_agents": self.suggested_agents,
        }


class ComplexityAnalyzer:
    """
    Analyzes task/feature complexity and provides actionable recommendations.

    Scoring formula:
        raw_score = weighted_sum(factors)
        complexity_score = normalize_to_1_10(raw_score)
    """

    # Factor weights (sum to 1.0)
    DEFAULT_WEIGHTS = {
        "files_affected": 0.15,
        "loc_estimate": 0.15,
        "dependencies": 0.10,
        "architecture_change": 0.20,
        "breaking_changes": 0.10,
        "testing_complexity": 0.10,
        "security_impact": 0.15,  # Increased from 0.05
        "integration_points": 0.05,
    }

    # Keywords for detecting complexity factors
    HIGH_COMPLEXITY_KEYWORDS = {
        "architecture": ["architecture", "refactor", "redesign", "restructure", "migrate"],
        "breaking": ["breaking", "incompatible", "migration", "deprecated"],
        "security": ["auth", "authentication", "authorization", "security", "crypto", "encryption"],
        "integration": ["integrate", "api", "webhook", "third-party", "external"],
        "database": ["database", "schema", "migration", "query", "index"],
        "testing": ["e2e", "integration test", "test coverage", "regression"],
    }

    # Subtask recommendations by complexity
    SUBTASK_MAPPING = {
        1: (1, 1),
        2: (1, 2),
        3: (2, 3),
        4: (2, 4),
        5: (3, 5),
        6: (4, 6),
        7: (5, 7),
        8: (6, 9),
        9: (8, 12),
        10: (10, 15),
    }

    # Agent recommendations by complexity
    AGENT_MAPPING = {
        (1, 3): ["rapid-prototyper", "code-explorer"],
        (4, 6): ["refactoring-expert", "code-explorer", "test-writer"],
        (7, 8): ["code-architect", "refactoring-expert", "security-auditor"],
        (9, 10): ["code-architect", "system-designer", "tech-lead", "security-auditor"],
    }

    def __init__(self, weights: dict[str, float] | None = None):
        """
        Initialize complexity analyzer.

        Args:
            weights: Custom factor weights (optional)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def analyze(
        self, task_description: str, metadata: dict[str, Any] | None = None
    ) -> ComplexityAnalysis:
        """
        Analyze task complexity and provide recommendations.

        Args:
            task_description: Natural language description of task/feature
            metadata: Optional metadata (files affected, dependencies, etc.)

        Returns:
            ComplexityAnalysis with scores and recommendations
        """
        metadata = metadata or {}

        # Extract factors
        factors = self._extract_factors(task_description, metadata)

        # Calculate weighted score (0-100)
        raw_score = self._calculate_weighted_score(factors)

        # Normalize to 1-10 scale
        complexity_score = self._normalize_score(raw_score)

        # Classify complexity level
        complexity_level = self._classify_level(complexity_score)

        # Generate recommendations
        recommended_subtasks = self._recommend_subtasks(complexity_score)
        phase_distribution = self._recommend_phases(complexity_score)
        risk_factors = self._identify_risks(task_description, factors)
        estimated_tokens = self._estimate_tokens(complexity_score)
        suggested_agents = self._suggest_agents(complexity_score)

        # Generate reasoning
        reasoning = self._generate_reasoning(complexity_score, factors, task_description)

        return ComplexityAnalysis(
            complexity_score=complexity_score,
            complexity_level=complexity_level.name,
            recommended_subtasks=recommended_subtasks,
            phase_distribution=phase_distribution,
            risk_factors=risk_factors,
            reasoning=reasoning,
            factors=factors,
            estimated_tokens=estimated_tokens,
            suggested_agents=suggested_agents,
        )

    def _extract_factors(self, description: str, metadata: dict[str, Any]) -> ComplexityFactors:
        """Extract complexity factors from description and metadata."""
        desc_lower = description.lower()

        # Files affected (from metadata or estimate from description)
        files_count = metadata.get("files_affected", self._estimate_files(description))
        files_score = min((files_count / 20) * 100, 100)

        # LOC estimate (from metadata or keywords)
        loc = metadata.get("loc_estimate", self._estimate_loc(description))
        loc_score = min((loc / 500) * 100, 100)

        # Dependencies (from metadata or keywords)
        deps_count = metadata.get("dependencies", self._estimate_dependencies(description))
        deps_score = min((deps_count / 10) * 100, 100)

        # Architecture change (keyword-based)
        arch_score = self._score_keywords(desc_lower, self.HIGH_COMPLEXITY_KEYWORDS["architecture"])

        # Breaking changes (keyword-based)
        breaking_score = self._score_keywords(desc_lower, self.HIGH_COMPLEXITY_KEYWORDS["breaking"])

        # Testing complexity (keyword-based + heuristics)
        testing_score = self._estimate_testing_complexity(description)

        # Security impact (keyword-based)
        security_score = self._score_keywords(desc_lower, self.HIGH_COMPLEXITY_KEYWORDS["security"])

        # Integration points (keyword-based)
        integration_score = self._score_keywords(
            desc_lower, self.HIGH_COMPLEXITY_KEYWORDS["integration"]
        )

        return ComplexityFactors(
            files_affected=files_score,
            loc_estimate=loc_score,
            dependencies=deps_score,
            architecture_change=arch_score,
            breaking_changes=breaking_score,
            testing_complexity=testing_score,
            security_impact=security_score,
            integration_points=integration_score,
        )

    def _estimate_files(self, description: str) -> int:
        """Estimate number of files affected from description."""
        desc_lower = description.lower()

        # Check for scope indicators
        if any(word in desc_lower for word in ["system-wide", "global", "entire", "migrate"]):
            return 20
        elif any(word in desc_lower for word in ["refactor", "redesign", "restructure"]):
            return 12
        elif any(
            word in desc_lower
            for word in ["module", "component", "service", "authentication", "auth"]
        ):
            return 8
        elif any(word in desc_lower for word in ["feature", "add", "implement", "page", "form"]):
            return 5
        elif any(word in desc_lower for word in ["fix", "update", "change", "button"]):
            return 2
        else:
            return 3  # Default

    def _estimate_loc(self, description: str) -> int:
        """Estimate lines of code from description."""
        desc_lower = description.lower()

        # Check specific high-complexity keywords first
        if any(word in desc_lower for word in ["migrate", "entire", "rewrite", "redesign"]):
            return 600
        elif any(word in desc_lower for word in ["refactor"]):
            return 400
        elif any(word in desc_lower for word in ["authentication", "auth"]):
            return 350  # Auth is always substantial
        elif any(word in desc_lower for word in ["feature", "system", "module"]):
            return 250
        elif any(word in desc_lower for word in ["page", "form", "validation"]):
            return 200
        elif any(word in desc_lower for word in ["add", "implement"]):
            return 150
        elif any(word in desc_lower for word in ["fix", "update"]):
            return 50
        elif any(word in desc_lower for word in ["button"]):
            return 30
        else:
            return 100  # Default

    def _estimate_dependencies(self, description: str) -> int:
        """Estimate number of dependencies from description."""
        desc_lower = description.lower()

        count = 1  # Base count

        # Count integration keywords
        count += (
            sum(
                1
                for keyword in self.HIGH_COMPLEXITY_KEYWORDS["integration"]
                if keyword in desc_lower
            )
            * 2
        )

        # Add database dependencies
        if any(word in desc_lower for word in self.HIGH_COMPLEXITY_KEYWORDS["database"]):
            count += 3

        # Add security dependencies
        if any(word in desc_lower for word in self.HIGH_COMPLEXITY_KEYWORDS["security"]):
            count += 2

        # Add for validation/forms
        if any(word in desc_lower for word in ["validation", "form"]):
            count += 1

        return count

    def _score_keywords(self, text: str, keywords: list[str]) -> float:
        """Score presence of keywords (0-100)."""
        matches = sum(1 for keyword in keywords if keyword in text)
        if matches == 0:
            return 0.0
        elif matches == 1:
            return 50.0
        else:
            return 100.0

    def _estimate_testing_complexity(self, description: str) -> float:
        """Estimate testing complexity."""
        desc_lower = description.lower()

        score = 0.0

        # Check test type keywords
        if "e2e" in desc_lower or "integration test" in desc_lower:
            score += 50
        if "regression" in desc_lower or "test coverage" in desc_lower:
            score += 30
        if any(word in desc_lower for word in ["api", "endpoint", "webhook"]):
            score += 20
        if any(word in desc_lower for word in ["authentication", "auth"]):
            score += 40  # Auth requires extensive testing
        if any(word in desc_lower for word in ["validation", "form"]):
            score += 20

        return min(score, 100.0)

    def _calculate_weighted_score(self, factors: ComplexityFactors) -> float:
        """Calculate weighted complexity score (0-100)."""
        score = 0.0
        for factor_name, weight in self.weights.items():
            factor_value = getattr(factors, factor_name, 0.0)
            score += weight * factor_value
        return score

    def _normalize_score(self, raw_score: float) -> int:
        """Normalize 0-100 score to 1-10 scale."""
        # Map 0-100 to 1-10 with slight bias toward middle
        if raw_score < 10:
            return 1
        elif raw_score < 20:
            return 2
        elif raw_score < 30:
            return 3
        elif raw_score < 40:
            return 4
        elif raw_score < 50:
            return 5
        elif raw_score < 60:
            return 6
        elif raw_score < 70:
            return 7
        elif raw_score < 80:
            return 8
        elif raw_score < 90:
            return 9
        else:
            return 10

    def _classify_level(self, score: int) -> ComplexityLevel:
        """Classify complexity level from score."""
        for level in ComplexityLevel:
            if level.min_score <= score <= level.max_score:
                return level
        return ComplexityLevel.MODERATE

    def _recommend_subtasks(self, complexity: int) -> int:
        """Recommend number of subtasks based on complexity."""
        min_tasks, max_tasks = self.SUBTASK_MAPPING.get(complexity, (3, 5))
        # Return middle of range
        return (min_tasks + max_tasks) // 2

    def _recommend_phases(self, complexity: int) -> dict[str, int]:
        """Recommend phase distribution based on complexity."""
        if complexity <= 2:
            # Trivial: minimal phases
            return {"implementation": 1, "testing": 1}
        elif complexity <= 4:
            # Simple: basic phases
            return {"planning": 1, "implementation": 2, "testing": 1}
        elif complexity <= 6:
            # Moderate: standard phases
            return {"planning": 1, "implementation": 3, "testing": 2, "review": 1}
        elif complexity <= 8:
            # Complex: extended phases
            return {
                "discovery": 1,
                "planning": 2,
                "implementation": 4,
                "testing": 2,
                "review": 1,
                "integration": 1,
            }
        else:
            # Very complex: full phases
            return {
                "discovery": 2,
                "architecture": 2,
                "planning": 3,
                "implementation": 5,
                "testing": 3,
                "review": 2,
                "integration": 2,
                "documentation": 1,
            }

    def _identify_risks(self, description: str, factors: ComplexityFactors) -> list[str]:
        """Identify risk factors."""
        risks = []
        desc_lower = description.lower()

        if factors.breaking_changes > 50:
            risks.append("breaking_changes")
        if factors.security_impact > 50:
            risks.append("security_critical")
        if factors.architecture_change > 70:
            risks.append("architecture_impact")
        if factors.integration_points > 60:
            risks.append("integration_complexity")
        if "performance" in desc_lower or "optimization" in desc_lower:
            risks.append("performance_sensitive")
        if "migrate" in desc_lower or "migration" in desc_lower:
            risks.append("data_migration")

        return risks

    def _estimate_tokens(self, complexity: int) -> dict[str, int]:
        """Estimate token usage based on complexity."""
        # Base token estimates for different task types
        if complexity <= 2:
            return {"planning": 2000, "implementation": 5000, "total": 7000}
        elif complexity <= 4:
            return {"planning": 4000, "implementation": 10000, "testing": 3000, "total": 17000}
        elif complexity <= 6:
            return {
                "planning": 8000,
                "implementation": 20000,
                "testing": 6000,
                "review": 4000,
                "total": 38000,
            }
        elif complexity <= 8:
            return {
                "discovery": 5000,
                "planning": 12000,
                "implementation": 35000,
                "testing": 10000,
                "review": 6000,
                "total": 68000,
            }
        else:
            return {
                "discovery": 10000,
                "architecture": 15000,
                "planning": 20000,
                "implementation": 60000,
                "testing": 20000,
                "review": 10000,
                "total": 135000,
            }

    def _suggest_agents(self, complexity: int) -> list[str]:
        """Suggest appropriate agents based on complexity."""
        for (min_complexity, max_complexity), agents in self.AGENT_MAPPING.items():
            if min_complexity <= complexity <= max_complexity:
                return agents.copy()
        return ["code-explorer"]  # Default

    def _generate_reasoning(self, score: int, factors: ComplexityFactors, description: str) -> str:
        """Generate human-readable reasoning for the score."""
        level = self._classify_level(score)

        # Find top 3 contributing factors
        factor_dict = factors.to_dict()
        sorted_factors = sorted(factor_dict.items(), key=lambda x: x[1], reverse=True)[:3]

        factor_names = {
            "files_affected": "multiple files affected",
            "loc_estimate": "significant code volume",
            "dependencies": "external dependencies",
            "architecture_change": "architecture changes required",
            "breaking_changes": "breaking changes involved",
            "testing_complexity": "complex testing requirements",
            "security_impact": "security considerations",
            "integration_points": "integration complexity",
        }

        top_factors = [factor_names.get(name, name) for name, value in sorted_factors if value > 20]

        reasoning_parts = [f"Complexity Score: {score}/10 ({level.description})"]

        if top_factors:
            reasoning_parts.append(f"Primary factors: {', '.join(top_factors)}")

        if score <= 3:
            reasoning_parts.append("This is a straightforward task that can be completed quickly.")
        elif score <= 6:
            reasoning_parts.append("This requires moderate planning and careful implementation.")
        elif score <= 8:
            reasoning_parts.append("This is a complex task requiring architectural consideration.")
        else:
            reasoning_parts.append(
                "This is a very complex task requiring thorough planning, "
                "multiple phases, and careful risk management."
            )

        return " ".join(reasoning_parts)


# =============================================================================
# Convenience Functions
# =============================================================================

_analyzer: ComplexityAnalyzer | None = None


def get_complexity_analyzer() -> ComplexityAnalyzer:
    """Get singleton ComplexityAnalyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = ComplexityAnalyzer()
    return _analyzer


def analyze_complexity(
    task_description: str, metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Analyze task complexity (convenience function).

    Args:
        task_description: Natural language task/feature description
        metadata: Optional metadata (files, dependencies, etc.)

    Returns:
        Dictionary with complexity analysis results
    """
    analyzer = get_complexity_analyzer()
    result = analyzer.analyze(task_description, metadata)
    return result.to_dict()


def quick_score(task_description: str) -> int:
    """
    Get quick complexity score (1-10) without full analysis.

    Args:
        task_description: Natural language task description

    Returns:
        Complexity score (1-10)
    """
    result = analyze_complexity(task_description)
    return result["complexity_score"]


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    print("Testing complexity_scoring.py...\n")

    test_cases = [
        ("Fix typo in README", {"files_affected": 1, "loc_estimate": 5}),
        ("Add user authentication with JWT", {}),
        ("Refactor database layer to use repository pattern", {}),
        ("Migrate entire application to microservices architecture", {}),
        ("Update button color in settings page", {"files_affected": 1}),
        ("Implement real-time collaborative editing with WebSockets", {}),
    ]

    for description, metadata in test_cases:
        print(f"Task: {description}")
        print(f"Metadata: {metadata}")

        result = analyze_complexity(description, metadata)

        print(f"  Complexity: {result['complexity_score']}/10 ({result['complexity_level']})")
        print(f"  Subtasks: {result['recommended_subtasks']}")
        print(f"  Phases: {result['phase_distribution']}")
        print(f"  Risks: {result['risk_factors']}")
        print(f"  Agents: {result['suggested_agents']}")
        print(f"  Reasoning: {result['reasoning']}")
        print()

    print("All tests completed!")
