#!/usr/bin/env python3
"""
Stop hook — Phase 1a-ii dispatcher (Plan v4.2 Layer 5).

Replaces the previous ``logs/stop.json`` raw-input dump (privacy violation
flagged by Codex) with a redacted-bundle dispatcher whose contract is:

1. Read the pending claim ledger written by ``/checkpoint`` at
   ``<repo>/.claude/popkit/pending-claim-ledger.json``.
2. If the pending ledger exists AND parses as JSON AND has expected fields,
   archive it into the per-turn bundle directory at
   ``<repo>/.claude/popkit/verifier-bundles/<session_id>/<turn_id>/ledger.json``
   and delete the pending slot.
3. If the pending ledger is missing OR malformed, write a ``status: "missing"``
   stub to the same bundle path AND print a loud stderr warning so the
   operator sees the absence during the turn (not just buried in a later
   verifier ``human`` verdict).
4. Stay under the 5000ms hooks.json Stop budget. Pure local IO; no
   network, no subprocess fanout.
5. Return a structured JSON response on stdout. Exit 0 even on errors so
   Claude Code's Stop pipeline isn't blocked by hook bugs.

Round 5 #4 directive (preserved):

    /checkpoint is the canonical writer. Stop hook is ONLY the absence
    detector and writes a stub if the writer was never invoked. The
    Stop hook NEVER synthesizes claims from transcript prose.

Privacy: this hook deliberately does NOT log the raw Claude Code stdin
payload anywhere. The Phase 1a-i ``checkpoint_writer.py`` is responsible
for the claim content; the dispatcher only moves bytes the writer wrote.
The ``transcript`` field that the previous version optionally saved to
``logs/chat.json`` is ALSO dropped — same privacy rationale.
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Mirrors claim-ledger.schema.json. The dispatcher must validate the full
# required-field set (round-11 P1: only checking schema_version + status
# let a {schema_version: 1, status: "normal"} stub through as a "valid"
# ledger). The writer at /checkpoint already validates these, but the
# dispatcher defends against interrupted writes, manual edits, and races.
SCHEMA_VERSION = 1
ALLOWED_STATUS = {"normal", "missing"}
ALLOWED_STAGES = {"plan", "code"}
ALLOWED_NEXT_ACTIONS = {"verify", "merge-ready", "needs-review"}
# claim-ledger.schema.json's required fields. status/schema_version are
# checked separately above; the rest must all be present and structurally
# sound (right type, non-empty for strings, list for arrays).
_REQUIRED_LEDGER_FIELDS = (
    "turn_id",
    "session_id",
    "lane_id",
    "stage",
    "intent",
    "changed_files",
    "acceptance_claims",
    "next_action",
)


def find_repo_root(start: Optional[Path] = None) -> Optional[Path]:
    """Walk up from ``start`` until a ``.git`` directory is found.

    Returns ``None`` rather than raising — the dispatcher must always
    exit 0 so Claude Code's Stop pipeline isn't blocked. Callers that
    need the path use ``or`` to short-circuit cleanly.
    """
    cur = (start or Path.cwd()).resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def read_pending_ledger(
    repo_root: Path,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Try to read + sanity-check the pending claim ledger.

    Returns ``(ledger_dict, None)`` on success or ``(None, reason)`` when the
    file is missing / unreadable / malformed. ``reason`` is the audit-friendly
    string the dispatcher writes into the stub's ``reason`` field.
    """
    pending = repo_root / ".claude" / "popkit" / "pending-claim-ledger.json"
    if not pending.exists():
        return None, "no_checkpoint_called"
    try:
        raw = pending.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"pending_read_failed: {exc}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"pending_invalid_json: {exc}"
    if not isinstance(data, dict):
        return None, "pending_not_object"
    if data.get("schema_version") != SCHEMA_VERSION:
        return (
            None,
            f"pending_unsupported_schema_version: {data.get('schema_version')!r}",
        )
    # Round-12 P2: type-check before set membership. ``value in some_set``
    # raises TypeError when value is unhashable (e.g. ``[]`` or ``{}``),
    # which would escape this read path uncontrolled and leave the
    # pending file in place. Same bug class as round-8 P2 in the
    # manifest loader.
    raw_status = data.get("status")
    if not isinstance(raw_status, str):
        return (
            None,
            f"pending_status_not_string: {type(raw_status).__name__}: {raw_status!r}",
        )
    if raw_status not in ALLOWED_STATUS:
        return None, f"pending_unknown_status: {raw_status!r}"
    structural = _validate_required_ledger_structure(data)
    if structural is not None:
        return None, structural
    return data, None


