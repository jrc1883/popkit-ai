#!/usr/bin/env python3
"""
Action Recommendation Script.

Score, rank, and recommend next actions based on project state.

Usage:
    python recommend_action.py [--mode MODE] [--state-file FILE]

Modes:
    score  - Calculate scores for all possible actions
    rank   - Rank actions by score
    report - Generate recommendation report

Output:
    JSON object with scored and ranked recommendations
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from popkit_shared.utils.interaction_surface import DecisionSpec, QuestionOption

# Base priority scores
BASE_PRIORITIES = {
    "fix_build_errors": 90,
    "process_research": 85,
    "commit_work": 80,
    "cleanup_stale_branches": 55,
    "push_changes": 60,
    "work_on_issue": 50,
    "tackle_tech_debt": 40,
    "start_new_feature": 30,
    "health_check": 20,
}

# Context multipliers
MULTIPLIERS = {
    "uncommitted_changes": 20,
    "typescript_errors": 30,
    "research_branches": 25,
    "many_open_issues": 10,
    "high_priority_issue": 15,
}

HIGH_PRIORITY_LABELS = {
    "p0-critical",
    "p1-high",
    "priority:critical",
    "priority:high",
}

DECISION_SPEC_HEADER = "Next Action"
DECISION_SPEC_QUESTION = "What should PopKit do next in this repository?"
DECISION_SPEC_SOURCE_COMMAND = "/popkit-dev:next"


def _normalize_labels(labels: List[Dict[str, Any]]) -> List[str]:
    """Normalize issue label names for case-insensitive matching."""
    return [str(label.get("name", "")).strip().lower() for label in labels]


def _resolve_repo_root(state: Dict[str, Any], repo_root_arg: Optional[str] = None) -> Path:
    """Resolve repository root for command translation."""
    if repo_root_arg:
        return Path(repo_root_arg).expanduser().resolve()

    candidate = state.get("repo_root")
    if candidate:
        return Path(str(candidate)).expanduser().resolve()

    cwd = Path.cwd()
    if (cwd / ".git").exists():
        return cwd

    # Fallback to the popkit-claude repository this script lives in.
    try:
        return Path(__file__).resolve().parents[5]
    except IndexError:
        return cwd


def _translate_popkit_command(command: str, repo_root: Path) -> Dict[str, str]:
    """Translate PopKit slash commands into Codex-runnable equivalents."""
    cmd = command.strip()
    if not cmd:
        return {"codex_command": "", "codex_note": ""}

    repo_str = str(repo_root)
    validate_commit_py = (
        repo_root / "packages" / "shared-py" / "popkit_shared" / "utils" / "validate_commit.py"
    )
    morning_py = (
        repo_root
        / "packages"
        / "popkit-dev"
        / "skills"
        / "pop-morning"
        / "scripts"
        / "morning_workflow.py"
    )
    analyze_state_py = (
        repo_root
        / "packages"
        / "popkit-dev"
        / "skills"
        / "pop-next-action"
        / "scripts"
        / "analyze_state.py"
    )
    merge_conflicts_py = (
        repo_root
        / "packages"
        / "popkit-research"
        / "skills"
        / "pop-research-merge"
        / "scripts"
        / "detect_conflicts.py"
    )

    match = re.match(r"^/popkit:dev work #(\d+)$", cmd)
    if match:
        issue_num = match.group(1)
        return {
            "codex_command": (
                f"gh issue view {issue_num} -R jrc1883/popkit-claude && "
                f'git -C "{repo_str}" checkout -b feat/issue-{issue_num}'
            ),
            "codex_note": "Creates a local feature branch after loading issue context.",
        }

    match = re.match(r"^/popkit-dev:git merge (.+)$", cmd)
    if match:
        base_ref = match.group(1).strip()
        return {
            "codex_command": (
                f'git -C "{repo_str}" fetch origin {base_ref} && '
                f'git -C "{repo_str}" merge origin/{base_ref}'
            ),
            "codex_note": "Merges latest base branch into the current branch.",
        }

    slash_map = {
        "/popkit:git commit": {
            "codex_command": (
                f'git -C "{repo_str}" add -A && '
                f'python "{str(validate_commit_py)}" '
                '"chore(wip): checkpoint current changes" && '
                f'git -C "{repo_str}" commit -m "chore(wip): checkpoint current changes"'
            ),
            "codex_note": (
                "Replace the default message with your preferred "
                "type(scope): description before running."
            ),
        },
        "/popkit:git push": {
            "codex_command": f'git -C "{repo_str}" push',
            "codex_note": "",
        },
        "/popkit:git review": {
            "codex_command": f'git -C "{repo_str}" diff --stat && git -C "{repo_str}" diff',
            "codex_note": "",
        },
        "/popkit:routine morning": {
            "codex_command": (f'python "{str(morning_py)}" --profile standard --quick'),
            "codex_note": "",
        },
        "/popkit:debug": {
            "codex_command": (f'python "{str(analyze_state_py)}" --section code'),
            "codex_note": "Runs code-health diagnostics to guide debugging next steps.",
        },
        "/popkit:dev brainstorm": {
            "codex_command": (
                'echo "Use skill: pop-writing-plans-codex for structured brainstorming/planning"'
            ),
            "codex_note": "",
        },
    }
    if cmd in slash_map:
        return slash_map[cmd]

    if cmd.startswith("/popkit:research merge"):
        return {
            "codex_command": (
                f'git -C "{repo_str}" fetch --all --prune && '
                f'git -C "{repo_str}" branch -r | rg "research"'
            ),
            "codex_note": "Lists research branches to process with research merge scripts.",
        }

    if cmd.lower().startswith("invoke pop-research-merge skill"):
        return {
            "codex_command": f'python "{str(merge_conflicts_py)}" --help',
            "codex_note": "Use merge scripts after selecting concrete research files/branches.",
        }

    return {
        "codex_command": cmd,
        "codex_note": "No explicit translation rule; using original command text.",
    }


def _annotate_actions_for_runtime(
    actions: List[Dict[str, Any]],
    runtime: str,
    repo_root: Path,
) -> List[Dict[str, Any]]:
    """Attach Codex command translations and optionally switch command output."""
    annotated: List[Dict[str, Any]] = []
    for action in actions:
        row = dict(action)
        translated = _translate_popkit_command(str(row.get("command", "")), repo_root)
        row["codex_command"] = translated.get("codex_command", "")
        if translated.get("codex_note"):
            row["codex_note"] = translated["codex_note"]

        if runtime == "codex" and row.get("codex_command"):
            row["command"] = row["codex_command"]

        annotated.append(row)
    return annotated


def _build_quick_reference(runtime: str, repo_root: Path) -> List[Dict[str, Any]]:
    """Build quick-reference rows with Codex translations."""
    rows = [
        {"goal": "Commit changes", "command": "/popkit:git commit"},
        {"goal": "Review code", "command": "/popkit:git review"},
        {"goal": "Project health", "command": "/popkit:routine morning"},
        {"goal": "Plan a feature", "command": "/popkit:dev brainstorm"},
        {"goal": "Debug an issue", "command": "/popkit:debug"},
    ]
    return _annotate_actions_for_runtime(rows, runtime, repo_root)


def _action_to_question_option(
    action: Dict[str, Any],
    *,
    recommended: bool,
) -> QuestionOption:
    """Convert a ranked action into a provider-neutral decision option."""
    why = str(action.get("why", "")).strip()
    benefit = str(action.get("benefit", "")).strip()
    if why and benefit:
        separator = "" if why.endswith((".", "!", "?")) else "."
        description = f"{why}{separator} Benefit: {benefit}"
    else:
        description = why or benefit or "Review this recommended action."

    return QuestionOption(
        id=str(action.get("id", "next_action")),
        label=str(action.get("name", "Recommended action")),
        description=description,
        recommended=recommended,
        follow_up=str(action.get("command", "")).strip() or None,
    )


def build_decision_spec(report: Dict[str, Any]) -> Dict[str, Any]:
    """Build a provider-neutral decision spec from a recommendation report."""
    recommendations = report.get("recommendations", [])[:3]
    options = [
        _action_to_question_option(action, recommended=index == 0)
        for index, action in enumerate(recommendations)
    ]
    follow_up = None
    if recommendations:
        follow_up = str(recommendations[0].get("command", "")).strip() or None

    spec = DecisionSpec(
        header=DECISION_SPEC_HEADER,
        question=DECISION_SPEC_QUESTION,
        options=options,
        source_command=DECISION_SPEC_SOURCE_COMMAND,
        follow_up=follow_up,
    )
    return spec.to_dict()


def load_state(state_file: Optional[str] = None) -> Dict[str, Any]:
    """Load project state from file or analyze."""
    if state_file and Path(state_file).exists():
        return json.loads(Path(state_file).read_text())

    # Default empty state
    return {
        "git": {"uncommitted_count": 0, "ahead_count": 0, "urgency": "LOW"},
        "code": {"typescript_errors": 0, "urgency": "LOW"},
        "issues": {"open_count": 0, "issues": [], "urgency": "LOW"},
        "research": {"has_research_branches": False, "branches": [], "urgency": "LOW"},
    }


def calculate_action_scores(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Calculate scores for all possible actions."""
    actions = []

    git = state.get("git", {})
    code = state.get("code", {})
    issues = state.get("issues", {})
    research = state.get("research", {})

    # Fix build errors
    if code.get("typescript_errors", 0) > 0:
        score = BASE_PRIORITIES["fix_build_errors"] + MULTIPLIERS["typescript_errors"]
        actions.append(
            {
                "id": "fix_build_errors",
                "name": "Fix Build Errors",
                "command": "/popkit:debug",
                "score": score,
                "why": f"TypeScript has {code['typescript_errors']} errors blocking build",
                "what": "Systematic debugging with root cause analysis",
                "benefit": "Unblocked development, passing CI",
            }
        )
    elif code.get("typescript_errors", 0) < 0:
        actions.append(
            {
                "id": "diagnose_typescript",
                "name": "Diagnose TypeScript Tooling",
                "command": "/popkit:debug",
                "score": 65,
                "why": "TypeScript diagnostics returned unknown status",
                "what": "Check TypeScript configuration and project-level toolchain",
                "benefit": "Restore reliable error detection before feature work",
            }
        )

    # Process research branches
    if research.get("has_research_branches") and research.get("branches"):
        score = BASE_PRIORITIES["process_research"] + MULTIPLIERS["research_branches"]
        branch_count = len(research["branches"])
        actions.append(
            {
                "id": "process_research",
                "name": "Process Research Branches",
                "command": "Invoke pop-research-merge skill",
                "score": score,
                "why": f"Found {branch_count} research branch(es) from Claude Code Web sessions",
                "what": "Merges research content, organizes docs, creates GitHub issues",
                "benefit": "Research findings become actionable issues in your backlog",
                "branches": research["branches"],
            }
        )

    # Continue work on feature branches
    branches = state.get("branches", {})
    stale_branches = branches.get("stale_branches", [])

    if stale_branches:
        score = BASE_PRIORITIES["cleanup_stale_branches"]
        if branches.get("has_feature_branches"):
            score -= 10

        actions.append(
            {
                "id": "review_stale_branches",
                "name": "Review Stale Local Branches",
                "command": "git branch -vv",
                "score": score,
                "why": (f"{len(stale_branches)} feature/fix branch(es) track deleted upstreams"),
                "what": (
                    "Confirm merged status and delete stale local branches that are no longer needed"
                ),
                "benefit": "Cleaner local context and better next-action recommendations",
                "stale_branches": stale_branches,
            }
        )

    if branches.get("has_feature_branches") and branches.get("branches"):
        # Sort by commits ahead (most work = highest priority)
        sorted_branches = sorted(
            branches["branches"], key=lambda b: b.get("commits_ahead", 0), reverse=True
        )
        top_branch = sorted_branches[0]

        score = 75  # High priority - work already started
        if top_branch.get("commits_ahead", 0) > 5:
            score += 10  # Bonus for significant work

        branch_name = top_branch.get("name", "")
        issue_num = top_branch.get("issue_number")
        commits_ahead = top_branch.get("commits_ahead", 0)
        last_commit = top_branch.get("last_commit", "")

        why_msg = f"Branch '{branch_name}' has {commits_ahead} commits"
        if issue_num:
            why_msg += f" (linked to issue #{issue_num})"

        actions.append(
            {
                "id": "continue_feature_branch",
                "name": f"Continue Work on {branch_name}",
                "command": f"git checkout {branch_name}",
                "score": score,
                "why": why_msg,
                "what": f"Resume work on feature branch. Last commit: {last_commit[:60]}",
                "benefit": "Complete started work before starting something new",
                "branch": branch_name,
                "issue_number": issue_num,
                "all_branches": [
                    {
                        "name": b.get("name"),
                        "commits": b.get("commits_ahead", 0),
                        "issue": b.get("issue_number"),
                        "age": b.get("age"),
                    }
                    for b in sorted_branches
                ],
            }
        )

    # Commit uncommitted work
    if git.get("uncommitted_count", 0) > 0:
        score = BASE_PRIORITIES["commit_work"] + MULTIPLIERS["uncommitted_changes"]
        actions.append(
            {
                "id": "commit_work",
                "name": "Commit Current Work",
                "command": "/popkit:git commit",
                "score": score,
                "why": f"You have {git['uncommitted_count']} uncommitted files",
                "what": "Auto-generates commit message matching repo style",
                "benefit": "Clean working directory, changes safely versioned",
            }
        )

    # Push changes
    if git.get("ahead_count", 0) > 0:
        score = BASE_PRIORITIES["push_changes"]
        actions.append(
            {
                "id": "push_changes",
                "name": "Push Changes",
                "command": "/popkit:git push",
                "score": score,
                "why": f"You have {git['ahead_count']} commits ahead of remote",
                "what": "Push changes to remote repository",
                "benefit": "Work backed up and visible to team",
            }
        )

    # Sync worktree with base branch
    worktree = git.get("worktree", {})
    if worktree and worktree.get("behindBase", 0) > 0:
        base_ref = worktree.get("baseRef", "main")
        behind_count = worktree["behindBase"]
        score = 70  # Higher than push, important to stay in sync

        actions.append(
            {
                "id": "sync_worktree",
                "name": f"Sync worktree with {base_ref}",
                "command": f"/popkit-dev:git merge {base_ref}",
                "score": score,
                "why": f"Worktree is {behind_count} commits behind {base_ref}",
                "what": f"Merge latest changes from {base_ref} into current worktree",
                "benefit": "Stay up to date with base branch, avoid merge conflicts later",
            }
        )

    # Work on issue
    if issues.get("open_count", 0) > 0 and issues.get("issues"):
        top_issue = issues["issues"][0]
        score = BASE_PRIORITIES["work_on_issue"]

        # Boost for priority labels
        labels = set(_normalize_labels(top_issue.get("labels", [])))
        is_high_priority = bool(labels & HIGH_PRIORITY_LABELS)
        if is_high_priority:
            score += MULTIPLIERS["high_priority_issue"]

        if issues["open_count"] >= 5:
            score += MULTIPLIERS["many_open_issues"]

        actions.append(
            {
                "id": "work_on_issue",
                "name": "Work on Open Issue",
                "command": f"/popkit:dev work #{top_issue['number']}",
                "score": score,
                "why": (
                    f'Issue #{top_issue["number"]} "{top_issue["title"]}" is high priority'
                    if is_high_priority
                    else f'Issue #{top_issue["number"]} "{top_issue["title"]}" is ready to pick up'
                ),
                "what": "Issue-driven development workflow",
                "benefit": "Structured progress on prioritized work",
                "issue": top_issue,
            }
        )

    # Health check (always available)
    if not actions or all(a["score"] < 50 for a in actions):
        score = BASE_PRIORITIES["health_check"]
        actions.append(
            {
                "id": "health_check",
                "name": "Check Project Health",
                "command": "/popkit:routine morning",
                "score": score,
                "why": "No urgent items - good time for health check",
                "what": "Comprehensive project status with Ready to Code score",
                "benefit": "Identify hidden issues before they become urgent",
            }
        )

    return actions


