#!/usr/bin/env python3
"""
Checkpoint writer.

The writer half of the ``/checkpoint`` slash command (Plan v4.2 Layer 1 +
Round 5 #4). The slash command at ``packages/popkit-core/commands/checkpoint.md``
collects the builder's atomic claims for the current turn and pipes them
to this script, which validates them against ``claim-ledger.schema.json``
and writes them to a pending location the Stop-hook dispatcher will read.

Round 5 #4 directive:

    /checkpoint is the canonical writer. Stop hook is ONLY the absence
    detector and writes a stub if the writer was never invoked. The
    writer never synthesizes claims from transcript prose.

Round 6 #3 directive:

    The writer lands at packages/popkit-core/scripts/checkpoint_writer.py
    so it's testable independently of the markdown command surface.

Pending location (Phase 1a-i):

    <repo_root>/.claude/popkit/pending-claim-ledger.json

This is a single-file slot — the latest /checkpoint of a turn wins.
The Stop-hook dispatcher (Phase 1a-ii) reads this file at turn-end,
moves it into the per-turn bundle directory, and deletes the slot.
``.claude/`` is gitignored so the pending file never accidentally
ships in a commit.

Usage::

    cat ledger.json | python checkpoint_writer.py
    # or pass via --input
    python checkpoint_writer.py --input ledger.json

Exit codes:
    0 — wrote pending ledger; printed absolute path to stdout.
    2 — validation failure; printed error JSON to stderr.
    3 — environment failure (repo not found, write failed).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Mirrors definitions in claim-ledger.schema.json. Kept here so the writer
# is dependency-free; the schema file is the source of truth and any
# divergence between this and the JSON Schema is itself a finding.
SCHEMA_VERSION = 1
ALLOWED_STAGES = {"plan", "code"}
ALLOWED_NEXT_ACTIONS = {"verify", "merge-ready", "needs-review"}
ALLOWED_GATE_RESULTS = {"pass", "fail", "skip"}
ALLOWED_COMPLIANCE_TOUCH = {
    "none",
    "schema",
    "audit",
    "auth",
    "child-data",
    "ferpa",
    "coppa",
}
REQUIRED_TOP_LEVEL = (
    "lane_id",
    "stage",
    "intent",
    "changed_files",
    "acceptance_claims",
    "next_action",
)

# Fields the writer owns and materializes itself. If the user supplies them in
# the payload we reject any divergent value rather than silently overwriting.
# Otherwise a confused builder could pass ``status: "missing"`` (only the
# dispatcher writes that) or ``schema_version: 2`` and never notice the
# writer overrode it.
_WRITER_OWNED_FIELDS = ("status", "schema_version", "turn_id", "session_id")


class CheckpointError(ValueError):
    """Raised when the input ledger fails validation."""


def find_repo_root(start: Optional[Path] = None) -> Path:
    """Walk up from ``start`` until a ``.git`` directory is found."""
    cur = (start or Path.cwd()).resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / ".git").exists():
            return candidate
    raise CheckpointError(
        f"could not locate repository root (no .git found from {cur})"
    )


def validate_input(payload: Any) -> Dict[str, Any]:
    """Validate the raw JSON payload and return a dict ready for normalize()."""
    if not isinstance(payload, dict):
        raise CheckpointError(
            f"top-level input must be an object, got {type(payload).__name__}"
        )

    missing = [k for k in REQUIRED_TOP_LEVEL if k not in payload]
    if missing:
        raise CheckpointError(f"missing required field(s): {', '.join(missing)}")

    # Writer-owned fields: reject any user-supplied value that doesn't match
    # what the writer would set anyway. Silent override is confusing — a
    # builder passing ``status: "missing"`` would expect the verifier to see
    # a stub, not a normal ledger with their other fields in it.
    if "status" in payload and payload["status"] != "normal":
        raise CheckpointError(
            f"status is writer-owned and is always 'normal' from /checkpoint; "
            f"the dispatcher writes 'missing' stubs. Got {payload['status']!r}; "
            f"omit the field."
        )
    if "schema_version" in payload and payload["schema_version"] != SCHEMA_VERSION:
        raise CheckpointError(
            f"schema_version is writer-owned and pinned to {SCHEMA_VERSION}; "
            f"got {payload['schema_version']!r}. Omit the field."
        )
    for field in ("turn_id", "session_id"):
        if field in payload:
            raise CheckpointError(
                f"{field} is writer-owned and supplied via env "
                f"(CLAUDE_SESSION_ID / POPKIT_SESSION_ID / POPKIT_TURN_ID) or "
                f"the --{field.replace('_', '-')} CLI flag, not in the payload. "
                f"Omit the field."
            )

    _require_string(payload, "lane_id", min_len=1)
    _require_string(payload, "intent", min_len=1)

    stage = payload["stage"]
    if not isinstance(stage, str) or stage not in ALLOWED_STAGES:
        raise CheckpointError(
            f"stage must be one of {sorted(ALLOWED_STAGES)}, got {stage!r}"
        )

    next_action = payload["next_action"]
    if not isinstance(next_action, str) or next_action not in ALLOWED_NEXT_ACTIONS:
        raise CheckpointError(
            f"next_action must be one of {sorted(ALLOWED_NEXT_ACTIONS)}, "
            f"got {next_action!r}"
        )

    changed_files = payload["changed_files"]
    if not isinstance(changed_files, list):
        raise CheckpointError(
            f"changed_files must be an array, got {type(changed_files).__name__}"
        )
    for i, entry in enumerate(changed_files):
        _validate_changed_file(entry, i)

    claims = payload["acceptance_claims"]
    if not isinstance(claims, list):
        raise CheckpointError(
            f"acceptance_claims must be an array, got {type(claims).__name__}"
        )
    for i, claim in enumerate(claims):
        if not isinstance(claim, str) or not claim:
            raise CheckpointError(
                f"acceptance_claims[{i}] must be a non-empty string, got {claim!r}"
            )

    if "tests_run" in payload:
        tests_run = payload["tests_run"]
        if not isinstance(tests_run, list):
            raise CheckpointError(
                f"tests_run must be an array, got {type(tests_run).__name__}"
            )
        for i, t in enumerate(tests_run):
            _validate_test_run(t, i)

    if "deterministic_gates_observed" in payload:
        gates = payload["deterministic_gates_observed"]
        if not isinstance(gates, dict):
            raise CheckpointError(
                f"deterministic_gates_observed must be an object, "
                f"got {type(gates).__name__}"
            )
        for k, v in gates.items():
            if not isinstance(k, str) or not k:
                raise CheckpointError(
                    f"deterministic_gates_observed key must be a non-empty "
                    f"string, got {k!r}"
                )
            if not isinstance(v, str) or v not in ALLOWED_GATE_RESULTS:
                raise CheckpointError(
                    f"deterministic_gates_observed[{k!r}] must be one of "
                    f"{sorted(ALLOWED_GATE_RESULTS)}, got {v!r}"
                )

    if "compliance_touch" in payload:
        ct = payload["compliance_touch"]
        if not isinstance(ct, list):
            raise CheckpointError(
                f"compliance_touch must be an array, got {type(ct).__name__}"
            )
        for i, c in enumerate(ct):
            if not isinstance(c, str) or c not in ALLOWED_COMPLIANCE_TOUCH:
                raise CheckpointError(
                    f"compliance_touch[{i}] must be one of "
                    f"{sorted(ALLOWED_COMPLIANCE_TOUCH)}, got {c!r}"
                )

    if "known_gaps" in payload:
        gaps = payload["known_gaps"]
        if not isinstance(gaps, list):
            raise CheckpointError(
                f"known_gaps must be an array, got {type(gaps).__name__}"
            )
        for i, g in enumerate(gaps):
            if not isinstance(g, str):
                raise CheckpointError(
                    f"known_gaps[{i}] must be a string, got {type(g).__name__}"
                )

    return payload


def _require_string(payload: Dict[str, Any], field: str, *, min_len: int) -> None:
    value = payload.get(field)
    if not isinstance(value, str) or len(value) < min_len:
        raise CheckpointError(
            f"{field} must be a non-empty string, got {type(value).__name__}: {value!r}"
        )


def _validate_changed_file(entry: Any, idx: int) -> None:
    if not isinstance(entry, dict):
        raise CheckpointError(
            f"changed_files[{idx}] must be an object, got {type(entry).__name__}"
        )
    if "path" not in entry:
        raise CheckpointError(f"changed_files[{idx}] missing required field 'path'")
    path = entry["path"]
    if not isinstance(path, str) or not path:
        raise CheckpointError(
            f"changed_files[{idx}].path must be a non-empty string, got {path!r}"
        )
    # Round-9 P2: claim-ledger.schema.json says path is "repo-root-relative
    # with forward-slash separators". Reject anything that violates that
    # contract at the writer boundary so absolute paths and parent-dir
    # traversals never reach the dispatcher/verifier as advisory data.
    if "\\" in path:
        raise CheckpointError(
            f"changed_files[{idx}].path must use forward slashes, got {path!r}"
        )
    if path.startswith("/") or (
        len(path) >= 3 and path[1] == ":" and path[2] in {"/", "\\"}
    ):
        raise CheckpointError(
            f"changed_files[{idx}].path must be repo-root-relative, "
            f"got absolute path {path!r}"
        )
    if any(seg == ".." for seg in path.split("/")):
        raise CheckpointError(
            f"changed_files[{idx}].path must be repo-root-relative; "
            f"parent-directory traversal segments are not allowed, "
            f"got {path!r}"
        )
    for k in ("added", "removed"):
        if k in entry:
            v = entry[k]
            # bool is an int subclass; reject explicitly so True/False aren't
            # silently accepted as 1/0 line counts.
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise CheckpointError(
                    f"changed_files[{idx}].{k} must be a non-negative integer, "
                    f"got {type(v).__name__}: {v!r}"
                )


def _validate_test_run(entry: Any, idx: int) -> None:
    if not isinstance(entry, dict):
        raise CheckpointError(
            f"tests_run[{idx}] must be an object, got {type(entry).__name__}"
        )
    name = entry.get("name")
    if not isinstance(name, str) or not name:
        raise CheckpointError(
            f"tests_run[{idx}].name must be a non-empty string, got {name!r}"
        )
    for k in ("passed", "failed"):
        if k in entry:
            v = entry[k]
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise CheckpointError(
                    f"tests_run[{idx}].{k} must be a non-negative integer, "
                    f"got {type(v).__name__}: {v!r}"
                )


def materialize_ledger(
    payload: Dict[str, Any],
    *,
    session_id: Optional[str] = None,
    turn_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply schema-version + ids and return the canonical ledger dict.

    ``session_id`` and ``turn_id`` may be supplied (e.g. by the slash command
    when Claude Code provides them via env). When absent, fresh UUIDs are
    generated and the writer notes the synthesis on stderr.
    """
    out = dict(payload)
    out["schema_version"] = SCHEMA_VERSION
    out["status"] = "normal"
    out["turn_id"] = turn_id or str(uuid.uuid4())
    out["session_id"] = session_id or str(uuid.uuid4())
    return out


