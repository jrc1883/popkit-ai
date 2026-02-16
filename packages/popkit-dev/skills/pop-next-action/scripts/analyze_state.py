#!/usr/bin/env python3
"""
Project State Analysis Script.

Analyze current project state for next action recommendations.

Usage:
    python analyze_state.py [--section SECTION]

Sections:
    git      - Git repository status
    code     - Code quality (TypeScript, lint)
    issues   - GitHub issues
    branches - Feature/fix branches with work in progress
    research - Research branches
    all      - All sections

Output:
    JSON object with project state analysis
"""

import json
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


HIGH_PRIORITY_LABELS = {
    "p0-critical",
    "p1-high",
    "priority:critical",
    "priority:high",
}

MEDIUM_PRIORITY_LABELS = {
    "p2-medium",
    "priority:medium",
}


def _normalize_command(cmd: Union[str, List[str]]) -> List[str]:
    """Normalize command input into an argv list without shell parsing."""
    if isinstance(cmd, str):
        return shlex.split(cmd, posix=False)
    return list(cmd)


def _resolve_executable(argv: List[str]) -> List[str]:
    """Resolve command executable path for reliable Windows process spawning."""
    if not argv:
        return argv

    executable = argv[0]
    if not executable:
        return argv

    # Keep explicit paths untouched.
    if Path(executable).is_absolute() or "\\" in executable or "/" in executable:
        return argv

    resolved = shutil.which(executable)
    if (
        not resolved
        and sys.platform.startswith("win")
        and not executable.lower().endswith(".cmd")
    ):
        resolved = shutil.which(f"{executable}.cmd")

    if resolved:
        argv[0] = resolved

    return argv


def run_command(
    cmd: Union[str, List[str]],
    timeout: int = 30,
    preserve_leading_ws: bool = False,
    cwd: Optional[str] = None,
) -> Tuple[str, bool]:
    """Run a command and return output and success status."""
    try:
        argv = _resolve_executable(_normalize_command(cmd))
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )

        output_text = result.stdout or ""
        if result.returncode != 0 and result.stderr:
            if output_text.strip():
                output_text = f"{output_text.rstrip()}\n{result.stderr}"
            else:
                output_text = result.stderr

        output = (
            output_text.rstrip("\r\n") if preserve_leading_ws else output_text.strip()
        )
        return output, result.returncode == 0
    except subprocess.TimeoutExpired:
        return "Command timed out", False
    except Exception as e:
        return str(e), False


def _extract_porcelain_path(line: str) -> str:
    """Extract file path from a git status --porcelain line."""
    entry = line.rstrip()
    if not entry:
        return ""

    parts = entry.split(maxsplit=1)
    path = parts[1].strip() if len(parts) == 2 else entry.strip()

    # Handle rename lines like: "R  old/path -> new/path"
    if " -> " in path:
        path = path.split(" -> ", 1)[1].strip()

    return path


def _find_tsconfig_files(root: Path, limit: int = 20) -> List[Path]:
    """Find tsconfig files in a monorepo, skipping generated directories."""
    excluded = {
        "node_modules",
        ".git",
        "dist",
        "build",
        ".next",
        ".turbo",
        ".workspace",
        "coverage",
        "htmlcov",
    }
    results: List[Path] = []
    for tsconfig in root.rglob("tsconfig.json"):
        if any(part.lower() in excluded for part in tsconfig.parts):
            continue
        results.append(tsconfig)
        if len(results) >= limit:
            break
    return results


def _count_typescript_errors(output: str) -> int:
    """Count TypeScript compiler errors from command output."""
    return sum(1 for line in output.splitlines() if "error TS" in line)


def _normalize_label_names(labels: List[Dict[str, Any]]) -> List[str]:
    """Normalize label names for case-insensitive comparison."""
    return [str(label.get("name", "")).strip().lower() for label in labels]


def _resolve_repo_root(repo_root_arg: Optional[str] = None) -> Path:
    """Resolve repository root path for analysis."""
    if repo_root_arg:
        return Path(repo_root_arg).expanduser().resolve()

    cwd = Path.cwd()
    if (cwd / ".git").exists():
        return cwd

    # Fallback to the popkit-claude repository this script lives in.
    try:
        return Path(__file__).resolve().parents[5]
    except IndexError:
        return cwd