def rank_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank actions by score (highest first)."""
    return sorted(actions, key=lambda x: x["score"], reverse=True)


def generate_report(
    ranked_actions: List[Dict[str, Any]],
    state: Dict[str, Any],
    runtime: str = "both",
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Generate recommendation report."""
    repo_root = repo_root or _resolve_repo_root(state)
    recommendations = _annotate_actions_for_runtime(ranked_actions[:5], runtime, repo_root)
    report = {
        "runtime": runtime,
        "repo_root": str(repo_root),
        "state_summary": {
            "uncommitted": state.get("git", {}).get("uncommitted_count", 0),
            "branch_sync": "ahead" if state.get("git", {}).get("ahead_count", 0) > 0 else "synced",
            "typescript": (
                "errors"
                if state.get("code", {}).get("typescript_errors", 0) > 0
                else (
                    "unknown" if state.get("code", {}).get("typescript_errors", 0) < 0 else "clean"
                )
            ),
            "open_issues": state.get("issues", {}).get("open_count", 0),
            "research_branches": len(state.get("research", {}).get("branches", [])),
        },
        "recommendations": recommendations,  # Top 5
        "quick_reference": _build_quick_reference(runtime, repo_root),
    }
    report["decision_spec"] = build_decision_spec(report)

    return report


