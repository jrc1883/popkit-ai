#!/usr/bin/env python3
"""Cross-model advisory code review utilities.

Runs an advisory review through the opposite model family when possible,
normalizes the output into a shared artifact contract, persists the result
outside the repo, and optionally publishes it back to GitHub.
"""

from __future__ import annotations

import hashlib
import json
import os
import textwrap
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from popkit_shared.providers import get_adapter

from .plugin_data import get_global_plugin_data_dir
from .session_recorder import record_cross_model_review
from .subprocess_utils import run_command


class CrossModelReviewError(RuntimeError):
    """Raised when outside-voice review cannot proceed."""


class ReviewScope(str, Enum):
    """Review scopes supported by the outside-voice runner."""

    BRANCH = "branch"
    UNCOMMITTED = "uncommitted"
    PR = "pr"
    COMMIT = "commit"


class ReviewVerdict(str, Enum):
    """Normalized review verdict."""

    APPROVE = "approve"
    CONCERNS = "concerns"
    FAIL = "fail"


class PublishMode(str, Enum):
    """How advisory results should be published."""

    NONE = "none"
    COMMENT = "comment"


class ReviewStatus(str, Enum):
    """Lifecycle states recorded for outside-voice review."""

    REQUESTED = "requested"
    COMPLETED = "completed"
    SKIPPED = "skipped"


SUPPORTED_PROVIDERS = {"claude-code", "codex"}
ALTERNATE_PROVIDERS = {"claude-code": "codex", "codex": "claude-code"}
COMMENT_MARKER = "popkit-outside-voice"


