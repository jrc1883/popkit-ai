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
import re
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
ALLOWED_LEDGER_GATE_RESULTS = {"pass", "fail", "skip"}
ALLOWED_LEDGER_COMPLIANCE_TOUCH = {
    "none",
    "schema",
    "audit",
    "auth",
    "child-data",
    "ferpa",
    "coppa",
}

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
    # Round-13 P2: bool is an int subclass and ``True == 1`` in Python,
    # so the naive ``!=`` check accepts ``schema_version: true`` as a
    # valid version 1 ledger. Reject bools first.
    raw_version = data.get("schema_version")
    if isinstance(raw_version, bool) or not isinstance(raw_version, int):
        return (
            None,
            f"ledger_schema_version_not_integer: {type(raw_version).__name__}: {raw_version!r}",
        )
    if raw_version != LEDGER_SCHEMA_VERSION:
        return (
            None,
            f"ledger_unsupported_schema_version: {raw_version!r}",
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
    for i, entry in enumerate(data["changed_files"]):
        cf_err = _validate_changed_file_entry(entry, i)
        if cf_err is not None:
            return cf_err
    if not isinstance(data["acceptance_claims"], list):
        return f"ledger_acceptance_claims_not_array: {type(data['acceptance_claims']).__name__}"
    for i, claim in enumerate(data["acceptance_claims"]):
        if not isinstance(claim, str) or not claim:
            return (
                f"ledger_acceptance_claims[{i}]_must_be_non_empty_string: "
                f"{type(claim).__name__}: {claim!r}"
            )

    # Optional fields: type + structural guards matching claim-ledger.schema.json.
    # Round-13 P1: the schema rejects malformed values here, the runner must
    # too — bundles edited in transit can carry malformed advisory data the
    # writer would have rejected.
    if "tests_run" in data:
        tr_err = _validate_tests_run(data["tests_run"])
        if tr_err is not None:
            return tr_err
    if "deterministic_gates_observed" in data:
        gates = data["deterministic_gates_observed"]
        if not isinstance(gates, dict):
            return f"ledger_deterministic_gates_observed_not_object: {type(gates).__name__}"
        for k, v in gates.items():
            if not isinstance(k, str) or not k:
                return (
                    f"ledger_deterministic_gates_observed_key_must_be_non_empty_string: "
                    f"{type(k).__name__}: {k!r}"
                )
            if not isinstance(v, str) or v not in ALLOWED_LEDGER_GATE_RESULTS:
                return (
                    f"ledger_deterministic_gates_observed_value_unknown: "
                    f"key={k!r} value={v!r} ({type(v).__name__})"
                )
    if "compliance_touch" in data:
        ct = data["compliance_touch"]
        if not isinstance(ct, list):
            return f"ledger_compliance_touch_not_array: {type(ct).__name__}"
        for i, c in enumerate(ct):
            if not isinstance(c, str) or c not in ALLOWED_LEDGER_COMPLIANCE_TOUCH:
                return f"ledger_compliance_touch[{i}]_unknown: {type(c).__name__}: {c!r}"
    if "known_gaps" in data:
        gaps = data["known_gaps"]
        if not isinstance(gaps, list):
            return f"ledger_known_gaps_not_array: {type(gaps).__name__}"
        for i, g in enumerate(gaps):
            if not isinstance(g, str):
                return f"ledger_known_gaps[{i}]_not_string: {type(g).__name__}: {g!r}"
    # Round-14 P2: claim-ledger.schema.json's optional ``reason`` field
    # must be a string when present (typically used with status='missing'
    # but the schema allows it on normal ledgers too). Without this guard
    # a normal ledger with reason: 123 / true / {} sailed past the runner
    # straight into the deferred-Codex state.
    if "reason" in data:
        reason = data["reason"]
        if not isinstance(reason, str):
            return f"ledger_reason_not_string: {type(reason).__name__}: {reason!r}"
    return None


def _validate_changed_file_entry(entry: Any, idx: int) -> Optional[str]:
    """Round-13 P1 deep validation of changed_files[].

    Mirrors the rules checkpoint_writer enforces at write time so a bundle
    edited in transit can't sneak malformed advisory data past the
    runner's defense layer.
    """
    if not isinstance(entry, dict):
        return f"ledger_changed_files[{idx}]_not_object: {type(entry).__name__}"
    if "path" not in entry:
        return f"ledger_changed_files[{idx}]_missing_path"
    path = entry["path"]
    if not isinstance(path, str) or not path:
        return (
            f"ledger_changed_files[{idx}].path_must_be_non_empty_string: "
            f"{type(path).__name__}: {path!r}"
        )
    # Round-14 P2: same checkpoint_writer rules apply here. The runner
    # is the last gate before Codex; an edited-in-transit bundle could
    # carry C:/secret.txt or ../outside.py and slip past until now.
    path_err = _validate_repo_relative_path(path, prefix=f"ledger_changed_files[{idx}].path")
    if path_err is not None:
        return path_err
    for k in ("added", "removed"):
        if k in entry:
            v = entry[k]
            # bool is an int subclass; reject explicitly.
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                return (
                    f"ledger_changed_files[{idx}].{k}_not_non_negative_integer: "
                    f"{type(v).__name__}: {v!r}"
                )
    return None


def _validate_tests_run(tests_run: Any) -> Optional[str]:
    if not isinstance(tests_run, list):
        return f"ledger_tests_run_not_array: {type(tests_run).__name__}"
    for i, t in enumerate(tests_run):
        if not isinstance(t, dict):
            return f"ledger_tests_run[{i}]_not_object: {type(t).__name__}"
        name = t.get("name")
        if not isinstance(name, str) or not name:
            return (
                f"ledger_tests_run[{i}].name_must_be_non_empty_string: "
                f"{type(name).__name__}: {name!r}"
            )
        for k in ("passed", "failed"):
            if k in t:
                v = t[k]
                if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                    return (
                        f"ledger_tests_run[{i}].{k}_not_non_negative_integer: "
                        f"{type(v).__name__}: {v!r}"
                    )
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
    # Round-13 P2: bool is an int subclass and ``True == 1`` in Python,
    # so the naive ``!=`` check accepts ``schema_version: true`` as a
    # valid version 1 verdict. Reject bools first.
    raw_version = verdict.get("schema_version")
    if isinstance(raw_version, bool) or not isinstance(raw_version, int):
        return f"verdict_schema_version_not_integer: {type(raw_version).__name__}: {raw_version!r}"
    if raw_version != VERIFIER_RESULT_SCHEMA_VERSION:
        return f"verdict_unsupported_schema_version: {raw_version!r}"
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
    # Round-14 P2: verifier-result.schema.json constrains ``reason``
    # whenever it is present on the verdict, not just for human verdicts.
    # A pass/feedback/block verdict with reason: 123 / 'bogus_reason'
    # used to slip past the schema-or-die guard. Now we validate the
    # field for every verdict shape, AND additionally require it for
    # human verdicts.
    if "reason" in verdict:
        reason = verdict["reason"]
        if not isinstance(reason, str):
            return f"verdict_reason_not_string: {type(reason).__name__}: {reason!r}"
        if reason not in ALLOWED_REASONS:
            return f"verdict_unknown_reason: {reason!r}"
    elif raw_verdict == "human":
        # human verdicts must always carry a reason — the dispatcher
        # routes on it (claim_ledger_missing_or_invalid, etc.).
        return "verdict_human_reason_missing"
    findings = verdict.get("findings", [])
    if not isinstance(findings, list):
        return f"verdict_findings_not_array: {type(findings).__name__}"
    for i, finding in enumerate(findings):
        finding_err = _validate_finding(finding, i)
        if finding_err is not None:
            return finding_err
    # Round-15 P2: cross-field consistency. The schema's findings field
    # description says "Empty array on verdict='pass'. Non-empty on
    # feedback/block/human." A contradictory verdict (pass with findings,
    # or feedback/block with no findings) is exactly the boundary the
    # future dispatcher routing keys off — reject before write so the
    # dispatcher never has to disambiguate.
    #
    # human verdicts are intentionally exempt from the non-empty rule:
    # the procedural fast-fail path (claim_ledger_missing_or_invalid)
    # carries its evidence in ``rationale`` and ``reason``, not findings.
    if raw_verdict == "pass" and findings:
        return f"verdict_pass_with_findings: got {len(findings)} findings"
    if raw_verdict in {"feedback", "block"} and not findings:
        return f"verdict_{raw_verdict}_without_findings"
    if "rationale" in verdict and not isinstance(verdict["rationale"], str):
        return f"verdict_rationale_not_string: {type(verdict['rationale']).__name__}"
    return None


_BRACKET_NON_DIGIT_RE = re.compile(r"\[[^\]]*\]")


def _redact_for_rationale(reason: Optional[str]) -> str:
    """Strip raw user values from a fail-reason category string.

    Round-15 P2: verifier-result.schema.json says rationale is "redaction-
    safe" — never raw PII or fixture content. The runner's fail_reason
    strings carry both a category (safe, e.g.
    ``ledger_changed_files[0].path_must_be_repo_relative``) AND debug
    detail (potentially unsafe — the offending path/value via ``{!r}``).
    For the persisted verdict's rationale we keep only the category so a
    malformed ledger with PII in changed_files[].path doesn't leak the
    raw path into the verdict artifact.

    The full detail still flows to the runner's CLI response (returned
    on stdout / consumed by tests and operator tooling), where the
    operator can debug structural reasons against the bundle they own.

    Round-15-bis P2: also normalize bracketed dynamic segments. Some
    validator messages historically embedded user-controlled keys inside
    ``[...]`` segments BEFORE the colon (e.g.
    ``ledger_deterministic_gates_observed['child-email@example.com']_unknown``)
    so splitting at the first colon wasn't enough. Now collapse any
    bracketed segment whose contents aren't a pure non-negative integer
    index to ``[*]``. Numeric indexes survive (``changed_files[0]`` →
    ``changed_files[0]``) so operators retain orientation; everything
    else (string keys, repr'd PII) collapses.
    """
    if not reason:
        return "unknown"
    # Reasons follow the convention "category: detail" — split at the
    # first colon. Categories are stable identifiers that don't carry
    # user data; everything after the first ``:`` is debug context.
    head = reason.split(":", 1)[0].strip()
    if not head:
        return "unknown"
    # Defense-in-depth: collapse any bracketed segment that isn't a pure
    # non-negative integer index. The regex matches ``[contents]``;
    # _maybe_redact_bracket inspects ``contents`` and returns either the
    # original (numeric index, kept for orientation) or ``[*]``.
    return _BRACKET_NON_DIGIT_RE.sub(_maybe_redact_bracket, head) or "unknown"


def _maybe_redact_bracket(match: re.Match[str]) -> str:
    inner = match.group(0)[1:-1]
    if inner.isdigit():
        return match.group(0)
    return "[*]"


def _validate_repo_relative_path(path: str, *, prefix: str) -> Optional[str]:
    """Reject absolute / drive-relative / UNC / parent-traversal paths.

    Mirrors checkpoint_writer's changed_files[].path rules so the same
    contract is enforced everywhere a path string flows through the
    verifier surface (ledger.changed_files[].path AND verifier-result
    findings[].file). Caller supplies an audit-friendly ``prefix`` that
    becomes the leading token in the returned reason string.
    """
    if "\\" in path:
        return f"{prefix}_must_use_forward_slashes: {path!r}"
    if path.startswith("/") or (len(path) >= 2 and path[0].isalpha() and path[1] == ":"):
        return f"{prefix}_must_be_repo_relative: got absolute or drive-anchored path {path!r}"
    if any(seg == ".." for seg in path.split("/")):
        return (
            f"{prefix}_must_be_repo_relative: "
            f"parent-directory traversal segments are not allowed, got {path!r}"
        )
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
    # Defense-in-depth on the optional schema fields. The runner only
    # produces empty findings today (the hard-fail path uses
    # ``findings: []``), but validate_verdict is the contract gate for
    # any verdict ANY caller might produce — including the future
    # Codex-driven path. Better to fail closed here than to let a
    # malformed finding reach the dispatcher.
    if "claim_id" in finding:
        claim_id = finding["claim_id"]
        # bool is an int subclass; reject explicitly.
        if isinstance(claim_id, bool) or not isinstance(claim_id, int):
            return (
                f"verdict_findings[{idx}].claim_id_not_integer: "
                f"{type(claim_id).__name__}: {claim_id!r}"
            )
        if claim_id < 0:
            return f"verdict_findings[{idx}].claim_id_negative: {claim_id!r}"
    if "file" in finding:
        f = finding["file"]
        if not isinstance(f, str) or not f:
            return (
                f"verdict_findings[{idx}].file_must_be_non_empty_string: {type(f).__name__}: {f!r}"
            )
        # Round-13 P2: verifier-result.schema.json documents file as
        # "repo-root-relative with forward-slash separators" — same
        # contract as claim-ledger's changed_files[].path. Apply the
        # same checkpoint_writer rules so a Codex-produced finding
        # can't route comments / actions against absolute or
        # parent-traversal paths the dispatcher trusts as repo-local.
        path_err = _validate_repo_relative_path(f, prefix=f"verdict_findings[{idx}].file")
        if path_err is not None:
            return path_err
    if "line" in finding:
        line = finding["line"]
        if isinstance(line, bool) or not isinstance(line, int):
            return f"verdict_findings[{idx}].line_not_integer: {type(line).__name__}: {line!r}"
        if line < 1:
            return f"verdict_findings[{idx}].line_below_one: {line!r}"
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
            # Round-15 P2: persisted rationale must be redaction-safe;
            # only the fail_reason category goes into the verdict
            # artifact. The full debug detail rides on
            # response["fast_fail_reason"] for operator tooling.
            rationale=f"Ledger fast-fail: {_redact_for_rationale(fail_reason)}",
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
        # Round-13 P2: route through the safe helpers so a malformed stub
        # (lane_id: [], turn_id: {}) still produces a verdict file rather
        # than write_verdict's schema-or-die guard rejecting and leaving
        # the bundle without any verdict at all.
        raw_reason = ledger.get("reason") if isinstance(ledger, dict) else None
        rationale_reason = raw_reason if isinstance(raw_reason, str) else "unknown"
        # Round-15 P2: same redaction as the structural-fail path. The
        # dispatcher's stub-reason strings include user values via
        # ``{!r}`` (e.g. pending_invalid_json: <bad JSON bytes>); we
        # keep only the category in the persisted rationale.
        safe_reason_category = _redact_for_rationale(rationale_reason)
        verdict = make_human_verdict(
            lane_id=_safe_lane_id(ledger),
            ledger_turn_id=_safe_turn_id(ledger, bundle_dir),
            reason="claim_ledger_missing_or_invalid",
            rationale=(
                f"Stop dispatcher wrote a missing-stub for this turn "
                f"(reason: {safe_reason_category}). The builder "
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
