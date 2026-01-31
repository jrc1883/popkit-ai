#!/usr/bin/env python3
"""
GitHub Metadata Cache
Caches GitHub repository metadata (labels, milestones, team members) to avoid
repeated API calls and prevent errors from using invalid values.

Features:
- Two-tier caching: Local JSON (free) or Upstash Redis (pro)
- Automatic TTL expiration
- "Check First" pattern validation
- Minimal API usage

Part of the popkit plugin system - Issue #96
"""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

# =============================================================================
# Cache Configuration
# =============================================================================

DEFAULT_TTL_MINUTES = 60  # 1 hour for most metadata
TEAM_TTL_MINUTES = 1440  # 24 hours for team members (changes infrequently)
MAX_CACHE_AGE_DAYS = 7  # Maximum cache age before forced refresh


# =============================================================================
# Local JSON Cache (Free Tier)
# =============================================================================


class LocalGitHubCache:
    """Local JSON-based cache for GitHub metadata.

    Stores cache in .claude/popkit/github-cache.json (gitignored).
    Suitable for single-session use and free tier.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize local cache.

        Args:
            cache_dir: Cache directory (default: .claude/popkit)
        """
        if cache_dir is None:
            cache_dir = Path(".claude/popkit")

        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / "github-cache.json"
        self._cache_data: Optional[Dict[str, Any]] = None

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from disk.

        Returns:
            Cache data dict or empty dict if not found
        """
        if self._cache_data is not None:
            return self._cache_data

        if not self.cache_file.exists():
            return self._init_cache()

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self._cache_data = json.load(f)
                return self._cache_data
        except (json.JSONDecodeError, IOError):
            # Corrupted cache, reinitialize
            return self._init_cache()

    def _init_cache(self) -> Dict[str, Any]:
        """Initialize empty cache structure.

        Returns:
            Empty cache dict with metadata
        """
        repo = self._get_current_repo()
        cache = {
            "repository": repo,
            "cache_version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "labels": None,
            "labels_updated": None,
            "labels_ttl_minutes": DEFAULT_TTL_MINUTES,
            "milestones": None,
            "milestones_updated": None,
            "milestones_ttl_minutes": DEFAULT_TTL_MINUTES,
            "team_members": None,
            "team_updated": None,
            "team_ttl_minutes": TEAM_TTL_MINUTES,
            "default_branch": None,
            "default_branch_updated": None,
        }
        self._cache_data = cache
        return cache

    def _save_cache(self) -> None:
        """Save cache to disk."""
        if self._cache_data is None:
            return

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self._cache_data, f, indent=2)

    def _get_current_repo(self) -> str:
        """Get current repository name from git remote.

        Returns:
            Repository name in format "owner/repo" or "unknown"
        """
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                url = result.stdout.strip()
                # Parse GitHub URL: https://github.com/owner/repo.git
                # or git@github.com:owner/repo.git

                # Handle SSH format (git@github.com:owner/repo.git)
                if url.startswith("git@"):
                    # Extract the part after git@
                    if "github.com:" in url:
                        path = url.split("github.com:")[-1]
                        parts = path.rstrip(".git").split("/")
                        if len(parts) == 2:
                            return f"{parts[0]}/{parts[1]}"
                else:
                    # Handle HTTPS format (https://github.com/owner/repo.git)
                    parsed = urlparse(url)
                    # Security: Verify the hostname is exactly github.com
                    if parsed.netloc == "github.com":
                        path = parsed.path.strip("/").rstrip(".git")
                        parts = path.split("/")
                        if len(parts) == 2:
                            return f"{parts[0]}/{parts[1]}"

            return "unknown"
        except Exception:
            return "unknown"

    def _is_expired(self, updated_at: Optional[str], ttl_minutes: int) -> bool:
        """Check if cache entry is expired.

        Args:
            updated_at: ISO timestamp of last update
            ttl_minutes: TTL in minutes

        Returns:
            True if expired or never set, False otherwise
        """
        if updated_at is None:
            return True

        try:
            updated = datetime.fromisoformat(updated_at)
            expiry = updated + timedelta(minutes=ttl_minutes)
            return datetime.now() > expiry
        except ValueError:
            return True

    def get_labels(self, force_refresh: bool = False) -> Optional[List[Dict[str, str]]]:
        """Get cached labels or None if expired.

        Args:
            force_refresh: Force API fetch even if cached

        Returns:
            List of label dicts with name, description, color
        """
        cache = self._load_cache()

        if force_refresh:
            return None

        if self._is_expired(
            cache.get("labels_updated"), cache.get("labels_ttl_minutes", DEFAULT_TTL_MINUTES)
        ):
            return None

        return cache.get("labels")

    def set_labels(self, labels: List[Dict[str, str]], ttl_minutes: Optional[int] = None) -> None:
        """Set cached labels.

        Args:
            labels: List of label dicts
            ttl_minutes: TTL override (default: DEFAULT_TTL_MINUTES)
        """
        cache = self._load_cache()
        cache["labels"] = labels
        cache["labels_updated"] = datetime.now().isoformat()
        if ttl_minutes is not None:
            cache["labels_ttl_minutes"] = ttl_minutes
        self._save_cache()

    def get_milestones(self, force_refresh: bool = False) -> Optional[List[Dict[str, Any]]]:
        """Get cached milestones or None if expired.

        Args:
            force_refresh: Force API fetch even if cached

        Returns:
            List of milestone dicts with title, number, state
        """
        cache = self._load_cache()

        if force_refresh:
            return None

        if self._is_expired(
            cache.get("milestones_updated"),
            cache.get("milestones_ttl_minutes", DEFAULT_TTL_MINUTES),
        ):
            return None

        return cache.get("milestones")

    def set_milestones(
        self, milestones: List[Dict[str, Any]], ttl_minutes: Optional[int] = None
    ) -> None:
        """Set cached milestones.

        Args:
            milestones: List of milestone dicts
            ttl_minutes: TTL override (default: DEFAULT_TTL_MINUTES)
        """
        cache = self._load_cache()
        cache["milestones"] = milestones
        cache["milestones_updated"] = datetime.now().isoformat()
        if ttl_minutes is not None:
            cache["milestones_ttl_minutes"] = ttl_minutes
        self._save_cache()

    def get_team_members(self, force_refresh: bool = False) -> Optional[List[str]]:
        """Get cached team members or None if expired.

        Args:
            force_refresh: Force API fetch even if cached

        Returns:
            List of GitHub usernames
        """
        cache = self._load_cache()

        if force_refresh:
            return None

        if self._is_expired(
            cache.get("team_updated"), cache.get("team_ttl_minutes", TEAM_TTL_MINUTES)
        ):
            return None

        return cache.get("team_members")

    def set_team_members(self, team: List[str], ttl_minutes: Optional[int] = None) -> None:
        """Set cached team members.

        Args:
            team: List of GitHub usernames
            ttl_minutes: TTL override (default: TEAM_TTL_MINUTES)
        """
        cache = self._load_cache()
        cache["team_members"] = team
        cache["team_updated"] = datetime.now().isoformat()
        if ttl_minutes is not None:
            cache["team_ttl_minutes"] = ttl_minutes
        self._save_cache()

    def get_default_branch(self, force_refresh: bool = False) -> Optional[str]:
        """Get cached default branch or None if expired.

        Args:
            force_refresh: Force API fetch even if cached

        Returns:
            Default branch name (e.g., "main", "master")
        """
        cache = self._load_cache()

        if force_refresh:
            return None

        # Default branch changes rarely, use labels TTL
        if self._is_expired(
            cache.get("default_branch_updated"),
            cache.get("labels_ttl_minutes", DEFAULT_TTL_MINUTES),
        ):
            return None

        return cache.get("default_branch")

    def set_default_branch(self, branch: str) -> None:
        """Set cached default branch.

        Args:
            branch: Default branch name
        """
        cache = self._load_cache()
        cache["default_branch"] = branch
        cache["default_branch_updated"] = datetime.now().isoformat()
        self._save_cache()

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache_data = self._init_cache()
        self._save_cache()


# =============================================================================
# Redis Cache (Pro Tier) - Future Enhancement
# =============================================================================


class RedisGitHubCache:
    """Upstash Redis-based cache for GitHub metadata.

    Shared across sessions and machines.
    Suitable for team environments and pro tier.

    Note: Not yet implemented - placeholder for future enhancement.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis cache.

        Args:
            redis_url: Upstash Redis URL (default: from env)
        """
        raise NotImplementedError("Redis cache not yet implemented. Use LocalGitHubCache for now.")


# =============================================================================
# GitHub CLI Detection
# =============================================================================


def is_gh_cli_available() -> bool:
    """Check if GitHub CLI is installed and authenticated.

    Returns:
        True if gh CLI is available and authenticated, False otherwise
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def ensure_gh_cli() -> None:
    """Display helpful error message if GitHub CLI is not available.

    Raises:
        RuntimeError: If GitHub CLI is not available
    """
    if is_gh_cli_available():
        return

    import platform

    error_msg = [
        "",
        "GitHub CLI (gh) not found or not authenticated",
        "",
        "PopKit requires GitHub CLI for GitHub operations.",
        "",
        "Installation:",
    ]

    # Platform-specific installation instructions
    system = platform.system()
    if system == "Darwin":  # macOS
        error_msg.append("  • macOS: brew install gh")
    elif system == "Windows":
        error_msg.append("  • Windows: winget install --id GitHub.cli")
    elif system == "Linux":
        error_msg.append("  • Linux: See https://cli.github.com/")
    else:
        error_msg.append("  • See https://cli.github.com/")

    error_msg.extend(["", "After installation, run: gh auth login", ""])

    raise RuntimeError("\n".join(error_msg))