@dataclass
class ReviewFinding:
    """Single normalized review finding."""

    severity: str
    title: str
    body: str
    file: str | None = None
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-safe dict."""
        return {
            "severity": self.severity,
            "title": self.title,
            "body": self.body,
            "file": self.file,
            "line": self.line,
        }


@dataclass
class ReviewRequest:
    """Requested outside-voice review parameters."""

    scope: ReviewScope = ReviewScope.BRANCH
    repo_root: Path | None = None
    base_ref: str | None = None
    head_ref: str | None = None
    pr_number: int | None = None
    commit_sha: str | None = None
    requested_by_provider: str | None = None
    target_provider: str = "auto"
    publish: PublishMode = PublishMode.NONE


@dataclass
class CrossModelReviewResult:
    """Normalized outside-voice review artifact."""

    requested_by_provider: str
    reviewer_provider: str
    scope: str
    base_ref: str | None
    head_ref: str
    pr_number: int | None
    verdict: str
    summary: str
    findings: list[ReviewFinding] = field(default_factory=list)
    raw_output_path: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    head_sha: str | None = None
    artifact_path: str | None = None
    published_comment_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-safe dict."""
        return {
            "requested_by_provider": self.requested_by_provider,
            "reviewer_provider": self.reviewer_provider,
            "scope": self.scope,
            "base_ref": self.base_ref,
            "head_ref": self.head_ref,
            "pr_number": self.pr_number,
            "verdict": self.verdict,
            "summary": self.summary,
            "findings": [finding.to_dict() for finding in self.findings],
            "raw_output_path": self.raw_output_path,
            "generated_at": self.generated_at,
            "head_sha": self.head_sha,
            "artifact_path": self.artifact_path,
            "published_comment_id": self.published_comment_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CrossModelReviewResult:
        """Deserialize from stored artifact."""
        findings = [ReviewFinding(**item) for item in data.get("findings", [])]
        return cls(
            requested_by_provider=data["requested_by_provider"],
            reviewer_provider=data["reviewer_provider"],
            scope=data["scope"],
            base_ref=data.get("base_ref"),
            head_ref=data["head_ref"],
            pr_number=data.get("pr_number"),
            verdict=data["verdict"],
            summary=data["summary"],
            findings=findings,
            raw_output_path=data.get("raw_output_path", ""),
            generated_at=data.get("generated_at", datetime.now(UTC).isoformat()),
            head_sha=data.get("head_sha"),
            artifact_path=data.get("artifact_path"),
            published_comment_id=data.get("published_comment_id"),
        )


@dataclass
class ReviewLookup:
    """Current outside-voice review status for a specific head SHA."""

    repo_root: str
    head_sha: str
    reviews: list[CrossModelReviewResult] = field(default_factory=list)

    @property
    def has_review(self) -> bool:
        """Whether at least one advisory review exists for this head."""
        return bool(self.reviews)

    def to_dict(self) -> dict[str, Any]:
        """Serialize review status for JSON output."""
        return {
            "repo_root": self.repo_root,
            "head_sha": self.head_sha,
            "has_review": self.has_review,
            "reviews": [review.to_dict() for review in self.reviews],
        }


def detect_current_provider() -> str:
    """Detect the current provider from environment.

    Claude-specific environment comes first, followed by explicit PopKit
    override, then Codex Desktop markers, and finally a Claude fallback for
    backward compatibility.
    """
    if os.environ.get("CLAUDE_PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_ROOT"):
        return "claude-code"

    popkit_provider = os.environ.get("POPKIT_PROVIDER")
    if popkit_provider:
        return popkit_provider

    if (
        os.environ.get("CODEX_SHELL")
        or os.environ.get("CODEX_THREAD_ID")
        or os.environ.get("CODEX_INTERNAL_ORIGINATOR_OVERRIDE")
    ):
        return "codex"

    return "claude-code"


def resolve_target_provider(
    current_provider: str | None = None, target_provider: str = "auto"
) -> str:
    """Resolve the provider that should perform the outside-voice review."""
    current = current_provider or detect_current_provider()

    if target_provider != "auto":
        if target_provider not in SUPPORTED_PROVIDERS:
            raise CrossModelReviewError(
                f"Unsupported outside-voice provider '{target_provider}'. "
                f"Supported providers: {', '.join(sorted(SUPPORTED_PROVIDERS))}."
            )
        return target_provider

    if current not in ALTERNATE_PROVIDERS:
        raise CrossModelReviewError(
            f"Current provider '{current}' does not have an alternate outside-voice provider."
        )

    return ALTERNATE_PROVIDERS[current]


def normalize_verdict(value: str | None) -> ReviewVerdict:
    """Normalize a verdict string into the shared enum."""
    if not value:
        return ReviewVerdict.CONCERNS

    lowered = value.strip().lower()
    if lowered in {ReviewVerdict.APPROVE.value, "approved", "pass", "passes"}:
        return ReviewVerdict.APPROVE
    if lowered in {ReviewVerdict.FAIL.value, "block", "blocked", "reject"}:
        return ReviewVerdict.FAIL
    if lowered in {ReviewVerdict.CONCERNS.value, "warning", "warnings"}:
        return ReviewVerdict.CONCERNS

    if any(token in lowered for token in ("critical", "blocking", "must fix", "unsafe")):
        return ReviewVerdict.FAIL
    if any(token in lowered for token in ("no issues", "looks good", "ship it", "approve")):
        return ReviewVerdict.APPROVE
    return ReviewVerdict.CONCERNS


def _repo_slug(repo_root: Path) -> str:
    """Generate a stable review-artifact directory name for a repo."""
    digest = hashlib.sha256(str(repo_root).encode("utf-8")).hexdigest()[:10]
    return f"{repo_root.name}-{digest}"


def _reviews_dir(repo_root: Path) -> Path:
    """Get the review artifact directory for a repo."""
    path = get_global_plugin_data_dir() / "cross-model-reviews" / _repo_slug(repo_root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _artifact_path(repo_root: Path, head_sha: str, reviewer_provider: str) -> Path:
    """Get the persisted JSON artifact path."""
    return _reviews_dir(repo_root) / f"{head_sha}-{reviewer_provider}.json"


def _raw_output_path(repo_root: Path, head_sha: str, reviewer_provider: str) -> Path:
    """Get the raw CLI transcript path."""
    return _reviews_dir(repo_root) / f"{head_sha}-{reviewer_provider}.raw.txt"


def _run_checked(cmd: list[str], cwd: Path | None = None, timeout: int = 60) -> tuple[str, str]:
    """Run a command and raise a review-specific error on failure."""
    exit_code, stdout, stderr = run_command(cmd, cwd=cwd, timeout=timeout, strip_output=False)
    if exit_code != 0:
        message = stderr.strip() or stdout.strip() or f"Exit code {exit_code}"
        raise CrossModelReviewError(message)
    return stdout, stderr


def resolve_repo_root(repo_root: str | Path | None = None) -> Path:
    """Resolve the git repository root for the current workspace."""
    if repo_root is not None:
        return Path(repo_root).resolve()

    stdout, _ = _run_checked(["git", "rev-parse", "--show-toplevel"])
    return Path(stdout.strip()).resolve()


def current_head_sha(repo_root: Path) -> str:
    """Get the HEAD commit SHA."""
    stdout, _ = _run_checked(["git", "rev-parse", "HEAD"], cwd=repo_root)
    return stdout.strip()


def current_branch_name(repo_root: Path) -> str:
    """Get the current branch name or HEAD if detached."""
    stdout, _ = _run_checked(["git", "branch", "--show-current"], cwd=repo_root)
    branch = stdout.strip()
    return branch or "HEAD"


def default_base_ref(repo_root: Path) -> str:
    """Infer the default base branch for branch reviews."""
    exit_code, stdout, _ = run_command(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        cwd=repo_root,
        timeout=30,
        strip_output=True,
    )
    if exit_code == 0 and stdout:
        return stdout.rsplit("/", 1)[-1]

    for candidate in ("main", "master"):
        exit_code, _, _ = run_command(
            ["git", "rev-parse", "--verify", candidate],
            cwd=repo_root,
            timeout=30,
            strip_output=True,
        )
        if exit_code == 0:
            return candidate

    return "main"


def validate_provider_available(provider_name: str) -> None:
    """Ensure the target provider adapter exists and is available."""
    adapter = get_adapter(provider_name)
    if adapter is None:
        raise CrossModelReviewError(
            f"Provider '{provider_name}' is not registered in the PopKit provider registry."
        )

    info = adapter.detect()
    if not info.is_available:
        raise CrossModelReviewError(f"Provider '{provider_name}' is not available on this machine.")


def validate_provider_auth(provider_name: str, repo_root: Path | None = None) -> None:
    """Ensure the target provider is authenticated locally."""
    cwd = repo_root or Path.cwd()

    if provider_name == "codex":
        try:
            stdout, _ = _run_checked(["codex", "login", "status"], cwd=cwd, timeout=30)
        except CrossModelReviewError as exc:
            raise CrossModelReviewError(
                "Codex CLI is installed but not authenticated. Run `codex login` first."
            ) from exc
        if "logged in" not in stdout.lower():
            raise CrossModelReviewError(
                "Codex CLI is installed but not authenticated. Run `codex login` first."
            )
        return

    if provider_name == "claude-code":
        try:
            stdout, _ = _run_checked(["claude", "auth", "status"], cwd=cwd, timeout=30)
        except CrossModelReviewError as exc:
            raise CrossModelReviewError(
                "Claude Code is installed but not authenticated. Run `claude auth login` first."
            ) from exc
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise CrossModelReviewError("Claude Code auth status returned malformed JSON.") from exc
        if not parsed.get("loggedIn"):
            raise CrossModelReviewError(
                "Claude Code is installed but not authenticated. Run `claude auth login` first."
            )
        return

    raise CrossModelReviewError(f"Unsupported provider '{provider_name}'.")


def resolve_pr_context(repo_root: Path, pr_number: int) -> tuple[str, str, str]:
    """Resolve base ref, head ref, and head SHA for a PR."""
    stdout, _ = _run_checked(
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--json",
            "baseRefName,headRefName,headRefOid",
        ],
        cwd=repo_root,
        timeout=30,
    )
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise CrossModelReviewError(f"Could not parse metadata for PR #{pr_number}.") from exc

    base_ref = payload.get("baseRefName")
    head_ref = payload.get("headRefName")
    head_sha = payload.get("headRefOid")
    if not base_ref or not head_ref or not head_sha:
        raise CrossModelReviewError(f"PR #{pr_number} is missing reviewable metadata.")

    current_sha = current_head_sha(repo_root)
    current_branch = current_branch_name(repo_root)
    if head_sha != current_sha and head_ref != current_branch:
        raise CrossModelReviewError(
            f"PR #{pr_number} is not checked out locally. Expected head '{head_ref}' ({head_sha[:12]})."
        )

    return str(base_ref), str(head_ref), str(head_sha)


def resolve_review_request(request: ReviewRequest) -> ReviewRequest:
    """Fill in missing request fields from repo state."""
    repo_root = resolve_repo_root(request.repo_root)
    head_ref = request.head_ref or current_branch_name(repo_root)
    base_ref = request.base_ref

    if request.scope == ReviewScope.BRANCH and not base_ref:
        base_ref = default_base_ref(repo_root)
    if request.scope == ReviewScope.PR and request.pr_number is None:
        raise CrossModelReviewError("PR review requires `pr_number`.")
    if request.scope == ReviewScope.PR and request.pr_number is not None:
        base_ref, head_ref, _ = resolve_pr_context(repo_root, request.pr_number)
    if request.scope == ReviewScope.COMMIT and not request.commit_sha:
        raise CrossModelReviewError("Commit review requires `commit_sha`.")

    requested_by_provider = request.requested_by_provider or detect_current_provider()
    publish = request.publish
    if isinstance(publish, str):
        publish = PublishMode(publish)

    return ReviewRequest(
        scope=request.scope,
        repo_root=repo_root,
        base_ref=base_ref,
        head_ref=head_ref,
        pr_number=request.pr_number,
        commit_sha=request.commit_sha,
        requested_by_provider=requested_by_provider,
        target_provider=request.target_provider,
        publish=publish,
    )


def _review_schema_json() -> str:
    """Structured-output schema used for Claude reviews."""
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "verdict": {
                "type": "string",
                "enum": [verdict.value for verdict in ReviewVerdict],
            },
            "summary": {"type": "string"},
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "severity": {"type": "string"},
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "file": {"type": ["string", "null"]},
                        "line": {"type": ["integer", "null"]},
                    },
                    "required": ["severity", "title", "body", "file", "line"],
                },
            },
        },
        "required": ["verdict", "summary", "findings"],
    }
    return json.dumps(schema, separators=(",", ":"))


