#!/usr/bin/env python3
"""
Lane Manifest Loader.

Reads ``.claude/lanes.yml``, validates it against
``packages/popkit-core/output-styles/schemas/lane-manifest.schema.json``,
materializes defaults the loader is responsible for (JSON Schema ``default``
is annotation only), and rejects forbidden combinations at load time.

Round-5 Codex directive (Plan v4.2 #5):

    JSON Schema default is annotation; the loader applies it; tests
    prove it.

Round-4 Codex directive (Plan v4.2 #7):

    Compliance lanes (audit, auth, child-data, ferpa, coppa) MUST have
    ``on_verifier_unreachable: closed_human``. The loader rejects any
    other value at load time with a clear error.

Usage::

    from lane_manifest_loader import LaneManifestError, load_lane_manifest

    try:
        manifest = load_lane_manifest(Path('.claude/lanes.yml'))
    except LaneManifestError as exc:
        print(f'Manifest invalid: {exc}', file=sys.stderr)
        raise SystemExit(2)

The loader returns a typed dict with defaults materialized so callers
don't need to defensively read optional fields.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional

# Compliance classes that mandate ``on_verifier_unreachable: closed_human``.
# Mirrors the table in Plan v4.2 ("on_verifier_unreachable schema defaults").
COMPLIANCE_CLOSED_HUMAN = {"audit", "auth", "child-data", "ferpa", "coppa"}

SUPPORTED_VERSIONS = {1}

DEFAULT_AUTO_CONTINUATION = "none"
DEFAULT_ON_VERIFIER_UNREACHABLE_NON_COMPLIANCE = "open_with_warning"
DEFAULT_ON_VERIFIER_UNREACHABLE_COMPLIANCE = "closed_human"

# Routing enums — must mirror lane-manifest.schema.json definitions.
# Round-8 Codex P1 #1: the loader must reject values outside these sets even
# when the lane is non-compliance. Without this gate the schema enums are
# advisory and routing-critical fields can reach dispatcher code as garbage
# strings.
ON_VERIFIER_UNREACHABLE_VALUES = {"open_with_warning", "closed_human"}
AUTO_CONTINUATION_VALUES = {"none", "feedback", "feedback-with-reverify", "human"}


class LaneManifestError(ValueError):
    """Raised when a manifest fails validation."""


class LoadResult(NamedTuple):
    """Result of a successful manifest load.

    Attributes:
        manifest: The validated manifest with defaults materialized in-place.
        warnings: Non-fatal observations (e.g., absolute paths outside repo root).
    """

    manifest: Dict[str, Any]
    warnings: List[str]


def load_lane_manifest(path: Path, *, repo_root: Optional[Path] = None) -> LoadResult:
    """Load + validate a lane manifest from ``path``.

    Args:
        path: Path to the manifest file (.yml or .yaml).
        repo_root: Repo root for relative path comparisons. Defaults to the
            manifest file's parent's parent (typical for ``.claude/lanes.yml``).

    Returns:
        ``LoadResult(manifest, warnings)`` with defaults materialized.

    Raises:
        LaneManifestError: when validation or default injection fails.
    """
    if not path.exists():
        raise LaneManifestError(f"manifest not found: {path}")

    raw = _read_yaml_or_json(path)
    if not isinstance(raw, dict):
        raise LaneManifestError(
            f"manifest top-level must be an object, got {type(raw).__name__}"
        )

    version = raw.get("version")
    if version not in SUPPORTED_VERSIONS:
        raise LaneManifestError(
            f"unsupported schema_version: {version!r}; "
            f"this loader supports {sorted(SUPPORTED_VERSIONS)}"
        )

    lanes_in = raw.get("lanes")
    if not isinstance(lanes_in, list) or not lanes_in:
        raise LaneManifestError("manifest must contain at least one lane")

    if repo_root is None:
        # `.claude/lanes.yml` -> parent is `.claude/`, parent's parent is repo root.
        repo_root = path.parent.parent

    warnings: List[str] = []
    seen_ids: Dict[str, int] = {}
    materialized_lanes: List[Dict[str, Any]] = []

    for idx, lane_in in enumerate(lanes_in):
        if not isinstance(lane_in, dict):
            raise LaneManifestError(f"lanes[{idx}] must be an object")
        lane = _materialize_lane(lane_in, idx, warnings=warnings, repo_root=repo_root)
        if lane["id"] in seen_ids:
            raise LaneManifestError(
                f"duplicate lane id {lane['id']!r} at lanes[{idx}] "
                f"(also at lanes[{seen_ids[lane['id']]}])"
            )
        seen_ids[lane["id"]] = idx
        materialized_lanes.append(lane)

    out = {"version": version, "lanes": materialized_lanes}
    return LoadResult(manifest=out, warnings=warnings)


_REQUIRED_STRING_FIELDS = (
    "id",
    "repo",
    "worktree",
    "branch",
    "base",
    "verifier_profile",
)


def _materialize_lane(
    lane_in: Dict[str, Any],
    idx: int,
    *,
    warnings: List[str],
    repo_root: Path,
) -> Dict[str, Any]:
    """Validate one lane entry and materialize its loader-applied defaults.

    Round-7 Codex P1: load and enforce types for every required field, not
    just presence. Without per-field type checks the loader was accepting
    manifests like ``repo: 123, worktree: ['not-string'], branch: 42``.
    """

    required = (
        "id",
        "repo",
        "worktree",
        "branch",
        "base",
        "file_ownership",
        "verifier_profile",
        "compliance_class",
        "max_rounds",
        "merge_gate",
    )
    missing = [k for k in required if k not in lane_in]
    if missing:
        raise LaneManifestError(
            f"lanes[{idx}] missing required field(s): {', '.join(missing)}"
        )

    # Round-7 P1: type-check required string fields BEFORE any other
    # processing. The schema annotates these as `type: string`; the loader
    # enforces it.
    for field in _REQUIRED_STRING_FIELDS:
        value = lane_in[field]
        if not isinstance(value, str) or not value:
            raise LaneManifestError(
                f"lanes[{idx}].{field} must be a non-empty string, "
                f"got {type(value).__name__}: {value!r}"
            )

    lane = dict(lane_in)  # shallow copy; we'll mutate to add defaults

    compliance_class = lane["compliance_class"]
    if compliance_class not in {
        "none",
        "schema",
        "audit",
        "auth",
        "child-data",
        "ferpa",
        "coppa",
    }:
        raise LaneManifestError(
            f"lanes[{idx}] ({lane['id']!r}) has unknown compliance_class: "
            f"{compliance_class!r}"
        )

    is_compliance = compliance_class in COMPLIANCE_CLOSED_HUMAN

    # Default + enforce: on_verifier_unreachable.
    # Round-8 P1 #1: validate against the schema enum FIRST, then apply
    # compliance reconciliation. Validating up front gives clean error
    # messages on bogus enum values regardless of compliance class, and
    # closes the gap where non-compliance lanes silently accepted garbage.
    declared_unreachable = lane.get("on_verifier_unreachable")
    if (
        declared_unreachable is not None
        and declared_unreachable not in ON_VERIFIER_UNREACHABLE_VALUES
    ):
        raise LaneManifestError(
            f"lanes[{idx}] ({lane['id']!r}) on_verifier_unreachable="
            f"{declared_unreachable!r} is not one of "
            f"{sorted(ON_VERIFIER_UNREACHABLE_VALUES)}"
        )
    if is_compliance:
        if (
            declared_unreachable is not None
            and declared_unreachable != DEFAULT_ON_VERIFIER_UNREACHABLE_COMPLIANCE
        ):
            raise LaneManifestError(
                f"lanes[{idx}] ({lane['id']!r}) has compliance_class="
                f"{compliance_class!r} which requires on_verifier_unreachable="
                f"{DEFAULT_ON_VERIFIER_UNREACHABLE_COMPLIANCE!r}, but manifest "
                f"declared {declared_unreachable!r}. Compliance lanes cannot "
                f"opt into open_with_warning."
            )
        lane["on_verifier_unreachable"] = DEFAULT_ON_VERIFIER_UNREACHABLE_COMPLIANCE
    else:
        lane["on_verifier_unreachable"] = (
            declared_unreachable
            if declared_unreachable is not None
            else DEFAULT_ON_VERIFIER_UNREACHABLE_NON_COMPLIANCE
        )

    # Default + enforce: auto_continuation_class. Same enum-first pattern.
    declared_auto = lane.get("auto_continuation_class")
    if declared_auto is not None and declared_auto not in AUTO_CONTINUATION_VALUES:
        raise LaneManifestError(
            f"lanes[{idx}] ({lane['id']!r}) auto_continuation_class="
            f"{declared_auto!r} is not one of {sorted(AUTO_CONTINUATION_VALUES)}"
        )
    if is_compliance:
        if declared_auto is not None and declared_auto != "human":
            raise LaneManifestError(
                f"lanes[{idx}] ({lane['id']!r}) has compliance_class="
                f"{compliance_class!r} which requires auto_continuation_class="
                f"'human', but manifest declared {declared_auto!r}."
            )
        lane["auto_continuation_class"] = "human"
    else:
        lane["auto_continuation_class"] = (
            declared_auto if declared_auto is not None else DEFAULT_AUTO_CONTINUATION
        )

    # shared_ownership requires priority
    shared = lane.get("shared_ownership", False)
    lane["shared_ownership"] = shared
    if shared and "priority" not in lane:
        raise LaneManifestError(
            f"lanes[{idx}] ({lane['id']!r}) declares shared_ownership=true but "
            f"is missing required 'priority' integer."
        )

    # File ownership shape check
    file_ownership = lane["file_ownership"]
    if not isinstance(file_ownership, list) or not file_ownership:
        raise LaneManifestError(
            f"lanes[{idx}] ({lane['id']!r}) file_ownership must be a non-empty "
            f"array of glob strings."
        )
    for j, glob in enumerate(file_ownership):
        if not isinstance(glob, str) or not glob:
            raise LaneManifestError(
                f"lanes[{idx}].file_ownership[{j}] must be a non-empty string"
            )
        # Round-8 P1 #2: absolute file_ownership globs MUST be rejected, not
        # warned. file_ownership is the safety boundary for parallel work; an
        # absolute glob like 'C:/repo/apps/**' looks distinct from 'apps/**'
        # but describes the same tree, and lanes-doctor's overlap detection
        # cannot canonicalize across that gap (repo_root is a per-loader
        # concern, not a per-glob concern). Reject at load time so manifest
        # authors fix the glob to a repo-relative form.
        # Detect absolute paths cross-platform: pathlib.Path.is_absolute() is
        # platform-specific (e.g. '/abs/path' is not absolute on Windows), so
        # also check for POSIX leading-slash and Windows drive-letter prefixes.
        is_posix_abs = glob.startswith("/")
        is_windows_abs = len(glob) >= 3 and glob[1] == ":" and glob[2] in {"/", "\\"}
        if Path(glob).is_absolute() or is_posix_abs or is_windows_abs:
            raise LaneManifestError(
                f"lanes[{idx}] ({lane['id']!r}) file_ownership[{j}]={glob!r} is an "
                f"absolute path; file_ownership must be repo-relative globs so "
                f"overlap detection is well-defined."
            )

    # max_rounds bounds — also reject bools (bool is a subclass of int in
    # Python; True/False would otherwise pass the isinstance(int) check)
    max_rounds = lane["max_rounds"]
    if isinstance(max_rounds, bool) or not isinstance(max_rounds, int):
        raise LaneManifestError(
            f"lanes[{idx}] ({lane['id']!r}) max_rounds must be an integer, "
            f"got {type(max_rounds).__name__}: {max_rounds!r}"
        )
    if not 1 <= max_rounds <= 20:
        raise LaneManifestError(
            f"lanes[{idx}] ({lane['id']!r}) max_rounds must be in [1, 20], "
            f"got {max_rounds!r}"
        )

    # merge_gate enum
    if lane["merge_gate"] not in {"auto", "human"}:
        raise LaneManifestError(
            f"lanes[{idx}] ({lane['id']!r}) merge_gate must be 'auto' or 'human', "
            f"got {lane['merge_gate']!r}"
        )

    # Optional fields — type-check each (round-7 P1)
    if "issue" in lane:
        issue = lane["issue"]
        if isinstance(issue, bool) or not isinstance(issue, int):
            raise LaneManifestError(
                f"lanes[{idx}] ({lane['id']!r}) issue must be an integer, "
                f"got {type(issue).__name__}: {issue!r}"
            )

    if not isinstance(lane["shared_ownership"], bool):
        raise LaneManifestError(
            f"lanes[{idx}] ({lane['id']!r}) shared_ownership must be a boolean, "
            f"got {type(lane['shared_ownership']).__name__}: {lane['shared_ownership']!r}"
        )

    if "priority" in lane:
        priority = lane["priority"]
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise LaneManifestError(
                f"lanes[{idx}] ({lane['id']!r}) priority must be an integer, "
                f"got {type(priority).__name__}: {priority!r}"
            )

    for cap_field in ("cost_cap_tokens_per_run", "cost_cap_tokens_per_day"):
        if cap_field in lane:
            cap = lane[cap_field]
            if isinstance(cap, bool) or not isinstance(cap, int) or cap < 0:
                raise LaneManifestError(
                    f"lanes[{idx}] ({lane['id']!r}) {cap_field} must be a "
                    f"non-negative integer, got {type(cap).__name__}: {cap!r}"
                )

    # deterministic_gates: array of objects with required fields + types
    if "deterministic_gates" in lane:
        gates = lane["deterministic_gates"]
        if not isinstance(gates, list):
            raise LaneManifestError(
                f"lanes[{idx}] ({lane['id']!r}) deterministic_gates must be an "
                f"array, got {type(gates).__name__}"
            )
        for g_idx, gate in enumerate(gates):
            _validate_gate(gate, idx, g_idx, lane["id"])

    # redaction: object with optional arrays of strings
    if "redaction" in lane:
        red = lane["redaction"]
        if not isinstance(red, dict):
            raise LaneManifestError(
                f"lanes[{idx}] ({lane['id']!r}) redaction must be an object, "
                f"got {type(red).__name__}"
            )
        for arr_field in ("paths_never_send", "content_redact_patterns"):
            if arr_field in red:
                arr = red[arr_field]
                if not isinstance(arr, list):
                    raise LaneManifestError(
                        f"lanes[{idx}] ({lane['id']!r}) redaction.{arr_field} "
                        f"must be an array of strings, got {type(arr).__name__}"
                    )
                for s_idx, s in enumerate(arr):
                    if not isinstance(s, str):
                        raise LaneManifestError(
                            f"lanes[{idx}] ({lane['id']!r}) "
                            f"redaction.{arr_field}[{s_idx}] must be a string, "
                            f"got {type(s).__name__}: {s!r}"
                        )

    return lane


def _validate_gate(gate: Any, lane_idx: int, gate_idx: int, lane_id: str) -> None:
    """Type-check a deterministic_gate entry per the lane manifest schema."""
    if not isinstance(gate, dict):
        raise LaneManifestError(
            f"lanes[{lane_idx}] ({lane_id!r}) deterministic_gates[{gate_idx}] "
            f"must be an object, got {type(gate).__name__}"
        )

    for required_field in ("id", "command"):
        if required_field not in gate:
            raise LaneManifestError(
                f"lanes[{lane_idx}] ({lane_id!r}) deterministic_gates[{gate_idx}] "
                f"missing required field {required_field!r}"
            )
        value = gate[required_field]
        if not isinstance(value, str) or not value:
            raise LaneManifestError(
                f"lanes[{lane_idx}] ({lane_id!r}) deterministic_gates[{gate_idx}]."
                f"{required_field} must be a non-empty string, "
                f"got {type(value).__name__}: {value!r}"
            )

    if "timeout_seconds" not in gate:
        raise LaneManifestError(
            f"lanes[{lane_idx}] ({lane_id!r}) deterministic_gates[{gate_idx}] "
            f"missing required field 'timeout_seconds'"
        )
    timeout = gate["timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, int):
        raise LaneManifestError(
            f"lanes[{lane_idx}] ({lane_id!r}) deterministic_gates[{gate_idx}]."
            f"timeout_seconds must be an integer, got {type(timeout).__name__}: "
            f"{timeout!r}"
        )
    if not 1 <= timeout <= 600:
        raise LaneManifestError(
            f"lanes[{lane_idx}] ({lane_id!r}) deterministic_gates[{gate_idx}]."
            f"timeout_seconds must be in [1, 600], got {timeout!r}"
        )

    if "cwd" in gate and not isinstance(gate["cwd"], str):
        raise LaneManifestError(
            f"lanes[{lane_idx}] ({lane_id!r}) deterministic_gates[{gate_idx}].cwd "
            f"must be a string, got {type(gate['cwd']).__name__}"
        )

    if "required" in gate and not isinstance(gate["required"], bool):
        raise LaneManifestError(
            f"lanes[{lane_idx}] ({lane_id!r}) deterministic_gates[{gate_idx}]."
            f"required must be a boolean, got {type(gate['required']).__name__}"
        )

    if "evidence_artifact" in gate:
        artifact = gate["evidence_artifact"]
        if artifact not in {
            "stdout",
            "stderr-on-fail",
            "stdout-tail-50",
            "structured-summary",
        }:
            raise LaneManifestError(
                f"lanes[{lane_idx}] ({lane_id!r}) deterministic_gates[{gate_idx}]."
                f"evidence_artifact={artifact!r} is not a recognized type"
            )


def _read_yaml_or_json(path: Path) -> Any:
    """Read a manifest file. Supports YAML (preferred) and JSON.

    YAML support uses ``yaml`` if available; otherwise the loader falls back
    to JSON. The lane manifest is YAML in production but JSON-compatible test
    fixtures keep the loader testable without a hard YAML dependency.
    """
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yml", ".yaml"}:
        try:
            import yaml  # type: ignore[import-untyped]

            return yaml.safe_load(text)
        except ImportError as exc:
            raise LaneManifestError(
                f"PyYAML is required to parse YAML manifests; install pyyaml or "
                f"convert {path} to JSON."
            ) from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LaneManifestError(f"failed to parse {path}: {exc}") from exc


def main(argv: Optional[List[str]] = None) -> int:
    """CLI: validate a manifest and print a JSON summary."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate a lane manifest and print a JSON summary."
    )
    parser.add_argument("path", type=Path, help="Path to .claude/lanes.yml")
    parser.add_argument(
        "--repo-root", type=Path, default=None, help="Override repo root path."
    )
    args = parser.parse_args(argv)

    try:
        result = load_lane_manifest(args.path, repo_root=args.repo_root)
    except LaneManifestError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "ok": True,
                "lane_count": len(result.manifest["lanes"]),
                "lane_ids": [lane["id"] for lane in result.manifest["lanes"]],
                "warnings": result.warnings,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