def _validate_required_ledger_structure(data: Dict[str, Any]) -> Optional[str]:
    """Round-11 P1: enforce all required claim-ledger fields are present
    with sensible types BEFORE archive. Returns ``None`` when the ledger
    is structurally sound, or an audit-friendly reason string when a
    field is missing / wrong type / empty.

    Defense-in-depth: the writer at /checkpoint already enforces these,
    but the dispatcher must protect against interrupted writes, manual
    edits to the pending file, and tampering. Validating here keeps
    malformed advisory data out of verifier-bundles/.
    """
    missing = [k for k in _REQUIRED_LEDGER_FIELDS if k not in data]
    if missing:
        return f"pending_missing_required_fields: {missing}"

    for str_field in ("turn_id", "session_id", "lane_id", "intent"):
        value = data[str_field]
        if not isinstance(value, str) or not value:
            return (
                f"pending_field_must_be_non_empty_string: "
                f"{str_field}={value!r} ({type(value).__name__})"
            )

    # Round-12 P2: type-check before set membership; lists/dicts are
    # unhashable and ``not in`` would raise TypeError otherwise.
    raw_stage = data["stage"]
    if not isinstance(raw_stage, str):
        return f"pending_stage_not_string: {type(raw_stage).__name__}: {raw_stage!r}"
    if raw_stage not in ALLOWED_STAGES:
        return f"pending_unknown_stage: {raw_stage!r}"
    raw_next = data["next_action"]
    if not isinstance(raw_next, str):
        return f"pending_next_action_not_string: {type(raw_next).__name__}: {raw_next!r}"
    if raw_next not in ALLOWED_NEXT_ACTIONS:
        return f"pending_unknown_next_action: {raw_next!r}"

    if not isinstance(data["changed_files"], list):
        return f"pending_changed_files_not_array: {type(data['changed_files']).__name__}"
    if not isinstance(data["acceptance_claims"], list):
        return f"pending_acceptance_claims_not_array: {type(data['acceptance_claims']).__name__}"

    return None


def make_stub_ledger(*, session_id: str, turn_id: str, reason: str) -> Dict[str, Any]:
    """Build the ``status='missing'`` stub the verifier will see when no
    /checkpoint was called this turn."""
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "missing",
        "reason": reason,
        "turn_id": turn_id,
        "session_id": session_id,
        "lane_id": "unknown",
        "stage": "code",
        "intent": "(no /checkpoint called this turn)",
        "changed_files": [],
        "acceptance_claims": [],
        "next_action": "needs-review",
    }


def archive_ledger(
    ledger: Dict[str, Any], *, repo_root: Path, session_id: str, turn_id: str
) -> Path:
    """Write the ledger into the per-turn bundle directory.

    The bundle path mirrors Plan v4.2 Layer 5:
    ``<repo>/.claude/popkit/verifier-bundles/<session_id>/<turn_id>/ledger.json``.
    """
    bundle_dir = repo_root / ".claude" / "popkit" / "verifier-bundles" / session_id / turn_id
    bundle_dir.mkdir(parents=True, exist_ok=True)
    target = bundle_dir / "ledger.json"
    tmp = bundle_dir / f"ledger.{uuid.uuid4().hex}.tmp"
    try:
        tmp.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        # os.replace would also work; Path.replace is the same semantics.
        tmp.replace(target)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError as exc:
                # Best-effort cleanup only; the archive succeeded.
                print(
                    f"warning: failed to remove temporary file {tmp}: {exc}",
                    file=sys.stderr,
                )
    return target


def delete_pending_ledger(repo_root: Path) -> None:
    """Remove the pending slot after a successful archive.

    Best-effort: if it can't be removed (already gone, lock contention),
    log a stderr warning but don't fail the dispatcher. The next
    /checkpoint call will overwrite it anyway.
    """
    pending = repo_root / ".claude" / "popkit" / "pending-claim-ledger.json"
    try:
        pending.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        print(
            f"warning: failed to remove pending ledger {pending}: {exc}",
            file=sys.stderr,
        )


