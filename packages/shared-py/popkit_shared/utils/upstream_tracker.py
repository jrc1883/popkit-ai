#!/usr/bin/env python3
"""
Anthropic Upstream Tracking System
Tracks Claude Code, official plugins, and SDK updates with research state management.

A "dependabot for Claude Code" - prevents duplicate research and maintains context.

Features:
- Track releases and commits from Anthropic repositories
- Status lifecycle: pending_research → researched → synthesized
- Impact assessment (critical/high/medium/low/none/alignment)
- Link to PopKit issues/PRs
- Research velocity metrics

Part of Issue #215 - /popkit-core:upstream command
"""

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

# =============================================================================
# Constants
# =============================================================================

REPO_SPECS: Dict[str, Dict[str, Any]] = {
    "anthropics/claude-code": {
        "track_releases": True,
        "track_commits": True,
        "max_releases": 10,
        "max_commits": 15,
        "bootstrap_commits": 1,
    },
    "anthropics/claude-plugins-official": {
        "track_releases": False,
        "track_commits": True,
        "max_releases": 0,
        "max_commits": 20,
        "bootstrap_commits": 1,
    },
    "anthropics/anthropic-sdk-python": {
        "track_releases": True,
        "track_commits": False,
        "max_releases": 10,
        "max_commits": 0,
        "bootstrap_commits": 0,
    },
    "anthropics/anthropic-sdk-typescript": {
        "track_releases": True,
        "track_commits": False,
        "max_releases": 15,
        "max_commits": 0,
        "bootstrap_commits": 0,
        # Keep the signal focused on the primary TypeScript SDK track.
        "release_tag_prefixes": ["sdk-v"],
    },
}
MONITORED_REPOS = list(REPO_SPECS.keys())

STATUS_PENDING = "pending_research"
STATUS_RESEARCHED = "researched"
STATUS_SYNTHESIZED = "synthesized"
STATUS_ARCHIVED = "archived"
STATUS_ALIASES = {
    "pending": STATUS_PENDING,
    "pending_research": STATUS_PENDING,
    "research": STATUS_RESEARCHED,
    "researched": STATUS_RESEARCHED,
    "synthesized": STATUS_SYNTHESIZED,
    "synthesize": STATUS_SYNTHESIZED,
    "done": STATUS_SYNTHESIZED,
    "archived": STATUS_ARCHIVED,
}

IMPACT_CRITICAL = "critical"
IMPACT_HIGH = "high"
IMPACT_MEDIUM = "medium"
IMPACT_LOW = "low"
IMPACT_NONE = "none"
IMPACT_ALIGNMENT = "alignment"

CHECK_FREQUENCY_HOURS = 24

# =============================================================================
# Data Model Classes
# =============================================================================


class ChangelogItem:
    """Represents a single changelog item (release, commit, or plugin update)."""

    def __init__(
        self,
        id: str,
        type: str,
        title: str,
        url: str,
        published_date: str,
        discovered_date: str,
        status: str = STATUS_PENDING,
        research_summary: Optional[str] = None,
        research_date: Optional[str] = None,
        popkit_impact: Optional[str] = None,
        related_issues: Optional[List[str]] = None,
        related_prs: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ):
        self.id = id
        self.type = type
        self.title = title
        self.url = url
        self.published_date = published_date
        self.discovered_date = discovered_date
        self.status = status
        self.research_summary = research_summary
        self.research_date = research_date
        self.popkit_impact = popkit_impact
        self.related_issues = related_issues or []
        self.related_prs = related_prs or []
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "url": self.url,
            "published_date": self.published_date,
            "discovered_date": self.discovered_date,
            "status": self.status,
            "research_summary": self.research_summary,
            "research_date": self.research_date,
            "popkit_impact": self.popkit_impact,
            "related_issues": self.related_issues,
            "related_prs": self.related_prs,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ChangelogItem":
        """Create from dictionary."""
        return ChangelogItem(
            id=data["id"],
            type=data["type"],
            title=data["title"],
            url=data["url"],
            published_date=data["published_date"],
            discovered_date=data["discovered_date"],
            status=data.get("status", STATUS_PENDING),
            research_summary=data.get("research_summary"),
            research_date=data.get("research_date"),
            popkit_impact=data.get("popkit_impact"),
            related_issues=data.get("related_issues", []),
            related_prs=data.get("related_prs", []),
            notes=data.get("notes"),
        )


