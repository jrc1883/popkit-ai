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

    Conservative: we test each glob's regex against a synthetic representative
    drawn from the other. For Phase 0, we use a simple containment heuristic:
    if one glob's regex matches the literal portion of the other, they can
    overlap. This catches the cases Plan v4.2 calls out (``apps/**`` vs
    ``apps/sub/*``) without trying to be a full glob-set decision procedure.
    """
    ra, rb = _glob_to_regex(a), _glob_to_regex(b)
    # Generate representative literal paths from each glob.
    sample_a = _sample_path_from_glob(normalize_path(a))
    sample_b = _sample_path_from_glob(normalize_path(b))
    return bool(ra.match(sample_b)) or bool(rb.match(sample_a))


def _sample_path_from_glob(p: str) -> str:
    """Replace glob metacharacters with a sentinel literal so the result is a
    concrete path the *other* glob's regex can be tested against."""
    out = []
    i = 0
    while i < len(p):
        if p[i : i + 2] == "**":
            out.append("x/y/z")
            i += 2
            if i < len(p) and p[i] == "/":
                i += 1
        elif p[i] == "*":
            out.append("xyz")
            i += 1
        elif p[i] == "?":
            out.append("x")
            i += 1
        else:
            out.append(p[i])
            i += 1
    return "".join(out)


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
