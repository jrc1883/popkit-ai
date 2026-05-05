#!/usr/bin/env python3
"""
Tests for the lane manifest loader.

Round-5 directive (Plan v4.2 closure trace #5):

    JSON Schema default is annotation; the loader applies it; tests
    prove it.

These tests prove four things:
1. Default injection works for non-compliance lanes.
2. Compliance lanes ENFORCE on_verifier_unreachable=closed_human at load time.
3. Non-compliance lanes can opt INTO closed_human for higher trust.
4. Other failure modes (missing fields, bad enums, shared_ownership without
   priority, malformed file_ownership) raise clean errors.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def load_loader_module():
    """Load lane_manifest_loader.py without making it a package."""
    loader_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "lane_manifest_loader.py"
    )
    spec = importlib.util.spec_from_file_location("lane_manifest_loader", loader_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def loader():
    return load_loader_module()


def _write_manifest(tmp_path: Path, manifest: dict) -> Path:
    """Write a JSON manifest (loader handles YAML or JSON) to a temp path."""
    path = tmp_path / "lanes.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _minimal_lane(**overrides) -> dict:
    """Return a minimum-viable lane with all required fields."""
    base = {
        "id": "test-lane",
        "repo": "owner/repo",
        "worktree": "/tmp/repo-worktree",
        "branch": "feat/test",
        "base": "origin/main",
        "file_ownership": ["src/**"],
        "verifier_profile": "docs",
        "compliance_class": "none",
        "max_rounds": 5,
        "merge_gate": "auto",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Default injection (non-compliance)
# ---------------------------------------------------------------------------


def test_default_injection_for_non_compliance_lane(loader, tmp_path):
    """compliance_class='none' + no on_verifier_unreachable -> open_with_warning."""
    path = _write_manifest(
        tmp_path, {"version": 1, "lanes": [_minimal_lane(compliance_class="none")]}
    )
    result = loader.load_lane_manifest(path)
    lane = result.manifest["lanes"][0]
    assert lane["on_verifier_unreachable"] == "open_with_warning"
    assert lane["auto_continuation_class"] == "none"


def test_default_injection_for_schema_class(loader, tmp_path):
    """compliance_class='schema' is non-compliance for routing purposes."""
    path = _write_manifest(
        tmp_path, {"version": 1, "lanes": [_minimal_lane(compliance_class="schema")]}
    )
    result = loader.load_lane_manifest(path)
    lane = result.manifest["lanes"][0]
    assert lane["on_verifier_unreachable"] == "open_with_warning"


# ---------------------------------------------------------------------------
# Compliance lane enforcement (must reject open_with_warning at load time)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "compliance_class", ["audit", "auth", "child-data", "ferpa", "coppa"]
)
def test_compliance_lane_rejects_open_with_warning(loader, tmp_path, compliance_class):
    """Compliance lanes cannot opt out of closed_human."""
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(
                    compliance_class=compliance_class,
                    on_verifier_unreachable="open_with_warning",
                )
            ],
        },
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    msg = str(exc_info.value)
    assert "compliance_class" in msg
    assert "closed_human" in msg
    assert "open_with_warning" in msg


@pytest.mark.parametrize(
    "compliance_class", ["audit", "auth", "child-data", "ferpa", "coppa"]
)
def test_compliance_lane_default_is_closed_human(loader, tmp_path, compliance_class):
    """Compliance lanes without on_verifier_unreachable get closed_human injected."""
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [_minimal_lane(compliance_class=compliance_class)],
        },
    )
    result = loader.load_lane_manifest(path)
    lane = result.manifest["lanes"][0]
    assert lane["on_verifier_unreachable"] == "closed_human"
    assert lane["auto_continuation_class"] == "human"


def test_compliance_lane_explicit_closed_human_accepted(loader, tmp_path):
    """Explicit closed_human on a compliance lane is fine (it matches the rule)."""
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(
                    compliance_class="child-data",
                    on_verifier_unreachable="closed_human",
                )
            ],
        },
    )
    result = loader.load_lane_manifest(path)
    assert result.manifest["lanes"][0]["on_verifier_unreachable"] == "closed_human"


def test_compliance_lane_rejects_non_human_auto_continuation(loader, tmp_path):
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(
                    compliance_class="audit", auto_continuation_class="feedback"
                )
            ],
        },
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "auto_continuation_class" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Non-compliance opt-in to higher trust
# ---------------------------------------------------------------------------


def test_non_compliance_can_opt_into_closed_human(loader, tmp_path):
    """Operator can choose closed_human on a non-compliance lane (more cautious)."""
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(
                    compliance_class="none",
                    on_verifier_unreachable="closed_human",
                )
            ],
        },
    )
    result = loader.load_lane_manifest(path)
    assert result.manifest["lanes"][0]["on_verifier_unreachable"] == "closed_human"


# ---------------------------------------------------------------------------
# Other failure modes
# ---------------------------------------------------------------------------


def test_unsupported_schema_version_rejected(loader, tmp_path):
    path = _write_manifest(tmp_path, {"version": 2, "lanes": [_minimal_lane()]})
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "unsupported schema_version" in str(exc_info.value)


def test_missing_required_lane_field_rejected(loader, tmp_path):
    lane = _minimal_lane()
    del lane["compliance_class"]
    path = _write_manifest(tmp_path, {"version": 1, "lanes": [lane]})
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "compliance_class" in str(exc_info.value)


def test_unknown_compliance_class_rejected(loader, tmp_path):
    path = _write_manifest(
        tmp_path,
        {"version": 1, "lanes": [_minimal_lane(compliance_class="bogus")]},
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "compliance_class" in str(exc_info.value)


def test_shared_ownership_requires_priority(loader, tmp_path):
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [_minimal_lane(shared_ownership=True)],
        },
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "priority" in str(exc_info.value)


def test_duplicate_lane_id_rejected(loader, tmp_path):
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(id="dup"),
                _minimal_lane(id="dup", branch="feat/other"),
            ],
        },
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "duplicate lane id" in str(exc_info.value)


def test_max_rounds_bounds_enforced(loader, tmp_path):
    path = _write_manifest(
        tmp_path, {"version": 1, "lanes": [_minimal_lane(max_rounds=0)]}
    )
    with pytest.raises(loader.LaneManifestError):
        loader.load_lane_manifest(path)
    path = _write_manifest(
        tmp_path, {"version": 1, "lanes": [_minimal_lane(max_rounds=21)]}
    )
    with pytest.raises(loader.LaneManifestError):
        loader.load_lane_manifest(path)


def test_empty_file_ownership_rejected(loader, tmp_path):
    path = _write_manifest(
        tmp_path, {"version": 1, "lanes": [_minimal_lane(file_ownership=[])]}
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "file_ownership" in str(exc_info.value)


@pytest.mark.parametrize(
    "absolute_glob",
    [
        "/abs/path/**",
        "C:/repo/apps/**",
        "c:/repo/apps/**",
        "C:\\repo\\apps\\**",
        "//server/share/**",
    ],
)
def test_absolute_path_in_file_ownership_rejected(loader, tmp_path, absolute_glob):
    """Round-8 P1 #2: absolute file_ownership globs are a safety hazard.

    Lane file_ownership is the safety boundary for parallel work. An
    absolute glob like ``C:/repo/apps/**`` describes the same tree as
    ``apps/**`` but lanes-doctor's overlap detector can't canonicalize
    across that gap, so two lanes with those values would silently bypass
    overlap detection. The loader must reject absolute paths so manifest
    authors fix them to repo-relative form.
    """
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [_minimal_lane(file_ownership=[absolute_glob])],
        },
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    msg = str(exc_info.value)
    assert "file_ownership" in msg
    assert "absolute" in msg.lower() or "repo-relative" in msg.lower()


def test_missing_manifest_file_rejected(loader, tmp_path):
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(tmp_path / "nonexistent.yml")
    assert "not found" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Type-checking required string fields (Codex round-7 P1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("repo", 123),
        ("repo", ["owner/repo"]),
        ("repo", ""),
        ("worktree", ["not-string"]),
        ("worktree", 42),
        ("branch", 42),
        ("branch", None),
        ("base", False),
        ("verifier_profile", False),
        ("verifier_profile", {"name": "docs"}),
        ("id", 999),
        ("id", ""),
    ],
)
def test_required_string_field_type_checked(loader, tmp_path, field, bad_value):
    """Round-7 P1: loader must reject non-string types in required string fields."""
    lane = _minimal_lane()
    lane[field] = bad_value
    path = _write_manifest(tmp_path, {"version": 1, "lanes": [lane]})
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert field in str(exc_info.value)


def test_max_rounds_bool_rejected(loader, tmp_path):
    """`True`/`False` are int subclasses in Python; loader must reject them."""
    path = _write_manifest(
        tmp_path, {"version": 1, "lanes": [_minimal_lane(max_rounds=True)]}
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "integer" in str(exc_info.value).lower()


def test_shared_ownership_must_be_bool(loader, tmp_path):
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [_minimal_lane(shared_ownership="yes", priority=1)],
        },
    )
    with pytest.raises(loader.LaneManifestError):
        loader.load_lane_manifest(path)


def test_priority_must_be_int(loader, tmp_path):
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [_minimal_lane(shared_ownership=True, priority="high")],
        },
    )
    with pytest.raises(loader.LaneManifestError):
        loader.load_lane_manifest(path)


def test_cost_cap_must_be_non_negative_int(loader, tmp_path):
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [_minimal_lane(cost_cap_tokens_per_run=-1)],
        },
    )
    with pytest.raises(loader.LaneManifestError):
        loader.load_lane_manifest(path)


def test_deterministic_gates_type_checked(loader, tmp_path):
    """Round-7 P1: deterministic_gates entries must be objects with proper types."""
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [_minimal_lane(deterministic_gates="not an array")],
        },
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "deterministic_gates" in str(exc_info.value)


def test_deterministic_gate_missing_required_field(loader, tmp_path):
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(
                    deterministic_gates=[
                        {"id": "typecheck"}  # missing command + timeout_seconds
                    ]
                )
            ],
        },
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "command" in str(exc_info.value) or "timeout" in str(exc_info.value)


def test_deterministic_gate_timeout_bounds(loader, tmp_path):
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(
                    deterministic_gates=[
                        {
                            "id": "typecheck",
                            "command": "tsc",
                            "timeout_seconds": 9999,  # > 600 max
                        }
                    ]
                )
            ],
        },
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "timeout" in str(exc_info.value).lower()


def test_deterministic_gate_unknown_evidence_artifact(loader, tmp_path):
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(
                    deterministic_gates=[
                        {
                            "id": "typecheck",
                            "command": "tsc",
                            "timeout_seconds": 60,
                            "evidence_artifact": "everything",  # not in enum
                        }
                    ]
                )
            ],
        },
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "evidence_artifact" in str(exc_info.value)


def test_redaction_paths_must_be_array_of_strings(loader, tmp_path):
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [_minimal_lane(redaction={"paths_never_send": "should-be-array"})],
        },
    )
    with pytest.raises(loader.LaneManifestError):
        loader.load_lane_manifest(path)


def test_redaction_pattern_string_validated(loader, tmp_path):
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [_minimal_lane(redaction={"content_redact_patterns": [123]})],
        },
    )
    with pytest.raises(loader.LaneManifestError):
        loader.load_lane_manifest(path)


# ---------------------------------------------------------------------------
# Routing enum validation (Codex round-8 P1 #1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bogus", ["bogus", 123, "OPEN_WITH_WARNING", "always"])
def test_on_verifier_unreachable_enum_rejected_for_non_compliance(
    loader, tmp_path, bogus
):
    """Non-compliance lanes must still validate the routing enum.

    Round-8 P1 #1: previously the non-compliance branch copied
    ``declared_unreachable`` straight onto the lane without checking it
    against the schema enum, so dispatcher routing could reach garbage
    values like 'bogus' or 123.
    """
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(compliance_class="none", on_verifier_unreachable=bogus)
            ],
        },
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "on_verifier_unreachable" in str(exc_info.value)


@pytest.mark.parametrize("bogus", ["bogus", 123, "FEEDBACK", "auto"])
def test_auto_continuation_class_enum_rejected_for_non_compliance(
    loader, tmp_path, bogus
):
    """Non-compliance lanes must still validate the routing enum."""
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(compliance_class="none", auto_continuation_class=bogus)
            ],
        },
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "auto_continuation_class" in str(exc_info.value)


@pytest.mark.parametrize("bogus", ["bogus", 123])
def test_on_verifier_unreachable_enum_rejected_for_compliance(loader, tmp_path, bogus):
    """Compliance lanes also reject bogus enum values cleanly.

    Before round-8 the compliance branch would surface a 'requires
    closed_human' message even for a typo'd 'bogus' value. After the
    fix the enum is validated up front so the error reflects the actual
    cause.
    """
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(compliance_class="audit", on_verifier_unreachable=bogus)
            ],
        },
    )
    with pytest.raises(loader.LaneManifestError) as exc_info:
        loader.load_lane_manifest(path)
    assert "on_verifier_unreachable" in str(exc_info.value)


@pytest.mark.parametrize(
    "value",
    ["none", "feedback", "feedback-with-reverify"],
)
def test_non_compliance_accepts_all_auto_continuation_enum_values(
    loader, tmp_path, value
):
    """All schema-permitted enum values pass on a non-compliance lane."""
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(compliance_class="none", auto_continuation_class=value)
            ],
        },
    )
    result = loader.load_lane_manifest(path)
    assert result.manifest["lanes"][0]["auto_continuation_class"] == value


def test_valid_complex_lane_loads_cleanly(loader, tmp_path):
    """Sanity check: a fully-populated lane with all optional fields loads."""
    path = _write_manifest(
        tmp_path,
        {
            "version": 1,
            "lanes": [
                _minimal_lane(
                    issue=1234,
                    shared_ownership=True,
                    priority=10,
                    cost_cap_tokens_per_run=80000,
                    cost_cap_tokens_per_day=500000,
                    deterministic_gates=[
                        {
                            "id": "typecheck",
                            "cwd": "apps/shprd",
                            "command": "pnpm type-check",
                            "timeout_seconds": 180,
                            "required": True,
                            "evidence_artifact": "stdout-tail-50",
                        }
                    ],
                    redaction={
                        "paths_never_send": ["**/__tests__/fixtures/**"],
                        "content_redact_patterns": ["age:\\s*\\d+"],
                    },
                )
            ],
        },
    )
    result = loader.load_lane_manifest(path)
    lane = result.manifest["lanes"][0]
    assert lane["issue"] == 1234
    assert lane["deterministic_gates"][0]["timeout_seconds"] == 180
