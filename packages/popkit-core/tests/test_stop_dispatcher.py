#!/usr/bin/env python3
"""
Tests for ``hooks/stop.py`` — Phase 1a-ii dispatcher.

Pin five things:

1. Pending ledger written by ``/checkpoint`` is archived into the
   per-turn bundle directory and the pending slot is removed.
2. Missing pending → ``status='missing'`` stub is written into the
   bundle AND a loud stderr warning surfaces ``no_checkpoint_called``.
3. Malformed pending (corrupt JSON, wrong schema_version, unknown
   status) is treated like missing and produces a stub with the
   specific reason recorded.
4. ``status: success`` JSON shape and exit code 0 hold across every
   path so Claude Code's Stop pipeline never gets blocked.
5. The previously-emitted privacy violations (``logs/stop.json`` raw
   dump, ``logs/chat.json`` transcript save) do NOT happen anymore.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def load_stop_module():
    here = Path(__file__).resolve().parents[1]
    stop_path = here / "hooks" / "stop.py"
    spec = importlib.util.spec_from_file_location("stop_dispatcher", stop_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def stop():
    return load_stop_module()


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    """Create a minimal directory tree with a ``.git`` marker."""
    (tmp_path / ".git").mkdir()
    return tmp_path


def _valid_pending_ledger(session_id: str = "sess-1", turn_id: str = "turn-1") -> dict:
    return {
        "schema_version": 1,
        "status": "normal",
        "session_id": session_id,
        "turn_id": turn_id,
        "lane_id": "popkit-docs",
        "stage": "code",
        "intent": "land Phase 1a-ii dispatcher",
        "changed_files": [{"path": "hooks/stop.py", "added": 100, "removed": 80}],
        "acceptance_claims": ["dispatcher archives pending ledger into bundle"],
        "next_action": "verify",
    }


def _write_pending(repo: Path, ledger) -> Path:
    pending_dir = repo / ".claude" / "popkit"
    pending_dir.mkdir(parents=True, exist_ok=True)
    pending = pending_dir / "pending-claim-ledger.json"
    if isinstance(ledger, str):
        pending.write_text(ledger, encoding="utf-8")
    else:
        pending.write_text(json.dumps(ledger), encoding="utf-8")
    return pending


def _bundle_path(repo: Path, session_id: str, turn_id: str) -> Path:
    return (
        repo
        / ".claude"
        / "popkit"
        / "verifier-bundles"
        / session_id
        / turn_id
        / "ledger.json"
    )


# ---------------------------------------------------------------------------
# Happy path: pending ledger archived
# ---------------------------------------------------------------------------


def test_pending_ledger_archived_and_pending_removed(stop, fake_repo, monkeypatch):
    monkeypatch.chdir(fake_repo)
    ledger = _valid_pending_ledger("sess-A", "turn-A")
    pending = _write_pending(fake_repo, ledger)

    response = stop.dispatch({"session_id": "claude-sess-from-stdin"})

    assert response["status"] == "success"
    assert response["ledger_status"] == "archived"
    # Writer-supplied ids win over Claude Code stdin ids — the bundle
    # path follows what /checkpoint already wrote.
    assert response["session_id"] == "sess-A"
    assert response["turn_id"] == "turn-A"
    bundle = _bundle_path(fake_repo, "sess-A", "turn-A")
    assert bundle.exists()
    on_disk = json.loads(bundle.read_text(encoding="utf-8"))
    assert on_disk == ledger
    assert not pending.exists()


def test_archived_response_includes_bundle_path(stop, fake_repo, monkeypatch):
    monkeypatch.chdir(fake_repo)
    _write_pending(fake_repo, _valid_pending_ledger("s", "t"))
    response = stop.dispatch({"session_id": "ignored"})
    assert response["bundle_path"].endswith(
        str(Path(".claude/popkit/verifier-bundles/s/t/ledger.json"))
    ) or response["bundle_path"].endswith("ledger.json")
    assert "missing_reason" not in response


# ---------------------------------------------------------------------------
# Missing pending → stub written + loud stderr
# ---------------------------------------------------------------------------


def test_missing_pending_writes_stub(stop, fake_repo, monkeypatch, capsys):
    """No /checkpoint this turn → bundle gets a status='missing' stub."""
    monkeypatch.chdir(fake_repo)
    response = stop.dispatch({"session_id": "sess-stub"})

    captured = capsys.readouterr()
    assert response["status"] == "success"
    assert response["ledger_status"] == "missing"
    assert response["missing_reason"] == "no_checkpoint_called"
    bundle = Path(response["bundle_path"])
    assert bundle.exists()
    stub = json.loads(bundle.read_text(encoding="utf-8"))
    assert stub["schema_version"] == 1
    assert stub["status"] == "missing"
    assert stub["reason"] == "no_checkpoint_called"
    assert stub["session_id"] == "sess-stub"
    # Stub still satisfies required-field structure so the verifier can
    # parse it on the same code path as a normal ledger.
    for k in (
        "turn_id",
        "lane_id",
        "stage",
        "intent",
        "changed_files",
        "acceptance_claims",
        "next_action",
    ):
        assert k in stub

    # Loud stderr per Codex round 5 #4 — operator sees absence during the turn.
    assert "WARNING" in captured.err
    assert "no /checkpoint called" in captured.err
    assert "no_checkpoint_called" in captured.err


# ---------------------------------------------------------------------------
# Malformed pending → treated as missing with specific reason
# ---------------------------------------------------------------------------


def test_corrupt_json_pending_treated_as_missing(stop, fake_repo, monkeypatch, capsys):
    monkeypatch.chdir(fake_repo)
    _write_pending(fake_repo, "{not valid json")
    response = stop.dispatch({"session_id": "s"})
    assert response["ledger_status"] == "missing"
    assert response["missing_reason"].startswith("pending_invalid_json")
    assert "WARNING" in capsys.readouterr().err


def test_wrong_schema_version_pending_treated_as_missing(stop, fake_repo, monkeypatch):
    monkeypatch.chdir(fake_repo)
    bad = _valid_pending_ledger()
    bad["schema_version"] = 2
    _write_pending(fake_repo, bad)
    response = stop.dispatch({"session_id": "s"})
    assert response["ledger_status"] == "missing"
    assert response["missing_reason"].startswith("pending_unsupported_schema_version")


def test_unknown_status_pending_treated_as_missing(stop, fake_repo, monkeypatch):
    monkeypatch.chdir(fake_repo)
    bad = _valid_pending_ledger()
    bad["status"] = "bogus"
    _write_pending(fake_repo, bad)
    response = stop.dispatch({"session_id": "s"})
    assert response["ledger_status"] == "missing"
    assert response["missing_reason"].startswith("pending_unknown_status")


def test_pending_top_level_not_object_treated_as_missing(stop, fake_repo, monkeypatch):
    monkeypatch.chdir(fake_repo)
    _write_pending(fake_repo, "[1, 2, 3]")
    response = stop.dispatch({"session_id": "s"})
    assert response["ledger_status"] == "missing"
    assert response["missing_reason"] == "pending_not_object"


# ---------------------------------------------------------------------------
# No-repo path (cwd outside any git repo)
# ---------------------------------------------------------------------------


def test_no_repo_root_returns_skipped(stop, tmp_path, monkeypatch):
    """If we can't find a repo root, dispatch returns cleanly with status
    skipped_no_repo. Claude Code's Stop must not be blocked even when
    invoked from outside a repo."""
    monkeypatch.chdir(tmp_path)
    response = stop.dispatch({"session_id": "no-repo"})
    assert response["status"] == "success"
    assert response["ledger_status"] == "skipped_no_repo"
    assert response["bundle_path"] is None


# ---------------------------------------------------------------------------
# Privacy: previous logs/stop.json + logs/chat.json dumps are gone
# ---------------------------------------------------------------------------


def test_no_logs_stop_json_written(stop, fake_repo, monkeypatch):
    """Privacy regression guard. The previous stop.py dumped the raw
    Claude Code stdin payload to logs/stop.json — Codex flagged that as
    a privacy violation. The new dispatcher must never write it."""
    monkeypatch.chdir(fake_repo)
    _write_pending(fake_repo, _valid_pending_ledger())
    stop.dispatch(
        {"session_id": "s", "transcript": [{"role": "user", "content": "secret"}]}
    )
    assert not (fake_repo / "logs" / "stop.json").exists()
    assert not (fake_repo / "logs").exists()


def test_no_logs_chat_json_written_even_with_save_chat_true(
    stop, fake_repo, monkeypatch
):
    """The previous version wrote logs/chat.json when save_chat=True. The
    new dispatcher ignores that field — same privacy rationale."""
    monkeypatch.chdir(fake_repo)
    response = stop.dispatch(
        {
            "session_id": "s",
            "save_chat": True,
            "transcript": [{"role": "user", "content": "secret"}],
        }
    )
    assert not (fake_repo / "logs" / "chat.json").exists()
    # Response shape no longer includes chat_saved either.
    assert "chat_saved" not in response


# ---------------------------------------------------------------------------
# Empty / weird stdin payloads
# ---------------------------------------------------------------------------


def test_empty_input_still_dispatches(stop, fake_repo, monkeypatch):
    monkeypatch.chdir(fake_repo)
    response = stop.dispatch({})
    # No session_id supplied → generated UUID.
    assert response["status"] == "success"
    assert response["ledger_status"] == "missing"
    assert isinstance(response["session_id"], str) and len(response["session_id"]) >= 8


def test_session_id_from_input_used_for_stub_path(stop, fake_repo, monkeypatch):
    """Stop hook stdin's session_id is what scopes the stub bundle dir
    when no /checkpoint was called."""
    monkeypatch.chdir(fake_repo)
    response = stop.dispatch({"session_id": "claude-sid-123"})
    bundle = Path(response["bundle_path"])
    assert "claude-sid-123" in bundle.parts


# ---------------------------------------------------------------------------
# CLI surface: stdin → stdout JSON, exit 0 always
# ---------------------------------------------------------------------------


def test_main_returns_zero_on_valid_stdin(stop, fake_repo, monkeypatch, capsys):
    monkeypatch.chdir(fake_repo)
    _write_pending(fake_repo, _valid_pending_ledger("s", "t"))
    monkeypatch.setattr(
        "sys.stdin", _StringStdin(json.dumps({"session_id": "ignored"}))
    )
    rc = stop.main()
    captured = capsys.readouterr()
    assert rc == 0
    response = json.loads(captured.out)
    assert response["status"] == "success"
    assert response["ledger_status"] == "archived"


def test_main_returns_zero_on_invalid_json(stop, fake_repo, monkeypatch, capsys):
    """Stop hook MUST NOT block Claude Code on parse failure."""
    monkeypatch.chdir(fake_repo)
    monkeypatch.setattr("sys.stdin", _StringStdin("{not json"))
    rc = stop.main()
    captured = capsys.readouterr()
    assert rc == 0
    response = json.loads(captured.out)
    assert response["status"] == "success"
    # Treats invalid stdin as empty payload → no /checkpoint → stub.
    assert response["ledger_status"] == "missing"
    assert "WARNING" in captured.err


def test_main_returns_zero_on_empty_input(stop, fake_repo, monkeypatch, capsys):
    monkeypatch.chdir(fake_repo)
    monkeypatch.setattr("sys.stdin", _StringStdin(""))
    rc = stop.main()
    captured = capsys.readouterr()
    assert rc == 0
    response = json.loads(captured.out)
    assert response["status"] == "success"


def test_main_returns_zero_on_dispatcher_exception(
    stop, fake_repo, monkeypatch, capsys
):
    """Last-resort safety net: an unexpected exception in dispatch()
    must surface as status='error' on stdout, not a non-zero exit."""
    monkeypatch.chdir(fake_repo)
    monkeypatch.setattr("sys.stdin", _StringStdin(json.dumps({"session_id": "s"})))

    def boom(input_data):
        raise RuntimeError("simulated dispatcher failure")

    monkeypatch.setattr(stop, "dispatch", boom)
    rc = stop.main()
    captured = capsys.readouterr()
    assert rc == 0
    response = json.loads(captured.out)
    assert response["status"] == "error"
    assert "simulated dispatcher failure" in response["error"]
    assert "ERROR" in captured.err


# ---------------------------------------------------------------------------
# Bundle write robustness
# ---------------------------------------------------------------------------


def test_no_leftover_tmp_file_in_bundle(stop, fake_repo, monkeypatch):
    """The atomic-write pattern's .tmp staging file must always be cleaned up."""
    monkeypatch.chdir(fake_repo)
    _write_pending(fake_repo, _valid_pending_ledger("s", "t"))
    stop.dispatch({"session_id": "s"})
    bundle_dir = fake_repo / ".claude" / "popkit" / "verifier-bundles" / "s" / "t"
    leftovers = list(bundle_dir.glob("*.tmp"))
    assert leftovers == []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _StringStdin:
    def __init__(self, value: str) -> None:
        self._value = value

    def read(self) -> str:
        return self._value