def build_review_prompt(request: ReviewRequest, target_provider: str) -> str:
    """Build a single review prompt for either provider."""
    scope_text = {
        ReviewScope.BRANCH: f"the current branch diff against `{request.base_ref}`",
        ReviewScope.UNCOMMITTED: "all uncommitted changes in the current workspace",
        ReviewScope.PR: f"the changes for PR #{request.pr_number}",
        ReviewScope.COMMIT: f"the changes introduced by commit `{request.commit_sha}`",
    }[request.scope]

    provider_note = (
        "Return valid JSON matching the requested schema."
        if target_provider == "claude-code"
        else "End your response with a final line exactly in the form "
        "`JSON_RESULT: { ... }` containing verdict, summary, and findings."
    )

    return textwrap.dedent(
        f"""
        Perform an advisory outside-voice code review for {scope_text}.

        Constraints:
        - Review only. Do not edit files, create commits, or run mutating commands.
        - Focus on bugs, regressions, risky assumptions, and missing tests.
        - Keep findings concrete and actionable.
        - Use `approve` only when there are no meaningful issues.
        - Use `fail` only for blocking or clearly unsafe problems.
        - Otherwise use `concerns`.
        - {provider_note}

        Findings format:
        - severity: `critical`, `high`, `medium`, or `low`
        - title: short label
        - body: one-paragraph explanation
        - file: repo-relative path when available, otherwise null
        - line: 1-based line number when available, otherwise null
        """
    ).strip()