# =============================================================================
# GitHub API Fetchers
# =============================================================================


def fetch_labels_from_github() -> List[Dict[str, str]]:
    """Fetch labels from GitHub API using gh CLI.

    Returns:
        List of label dicts with name, description, color
    """
    try:
        result = subprocess.run(
            ["gh", "label", "list", "--json", "name,description,color"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return []
    except Exception:
        return []


def fetch_milestones_from_github(state: str = "open") -> List[Dict[str, Any]]:
    """Fetch milestones from GitHub API using gh CLI.

    Args:
        state: Milestone state filter ("open", "closed", "all")

    Returns:
        List of milestone dicts with title, number, state, description
    """
    try:
        result = subprocess.run(
            ["gh", "api", f"/repos/{{owner}}/{{repo}}/milestones?state={state}"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            milestones = json.loads(result.stdout)
            # Simplify to essential fields
            return [
                {
                    "title": m.get("title"),
                    "number": m.get("number"),
                    "state": m.get("state"),
                    "description": m.get("description"),
                }
                for m in milestones
            ]
        else:
            return []
    except Exception:
        return []


def fetch_default_branch_from_github() -> str:
    """Fetch default branch from GitHub API using gh CLI.

    Returns:
        Default branch name or "main" as fallback
    """
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "main"
    except Exception:
        return "main"


# =============================================================================
# High-Level Cache Interface
# =============================================================================


class GitHubCache:
    """Unified GitHub cache interface.

    Automatically selects between local JSON cache (free) and Redis cache (pro)
    based on environment configuration.

    Usage:
        cache = GitHubCache()

        # Labels
        labels = cache.get_labels()
        if labels is None:
            labels = fetch_labels_from_github()
            cache.set_labels(labels)

        # Milestones
        milestones = cache.get_milestones()
        if milestones is None:
            milestones = fetch_milestones_from_github()
            cache.set_milestones(milestones)
    """

    def __init__(self, use_redis: bool = False):
        """Initialize cache.

        Args:
            use_redis: Use Redis cache instead of local JSON (not yet implemented)
        """
        if use_redis:
            # Future: Check for UPSTASH_REDIS_URL env var
            self._backend = RedisGitHubCache()
        else:
            self._backend = LocalGitHubCache()

    def get_labels(self, force_refresh: bool = False) -> Optional[List[Dict[str, str]]]:
        """Get labels from cache or fetch from GitHub."""
        cached = self._backend.get_labels(force_refresh=force_refresh)
        if cached is not None:
            return cached

        # Fetch from GitHub - requires gh CLI
        ensure_gh_cli()
        labels = fetch_labels_from_github()
        if labels:
            self._backend.set_labels(labels)
        return labels

    def get_milestones(
        self, state: str = "open", force_refresh: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """Get milestones from cache or fetch from GitHub."""
        cached = self._backend.get_milestones(force_refresh=force_refresh)
        if cached is not None:
            return cached

        # Fetch from GitHub - requires gh CLI
        ensure_gh_cli()
        milestones = fetch_milestones_from_github(state=state)
        if milestones:
            self._backend.set_milestones(milestones)
        return milestones

    def get_default_branch(self, force_refresh: bool = False) -> str:
        """Get default branch from cache or fetch from GitHub."""
        cached = self._backend.get_default_branch(force_refresh=force_refresh)
        if cached is not None:
            return cached

        # Fetch from GitHub - requires gh CLI
        ensure_gh_cli()
        branch = fetch_default_branch_from_github()
        if branch:
            self._backend.set_default_branch(branch)
        return branch

    def clear(self) -> None:
        """Clear all cached data."""
        self._backend.clear()


# =============================================================================
# CLI Test Interface
# =============================================================================


if __name__ == "__main__":
    import sys

    cache = GitHubCache()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "labels":
            print("Fetching labels (cached if available)...")
            labels = cache.get_labels()
            print(json.dumps(labels, indent=2))

        elif cmd == "milestones":
            print("Fetching milestones (cached if available)...")
            milestones = cache.get_milestones()
            print(json.dumps(milestones, indent=2))

        elif cmd == "branch":
            print("Fetching default branch (cached if available)...")
            branch = cache.get_default_branch()
            print(f"Default branch: {branch}")

        elif cmd == "status":
            print("GitHub Cache Status\n")
            backend = cache._backend
            cache_data = backend._load_cache()

            print(f"Repository: {cache_data.get('repository', 'unknown')}")
            print(f"Cache Version: {cache_data.get('cache_version', '1.0.0')}")
            print(f"Created: {cache_data.get('created_at', 'unknown')}\n")

            # Labels status
            labels_updated = cache_data.get("labels_updated")
            labels_count = len(cache_data.get("labels", [])) if cache_data.get("labels") else 0
            labels_ttl = cache_data.get("labels_ttl_minutes", DEFAULT_TTL_MINUTES)
            labels_expired = backend._is_expired(labels_updated, labels_ttl)

            print("Labels:")
            print(f"  Count: {labels_count}")
            print(f"  Last Updated: {labels_updated or 'Never'}")
            print(f"  TTL: {labels_ttl} minutes")
            print(f"  Status: {'Expired' if labels_expired else 'Fresh'}\n")

            # Milestones status
            milestones_updated = cache_data.get("milestones_updated")
            milestones_count = (
                len(cache_data.get("milestones", [])) if cache_data.get("milestones") else 0
            )
            milestones_ttl = cache_data.get("milestones_ttl_minutes", DEFAULT_TTL_MINUTES)
            milestones_expired = backend._is_expired(milestones_updated, milestones_ttl)

            print("Milestones:")
            print(f"  Count: {milestones_count}")
            print(f"  Last Updated: {milestones_updated or 'Never'}")
            print(f"  TTL: {milestones_ttl} minutes")
            print(f"  Status: {'Expired' if milestones_expired else 'Fresh'}\n")

            # Team members status
            team_updated = cache_data.get("team_updated")
            team_count = (
                len(cache_data.get("team_members", [])) if cache_data.get("team_members") else 0
            )
            team_ttl = cache_data.get("team_ttl_minutes", TEAM_TTL_MINUTES)
            team_expired = backend._is_expired(team_updated, team_ttl)

            print("Team Members:")
            print(f"  Count: {team_count}")
            print(f"  Last Updated: {team_updated or 'Never'}")
            print(f"  TTL: {team_ttl} minutes (24 hours)")
            print(f"  Status: {'Expired' if team_expired else 'Fresh'}\n")

            # Default branch status
            default_branch = cache_data.get("default_branch")
            default_branch_updated = cache_data.get("default_branch_updated")
            default_branch_expired = backend._is_expired(
                default_branch_updated, cache_data.get("labels_ttl_minutes", DEFAULT_TTL_MINUTES)
            )

            print(f"Default Branch: {default_branch or 'Not cached'}")
            print(f"  Last Updated: {default_branch_updated or 'Never'}")
            print(f"  Status: {'Expired' if default_branch_expired else 'Fresh'}\n")

            # Overall health
            all_fresh = not any(
                [labels_expired, milestones_expired, team_expired, default_branch_expired]
            )
            print(f"Cache Health: {'All entries fresh' if all_fresh else 'Some entries expired'}")

        elif cmd == "clear":
            print("Clearing cache...")
            cache.clear()
            print("Cache cleared!")

        elif cmd == "refresh":
            print("Force refreshing all cache...")
            labels = cache.get_labels(force_refresh=True)
            milestones = cache.get_milestones(force_refresh=True)
            branch = cache.get_default_branch(force_refresh=True)
            print(
                f"Cached: {len(labels)} labels, {len(milestones)} milestones, default branch: {branch}"
            )

        else:
            print(f"Unknown command: {cmd}")
            print("\nUsage:")
            print("  python github_cache.py labels     # Show cached labels")
            print("  python github_cache.py milestones # Show cached milestones")
            print("  python github_cache.py branch     # Show default branch")
            print("  python github_cache.py status     # Show cache status")
            print("  python github_cache.py clear      # Clear cache")
            print("  python github_cache.py refresh    # Force refresh all")
    else:
        print("GitHub Cache Test")
        print("\nUsage:")
        print("  python github_cache.py labels     # Show cached labels")
        print("  python github_cache.py milestones # Show cached milestones")
        print("  python github_cache.py branch     # Show default branch")
        print("  python github_cache.py status     # Show cache status")
        print("  python github_cache.py clear      # Clear cache")
        print("  python github_cache.py refresh    # Force refresh all")
