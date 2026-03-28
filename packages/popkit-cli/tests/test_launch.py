#!/usr/bin/env python3
"""Tests for popkit provider launch."""

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PACKAGES / "shared-py"))

from popkit_cli.commands.launch import _host_supports_plan_mode, run_launch
from popkit_cli.main import build_parser


def test_parser_supports_provider_launch():
    parser = build_parser()

    args = parser.parse_args(
        [
            "provider",
            "launch",
            "codex",
            "--mode",
            "plan",
            "--command",
            "/popkit-dev:next",
            "--print-only",
        ]
    )

    assert args.command == "provider"
    assert args.provider_command == "launch"
    assert args.provider == "codex"
    assert args.mode == "plan"
    assert args.launch_command == "/popkit-dev:next"
    assert args.print_only is True


def test_host_supports_plan_mode_from_env():
    assert _host_supports_plan_mode({"POPKIT_HOST_CAN_REQUEST_USER_INPUT": "true"}) is True
    assert _host_supports_plan_mode({"POPKIT_HOST_SUPPORTS_CODEX_PLAN_MODE": "1"}) is True
    assert _host_supports_plan_mode({}) is False


def test_run_launch_print_only_falls_back_without_host_support(monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("POPKIT_HOST_CAN_REQUEST_USER_INPUT", raising=False)
    monkeypatch.delenv("POPKIT_HOST_SUPPORTS_CODEX_PLAN_MODE", raising=False)

    args = argparse.Namespace(
        provider="codex",
        mode="plan",
        launch_command="/popkit-dev:next",
        cd=str(tmp_path),
        print_only=True,
    )

    result = run_launch(args)

    captured = capsys.readouterr()
    assert result == 0
    assert "Actual mode: default" in captured.out
    assert "Interaction surface: plain_text" in captured.out
    assert "Falling back to standard launch" in captured.out


def test_run_launch_executes_plan_mode_when_host_support_exists(monkeypatch, capsys, tmp_path):
    calls = {}

    def fake_run(command, cwd, env, check):
        calls["command"] = command
        calls["cwd"] = cwd
        calls["env"] = env
        calls["check"] = check
        return SimpleNamespace(returncode=0)

    monkeypatch.setenv("POPKIT_HOST_CAN_REQUEST_USER_INPUT", "1")
    monkeypatch.setattr("popkit_cli.commands.launch.subprocess.run", fake_run)

    args = argparse.Namespace(
        provider="codex",
        mode="plan",
        launch_command="/popkit-dev:next",
        cd=str(tmp_path),
        print_only=False,
    )

    result = run_launch(args)

    captured = capsys.readouterr()
    assert result == 0
    assert "Actual mode: plan" in captured.out
    assert "Interaction surface: request_user_input" in captured.out
    assert calls["cwd"] == str(tmp_path)
    assert calls["env"]["POPKIT_PROVIDER"] == "codex"
    assert calls["env"]["POPKIT_INTERACTION_SURFACE"] == "request_user_input"
    assert calls["env"]["POPKIT_CAN_REQUEST_USER_INPUT"] == "1"
    assert calls["command"][-1] == "/popkit-dev:next"
    assert ["-c", 'model_reasoning_effort="high"'] == calls["command"][3:5]
    assert calls["check"] is False


def test_run_launch_rejects_unknown_provider(capsys):
    args = argparse.Namespace(
        provider="unknown",
        mode="default",
        launch_command=None,
        cd=None,
        print_only=True,
    )

    result = run_launch(args)

    captured = capsys.readouterr()
    assert result == 1
    assert "Unknown provider 'unknown'" in captured.out