def build_review_command(
    request: ReviewRequest, target_provider: str, repo_root: Path
) -> list[str]:
    """Build the provider-specific CLI command."""
    prompt = build_review_prompt(request, target_provider)

    if target_provider == "codex":
        cmd = ["codex", "review"]
        if request.scope == ReviewScope.UNCOMMITTED:
            cmd.append("--uncommitted")
        elif request.scope == ReviewScope.BRANCH:
            cmd.extend(["--base", request.base_ref or default_base_ref(repo_root)])
        elif request.scope == ReviewScope.PR:
            cmd.extend(["--base", request.base_ref or default_base_ref(repo_root)])
        elif request.scope == ReviewScope.COMMIT:
            cmd.extend(["--commit", request.commit_sha or "HEAD"])
        cmd.append(prompt)
        return cmd

    if target_provider == "claude-code":
        cmd = [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "json",
            "--json-schema",
            _review_schema_json(),
            "--tools",
            "Read,Grep,Glob,LS,Bash",
            "--allowedTools",
            "Read,Grep,Glob,LS,Bash(git:*)",
            "--permission-mode",
            "default",
            "--strict-mcp-config",
            "--mcp-config",
            "{}",
            "--append-system-prompt",
            (
                "You are performing a read-only code review. "
                "You may inspect the repository and run read-only git commands only."
            ),
        ]
        if request.scope == ReviewScope.UNCOMMITTED:
            cmd.extend(
                [
                    "--append-system-prompt",
                    "Review scope: all uncommitted tracked and untracked changes in the current repo.",
                ]
            )
        elif request.scope == ReviewScope.BRANCH:
            cmd.extend(
                [
                    "--append-system-prompt",
                    f"Review scope: current branch diff against {request.base_ref or default_base_ref(repo_root)}.",
                ]
            )
        elif request.scope == ReviewScope.PR:
            cmd.extend(
                [
                    "--append-system-prompt",
                    f"Review scope: current checkout as PR #{request.pr_number} against {request.base_ref or default_base_ref(repo_root)}.",
                ]
            )
        elif request.scope == ReviewScope.COMMIT:
            cmd.extend(
                [
                    "--append-system-prompt",
                    f"Review scope: commit {request.commit_sha}.",
                ]
            )
        return cmd

    raise CrossModelReviewError(f"Unsupported provider '{target_provider}'.")


