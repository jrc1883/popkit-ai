#!/usr/bin/env python3
"""
popkit-verifier-runner CLI — Phase 1a-iii.

Reads a per-turn bundle written by the Phase 1a-ii Stop dispatcher, decides
whether the ledger fast-fails to a ``verdict='human'`` write, and (in a
future PR) hands valid bundles off to Codex CLI. This PR lands the
fast-fail path only:

* ``ledger.json`` missing / unparseable → write
  ``verdict.json`` with ``verdict='human'`` and
  ``reason='claim_ledger_missing_or_invalid'``.
* Ledger has ``status='missing'`` (the dispatcher's stub) → same.
* Ledger structurally invalid against the required-field set → same.
* Ledger valid and ``status='normal'`` → exit cleanly without writing
  a verdict, signaling "deferred to Codex invocation in a future PR".

Plan v4.2 Layer 1 hard contract (Codex round 2 + 3):

    if the ledger is absent or fails schema validation, the verifier
    returns { verdict: "human", reason: "claim_ledger_missing_or_invalid" }.
    The verifier MUST NOT reconstruct the ledger from transcript prose.
    No quiet diff-only fallback.

Plan v4.2 Layer 5:

    Operator (or a separate slash command, or a parallel Claude session)
    runs `popkit-verifier-runner --bundle <artifact-dir>` later. Runner
    writes a verdict file to the same bundle.

Usage::

    popkit-verifier-runner --bundle <repo>/.claude/popkit/verifier-bundles/<sid>/<tid>/

Exit codes:
    0 — verdict.json was written (human verdict for the fast-fail
        path) OR the ledger was valid and the runner deferred to a
        future Codex invocation.
    2 — bundle is unusable (path doesn't exist, isn't a directory).
    3 — internal write failure (verdict.json couldn't be persisted).
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Mirrors verifier-result.schema.json. Kept here so the runner is
# dependency-free; the schema file is the source of truth and any
# divergence between this and the JSON Schema is itself a finding.
VERIFIER_RESULT_SCHEMA_VERSION = 1
ALLOWED_VERDICTS = {"pass", "feedback", "block", "human"}
ALLOWED_REASONS = {
    "claim_ledger_missing_or_invalid",
    "verifier_output_unparseable",
    "daily_cost_cap_exceeded",
    "verifier_unreachable_compliance_lane",
    "compliance_class_blocks_auto_continuation",
    "max_rounds_reached",
    "operator_escalation",
}
ALLOWED_FINDING_SEVERITIES = {"high", "medium", "low"}
ALLOWED_SUGGESTED_ACTIONS = {"block", "feedback", "human"}

# Mirrors claim-ledger.schema.json's required envelope. The dispatcher
# already enforces this; the runner re-validates as defense-in-depth so
# bundles edited or moved between Stop and runner still fail closed.
LEDGER_SCHEMA_VERSION = 1
LEDGER_ALLOWED_STATUS = {"normal", "missing"}
LEDGER_ALLOWED_STAGES = {"plan", "code"}
LEDGER_ALLOWED_NEXT_ACTIONS = {"verify", "merge-ready", "needs-review"}
_LEDGER_REQUIRED_FIELDS = (
    "turn_id",
    "session_id",
    "lane_id",
    "stage",
    "intent",
    "changed_files",
    "acceptance_claims",
    "next_action",
)


class VerdictWriteError(RuntimeError):
    """Raised when the runner can't persist verdict.json."""