def format_report_display(report: Dict[str, Any]) -> str:
    """Format report for display."""
    lines = []
    state = report["state_summary"]

    lines.append("## Current State\n")
    lines.append("| Indicator | Status | Urgency |")
    lines.append("|-----------|--------|---------|")
    lines.append(
        f"| Uncommitted | {state['uncommitted']} files | {'HIGH' if state['uncommitted'] > 0 else 'OK'} |"
    )
    lines.append(
        f"| Branch Sync | {state['branch_sync']} | {'MEDIUM' if state['branch_sync'] == 'ahead' else 'OK'} |"
    )
    lines.append(
        f"| TypeScript | {state['typescript']} | {'HIGH' if state['typescript'] == 'errors' else ('MEDIUM' if state['typescript'] == 'unknown' else 'OK')} |"
    )
    lines.append(
        f"| Open Issues | {state['open_issues']} | {'MEDIUM' if state['open_issues'] > 3 else 'LOW'} |"
    )
    if state["research_branches"] > 0:
        lines.append(f"| Research Branches | {state['research_branches']} | HIGH |")

    lines.append("\n## Recommended Actions\n")

    for i, action in enumerate(report["recommendations"][:3], 1):
        lines.append(f"### {i}. {action['name']} (Score: {action['score']})")
        lines.append(f"**Command:** `{action['command']}`")
        if action.get("codex_command") and action["codex_command"] != action["command"]:
            lines.append(f"**Codex Equivalent:** `{action['codex_command']}`")
        if action.get("codex_note"):
            lines.append(f"**Codex Note:** {action['codex_note']}")
        lines.append(f"**Why:** {action['why']}")
        lines.append(f"**What it does:** {action['what']}")
        lines.append(f"**Benefit:** {action['benefit']}")
        lines.append("")

    lines.append("## Quick Reference\n")
    has_codex_column = any(
        item.get("codex_command") and item["codex_command"] != item["command"]
        for item in report["quick_reference"]
    )
    if has_codex_column:
        lines.append("| If you want to... | PopKit Command | Codex Equivalent |")
        lines.append("|-------------------|----------------|------------------|")
        for item in report["quick_reference"]:
            codex_value = item.get("codex_command", item["command"])
            lines.append(f"| {item['goal']} | `{item['command']}` | `{codex_value}` |")
    else:
        lines.append("| If you want to... | Use this command |")
        lines.append("|-------------------|------------------|")
        for item in report["quick_reference"]:
            lines.append(f"| {item['goal']} | `{item['command']}` |")

    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Recommend next action")
    parser.add_argument(
        "--mode",
        choices=["score", "rank", "report"],
        default="report",
        help="Output mode",
    )
    parser.add_argument("--state-file", help="Path to state JSON file")
    parser.add_argument(
        "--format",
        choices=["json", "display", "decision-spec"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--runtime",
        choices=["claude", "codex", "both"],
        default="both",
        help="Command style for recommendations",
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root path to translate commands against",
    )
    args = parser.parse_args()

    if args.format == "decision-spec" and args.mode != "report":
        parser.error("--format decision-spec requires --mode report")

    result = {
        "operation": f"recommend_action_{args.mode}",
        "timestamp": datetime.now().isoformat(),
    }

    # Load state
    state = load_state(args.state_file)
    if args.repo_root:
        state["repo_root"] = str(Path(args.repo_root).expanduser().resolve())
    repo_root = _resolve_repo_root(state, args.repo_root)
    result["state"] = state
    result["repo_root"] = str(repo_root)

    # Calculate scores
    actions = calculate_action_scores(state)

    if args.mode == "score":
        result["actions"] = actions

    elif args.mode in ["rank", "report"]:
        ranked = rank_actions(actions)
        result["ranked_actions"] = _annotate_actions_for_runtime(ranked, args.runtime, repo_root)

        if args.mode == "report":
            report = generate_report(ranked, state, runtime=args.runtime, repo_root=repo_root)
            result["report"] = report

            if args.format == "display":
                print(format_report_display(report))
                return 0
            if args.format == "decision-spec":
                print(json.dumps(report["decision_spec"], indent=2))
                return 0

    result["success"] = True
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
