#!/usr/bin/env python3
"""Unit tests for pop-next-action analyze_state helpers."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "pop-next-action"
    / "scripts"
    / "analyze_state.py"
)
SPEC = spec_from_file_location("pop_next_action_analyze_state", SCRIPT_PATH)
assert SPEC and SPEC.loader
analyze_state = module_from_spec(SPEC)
SPEC.loader.exec_module(analyze_state)


def test_typescript_command_uses_windows_npx_cmd(monkeypatch):
    """Windows should prefer npx.cmd so subprocess can launch Node tooling."""

    def fake_which(name):
        if name == "npx.cmd":
            return r"C:\Program Files\nodejs\npx.cmd"
        return None

    monkeypatch.setattr(analyze_state.sys, "platform", "win32")
    monkeypatch.setattr(analyze_state.shutil, "which", fake_which)

    command = analyze_state._typescript_command("--noEmit")

    assert command == [r"C:\Program Files\nodejs\npx.cmd", "tsc", "--noEmit"]


def test_analyze_code_state_uses_resolved_typescript_command(monkeypatch, tmp_path):
    """Monorepo TS analysis should use the resolved runner and report clean state."""

    tsconfig = tmp_path / "packages" / "docs" / "tsconfig.json"
    tsconfig.parent.mkdir(parents=True)
    tsconfig.write_text("{}")

    observed_commands = []

    def fake_run_command_simple(cmd, **kwargs):
        observed_commands.append(cmd)
        return "", True

    monkeypatch.setattr(analyze_state.sys, "platform", "win32")
    monkeypatch.setattr(
        analyze_state.shutil,
        "which",
        lambda name: r"C:\Program Files\nodejs\npx.cmd" if name == "npx.cmd" else None,
    )
    monkeypatch.setattr(analyze_state, "run_command_simple", fake_run_command_simple)

    state = analyze_state.analyze_code_state(tmp_path)

    assert state["has_typescript"] is True
    assert state["typescript_errors"] == 0
    assert state["typescript_projects_checked"] == 1
    assert observed_commands == [
        [
            r"C:\Program Files\nodejs\npx.cmd",
            "tsc",
            "--noEmit",
            "--pretty",
            "false",
            "--project",
            str(tsconfig),
        ]
    ]