def _extract_json_suffix(raw_output: str) -> dict[str, Any] | None:
    """Extract the JSON_RESULT payload from a Codex review transcript."""
    marker = "JSON_RESULT:"
    if marker not in raw_output:
        return None

    payload = raw_output.split(marker)[-1].strip()
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def _find_json_object(raw_output: str) -> dict[str, Any] | None:
    """Best-effort JSON object extraction from arbitrary output."""
    stripped = raw_output.strip()
    if not stripped:
        return None

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict):
        return parsed

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        parsed = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _normalize_findings(raw_findings: list[dict[str, Any]] | None) -> list[ReviewFinding]:
    """Normalize provider findings into the shared contract."""
    findings: list[ReviewFinding] = []
    for item in raw_findings or []:
        if not isinstance(item, dict):
            continue
        findings.append(
            ReviewFinding(
                severity=str(item.get("severity") or "medium"),
                title=str(item.get("title") or "Review finding"),
                body=str(item.get("body") or "").strip() or "No details provided.",
                file=item.get("file"),
                line=item.get("line"),
            )
        )
    return findings


def parse_review_output(
    raw_output: str, provider_name: str
) -> tuple[ReviewVerdict, str, list[ReviewFinding]]:
    """Parse provider output into verdict, summary, and findings."""
    parsed: dict[str, Any] | None
    if provider_name == "codex":
        parsed = _extract_json_suffix(raw_output) or _find_json_object(raw_output)
    else:
        parsed = _find_json_object(raw_output)

    if parsed:
        verdict = normalize_verdict(str(parsed.get("verdict")))
        summary = str(parsed.get("summary") or "").strip()
        findings = _normalize_findings(parsed.get("findings"))
        if summary:
            return verdict, summary, findings

    verdict = normalize_verdict(raw_output)
    summary = (
        raw_output.strip().splitlines()[0] if raw_output.strip() else "No review output returned."
    )
    return verdict, summary, []


