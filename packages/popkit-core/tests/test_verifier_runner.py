#!/usr/bin/env python3
"""
Tests for ``hooks/verifier-runner-cli.py`` — Phase 1a-iii.

Pin five things:

1. **Hard-fail contract.** Missing / unparseable / structurally-invalid
   ledger.json produces a verdict.json with verdict='human' and
   reason='claim_ledger_missing_or_invalid' per Plan v4.2 Layer 1.
2. **Stop-dispatcher stub recognized.** A ledger with status='missing'
   (the dispatcher's intentional stub) gets the same human verdict.
3. **Schema-or-die write.** validate_verdict refuses to persist a
   malformed verdict; write_verdict raises VerdictWriteError.
4. **Deferred Codex path.** Valid status='normal' ledgers exit cleanly
   without writing a verdict (the Codex invocation lands in a future
   PR alongside redaction).
5. **Bundle-dir errors are structured.** Missing or non-directory
   bundle paths produce structured CLI errors with non-zero exit
   codes — never raw tracebacks.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def load_runner_module():
    here = Path(__file__).resolve().parents[1]
    runner_path = here / "hooks" / "verifier-runner-cli.py"
    spec = importlib.util.spec_from_file_location("verifier_runner", runner_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def runner():
    return load_runner_module()


@pytest.fixture()
def bundle_dir(tmp_path: Path) -> Path:
    """Create a bundle directory at the per-turn path shape the
    dispatcher would produce."""
    d = tmp_path / "verifier-bundles" / "sess-1" / "turn-1"
    d.mkdir(parents=True)
    return d


def _valid_ledger(**overrides) -> dict:
    base = {
        "schema_version": 1,
        "status": "normal",
        "session_id": "sess-1",
        "turn_id": "turn-1",
        "lane_id": "popkit-docs",
        "stage": "code",
        "intent": "land Phase 1a-iii runner",
        "changed_files": [{"path": "hooks/verifier-runner-cli.py"}],
        "acceptance_claims": ["runner fast-fails on missing ledgers"],
        "next_action": "verify",
    }
    base.update(overrides)
    return base


def _write_ledger(bundle: Path, ledger) -> Path:
    ledger_path = bundle / "ledger.json"
    if isinstance(ledger, str):
        ledger_path.write_text(ledger, encoding="utf-8")
    else:
        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    return ledger_path


# ---------------------------------------------------------------------------
# Bundle-dir validation
# ---------------------------------------------------------------------------


def test_missing_bundle_dir_returns_exit_2(runner, tmp_path):
    response = runner.run(tmp_path / "does-not-exist")
    assert response["ok"] is False
    assert response["exit"] == 2
    assert "bundle_not_found" in response["error"]


def test_bundle_path_is_file_returns_exit_2(runner, tmp_path):
    f = tmp_path / "not-a-dir.json"
    f.write_text("{}", encoding="utf-8")
    response = runner.run(f)
    assert response["ok"] is False
    assert response["exit"] == 2
    assert "bundle_not_directory" in response["error"]


# ---------------------------------------------------------------------------
# Hard-fail contract: missing / invalid ledger → human verdict
# ---------------------------------------------------------------------------


def test_missing_ledger_writes_human_verdict(runner, bundle_dir):
    response = runner.run(bundle_dir)
    assert response["ok"] is True
    assert response["verdict"] == "human"
    assert response["reason"] == "claim_ledger_missing_or_invalid"
    assert response["fast_fail_reason"] == "ledger_json_not_found"
    verdict = json.loads(Path(response["verdict_path"]).read_text(encoding="utf-8"))
    assert verdict["schema_version"] == 1
    assert verdict["verdict"] == "human"
    assert verdict["reason"] == "claim_ledger_missing_or_invalid"
    assert verdict["lane_id"] == "unknown"
    # Falls back to the bundle dir leaf when the ledger doesn't exist.
    assert verdict["ledger_turn_id"] == "turn-1"
    assert "Ledger fast-fail" in verdict["rationale"]


def test_corrupt_json_ledger_writes_human_verdict(runner, bundle_dir):
    _write_ledger(bundle_dir, "{not valid json")
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert response["reason"] == "claim_ledger_missing_or_invalid"
    assert response["fast_fail_reason"].startswith("ledger_invalid_json")


def test_non_object_top_level_writes_human_verdict(runner, bundle_dir):
    _write_ledger(bundle_dir, "[1, 2, 3]")
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert response["fast_fail_reason"] == "ledger_not_object"


def test_wrong_schema_version_writes_human_verdict(runner, bundle_dir):
    bad = _valid_ledger()
    bad["schema_version"] = 2
    _write_ledger(bundle_dir, bad)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert response["fast_fail_reason"].startswith("ledger_unsupported_schema_version")


@pytest.mark.parametrize(
    "field",
    [
        "turn_id",
        "session_id",
        "lane_id",
        "stage",
        "intent",
        "changed_files",
        "acceptance_claims",
        "next_action",
    ],
)
def test_missing_required_field_writes_human_verdict(runner, bundle_dir, field):
    bad = _valid_ledger()
    del bad[field]
    _write_ledger(bundle_dir, bad)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert field in response["fast_fail_reason"]


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("status", []),
        ("status", {}),
        ("stage", []),
        ("stage", {}),
        ("next_action", []),
        ("next_action", 0),
        ("turn_id", ""),
        ("turn_id", 123),
        ("intent", ""),
    ],
)
def test_invalid_field_value_writes_human_verdict(runner, bundle_dir, field, bad_value):
    """Round-12 P2 sibling: type-check before set membership prevents
    the runner from crashing on unhashable enum values."""
    bad = _valid_ledger()
    bad[field] = bad_value
    _write_ledger(bundle_dir, bad)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert response["reason"] == "claim_ledger_missing_or_invalid"


# ---------------------------------------------------------------------------
# Dispatcher stub: status='missing' ledger
# ---------------------------------------------------------------------------


def test_status_missing_stub_writes_human_verdict(runner, bundle_dir):
    """The Stop dispatcher writes a status='missing' stub when /checkpoint
    wasn't called. The runner must still produce a human verdict — but
    the rationale should reference the dispatcher rather than a
    structural error."""
    stub = {
        "schema_version": 1,
        "status": "missing",
        "reason": "no_checkpoint_called",
        "session_id": "sess-1",
        "turn_id": "turn-1",
        "lane_id": "stub-lane",
        "stage": "code",
        "intent": "(no /checkpoint called this turn)",
        "changed_files": [],
        "acceptance_claims": [],
        "next_action": "needs-review",
    }
    _write_ledger(bundle_dir, stub)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert response["reason"] == "claim_ledger_missing_or_invalid"
    assert response["fast_fail_reason"] == "ledger_status_missing"
    verdict = json.loads(Path(response["verdict_path"]).read_text(encoding="utf-8"))
    # Stub-aware rationale: references dispatcher + the upstream reason.
    assert "Stop dispatcher" in verdict["rationale"]
    assert "no_checkpoint_called" in verdict["rationale"]
    # Stub-aware identifiers: real lane/turn from the stub, not "unknown".
    assert verdict["lane_id"] == "stub-lane"
    assert verdict["ledger_turn_id"] == "turn-1"


# ---------------------------------------------------------------------------
# Deferred-Codex path: valid normal ledger
# ---------------------------------------------------------------------------


def test_valid_ledger_defers_without_writing_verdict(runner, bundle_dir):
    """Valid status='normal' ledger means the Codex invocation can
    proceed in a future PR. This PR ships the runner shell only; the
    runner exits cleanly without writing a verdict."""
    _write_ledger(bundle_dir, _valid_ledger())
    response = runner.run(bundle_dir)
    assert response["ok"] is True
    assert response["deferred"] is True
    assert response["deferred_reason"] == "codex_invocation_not_yet_implemented"
    assert response["verdict_path"] is None
    assert response["ledger_lane_id"] == "popkit-docs"
    assert response["ledger_turn_id"] == "turn-1"
    # No verdict.json got written.
    assert not (bundle_dir / "verdict.json").exists()


# ---------------------------------------------------------------------------
# Schema-or-die: validate_verdict + write_verdict
# ---------------------------------------------------------------------------


def test_validate_verdict_accepts_well_formed_human(runner):
    v = runner.make_human_verdict(
        lane_id="x",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    assert runner.validate_verdict(v) is None


def test_validate_verdict_rejects_unknown_verdict_value(runner):
    v = runner.make_human_verdict(
        lane_id="x",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    v["verdict"] = "approved"
    assert "verdict_unknown_value" in runner.validate_verdict(v)


def test_validate_verdict_rejects_human_with_unknown_reason(runner):
    v = runner.make_human_verdict(
        lane_id="x",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    v["reason"] = "bogus_reason"
    assert "verdict_unknown_reason" in runner.validate_verdict(v)


def test_validate_verdict_rejects_wrong_schema_version(runner):
    v = runner.make_human_verdict(
        lane_id="x",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    v["schema_version"] = 2
    assert "verdict_unsupported_schema_version" in runner.validate_verdict(v)


def test_validate_verdict_rejects_empty_lane_id(runner):
    v = runner.make_human_verdict(
        lane_id="",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    err = runner.validate_verdict(v)
    assert err is not None and "lane_id" in err


def test_validate_verdict_finding_severity_must_be_enum(runner):
    v = runner.make_human_verdict(
        lane_id="x",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    v["findings"] = [{"severity": "critical", "message": "boom"}]
    assert "severity_unknown" in runner.validate_verdict(v)


def test_validate_verdict_finding_message_must_be_non_empty(runner):
    v = runner.make_human_verdict(
        lane_id="x",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    v["findings"] = [{"severity": "high", "message": ""}]
    assert "message_must_be_non_empty_string" in runner.validate_verdict(v)


@pytest.mark.parametrize(
    "field,bad_value,expected_substr",
    [
        ("claim_id", "first", "claim_id_not_integer"),
        ("claim_id", True, "claim_id_not_integer"),
        ("claim_id", -1, "claim_id_negative"),
        ("file", "", "file_must_be_non_empty_string"),
        ("file", 42, "file_must_be_non_empty_string"),
        ("line", "10", "line_not_integer"),
        ("line", True, "line_not_integer"),
        ("line", 0, "line_below_one"),
        ("line", -5, "line_below_one"),
    ],
)
def test_validate_verdict_optional_finding_fields(
    runner, field, bad_value, expected_substr
):
    """Optional schema fields on findings still get type-guarded so the
    future Codex-driven path can't sneak malformed data past the
    schema-or-die write gate."""
    v = runner.make_human_verdict(
        lane_id="x",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    finding = {"severity": "high", "message": "boom", field: bad_value}
    v["findings"] = [finding]
    err = runner.validate_verdict(v)
    assert err is not None and expected_substr in err


def test_validate_verdict_optional_finding_fields_accept_valid_values(runner):
    v = runner.make_human_verdict(
        lane_id="x",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    v["findings"] = [
        {
            "severity": "high",
            "message": "structural finding",
            "claim_id": 0,
            "file": "apps/shprd/src/x.ts",
            "line": 1,
            "suggested_action": "block",
        }
    ]
    assert runner.validate_verdict(v) is None


def test_write_verdict_refuses_malformed(runner, bundle_dir):
    bad = {"schema_version": 1, "verdict": "approved"}
    with pytest.raises(runner.VerdictWriteError):
        runner.write_verdict(bad, bundle_dir=bundle_dir)
    assert not (bundle_dir / "verdict.json").exists()


# ---------------------------------------------------------------------------
# Round-13 P1: deep ledger validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "changed_files",
    [
        [{}],  # missing path
        [{"path": 123}],  # non-string path
        [{"path": ""}],  # empty path
        [{"path": "a.py", "added": -1}],  # negative
        [{"path": "a.py", "added": True}],  # bool
        [{"path": "a.py", "removed": "lots"}],  # non-int
        [{"not_an_object": True}],  # missing path
        ["not-a-dict"],  # entry not object
    ],
)
def test_runner_rejects_invalid_changed_files_entries(
    runner, bundle_dir, changed_files
):
    bad = _valid_ledger(changed_files=changed_files)
    _write_ledger(bundle_dir, bad)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert response["reason"] == "claim_ledger_missing_or_invalid"
    assert "changed_files" in response["fast_fail_reason"]


@pytest.mark.parametrize(
    "claims",
    [
        [123],  # non-string
        [""],  # empty
        ["valid", 42],  # one bad
        [{"not": "string"}],  # dict instead of string
        [None],
    ],
)
def test_runner_rejects_invalid_acceptance_claims(runner, bundle_dir, claims):
    bad = _valid_ledger(acceptance_claims=claims)
    _write_ledger(bundle_dir, bad)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert "acceptance_claims" in response["fast_fail_reason"]


def test_runner_rejects_invalid_tests_run(runner, bundle_dir):
    bad = _valid_ledger(
        tests_run=[{"name": "test_x.py", "passed": -1}],
    )
    _write_ledger(bundle_dir, bad)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert "tests_run" in response["fast_fail_reason"]


def test_runner_rejects_tests_run_missing_name(runner, bundle_dir):
    bad = _valid_ledger(tests_run=[{"passed": 5}])
    _write_ledger(bundle_dir, bad)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert "tests_run" in response["fast_fail_reason"]


def test_runner_rejects_invalid_deterministic_gates_observed(runner, bundle_dir):
    bad = _valid_ledger(deterministic_gates_observed={"typecheck": "ok"})
    _write_ledger(bundle_dir, bad)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert "deterministic_gates_observed" in response["fast_fail_reason"]


def test_runner_rejects_deterministic_gates_observed_not_object(runner, bundle_dir):
    bad = _valid_ledger(deterministic_gates_observed=["not", "an", "object"])
    _write_ledger(bundle_dir, bad)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert "deterministic_gates_observed" in response["fast_fail_reason"]


def test_runner_rejects_invalid_compliance_touch(runner, bundle_dir):
    bad = _valid_ledger(compliance_touch=["bogus"])
    _write_ledger(bundle_dir, bad)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert "compliance_touch" in response["fast_fail_reason"]


def test_runner_rejects_invalid_known_gaps(runner, bundle_dir):
    bad = _valid_ledger(known_gaps=[123])
    _write_ledger(bundle_dir, bad)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert "known_gaps" in response["fast_fail_reason"]


# ---------------------------------------------------------------------------
# Round-13 P2: schema_version bool acceptance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bool_value", [True, False])
def test_runner_rejects_bool_schema_version_in_ledger(runner, bundle_dir, bool_value):
    """``True == 1`` in Python; the runner must reject bools explicitly so
    a malformed ledger with ``schema_version: true`` can't slip through."""
    bad = _valid_ledger()
    bad["schema_version"] = bool_value
    _write_ledger(bundle_dir, bad)
    response = runner.run(bundle_dir)
    assert response["verdict"] == "human"
    assert response["fast_fail_reason"].startswith("ledger_schema_version_not_integer")


