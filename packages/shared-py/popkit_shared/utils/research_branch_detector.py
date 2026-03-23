#!/usr/bin/env python3
"""
Research Branch Detector Utility

Detects and processes research branches created by Claude Code Web sessions.
Part of issue #181: Auto-Process Research Branches in /popkit:next

Patterns detected:
- origin/claude/research-*
- origin/claude/*-research-*
- Branches with research docs (*.md in root, .claude/research/, or legacy docs/research/)

Usage:
    from popkit_shared.utils.research_branch_detector import (
        fetch_remotes,
        get_research_branches,
        parse_research_doc,
        get_branch_content,
    )
"""

import json
import re
from dataclasses import dataclass

from popkit_shared.utils.subprocess_utils import run_git_command


@dataclass
class ResearchBranch:
    """Represents a detected research branch.

    Attributes:
        full_name: Full remote ref (e.g., origin/claude/research-claude-code-features-01Wp...).
        short_name: Cleaned short name without remote prefix or session ID suffix.
        topic: Extracted topic slug (e.g., claude-code-features).
        created_ago: Human-readable time since last commit (e.g., "2 hours ago").
        commit_count: Number of commits ahead of the main branch.
        files_changed: List of file paths changed relative to main.
        has_docs: Whether the branch contains documentation files.
        doc_paths: Paths to detected research documentation files.
    """

    full_name: str
    short_name: str
    topic: str
    created_ago: str
    commit_count: int
    files_changed: list[str]
    has_docs: bool
    doc_paths: list[str]


def _run_git(args: list[str]) -> tuple[bool, str]:
    """Run a git command and return (success, output).

    Thin wrapper around subprocess_utils.run_git_command that returns
    (bool, str) for backward compatibility with internal callers.

    Args:
        args: Git arguments without the leading 'git'.

    Returns:
        Tuple of (success, output_or_error).
    """
    output, success = run_git_command(args)
    return success, output


def fetch_remotes() -> bool:
    """Fetch all remotes and prune deleted branches.

    Runs ``git fetch --all --prune`` so that the local view of remote
    branches is up to date before detection.

    Returns:
        True if the fetch succeeded, False otherwise.
    """
    success, _ = _run_git(["fetch", "--all", "--prune"])
    return success


def get_research_branches(remote: str = "origin") -> list[ResearchBranch]:
    """Detect research branches matching known patterns.

    Scans remote branches for names that match Claude Code Web session
    research patterns:

    1. ``{remote}/claude/research-*``
    2. ``{remote}/claude/*-research-*``

    Args:
        remote: Git remote name to scan. Defaults to "origin".

    Returns:
        List of ResearchBranch objects with metadata for each detected
        branch. Returns an empty list if no branches match or if the
        git command fails.
    """
    branches: list[ResearchBranch] = []

    # Get all remote branches
    success, output = _run_git(["branch", "-r", "--format=%(refname:short)"])
    if not success:
        return branches

    all_remotes = output.split("\n") if output else []

    # Pattern 1 & 2: Claude research branches
    research_patterns = [
        rf"{re.escape(remote)}/claude/research-(.+)",
        rf"{re.escape(remote)}/claude/(.+)-research-(.+)",
    ]

    for branch in all_remotes:
        branch = branch.strip()
        if not branch:
            continue

        # Check pattern matches
        for pattern in research_patterns:
            match = re.match(pattern, branch)
            if match:
                research_branch = _analyze_branch(branch, match)
                if research_branch:
                    branches.append(research_branch)
                break

    return branches