def save_review_artifact(
    repo_root: Path,
    reviewer_provider: str,
    head_sha: str,
    raw_output: str,
    result: CrossModelReviewResult,
) -> CrossModelReviewResult:
    """Persist raw output plus normalized artifact outside the repo."""
    raw_path = _raw_output_path(repo_root, head_sha, reviewer_provider)
    artifact_path = _artifact_path(repo_root, head_sha, reviewer_provider)

    raw_path.write_text(raw_output, encoding="utf-8")
    result.raw_output_path = str(raw_path)
    result.artifact_path = str(artifact_path)
    artifact_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return result


def load_review_status(repo_root: str | Path, head_sha: str | None = None) -> ReviewLookup:
    """Load persisted advisory reviews for the current or specified head SHA."""
    repo_path = resolve_repo_root(repo_root)
    sha = head_sha or current_head_sha(repo_path)
    reviews: list[CrossModelReviewResult] = []

    for artifact_file in sorted(_reviews_dir(repo_path).glob(f"{sha}-*.json")):
        try:
            payload = json.loads(artifact_file.read_text(encoding="utf-8"))
            reviews.append(CrossModelReviewResult.from_dict(payload))
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            continue

    return ReviewLookup(repo_root=str(repo_path), head_sha=sha, reviews=reviews)


