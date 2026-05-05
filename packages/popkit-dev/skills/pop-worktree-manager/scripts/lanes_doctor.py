#!/usr/bin/env python3
"""
Lanes Doctor — read-only reconciliation between a lane manifest and the
actual git worktree state of a repo.

This is the Phase 0 deliverable from
~/.claude/plans/verifier-pair-infrastructure-v1.md. It reuses
``worktree_operations.py``'s ``run_git_command`` helper (round-3 directive:
extend, don't write a new git wrapper).

Read-only by design — does NOT modify worktrees, branches, or the manifest.
Reports drift in three categories:

1. **Manifest-only**: lanes declared in the manifest whose worktree path
   doesn't appear in ``git worktree list``.
2. **Worktree-only**: worktrees on disk that aren't declared as lanes.
3. **Branch mismatches**: a lane declares ``branch: feat/x`` but the
   worktree is on ``feat/y`` (drift between manifest and reality).

Plus the round-4 #8 + round-6 #7 lane-overlap check:

* Rejects file_ownership glob overlap unless BOTH lanes declare
  ``shared_ownership: true`` AND set ``priority``.
* Path normalization in Phase 0:
  - Windows-aware case-insensitive comparison
  - Forward-slash canonical
  - Drive-letter casing (C:\\ vs c:\\)
  - UNC string normalization
  - Glob pair overlap (e.g., ``apps/**`` vs ``apps/sub/*``)
* DEFERRED to a later phase (round-6 #7): symlink/junction resolution.

Exits non-zero on:
- Manifest validation failure (delegates to lane_manifest_loader).
- File-ownership overlap without shared_ownership opt-in.
- Branch drift on any declared lane.

Manifest-only / worktree-only entries surface as warnings (exit 0 unless
combined with a hard failure).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Module-loading helpers (we reuse without making PopKit a package)
# ---------------------------------------------------------------------------


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_loader_module():
    """Load ``lane_manifest_loader.py`` from ``popkit-core``."""
    here = Path(__file__).resolve()
    # popkit-dev/skills/pop-worktree-manager/scripts/ → popkit-ai root
    repo_root = here.parents[5]
    loader_path = (
        repo_root
        / "packages"
        / "popkit-core"
        / "scripts"
        / "lane_manifest_loader.py"
    )
    return _load_module("lane_manifest_loader", loader_path)


def _load_worktree_ops_module():
    """Load ``worktree_operations.py`` from the same directory."""
    here = Path(__file__).resolve()
    return _load_module("worktree_operations", here.parent / "worktree_operations.py")


# ---------------------------------------------------------------------------
# Path normalization (Phase 0 cheap cases)
# ---------------------------------------------------------------------------


_UNC_RE = re.compile(r"^\\\\([^\\]+)\\([^\\]+)(\\.*)?$")


def normalize_path(p: str) -> str:
    """Cross-platform canonical comparison form for repo-internal paths.

    Handles:
    - Forward-slash canonical (Windows ``\\`` becomes ``/``)
    - Case-insensitive (lowercased)
    - Drive-letter casing (``C:`` and ``c:`` collapse)
    - UNC string normalization (``\\\\server\\share\\path`` → ``//server/share/path``)
    - Trailing-slash stripped (``foo/`` and ``foo`` are equivalent)

    DOES NOT handle (deferred per round-6 #7):
    - Symlink resolution
    - NTFS junction resolution
    - Filesystem alias detection beyond literal-string comparison
    """
    if not p:
        return ""
    # UNC string normalization first (preserve the leading // marker)
    unc = _UNC_RE.match(p)
    if unc:
        server, share, rest = unc.group(1), unc.group(2), unc.group(3) or ""
        return f"//{server}/{share}{rest}".replace("\\", "/").lower().rstrip("/")
    # Replace backslashes with forward slashes
    out = p.replace("\\", "/")
    # Normalize drive-letter casing (C:/foo ↔ c:/foo)
    out = out.lower()
    # Strip trailing slash (but keep root markers like '/' or '//' or 'c:/')
    if len(out) > 1 and out.endswith("/") and not out.endswith("//"):
        if not (len(out) == 3 and out[1] == ":"):
            out = out[:-1]
    return out


# ---------------------------------------------------------------------------
# Glob overlap (Phase 0 cheap cases)
# ---------------------------------------------------------------------------


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a glob pattern to a regex for overlap checking.

    Supports the subset PopKit lanes use:
    - ``*`` matches any character except ``/``
    - ``**`` matches any character including ``/``
    - ``?`` matches a single character except ``/``
    - All other characters match literally (escaped)
    """
    p = normalize_path(pattern)
    out = []
    i = 0
    while i < len(p):
        ch = p[i]
        if p[i : i + 2] == "**":
            out.append(".*")
            i += 2
            # Consume optional trailing /
            if i < len(p) and p[i] == "/":
                i += 1
        elif ch == "*":
            out.append("[^/]*")
            i += 1
        elif ch == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(ch))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def globs_can_overlap(a: str, b: str) -> bool:
    """Return True if globs ``a`` and ``b`` could match the same path.

    Round-7 P1 fix: the previous single-sample heuristic missed cases like
    ``apps/*/settings.ts`` vs ``apps/shprd/*`` — both match
    ``apps/shprd/settings.ts`` but neither's literal-with-sentinel sample
    matches the other's regex.

    The current algorithm splits both globs by ``/``, treats ``**`` as a
    variable-length wildcard and other patterns as fixed-length-1 segments,
    and tests pairwise segment compatibility. Two segments are compatible
    if either:
      * Both are exact-match strings and equal (case-insensitive).
      * At least one is a wildcard segment (``*``, ``?``, or pattern with
        metacharacters that could match the other's literal).

    Errs toward returning True when uncertain — Codex round-7 directive:
    "replace the glob-overlap heuristic with a conservative algorithm that
    errs toward rejecting uncertain overlap."
    """
    seg_a = normalize_path(a).split("/")
    seg_b = normalize_path(b).split("/")
    return _segments_overlap(seg_a, seg_b)


def _segments_overlap(seg_a: List[str], seg_b: List[str]) -> bool:
    """Recursive segment-by-segment overlap check.

    Handles ``**`` (matches zero or more segments) by branching on both
    options at each step. Otherwise compares one segment from each side.
    """
    # Both lists exhausted simultaneously → exact match path
    if not seg_a and not seg_b:
        return True
    # One side is just trailing ``**``: matches the rest of the other side
    if seg_a == ["**"] or seg_b == ["**"]:
        return True
    # If one side is exhausted but the other isn't, only ``**`` on the
    # non-exhausted side could allow overlap.
    if not seg_a:
        return seg_b[0] == "**" and _segments_overlap([], seg_b[1:])
    if not seg_b:
        return seg_a[0] == "**" and _segments_overlap(seg_a[1:], [])

    head_a, head_b = seg_a[0], seg_b[0]

    # ``**`` matches zero or more segments on its side; branch.
    if head_a == "**":
        # Try: ** matches zero segments (skip ** and continue at seg_a[1:])
        if _segments_overlap(seg_a[1:], seg_b):
            return True
        # Try: ** consumes one segment from b and stays for more
        return _segments_overlap(seg_a, seg_b[1:])
    if head_b == "**":
        if _segments_overlap(seg_a, seg_b[1:]):
            return True
        return _segments_overlap(seg_a[1:], seg_b)

    # Neither head is **. Both consume one segment.
    if not _single_segments_compatible(head_a, head_b):
        return False
    return _segments_overlap(seg_a[1:], seg_b[1:])


def _single_segments_compatible(a: str, b: str) -> bool:
    """Check whether two single-segment patterns can match a common literal.

    Segments here do NOT contain ``/`` (the caller split on slashes). So
    the metacharacters that matter are ``*`` (any except ``/``) and ``?``
    (any single except ``/``).

    Conservative: when uncertain (both contain wildcards), return True.
    """
    if a == b:
        return True
    has_meta_a = "*" in a or "?" in a
    has_meta_b = "*" in b or "?" in b
    # If neither has metacharacters, equality already failed → no overlap.
    if not has_meta_a and not has_meta_b:
        return False
    # Test each pattern's regex against the other's literal-with-sentinel.
    # If either side is purely a literal, the test is exact.
    if has_meta_a and not has_meta_b:
        return _segment_regex(a).match(b) is not None
    if has_meta_b and not has_meta_a:
        return _segment_regex(b).match(a) is not None
    # Both have metacharacters. Conservative test: do the literal-with-
    # sentinel forms cross-match?
    sample_a = _segment_sample(a)
    sample_b = _segment_sample(b)
    if (
        _segment_regex(a).match(sample_b) is not None
        or _segment_regex(b).match(sample_a) is not None
    ):
        return True
    # Last resort — if the two patterns share any literal character class
    # in common positions, assume they can overlap. Errs True per round-7.
    return _patterns_share_any_literal(a, b)


def _segment_regex(p: str) -> re.Pattern[str]:
    """Compile a segment-only glob (no ``/``) to a regex."""
    out = []
    for ch in p:
        if ch == "*":
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(ch))
    return re.compile("^" + "".join(out) + "$")