def test_validate_verdict_rejects_bool_schema_version(runner):
    v = runner.make_human_verdict(
        lane_id="x",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    v["schema_version"] = True
    assert "verdict_schema_version_not_integer" in runner.validate_verdict(v)


# ---------------------------------------------------------------------------
# Round-13 P2: malformed missing-stub still produces a verdict
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("lane_id", []),
        ("lane_id", {}),
        ("lane_id", 123),
        ("lane_id", ""),
        ("turn_id", []),
        ("turn_id", {}),
        ("turn_id", 0),
        ("turn_id", ""),
    ],
)
def test_malformed_missing_stub_still_writes_human_verdict(
    runner, bundle_dir, field, bad_value
):
    """Round-13 P2: the dispatcher's missing-stub path used raw
    ledger.get(...) values for lane_id/turn_id. A malformed stub with
    a non-string identifier got rejected by validate_verdict's schema-
    or-die guard, leaving the bundle with NO verdict file. The runner
    must route through the safe helpers so a malformed stub still
    produces a verdict."""
    stub = {
        "schema_version": 1,
        "status": "missing",
        "reason": "no_checkpoint_called",
        "session_id": "s",
        "turn_id": "stub-t",
        "lane_id": "stub-lane",
        "stage": "code",
        "intent": "(stub)",
        "changed_files": [],
        "acceptance_claims": [],
        "next_action": "needs-review",
    }
    stub[field] = bad_value
    _write_ledger(bundle_dir, stub)
    response = runner.run(bundle_dir)
    assert response["ok"] is True
    assert response["verdict"] == "human"
    assert response["reason"] == "claim_ledger_missing_or_invalid"
    assert (bundle_dir / "verdict.json").exists()