def render_review_markdown(result: CrossModelReviewResult, include_marker: bool = True) -> str:
    """Render a normalized advisory review as Markdown."""
    lines = []
    if include_marker and result.head_sha:
        lines.append(f"<!-- {COMMENT_MARKER} head_sha={result.head_sha} -->")

    lines.extend(
        [
            "## Outside Voice Review",
            "",
            f"- Requested by: `{result.requested_by_provider}`",
            f"- Reviewer: `{result.reviewer_provider}`",
            f"- Scope: `{result.scope}`",
            f"- Verdict: `{result.verdict}`",
        ]
    )

    if result.base_ref:
        lines.append(f"- Base ref: `{result.base_ref}`")
    lines.append(f"- Head ref: `{result.head_ref}`")
    if result.pr_number is not None:
        lines.append(f"- PR: `#{result.pr_number}`")
    if result.head_sha:
        lines.append(f"- Head SHA: `{result.head_sha}`")

    lines.extend(["", f"**Summary:** {result.summary}", ""])

    if result.findings:
        lines.append("### Findings")
        lines.append("")
        for index, finding in enumerate(result.findings, start=1):
            location = ""
            if finding.file:
                location = f" ({finding.file}"
                if finding.line is not None:
                    location += f":{finding.line}"
                location += ")"
            lines.append(
                f"{index}. **[{finding.severity}] {finding.title}**{location}  \n{finding.body}"
            )
    else:
        lines.extend(["No actionable findings reported.", ""])

    lines.extend(
        [
            "",
            "_Advisory only. Human approval remains separate._",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _current_repo_name(repo_root: Path) -> str:
    """Resolve the current GitHub repo slug via gh."""
    stdout, _ = _run_checked(
        ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
        cwd=repo_root,
        timeout=30,
    )
    return stdout.strip()


def _resolve_pr_number(repo_root: Path, pr_number: int | None) -> int:
    """Resolve the target PR number for comment publishing."""
    if pr_number is not None:
        return pr_number

    stdout, _ = _run_checked(
        ["gh", "pr", "view", "--json", "number", "--jq", ".number"],
        cwd=repo_root,
        timeout=30,
    )
    try:
        return int(stdout.strip())
    except ValueError as exc:
        raise CrossModelReviewError("Could not determine current PR number.") from exc


def publish_review_comment(
    result: CrossModelReviewResult, repo_root: str | Path
) -> CrossModelReviewResult:
    """Create or update a PR comment for the advisory review."""
    repo_path = resolve_repo_root(repo_root)
    repo_name = _current_repo_name(repo_path)
    pr_number = _resolve_pr_number(repo_path, result.pr_number)
    marker = f"<!-- {COMMENT_MARKER} head_sha={result.head_sha} -->"
    body = render_review_markdown(result, include_marker=True)

    stdout, _ = _run_checked(
        [
            "gh",
            "api",
            f"repos/{repo_name}/issues/{pr_number}/comments",
            "--paginate",
            "--slurp",
        ],
        cwd=repo_path,
        timeout=30,
    )
    try:
        comments = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise CrossModelReviewError("Could not parse GitHub issue comments.") from exc

    existing_id: int | None = None
    if comments and isinstance(comments[0], list):
        comments = [item for page in comments for item in page]

    for comment in comments:
        if isinstance(comment, dict) and marker in str(comment.get("body", "")):
            existing_id = comment.get("id")
            break

    if existing_id is not None:
        _run_checked(
            [
                "gh",
                "api",
                f"repos/{repo_name}/issues/comments/{existing_id}",
                "--method",
                "PATCH",
                "--raw-field",
                f"body={body}",
            ],
            cwd=repo_path,
            timeout=30,
        )
        result.published_comment_id = existing_id
        result.pr_number = pr_number
        return result

    stdout, _ = _run_checked(
        [
            "gh",
            "api",
            f"repos/{repo_name}/issues/{pr_number}/comments",
            "--method",
            "POST",
            "--raw-field",
            f"body={body}",
        ],
        cwd=repo_path,
        timeout=30,
    )
    try:
        created = json.loads(stdout)
    except json.JSONDecodeError:
        created = {}

    result.published_comment_id = created.get("id")
    result.pr_number = pr_number
    return result


def _record_review_event(status: ReviewStatus, payload: dict[str, Any]) -> None:
    """Record an outside-voice review lifecycle event."""
    record_cross_model_review(status.value, payload)


def run_cross_model_review(request: ReviewRequest) -> CrossModelReviewResult:
    """Execute an advisory outside-voice review and persist the artifact."""
    resolved = resolve_review_request(request)
    assert resolved.repo_root is not None
    repo_root = resolved.repo_root
    requested_by = resolved.requested_by_provider or detect_current_provider()
    reviewer_provider = resolve_target_provider(requested_by, resolved.target_provider)
    validate_provider_available(reviewer_provider)
    validate_provider_auth(reviewer_provider, repo_root)

    head_sha = current_head_sha(repo_root)
    _record_review_event(
        ReviewStatus.REQUESTED,
        {
            "requested_by_provider": requested_by,
            "reviewer_provider": reviewer_provider,
            "scope": resolved.scope.value,
            "base_ref": resolved.base_ref,
            "head_ref": resolved.head_ref,
            "head_sha": head_sha,
            "pr_number": resolved.pr_number,
        },
    )

    command = build_review_command(resolved, reviewer_provider, repo_root)
    stdout, stderr = _run_checked(command, cwd=repo_root, timeout=180)
    raw_output = stdout if stdout.strip() else stderr
    verdict, summary, findings = parse_review_output(raw_output, reviewer_provider)

    result = CrossModelReviewResult(
        requested_by_provider=requested_by,
        reviewer_provider=reviewer_provider,
        scope=resolved.scope.value,
        base_ref=resolved.base_ref,
        head_ref=resolved.head_ref or current_branch_name(repo_root),
        pr_number=resolved.pr_number,
        verdict=verdict.value,
        summary=summary,
        findings=findings,
        head_sha=head_sha,
    )
    save_review_artifact(repo_root, reviewer_provider, head_sha, raw_output, result)

    if resolved.publish == PublishMode.COMMENT:
        publish_review_comment(result, repo_root)
        if result.artifact_path:
            Path(result.artifact_path).write_text(
                json.dumps(result.to_dict(), indent=2), encoding="utf-8"
            )

    _record_review_event(
        ReviewStatus.COMPLETED,
        {
            "requested_by_provider": result.requested_by_provider,
            "reviewer_provider": result.reviewer_provider,
            "scope": result.scope,
            "base_ref": result.base_ref,
            "head_ref": result.head_ref,
            "head_sha": result.head_sha,
            "pr_number": result.pr_number,
            "verdict": result.verdict,
            "artifact_path": result.artifact_path,
            "raw_output_path": result.raw_output_path,
        },
    )

    return result


def record_review_skip(
    repo_root: str | Path, requested_by_provider: str | None = None
) -> dict[str, Any]:
    """Record that the user explicitly skipped outside-voice review."""
    repo_path = resolve_repo_root(repo_root)
    payload = {
        "requested_by_provider": requested_by_provider or detect_current_provider(),
        "head_ref": current_branch_name(repo_path),
        "head_sha": current_head_sha(repo_path),
    }
    _record_review_event(ReviewStatus.SKIPPED, payload)
    return payload


def mark_pr_ready(
    repo_root: str | Path,
    pr_number: int | None = None,
    run_review_if_missing: bool = False,
    skip_if_missing: bool = False,
    target_provider: str = "auto",
    publish: PublishMode = PublishMode.COMMENT,
) -> dict[str, Any]:
    """Mark a draft PR ready after satisfying outside-voice review policy.

    By default, requires an existing outside-voice review artifact for the
    current head. Callers can choose to run the review automatically or record
    an explicit skip before continuing.
    """
    repo_path = resolve_repo_root(repo_root)
    head_sha = current_head_sha(repo_path)
    head_ref = current_branch_name(repo_path)
    resolved_pr_number = _resolve_pr_number(repo_path, pr_number)
    status = load_review_status(repo_path, head_sha=head_sha)

    result: CrossModelReviewResult | None = status.reviews[0] if status.reviews else None
    action = "used-existing-review"

    if not status.has_review:
        if run_review_if_missing:
            result = run_cross_model_review(
                ReviewRequest(
                    scope=ReviewScope.PR,
                    repo_root=repo_path,
                    pr_number=resolved_pr_number,
                    target_provider=target_provider,
                    publish=publish,
                )
            )
            action = "ran-review"
        elif skip_if_missing:
            record_review_skip(repo_path)
            action = "recorded-skip"
        else:
            raise CrossModelReviewError(
                "No outside-voice review found for the current head. "
                "Run advisory review first or call with "
                "`run_review_if_missing=True` or `skip_if_missing=True`."
            )

    _run_checked(
        ["gh", "pr", "ready", str(resolved_pr_number)],
        cwd=repo_path,
        timeout=30,
    )

    response = {
        "status": "ready",
        "action": action,
        "pr_number": resolved_pr_number,
        "head_ref": head_ref,
        "head_sha": head_sha,
        "outside_voice_review_present": status.has_review or action == "ran-review",
    }
    if result is not None:
        response["reviewer_provider"] = result.reviewer_provider
        response["verdict"] = result.verdict
        response["artifact_path"] = result.artifact_path
    return response


__all__ = [
    "ALTERNATE_PROVIDERS",
    "COMMENT_MARKER",
    "CrossModelReviewError",
    "CrossModelReviewResult",
    "PublishMode",
    "ReviewFinding",
    "ReviewLookup",
    "ReviewRequest",
    "ReviewScope",
    "ReviewVerdict",
    "build_review_command",
    "build_review_prompt",
    "current_head_sha",
    "default_base_ref",
    "detect_current_provider",
    "load_review_status",
    "normalize_verdict",
    "mark_pr_ready",
    "publish_review_comment",
    "record_review_skip",
    "render_review_markdown",
    "resolve_repo_root",
    "resolve_review_request",
    "resolve_target_provider",
    "run_cross_model_review",
    "save_review_artifact",
    "validate_provider_auth",
    "validate_provider_available",
]
