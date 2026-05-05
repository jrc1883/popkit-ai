#!/usr/bin/env python3
"""
Tests for ``checkpoint_writer.py`` (Plan v4.2 Phase 1a-i).

The writer is the canonical ``/checkpoint`` slash command back-end. The
tests pin three things:

1. **Valid ledgers round-trip.** Required fields produce a pending ledger
   on disk with ``status: 'normal'``, ``schema_version: 1``, generated
   UUIDs, and the user-supplied content unchanged.
2. **Schema mismatches raise CheckpointError.** Every required-field /
   enum / type rule from claim-ledger.schema.json fails closed.
3. **The pending file is the canonical handoff to the Stop dispatcher.**
   Repeated /checkpoint calls in one turn replace the pending file
   atomically (last-writer-wins is the documented contract).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def load_writer_module():
    """Load checkpoint_writer.py without making it a package."""
    here = Path(__file__).resolve().parents[1]
    writer_path = here / "scripts" / "checkpoint_writer.py"
    spec = importlib.util.spec_from_file_location("checkpoint_writer", writer_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def writer():
    return load_writer_module()


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    """Create a minimal directory tree with a ``.git`` marker."""
    (tmp_path / ".git").mkdir()
    return tmp_path


def _minimal_payload(**overrides) -> dict:
    base = {
        "lane_id": "popkit-docs",
        "stage": "code",
        "intent": "close round-8 P2 finding",
        "changed_files": [{"path": "scripts/loader.py", "added": 12, "removed": 3}],
        "acceptance_claims": [
            "writer rejects non-string inputs",
            "loader returns LaneManifestError on unhashable enum value",
        ],
        "next_action": "verify",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_valid_ledger_writes_pending_file(writer, fake_repo):
    target, ledger = writer.write_checkpoint(_minimal_payload(), repo_root=fake_repo)
    assert target == fake_repo / ".claude" / "popkit" / "pending-claim-ledger.json"
    on_disk = json.loads(target.read_text(encoding="utf-8"))
    assert on_disk == ledger
    assert on_disk["schema_version"] == 1
    assert on_disk["status"] == "normal"
    assert on_disk["lane_id"] == "popkit-docs"
    assert on_disk["intent"] == "close round-8 P2 finding"
    assert on_disk["acceptance_claims"][0] == "writer rejects non-string inputs"


def test_session_and_turn_ids_are_uuids_when_unspecified(writer, fake_repo):
    _, ledger = writer.write_checkpoint(_minimal_payload(), repo_root=fake_repo)
    # uuid4 strings are 36 chars with dashes at fixed positions
    for field in ("session_id", "turn_id"):
        v = ledger[field]
        assert isinstance(v, str)
        assert len(v) == 36
        assert v[8] == "-" and v[13] == "-" and v[18] == "-" and v[23] == "-"


def test_explicit_ids_round_trip(writer, fake_repo):
    _, ledger = writer.write_checkpoint(
        _minimal_payload(),
        repo_root=fake_repo,
        session_id="sess-xyz",
        turn_id="turn-abc",
    )
    assert ledger["session_id"] == "sess-xyz"
    assert ledger["turn_id"] == "turn-abc"


def test_repeated_checkpoint_replaces_pending_atomically(writer, fake_repo):
    """Round 5 #4: the writer's contract is last-writer-wins."""
    target, first = writer.write_checkpoint(
        _minimal_payload(intent="first checkpoint"), repo_root=fake_repo
    )
    target2, second = writer.write_checkpoint(
        _minimal_payload(intent="second checkpoint"), repo_root=fake_repo
    )
    assert target == target2
    on_disk = json.loads(target2.read_text(encoding="utf-8"))
    assert on_disk["intent"] == "second checkpoint"
    # No leftover .tmp file from the atomic replace.
    assert not (target.parent / "pending-claim-ledger.json.tmp").exists()
    # Each checkpoint generates a fresh turn_id when none is supplied.
    assert first["turn_id"] != second["turn_id"]


def test_optional_fields_round_trip(writer, fake_repo):
    payload = _minimal_payload(
        tests_run=[{"name": "test_loader.py", "passed": 104, "failed": 0}],
        deterministic_gates_observed={"typecheck": "pass", "lint": "skip"},
        compliance_touch=["none", "schema"],
        known_gaps=["redaction fixtures land in 1a-iv"],
    )
    _, ledger = writer.write_checkpoint(payload, repo_root=fake_repo)
    assert ledger["tests_run"][0]["passed"] == 104
    assert ledger["deterministic_gates_observed"]["typecheck"] == "pass"
    assert ledger["compliance_touch"] == ["none", "schema"]
    assert ledger["known_gaps"][0].startswith("redaction fixtures")


# ---------------------------------------------------------------------------
# Validation failure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field",
    ["lane_id", "stage", "intent", "changed_files", "acceptance_claims", "next_action"],
)
def test_missing_required_field_raises(writer, fake_repo, field):
    payload = _minimal_payload()
    del payload[field]
    with pytest.raises(writer.CheckpointError) as exc:
        writer.write_checkpoint(payload, repo_root=fake_repo)
    assert field in str(exc.value)


