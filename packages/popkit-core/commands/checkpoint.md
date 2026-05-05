---
description: "Write a claim ledger for the verifier dispatcher (Plan v4.2 Layer 1)"
argument-hint: "<lane-id>"
---

# /popkit-core:checkpoint

Write the builder agent's atomic claim ledger for the current turn so the
verifier can validate them against the diff + tests without inferring intent
from transcript prose.

This is the **canonical writer** for `claim-ledger.schema.json`. The Stop-hook
dispatcher (Phase 1a-ii) reads what this command writes; if you don't call
`/checkpoint` before turn-end the dispatcher writes a `status: "missing"` stub
and the verifier returns `verdict: "human"` with reason
`claim_ledger_missing_or_invalid`.

## Architecture

| Field                  | Source                                                                |
| ---------------------- | --------------------------------------------------------------------- |
| Slash command markdown | `packages/popkit-core/commands/checkpoint.md` (this file)             |
| Writer script          | `packages/popkit-core/scripts/checkpoint_writer.py`                   |
| Schema                 | `packages/popkit-core/output-styles/schemas/claim-ledger.schema.json` |
| Pending location       | `<repo>/.claude/popkit/pending-claim-ledger.json`                     |

The slash command shells out to the writer script so the validation logic is
unit-testable independently of the markdown surface (Codex round 6 #3).

## Required fields

| Field               | Type                                              | Notes                                                                                                 |
| ------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `lane_id`           | string                                            | Identifier from the active lane manifest.                                                             |
| `stage`             | enum: `plan` \| `code`                            | Plan-stage reviews verify a plan doc; code-stage verifies diffs.                                      |
| `intent`            | string                                            | One-line user-requested goal for this turn.                                                           |
| `changed_files`     | array of `{path, added?, removed?}`               | Empty array is valid for plan-only turns.                                                             |
| `acceptance_claims` | array of non-empty strings                        | What this turn's changes are SUPPOSED to satisfy. The verifier validates each claim against the diff. |
| `next_action`       | enum: `verify` \| `merge-ready` \| `needs-review` | Builder's recommendation; the verifier may override.                                                  |

## Optional fields

| Field                          | Type                                                                                   |
| ------------------------------ | -------------------------------------------------------------------------------------- |
| `tests_run`                    | array of `{name, passed?, failed?}`                                                    |
| `deterministic_gates_observed` | object mapping gate id → `pass` \| `fail` \| `skip`                                    |
| `compliance_touch`             | array of `none` \| `schema` \| `audit` \| `auth` \| `child-data` \| `ferpa` \| `coppa` |
| `known_gaps`                   | array of strings — explicitly out-of-scope items                                       |

## Instructions

When the user runs `/popkit-core:checkpoint`:

1. **Build the ledger payload** as a Python dict from the current turn's
   atomic claims. Include every required field above, plus any optional
   fields that apply to the turn.
2. **Pipe the payload as JSON to `checkpoint_writer.py`** via subprocess.
   The script validates and writes the pending ledger.
3. **Surface the result** — on success, the writer prints `{"ok": true,
"path": ..., "turn_id": ..., "session_id": ...}` to stdout. On failure
   it prints `{"ok": false, "error": ...}` to stderr with a non-zero exit
   code.

### Reference invocation

```python
import json
import os
import subprocess
import sys
from pathlib import Path

# 1. Assemble the ledger from the current turn's atomic claims.
payload = {
    "lane_id": "popkit-docs",          # Replace with the active lane id.
    "stage": "code",                   # or "plan"
    "intent": "Close codex round-8 P2 finding",
    "changed_files": [
        {"path": "packages/popkit-core/scripts/lane_manifest_loader.py",
         "added": 41, "removed": 8},
        {"path": "packages/popkit-core/tests/test_lane_manifest_loader.py",
         "added": 77, "removed": 10},
    ],
    "acceptance_claims": [
        "loader rejects unhashable enum inputs with LaneManifestError",
        "lanes_doctor --json emits clean error JSON on the unhashable case",
    ],
    "next_action": "verify",
}

# Optional fields — include when relevant.
payload["tests_run"] = [
    {"name": "test_lane_manifest_loader.py", "passed": 75, "failed": 0},
    {"name": "test_lanes_doctor.py", "passed": 29, "failed": 0},
]
payload["deterministic_gates_observed"] = {
    "ruff-lint": "pass",
    "ruff-format": "pass",
    "pytest": "pass",
}
payload["compliance_touch"] = ["none"]

# 2. Resolve the writer script path. CLAUDE_PLUGIN_ROOT (when running
#    inside Claude Code) points at the plugin directory; fall back to
#    walking up from cwd for direct invocation.
plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
if plugin_root:
    writer = Path(plugin_root) / "scripts" / "checkpoint_writer.py"
else:
    here = Path.cwd()
    for candidate in (here, *here.parents):
        wp = candidate / "packages" / "popkit-core" / "scripts" / "checkpoint_writer.py"
        if wp.exists():
            writer = wp
            break
    else:
        print("[ERROR] could not locate checkpoint_writer.py", file=sys.stderr)
        raise SystemExit(1)

# 3. Pipe payload to the writer; surface the writer's exit code.
result = subprocess.run(
    [sys.executable, str(writer)],
    input=json.dumps(payload),
    capture_output=True,
    text=True,
    timeout=10,
)

if result.returncode == 0:
    info = json.loads(result.stdout)
    print(f"[OK] Pending claim ledger written.")
    print(f"  path:       {info['path']}")
    print(f"  turn_id:    {info['turn_id']}")
    print(f"  session_id: {info['session_id']}")
    print()
    print("The Stop-hook dispatcher will archive this into the per-turn")
    print("verifier bundle at end-of-turn. Run /checkpoint again to")
    print("replace it (last-writer-wins).")
else:
    err = result.stderr.strip() or result.stdout.strip() or "unknown error"
    print(f"[ERROR] checkpoint_writer rejected the ledger:", file=sys.stderr)
    print(f"  {err}", file=sys.stderr)
    raise SystemExit(result.returncode)
```

## What the writer does NOT do

- **Does not call the verifier.** That happens later via `popkit-verifier-runner`
  (Phase 1a-iii).
- **Does not redact.** Redaction is the Stop-hook dispatcher's job (Phase 1a-ii)
  before the bundle is handed to the verifier.
- **Does not synthesize claims from transcript prose.** The whole point of
  this command is that the builder writes claims explicitly. If you skip
  `/checkpoint`, the dispatcher writes a stub and the verifier returns
  `human` immediately.
- **Does not assume a session_id or turn_id.** The writer reads
  `CLAUDE_SESSION_ID` / `POPKIT_SESSION_ID` from env or generates a UUID4
  per call. The dispatcher in Phase 1a-ii will reconcile these against the
  Claude Code Stop-hook payload.

## Failure modes

| Symptom                                           | Cause                      | Fix                                                       |
| ------------------------------------------------- | -------------------------- | --------------------------------------------------------- |
| `missing required field(s): lane_id`              | Forgot to include lane_id  | Add `lane_id: <active-lane-id>` from `.claude/lanes.yml`. |
| `stage must be one of ['code', 'plan']`           | Used a different label     | Use exactly `code` or `plan`.                             |
| `acceptance_claims[N] must be a non-empty string` | Empty bullet               | Either remove the bullet or write a real claim.           |
| `could not locate repository root`                | Running outside a git repo | Invoke from inside the repo root.                         |
| `write failed: ...`                               | Disk / permissions         | Check `<repo>/.claude/popkit/` is writable.               |

## Related

- Schema: `packages/popkit-core/output-styles/schemas/claim-ledger.schema.json`
- Writer: `packages/popkit-core/scripts/checkpoint_writer.py`
- Tests: `packages/popkit-core/tests/test_checkpoint_writer.py`
- Plan: `~/.claude/plans/verifier-pair-infrastructure-v1.md` (Layer 1, Round 5 #4, Round 6 #3)