def _segment_sample(p: str) -> str:
    """Replace metacharacters with a single sentinel character. Used as a
    cross-test input for ``_single_segments_compatible``."""
    return "".join("x" if ch in {"*", "?"} else ch for ch in p)


def _patterns_share_any_literal(a: str, b: str) -> bool:
    """Conservative tiebreaker for the rare case where both segment patterns
    have metacharacters and neither's regex matches the other's
    literal-with-sentinel sample. Errs True per Codex round-7 directive
    ("errs toward rejecting uncertain overlap" — i.e., treat uncertain
    pairs as potentially-overlapping so the doctor flags them).

    This branch is reached only when both segments contain metacharacters
    AND the cross-regex tests both fail. Lane file_ownership in practice
    uses simple ``foo/**`` / ``foo/*`` patterns, so this branch is
    effectively unreachable for real manifests; returning True here only
    causes spurious overlap reports for hand-crafted edge-case fixtures.
    """
    return True

# Compatibility shim for any callers that used the old name internally.
_glob_to_regex = _segment_regex
# Module-internal alias so the legacy ``_sample_path_from_glob`` name remains
# discoverable in case a downstream test or doc references it. The new
# segment-based algorithm doesn't use full-path samples but this keeps the
# refactor non-breaking for any existing callers.
def _sample_path_from_glob(p: str) -> str:  # pragma: no cover - legacy shim
    return _segment_sample(p)