def dispatch(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run the dispatcher on parsed Claude Code stdin and return the
    response dict that will be written to stdout.

    Tests import this directly so they don't drive the CLI.
    """
    session_id = str(input_data.get("session_id") or uuid.uuid4())
    turn_id = str(uuid.uuid4())
    timestamp = datetime.now(tz=UTC).isoformat()

    response: Dict[str, Any] = {
        "status": "success",
        "session_id": session_id,
        "turn_id": turn_id,
        "timestamp": timestamp,
    }

    repo_root = find_repo_root()
    if repo_root is None:
        # No repo → no place to archive. Return cleanly so Claude exit
        # isn't blocked. The verifier infrastructure is repo-scoped.
        response["ledger_status"] = "skipped_no_repo"
        response["bundle_path"] = None
        return response

    ledger, missing_reason = read_pending_ledger(repo_root)
    if ledger is None:
        ledger = make_stub_ledger(
            session_id=session_id, turn_id=turn_id, reason=missing_reason or "unknown"
        )
        response["ledger_status"] = "missing"
        response["missing_reason"] = missing_reason
        # Loud stderr so the operator sees absence during the turn.
        print(
            f"[popkit-verifier] WARNING: no /checkpoint called this turn "
            f"(reason: {missing_reason!r}). Wrote status='missing' stub at "
            f"bundle <session>/{turn_id[:8]}/. The verifier will return "
            f"verdict='human' with reason='claim_ledger_missing_or_invalid'.",
            file=sys.stderr,
        )
    else:
        # Use the writer-supplied turn_id/session_id when present so the
        # claim ledger and the bundle directory it lands in stay
        # consistent with what /checkpoint already produced.
        ledger_turn_id = ledger.get("turn_id") or turn_id
        ledger_session_id = ledger.get("session_id") or session_id
        turn_id = ledger_turn_id
        session_id = ledger_session_id
        response["session_id"] = session_id
        response["turn_id"] = turn_id
        response["ledger_status"] = "archived"

    try:
        target = archive_ledger(ledger, repo_root=repo_root, session_id=session_id, turn_id=turn_id)
        response["bundle_path"] = str(target)
    except OSError as exc:
        # Archive write failed — surface the cause but keep exit 0.
        response["ledger_status"] = "archive_failed"
        response["error"] = f"archive_write_failed: {exc}"
        response["bundle_path"] = None
        print(
            f"[popkit-verifier] ERROR: failed to archive ledger: {exc}",
            file=sys.stderr,
        )
        return response

    # Round-11 P2: always remove the pending slot after a successful
    # bundle write, whether we archived a real ledger or wrote a stub
    # for a malformed pending file. Leaving a malformed pending file
    # behind would poison subsequent Stop runs (every dispatch would
    # archive the same stub) until /checkpoint overwrote it. The slot
    # is single-use per turn by contract.
    if response["ledger_status"] in {"archived", "missing"}:
        delete_pending_ledger(repo_root)

    return response


def main() -> int:
    """CLI entry point. Reads JSON from stdin and writes JSON to stdout.

    Always exits 0 so a hook bug never blocks Claude Code's Stop
    pipeline. Errors are surfaced in the response JSON ``status`` and
    via stderr, but never via a non-zero exit code.
    """
    try:
        raw = sys.stdin.read()
        input_data = json.loads(raw) if raw.strip() else {}
        if not isinstance(input_data, dict):
            input_data = {}
    except json.JSONDecodeError:
        # Surface the parse failure but proceed with an empty payload —
        # the dispatcher will write a stub and the verifier will see it.
        input_data = {}
        print(
            "[popkit-verifier] WARNING: stdin was not valid JSON; treating as empty payload.",
            file=sys.stderr,
        )

    try:
        response = dispatch(input_data)
    except Exception as exc:  # noqa: BLE001 — Stop hook must not raise
        # Last-resort safety net: any unexpected exception is logged but
        # never bubbles up. Claude Code keeps moving.
        response = {
            "status": "error",
            "error": f"dispatcher_failed: {exc}",
            "timestamp": datetime.now(tz=UTC).isoformat(),
        }
        print(
            f"[popkit-verifier] ERROR: dispatcher exception: {exc}",
            file=sys.stderr,
        )

    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
