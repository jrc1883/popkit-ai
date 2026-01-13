#!/usr/bin/env python3
"""
Routine Cache System.

Detects unchanged state to avoid redundant tool calls and reduce token usage.
Caches git status, test results, and other expensive operations.
"""

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class CacheEntry:
    """Single cache entry with TTL and hash."""

    key: str
    value: Any
    hash: str
    timestamp: float
    ttl: int  # seconds

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.timestamp > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        return cls(**data)


class RoutineCache:
    """Cache manager for routine executions."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize cache.

        Args:
            cache_dir: Directory for cache storage (default: .claude/popkit/cache/)
        """
        if cache_dir is None:
            cache_dir = Path.cwd() / ".claude" / "popkit" / "cache"

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "routine_cache.json"
        self.cache: Dict[str, CacheEntry] = {}
        self._load()

    def _load(self) -> None:
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    self.cache = {k: CacheEntry.from_dict(v) for k, v in data.items()}
            except (json.JSONDecodeError, KeyError):
                # Corrupted cache, start fresh
                self.cache = {}

    def _save(self) -> None:
        """Save cache to disk."""
        data = {k: v.to_dict() for k, v in self.cache.items()}
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)

    def _hash_value(self, value: Any) -> str:
        """Generate hash of value for change detection.

        Args:
            value: Value to hash

        Returns:
            SHA256 hex digest
        """
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        elif not isinstance(value, str):
            value = str(value)

        return hashlib.sha256(value.encode()).hexdigest()

    def get(self, key: str, current_value: Optional[Any] = None) -> Optional[Any]:
        """Get cached value if still valid.

        Args:
            key: Cache key
            current_value: Current value to check against cache

        Returns:
            Cached value if valid, None otherwise
        """
        entry = self.cache.get(key)

        if entry is None:
            return None

        # Check if expired
        if entry.is_expired():
            del self.cache[key]
            self._save()
            return None

        # If current_value provided, check if changed
        if current_value is not None:
            current_hash = self._hash_value(current_value)
            if current_hash != entry.hash:
                # Value changed, invalidate cache
                return None

        return entry.value

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set cached value.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 5 minutes)
        """
        value_hash = self._hash_value(value)

        entry = CacheEntry(key=key, value=value, hash=value_hash, timestamp=time.time(), ttl=ttl)

        self.cache[key] = entry
        self._save()

    def invalidate(self, key: str) -> None:
        """Invalidate a cache entry.

        Args:
            key: Cache key to invalidate
        """
        if key in self.cache:
            del self.cache[key]
            self._save()

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache = {}
        self._save()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total = len(self.cache)
        expired = sum(1 for e in self.cache.values() if e.is_expired())
        valid = total - expired

        return {
            "total_entries": total,
            "valid_entries": valid,
            "expired_entries": expired,
            "cache_file": str(self.cache_file),
            "cache_size_bytes": self.cache_file.stat().st_size if self.cache_file.exists() else 0,
        }


# Predefined cache keys for common routine operations
CACHE_KEYS = {
    "GIT_STATUS": "git_status",
    "GIT_DIFF_STAT": "git_diff_stat",
    "TEST_RESULTS": "test_results",
    "LINT_RESULTS": "lint_results",
    "TYPE_CHECK": "type_check",
    "LAST_COMMIT": "last_commit",
    "BRANCH_INFO": "branch_info",
}


def check_git_status_unchanged(cache: RoutineCache) -> bool:
    """Check if git status has changed since last cache.

    Args:
        cache: Cache instance

    Returns:
        True if unchanged (can use cached result), False if changed
    """
    import subprocess

    try:
        # Get current git status
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=5
        )
        current_status = result.stdout

        # Check cache
        cached_status = cache.get(CACHE_KEYS["GIT_STATUS"], current_status)

        if cached_status is not None:
            # Cache hit and unchanged
            return True
        else:
            # Cache miss or changed - update cache
            cache.set(CACHE_KEYS["GIT_STATUS"], current_status, ttl=60)
            return False

    except (subprocess.TimeoutExpired, FileNotFoundError):
        # Git not available or timeout
        return False


def check_tests_unchanged(cache: RoutineCache, test_command: str = "pytest") -> bool:
    """Check if tests results would be the same.

    Uses file modification times to detect if source/test files changed.

    Args:
        cache: Cache instance
        test_command: Test command to check

    Returns:
        True if tests likely unchanged, False if need to re-run
    """
    from pathlib import Path
    import glob

    try:
        # Get modification times of test and source files
        test_files = list(Path.cwd().rglob("test_*.py")) + list(Path.cwd().rglob("*_test.py"))
        source_files = list(Path.cwd().rglob("*.py"))

        # Exclude test files from source files
        source_files = [
            f
            for f in source_files
            if not any(f.name.startswith("test_") or f.name.endswith("_test.py") for _ in [f])
        ]

        # Get latest modification time
        all_files = test_files + source_files
        if not all_files:
            return False

        latest_mtime = max(f.stat().st_mtime for f in all_files if f.exists())

        # Check cache
        cached_result = cache.get(CACHE_KEYS["TEST_RESULTS"])

        if cached_result is not None:
            cached_mtime = cached_result.get("latest_mtime", 0)
            if latest_mtime <= cached_mtime:
                # No files changed since last test run
                return True

        # Files changed or no cache
        return False

    except Exception:
        # Error checking files, assume changed
        return False


def update_test_cache(cache: RoutineCache, test_output: str, passed: bool) -> None:
    """Update test cache with results.

    Args:
        cache: Cache instance
        test_output: Test command output
        passed: Whether tests passed
    """
    from pathlib import Path

    try:
        # Get current latest modification time
        test_files = list(Path.cwd().rglob("test_*.py")) + list(Path.cwd().rglob("*_test.py"))
        source_files = list(Path.cwd().rglob("*.py"))

        all_files = test_files + source_files
        if all_files:
            latest_mtime = max(f.stat().st_mtime for f in all_files if f.exists())
        else:
            latest_mtime = time.time()

        cache.set(
            CACHE_KEYS["TEST_RESULTS"],
            {
                "output": test_output,
                "passed": passed,
                "latest_mtime": latest_mtime,
                "timestamp": time.time(),
            },
            ttl=3600,  # 1 hour
        )
    except Exception:
        # Error updating cache, ignore
        pass


def get_cache_stats_report(cache: RoutineCache) -> str:
    """Generate human-readable cache stats report.

    Args:
        cache: Cache instance

    Returns:
        Formatted stats string
    """
    stats = cache.get_stats()

    report = []
    report.append("Cache Statistics:")
    report.append(f"  Valid entries: {stats['valid_entries']}")
    report.append(f"  Expired entries: {stats['expired_entries']}")
    report.append(f"  Cache size: {stats['cache_size_bytes']} bytes")
    report.append(f"  Cache file: {stats['cache_file']}")

    return "\n".join(report)