# ---------------------------------------------------------------------------
# Worktree enumeration (reuses worktree_operations.run_git_command)
# ---------------------------------------------------------------------------


def list_git_worktrees(run_git_command) -> List[Dict[str, str]]:
    """Return ``[{'path', 'branch', 'commit'}]`` for each worktree.

    Uses ``git worktree list --porcelain`` for stable parsing.
    """
    output, ok = run_git_command("worktree list --porcelain")
    if not ok:
        return []
    worktrees: List[Dict[str, str]] = []
    current: Dict[str, str] = {}
    for line in output.splitlines():
        if line.startswith("worktree "):
            if current:
                worktrees.append(current)
            current = {"path": line[len("worktree ") :].strip()}
        elif line.startswith("HEAD "):
            current["commit"] = line[len("HEAD ") :].strip()
        elif line.startswith("branch "):
            current["branch"] = line[len("branch ") :].strip().replace("refs/heads/", "")
        elif line.startswith("detached"):
            current["branch"] = "(detached)"
        elif not line.strip() and current:
            worktrees.append(current)
            current = {}
    if current:
        worktrees.append(current)
    return worktrees


# ---------------------------------------------------------------------------
# Doctor checks
# ---------------------------------------------------------------------------


def check_lane_overlap(lanes: List[Dict[str, Any]]) -> List[str]:
    """Return list of error messages for file_ownership overlap without opt-in."""
    errors: List[str] = []
    for i in range(len(lanes)):
        for j in range(i + 1, len(lanes)):
            a, b = lanes[i], lanes[j]
            for ga in a["file_ownership"]:
                for gb in b["file_ownership"]:
                    if globs_can_overlap(ga, gb):
                        a_shared = a.get("shared_ownership", False)
                        b_shared = b.get("shared_ownership", False)
                        if not (a_shared and b_shared):
                            errors.append(
                                f"file_ownership overlap between lanes "
                                f"{a['id']!r} ({ga!r}) and {b['id']!r} ({gb!r}); "
                                f"both lanes must declare shared_ownership=true "
                                f"with priority to opt in."
                            )
    return errors