def analyze_git_state(repo_root: Path) -> Dict[str, Any]:
    """Analyze git repository state."""
    state = {
        "is_repo": True,
        "repo_path": str(repo_root),
        "branch": "",
        "uncommitted_count": 0,
        "uncommitted_files": [],
        "ahead_count": 0,
        "behind_count": 0,
        "recent_commits": [],
        "urgency": "LOW",
    }

    # Check if git repo (capture_output=True already suppresses stderr)
    _, is_repo = run_command(["git", "rev-parse", "--git-dir"], cwd=str(repo_root))
    if not is_repo:
        state["is_repo"] = False
        return state

    # Get branch
    branch, ok = run_command(["git", "branch", "--show-current"], cwd=str(repo_root))
    if ok:
        state["branch"] = branch

    # Get uncommitted changes
    status, ok = run_command(
        ["git", "status", "--porcelain"], preserve_leading_ws=True, cwd=str(repo_root)
    )
    if ok and status:
        files = [
            _extract_porcelain_path(line) for line in status.split("\n") if line.strip()
        ]
        files = [path for path in files if path]
        state["uncommitted_count"] = len(files)
        state["uncommitted_files"] = files[:5]  # First 5

        if len(files) > 0:
            state["urgency"] = "HIGH"

    # Get ahead/behind (capture_output=True already suppresses stderr)
    ahead_behind, ok = run_command(
        ["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"],
        cwd=str(repo_root),
    )
    if ok and "\t" in ahead_behind:
        parts = ahead_behind.split("\t")
        state["behind_count"] = int(parts[0]) if parts[0].isdigit() else 0
        state["ahead_count"] = (
            int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        )

        if state["ahead_count"] > 0:
            state["urgency"] = max(state["urgency"], "MEDIUM")

    # Get recent commits
    commits, ok = run_command(["git", "log", "--oneline", "-5"], cwd=str(repo_root))
    if ok:
        state["recent_commits"] = commits.splitlines()[:5]

    return state


def analyze_code_state(repo_root: Path) -> Dict[str, Any]:
    """Analyze code quality state."""
    state = {
        "has_typescript": False,
        "typescript_errors": 0,
        "typescript_projects_checked": 0,
        "has_lint": False,
        "lint_errors": 0,
        "urgency": "LOW",
    }

    tsconfig_files = _find_tsconfig_files(repo_root)
    if tsconfig_files:
        state["has_typescript"] = True

        # Prefer root TypeScript check if root config exists.
        if (repo_root / "tsconfig.json").exists():
            output, ok = run_command(
                ["npx", "tsc", "--noEmit", "--pretty", "false"],
                timeout=90,
                preserve_leading_ws=True,
                cwd=str(repo_root),
            )
            state["typescript_projects_checked"] = 1
            if ok:
                state["typescript_errors"] = 0
            else:
                error_count = _count_typescript_errors(output)
                state["typescript_errors"] = error_count if error_count > 0 else -1
        else:
            # Monorepo fallback: sample up to 3 package tsconfigs.
            total_errors = 0
            unknown_failure = False
            for tsconfig in tsconfig_files[:3]:
                output, ok = run_command(
                    [
                        "npx",
                        "tsc",
                        "--noEmit",
                        "--pretty",
                        "false",
                        "--project",
                        str(tsconfig),
                    ],
                    timeout=75,
                    preserve_leading_ws=True,
                    cwd=str(repo_root),
                )
                state["typescript_projects_checked"] += 1
                if ok:
                    continue
                error_count = _count_typescript_errors(output)
                if error_count > 0:
                    total_errors += error_count
                else:
                    unknown_failure = True

            if total_errors > 0:
                state["typescript_errors"] = total_errors
            elif unknown_failure:
                state["typescript_errors"] = -1
            else:
                state["typescript_errors"] = 0

        if state["typescript_errors"] > 0:
            state["urgency"] = "HIGH"
        elif state["typescript_errors"] == -1 and state["urgency"] != "HIGH":
            state["urgency"] = "MEDIUM"

    # Check for lint
    if (repo_root / "package.json").exists():
        try:
            pkg_json = json.loads((repo_root / "package.json").read_text())
            scripts = pkg_json.get("scripts", {})
            state["has_lint"] = any(
                name in scripts for name in ["lint", "lint:ts", "lint:js"]
            )
        except (json.JSONDecodeError, OSError, TypeError):
            state["has_lint"] = False

    return state


def analyze_issues(repo_root: Path) -> Dict[str, Any]:
    """Analyze GitHub issues."""
    state = {"has_gh": False, "open_count": 0, "issues": [], "urgency": "LOW"}

    # Check for gh CLI
    _, has_gh = run_command(["gh", "--version"], cwd=str(repo_root))
    state["has_gh"] = has_gh

    if not has_gh:
        return state

    # Get open issues
    output, ok = run_command(
        [
            "gh",
            "issue",
            "list",
            "--state",
            "open",
            "--limit",
            "10",
            "--json",
            "number,title,labels",
        ],
        cwd=str(repo_root),
    )
    if ok and output:
        try:
            issues = json.loads(output)
            state["open_count"] = len(issues)
            state["issues"] = issues[:5]

            # Check for priority labels
            for issue in issues:
                labels = set(_normalize_label_names(issue.get("labels", [])))
                if labels & HIGH_PRIORITY_LABELS:
                    state["urgency"] = "HIGH"
                    break
                elif labels & MEDIUM_PRIORITY_LABELS and state["urgency"] != "HIGH":
                    state["urgency"] = "MEDIUM"
        except json.JSONDecodeError:
            # Ignore malformed JSON - issue data is optional context
            pass

    return state


