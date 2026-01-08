#!/usr/bin/env python3
"""
Enhanced Changelog Generator with Semantic Versioning
Generates CHANGELOG.md and GitHub release notes from conventional commits.

Features:
- Automatic semantic version bump detection (MAJOR.MINOR.PATCH)
- Categorized commits with emoji icons
- Breaking change detection and highlighting
- GitHub release notes generation
- Integration with git workflow

Part of PopKit plugin - Quick Win from Issue #27 (Auto Claude Competitive Features)

Usage:
    python changelog_generator.py                    # Generate for next version
    python changelog_generator.py --version 1.1.0   # Specify version
    python changelog_generator.py --since v1.0.0    # From specific tag
    python changelog_generator.py --json            # Output as JSON
    python changelog_generator.py --preview         # Preview without updating
    python changelog_generator.py --release         # Generate GitHub release notes
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict


# Conventional commit type to display name mapping with emojis
COMMIT_TYPES = {
    "feat": "✨ Features",
    "fix": "🐛 Bug Fixes",
    "breaking": "💥 BREAKING CHANGES",
    "docs": "📚 Documentation",
    "style": "💄 Style",
    "refactor": "♻️ Code Refactoring",
    "perf": "⚡ Performance",
    "test": "✅ Tests",
    "build": "📦 Build System",
    "ci": "👷 CI/CD",
    "chore": "🔧 Chores",
    "revert": "⏪ Reverts"
}

# Priority order for changelog sections
TYPE_PRIORITY = ["breaking", "feat", "fix", "perf", "refactor", "docs", "test", "ci", "build", "chore", "style", "revert"]

# Semantic versioning bump rules
VERSION_BUMP_RULES = {
    "major": ["breaking"],  # BREAKING CHANGE
    "minor": ["feat"],       # New features
    "patch": ["fix", "perf", "refactor", "docs", "test", "build", "ci", "chore", "style", "revert"]
}


class ChangelogGenerator:
    """Generates changelog entries from git commits."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()

    def run_git(self, args: List[str]) -> str:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                encoding="utf-8"
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def get_latest_tag(self) -> Optional[str]:
        """Get the most recent version tag."""
        # Try to get tags that look like versions
        tags = self.run_git(["tag", "-l", "v*", "--sort=-v:refname"])
        if tags:
            return tags.split("\n")[0]
        return None

    def get_commits_since(self, since_ref: str = None) -> List[Dict[str, Any]]:
        """Get commits since a reference (tag or commit)."""
        if since_ref:
            range_spec = f"{since_ref}..HEAD"
        else:
            # Get all commits if no tag exists
            range_spec = "HEAD"

        # Format: hash|subject|body
        log_output = self.run_git([
            "log", range_spec,
            "--pretty=format:%H|%s|%b|||COMMIT_END|||"
        ])

        if not log_output:
            return []

        commits = []
        for entry in log_output.split("|||COMMIT_END|||"):
            entry = entry.strip()
            if not entry:
                continue

            parts = entry.split("|", 2)
            if len(parts) < 2:
                continue

            commit_hash = parts[0][:7]
            subject = parts[1]
            body = parts[2] if len(parts) > 2 else ""

            parsed = self.parse_commit(subject, body)
            if parsed:
                parsed["hash"] = commit_hash
                commits.append(parsed)

        return commits

    def parse_commit(self, subject: str, body: str = "") -> Optional[Dict[str, Any]]:
        """Parse a conventional commit message."""
        # Check for breaking change first
        is_breaking = "BREAKING CHANGE" in body or "BREAKING CHANGE:" in subject.upper()

        # Pattern: type(scope): description
        # or: type: description
        pattern = r'^(\w+)(?:\(([^)]+)\))?:\s*(.+)$'
        match = re.match(pattern, subject)

        if not match:
            # Non-conventional commit
            return {
                "type": "breaking" if is_breaking else "other",
                "scope": None,
                "description": subject,
                "body": body,
                "issues": self.extract_issues(subject + " " + body),
                "breaking": is_breaking
            }

        commit_type = match.group(1).lower()
        scope = match.group(2)
        description = match.group(3)

        # Override type if breaking change
        if is_breaking:
            commit_type = "breaking"

        return {
            "type": commit_type,
            "scope": scope,
            "description": description,
            "body": body,
            "issues": self.extract_issues(subject + " " + body),
            "breaking": is_breaking
        }

    def extract_issues(self, text: str) -> List[int]:
        """Extract issue/PR numbers from text."""
        # Match #N patterns
        pattern = r'#(\d+)'
        matches = re.findall(pattern, text)
        return sorted(set(int(m) for m in matches))

    def group_commits(self, commits: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group commits by type."""
        groups = defaultdict(list)
        for commit in commits:
            groups[commit["type"]].append(commit)
        return dict(groups)

    def determine_version_bump(self, commits: List[Dict[str, Any]]) -> str:
        """
        Determine semantic version bump based on commit types.

        Rules:
        - BREAKING CHANGE → MAJOR (1.0.0 → 2.0.0)
        - feat → MINOR (1.0.0 → 1.1.0)
        - fix/perf/refactor/etc → PATCH (1.0.0 → 1.0.1)

        Returns:
            "major", "minor", or "patch"
        """
        commit_types = [c["type"] for c in commits]

        # Check for major bump (breaking changes)
        if any(t in VERSION_BUMP_RULES["major"] for t in commit_types):
            return "major"

        # Check for minor bump (new features)
        if any(t in VERSION_BUMP_RULES["minor"] for t in commit_types):
            return "minor"

        # Default to patch
        return "patch"

    def bump_version(self, current_version: str, bump_type: str) -> str:
        """
        Bump a semantic version.

        Args:
            current_version: Current version (e.g., "1.2.3" or "v1.2.3")
            bump_type: "major", "minor", or "patch"

        Returns:
            New version string (without 'v' prefix)
        """
        # Remove 'v' prefix if present
        version = current_version.lstrip('v')

        # Parse version
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version)
        if not match:
            return "1.0.0"

        major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))

        if bump_type == "major":
            return f"{major + 1}.0.0"
        elif bump_type == "minor":
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"

    def generate_markdown(
        self,
        version: str,
        title: str = None,
        since_ref: str = None,
        for_changelog: bool = True
    ) -> str:
        """
        Generate CHANGELOG.md entry.

        Args:
            version: Version number
            title: Optional release title
            since_ref: Generate since this tag/ref
            for_changelog: If True, format for CHANGELOG.md; if False, for CLAUDE.md

        Returns:
            Formatted changelog entry
        """
        commits = self.get_commits_since(since_ref)
        if not commits:
            return f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\nNo changes since last release.\n"

        grouped = self.group_commits(commits)

        # Collect all issue numbers
        all_issues = set()
        for commit_list in grouped.values():
            for commit in commit_list:
                all_issues.update(commit["issues"])

        # Build the changelog
        lines = []

        # Header
        if for_changelog:
            lines.append(f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}")
        else:
            if title:
                lines.append(f"### v{version} (Current) - {title}")
            else:
                lines.append(f"### v{version} (Current)")
        lines.append("")

        # Generate sections in priority order
        for commit_type in TYPE_PRIORITY:
            if commit_type not in grouped:
                continue

            type_commits = grouped[commit_type]
            if not type_commits:
                continue

            # Section header
            section_name = COMMIT_TYPES.get(commit_type, commit_type.title())
            lines.append(f"### {section_name}")
            lines.append("")

            # Commits in this section
            for commit in type_commits:
                scope = commit.get("scope")
                desc = commit["description"]
                issues = commit["issues"]
                body = commit.get("body", "")

                # Format: - **scope**: description (#123)
                if scope:
                    line = f"- **{scope}**: {desc}"
                else:
                    line = f"- {desc}"

                if issues:
                    issue_refs = ", ".join(f"#{i}" for i in issues)
                    line += f" ({issue_refs})"

                lines.append(line)

                # For breaking changes, add migration note if present
                if commit_type == "breaking" and body:
                    # Extract migration info from body
                    migration_lines = [l.strip() for l in body.split("\n") if l.strip()]
                    for mline in migration_lines[:3]:  # Max 3 lines
                        lines.append(f"  - {mline}")

            lines.append("")

        return "\n".join(lines)

    def generate_github_release_notes(
        self,
        version: str,
        title: str = None,
        since_ref: str = None
    ) -> str:
        """
        Generate GitHub release notes.

        Returns:
            Formatted release notes suitable for GitHub releases
        """
        commits = self.get_commits_since(since_ref)
        if not commits:
            return f"# {version}\n\nNo changes since last release."

        grouped = self.group_commits(commits)

        # Collect statistics
        all_issues = set()
        for commit_list in grouped.values():
            for commit in commit_list:
                all_issues.update(commit["issues"])

        # Count commits by type
        feat_count = len(grouped.get("feat", []))
        fix_count = len(grouped.get("fix", []))
        breaking_count = len(grouped.get("breaking", []))

        # Build release notes
        lines = []

        # Title
        if title:
            lines.append(f"# PopKit {version} - {title}")
        else:
            lines.append(f"# PopKit {version}")
        lines.append("")

        # Summary
        lines.append("## 🎉 What's New")
        lines.append("")

        if breaking_count > 0:
            lines.append(f"⚠️ **This release contains {breaking_count} breaking change(s)** - please review the Breaking Changes section below.")
            lines.append("")

        # Highlights (features)
        if "feat" in grouped:
            for commit in grouped["feat"][:5]:  # Top 5 features
                scope = commit.get("scope", "")
                desc = commit["description"]
                issues = commit["issues"]

                if scope:
                    lines.append(f"### {scope.replace('-', ' ').title()}")
                else:
                    lines.append(f"### {desc.split()[0].title()}")

                lines.append(f"{desc}")
                if issues:
                    issue_refs = ", ".join(f"#{i}" for i in issues)
                    lines.append(f"({issue_refs})")
                lines.append("")

        # Breaking changes
        if "breaking" in grouped:
            lines.append("## 💥 Breaking Changes")
            lines.append("")
            for commit in grouped["breaking"]:
                desc = commit["description"]
                body = commit.get("body", "")
                lines.append(f"### {desc}")
                lines.append("")
                if body:
                    lines.append("**Migration:**")
                    migration_lines = [l.strip() for l in body.split("\n") if l.strip()]
                    for mline in migration_lines:
                        lines.append(f"- {mline}")
                    lines.append("")

        # Bug fixes
        if "fix" in grouped:
            lines.append("## 🐛 Bug Fixes")
            lines.append("")
            for commit in grouped["fix"]:
                desc = commit["description"]
                issues = commit["issues"]
                if issues:
                    issue_refs = ", ".join(f"#{i}" for i in issues)
                    lines.append(f"- {desc} ({issue_refs})")
                else:
                    lines.append(f"- {desc}")
            lines.append("")

        # Statistics
        lines.append("## 📊 Statistics")
        lines.append("")
        lines.append(f"- **Features Added:** {feat_count}")
        lines.append(f"- **Bug Fixes:** {fix_count}")
        lines.append(f"- **Total Commits:** {len(commits)}")
        if all_issues:
            lines.append(f"- **Issues Closed:** {len(all_issues)}")
        lines.append("")

        # Links
        lines.append("## 🔗 Links")
        lines.append("")
        lines.append(f"- **Full Changelog:** [CHANGELOG.md](CHANGELOG.md#{version.replace('.', '')}---{datetime.now().strftime('%Y-%m-%d')})")
        if all_issues:
            sorted_issues = sorted(all_issues)
            issue_list = ", ".join(f"#{i}" for i in sorted_issues)
            lines.append(f"- **Issues Closed:** {issue_list}")
        lines.append("")

        # Installation
        lines.append("---")
        lines.append("")
        lines.append("**Install:** `/plugin install popkit-suite@popkit-claude`")
        lines.append("")
        lines.append("**Upgrade:** `/plugin update popkit-suite`")

        return "\n".join(lines)

    def format_issue_ranges(self, issues: List[int]) -> str:
        """Format issue numbers, using ranges where consecutive."""
        if not issues:
            return ""

        ranges = []
        start = issues[0]
        end = issues[0]

        for i in issues[1:]:
            if i == end + 1:
                end = i
            else:
                if start == end:
                    ranges.append(f"#{start}")
                else:
                    ranges.append(f"#{start}-{end}")
                start = i
                end = i

        # Add last range
        if start == end:
            ranges.append(f"#{start}")
        else:
            ranges.append(f"#{start}-{end}")

        return ", ".join(ranges)

    def update_changelog(self, version: str, title: str = None, since_ref: str = None) -> bool:
        """Update CHANGELOG.md with new version entry."""
        changelog = self.project_root / "CHANGELOG.md"

        # Generate new entry
        new_entry = self.generate_markdown(version, title, since_ref, for_changelog=True)

        if not changelog.exists():
            # Create new CHANGELOG.md
            content = f"""# Changelog

All notable changes to PopKit are documented in this file.

**Versioning:** PopKit uses semantic versioning. Currently in preview (0.x) until stable public launch.

## [Unreleased]

_No unreleased changes yet._

---

{new_entry}
"""
            try:
                changelog.write_text(content, encoding="utf-8")
                return True
            except IOError:
                return False
        else:
            # Update existing CHANGELOG.md
            try:
                content = changelog.read_text(encoding="utf-8")
            except IOError:
                return False

            # Find where to insert (after [Unreleased] section and ---)
            pattern = r'(## \[Unreleased\].*?---\s*\n+)'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                # Insert after the --- separator
                insert_pos = match.end()
                updated = content[:insert_pos] + new_entry + "\n" + content[insert_pos:]

                try:
                    changelog.write_text(updated, encoding="utf-8")
                    return True
                except IOError:
                    return False
            else:
                # Fallback: insert after first line
                lines = content.split("\n", 1)
                if len(lines) > 1:
                    updated = lines[0] + "\n\n" + new_entry + "\n" + lines[1]
                    try:
                        changelog.write_text(updated, encoding="utf-8")
                        return True
                    except IOError:
                        return False

        return False

    def update_claude_md(self, version: str, title: str = None, since_ref: str = None) -> bool:
        """Update CLAUDE.md with new version entry."""
        claude_md = self.project_root / "CLAUDE.md"
        if not claude_md.exists():
            return False

        try:
            content = claude_md.read_text(encoding="utf-8")
        except IOError:
            return False

        # Generate new entry (old format for CLAUDE.md)
        new_entry = self.generate_markdown(version, title, since_ref, for_changelog=False)

        # Find where to insert (after "## Version History" header and note)
        # Look for the first ### entry
        pattern = r'(## Version History\s+\*\*Note:\*\*[^\n]+\n+)'
        match = re.search(pattern, content)

        if match:
            # Insert after the header and note
            insert_pos = match.end()
            updated = content[:insert_pos] + new_entry + "\n" + content[insert_pos:]

            # Update the "(Current)" marker on old versions
            # Remove (Current) from previous version
            updated = re.sub(r'### v[\d.]+ \(Current\)', lambda m: m.group(0).replace(" (Current)", ""), updated, count=1)

            try:
                claude_md.write_text(updated, encoding="utf-8")
                return True
            except IOError:
                return False

        return False

    def save_release_notes(self, version: str, title: str = None, since_ref: str = None, output_file: str = None) -> bool:
        """Save GitHub release notes to a file."""
        if output_file is None:
            output_file = f"release-notes-{version}.md"

        release_notes = self.generate_github_release_notes(version, title, since_ref)

        output_path = self.project_root / output_file
        try:
            output_path.write_text(release_notes, encoding="utf-8")
            return True
        except IOError:
            return False

    def to_json(self, version: str = None, since_ref: str = None) -> str:
        """Output changelog data as JSON."""
        commits = self.get_commits_since(since_ref)
        grouped = self.group_commits(commits)

        all_issues = set()
        for commit_list in grouped.values():
            for commit in commit_list:
                all_issues.update(commit["issues"])

        # Determine version bump
        bump_type = self.determine_version_bump(commits)

        # Get current version and calculate next version
        current_tag = since_ref or self.get_latest_tag() or "v0.0.0"
        suggested_version = self.bump_version(current_tag, bump_type)

        return json.dumps({
            "version": version or suggested_version,
            "since_ref": since_ref,
            "commits": commits,
            "grouped": grouped,
            "issues_closed": sorted(all_issues),
            "commit_count": len(commits),
            "version_bump": bump_type,
            "suggested_version": suggested_version
        }, indent=2)


def main():
    """CLI entry point."""
    import argparse
    import io

    # Handle Windows encoding
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description="Enhanced changelog generator with semantic versioning")
    parser.add_argument("--version", "-v", help="Version number (e.g., 1.1.0). If not provided, auto-determined from commits")
    parser.add_argument("--title", "-t", help="Release title")
    parser.add_argument("--since", "-s", help="Generate since this tag/ref")
    parser.add_argument("--json", action="store_true", help="Output as JSON with version bump analysis")
    parser.add_argument("--preview", "-p", action="store_true", help="Preview without updating files")
    parser.add_argument("--update", "-u", action="store_true", help="Update CHANGELOG.md")
    parser.add_argument("--release", "-r", action="store_true", help="Generate GitHub release notes")
    parser.add_argument("--auto", "-a", action="store_true", help="Auto-determine version bump from commits")
    args = parser.parse_args()

    generator = ChangelogGenerator()

    # Get since ref (default to latest tag)
    since_ref = args.since
    if not since_ref:
        since_ref = generator.get_latest_tag()

    # Get version
    version = args.version
    if not version or args.auto:
        # Auto-determine version from commits
        commits = generator.get_commits_since(since_ref)
        if commits:
            bump_type = generator.determine_version_bump(commits)
            current_tag = since_ref or "v0.0.0"
            version = generator.bump_version(current_tag, bump_type)
            if args.auto:
                print(f"Auto-determined version bump: {bump_type.upper()}")
                print(f"Next version: {version}")
                print()
        else:
            version = "0.0.1"

    if args.json:
        print(generator.to_json(version, since_ref))
    elif args.release:
        # Generate GitHub release notes
        release_notes = generator.generate_github_release_notes(version, args.title, since_ref)
        print(release_notes)
        if not args.preview:
            # Save to file
            success = generator.save_release_notes(version, args.title, since_ref)
            if success:
                print(f"\n✅ Release notes saved to release-notes-{version}.md", file=sys.stderr)
    elif args.update:
        success = generator.update_changelog(version, args.title, since_ref)
        if success:
            print(f"✅ Updated CHANGELOG.md with v{version}")
        else:
            print("❌ Failed to update CHANGELOG.md", file=sys.stderr)
            sys.exit(1)
    else:
        # Preview mode (default)
        print(f"Changelog for v{version} (since {since_ref or 'beginning'}):")
        print("=" * 50)
        print(generator.generate_markdown(version, args.title, since_ref))


if __name__ == "__main__":
    main()
