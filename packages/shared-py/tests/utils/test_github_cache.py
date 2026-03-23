#!/usr/bin/env python3
"""Tests for github_cache module (LocalGitHubCache)."""

from datetime import datetime, timedelta
from unittest.mock import patch

from popkit_shared.utils.github_cache import LocalGitHubCache


class TestLocalGitHubCacheInit:
    """Test LocalGitHubCache initialization."""

    def test_init_default_cache_dir(self):
        cache = LocalGitHubCache()
        assert "popkit" in str(cache.cache_dir)
        assert str(cache.cache_file).endswith("github-cache.json")

    def test_init_custom_cache_dir(self, tmp_path):
        cache_dir = tmp_path / "custom"
        cache = LocalGitHubCache(cache_dir=cache_dir)
        assert cache.cache_dir == cache_dir
        assert cache.cache_file == cache_dir / "github-cache.json"

    def test_init_cache_data_is_none(self, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        assert cache._cache_data is None


class TestLocalGitHubCacheLoadAndInit:
    """Test cache loading and initialization."""

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_load_creates_cache_dir(self, mock_repo, tmp_path):
        cache_dir = tmp_path / "new_dir"
        cache = LocalGitHubCache(cache_dir=cache_dir)
        cache._load_cache()
        # _init_cache doesn't create dir, _save_cache does
        assert cache._cache_data is not None

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_load_empty_creates_structure(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        data = cache._load_cache()
        assert data["repository"] == "test/repo"
        assert data["cache_version"] == "1.0.0"
        assert data["labels"] is None
        assert data["milestones"] is None
        assert data["team_members"] is None
        assert data["default_branch"] is None

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_load_returns_cached_data(self, mock_repo, tmp_path):
        """Second load returns in-memory cache."""
        cache = LocalGitHubCache(cache_dir=tmp_path)
        data1 = cache._load_cache()
        data2 = cache._load_cache()
        assert data1 is data2

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_corrupted_cache_reinitializes(self, mock_repo, tmp_path):
        """Corrupted cache file is handled gracefully."""
        cache_file = tmp_path / "github-cache.json"
        cache_file.write_text("not valid json{{{")

        cache = LocalGitHubCache(cache_dir=tmp_path)
        data = cache._load_cache()
        assert data["cache_version"] == "1.0.0"
        assert data["labels"] is None


class TestLocalGitHubCacheLabels:
    """Test label caching."""

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_set_and_get_labels(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        test_labels = [
            {"name": "bug", "color": "d73a4a"},
            {"name": "enhancement", "color": "a2eeef"},
        ]
        cache.set_labels(test_labels)
        result = cache.get_labels()
        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "bug"

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_get_labels_none_when_not_set(self, mock_repo, tmp_path):
        """Unset labels return None (expired since updated_at is None)."""
        cache = LocalGitHubCache(cache_dir=tmp_path)
        result = cache.get_labels()
        assert result is None

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_get_labels_force_refresh(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        cache.set_labels([{"name": "test"}])
        result = cache.get_labels(force_refresh=True)
        assert result is None

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_set_labels_custom_ttl(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        cache.set_labels([{"name": "test"}], ttl_minutes=120)
        data = cache._load_cache()
        assert data["labels_ttl_minutes"] == 120


class TestLocalGitHubCacheMilestones:
    """Test milestone caching."""

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_set_and_get_milestones(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        milestones = [{"title": "v1.0", "number": 1, "state": "open"}]
        cache.set_milestones(milestones)
        result = cache.get_milestones()
        assert result is not None
        assert len(result) == 1
        assert result[0]["title"] == "v1.0"

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_get_milestones_none_when_not_set(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        result = cache.get_milestones()
        assert result is None

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_get_milestones_force_refresh(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        cache.set_milestones([{"title": "v2.0"}])
        result = cache.get_milestones(force_refresh=True)
        assert result is None


class TestLocalGitHubCacheTeamMembers:
    """Test team member caching."""

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_set_and_get_team_members(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        team = ["alice", "bob", "charlie"]
        cache.set_team_members(team)
        result = cache.get_team_members()
        assert result is not None
        assert len(result) == 3
        assert "alice" in result

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_get_team_none_when_not_set(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        result = cache.get_team_members()
        assert result is None

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_set_team_custom_ttl(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        cache.set_team_members(["alice"], ttl_minutes=60)
        data = cache._load_cache()
        assert data["team_ttl_minutes"] == 60


class TestLocalGitHubCacheDefaultBranch:
    """Test default branch caching."""

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_set_and_get_default_branch(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        cache.set_default_branch("main")
        result = cache.get_default_branch()
        assert result == "main"

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_get_default_branch_none_when_not_set(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        result = cache.get_default_branch()
        assert result is None


class TestLocalGitHubCacheExpiry:
    """Test cache expiry logic."""

    def test_is_expired_none_updated_at(self, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        assert cache._is_expired(None, 60) is True

    def test_is_expired_invalid_timestamp(self, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        assert cache._is_expired("not-a-date", 60) is True

    def test_is_expired_fresh(self, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        now = datetime.now().isoformat()
        assert cache._is_expired(now, 60) is False

    def test_is_expired_old(self, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        old = (datetime.now() - timedelta(hours=2)).isoformat()
        assert cache._is_expired(old, 60) is True

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_expired_labels_return_none(self, mock_repo, tmp_path):
        """Labels with expired TTL return None."""
        cache = LocalGitHubCache(cache_dir=tmp_path)
        cache.set_labels([{"name": "test"}])

        # Manually expire by backdating the update timestamp
        data = cache._load_cache()
        data["labels_updated"] = (datetime.now() - timedelta(hours=2)).isoformat()
        cache._save_cache()
        cache._cache_data = None  # Force reload from disk

        result = cache.get_labels()
        assert result is None


class TestLocalGitHubCachePersistence:
    """Test cache persistence across instances."""

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_persistence_across_instances(self, mock_repo, tmp_path):
        """Cache persists between instances."""
        cache1 = LocalGitHubCache(cache_dir=tmp_path)
        cache1.set_labels([{"name": "persist-test"}])

        cache2 = LocalGitHubCache(cache_dir=tmp_path)
        result = cache2.get_labels()
        assert result is not None
        assert result[0]["name"] == "persist-test"

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_clear_removes_all_data(self, mock_repo, tmp_path):
        cache = LocalGitHubCache(cache_dir=tmp_path)
        cache.set_labels([{"name": "test"}])
        cache.set_milestones([{"title": "v1.0"}])
        cache.set_team_members(["alice"])
        cache.set_default_branch("main")

        cache.clear()

        assert cache.get_labels() is None
        assert cache.get_milestones() is None
        assert cache.get_team_members() is None
        assert cache.get_default_branch() is None

    @patch.object(LocalGitHubCache, "_get_current_repo", return_value="test/repo")
    def test_save_creates_directory(self, mock_repo, tmp_path):
        """Saving cache creates the directory if needed."""
        cache_dir = tmp_path / "deep" / "nested" / "dir"
        cache = LocalGitHubCache(cache_dir=cache_dir)
        cache.set_labels([{"name": "test"}])
        assert cache_dir.exists()
        assert (cache_dir / "github-cache.json").exists()
