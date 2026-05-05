#!/usr/bin/env python3
"""
Tests for lanes_doctor.py.

Round-4 #8 + round-6 #7 directives:
- Lane file_ownership overlap rejected unless both lanes opt in via
  shared_ownership=True + priority.
- Path normalization is Phase-0 cheap-cases-only:
  case-insensitive, slash-canonical, drive-letter, UNC string. Symlink
  / junction resolution is deferred to a later phase.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_doctor_module():
    here = Path(__file__).resolve()
    doctor_path = here.parent.parent / "lanes_doctor.py"
    spec = importlib.util.spec_from_file_location("lanes_doctor", doctor_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def doctor():
    return _load_doctor_module()


# ---------------------------------------------------------------------------
# Path normalization
# ---------------------------------------------------------------------------


class TestNormalizePath:
    def test_lowercases(self, doctor):
        assert doctor.normalize_path("Apps/Shprd/Foo") == "apps/shprd/foo"

    def test_drive_letter_casing(self, doctor):
        assert doctor.normalize_path("C:/Foo/Bar") == "c:/foo/bar"
        assert doctor.normalize_path("c:/foo/bar") == "c:/foo/bar"

    def test_backslash_to_forward(self, doctor):
        assert doctor.normalize_path("c:\\foo\\bar") == "c:/foo/bar"

    def test_mixed_slashes(self, doctor):
        assert doctor.normalize_path("C:/foo\\bar") == "c:/foo/bar"

    def test_unc_path_normalized(self, doctor):
        # The double-leading-slash form
        assert doctor.normalize_path("//server/share/path") == "//server/share/path"
        # The Windows UNC form
        assert (
            doctor.normalize_path("\\\\server\\share\\path") == "//server/share/path"
        )

    def test_trailing_slash_stripped(self, doctor):
        assert doctor.normalize_path("foo/bar/") == "foo/bar"

    def test_root_preserved(self, doctor):
        assert doctor.normalize_path("/") == "/"

    def test_empty_string(self, doctor):
        assert doctor.normalize_path("") == ""


# ---------------------------------------------------------------------------
# Glob overlap detection
# ---------------------------------------------------------------------------


class TestGlobsCanOverlap:
    def test_same_glob_overlaps_itself(self, doctor):
        assert doctor.globs_can_overlap("apps/**", "apps/**")

    def test_globstar_contains_subpath(self, doctor):
        assert doctor.globs_can_overlap("apps/**", "apps/sub/*")

    def test_disjoint_globs_do_not_overlap(self, doctor):
        assert not doctor.globs_can_overlap("apps/**", "lib/**")

    def test_case_insensitive_overlap(self, doctor):
        # Round-6 #7 — Windows-aware case-insensitive comparison
        assert doctor.globs_can_overlap("Apps/**", "apps/sub/*")

    def test_slash_canonical_overlap(self, doctor):
        # Round-6 #7 — backslash and forward-slash forms canonicalize
        assert doctor.globs_can_overlap("apps\\src\\**", "apps/src/foo")

    def test_question_mark_glob(self, doctor):
        assert doctor.globs_can_overlap("file?.txt", "file1.txt")
        assert not doctor.globs_can_overlap("file?.txt", "filename.txt")


# ---------------------------------------------------------------------------
# Lane overlap policy
# ---------------------------------------------------------------------------


def _lane(id_, file_ownership, **extra):
    base = {
        "id": id_,
        "file_ownership": file_ownership,
    }
    base.update(extra)
    return base


class TestCheckLaneOverlap:
    def test_disjoint_lanes_no_errors(self, doctor):
        lanes = [
            _lane("a", ["apps/**"]),
            _lane("b", ["lib/**"]),
        ]
        assert doctor.check_lane_overlap(lanes) == []

    def test_overlapping_lanes_without_opt_in_rejected(self, doctor):
        lanes = [
            _lane("a", ["apps/**"]),
            _lane("b", ["apps/sub/*"]),
        ]
        errors = doctor.check_lane_overlap(lanes)
        assert len(errors) == 1
        assert "shared_ownership=true" in errors[0]
        assert "'a'" in errors[0]
        assert "'b'" in errors[0]

    def test_overlapping_lanes_with_both_opt_in_allowed(self, doctor):
        lanes = [
            _lane("a", ["apps/**"], shared_ownership=True, priority=1),
            _lane("b", ["apps/sub/*"], shared_ownership=True, priority=2),
        ]
        assert doctor.check_lane_overlap(lanes) == []

    def test_one_sided_opt_in_still_rejected(self, doctor):
        # If only one lane opts in, the overlap is still ambiguous.
        lanes = [
            _lane("a", ["apps/**"], shared_ownership=True, priority=1),
            _lane("b", ["apps/sub/*"]),  # b did NOT declare shared_ownership
        ]
        errors = doctor.check_lane_overlap(lanes)
        assert len(errors) == 1


# ---------------------------------------------------------------------------
# Worktree drift detection
# ---------------------------------------------------------------------------


class TestCheckWorktreeDrift:
    def test_clean_match(self, doctor):
        lanes = [
            {"id": "a", "worktree": "C:/repo/main", "branch": "main"},
        ]
        worktrees = [
            {"path": "C:/repo/main", "branch": "main", "commit": "abc"},
        ]
        manifest_only, worktree_only, branch_drift = doctor.check_worktree_drift(
            lanes, worktrees
        )
        assert manifest_only == []
        assert worktree_only == []
        assert branch_drift == []

    def test_manifest_only_warning(self, doctor):
        lanes = [
            {"id": "phantom", "worktree": "C:/repo/ghost", "branch": "main"},
        ]
        worktrees = []
        manifest_only, _, _ = doctor.check_worktree_drift(lanes, worktrees)
        assert len(manifest_only) == 1
        assert "phantom" in manifest_only[0]

    def test_worktree_only_warning(self, doctor):
        lanes = []
        worktrees = [{"path": "C:/repo/wandering", "branch": "main"}]
        _, worktree_only, _ = doctor.check_worktree_drift(lanes, worktrees)
        assert len(worktree_only) == 1
        assert "wandering" in worktree_only[0]

    def test_branch_drift_error(self, doctor):
        lanes = [
            {"id": "a", "worktree": "C:/repo/main", "branch": "feat/expected"},
        ]
        worktrees = [
            {"path": "C:/repo/main", "branch": "feat/actual", "commit": "abc"},
        ]
        _, _, branch_drift = doctor.check_worktree_drift(lanes, worktrees)
        assert len(branch_drift) == 1
        assert "feat/expected" in branch_drift[0]
        assert "feat/actual" in branch_drift[0]

    def test_detached_head_not_drift(self, doctor):
        # Detached HEAD is reported as branch='(detached)'; doctor should
        # not flag this as drift since no specific branch was claimed.
        lanes = [
            {"id": "a", "worktree": "C:/repo/main", "branch": "feat/expected"},
        ]
        worktrees = [
            {"path": "C:/repo/main", "branch": "(detached)", "commit": "abc"},
        ]
        _, _, branch_drift = doctor.check_worktree_drift(lanes, worktrees)
        assert branch_drift == []

    def test_path_normalization_in_drift_check(self, doctor):
        # Manifest declares C:/Foo/Repo, git reports c:\\foo\\repo
        lanes = [
            {"id": "a", "worktree": "C:/Foo/Repo", "branch": "main"},
        ]
        worktrees = [
            {"path": "c:\\foo\\repo", "branch": "main", "commit": "abc"},
        ]
        manifest_only, worktree_only, branch_drift = doctor.check_worktree_drift(
            lanes, worktrees
        )
        # Should be considered the same path; nothing drifts.
        assert manifest_only == []
        assert worktree_only == []
        assert branch_drift == []
