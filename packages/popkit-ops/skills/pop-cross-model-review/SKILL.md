---
name: cross-model-review
description: "Run an advisory outside-voice review through the opposite model family. Uses Codex when working in Claude Code, and Claude Code when working in Codex, unless explicitly overridden. Produces a normalized review artifact, prints the advisory report, and can optionally publish it as a PR comment keyed to the current head SHA."
inputs:
  - from: any
    field: git_range
    required: false
outputs:
  - field: review_artifact
    type: file_path
  - field: reviewer_provider
    type: string
  - field: verdict
    type: string
next_skills:
  - pop-code-review
  - pop-finish-branch
---

# Cross-Model Review

Run an advisory outside-voice review using the opposite model family when possible.

## When To Use

- Before marking a PR ready when you want a second opinion from a different model.
- During branch completion when you want a non-blocking advisory review.
- When a user explicitly asks for an outside voice, second model, or cross-model review.

## Commands

Run the script directly from the repo root:

```bash
python packages/popkit-ops/skills/pop-cross-model-review/scripts/run_review.py
```

Common variants:

```bash
# Review the current branch diff against the default base branch
python packages/popkit-ops/skills/pop-cross-model-review/scripts/run_review.py

# Review uncommitted changes (matches /popkit-dev:git review --staged intent)
python packages/popkit-ops/skills/pop-cross-model-review/scripts/run_review.py --staged

# Review a PR and publish/update an advisory PR comment
python packages/popkit-ops/skills/pop-cross-model-review/scripts/run_review.py --pr 123 --publish comment

# Force a specific reviewer provider
python packages/popkit-ops/skills/pop-cross-model-review/scripts/run_review.py --target-provider codex

# Check whether the current head already has an outside-voice review
python packages/popkit-ops/skills/pop-cross-model-review/scripts/run_review.py --status

# Record an explicit skip during finish-branch / PR-ready flow
python packages/popkit-ops/skills/pop-cross-model-review/scripts/run_review.py --skip

# Mark a draft PR ready, requiring an outside-voice review by default
python packages/popkit-ops/skills/pop-cross-model-review/scripts/pr_ready.py --pr 123

# Run the review automatically if missing, then mark ready
python packages/popkit-ops/skills/pop-cross-model-review/scripts/pr_ready.py --pr 123 --run-review-if-missing --publish comment

# Record an explicit skip, then mark ready
python packages/popkit-ops/skills/pop-cross-model-review/scripts/pr_ready.py --pr 123 --skip-outside-voice
```

## Finish-Branch Guidance

During `pop-finish-branch`, do not force outside voice on every completion path.

- If the user is merging locally, keeping the branch, or discarding work, outside voice is optional.
- If the user explicitly wants a second opinion before PR creation, run `run_review.py`.
- If the user is marking a draft PR ready, prefer `pr_ready.py` instead of manual status checks.
- Use `--run-review-if-missing --publish comment` when you want the helper to run the advisory review and advance the PR in one step.
- Use `--skip-outside-voice` only when the user explicitly declines the advisory review.

## Notes

- This review is advisory only. It does not block merge and does not replace human approval.
- Artifacts are stored in PopKit plugin data, not in the repo.
- Re-running on the same head SHA updates the stored artifact and reuses the PR comment marker.