def _analyze_branch(full_name: str, match: re.Match) -> ResearchBranch | None:
    """Analyze a branch to extract research information.

    Args:
        full_name: Full remote branch ref (e.g., origin/claude/research-topic-abc123).
        match: Regex match object from pattern detection.

    Returns:
        A ResearchBranch with populated metadata, or None if analysis fails.
    """
    # Extract topic from match groups
    groups = match.groups()
    if len(groups) == 1:
        topic = groups[0]
    else:
        topic = "-".join(groups)

    # Remove session ID suffix (e.g., -01WpyQzGrNeGx7cSNqM91iqP)
    topic_clean = re.sub(r"-[A-Za-z0-9]{20,}$", "", topic)

    # Get commit info
    success, commit_time = _run_git(["log", "-1", "--format=%ar", full_name])
    created_ago = commit_time if success else "unknown"

    # Get commit count ahead of master
    success, count = _run_git(["rev-list", "--count", f"master..{full_name}"])
    commit_count = int(count) if success and count.isdigit() else 0

    # Get files changed
    success, diff_stat = _run_git(["diff", "--stat", "--name-only", f"master...{full_name}"])
    files_changed = diff_stat.split("\n") if success and diff_stat else []
    files_changed = [f.strip() for f in files_changed if f.strip()]

    # Detect doc files
    doc_patterns = [
        r"\.claude/research/.*\.md",
        r"docs/research/.*\.md",
        r"docs/.*RESEARCH.*\.md",
        r"RESEARCH.*\.md",
        r".*_RESEARCH\.md",
    ]

    doc_paths = []
    for f in files_changed:
        for pattern in doc_patterns:
            if re.match(pattern, f, re.IGNORECASE):
                doc_paths.append(f)
                break

    has_docs = len(doc_paths) > 0 or any("docs" in f.lower() for f in files_changed)

    # Generate short name
    short_name = full_name.replace("origin/claude/", "").replace("origin/", "")
    short_name = re.sub(r"-[A-Za-z0-9]{20,}$", "", short_name)  # Remove session ID

    return ResearchBranch(
        full_name=full_name,
        short_name=short_name,
        topic=topic_clean,
        created_ago=created_ago,
        commit_count=commit_count,
        files_changed=files_changed,
        has_docs=has_docs,
        doc_paths=doc_paths,
    )


def get_branch_content(branch: str, path: str) -> str:
    """Read a file from a branch without checking it out.

    Uses ``git show <branch>:<path>`` to retrieve file contents directly
    from the object store.

    Args:
        branch: Full branch ref (e.g., "origin/claude/research-topic").
        path: File path relative to the repository root.

    Returns:
        File contents as a string.

    Raises:
        FileNotFoundError: If the path does not exist on the branch.
        RuntimeError: If the git command fails for another reason.
    """
    success, output = _run_git(["show", f"{branch}:{path}"])
    if not success:
        if "does not exist" in output or "not exist" in output or "fatal" in output:
            raise FileNotFoundError(f"Path '{path}' not found on branch '{branch}': {output}")
        raise RuntimeError(f"Failed to read '{path}' from '{branch}': {output}")
    return output


def format_branch_table(branches: list[ResearchBranch]) -> str:
    """Format research branches as a markdown table.

    Args:
        branches: List of detected research branches.

    Returns:
        Markdown-formatted table string, or a "no branches" message if
        the list is empty.
    """
    if not branches:
        return "No research branches detected."

    lines = ["| Branch | Topic | Created | Files |", "|--------|-------|---------|-------|"]

    for b in branches:
        files_summary = f"{len(b.files_changed)} files"
        if b.has_docs:
            files_summary += " (has docs)"
        lines.append(f"| `{b.short_name}` | {b.topic} | {b.created_ago} | {files_summary} |")

    return "\n".join(lines)


def get_branch_content_preview(branch: ResearchBranch, max_lines: int = 50) -> dict[str, str]:
    """Get preview of doc content from a research branch.

    Reads the first ``max_lines`` of up to 3 documentation files found
    on the branch.

    Args:
        branch: ResearchBranch to preview.
        max_lines: Maximum number of lines to return per file.

    Returns:
        Dict mapping file path to truncated content string.
    """
    previews: dict[str, str] = {}

    for doc_path in branch.doc_paths[:3]:  # Limit to 3 docs
        try:
            content = get_branch_content(branch.full_name, doc_path)
            lines = content.split("\n")[:max_lines]
            previews[doc_path] = "\n".join(lines)
        except (FileNotFoundError, RuntimeError):
            continue

    return previews