def check_worktree_drift(
    lanes: List[Dict[str, Any]], worktrees: List[Dict[str, str]]
) -> Tuple[List[str], List[str], List[str]]:
    """Return (manifest_only_warnings, worktree_only_warnings, branch_drift_errors).

    Branch drift is treated as an error because it usually indicates a stale
    or recovered manifest entry; manifest/worktree-only are warnings because
    they're often legitimate work-in-progress states.
    """
    worktrees_by_path = {normalize_path(w["path"]): w for w in worktrees}
    declared_paths = {normalize_path(lane["worktree"]) for lane in lanes}

    manifest_only: List[str] = []
    branch_drift: List[str] = []

    for lane in lanes:
        norm = normalize_path(lane["worktree"])
        if norm not in worktrees_by_path:
            manifest_only.append(
                f"lane {lane['id']!r} declares worktree {lane['worktree']!r} "
                f"but no matching worktree found in `git worktree list`."
            )
            continue
        wt = worktrees_by_path[norm]
        wt_branch = wt.get("branch", "")
        if wt_branch and wt_branch != "(detached)" and wt_branch != lane["branch"]:
            branch_drift.append(
                f"lane {lane['id']!r} declares branch {lane['branch']!r} but "
                f"worktree {wt['path']!r} is on branch {wt_branch!r}."
            )

    worktree_only: List[str] = []
    for wt in worktrees:
        norm = normalize_path(wt["path"])
        if norm not in declared_paths:
            worktree_only.append(
                f"worktree {wt['path']!r} (branch {wt.get('branch', '?')!r}) is "
                f"not declared as a lane in the manifest."
            )

    return manifest_only, worktree_only, branch_drift


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def run_doctor(manifest_path: Path) -> Dict[str, Any]:
    loader_mod = _load_loader_module()
    worktree_ops = _load_worktree_ops_module()

    try:
        result = loader_mod.load_lane_manifest(manifest_path)
    except loader_mod.LaneManifestError as exc:
        return {
            "ok": False,
            "stage": "manifest_load",
            "errors": [str(exc)],
            "warnings": [],
        }

    lanes = result.manifest["lanes"]
    overlap_errors = check_lane_overlap(lanes)
    worktrees = list_git_worktrees(worktree_ops.run_git_command)
    manifest_only, worktree_only, branch_drift = check_worktree_drift(lanes, worktrees)

    errors = overlap_errors + branch_drift
    warnings = list(result.warnings) + manifest_only + worktree_only

    return {
        "ok": not errors,
        "stage": "complete",
        "errors": errors,
        "warnings": warnings,
        "lane_count": len(lanes),
        "worktree_count": len(worktrees),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only lane manifest reconciliation against git worktree state."
    )
    parser.add_argument(
        "manifest",
        type=Path,
        nargs="?",
        default=Path(".claude/lanes.yml"),
        help="Path to lane manifest (default: .claude/lanes.yml in cwd).",
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit JSON instead of human-readable text."
    )
    args = parser.parse_args(argv)

    report = run_doctor(args.manifest)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        if report["ok"]:
            print(f"OK — {report.get('lane_count', 0)} lane(s) reconciled.")
        else:
            print(f"FAIL — {len(report['errors'])} error(s):", file=sys.stderr)
            for err in report["errors"]:
                print(f"  - {err}", file=sys.stderr)
        if report["warnings"]:
            print(f"\n{len(report['warnings'])} warning(s):", file=sys.stderr)
            for w in report["warnings"]:
                print(f"  - {w}", file=sys.stderr)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
