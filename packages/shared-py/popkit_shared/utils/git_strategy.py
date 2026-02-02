#!/usr/bin/env python3
"""
Git Branch Strategy Detection

Analyzes repository branch patterns to identify branching strategy.
Supports detection of:
- Trunk-based Development
- Git Flow
- GitHub Flow
- GitLab Flow
- Custom strategies
"""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class BranchingStrategy(Enum):
    """Supported branching strategies."""

    GIT_FLOW = "Git Flow"
    GITHUB_FLOW = "GitHub Flow"
    GITLAB_FLOW = "GitLab Flow"
    TRUNK_BASED = "Trunk-based Development"
    CUSTOM = "Custom Strategy"
    UNKNOWN = "Unknown Strategy"


@dataclass
class BranchInfo:
    """Information about a branch."""

    name: str
    is_remote: bool
    last_commit_date: Optional[datetime]
    commit_count: int
    is_merged: bool


@dataclass
class StrategyAnalysis:
    """Results of strategy analysis."""

    detected_strategy: BranchingStrategy
    confidence: float  # 0.0-1.0
    evidence: List[str]
    recommendations: List[str]
    branch_stats: Dict[str, Any]
    protected_branches: List[str]


class GitStrategyDetector:
    """Detects and analyzes Git branching strategies."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _run_git(self, args: List[str]) -> str:
        """Run git command and return output."""
        result = subprocess.run(
            ["git"] + args,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip()

    def _run_gh(self, args: List[str]) -> Optional[str]:
        """Run gh CLI command and return output."""
        try:
            result = subprocess.run(
                ["gh"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except FileNotFoundError:
            return None

    def get_all_branches(self) -> List[BranchInfo]:
        """Get all local and remote branches with metadata."""
        branches = []

        # Get all branches (local and remote)
        output = self._run_git(["branch", "-a", "--format=%(refname:short)"])
        if not output:
            return branches

        branch_names = [line.strip() for line in output.split("\n") if line.strip()]

        for branch_name in branch_names:
            # Skip HEAD reference
            if "HEAD" in branch_name:
                continue

            is_remote = branch_name.startswith("origin/")
            clean_name = branch_name.replace("origin/", "") if is_remote else branch_name

            # Get last commit date
            date_output = self._run_git(["log", "-1", "--format=%ci", branch_name])
            try:
                last_commit_date = (
                    datetime.strptime(date_output[:19], "%Y-%m-%d %H:%M:%S")
                    if date_output
                    else None
                )
            except ValueError:
                last_commit_date = None

            # Get commit count
            count_output = self._run_git(["rev-list", "--count", branch_name])
            commit_count = int(count_output) if count_output.isdigit() else 0

            # Check if merged to main/master
            merged_output = self._run_git(["branch", "-a", "--merged", "main"])
            is_merged = branch_name in merged_output or clean_name in merged_output

            if not is_merged:
                merged_output = self._run_git(["branch", "-a", "--merged", "master"])
                is_merged = branch_name in merged_output or clean_name in merged_output

            branches.append(
                BranchInfo(
                    name=clean_name,
                    is_remote=is_remote,
                    last_commit_date=last_commit_date,
                    commit_count=commit_count,
                    is_merged=is_merged,
                )
            )

        return branches

    def get_protected_branches(self) -> List[str]:
        """Get list of protected branches from GitHub."""
        protected = ["main", "master"]  # Common defaults

        # Try to get from GitHub API
        gh_output = self._run_gh(
            [
                "api",
                "repos/:owner/:repo/branches",
                "--jq",
                ".[].name | select(.protected == true)",
            ]
        )

        if gh_output:
            protected.extend(line.strip() for line in gh_output.split("\n") if line.strip())

        return list(set(protected))

    def analyze_branch_patterns(self, branches: List[BranchInfo]) -> Dict[str, Any]:
        """Analyze branch naming patterns and lifecycle."""
        patterns = {
            "feature_branches": 0,
            "bugfix_branches": 0,
            "hotfix_branches": 0,
            "release_branches": 0,
            "develop_exists": False,
            "staging_exists": False,
            "production_exists": False,
            "main_or_master_exists": False,
            "long_lived_branches": [],
            "avg_branch_lifetime_days": 0,
            "total_branches": len(branches),
        }

        # Unique branch names (combine local/remote)
        unique_branches = {}
        for branch in branches:
            if branch.name not in unique_branches:
                unique_branches[branch.name] = branch

        branch_list = list(unique_branches.values())

        # Analyze patterns
        lifetimes = []
        now = datetime.now()

        for branch in branch_list:
            name_lower = branch.name.lower()

            # Count branch types
            if name_lower.startswith(("feat/", "feature/")):
                patterns["feature_branches"] += 1
            elif name_lower.startswith(("fix/", "bugfix/")):
                patterns["bugfix_branches"] += 1
            elif name_lower.startswith("hotfix/"):
                patterns["hotfix_branches"] += 1
            elif name_lower.startswith("release/"):
                patterns["release_branches"] += 1

            # Check for long-lived branches
            if name_lower in ["develop", "development", "dev"]:
                patterns["develop_exists"] = True
                patterns["long_lived_branches"].append(branch.name)
            elif name_lower in ["staging", "stage"]:
                patterns["staging_exists"] = True
                patterns["long_lived_branches"].append(branch.name)
            elif name_lower in ["production", "prod"]:
                patterns["production_exists"] = True
                patterns["long_lived_branches"].append(branch.name)
            elif name_lower in ["main", "master"]:
                patterns["main_or_master_exists"] = True
                patterns["long_lived_branches"].append(branch.name)

            # Calculate branch lifetime
            if branch.last_commit_date:
                lifetime = (now - branch.last_commit_date).days
                lifetimes.append(lifetime)

        # Calculate average lifetime
        if lifetimes:
            patterns["avg_branch_lifetime_days"] = sum(lifetimes) // len(lifetimes)

        return patterns

    def detect_strategy(
        self, patterns: Dict[str, Any]
    ) -> tuple[BranchingStrategy, float, List[str]]:
        """
        Detect branching strategy based on patterns.

        Returns:
            (strategy, confidence, evidence)
        """
        evidence = []

        # Git Flow indicators
        gitflow_score = 0
        if patterns["develop_exists"]:
            gitflow_score += 3
            evidence.append("develop branch exists")
        if patterns["release_branches"] > 0:
            gitflow_score += 2
            evidence.append(f"{patterns['release_branches']} release branches")
        if patterns["hotfix_branches"] > 0:
            gitflow_score += 1
            evidence.append(f"{patterns['hotfix_branches']} hotfix branches")

        # GitHub Flow indicators
        github_flow_score = 0
        if patterns["feature_branches"] > 5:
            github_flow_score += 2
            evidence.append(f"{patterns['feature_branches']} feature branches")
        if patterns["main_or_master_exists"] and not patterns["develop_exists"]:
            github_flow_score += 2
            evidence.append("main/master as primary branch")
        if patterns["avg_branch_lifetime_days"] < 7:
            github_flow_score += 1
            evidence.append(
                f"short-lived branches (avg {patterns['avg_branch_lifetime_days']} days)"
            )

        # GitLab Flow indicators
        gitlab_flow_score = 0
        if patterns["staging_exists"]:
            gitlab_flow_score += 2
            evidence.append("staging branch exists")
        if patterns["production_exists"]:
            gitlab_flow_score += 2
            evidence.append("production branch exists")

        # Trunk-based indicators
        trunk_based_score = 0
        if (
            patterns["main_or_master_exists"]
            and not patterns["develop_exists"]
            and not patterns["staging_exists"]
            and patterns["avg_branch_lifetime_days"] < 3
        ):
            trunk_based_score += 3
            evidence.append("direct merges to main, short branch lifetime")

        # Determine strategy based on scores
        scores = {
            BranchingStrategy.GIT_FLOW: gitflow_score,
            BranchingStrategy.GITHUB_FLOW: github_flow_score,
            BranchingStrategy.GITLAB_FLOW: gitlab_flow_score,
            BranchingStrategy.TRUNK_BASED: trunk_based_score,
        }

        max_score = max(scores.values())
        if max_score == 0:
            return BranchingStrategy.UNKNOWN, 0.0, ["No clear branching pattern detected"]

        detected = max(scores, key=scores.get)
        confidence = min(max_score / 5.0, 1.0)  # Normalize to 0-1

        return detected, confidence, evidence

    def generate_recommendations(
        self, strategy: BranchingStrategy, patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on detected strategy."""
        recommendations = []

        if strategy == BranchingStrategy.TRUNK_BASED:
            recommendations.append("[OK] Good for: Small teams (2-5 developers), rapid iteration")
            recommendations.append(
                "[OK] Benefits: Fast merges, simple workflow, continuous integration"
            )
            if patterns["total_branches"] > 20:
                recommendations.append(
                    "[WARN] Consider cleaning up old branches (detected 20+ branches)"
                )
            recommendations.append(
                "[INFO] Consider Git Flow if: Need release coordination or multiple version support"
            )

        elif strategy == BranchingStrategy.GITHUB_FLOW:
            recommendations.append(
                "[OK] Good for: Medium teams (5-15 developers), web applications"
            )
            recommendations.append("[OK] Benefits: Simple workflow, good for continuous deployment")
            if patterns["avg_branch_lifetime_days"] > 7:
                recommendations.append("[WARN] Branches staying open longer than typical (>7 days)")
            recommendations.append("[INFO] Consider Git Flow if: Need structured release process")

        elif strategy == BranchingStrategy.GIT_FLOW:
            recommendations.append(
                "[OK] Good for: Large teams (15+ developers), coordinated releases"
            )
            recommendations.append(
                "[OK] Benefits: Clear release process, hotfix support, version management"
            )
            if patterns["avg_branch_lifetime_days"] < 3:
                recommendations.append(
                    "[INFO] Consider GitHub Flow for simpler workflow (short branch lifetimes detected)"
                )
            recommendations.append("[WARN] Requires discipline and clear communication")

        elif strategy == BranchingStrategy.GITLAB_FLOW:
            recommendations.append("[OK] Good for: Teams with staging/production environments")
            recommendations.append(
                "[OK] Benefits: Environment-based workflow, clear deployment path"
            )
            recommendations.append("[INFO] Ensure CI/CD pipeline matches branch strategy")

        else:
            recommendations.append("[?] Strategy unclear - consider standardizing workflow")
            recommendations.append("[INFO] See documentation: /popkit-dev:git recommend-strategy")

        return recommendations

    def analyze(self) -> StrategyAnalysis:
        """Perform full strategy analysis."""
        branches = self.get_all_branches()
        patterns = self.analyze_branch_patterns(branches)
        protected = self.get_protected_branches()

        strategy, confidence, evidence = self.detect_strategy(patterns)
        recommendations = self.generate_recommendations(strategy, patterns)

        return StrategyAnalysis(
            detected_strategy=strategy,
            confidence=confidence,
            evidence=evidence,
            recommendations=recommendations,
            branch_stats=patterns,
            protected_branches=protected,
        )


