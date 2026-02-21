#!/usr/bin/env python3
"""Tests for upstream_tracker.py."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.upstream_tracker import (  # noqa: E402
    STATUS_PENDING,
    ChangelogItem,
    RepositoryTracking,
    UpstreamTracker,
)


def test_list_items_accepts_pending_alias(temp_project_dir):
    tracker = UpstreamTracker(cache_dir=temp_project_dir / ".claude" / "popkit")
    tracking = tracker._load_tracking()
    tracking["repositories"]["anthropics/claude-code"]["changelog_items"] = [
        ChangelogItem(
            id="test-item",
            type="release",
            title="Test Release",
            url="https://example.com/release",
            published_date="2026-02-17T00:00:00Z",
            discovered_date="2026-02-17T00:00:00",
            status=STATUS_PENDING,
        ).to_dict()
    ]

    items = tracker.list_items(status_filter="pending")

    assert len(items) == 1
    assert items[0].status == STATUS_PENDING


def test_fetch_releases_applies_tag_prefix_filter(monkeypatch, temp_project_dir):
    tracker = UpstreamTracker(cache_dir=temp_project_dir / ".claude" / "popkit")
    releases = [
        {
            "tag_name": "sdk-v0.74.0",
            "name": "sdk: v0.74.0",
            "published_at": "2026-02-07T18:00:01Z",
            "html_url": "https://example.com/sdk-v0.74.0",
            "body": "sdk release",
        },
        {
            "tag_name": "bedrock-sdk-v0.30.0",
            "name": "bedrock: v0.30.0",
            "published_at": "2026-02-08T00:00:00Z",
            "html_url": "https://example.com/bedrock-sdk-v0.30.0",
            "body": "bedrock release",
        },
    ]

    monkeypatch.setattr(
        "subprocess.run",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(releases)),
    )

    filtered = tracker._fetch_releases(
        repo="anthropics/anthropic-sdk-typescript",
        max_releases=10,
        release_tag_prefixes=["sdk-v"],
    )

    assert len(filtered) == 1
    assert filtered[0]["tag_name"] == "sdk-v0.74.0"


def test_fetch_repo_updates_adds_commit_items_for_commit_tracked_repo(
    monkeypatch, temp_project_dir
):
    tracker = UpstreamTracker(cache_dir=temp_project_dir / ".claude" / "popkit")
    repo_tracking = RepositoryTracking(
        repo="anthropics/claude-plugins-official",
        last_checked="2026-02-01T00:00:00",
    )

    monkeypatch.setattr(tracker, "_fetch_releases", lambda **_: [])
    monkeypatch.setattr(
        tracker,
        "_fetch_commits",
        lambda **_: [
            {
                "sha": "abcdef123456",
                "title": "claude-plugins-official commit: add feature-dev improvements",
                "published_at": "2026-02-17T00:00:00Z",
                "url": "https://example.com/commit/abcdef123456",
            }
        ],
    )

    items = tracker._fetch_repo_updates("anthropics/claude-plugins-official", repo_tracking)

    assert len(items) == 1
    assert items[0].type == "commit"
    assert repo_tracking.latest_commit == "abcdef123456"


def test_initial_commit_bootstrap_is_limited(monkeypatch, temp_project_dir):
    tracker = UpstreamTracker(cache_dir=temp_project_dir / ".claude" / "popkit")
    repo_tracking = RepositoryTracking(
        repo="anthropics/claude-plugins-official",
        last_checked=None,
    )

    monkeypatch.setattr(tracker, "_fetch_releases", lambda **_: [])
    monkeypatch.setattr(
        tracker,
        "_fetch_commits",
        lambda **_: [
            {
                "sha": "111111111111",
                "title": "claude-plugins-official commit: one",
                "published_at": "2026-02-17T00:00:00Z",
                "url": "https://example.com/commit/111111111111",
            },
            {
                "sha": "222222222222",
                "title": "claude-plugins-official commit: two",
                "published_at": "2026-02-16T00:00:00Z",
                "url": "https://example.com/commit/222222222222",
            },
            {
                "sha": "333333333333",
                "title": "claude-plugins-official commit: three",
                "published_at": "2026-02-15T00:00:00Z",
                "url": "https://example.com/commit/333333333333",
            },
        ],
    )

    items = tracker._fetch_repo_updates("anthropics/claude-plugins-official", repo_tracking)

    assert len(items) == 1
    assert items[0].url == "https://example.com/commit/111111111111"
