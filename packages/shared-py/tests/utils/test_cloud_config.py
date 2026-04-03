#!/usr/bin/env python3
"""Tests for shared cloud config resolution."""

import json
from pathlib import Path

from popkit_shared.utils.cloud_config import (
    DEFAULT_API_URL,
    get_cloud_config_paths,
    has_cloud_api_key,
    load_cloud_config,
    resolve_cloud_config,
)


def test_get_cloud_config_paths_uses_expected_locations(tmp_path: Path):
    """Config lookup should check the primary file before the legacy fallback."""
    paths = get_cloud_config_paths(home=tmp_path)

    assert paths == [
        tmp_path / ".popkit" / "cloud-config.json",
        tmp_path / ".claude" / "popkit" / "cloud-config.json",
    ]


def test_resolve_cloud_config_prefers_env_values(tmp_path: Path):
    """Explicit env vars should win over anything saved on disk."""
    config_path = tmp_path / ".popkit" / "cloud-config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(json.dumps({"api_key": "pk_file", "api_url": "https://file.example"}))

    api_key, api_url = resolve_cloud_config(
        env={"POPKIT_API_KEY": "pk_env", "POPKIT_API_URL": "https://env.example"},
        config_paths=[config_path],
    )

    assert api_key == "pk_env"
    assert api_url == "https://env.example"


def test_resolve_cloud_config_reads_saved_file_when_env_missing(tmp_path: Path):
    """Saved login config should work without exported env vars."""
    config_path = tmp_path / ".popkit" / "cloud-config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(json.dumps({"api_key": "pk_saved", "api_url": "https://saved.example"}))

    api_key, api_url = resolve_cloud_config(env={}, config_paths=[config_path])

    assert api_key == "pk_saved"
    assert api_url == "https://saved.example"


def test_load_cloud_config_skips_invalid_files_and_uses_legacy_fallback(tmp_path: Path):
    """Invalid primary config should not block the legacy fallback."""
    primary = tmp_path / ".popkit" / "cloud-config.json"
    legacy = tmp_path / ".claude" / "popkit" / "cloud-config.json"
    primary.parent.mkdir(parents=True)
    legacy.parent.mkdir(parents=True)
    primary.write_text("{not-json")
    legacy.write_text(json.dumps({"api_key": "pk_legacy"}))

    config = load_cloud_config(config_paths=[primary, legacy])

    assert config == {"api_key": "pk_legacy"}


def test_has_cloud_api_key_false_when_only_url_is_present(tmp_path: Path):
    """A saved API URL without a key should still count as unauthenticated."""
    config_path = tmp_path / ".popkit" / "cloud-config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(json.dumps({"api_url": "https://saved.example"}))

    assert has_cloud_api_key(env={}, config_paths=[config_path]) is False
    assert resolve_cloud_config(env={}, config_paths=[config_path]) == ("", "https://saved.example")


def test_resolve_cloud_config_defaults_url_when_nothing_is_configured():
    """The default cloud URL should stay stable with no config."""
    assert resolve_cloud_config(env={}, config_paths=[]) == ("", DEFAULT_API_URL)
