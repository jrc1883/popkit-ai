#!/usr/bin/env python3
"""Run an advisory outside-voice review from a PopKit skill."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGES_DIR = Path(__file__).resolve().parents[4]
SHARED_PY_DIR = PACKAGES_DIR / "shared-py"
if str(SHARED_PY_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_PY_DIR))

from popkit_shared.utils.cross_model_review import (  # noqa: E402
    CrossModelReviewError,
    PublishMode,
    ReviewRequest,
    ReviewScope,
    load_review_status,
    record_review_skip,
    render_review_markdown,
    run_cross_model_review,
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run an advisory outside-voice code review.")
    parser.add_argument("--repo-root", help="Repository root. Defaults to the current git repo.")
    parser.add_argument("--base", help="Base ref for branch/PR reviews.")
    parser.add_argument("--pr", type=int, help="PR number to review.")
    parser.add_argument("--commit", help="Commit SHA to review.")
    parser.add_argument(
        "--target-provider",
        default="auto",
        choices=["auto", "claude-code", "codex"],
        help="Target provider to run the advisory review with.",
    )
    parser.add_argument(
        "--publish",
        default=PublishMode.NONE.value,
        choices=[mode.value for mode in PublishMode],
        help="Optional publication mode for GitHub PR comments.",
    )
    parser.add_argument(
        "--scope",
        choices=[scope.value for scope in ReviewScope],
        help="Explicit review scope. Defaults to branch unless another scope flag is provided.",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Alias for uncommitted review scope to match existing git review usage.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show existing outside-voice review status for the current head.",
    )
    parser.add_argument(
        "--skip",
        action="store_true",
        help="Record that outside-voice review was explicitly skipped.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of Markdown/human-readable output.",
    )
    return parser.parse_args()


def determine_scope(args: argparse.Namespace) -> ReviewScope:
    """Determine review scope from flags."""
    if args.scope:
        return ReviewScope(args.scope)
    if args.staged:
        return ReviewScope.UNCOMMITTED
    if args.pr is not None:
        return ReviewScope.PR
    if args.commit:
        return ReviewScope.COMMIT
    return ReviewScope.BRANCH


def main() -> int:
    """CLI entrypoint."""
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else None

    try:
        if args.status:
            status = load_review_status(repo_root or Path.cwd())
            if args.json:
                print(json.dumps(status.to_dict(), indent=2))
            elif status.has_review:
                print(
                    f"Outside-voice review exists for {status.head_sha}: "
                    f"{', '.join(review.reviewer_provider for review in status.reviews)}"
                )
            else:
                print(f"No outside-voice review found for {status.head_sha}.")
            return 0

        if args.skip:
            payload = record_review_skip(repo_root or Path.cwd())
            if args.json:
                print(json.dumps({"status": "skipped", **payload}, indent=2))
            else:
                print(
                    "Recorded outside-voice review skip for "
                    f"{payload['head_ref']} ({payload['head_sha'][:12]})."
                )
            return 0

        request = ReviewRequest(
            scope=determine_scope(args),
            repo_root=repo_root,
            base_ref=args.base,
            pr_number=args.pr,
            commit_sha=args.commit,
            target_provider=args.target_provider,
            publish=PublishMode(args.publish),
        )
        result = run_cross_model_review(request)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(render_review_markdown(result))
        return 0
    except CrossModelReviewError as exc:
        payload = {"status": "error", "message": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Outside-voice review failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
