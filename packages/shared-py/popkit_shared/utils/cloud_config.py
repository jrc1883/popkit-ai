#!/usr/bin/env python3
"""Shared PopKit Cloud configuration resolution."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

DEFAULT_API_URL = "https://api.thehouseofdeals.com"


def get_cloud_config_paths(home: Path | None = None) -> list[Path]:
    """Return config locations in priority order."""
    if home is not None:
        base = home
    else:
        try:
            base = Path.home()
        except RuntimeError:
            return []

    return [
        base / ".popkit" / "cloud-config.json",
        base / ".claude" / "popkit" / "cloud-config.json",
    ]


def load_cloud_config(config_paths: Sequence[Path] | None = None) -> dict[str, Any] | None:
    """Load the first valid cloud config file."""
    for config_path in config_paths or get_cloud_config_paths():
        if not config_path.exists():
            continue

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        if isinstance(data, dict):
            return data

    return None


def resolve_cloud_config(
    env: Mapping[str, str] | None = None,
    config_paths: Sequence[Path] | None = None,
) -> tuple[str, str]:
    """Resolve API key and URL from env vars first, then saved config."""
    values = env if env is not None else os.environ

    api_key = str(values.get("POPKIT_API_KEY", "") or "").strip()
    api_url = str(values.get("POPKIT_API_URL", DEFAULT_API_URL) or DEFAULT_API_URL).strip()

    if api_key:
        return api_key, api_url.rstrip("/")

    config = load_cloud_config(config_paths=config_paths)
    if config:
        saved_key = str(config.get("api_key", "") or "").strip()
        saved_url = str(config.get("api_url", api_url) or api_url).strip()
        if saved_key:
            return saved_key, saved_url.rstrip("/")
        api_url = saved_url

    return "", api_url.rstrip("/")


def get_cloud_api_key(
    env: Mapping[str, str] | None = None,
    config_paths: Sequence[Path] | None = None,
) -> str:
    """Return the resolved PopKit Cloud API key."""
    return resolve_cloud_config(env=env, config_paths=config_paths)[0]


def get_cloud_api_url(
    env: Mapping[str, str] | None = None,
    config_paths: Sequence[Path] | None = None,
) -> str:
    """Return the resolved PopKit Cloud API URL."""
    return resolve_cloud_config(env=env, config_paths=config_paths)[1]


def has_cloud_api_key(
    env: Mapping[str, str] | None = None,
    config_paths: Sequence[Path] | None = None,
) -> bool:
    """Return True when a cloud API key is configured."""
    return bool(get_cloud_api_key(env=env, config_paths=config_paths))
