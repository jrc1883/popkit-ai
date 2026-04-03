#!/usr/bin/env python3
"""Mark a draft PR ready with outside-voice review enforcement."""

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
    mark_pr_ready,
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Mark a draft PR ready after outside-voice review checks."
    )
    parser.add_argument("--repo-root", help="Repository root. Defaults to the current git repo.")
    parser.add_argument("--pr", type=int, help="PR number to mark ready. Defaults to current PR.")
    parser.add_argument(
        "--run-review-if-missing",
        action="store_true",
        help="Run outside-voice review automatically when no current-head artifact exists.",
    )
    parser.add_argument(
        "--skip-outside-voice",
        action="store_true",
        help="Record an explicit outside-voice skip when no artifact exists.",
    )
    parser.add_argument(
        "--target-provider",
        default="auto",
        choices=["auto", "claude-code", "codex"],
        help="Reviewer provider to use if a review must be run.",
    )
    parser.add_argument(
        "--publish",
        default=PublishMode.COMMENT.value,
        choices=[mode.value for mode in PublishMode],
        help="How to publish the review if one must be run.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path.cwd()

    try:
        result = mark_pr_ready(
            repo_root=repo_root,
            pr_number=args.pr,
            run_review_if_missing=args.run_review_if_missing,
            skip_if_missing=args.skip_outside_voice,
            target_provider=args.target_provider,
            publish=PublishMode(args.publish),
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(
                f"PR #{result['pr_number']} marked ready "
                f"({result['action']}, head {result['head_sha'][:12]})."
            )
        return 0
    except CrossModelReviewError as exc:
        payload = {"status": "error", "message": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Cannot mark PR ready: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
