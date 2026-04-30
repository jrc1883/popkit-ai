#!/usr/bin/env python3
"""Tests for popkit login config handling."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI_ROOT = ROOT / "popkit-cli"
SHARED_ROOT = ROOT / "shared-py"

for candidate in (CLI_ROOT, SHARED_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from popkit_cli.commands import login  # noqa: E402


def test_save_config_writes_expected_payload(tmp_path, monkeypatch):
    """Direct key entry should persist key, email, and URL to the primary config path."""
    config_dir = tmp_path / ".popkit"
    config_path = config_dir / "cloud-config.json"
    monkeypatch.setattr(login, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(login, "CONFIG_FILE", config_path)

    saved_path = login.save_config(
        "pk_test_123", email="user@example.com", api_url="https://api.example"
    )

    assert saved_path == config_path
    assert json.loads(config_path.read_text()) == {
        "api_key": "pk_test_123",
        "email": "user@example.com",
        "api_url": "https://api.example",
    }


def test_get_api_key_prefers_env_over_saved_config(tmp_path):
    """Env vars should stay the highest-priority auth source."""
    config_path = tmp_path / ".popkit" / "cloud-config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(json.dumps({"api_key": "pk_saved"}))

    api_key, _ = login.resolve_cloud_config(
        env={"POPKIT_API_KEY": "pk_env"},
        config_paths=[config_path],
    )

    assert api_key == "pk_env"


def test_load_config_reads_saved_primary_file(tmp_path):
    """Login helpers should read the same config shape they write."""
    config_path = tmp_path / ".popkit" / "cloud-config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(json.dumps({"api_key": "pk_saved", "email": "user@example.com"}))

    config = login.load_cloud_config(config_paths=[config_path])

    assert config == {"api_key": "pk_saved", "email": "user@example.com"}