class RepositoryTracking:
    """Tracks a single Anthropic repository."""

    def __init__(
        self,
        repo: str,
        last_checked: Optional[str] = None,
        latest_release: Optional[str] = None,
        latest_commit: Optional[str] = None,
        changelog_items: Optional[List[ChangelogItem]] = None,
    ):
        self.repo = repo
        self.last_checked = last_checked
        self.latest_release = latest_release
        self.latest_commit = latest_commit
        self.changelog_items = changelog_items or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "last_checked": self.last_checked,
            "latest_release": self.latest_release,
            "latest_commit": self.latest_commit,
            "changelog_items": [item.to_dict() for item in self.changelog_items],
        }

    @staticmethod
    def from_dict(repo: str, data: Dict[str, Any]) -> "RepositoryTracking":
        """Create from dictionary."""
        return RepositoryTracking(
            repo=repo,
            last_checked=data.get("last_checked"),
            latest_release=data.get("latest_release"),
            latest_commit=data.get("latest_commit"),
            changelog_items=[
                ChangelogItem.from_dict(item) for item in data.get("changelog_items", [])
            ],
        )


# =============================================================================
# Upstream Tracker Main Class
# =============================================================================


class UpstreamTracker:
    """Main tracking interface for Anthropic repository updates."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize upstream tracker.

        Args:
            cache_dir: Cache directory (default: .claude/popkit)
        """
        if cache_dir is None:
            cache_dir = Path(".claude/popkit")

        self.cache_dir = Path(cache_dir)
        self.tracking_file = self.cache_dir / "upstream-tracking.json"
        self._tracking_data: Optional[Dict[str, Any]] = None

    def _load_tracking(self) -> Dict[str, Any]:
        """Load tracking data from disk.

        Returns:
            Tracking data dict or empty structure if not found
        """
        if self._tracking_data is not None:
            return self._tracking_data

        if not self.tracking_file.exists():
            return self._init_tracking()

        try:
            with open(self.tracking_file, "r", encoding="utf-8") as f:
                self._tracking_data = json.load(f)
                return self._tracking_data
        except (json.JSONDecodeError, IOError):
            # Corrupted tracking file, reinitialize
            return self._init_tracking()

    def _init_tracking(self) -> Dict[str, Any]:
        """Initialize empty tracking structure.

        Returns:
            Empty tracking dict with metadata
        """
        tracking = {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "repositories": {},
            "settings": {
                "check_frequency_hours": CHECK_FREQUENCY_HOURS,
                "auto_check_in_morning_routine": True,
                "notification_threshold": "all",
            },
            "statistics": {
                "total_items_tracked": 0,
                "pending_research": 0,
                "researched": 0,
                "synthesized": 0,
                "avg_research_time_days": 0.0,
            },
        }

        # Initialize empty repos
        for repo in MONITORED_REPOS:
            tracking["repositories"][repo] = {
                "last_checked": None,
                "latest_release": None,
                "latest_commit": None,
                "changelog_items": [],
            }

        self._tracking_data = tracking
        return tracking

    def _save_tracking(self) -> None:
        """Save tracking data to disk."""
        if self._tracking_data is None:
            return

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Update statistics before saving
        self._update_statistics()

        with open(self.tracking_file, "w", encoding="utf-8") as f:
            json.dump(self._tracking_data, f, indent=2)

    def _update_statistics(self) -> None:
        """Update statistics in tracking data."""
        if self._tracking_data is None:
            return

        tracking = self._tracking_data
        stats = tracking["statistics"]

        # Count items by status
        total = 0
        pending = 0
        researched = 0
        synthesized = 0

        research_times = []

        for repo_data in tracking["repositories"].values():
            for item_data in repo_data["changelog_items"]:
                total += 1
                status = item_data.get("status", STATUS_PENDING)

                if status == STATUS_PENDING:
                    pending += 1
                elif status == STATUS_RESEARCHED:
                    researched += 1
                elif status == STATUS_SYNTHESIZED:
                    synthesized += 1

                # Calculate research time
                if item_data.get("research_date") and item_data.get("discovered_date"):
                    try:
                        discovered = datetime.fromisoformat(item_data["discovered_date"])
                        researched_dt = datetime.fromisoformat(item_data["research_date"])
                        delta = researched_dt - discovered
                        research_times.append(delta.total_seconds() / (24 * 3600))  # days
                    except ValueError:
                        # Invalid date format - skip this item for research time calculation
                        # This is safe to ignore as it only affects statistics, not core functionality
                        continue

        stats["total_items_tracked"] = total
        stats["pending_research"] = pending
        stats["researched"] = researched
        stats["synthesized"] = synthesized

        if research_times:
            stats["avg_research_time_days"] = sum(research_times) / len(research_times)
        else:
            stats["avg_research_time_days"] = 0.0

    # =============================================================================
    # Public API Methods
    # =============================================================================

    @staticmethod
    def normalize_status(status: Optional[str]) -> Optional[str]:
        """Normalize status aliases to canonical values."""
        if status is None:
            return None
        return STATUS_ALIASES.get(status.strip().lower(), status.strip().lower())

    def check_updates(self, force: bool = False) -> Tuple[int, List[str]]:
        """Check all monitored repositories for new updates.

        Args:
            force: Force check even if recently checked

        Returns:
            Tuple of (new_items_count, repository_names_with_updates)
        """
        tracking = self._load_tracking()
        new_items_count = 0
        repos_with_updates = []

        for repo in MONITORED_REPOS:
            repo_tracking = RepositoryTracking.from_dict(repo, tracking["repositories"][repo])

            # Check if should skip (recently checked)
            if not force and repo_tracking.last_checked:
                try:
                    last_check = datetime.fromisoformat(repo_tracking.last_checked)
                    now_ref = (
                        datetime.now(last_check.tzinfo) if last_check.tzinfo else datetime.now()
                    )
                    if now_ref - last_check < timedelta(hours=CHECK_FREQUENCY_HOURS):
                        continue
                except ValueError:
                    # Invalid date format in last_checked - treat as never checked
                    # This is safe to ignore as we'll simply recheck the repo
                    pass

            # Fetch new items
            new_items = self._fetch_repo_updates(repo, repo_tracking)

            if new_items:
                new_items_count += len(new_items)
                repos_with_updates.append(repo)
                repo_tracking.changelog_items.extend(new_items)

            # Update last checked
            repo_tracking.last_checked = datetime.now().isoformat()

            # Save back to tracking
            tracking["repositories"][repo] = repo_tracking.to_dict()

        self._save_tracking()

        return (new_items_count, repos_with_updates)

    def _fetch_repo_updates(
        self, repo: str, repo_tracking: RepositoryTracking
    ) -> List[ChangelogItem]:
        """Fetch new updates for a repository.

        Args:
            repo: Repository name (owner/repo)
            repo_tracking: Current tracking state

        Returns:
            List of new ChangelogItem objects
        """
        new_items = []
        spec = REPO_SPECS.get(repo, {})
        existing_urls = {item.url for item in repo_tracking.changelog_items}

        if spec.get("track_releases", True):
            releases = self._fetch_releases(
                repo=repo,
                max_releases=spec.get("max_releases", 10),
                release_tag_prefixes=spec.get("release_tag_prefixes"),
            )
            for release in releases:
                if release["url"] in existing_urls:
                    continue

                item = ChangelogItem(
                    id=f"{repo.replace('/', '-')}-{release['tag_name']}",
                    type="release",
                    title=f"{repo.split('/')[-1]} {release['tag_name']}",
                    url=release["url"],
                    published_date=release["published_at"],
                    discovered_date=datetime.now().isoformat(),
                )
                new_items.append(item)
                existing_urls.add(release["url"])

            if releases:
                repo_tracking.latest_release = releases[0]["tag_name"]

        if spec.get("track_commits", False):
            commits = self._fetch_commits(
                repo=repo,
                since=repo_tracking.last_checked,
                max_commits=spec.get("max_commits", 20),
            )

            if commits:
                repo_tracking.latest_commit = commits[0]["sha"]

            if repo_tracking.last_checked is None:
                # Bootstrap without flooding initial backlogs.
                commits = commits[: spec.get("bootstrap_commits", 0)]

            for commit in commits:
                if commit["url"] in existing_urls:
                    continue

                item = ChangelogItem(
                    id=f"{repo.replace('/', '-')}-commit-{commit['sha'][:10]}",
                    type="commit",
                    title=commit["title"],
                    url=commit["url"],
                    published_date=commit["published_at"],
                    discovered_date=datetime.now().isoformat(),
                )
                new_items.append(item)
                existing_urls.add(commit["url"])

        return new_items

    def _fetch_releases(
        self,
        repo: str,
        max_releases: int = 10,
        release_tag_prefixes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch releases from GitHub API.

        Args:
            repo: Repository name (owner/repo)
            max_releases: Maximum number of releases to fetch
            release_tag_prefixes: Optional list of allowed tag prefixes

        Returns:
            List of release dicts
        """
        try:
            result = subprocess.run(
                ["gh", "api", f"/repos/{repo}/releases", "--jq", f".[0:{max_releases}]"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                releases = json.loads(result.stdout)
                # Filter to essential fields
                filtered = []
                for release in releases:
                    tag_name = release.get("tag_name", "")
                    if release_tag_prefixes and not any(
                        tag_name.startswith(prefix) for prefix in release_tag_prefixes
                    ):
                        continue

                    filtered.append(
                        {
                            "tag_name": tag_name,
                            "name": release.get("name", ""),
                            "published_at": release.get("published_at", ""),
                            "url": release.get("html_url", ""),
                            "body": release.get("body", ""),
                        }
                    )
                return filtered
            else:
                return []
        except Exception:
            return []

    def _fetch_commits(
        self,
        repo: str,
        since: Optional[str] = None,
        max_commits: int = 20,
    ) -> List[Dict[str, Any]]:
        """Fetch commits from GitHub API.

        Args:
            repo: Repository name (owner/repo)
            since: Optional ISO timestamp for incremental checks
            max_commits: Maximum number of commits to fetch

        Returns:
            List of commit dicts
        """
        endpoint = f"/repos/{repo}/commits?sha=main&per_page={max_commits}"
        normalized_since = self._format_since_for_github(since)
        if normalized_since:
            endpoint = f"{endpoint}&since={quote(normalized_since, safe='')}"

        try:
            result = subprocess.run(
                ["gh", "api", endpoint, "--jq", f".[0:{max_commits}]"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return []

            commits = json.loads(result.stdout)
            formatted: List[Dict[str, Any]] = []
            for commit in commits:
                sha = commit.get("sha", "")
                message = (commit.get("commit", {}).get("message") or "").strip()
                if not sha or not message:
                    continue

                title = message.splitlines()[0]
                published_at = (
                    commit.get("commit", {}).get("author", {}).get("date")
                    or commit.get("commit", {}).get("committer", {}).get("date")
                    or ""
                )
                url = commit.get("html_url", "")
                if not url:
                    continue

                formatted.append(
                    {
                        "sha": sha,
                        "title": f"{repo.split('/')[-1]} commit: {title}",
                        "published_at": published_at,
                        "url": url,
                    }
                )

            return formatted
        except Exception:
            return []

    @staticmethod
    def _format_since_for_github(since: Optional[str]) -> Optional[str]:
        """Convert local ISO timestamp to GitHub API-compatible UTC timestamp."""
        if not since:
            return None
        try:
            parsed = datetime.fromisoformat(since)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            else:
                parsed = parsed.astimezone(timezone.utc)
            return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")
        except ValueError:
            return None

    def list_items(
        self, status_filter: Optional[str] = None, repo_filter: Optional[str] = None
    ) -> List[ChangelogItem]:
        """List tracked changelog items.

        Args:
            status_filter: Filter by status (supports aliases like "pending")
            repo_filter: Filter by repository name

        Returns:
            List of ChangelogItem objects
        """
        tracking = self._load_tracking()
        items = []
        normalized_filter = self.normalize_status(status_filter)

        for repo, repo_data in tracking["repositories"].items():
            if repo_filter and repo != repo_filter:
                continue

            repo_tracking = RepositoryTracking.from_dict(repo, repo_data)

            for item in repo_tracking.changelog_items:
                if normalized_filter and item.status != normalized_filter:
                    continue

                items.append(item)

        # Sort by discovered date (newest first)
        items.sort(key=lambda x: x.discovered_date, reverse=True)

        return items

    def get_item(self, item_id: str) -> Optional[ChangelogItem]:
        """Get a specific changelog item by ID.

        Args:
            item_id: Item ID

        Returns:
            ChangelogItem or None if not found
        """
        tracking = self._load_tracking()

        for repo_data in tracking["repositories"].values():
            repo_tracking = RepositoryTracking.from_dict("", repo_data)

            for item in repo_tracking.changelog_items:
                if item.id == item_id:
                    return item

        return None

    def update_item(
        self,
        item_id: str,
        status: Optional[str] = None,
        research_summary: Optional[str] = None,
        popkit_impact: Optional[str] = None,
        related_issues: Optional[List[str]] = None,
        related_prs: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """Update a changelog item.

        Args:
            item_id: Item ID
            status: New status
            research_summary: Research summary
            popkit_impact: Impact assessment
            related_issues: Related issue numbers
            related_prs: Related PR numbers
            notes: Additional notes

        Returns:
            True if updated, False if not found
        """
        tracking = self._load_tracking()

        for repo, repo_data in tracking["repositories"].items():
            for item_data in repo_data["changelog_items"]:
                if item_data["id"] == item_id:
                    # Update fields
                    if status is not None:
                        item_data["status"] = self.normalize_status(status)

                        # Set research date when status changes to researched
                        if item_data["status"] == STATUS_RESEARCHED and not item_data.get(
                            "research_date"
                        ):
                            item_data["research_date"] = datetime.now().isoformat()

                    if research_summary is not None:
                        item_data["research_summary"] = research_summary

                    if popkit_impact is not None:
                        item_data["popkit_impact"] = popkit_impact

                    if related_issues is not None:
                        item_data["related_issues"] = related_issues

                    if related_prs is not None:
                        item_data["related_prs"] = related_prs

                    if notes is not None:
                        item_data["notes"] = notes

                    self._save_tracking()
                    return True

        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get tracking statistics.

        Returns:
            Statistics dict
        """
        tracking = self._load_tracking()
        return tracking["statistics"]


# =============================================================================
# CLI Test Interface
# =============================================================================


if __name__ == "__main__":
    import sys

    tracker = UpstreamTracker()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "check":
            print("Checking for upstream updates...")
            new_count, repos = tracker.check_updates(force=True)
            print(f"\nFound {new_count} new items")
            if repos:
                print(f"Repositories with updates: {', '.join(repos)}")

        elif cmd == "list":
            status = sys.argv[2] if len(sys.argv) > 2 else None
            print(f"Listing items (status: {status or 'all'})...\n")
            items = tracker.list_items(status_filter=status)

            for item in items:
                print(f"[{item.id}] {item.title}")
                print(f"  Status: {item.status}")
                print(f"  Discovered: {item.discovered_date}")
                print(f"  URL: {item.url}")
                if item.popkit_impact:
                    print(f"  Impact: {item.popkit_impact}")
                print()

        elif cmd == "stats":
            print("Upstream Tracking Statistics\n")
            stats = tracker.get_statistics()

            print(f"Total Items: {stats['total_items_tracked']}")
            print(f"  Pending Research: {stats['pending_research']}")
            print(f"  Researched: {stats['researched']}")
            print(f"  Synthesized: {stats['synthesized']}")
            print(f"\nAvg Research Time: {stats['avg_research_time_days']:.1f} days")

        else:
            print(f"Unknown command: {cmd}")
            print("\nUsage:")
            print("  python upstream_tracker.py check     # Check for updates")
            print("  python upstream_tracker.py list      # List all items")
            print("  python upstream_tracker.py list pending  # List pending items")
            print("  python upstream_tracker.py stats     # Show statistics")
    else:
        print("Upstream Tracker Test")
        print("\nUsage:")
        print("  python upstream_tracker.py check     # Check for updates")
        print("  python upstream_tracker.py list      # List all items")
        print("  python upstream_tracker.py list pending  # List pending items")
        print("  python upstream_tracker.py stats     # Show statistics")