# ---------------------------------------------------------------------------
# Round-13 P2: findings[].file repo-relative contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_path",
    [
        "C:/secret.txt",
        "c:/secret.txt",
        "C:secret.txt",
        "C:\\secret.txt",
        "/etc/passwd",
        "//server/share/file.py",
        "../outside.py",
        "apps/../../../etc/passwd",
        "packages\\popkit-core\\x.py",
    ],
)
def test_validate_verdict_finding_file_must_be_repo_relative(runner, bad_path):
    """Round-13 P2: verifier-result.schema.json says findings[].file is
    repo-root-relative with forward-slash separators. Apply the same
    rules checkpoint_writer enforces on changed_files[].path."""
    v = runner.make_human_verdict(
        lane_id="x",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    v["findings"] = [{"severity": "high", "message": "boom", "file": bad_path}]
    err = runner.validate_verdict(v)
    assert err is not None
    assert "file" in err
    assert "must_use_forward_slashes" in err or "must_be_repo_relative" in err


@pytest.mark.parametrize(
    "good_path",
    [
        "apps/shprd/src/Foo.tsx",
        "packages/popkit-core/scripts/checkpoint_writer.py",
        "README.md",
        "./relative-with-dot.txt",
    ],
)
def test_validate_verdict_finding_file_accepts_repo_relative(runner, good_path):
    v = runner.make_human_verdict(
        lane_id="x",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    v["findings"] = [{"severity": "high", "message": "boom", "file": good_path}]
    assert runner.validate_verdict(v) is None


def test_write_verdict_no_leftover_tmp(runner, bundle_dir):
    v = runner.make_human_verdict(
        lane_id="x",
        ledger_turn_id="t",
        reason="claim_ledger_missing_or_invalid",
        rationale="test",
    )
    runner.write_verdict(v, bundle_dir=bundle_dir)
    leftovers = list(bundle_dir.glob("*.tmp"))
    assert leftovers == []


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_cli_main_missing_bundle_returns_two(runner, tmp_path, capsys):
    rc = runner.main(["--bundle", str(tmp_path / "ghost")])
    captured = capsys.readouterr()
    assert rc == 2
    out = json.loads(captured.out)
    assert out["ok"] is False
    assert "bundle_not_found" in out["error"]


def test_cli_main_human_verdict_returns_zero(runner, bundle_dir, capsys):
    """Hard-fail path is a successful runner outcome (exit 0); the
    verdict file is the dispatcher's signal that this turn requires a
    human."""
    rc = runner.main(["--bundle", str(bundle_dir)])
    captured = capsys.readouterr()
    assert rc == 0
    out = json.loads(captured.out)
    assert out["ok"] is True
    assert out["verdict"] == "human"
    assert out["reason"] == "claim_ledger_missing_or_invalid"


def test_cli_main_deferred_returns_zero(runner, bundle_dir, capsys):
    _write_ledger(bundle_dir, _valid_ledger())
    rc = runner.main(["--bundle", str(bundle_dir)])
    captured = capsys.readouterr()
    assert rc == 0
    out = json.loads(captured.out)
    assert out["ok"] is True
    assert out["deferred"] is True
    assert out["verdict_path"] is None
