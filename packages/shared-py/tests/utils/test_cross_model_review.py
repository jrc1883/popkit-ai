#!/usr/bin/env python3
"""Tests for cross_model_review utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from popkit_shared.utils import cross_model_review as cmr


class DummyAdapter:
    """Minimal provider adapter stub for availability checks."""

    def __init__(self, is_available: bool = True):
        self._is_available = is_available

    def detect(self):
        class Info:
            def __init__(self, is_available: bool):
                self.is_available = is_available

        return Info(self._is_available)


def stub_run_command(
    responses: dict[tuple[str, ...], tuple[int, str, str]], calls: list[tuple[str, ...]]
):
    """Build a run_command stub with exact tuple matching."""

    def _runner(cmd, cwd=None, timeout=30, shell=False, strip_output=True):
        key = tuple(cmd) if isinstance(cmd, list) else tuple(str(cmd).split())
        calls.append(key)
        if key not in responses:
            raise AssertionError(f"Unexpected command: {key}")
        return responses[key]

    return _runner


def test_detect_current_provider_prefers_codex_env(monkeypatch):
    """Codex Desktop markers should resolve to codex."""
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    monkeypatch.delenv("POPKIT_PROVIDER", raising=False)
    monkeypatch.setenv("CODEX_SHELL", "1")

    assert cmr.detect_current_provider() == "codex"


def test_resolve_target_provider_auto_and_override():
    """Auto should pick the opposite provider and explicit override should win."""
    assert cmr.resolve_target_provider("claude-code", "auto") == "codex"
    assert cmr.resolve_target_provider("codex", "auto") == "claude-code"
    assert cmr.resolve_target_provider("codex", "codex") == "codex"


def test_build_review_command_for_codex_branch(tmp_path):
    """Codex review command should use base ref and prompt."""
    request = cmr.ReviewRequest(scope=cmr.ReviewScope.BRANCH, base_ref="main", repo_root=tmp_path)

    command = cmr.build_review_command(request, "codex", tmp_path)

    assert command[:4] == ["codex", "review", "--base", "main"]
    assert "JSON_RESULT:" in command[-1]


def test_build_review_command_for_claude_commit(tmp_path):
    """Claude review command should force structured JSON output."""
    request = cmr.ReviewRequest(
        scope=cmr.ReviewScope.COMMIT,
        commit_sha="abc123",
        repo_root=tmp_path,
    )

    command = cmr.build_review_command(request, "claude-code", tmp_path)

    assert command[0:2] == ["claude", "-p"]
    assert "--json-schema" in command
    assert "--allowedTools" in command
    assert "--strict-mcp-config" in command


def test_parse_review_output_from_codex_json_suffix():
    """Codex transcripts should parse the trailing JSON_RESULT block."""
    raw_output = (
        "Review summary\n\n"
        'JSON_RESULT: {"verdict":"concerns","summary":"Missing test coverage.",'
        '"findings":[{"severity":"high","title":"Missing tests","body":"Add a regression test.",'
        '"file":"src/app.py","line":42}]}'
    )

    verdict, summary, findings = cmr.parse_review_output(raw_output, "codex")

    assert verdict == cmr.ReviewVerdict.CONCERNS
    assert summary == "Missing test coverage."
    assert findings[0].file == "src/app.py"
    assert findings[0].line == 42


def test_save_and_load_review_artifact(tmp_path, monkeypatch):
    """Artifacts should persist outside the repo and load by head SHA."""
    monkeypatch.setenv("POPKIT_HOME", str(tmp_path / "popkit-home"))

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    result = cmr.CrossModelReviewResult(
        requested_by_provider="claude-code",
        reviewer_provider="codex",
        scope="branch",
        base_ref="main",
        head_ref="feat/outside-voice",
        pr_number=None,
        verdict="approve",
        summary="Looks good.",
        findings=[],
        head_sha="abc123def456",
    )

    cmr.save_review_artifact(repo_root, "codex", "abc123def456", "raw output", result)
    lookup = cmr.load_review_status(repo_root, head_sha="abc123def456")

    assert lookup.has_review is True
    assert lookup.reviews[0].summary == "Looks good."
    assert Path(lookup.reviews[0].raw_output_path).exists()


def test_publish_review_comment_updates_existing(tmp_path, monkeypatch):
    """Publishing should patch an existing advisory comment for the same head."""
    calls: list[tuple[str, ...]] = []

    def _runner(cmd, cwd=None, timeout=30, shell=False, strip_output=True):
        key = tuple(cmd)
        calls.append(key)
        if key == ("gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"):
            return 0, "jrc1883/popkit-claude\n", ""
        if key == (
            "gh",
            "api",
            "repos/jrc1883/popkit-claude/issues/361/comments",
            "--paginate",
            "--slurp",
        ):
            return (
                0,
                json.dumps(
                    [
                        {
                            "id": 17,
                            "body": "<!-- popkit-outside-voice head_sha=abc123 -->\nold",
                        }
                    ]
                ),
                "",
            )
        if key[:6] == (
            "gh",
            "api",
            "repos/jrc1883/popkit-claude/issues/comments/17",
            "--method",
            "PATCH",
            "--raw-field",
        ):
            return 0, json.dumps({"id": 17}), ""
        raise AssertionError(f"Unexpected command: {key}")

    monkeypatch.setattr(cmr, "run_command", _runner)

    result = cmr.CrossModelReviewResult(
        requested_by_provider="claude-code",
        reviewer_provider="codex",
        scope="branch",
        base_ref="main",
        head_ref="feat/outside-voice",
        pr_number=361,
        verdict="approve",
        summary="Looks good.",
        findings=[],
        head_sha="abc123",
    )

    updated = cmr.publish_review_comment(result, tmp_path)

    assert updated.published_comment_id == 17
    assert any("/issues/comments/17" in " ".join(call) for call in calls)


def test_run_cross_model_review_branch_persists_result(tmp_path, monkeypatch):
    """Branch review should persist artifacts and record lifecycle events."""
    monkeypatch.setenv("POPKIT_HOME", str(tmp_path / "popkit-home"))
    monkeypatch.setattr(cmr, "get_adapter", lambda provider: DummyAdapter(True))

    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        cmr,
        "record_cross_model_review",
        lambda status, payload=None: events.append((status, payload or {})),
    )

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    calls: list[tuple[str, ...]] = []
    responses = {
        ("codex", "login", "status"): (0, "Logged in using ChatGPT\n", ""),
        ("git", "rev-parse", "HEAD"): (0, "abc123def456\n", ""),
        ("git", "branch", "--show-current"): (0, "feat/outside-voice\n", ""),
        (
            "codex",
            "review",
            "--base",
            "main",
            cmr.build_review_prompt(
                cmr.ReviewRequest(scope=cmr.ReviewScope.BRANCH, base_ref="main"),
                "codex",
            ),
        ): (
            0,
            'Review done\nJSON_RESULT: {"verdict":"approve","summary":"Looks good.","findings":[]}\n',
            "",
        ),
    }
    monkeypatch.setattr(cmr, "run_command", stub_run_command(responses, calls))

    result = cmr.run_cross_model_review(
        cmr.ReviewRequest(
            scope=cmr.ReviewScope.BRANCH,
            repo_root=repo_root,
            base_ref="main",
            requested_by_provider="claude-code",
        )
    )

    assert result.reviewer_provider == "codex"
    assert result.verdict == "approve"
    assert Path(result.artifact_path).exists()
    assert [event[0] for event in events] == ["requested", "completed"]


def test_run_cross_model_review_uncommitted_uses_uncommitted_flag(tmp_path, monkeypatch):
    """Uncommitted review scope should map to codex --uncommitted."""
    monkeypatch.setenv("POPKIT_HOME", str(tmp_path / "popkit-home"))
    monkeypatch.setattr(cmr, "get_adapter", lambda provider: DummyAdapter(True))
    monkeypatch.setattr(cmr, "record_cross_model_review", lambda status, payload=None: None)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    calls: list[tuple[str, ...]] = []
    prompt = cmr.build_review_prompt(
        cmr.ReviewRequest(scope=cmr.ReviewScope.UNCOMMITTED),
        "codex",
    )
    responses = {
        ("codex", "login", "status"): (0, "Logged in using ChatGPT\n", ""),
        ("git", "rev-parse", "HEAD"): (0, "abc123def456\n", ""),
        ("git", "branch", "--show-current"): (0, "feat/outside-voice\n", ""),
        ("codex", "review", "--uncommitted", prompt): (
            0,
            'JSON_RESULT: {"verdict":"approve","summary":"Looks good.","findings":[]}\n',
            "",
        ),
    }
    monkeypatch.setattr(cmr, "run_command", stub_run_command(responses, calls))

    result = cmr.run_cross_model_review(
        cmr.ReviewRequest(
            scope=cmr.ReviewScope.UNCOMMITTED,
            repo_root=repo_root,
            requested_by_provider="claude-code",
        )
    )

    assert result.scope == "uncommitted"
    assert ("codex", "review", "--uncommitted", prompt) in calls


def test_resolve_review_request_for_pr_uses_gh_metadata(tmp_path, monkeypatch):
    """PR review should resolve base/head refs through gh."""
    calls: list[tuple[str, ...]] = []
    responses = {
        ("gh", "pr", "view", "361", "--json", "baseRefName,headRefName,headRefOid"): (
            0,
            json.dumps(
                {
                    "baseRefName": "main",
                    "headRefName": "feat/outside-voice",
                    "headRefOid": "abc123def456",
                }
            ),
            "",
        ),
        ("git", "rev-parse", "HEAD"): (0, "abc123def456\n", ""),
        ("git", "branch", "--show-current"): (0, "feat/outside-voice\n", ""),
    }
    monkeypatch.setattr(cmr, "run_command", stub_run_command(responses, calls))

    resolved = cmr.resolve_review_request(
        cmr.ReviewRequest(scope=cmr.ReviewScope.PR, repo_root=tmp_path, pr_number=361)
    )

    assert resolved.base_ref == "main"
    assert resolved.head_ref == "feat/outside-voice"


def test_validate_provider_auth_raises_for_missing_codex_login(tmp_path, monkeypatch):
    """Missing auth should produce a clear error."""
    monkeypatch.setattr(
        cmr,
        "run_command",
        lambda cmd, cwd=None, timeout=30, shell=False, strip_output=True: (
            1,
            "",
            "Not logged in",
        ),
    )

    with pytest.raises(cmr.CrossModelReviewError, match="codex login"):
        cmr.validate_provider_auth("codex", tmp_path)


def test_mark_pr_ready_requires_review_by_default(tmp_path, monkeypatch):
    """PR ready should fail when no outside-voice review exists and no override is set."""
    monkeypatch.setattr(cmr, "_resolve_pr_number", lambda repo_root, pr_number: 361)
    monkeypatch.setattr(
        cmr,
        "load_review_status",
        lambda repo_root, head_sha=None: cmr.ReviewLookup(str(repo_root), "abc123", []),
    )
    monkeypatch.setattr(cmr, "current_head_sha", lambda repo_root: "abc123")
    monkeypatch.setattr(cmr, "current_branch_name", lambda repo_root: "feat/outside-voice")

    with pytest.raises(cmr.CrossModelReviewError, match="No outside-voice review found"):
        cmr.mark_pr_ready(tmp_path, pr_number=361)


def test_mark_pr_ready_uses_existing_review(tmp_path, monkeypatch):
    """Existing review artifact should allow gh pr ready directly."""
    review = cmr.CrossModelReviewResult(
        requested_by_provider="claude-code",
        reviewer_provider="codex",
        scope="pr",
        base_ref="main",
        head_ref="feat/outside-voice",
        pr_number=361,
        verdict="approve",
        summary="Looks good.",
        findings=[],
        head_sha="abc123",
        artifact_path=str(tmp_path / "artifact.json"),
    )
    monkeypatch.setattr(cmr, "_resolve_pr_number", lambda repo_root, pr_number: 361)
    monkeypatch.setattr(
        cmr,
        "load_review_status",
        lambda repo_root, head_sha=None: cmr.ReviewLookup(str(repo_root), "abc123", [review]),
    )
    monkeypatch.setattr(cmr, "current_head_sha", lambda repo_root: "abc123")
    monkeypatch.setattr(cmr, "current_branch_name", lambda repo_root: "feat/outside-voice")

    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        cmr,
        "run_command",
        stub_run_command({("gh", "pr", "ready", "361"): (0, "", "")}, calls),
    )

    result = cmr.mark_pr_ready(tmp_path, pr_number=361)

    assert result["status"] == "ready"
    assert result["action"] == "used-existing-review"
    assert ("gh", "pr", "ready", "361") in calls


def test_mark_pr_ready_runs_review_if_missing(tmp_path, monkeypatch):
    """PR ready should be able to run outside-voice review before continuing."""
    review = cmr.CrossModelReviewResult(
        requested_by_provider="claude-code",
        reviewer_provider="codex",
        scope="pr",
        base_ref="main",
        head_ref="feat/outside-voice",
        pr_number=361,
        verdict="approve",
        summary="Looks good.",
        findings=[],
        head_sha="abc123",
        artifact_path=str(tmp_path / "artifact.json"),
    )
    monkeypatch.setattr(cmr, "_resolve_pr_number", lambda repo_root, pr_number: 361)
    monkeypatch.setattr(
        cmr,
        "load_review_status",
        lambda repo_root, head_sha=None: cmr.ReviewLookup(str(repo_root), "abc123", []),
    )
    monkeypatch.setattr(cmr, "current_head_sha", lambda repo_root: "abc123")
    monkeypatch.setattr(cmr, "current_branch_name", lambda repo_root: "feat/outside-voice")
    monkeypatch.setattr(cmr, "run_cross_model_review", lambda request: review)

    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        cmr,
        "run_command",
        stub_run_command({("gh", "pr", "ready", "361"): (0, "", "")}, calls),
    )

    result = cmr.mark_pr_ready(tmp_path, pr_number=361, run_review_if_missing=True)

    assert result["action"] == "ran-review"
    assert result["outside_voice_review_present"] is True
    assert ("gh", "pr", "ready", "361") in calls


def test_mark_pr_ready_records_skip_if_requested(tmp_path, monkeypatch):
    """Explicit skip should be recorded before marking ready."""
    monkeypatch.setattr(cmr, "_resolve_pr_number", lambda repo_root, pr_number: 361)
    monkeypatch.setattr(
        cmr,
        "load_review_status",
        lambda repo_root, head_sha=None: cmr.ReviewLookup(str(repo_root), "abc123", []),
    )
    monkeypatch.setattr(cmr, "current_head_sha", lambda repo_root: "abc123")
    monkeypatch.setattr(cmr, "current_branch_name", lambda repo_root: "feat/outside-voice")

    skip_calls: list[Path] = []
    monkeypatch.setattr(
        cmr,
        "record_review_skip",
        lambda repo_root, requested_by_provider=None: (
            skip_calls.append(Path(repo_root)) or {"head_sha": "abc123"}
        ),
    )

    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        cmr,
        "run_command",
        stub_run_command({("gh", "pr", "ready", "361"): (0, "", "")}, calls),
    )

    result = cmr.mark_pr_ready(tmp_path, pr_number=361, skip_if_missing=True)

    assert result["action"] == "recorded-skip"
    assert skip_calls == [tmp_path]
    assert ("gh", "pr", "ready", "361") in calls