def format_analysis_report(analysis: StrategyAnalysis) -> str:
    """Format analysis results as human-readable report."""
    lines = []

    lines.append("# Git Branch Strategy Analysis")
    lines.append("")
    lines.append(f"**Detected Strategy**: {analysis.detected_strategy.value}")
    lines.append(f"**Confidence**: {analysis.confidence:.0%}")
    lines.append("")

    lines.append("## Evidence")
    for item in analysis.evidence:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Branch Statistics")
    stats = analysis.branch_stats
    lines.append(f"- Total branches: {stats['total_branches']}")
    lines.append(f"- Feature branches: {stats['feature_branches']}")
    lines.append(f"- Bugfix branches: {stats['bugfix_branches']}")
    lines.append(f"- Release branches: {stats['release_branches']}")
    lines.append(f"- Hotfix branches: {stats['hotfix_branches']}")
    lines.append(f"- Average branch lifetime: {stats['avg_branch_lifetime_days']} days")
    lines.append("")

    if stats["long_lived_branches"]:
        lines.append("## Long-lived Branches")
        for branch in stats["long_lived_branches"]:
            lines.append(f"- {branch}")
        lines.append("")

    if analysis.protected_branches:
        lines.append("## Protected Branches")
        for branch in analysis.protected_branches:
            lines.append(f"- {branch}")
        lines.append("")

    lines.append("## Recommendations")
    for rec in analysis.recommendations:
        lines.append(f"{rec}")
    lines.append("")

    return "\n".join(lines)