def write_pending_ledger(ledger: Dict[str, Any], *, repo_root: Path) -> Path:
    """Atomically write the ledger to ``<repo>/.claude/popkit/pending-claim-ledger.json``.

    Two parallel ``/checkpoint`` invocations could otherwise collide on a
    shared ``.tmp`` filename and produce a partial-write corruption. The tmp
    name carries a fresh UUID + pid so concurrent writers each have their own
    staging file; ``os.replace`` then races atomically for the target.
    Last-writer-wins is the documented contract.
    """
    target_dir = repo_root / ".claude" / "popkit"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "pending-claim-ledger.json"
    tmp = target_dir / f"pending-claim-ledger.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    try:
        tmp.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        # os.replace is atomic on POSIX and Windows when src + dst are on the
        # same filesystem; both live under the same `.claude/popkit/` dir.
        os.replace(tmp, target)
    finally:
        # Clean up the tmp on any failure path (success path already moved it).
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
    return target


def write_checkpoint(
    payload: Any,
    *,
    repo_root: Optional[Path] = None,
    session_id: Optional[str] = None,
    turn_id: Optional[str] = None,
) -> Tuple[Path, Dict[str, Any]]:
    """Validate ``payload`` and write the pending ledger.

    Returns ``(written_path, materialized_ledger)``. Tests import this
    rather than driving the CLI.
    """
    validated = validate_input(payload)
    if repo_root is None:
        repo_root = find_repo_root()
    if session_id is None:
        session_id = os.environ.get("CLAUDE_SESSION_ID") or os.environ.get(
            "POPKIT_SESSION_ID"
        )
    if turn_id is None:
        turn_id = os.environ.get("POPKIT_TURN_ID")
    ledger = materialize_ledger(validated, session_id=session_id, turn_id=turn_id)
    target = write_pending_ledger(ledger, repo_root=repo_root)
    return target, ledger


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write a pending claim ledger for the verifier dispatcher."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to a JSON file. Defaults to stdin.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override repo root detection.",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Override CLAUDE_SESSION_ID env var.",
    )
    parser.add_argument(
        "--turn-id",
        default=None,
        help="Override turn_id (default: fresh UUID4).",
    )
    args = parser.parse_args(argv)

    # Round-9 P3: --input file errors must surface as structured JSON, not
    # raw FileNotFoundError tracebacks, so the CLI's failure contract is
    # uniform across stdin and --input.
    if args.input:
        try:
            raw = args.input.read_text(encoding="utf-8")
        except (FileNotFoundError, IsADirectoryError, PermissionError, OSError) as exc:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": f"could not read --input {args.input}: {exc}",
                    }
                ),
                file=sys.stderr,
            )
            return 2
    else:
        raw = sys.stdin.read()
    if not raw.strip():
        print(
            json.dumps(
                {"ok": False, "error": "empty input — pipe a JSON object on stdin"}
            ),
            file=sys.stderr,
        )
        return 2

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(
            json.dumps({"ok": False, "error": f"invalid JSON: {exc}"}),
            file=sys.stderr,
        )
        return 2

    try:
        target, ledger = write_checkpoint(
            payload,
            repo_root=args.repo_root,
            session_id=args.session_id,
            turn_id=args.turn_id,
        )
    except CheckpointError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2
    except OSError as exc:
        print(
            json.dumps({"ok": False, "error": f"write failed: {exc}"}),
            file=sys.stderr,
        )
        return 3

    print(
        json.dumps(
            {
                "ok": True,
                "path": str(target),
                "turn_id": ledger["turn_id"],
                "session_id": ledger["session_id"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
