#!/usr/bin/env python3
"""
Test suite for session_branch_manager.py

Tests DAG-based session branching: create, switch, merge, delete branches,
history tracking, context/task updates, and nested branch operations.
"""

import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from popkit_shared.utils.session_branch_manager import (
    create_branch,
    delete_branch,
    get_branch_history,
    get_current_branch,
    list_branches,
    merge_branch,
    switch_branch,
    update_branch_context,
    update_branch_tasks,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def isolated_workdir(tmp_path, monkeypatch):
    """Isolate every test in a fresh temp directory so STATUS.json never
    touches the real project.  Because the module resolves the status path
    via Path.cwd(), chdir is all we need."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def workdir_with_claude(isolated_workdir):
    """A working directory that already has a .claude/ folder, so the module
    writes STATUS.json inside it (the preferred path)."""
    claude_dir = isolated_workdir / ".claude"
    claude_dir.mkdir()
    return isolated_workdir


@pytest.fixture
def seeded_branch(isolated_workdir):
    """Create a single feature branch and return its data.
    The current branch will be the newly created branch."""
    return create_branch("feature-x", reason="Investigate feature X")


@pytest.fixture
def merged_branch(seeded_branch):
    """Create a branch, merge it, and return the merge result.
    Current branch switches back to main after merge."""
    return merge_branch("feature-x", outcome="Resolved feature X")


# =============================================================================
# Helpers
# =============================================================================


def _read_status(workdir: Path) -> dict:
    """Read the raw STATUS.json for assertions that go beyond the public API."""
    claude_path = workdir / ".claude" / "STATUS.json"
    root_path = workdir / "STATUS.json"
    path = claude_path if claude_path.exists() else root_path
    return json.loads(path.read_text())


# =============================================================================
# Tests -- create_branch
# =============================================================================


class TestCreateBranch:
    """Tests for create_branch()."""

    def test_create_branch_from_main(self, isolated_workdir):
        """Creating a branch from main sets parent to 'main' and switches to it."""
        result = create_branch("auth-bug", reason="Investigating token expiry")

        assert result["id"] == "auth-bug"
        assert result["parent"] == "main"
        assert result["reason"] == "Investigating token expiry"
        assert result["merged"] is False

        # Current branch should now be the new branch
        current_id, current_data = get_current_branch()
        assert current_id == "auth-bug"
        assert current_data["id"] == "auth-bug"

    def test_create_branch_copies_context_by_default(self, isolated_workdir):
        """With copy_context=True (default), the parent context is copied."""
        # Seed main with some context first
        update_branch_context({"focus": "deployment"}, branch_id="main")

        result = create_branch("deploy-fix", reason="Fix deploy pipeline")

        assert result["context"].get("focus") == "deployment"

    def test_create_branch_without_context_copy(self, isolated_workdir):
        """With copy_context=False, the new branch starts with empty context."""
        update_branch_context({"focus": "deployment"}, branch_id="main")

        result = create_branch("clean-start", reason="Fresh investigation", copy_context=False)

        assert result["context"] == {}
        assert result["git"] == {}

    def test_create_branch_initializes_empty_tasks(self, isolated_workdir):
        """New branches always get empty task lists regardless of copy_context."""
        result = create_branch("task-test", reason="Check tasks")

        assert result["tasks"] == {"inProgress": [], "completed": [], "blocked": []}

    def test_create_duplicate_branch_raises(self, seeded_branch):
        """Creating a branch with an existing ID raises ValueError."""
        with pytest.raises(ValueError, match="already exists"):
            create_branch("feature-x", reason="duplicate")

    def test_create_branch_empty_id_raises(self, isolated_workdir):
        """Empty string ID raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            create_branch("", reason="no id")

    def test_create_branch_with_spaces_raises(self, isolated_workdir):
        """Branch ID containing spaces raises ValueError."""
        with pytest.raises(ValueError, match="no spaces or slashes"):
            create_branch("my branch", reason="bad id")

    def test_create_branch_with_slash_raises(self, isolated_workdir):
        """Branch ID containing slashes raises ValueError."""
        with pytest.raises(ValueError, match="no spaces or slashes"):
            create_branch("feat/auth", reason="bad id")

    def test_create_branch_records_history(self, isolated_workdir):
        """Creating a branch appends a 'branch' entry to history."""
        create_branch("hist-test", reason="History check")

        history = get_branch_history()
        assert len(history) == 1
        assert history[0]["action"] == "branch"
        assert history[0]["from"] == "main"
        assert history[0]["to"] == "hist-test"
        assert history[0]["reason"] == "History check"

    def test_create_branch_writes_to_claude_dir(self, workdir_with_claude):
        """When .claude/ exists, STATUS.json is written inside it."""
        create_branch("claude-dir-test", reason="Path check")

        status_path = workdir_with_claude / ".claude" / "STATUS.json"
        assert status_path.exists()
        # Root-level STATUS.json should NOT exist
        assert not (workdir_with_claude / "STATUS.json").exists()


# =============================================================================
# Tests -- switch_branch
# =============================================================================


class TestSwitchBranch:
    """Tests for switch_branch()."""

    def test_switch_to_existing_branch(self, seeded_branch):
        """Switching to an existing branch updates current branch."""
        # seeded_branch leaves us on feature-x; switch back to main
        result = switch_branch("main")

        assert result["id"] == "main"
        current_id, _ = get_current_branch()
        assert current_id == "main"

    def test_switch_to_nonexistent_branch_raises(self, isolated_workdir):
        """Switching to a branch that doesn't exist raises ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            switch_branch("ghost-branch")

    def test_switch_to_current_branch_is_noop(self, seeded_branch):
        """Switching to the already-current branch returns data without history entry."""
        history_before = get_branch_history()
        result = switch_branch("feature-x")

        assert result["id"] == "feature-x"
        # No new history entry for a no-op switch
        history_after = get_branch_history()
        assert len(history_after) == len(history_before)

    def test_switch_records_history(self, seeded_branch):
        """Switching branches appends a 'switch' entry to history."""
        switch_branch("main")

        history = get_branch_history()
        switch_entries = [h for h in history if h["action"] == "switch"]
        assert len(switch_entries) == 1
        assert switch_entries[0]["from"] == "feature-x"
        assert switch_entries[0]["to"] == "main"


# =============================================================================
# Tests -- merge_branch
# =============================================================================


class TestMergeBranch:
    """Tests for merge_branch()."""

    def test_merge_branch_to_parent(self, seeded_branch):
        """Merging a branch marks it merged and switches to the parent."""
        result = merge_branch("feature-x", outcome="Fixed the bug")

        assert result["merged"] is True
        assert result["from"] == "feature-x"
        assert result["to"] == "main"
        assert result["outcome"] == "Fixed the bug"

        # Should now be on main
        current_id, _ = get_current_branch()
        assert current_id == "main"

    def test_merge_marks_branch_merged(self, seeded_branch):
        """After merge the branch data carries merged=True and a timestamp."""
        merge_branch("feature-x", outcome="Done")

        branches = list_branches()
        feature = next(b for b in branches if b["id"] == "feature-x")
        assert feature["merged"] is True
        assert feature["merged_at"] is not None

    def test_merge_with_delete(self, seeded_branch):
        """delete_after_merge=True removes the branch from the listing."""
        merge_branch("feature-x", outcome="Done", delete_after_merge=True)

        branch_ids = [b["id"] for b in list_branches()]
        assert "feature-x" not in branch_ids

    def test_merge_copies_outcome_to_parent_context(self, seeded_branch):
        """Merge outcome is recorded in the parent's recentMerges context."""
        merge_branch("feature-x", outcome="Token refresh fixed")

        _, main_data = get_current_branch()
        recent = main_data.get("context", {}).get("recentMerges", [])
        assert len(recent) == 1
        assert recent[0]["branch"] == "feature-x"
        assert recent[0]["outcome"] == "Token refresh fixed"

    def test_merge_copies_key_decisions(self, seeded_branch):
        """Key decisions from branch context are prefixed and merged to parent."""
        update_branch_context(
            {"keyDecisions": ["Use JWT refresh tokens"]},
            branch_id="feature-x",
        )
        merge_branch("feature-x", outcome="Decision made")

        _, main_data = get_current_branch()
        decisions = main_data.get("context", {}).get("keyDecisions", [])
        assert any("[feature-x]" in d for d in decisions)

    def test_merge_main_raises(self, isolated_workdir):
        """Merging the main branch raises ValueError."""
        with pytest.raises(ValueError, match="Cannot merge main"):
            merge_branch("main", outcome="nope")

    def test_merge_nonexistent_branch_raises(self, isolated_workdir):
        """Merging a non-existent branch raises ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            merge_branch("phantom", outcome="nope")

    def test_merge_records_history(self, seeded_branch):
        """Merging a branch appends a 'merge' entry to history."""
        merge_branch("feature-x", outcome="All good")

        history = get_branch_history()
        merge_entries = [h for h in history if h["action"] == "merge"]
        assert len(merge_entries) == 1
        assert merge_entries[0]["from"] == "feature-x"
        assert merge_entries[0]["to"] == "main"
        assert merge_entries[0]["outcome"] == "All good"

    def test_merge_keeps_only_last_five_recent_merges(self, isolated_workdir):
        """The recentMerges list on the parent is capped at 5."""
        for i in range(7):
            branch_id = f"branch-{i}"
            create_branch(branch_id, reason=f"Branch {i}")
            merge_branch(branch_id, outcome=f"Outcome {i}")

        _, main_data = get_current_branch()
        recent = main_data.get("context", {}).get("recentMerges", [])
        assert len(recent) == 5
        # The last 5 should be branches 2..6
        assert recent[0]["branch"] == "branch-2"
        assert recent[-1]["branch"] == "branch-6"


# =============================================================================
# Tests -- delete_branch
# =============================================================================


class TestDeleteBranch:
    """Tests for delete_branch()."""

    def test_delete_merged_branch(self, merged_branch):
        """Deleting a merged branch succeeds and returns True."""
        result = delete_branch("feature-x")

        assert result is True
        branch_ids = [b["id"] for b in list_branches()]
        assert "feature-x" not in branch_ids

    def test_delete_unmerged_without_force_raises(self, seeded_branch):
        """Deleting an unmerged branch without force raises ValueError."""
        # Switch away first so it's not the current branch
        switch_branch("main")

        with pytest.raises(ValueError, match="not merged"):
            delete_branch("feature-x")

    def test_delete_unmerged_with_force(self, seeded_branch):
        """Deleting an unmerged branch with force=True succeeds."""
        switch_branch("main")

        result = delete_branch("feature-x", force=True)
        assert result is True
        branch_ids = [b["id"] for b in list_branches()]
        assert "feature-x" not in branch_ids

    def test_delete_main_raises(self, isolated_workdir):
        """Deleting the main branch raises ValueError."""
        with pytest.raises(ValueError, match="Cannot delete main"):
            delete_branch("main")

    def test_delete_current_branch_raises(self, seeded_branch):
        """Deleting the current branch raises ValueError."""
        # seeded_branch leaves us on feature-x
        with pytest.raises(ValueError, match="Cannot delete current branch"):
            delete_branch("feature-x")

    def test_delete_nonexistent_branch_raises(self, isolated_workdir):
        """Deleting a branch that doesn't exist raises ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            delete_branch("no-such-branch")

    def test_delete_records_history(self, merged_branch):
        """Deleting a branch appends a 'delete' entry to history."""
        delete_branch("feature-x")

        history = get_branch_history()
        delete_entries = [h for h in history if h["action"] == "delete"]
        assert len(delete_entries) == 1
        assert delete_entries[0]["branch"] == "feature-x"
        assert delete_entries[0]["forced"] is False

    def test_force_delete_records_forced_flag(self, seeded_branch):
        """Force-deleting an unmerged branch records forced=True in history."""
        switch_branch("main")
        delete_branch("feature-x", force=True)

        history = get_branch_history()
        delete_entries = [h for h in history if h["action"] == "delete"]
        assert delete_entries[0]["forced"] is True


# =============================================================================
# Tests -- list_branches
# =============================================================================


class TestListBranches:
    """Tests for list_branches()."""

    def test_list_default_has_main(self, isolated_workdir):
        """A fresh state lists only main, marked active."""
        branches = list_branches()

        assert len(branches) == 1
        assert branches[0]["id"] == "main"
        assert branches[0]["active"] is True
        assert branches[0]["parent"] is None

    def test_list_shows_active_status(self, seeded_branch):
        """The active flag is True only for the current branch."""
        branches = list_branches()

        main_branch = next(b for b in branches if b["id"] == "main")
        feature_branch = next(b for b in branches if b["id"] == "feature-x")

        assert main_branch["active"] is False
        assert feature_branch["active"] is True

    def test_list_shows_merged_status(self, merged_branch):
        """Merged branches show merged=True with a timestamp."""
        branches = list_branches()

        feature = next(b for b in branches if b["id"] == "feature-x")
        assert feature["merged"] is True
        assert feature["merged_at"] is not None

    def test_list_main_always_first(self, isolated_workdir):
        """Main branch always appears first in the listing."""
        create_branch("aaa-first-alpha", reason="Should not be first")
        switch_branch("main")
        create_branch("zzz-last-alpha", reason="Should not be first")

        branches = list_branches()
        assert branches[0]["id"] == "main"

    def test_list_multiple_branches(self, isolated_workdir):
        """All created branches appear in the listing."""
        create_branch("branch-a", reason="A")
        switch_branch("main")
        create_branch("branch-b", reason="B")

        branches = list_branches()
        ids = {b["id"] for b in branches}
        assert ids == {"main", "branch-a", "branch-b"}


# =============================================================================
# Tests -- get_current_branch
# =============================================================================


class TestGetCurrentBranch:
    """Tests for get_current_branch()."""

    def test_default_is_main(self, isolated_workdir):
        """On a fresh state the current branch is main."""
        branch_id, branch_data = get_current_branch()

        assert branch_id == "main"
        assert branch_data["id"] == "main"
        assert branch_data["parent"] is None

    def test_returns_correct_branch_after_create(self, seeded_branch):
        """After creating a branch, current branch reflects the new one."""
        branch_id, branch_data = get_current_branch()

        assert branch_id == "feature-x"
        assert branch_data["reason"] == "Investigate feature X"

    def test_returns_correct_branch_after_switch(self, seeded_branch):
        """After switching, current branch reflects the target."""
        switch_branch("main")
        branch_id, _ = get_current_branch()
        assert branch_id == "main"


# =============================================================================
# Tests -- get_branch_history
# =============================================================================


class TestGetBranchHistory:
    """Tests for get_branch_history()."""

    def test_empty_history_on_fresh_state(self, isolated_workdir):
        """Fresh state has no history entries."""
        history = get_branch_history()
        assert history == []

    def test_history_records_all_operations(self, isolated_workdir):
        """History captures branch, switch, merge, and delete actions."""
        create_branch("track-all", reason="Track ops")  # branch
        switch_branch("main")  # switch
        switch_branch("track-all")  # switch
        merge_branch("track-all", outcome="Done")  # merge
        # Create another branch to delete
        create_branch("to-delete", reason="Will be deleted")  # branch
        switch_branch("main")  # switch
        delete_branch("to-delete", force=True)  # delete

        history = get_branch_history()
        actions = [h["action"] for h in history]

        assert "branch" in actions
        assert "switch" in actions
        assert "merge" in actions
        assert "delete" in actions

    def test_history_most_recent_first(self, isolated_workdir):
        """History is returned with the most recent entry first."""
        create_branch("first", reason="First")
        switch_branch("main")
        create_branch("second", reason="Second")

        history = get_branch_history()
        # Most recent entry is the second branch creation
        assert history[0]["to"] == "second"

    def test_history_respects_limit(self, isolated_workdir):
        """The limit parameter caps the number of returned entries."""
        for i in range(10):
            create_branch(f"lim-{i}", reason=f"Branch {i}")
            switch_branch("main")

        history = get_branch_history(limit=3)
        assert len(history) == 3

    def test_history_limit_default(self, isolated_workdir):
        """Default limit is 20."""
        for i in range(25):
            create_branch(f"def-{i}", reason=f"Branch {i}")
            switch_branch("main")

        history = get_branch_history()
        assert len(history) == 20


# =============================================================================
# Tests -- update_branch_context
# =============================================================================


class TestUpdateBranchContext:
    """Tests for update_branch_context()."""

    def test_update_current_branch_context(self, seeded_branch):
        """Updating context without branch_id targets the current branch."""
        result = update_branch_context({"focus": "auth module"})

        assert result["context"]["focus"] == "auth module"
        assert "lastUpdated" in result

    def test_update_specific_branch_context(self, seeded_branch):
        """Updating context with explicit branch_id targets that branch."""
        result = update_branch_context({"focus": "deploy"}, branch_id="main")

        assert result["context"]["focus"] == "deploy"
        # Current branch context should be unchanged
        _, current = get_current_branch()
        assert current["context"].get("focus") != "deploy"

    def test_update_context_merges_keys(self, seeded_branch):
        """Multiple updates merge keys, later values overwrite earlier ones."""
        update_branch_context({"a": 1, "b": 2})
        result = update_branch_context({"b": 99, "c": 3})

        assert result["context"]["a"] == 1
        assert result["context"]["b"] == 99
        assert result["context"]["c"] == 3

    def test_update_context_nonexistent_branch_raises(self, isolated_workdir):
        """Updating context for a non-existent branch raises ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            update_branch_context({"key": "val"}, branch_id="ghost")

    def test_update_context_sets_last_updated(self, seeded_branch):
        """Updating context sets the lastUpdated timestamp."""
        result = update_branch_context({"x": 1})
        assert "lastUpdated" in result


# =============================================================================
# Tests -- update_branch_tasks
# =============================================================================


class TestUpdateBranchTasks:
    """Tests for update_branch_tasks()."""

    def test_update_current_branch_tasks(self, seeded_branch):
        """Updating tasks without branch_id targets the current branch."""
        result = update_branch_tasks({"inProgress": ["Fix auth"], "completed": ["Read logs"]})

        assert result["tasks"]["inProgress"] == ["Fix auth"]
        assert result["tasks"]["completed"] == ["Read logs"]
        assert "lastUpdated" in result

    def test_update_specific_branch_tasks(self, seeded_branch):
        """Updating tasks with explicit branch_id targets that branch."""
        result = update_branch_tasks({"blocked": ["Waiting on API key"]}, branch_id="main")

        assert result["tasks"]["blocked"] == ["Waiting on API key"]

    def test_update_tasks_merges_keys(self, seeded_branch):
        """Multiple task updates merge keys."""
        update_branch_tasks({"inProgress": ["Task A"]})
        result = update_branch_tasks({"completed": ["Task B"]})

        assert result["tasks"]["inProgress"] == ["Task A"]
        assert result["tasks"]["completed"] == ["Task B"]

    def test_update_tasks_nonexistent_branch_raises(self, isolated_workdir):
        """Updating tasks for a non-existent branch raises ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            update_branch_tasks({"inProgress": ["x"]}, branch_id="nope")

    def test_update_tasks_sets_last_updated(self, seeded_branch):
        """Updating tasks sets the lastUpdated timestamp."""
        result = update_branch_tasks({"inProgress": ["task"]})
        assert "lastUpdated" in result


# =============================================================================
# Tests -- nested branches
# =============================================================================


class TestNestedBranches:
    """Tests for branching from branches (DAG depth > 1)."""

    def test_create_branch_from_branch(self, seeded_branch):
        """Creating a branch while on a non-main branch sets the correct parent."""
        # We're on feature-x; branch from it
        child = create_branch("feature-x-sub", reason="Sub-investigation")

        assert child["parent"] == "feature-x"

        current_id, _ = get_current_branch()
        assert current_id == "feature-x-sub"

    def test_nested_merge_returns_to_parent(self, seeded_branch):
        """Merging a nested branch switches back to its parent, not main."""
        create_branch("feature-x-sub", reason="Sub")
        merge_branch("feature-x-sub", outcome="Sub done")

        current_id, _ = get_current_branch()
        assert current_id == "feature-x"

    def test_nested_merge_chain(self, seeded_branch):
        """Merge child to parent, then parent to main, in sequence."""
        create_branch("child", reason="Child investigation")

        # Merge child back to feature-x
        merge_branch("child", outcome="Child findings")
        current_id, _ = get_current_branch()
        assert current_id == "feature-x"

        # Merge feature-x back to main
        merge_branch("feature-x", outcome="Feature complete")
        current_id, _ = get_current_branch()
        assert current_id == "main"

    def test_nested_context_inheritance(self, seeded_branch):
        """A child branch copies context from its parent (the non-main branch)."""
        update_branch_context({"focus": "parent focus"})

        child = create_branch("inheritor", reason="Should get parent context")
        assert child["context"].get("focus") == "parent focus"

    def test_deeply_nested_branches(self, isolated_workdir):
        """Three levels of nesting: main -> a -> b -> c."""
        create_branch("level-a", reason="A")
        create_branch("level-b", reason="B")
        create_branch("level-c", reason="C")

        # Verify the DAG chain
        branches = list_branches()
        b_map = {b["id"]: b for b in branches}

        assert b_map["level-c"]["parent"] is not None
        # Walk up the chain
        assert b_map["level-c"]["parent"] == "level-b"

        # list_branches doesn't include parent of non-main branches beyond id,
        # so verify via the raw data
        _, level_b = get_current_branch()  # still on level-c
        switch_branch("level-b")
        _, level_b_data = get_current_branch()
        assert level_b_data["parent"] == "level-a"


# =============================================================================
# Tests -- persistence and edge cases
# =============================================================================


class TestPersistenceAndEdgeCases:
    """Tests for file I/O, corrupt data, and boundary conditions."""

    def test_status_created_on_first_write(self, isolated_workdir):
        """STATUS.json is created on the first mutating operation."""
        assert not (isolated_workdir / "STATUS.json").exists()

        # Read-only calls don't persist; a write operation does
        create_branch("init-test", reason="Trigger first write")

        assert (isolated_workdir / "STATUS.json").exists()

    def test_corrupt_json_recovers(self, isolated_workdir):
        """If STATUS.json contains invalid JSON, the module recovers gracefully."""
        status_path = isolated_workdir / "STATUS.json"
        status_path.write_text("{{{bad json")

        # Should not raise; initializes fresh state
        branch_id, branch_data = get_current_branch()
        assert branch_id == "main"

    def test_empty_file_recovers(self, isolated_workdir):
        """An empty STATUS.json is treated as a fresh state."""
        status_path = isolated_workdir / "STATUS.json"
        status_path.write_text("")

        branch_id, _ = get_current_branch()
        assert branch_id == "main"

    def test_state_persists_across_calls(self, isolated_workdir):
        """Data written by one function is visible to the next."""
        create_branch("persist-test", reason="Check persistence")

        # Read state fresh (simulates a new process)
        branches = list_branches()
        ids = {b["id"] for b in branches}
        assert "persist-test" in ids

    def test_concurrent_branch_create_switch_sequence(self, isolated_workdir):
        """Sequential create-switch-create produces correct state."""
        create_branch("br-1", reason="First")
        switch_branch("main")
        create_branch("br-2", reason="Second")
        switch_branch("main")
        create_branch("br-3", reason="Third")

        branches = list_branches()
        ids = {b["id"] for b in branches}
        assert ids == {"main", "br-1", "br-2", "br-3"}

        # All three should have main as parent (created from main)
        for b in branches:
            if b["id"] != "main":
                assert b["parent"] == "main"

    def test_status_json_in_claude_dir_preferred(self, workdir_with_claude):
        """When .claude/ exists, STATUS.json goes there, not project root."""
        create_branch("loc-test", reason="Location check")

        assert (workdir_with_claude / ".claude" / "STATUS.json").exists()
        assert not (workdir_with_claude / "STATUS.json").exists()

    def test_branch_created_timestamp_is_iso_utc(self, isolated_workdir):
        """Branch 'created' field is a valid ISO 8601 UTC timestamp."""
        from datetime import datetime

        result = create_branch("ts-test", reason="Timestamp check")

        # Should parse without error
        dt = datetime.fromisoformat(result["created"])
        assert dt.tzinfo is not None  # timezone-aware

    def test_many_branches_and_cleanup(self, isolated_workdir):
        """Creating, merging, and deleting many branches leaves only main."""
        for i in range(10):
            create_branch(f"batch-{i}", reason=f"Batch {i}")
            merge_branch(f"batch-{i}", outcome=f"Done {i}", delete_after_merge=True)

        branches = list_branches()
        assert len(branches) == 1
        assert branches[0]["id"] == "main"