@pytest.mark.parametrize("value", ["plan-stage", "PLAN", "review", 123, None, [], {}])
def test_invalid_stage_rejected(writer, fake_repo, value):
    payload = _minimal_payload(stage=value)
    with pytest.raises(writer.CheckpointError) as exc:
        writer.write_checkpoint(payload, repo_root=fake_repo)
    assert "stage" in str(exc.value)


@pytest.mark.parametrize("value", ["maybe", "ship-it", 0, None, [], {}])
def test_invalid_next_action_rejected(writer, fake_repo, value):
    payload = _minimal_payload(next_action=value)
    with pytest.raises(writer.CheckpointError) as exc:
        writer.write_checkpoint(payload, repo_root=fake_repo)
    assert "next_action" in str(exc.value)


def test_empty_intent_rejected(writer, fake_repo):
    with pytest.raises(writer.CheckpointError) as exc:
        writer.write_checkpoint(_minimal_payload(intent=""), repo_root=fake_repo)
    assert "intent" in str(exc.value)


def test_acceptance_claims_must_be_array_of_non_empty_strings(writer, fake_repo):
    with pytest.raises(writer.CheckpointError) as exc:
        writer.write_checkpoint(
            _minimal_payload(acceptance_claims=["", "valid claim"]),
            repo_root=fake_repo,
        )
    assert "acceptance_claims" in str(exc.value)


def test_changed_files_path_must_be_non_empty_string(writer, fake_repo):
    with pytest.raises(writer.CheckpointError) as exc:
        writer.write_checkpoint(
            _minimal_payload(changed_files=[{"path": ""}]), repo_root=fake_repo
        )
    assert "path" in str(exc.value)


def test_changed_files_added_must_be_non_negative_int(writer, fake_repo):
    """Bool is an int subclass in Python; reject explicitly."""
    with pytest.raises(writer.CheckpointError):
        writer.write_checkpoint(
            _minimal_payload(changed_files=[{"path": "a.py", "added": True}]),
            repo_root=fake_repo,
        )
    with pytest.raises(writer.CheckpointError):
        writer.write_checkpoint(
            _minimal_payload(changed_files=[{"path": "a.py", "added": -1}]),
            repo_root=fake_repo,
        )


def test_deterministic_gates_observed_value_must_be_enum(writer, fake_repo):
    with pytest.raises(writer.CheckpointError) as exc:
        writer.write_checkpoint(
            _minimal_payload(deterministic_gates_observed={"typecheck": "ok"}),
            repo_root=fake_repo,
        )
    assert "deterministic_gates_observed" in str(exc.value)


def test_compliance_touch_value_must_be_enum(writer, fake_repo):
    with pytest.raises(writer.CheckpointError) as exc:
        writer.write_checkpoint(
            _minimal_payload(compliance_touch=["bogus"]), repo_root=fake_repo
        )
    assert "compliance_touch" in str(exc.value)


def test_top_level_must_be_object(writer, fake_repo):
    with pytest.raises(writer.CheckpointError) as exc:
        writer.write_checkpoint(["not", "an", "object"], repo_root=fake_repo)
    assert "object" in str(exc.value)


def test_repo_root_detection_walks_up(writer, tmp_path):
    """find_repo_root walks parent dirs looking for .git/."""
    (tmp_path / ".git").mkdir()
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    assert writer.find_repo_root(start=nested) == tmp_path


def test_repo_root_detection_raises_when_not_in_repo(writer, tmp_path):
    with pytest.raises(writer.CheckpointError) as exc:
        writer.find_repo_root(start=tmp_path)
    assert "could not locate" in str(exc.value)


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_cli_main_writes_pending_and_returns_zero(
    writer, fake_repo, monkeypatch, capsys
):
    """End-to-end: stdin JSON → exit 0 → stdout reports the path."""
    payload_json = json.dumps(_minimal_payload())
    monkeypatch.setattr("sys.stdin", _StringStdin(payload_json))
    rc = writer.main(["--repo-root", str(fake_repo)])
    captured = capsys.readouterr()
    assert rc == 0
    out = json.loads(captured.out)
    assert out["ok"] is True
    assert out["path"].endswith("pending-claim-ledger.json")


def test_cli_main_invalid_payload_returns_two(writer, fake_repo, monkeypatch, capsys):
    payload = _minimal_payload()
    del payload["lane_id"]
    monkeypatch.setattr("sys.stdin", _StringStdin(json.dumps(payload)))
    rc = writer.main(["--repo-root", str(fake_repo)])
    captured = capsys.readouterr()
    assert rc == 2
    err = json.loads(captured.err)
    assert err["ok"] is False
    assert "lane_id" in err["error"]


def test_cli_main_invalid_json_returns_two(writer, fake_repo, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", _StringStdin("{not json}"))
    rc = writer.main(["--repo-root", str(fake_repo)])
    captured = capsys.readouterr()
    assert rc == 2
    err = json.loads(captured.err)
    assert err["ok"] is False
    assert "invalid JSON" in err["error"]


def test_cli_main_empty_input_returns_two(writer, fake_repo, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", _StringStdin(""))
    rc = writer.main(["--repo-root", str(fake_repo)])
    captured = capsys.readouterr()
    assert rc == 2
    assert "empty input" in captured.err


class _StringStdin:
    """Minimal stdin shim so monkeypatch.setattr('sys.stdin', ...) works."""

    def __init__(self, value: str) -> None:
        self._value = value

    def read(self) -> str:
        return self._value