def parse_research_doc(content: str) -> dict[str, object]:
    """Parse a research document to extract structured information.

    Extracts YAML-style frontmatter metadata and markdown sections from
    a research document following the standard format::

        # Research: [Topic Name]

        **Research Date:** YYYY-MM-DD
        **Status:** Research Document
        **Priority:** P1-high | P2-medium | P3-low

        ## Executive Summary
        [This becomes the issue body]

        ## Implementation Tasks
        - [ ] Task 1
        - [ ] Task 2

    Args:
        content: Raw markdown content of the research document.

    Returns:
        Dict with keys: title, date, priority, summary, tasks,
        raw_content. Tasks is a list of strings; other values are
        strings. Missing fields default to empty strings or
        "P2-medium" for priority.
    """
    result: dict[str, object] = {
        "title": "",
        "date": "",
        "priority": "P2-medium",
        "summary": "",
        "tasks": [],
        "raw_content": content,
    }

    lines = content.split("\n")

    # Extract title
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            # Clean up "Research: " prefix
            title = re.sub(r"^Research:\s*", "", title)
            result["title"] = title
            break

    # Extract metadata
    for line in lines:
        if "**Research Date:**" in line or "**Date:**" in line or "Date:" in line:
            date_match = re.search(r"(\d{4}-\d{2}-\d{2}|[A-Z][a-z]+ \d{1,2}, \d{4})", line)
            if date_match:
                result["date"] = date_match.group(0)
        elif "**Priority:**" in line:
            prio_match = re.search(r"P[0-3]-(critical|high|medium|low)", line, re.IGNORECASE)
            if prio_match:
                result["priority"] = prio_match.group(0)

    # Extract executive summary
    in_summary = False
    summary_lines: list[str] = []
    for line in lines:
        if "## Executive Summary" in line:
            in_summary = True
            continue
        elif in_summary and line.startswith("## "):
            break
        elif in_summary:
            summary_lines.append(line)

    result["summary"] = "\n".join(summary_lines).strip()

    # Extract implementation tasks
    tasks: list[str] = []
    in_tasks = False
    for line in lines:
        if "## Implementation" in line or "## Tasks" in line:
            in_tasks = True
            continue
        elif in_tasks and line.startswith("## "):
            break
        elif in_tasks:
            task_match = re.match(r"^\s*-\s*\[[ x]\]\s*(.+)", line)
            if task_match:
                tasks.append(task_match.group(1))

    result["tasks"] = tasks

    return result


def generate_issue_body(branch: ResearchBranch, parsed_docs: list[dict[str, object]]) -> str:
    """Generate a GitHub issue body from research branch content.

    Args:
        branch: The research branch to generate the issue for.
        parsed_docs: List of parsed research documents (from parse_research_doc).

    Returns:
        Markdown-formatted issue body string.
    """
    # Use first doc for primary content
    primary = parsed_docs[0] if parsed_docs else {}

    body_parts = [
        "## Summary",
        "",
        str(primary.get("summary", "Research findings from Claude Code Web session.")),
        "",
        "## Source",
        f"- **Branch:** `{branch.full_name}`",
        f"- **Created:** {branch.created_ago}",
        f"- **Files:** {len(branch.files_changed)} changed",
    ]

    if branch.doc_paths:
        body_parts.extend(
            [
                "",
                "## Documentation",
                "",
            ]
        )
        for path in branch.doc_paths:
            body_parts.append(f"- `{path}`")

    tasks = primary.get("tasks", [])
    if tasks:
        body_parts.extend(
            [
                "",
                "## Implementation Tasks",
                "",
            ]
        )
        for task in tasks:
            body_parts.append(f"- [ ] {task}")

    body_parts.extend(["", "---", "*Auto-generated from research branch by PopKit*"])

    return "\n".join(body_parts)


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: research_branch_detector.py <command>")
        print("Commands: detect, preview <branch>, parse <file>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "detect":
        print("Fetching remotes...")
        fetch_remotes()
        branches = get_research_branches()
        print(format_branch_table(branches))

    elif command == "preview" and len(sys.argv) > 2:
        branch_name = sys.argv[2]
        fetch_remotes()
        branches = get_research_branches()
        for b in branches:
            if branch_name in b.full_name or branch_name in b.short_name:
                print(f"Branch: {b.full_name}")
                print(f"Topic: {b.topic}")
                print(f"Created: {b.created_ago}")
                print(f"Files: {b.files_changed}")
                print("\nDoc previews:")
                previews = get_branch_content_preview(b)
                for path, content in previews.items():
                    print(f"\n--- {path} ---")
                    print(content)
                break
        else:
            print(f"Branch '{branch_name}' not found")

    elif command == "parse" and len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            content = f.read()
        result = parse_research_doc(content)
        print(json.dumps(result, indent=2))

    elif command == "content" and len(sys.argv) > 3:
        branch_ref = sys.argv[2]
        file_path = sys.argv[3]
        try:
            content = get_branch_content(branch_ref, file_path)
            print(content)
        except (FileNotFoundError, RuntimeError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