def read_ledger(bundle_dir: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Try to read + sanity-check ``<bundle>/ledger.json``.

    Returns ``(ledger, None)`` on success or ``(None, reason)`` when the
    file is missing / unreadable / structurally invalid. ``reason`` is
    audit-friendly and will be folded into the human verdict's
    ``rationale`` field so operators see WHY the runner fast-failed.
    """
    ledger_path = bundle_dir / "ledger.json"
    if not ledger_path.exists():
        return None, "ledger_json_not_found"
    try:
        raw = ledger_path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"ledger_read_failed: {exc}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"ledger_invalid_json: {exc}"
    if not isinstance(data, dict):
        return None, "ledger_not_object"
    if data.get("schema_version") != LEDGER_SCHEMA_VERSION:
        return (
            None,
            f"ledger_unsupported_schema_version: {data.get('schema_version')!r}",
        )
    # Round-12-style type-guard before set membership so unhashable
    # values can't crash the runner.
    raw_status = data.get("status")
    if not isinstance(raw_status, str):
        return (
            None,
            f"ledger_status_not_string: {type(raw_status).__name__}: {raw_status!r}",
        )
    if raw_status not in LEDGER_ALLOWED_STATUS:
        return None, f"ledger_unknown_status: {raw_status!r}"
    if raw_status == "missing":
        # status='missing' is the dispatcher's intentional stub. Fast-fail
        # without further structural validation — the stub is INTENDED to
        # surface as a human verdict.
        return data, "ledger_status_missing"
    structural = _validate_ledger_structure(data)
    if structural is not None:
        return None, structural
    return data, None


def _validate_ledger_structure(data: Dict[str, Any]) -> Optional[str]:
    """Required-field validation matching the dispatcher's defense layer.

    The runner duplicates this rather than importing the dispatcher to
    keep the CLI standalone — bundles can be carried between machines or
    edited in transit, and the runner is the last gate before Codex sees
    the data.
    """
    missing = [k for k in _LEDGER_REQUIRED_FIELDS if k not in data]
    if missing:
        return f"ledger_missing_required_fields: {missing}"
    for str_field in ("turn_id", "session_id", "lane_id", "intent"):
        value = data[str_field]
        if not isinstance(value, str) or not value:
            return (
                f"ledger_field_must_be_non_empty_string: "
                f"{str_field}={value!r} ({type(value).__name__})"
            )
    raw_stage = data["stage"]
    if not isinstance(raw_stage, str):
        return f"ledger_stage_not_string: {type(raw_stage).__name__}: {raw_stage!r}"
    if raw_stage not in LEDGER_ALLOWED_STAGES:
        return f"ledger_unknown_stage: {raw_stage!r}"
    raw_next = data["next_action"]
    if not isinstance(raw_next, str):
        return f"ledger_next_action_not_string: {type(raw_next).__name__}: {raw_next!r}"
    if raw_next not in LEDGER_ALLOWED_NEXT_ACTIONS:
        return f"ledger_unknown_next_action: {raw_next!r}"
    if not isinstance(data["changed_files"], list):
        return f"ledger_changed_files_not_array: {type(data['changed_files']).__name__}"
    if not isinstance(data["acceptance_claims"], list):
        return f"ledger_acceptance_claims_not_array: {type(data['acceptance_claims']).__name__}"
    return None


def make_human_verdict(
    *,
    lane_id: str,
    ledger_turn_id: str,
    reason: str,
    rationale: str,
) -> Dict[str, Any]:
    """Build a verifier-result.schema.json conforming verdict for the
    fast-fail path. Verdict is always ``human`` here — the runner only
    writes verdicts in this PR for the missing/invalid case."""
    return {
        "schema_version": VERIFIER_RESULT_SCHEMA_VERSION,
        "verdict": "human",
        "lane_id": lane_id,
        "ledger_turn_id": ledger_turn_id,
        "findings": [],
        "rationale": rationale,
        "reason": reason,
    }


def validate_verdict(verdict: Any) -> Optional[str]:
    """Round-9-style schema-or-die guard: validate before writing.

    Returns ``None`` when the verdict matches verifier-result.schema.json
    or an audit-friendly reason string when it doesn't. The runner
    refuses to persist a malformed verdict — that protects the dispatcher
    state machine from acting on garbage.
    """
    if not isinstance(verdict, dict):
        return f"verdict_not_object: {type(verdict).__name__}"
    if verdict.get("schema_version") != VERIFIER_RESULT_SCHEMA_VERSION:
        return f"verdict_unsupported_schema_version: {verdict.get('schema_version')!r}"
    raw_verdict = verdict.get("verdict")
    if not isinstance(raw_verdict, str):
        return f"verdict_not_string: {type(raw_verdict).__name__}: {raw_verdict!r}"
    if raw_verdict not in ALLOWED_VERDICTS:
        return f"verdict_unknown_value: {raw_verdict!r}"
    for required in ("lane_id", "ledger_turn_id"):
        value = verdict.get(required)
        if not isinstance(value, str) or not value:
            return (
                f"verdict_field_must_be_non_empty_string: "
                f"{required}={value!r} ({type(value).__name__})"
            )
    if raw_verdict == "human":
        # reason is required when the schema says so (description-only,
        # but the runner is the producer here so we hold ourselves to it).
        reason = verdict.get("reason")
        if not isinstance(reason, str):
            return f"verdict_human_reason_not_string: {type(reason).__name__}: {reason!r}"
        if reason not in ALLOWED_REASONS:
            return f"verdict_unknown_reason: {reason!r}"
    findings = verdict.get("findings", [])
    if not isinstance(findings, list):
        return f"verdict_findings_not_array: {type(findings).__name__}"
    for i, finding in enumerate(findings):
        finding_err = _validate_finding(finding, i)
        if finding_err is not None:
            return finding_err
    if "rationale" in verdict and not isinstance(verdict["rationale"], str):
        return f"verdict_rationale_not_string: {type(verdict['rationale']).__name__}"
    return None


def _validate_finding(finding: Any, idx: int) -> Optional[str]:
    if not isinstance(finding, dict):
        return f"verdict_findings[{idx}]_not_object: {type(finding).__name__}"
    severity = finding.get("severity")
    if not isinstance(severity, str):
        return (
            f"verdict_findings[{idx}].severity_not_string: {type(severity).__name__}: {severity!r}"
        )
    if severity not in ALLOWED_FINDING_SEVERITIES:
        return f"verdict_findings[{idx}].severity_unknown: {severity!r}"
    message = finding.get("message")
    if not isinstance(message, str) or not message:
        return (
            f"verdict_findings[{idx}].message_must_be_non_empty_string: "
            f"{type(message).__name__}: {message!r}"
        )
    if "suggested_action" in finding:
        suggested = finding["suggested_action"]
        if not isinstance(suggested, str):
            return (
                f"verdict_findings[{idx}].suggested_action_not_string: "
                f"{type(suggested).__name__}: {suggested!r}"
            )
        if suggested not in ALLOWED_SUGGESTED_ACTIONS:
            return f"verdict_findings[{idx}].suggested_action_unknown: {suggested!r}"
    return None


def write_verdict(verdict: Dict[str, Any], *, bundle_dir: Path) -> Path:
    """Schema-or-die write to ``<bundle>/verdict.json``.

    Atomic via per-call ``.tmp`` + ``Path.replace``. Refuses to persist
    a verdict that fails ``validate_verdict``.
    """
    structural = validate_verdict(verdict)
    if structural is not None:
        raise VerdictWriteError(f"refusing to write malformed verdict ({structural})")
    target = bundle_dir / "verdict.json"
    tmp = bundle_dir / f"verdict.{uuid.uuid4().hex}.tmp"
    try:
        tmp.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        tmp.replace(target)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError as exc:
                # Best-effort cleanup — the verdict write itself
                # succeeded; a leftover .tmp will be overwritten by
                # the next call's unique filename.
                print(
                    f"warning: failed to remove temporary file {tmp}: {exc}",
                    file=sys.stderr,
                )
    return target


def run(bundle_dir: Path) -> Dict[str, Any]:
    """Execute the runner against ``bundle_dir`` and return a structured
    response. Tests import this directly so they don't drive the CLI.
    """
    if not bundle_dir.exists():
        return {"ok": False, "error": f"bundle_not_found: {bundle_dir}", "exit": 2}
    if not bundle_dir.is_dir():
        return {"ok": False, "error": f"bundle_not_directory: {bundle_dir}", "exit": 2}

    ledger, fail_reason = read_ledger(bundle_dir)
    if fail_reason is not None and fail_reason != "ledger_status_missing":
        # Hard-fail: ledger missing or invalid. The dispatcher's contract
        # says the verifier returns human + claim_ledger_missing_or_invalid.
        # The specific structural reason rides in the rationale so
        # operators can debug.
        verdict = make_human_verdict(
            lane_id=_safe_lane_id(ledger),
            ledger_turn_id=_safe_turn_id(ledger, bundle_dir),
            reason="claim_ledger_missing_or_invalid",
            rationale=f"Ledger fast-fail: {fail_reason}",
        )
        try:
            target = write_verdict(verdict, bundle_dir=bundle_dir)
        except VerdictWriteError as exc:
            return {"ok": False, "error": str(exc), "exit": 3}
        except OSError as exc:
            return {
                "ok": False,
                "error": f"verdict_write_failed: {exc}",
                "exit": 3,
            }
        return {
            "ok": True,
            "verdict_path": str(target),
            "verdict": verdict["verdict"],
            "reason": verdict["reason"],
            "fast_fail_reason": fail_reason,
            "exit": 0,
        }

    if fail_reason == "ledger_status_missing":
        # The dispatcher already wrote a status='missing' stub for this
        # turn. Same contract: human verdict, claim_ledger_missing_or_invalid.
        verdict = make_human_verdict(
            lane_id=ledger.get("lane_id", "unknown"),
            ledger_turn_id=ledger.get("turn_id", "unknown"),
            reason="claim_ledger_missing_or_invalid",
            rationale=(
                f"Stop dispatcher wrote a missing-stub for this turn "
                f"(reason: {ledger.get('reason', 'unknown')!r}). The builder "
                f"did not call /checkpoint or the pending ledger was malformed."
            ),
        )
        try:
            target = write_verdict(verdict, bundle_dir=bundle_dir)
        except VerdictWriteError as exc:
            return {"ok": False, "error": str(exc), "exit": 3}
        except OSError as exc:
            return {
                "ok": False,
                "error": f"verdict_write_failed: {exc}",
                "exit": 3,
            }
        return {
            "ok": True,
            "verdict_path": str(target),
            "verdict": verdict["verdict"],
            "reason": verdict["reason"],
            "fast_fail_reason": "ledger_status_missing",
            "exit": 0,
        }

    # Valid status='normal' ledger. The Codex invocation lives in a
    # future PR (alongside redaction wiring). Until then the runner
    # exits cleanly without writing a verdict — the bundle stays in a
    # "ready for codex" state and a later run picks it up.
    return {
        "ok": True,
        "verdict_path": None,
        "deferred": True,
        "deferred_reason": "codex_invocation_not_yet_implemented",
        "ledger_lane_id": ledger["lane_id"],
        "ledger_turn_id": ledger["turn_id"],
        "exit": 0,
    }


def _safe_lane_id(ledger: Optional[Dict[str, Any]]) -> str:
    """Pull lane_id off a possibly-malformed ledger without crashing."""
    if isinstance(ledger, dict):
        v = ledger.get("lane_id")
        if isinstance(v, str) and v:
            return v
    return "unknown"


def _safe_turn_id(ledger: Optional[Dict[str, Any]], bundle_dir: Path) -> str:
    """Pull turn_id off a possibly-malformed ledger; fall back to the
    bundle dir name (the dispatcher writes per ``<sid>/<tid>/`` so the
    leaf is the turn id)."""
    if isinstance(ledger, dict):
        v = ledger.get("turn_id")
        if isinstance(v, str) and v:
            return v
    return bundle_dir.name or "unknown"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verifier runner for PopKit bundle directories.",
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        required=True,
        help="Path to a per-turn bundle directory written by the Stop dispatcher.",
    )
    args = parser.parse_args(argv)

    response = run(args.bundle.resolve())
    rc = response.pop("exit", 0)
    print(json.dumps(response, indent=2))
    if not response.get("ok", False):
        return rc if rc != 0 else 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