def analyze_feature_branches(repo_root: Path) -> Dict[str, Any]:
    """Analyze feature/fix branches with work in progress."""
    import re

    state = {"has_feature_branches": False, "branches": [], "urgency": "LOW"}

    # Get all local branches
    branches, ok = run_command(["git", "branch"], cwd=str(repo_root))
    if not ok:
        return state

    # Patterns for feature/fix branches
    branch_patterns = [r"^feat/", r"^fix/", r"^feature/"]
    issue_pattern = r"(?:issue-|#)?(\d+)"

    for line in branches.split("\n"):
        branch = line.strip().lstrip("* ").strip()
        if not branch or branch == "main" or branch == "master":
            continue

        # Check if it's a feature/fix branch
        is_feature_branch = any(
            re.search(pattern, branch) for pattern in branch_patterns
        )
        if not is_feature_branch:
            continue

        # Extract issue number if present
        issue_match = re.search(issue_pattern, branch)
        issue_number = int(issue_match.group(1)) if issue_match else None

        # Get last commit date and message
        date_output, _ = run_command(
            ["git", "log", "-1", "--format=%ar", branch], cwd=str(repo_root)
        )
        msg_output, _ = run_command(
            ["git", "log", "-1", "--format=%s", branch], cwd=str(repo_root)
        )

        # Count commits ahead of main
        ahead_output, _ = run_command(
            ["git", "rev-list", "--count", f"main..{branch}"], cwd=str(repo_root)
        )
        commits_ahead = (
            int(ahead_output.strip()) if ahead_output.strip().isdigit() else 0
        )

        branch_info = {
            "name": branch,
            "age": date_output or "unknown",
            "last_commit": msg_output or "",
            "commits_ahead": commits_ahead,
            "issue_number": issue_number,
        }

        state["branches"].append(branch_info)

    if state["branches"]:
        state["has_feature_branches"] = True
        # Higher urgency if branches have work
        if any(b["commits_ahead"] > 0 for b in state["branches"]):
            state["urgency"] = "MEDIUM"

    # Sort by most recent activity
    state["branches"].sort(key=lambda x: x.get("age", ""), reverse=False)

    return state


def analyze_research_branches(repo_root: Path) -> Dict[str, Any]:
    """Analyze research branches from Claude Code Web sessions."""
    state = {"has_research_branches": False, "branches": [], "urgency": "LOW"}

    # Fetch to get all remote branches
    # SECURE: Using list-based arguments instead of shell string
    run_command(["git", "fetch", "--all", "--prune"], cwd=str(repo_root))

    # Look for research-related branches
    branches, ok = run_command(["git", "branch", "-r"], cwd=str(repo_root))
    if not ok:
        return state

    research_patterns = ["research-", "claude/research", "/research-"]

    for line in branches.split("\n"):
        branch = line.strip()
        if not branch or "HEAD" in branch:
            continue

        # Check if it matches research patterns
        if any(pattern in branch.lower() for pattern in research_patterns):
            # Get branch creation time - SECURE: branch is separate argument
            date_output, _ = run_command(
                ["git", "log", "-1", "--format=%ar", branch], cwd=str(repo_root)
            )

            state["branches"].append({"name": branch, "age": date_output or "unknown"})

    if state["branches"]:
        state["has_research_branches"] = True
        state["urgency"] = "HIGH"

    return state


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze project state")
    parser.add_argument(
        "--section",
        choices=["git", "code", "issues", "branches", "research", "all"],
        default="all",
        help="Section to analyze",
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root path to analyze (defaults to current git repo or script repo)",
    )
    args = parser.parse_args()
    repo_root = _resolve_repo_root(args.repo_root)

    result = {
        "operation": "analyze_state",
        "section": args.section,
        "repo_root": str(repo_root),
        "timestamp": datetime.now().isoformat(),
    }

    if args.section in ["git", "all"]:
        result["git"] = analyze_git_state(repo_root)

    if args.section in ["code", "all"]:
        result["code"] = analyze_code_state(repo_root)

    if args.section in ["issues", "all"]:
        result["issues"] = analyze_issues(repo_root)

    if args.section in ["branches", "all"]:
        result["branches"] = analyze_feature_branches(repo_root)

    if args.section in ["research", "all"]:
        result["research"] = analyze_research_branches(repo_root)

    # Calculate overall urgency
    urgencies = []
    for section in ["git", "code", "issues", "branches", "research"]:
        if section in result:
            urgencies.append(result[section].get("urgency", "LOW"))

    if "HIGH" in urgencies:
        result["overall_urgency"] = "HIGH"
    elif "MEDIUM" in urgencies:
        result["overall_urgency"] = "MEDIUM"
    else:
        result["overall_urgency"] = "LOW"

    result["success"] = True
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
