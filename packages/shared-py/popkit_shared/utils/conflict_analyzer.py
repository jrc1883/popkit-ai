#!/usr/bin/env python3
"""
Merge Conflict Analyzer - Detection and Complexity Analysis

Provides comprehensive merge conflict detection, parsing, and complexity analysis
for intelligent conflict resolution. Integrates with PopKit's complexity scoring
system for prioritization.

Part of PopKit's merge conflict resolution system.

Usage:
    from popkit_shared.utils.conflict_analyzer import ConflictResolver, Conflict

    resolver = ConflictResolver()
    conflicts = resolver.detect_conflicts()

    for conflict in conflicts:
        complexity = resolver.analyze_conflict_complexity(conflict)
        print(f"{conflict.file_path}: {complexity['complexity_score']}/10")
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class Conflict:
    """Represents a single merge conflict."""

    file_path: str
    content: str
    our_side: str = ""
    their_side: str = ""
    base: Optional[str] = None
    lines_count: int = 0
    complexity_score: int = 0
    risk_factors: List[str] = None
    priority: float = 0.0
    scope: str = ""  # Function/class/module where conflict occurs
    is_architectural: bool = False
    is_breaking: bool = False
    has_tests: bool = False
    file_importance: int = 0  # 1-10 scale
    our_changes_summary: str = ""
    their_changes_summary: str = ""

    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
        self._parse_markers()
        self._analyze_scope()

    def _parse_markers(self):
        """Extract conflict sections from markers."""
        # Extract between <<<<<<< and =======
        our_pattern = r"<{7}[^\n]*\n(.*?)\n={7}"
        our_match = re.search(our_pattern, self.content, re.DOTALL)

        # Extract between ======= and >>>>>>>
        their_pattern = r"={7}\n(.*?)\n>{7}"
        their_match = re.search(their_pattern, self.content, re.DOTALL)

        if our_match:
            self.our_side = our_match.group(1).strip()
        if their_match:
            self.their_side = their_match.group(1).strip()

        self.lines_count = len(self.content.split("\n"))

        # Generate summaries
        self.our_changes_summary = self._summarize_changes(self.our_side)
        self.their_changes_summary = self._summarize_changes(self.their_side)

    def _summarize_changes(self, code: str) -> str:
        """Generate a brief summary of code changes."""
        if not code:
            return "No changes"

        lines = code.strip().split("\n")
        if len(lines) == 1:
            return f"1 line: {lines[0][:50]}..."
        else:
            return f"{len(lines)} lines modified"

    def _analyze_scope(self):
        """Determine the scope (function/class) of the conflict."""
        # Look for function/class definitions in surrounding context
        lines_before = self.content.split("<<<<<<<")[0].split("\n")

        # Search backwards for function/class definitions
        for line in reversed(lines_before[-20:]):
            # Python
            if re.match(r"^\s*(def|class|async def)\s+(\w+)", line):
                match = re.match(r"^\s*(def|class|async def)\s+(\w+)", line)
                self.scope = match.group(2)
                return
            # JavaScript/TypeScript
            if re.match(r"^\s*(function|class|const|let|var)\s+(\w+)", line):
                match = re.match(r"^\s*(function|class|const|let|var)\s+(\w+)", line)
                self.scope = match.group(2)
                return

        self.scope = "unknown"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "lines_count": self.lines_count,
            "complexity_score": self.complexity_score,
            "risk_factors": self.risk_factors,
            "priority": self.priority,
            "scope": self.scope,
            "is_architectural": self.is_architectural,
            "is_breaking": self.is_breaking,
            "our_summary": self.our_changes_summary,
            "their_summary": self.their_changes_summary,
        }


class ConflictResolver:
    """Analyze and resolve merge conflicts with intelligence."""

    # File importance classification
    CORE_FILES = ["auth", "security", "core", "api", "database", "schema"]
    TEST_FILES = ["test", "spec", ".test.", ".spec."]
    CONFIG_FILES = ["config", "package.json", "tsconfig", "webpack", "vite"]
    DOC_FILES = ["README", "CHANGELOG", "docs/", ".md"]

    def __init__(self):
        """Initialize conflict resolver."""
        self.conflicts: List[Conflict] = []

    def detect_conflicts(self) -> List[Conflict]:
        """
        Detect all merge conflicts in repository.

        Returns:
            List of Conflict objects
        """
        conflicts = []

        try:
            # Get conflicted files using git diff
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                return []

            file_paths = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

            # Parse each conflicted file
            for file_path in file_paths:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Check for conflict markers
                    if "<<<<<<<" in content and ">>>>>>>" in content:
                        conflict = Conflict(file_path=file_path, content=content)
                        conflict.file_importance = self._assess_file_importance(file_path)
                        conflict.has_tests = self._has_test_file(file_path)
                        conflicts.append(conflict)

                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue

            self.conflicts = conflicts
            return conflicts

        except Exception as e:
            print(f"Error detecting conflicts: {e}")
            return []

    def _assess_file_importance(self, file_path: str) -> int:
        """
        Assess file importance on 1-10 scale.

        Args:
            file_path: Path to file

        Returns:
            Importance score (1-10)
        """
        lower_path = file_path.lower()

        # Core files = highest importance
        if any(core in lower_path for core in self.CORE_FILES):
            return 10

        # Config files = high importance
        if any(config in lower_path for config in self.CONFIG_FILES):
            return 8

        # Test files = medium importance
        if any(test in lower_path for test in self.TEST_FILES):
            return 5

        # Doc files = lower importance
        if any(doc in lower_path for doc in self.DOC_FILES):
            return 3

        # Default = medium
        return 6

    def _has_test_file(self, file_path: str) -> bool:
        """Check if file has associated test file."""
        # Check for common test file patterns
        base_path = Path(file_path)
        stem = base_path.stem
        parent = base_path.parent

        test_patterns = [
            f"{stem}.test{base_path.suffix}",
            f"{stem}.spec{base_path.suffix}",
            f"test_{stem}{base_path.suffix}",
            f"{stem}_test{base_path.suffix}",
        ]

        for pattern in test_patterns:
            test_path = parent / pattern
            if test_path.exists():
                return True

        return False

    def analyze_conflict_complexity(self, conflict: Conflict) -> Dict:
        """
        Analyze conflict complexity using complexity analyzer.

        Args:
            conflict: Conflict to analyze

        Returns:
            Dictionary with complexity analysis
        """
        try:
            from popkit_shared.utils.complexity_scoring import analyze_complexity

            # Build description for complexity analysis
            description = f"""
            Resolve merge conflict in {conflict.file_path}:
            - Our changes: {conflict.our_changes_summary}
            - Their changes: {conflict.their_changes_summary}
            - Lines affected: {conflict.lines_count}
            - Function/class: {conflict.scope}
            - File type: {Path(conflict.file_path).suffix}
            """

            # Check for architectural indicators
            conflict.is_architectural = self._is_architectural_conflict(conflict)
            conflict.is_breaking = self._is_breaking_conflict(conflict)

            # Analyze complexity
            complexity = analyze_complexity(
                description,
                metadata={
                    "files_affected": 1,
                    "loc_estimate": conflict.lines_count,
                    "architecture_change": conflict.is_architectural,
                    "breaking_changes": conflict.is_breaking,
                },
            )

            # Update conflict with complexity data
            conflict.complexity_score = complexity["complexity_score"]
            conflict.risk_factors = complexity["risk_factors"]

            # Calculate priority (higher complexity = higher priority)
            conflict.priority = self._calculate_priority(conflict)

            return complexity

        except Exception as e:
            print(f"Error analyzing complexity: {e}")
            # Default complexity if analysis fails
            return {
                "complexity_score": 5,
                "risk_factors": [],
                "reasoning": "Default complexity (analysis failed)",
            }

    def _is_architectural_conflict(self, conflict: Conflict) -> bool:
        """Determine if conflict involves architectural changes."""
        arch_indicators = [
            "class ",
            "interface ",
            "extends ",
            "implements ",
            "import ",
            "export ",
            "module.exports",
            "@dataclass",
            "def __init__",
            "constructor(",
        ]

        combined = conflict.our_side + conflict.their_side
        return any(indicator in combined for indicator in arch_indicators)

    def _is_breaking_conflict(self, conflict: Conflict) -> bool:
        """Determine if conflict involves breaking changes."""
        breaking_indicators = [
            "BREAKING",
            "deprecated",
            "removed",
            "delete",
            "version",
            "migration",
            "upgrade",
        ]

        combined = conflict.our_side + conflict.their_side + conflict.file_path
        return any(indicator.lower() in combined.lower() for indicator in breaking_indicators)

    def _calculate_priority(self, conflict: Conflict) -> float:
        """
        Calculate conflict resolution priority.

        Higher priority = resolve first.

        Formula:
            priority = complexity_score * 10 +
                      len(risk_factors) * 5 +
                      file_importance -
                      (10 if has_tests else 0)

        Args:
            conflict: Conflict to prioritize

        Returns:
            Priority score (higher = more important)
        """
        priority = (
            conflict.complexity_score * 10
            + len(conflict.risk_factors) * 5
            + conflict.file_importance
            - (10 if conflict.has_tests else 0)  # Tested files are safer, lower priority
        )

        return float(priority)

    def prioritize_conflicts(self, conflicts: List[Conflict]) -> List[Conflict]:
        """
        Sort conflicts by priority (highest first).

        Args:
            conflicts: List of conflicts to prioritize

        Returns:
            Sorted list (highest priority first)
        """
        # Analyze complexity for all conflicts first
        for conflict in conflicts:
            self.analyze_conflict_complexity(conflict)

        # Sort by priority (descending)
        sorted_conflicts = sorted(
            conflicts,
            key=lambda c: (
                -c.priority,  # Higher priority first
                -c.complexity_score,  # Higher complexity first
                -len(c.risk_factors),  # More risks first
                -c.file_importance,  # More important files first
                c.has_tests,  # Tested files last (safer)
            ),
        )

        return sorted_conflicts

    def get_conflict_context(self, conflict: Conflict, context_lines: int = 50) -> Dict[str, str]:
        """
        Get surrounding context for a conflict.

        Args:
            conflict: Conflict to analyze
            context_lines: Number of lines before/after conflict

        Returns:
            Dictionary with before/after context
        """
        try:
            with open(conflict.file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Find conflict markers
            conflict_start = -1
            conflict_end = -1

            for i, line in enumerate(lines):
                if "<<<<<<<" in line and conflict_start == -1:
                    conflict_start = i
                if ">>>>>>>" in line and conflict_start != -1:
                    conflict_end = i
                    break

            if conflict_start == -1 or conflict_end == -1:
                return {"before": "", "after": ""}

            # Extract context
            start_idx = max(0, conflict_start - context_lines)
            end_idx = min(len(lines), conflict_end + context_lines + 1)

            before = "".join(lines[start_idx:conflict_start])
            after = "".join(lines[conflict_end + 1 : end_idx])

            return {
                "before": before,
                "after": after,
                "conflict_start_line": conflict_start + 1,
                "conflict_end_line": conflict_end + 1,
            }

        except Exception as e:
            print(f"Error getting context: {e}")
            return {"before": "", "after": ""}

    def get_commit_context(self, conflict: Conflict) -> Dict[str, str]:
        """
        Get commit history context for conflict.

        Args:
            conflict: Conflict to analyze

        Returns:
            Dictionary with commit context
        """
        try:
            # Get commits that modified this file recently
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", "5", "--", conflict.file_path],
                capture_output=True,
                text=True,
                check=False,
            )

            commits = result.stdout.strip() if result.returncode == 0 else ""

            # Get current merge context
            merge_result = subprocess.run(
                ["git", "log", "--oneline", "-1", "MERGE_HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )

            merge_head = merge_result.stdout.strip() if merge_result.returncode == 0 else ""

            return {"recent_commits": commits, "merge_head": merge_head}

        except Exception as e:
            print(f"Error getting commit context: {e}")
            return {"recent_commits": "", "merge_head": ""}


# =============================================================================
# Convenience Functions
# =============================================================================


def detect_and_analyze_conflicts() -> Tuple[List[Conflict], List[Dict]]:
    """
    Convenience function to detect and analyze all conflicts.

    Returns:
        Tuple of (conflicts, complexity_analyses)
    """
    resolver = ConflictResolver()
    conflicts = resolver.detect_conflicts()

    analyses = []
    for conflict in conflicts:
        analysis = resolver.analyze_conflict_complexity(conflict)
        analyses.append(analysis)

    prioritized = resolver.prioritize_conflicts(conflicts)

    return prioritized, analyses


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    print("Testing conflict_analyzer.py...\n")

    # Test detection
    resolver = ConflictResolver()
    conflicts = resolver.detect_conflicts()

    if not conflicts:
        print("No conflicts detected in current repository.")
    else:
        print(f"Found {len(conflicts)} conflicts:\n")

        # Prioritize conflicts
        prioritized = resolver.prioritize_conflicts(conflicts)

        for i, conflict in enumerate(prioritized, 1):
            print(f"{i}. {conflict.file_path}")
            print(f"   Complexity: {conflict.complexity_score}/10")
            print(f"   Priority: {conflict.priority:.1f}")
            print(
                f"   Risk Factors: {', '.join(conflict.risk_factors) if conflict.risk_factors else 'None'}"
            )
            print(f"   Scope: {conflict.scope}")
            print(f"   Lines: {conflict.lines_count}")
            print(f"   Importance: {conflict.file_importance}/10")
            print(f"   Has Tests: {conflict.has_tests}")
            print()

    print("Testing complete!")
