# `quality-gate.py` Audit

**Purpose:** Phase 0 deliverable from `~/.claude/plans/verifier-pair-infrastructure-v1.md` (Plan v4.2). Documents what `packages/popkit-core/hooks/quality-gate.py` does today, where the verifier-pair work intends to extend it (NOT replace), and what tests must land before any wrapping code merges.

Codex round-3 #6: extend, don't rewrite. Codex round-4 #4 + round-6 enumerated the 8 audit sections this doc covers; the auditor reads `quality-gate.py` and decides what's safely wrap-able vs what needs explicit work.

This audit is read-only — it changes nothing in `quality-gate.py`. Wrapper code lands in a follow-up PR after Codex reviews this doc.

---

## 1. Current entry points

`quality-gate.py` is invoked as a Claude Code `PostToolUse` hook (registered in `packages/popkit-core/hooks/hooks.json`). Trigger surface:

- **Hook invocation**: Claude Code's PostToolUse pipeline pipes a JSON payload to the script's stdin (`{ tool_name, tool_args, ... }`). The script runs `process(input_data)` from `__main__`.
- **CLI invocation** (defensive): the script's `main()` reads stdin and exits with status reflecting the result. Direct CLI is supported but not the primary use.
- **Test invocation**: existing tests under `packages/popkit-core/tests/hooks/test_quality_gate_command.py` and siblings load the module via `importlib.util.spec_from_file_location` (no package import — the file has a hyphen).

**Implication for verifier work:** wrappers must accept the same hook-invocation contract (stdin JSON, status-coded exit, `hooks.json`-compatible). A new lane-aware mode adds an env var (`POPKIT_LANE_ID`) that the dispatcher sets before the PostToolUse hook fires.

## 2. Inputs / outputs

**Inputs:**

- stdin: JSON `{ tool_name: str, tool_args: dict, ... }` from PostToolUse.
- `.claude/quality-gates.json` (config; optional): `{ triggers, gates, options }`.
- `package.json` / `pyproject.toml` / etc. for auto-detection in `detect_gates()`.

**Outputs:**

- stdout: JSON `{ status: "success" | "block" | "warn", message, ... }` consumed by Claude Code.
- Side-effect writes to `.claude/quality-gate-state.json`, `.claude/checkpoints/<timestamp>/`, audit-log entries.
- Exit code: 0 for success, non-zero for hook-block.

**Implication:** the lane-config wrapper reads gates from the active lane manifest (via `lane_manifest_loader.py`) instead of `.claude/quality-gates.json`. The output JSON shape stays the same so existing Claude Code consumers don't change. The wrapper substitutes the gate source, not the gate runner.

## 3. State files

- `.claude/quality-gate-state.json` — counters (`file_edit_count`, `recent_files`, `recent_file_count`), `test_results` ledger, last-run timestamps.
- `.claude/quality-gates.json` — config (gates list, triggers, options).
- `.claude/checkpoints/<timestamp>/` — per-checkpoint patches + manifest.
- `.claude/logs/` — referenced indirectly via PopKit's broader logging.

**Implication:** Plan v4.2 cost ledger is USER-LOCAL (`~/.claude/popkit/cost-ledger.jsonl`) NOT under repo `.claude/` — different storage tier. The verifier work doesn't touch `quality-gate-state.json`. Quality gate state stays repo-local; cost ledger is durable across `git clean -fdx`.

## 4. Failure semantics

- **Gate command non-zero exit** → `run_gate` returns `{ passed: False, ... }`. Aggregated by `run_all_gates`.
- **Fail-fast** (default per config `options.fail_fast`): first failure short-circuits remaining gates.
- **Power-mode lightweight check** (`is_power_mode_active() → run_lightweight_check`): skips heavy gates, runs a 15s cap.
- **Adversarial / hook timeout** (180s `hooks.json` timeout, see file header): individual `subprocess.run` calls have their own per-gate timeout that's smaller; aggregate stays under the wrapping hook timeout.
- **Test flakiness** (`check_flaky_tests`): if a test passes/fails non-deterministically over recent runs, surfaces as a `flaky` warning rather than a hard failure.
- **Destructive ops** (`destructive_ops_allowed`): rollback is gated behind config opt-in.

**Implication for verifier work:** the lane-config wrapper preserves these failure semantics. Compliance lanes' `closed_human` `on_verifier_unreachable` semantics apply to LLM-verifier failures, NOT to deterministic-gate failures (which already have their own clean failure path here).

## 5. Timeout behavior

- Hook outer timeout: 5000ms for Stop-style hooks elsewhere; **180000ms (180s) for `quality-gate.py`'s PostToolUse entry** (see file-header rationale).
- Per-gate timeout: tunable via `gates[].timeout_seconds` (default 60s); `subprocess.run(timeout=...)` enforced.
- Power-mode lightweight: 15s cap.

**Implication:** Plan v4.2 lane-manifest `deterministic_gates[].timeout_seconds` (1-600 inclusive per `lane-manifest.schema.json`) cleanly maps onto the existing per-gate timeout. The wrapper just reads the lane manifest's gate list and feeds it to the existing runner. No timeout-handling code changes.

## 6. Privacy risks

**Currently logged content that the new redaction policy would forbid:**

- `recent_files` in `.claude/quality-gate-state.json` keeps file paths only — paths CAN reveal child-data fixture locations (e.g., `apps/shprd/src/__tests__/fixtures/attachments/family-snapshot.pdf`). Path strings are typically safe but the FACT that a path was edited might leak intent.
- `test_results` ledger: keeps test names + pass/fail. Test names can be descriptive (`describe('parent uploads attachment for child Alice'...)`). Risk: names could embed PII or fixture references.
- Error-output capture (`format_errors_for_context`): pipes test-runner stdout into the Claude Code context. **Test runners can print fixture content on assertion failure.** This is the highest privacy-risk surface.

**Wrapper requirement:** the verifier-pair wrapper redacts gate outputs through Tier 1 path filter + Tier 2 regex content scan (per `packages/popkit-core/REDACTION_POLICY.md`) BEFORE they land in any artifact bound for the LLM verifier. The existing `quality-gate.py` continues to write its raw output to `.claude/quality-gate-state.json` (repo-local, gitignored, not sent to Codex); only the dispatcher's bundle goes through redaction.

**Pre-existing concern (not a regression):** the `logs/stop.json` raw-input dump in the existing `stop.py` (Codex round 4 #4) is a known privacy violation and is removed by the verifier work. `quality-gate-state.json` is similar in spirit but stays repo-local — acceptable as long as nothing forwards it to a third party.

## 7. Lane-manifest extension points

Concrete file:line where the wrapper plugs in:

- **`QualityGateHook.__init__`** (line 75): the wrapper inspects `os.environ.get("POPKIT_LANE_ID")`. If set, it loads the lane manifest via `lane_manifest_loader.load_lane_manifest()` and substitutes `self.config["gates"]` with `lane.deterministic_gates`. If unset, falls through to current `.claude/quality-gates.json` config.
- **`QualityGateHook.load_config`** (line 113): cleanest single-point override. Add an early-return branch that prefers lane-manifest gates when `POPKIT_LANE_ID` is set.
- **`QualityGateHook.detect_gates`** (line 126): not touched. Auto-detection stays for projects without a lane manifest.
- **`QualityGateHook.run_gate`** (line 313): not touched. The runner is generic (cwd, command, timeout, evidence-artifact). Lane-manifest gate specs (per `lane-manifest.schema.json` definitions/deterministic_gate) are field-compatible.

**Wrap surface size:** approximately 30-50 LOC change isolated to `load_config`. All other methods stay untouched.

## 8. Tests required before wrapping

The wrapper PR must include all of the following BEFORE any line of wrapping code merges:

1. **Lane-config substitution test** — when `POPKIT_LANE_ID` is set, `load_config` returns gates from the lane manifest, not from `.claude/quality-gates.json`. Mock the lane manifest loader.
2. **Fall-through test** — when `POPKIT_LANE_ID` is unset, current behavior is byte-identical (regression guard for the 95% of repos that don't use the verifier pair).
3. **Per-gate evidence-artifact capture test** — the new `evidence_artifact: stdout-tail-50` etc. options produce the expected captured form. (Currently `quality-gate.py` doesn't capture per-gate evidence in the artifact-typed way the lane manifest defines; the wrapper adds this.)
4. **Failure semantics regression test** — gate failure when running under lane manifest produces the same JSON output shape and the same exit code as gate failure under `.claude/quality-gates.json`.
5. **Privacy-redaction integration test** — the wrapper's evidence-artifact output, when fed through the Phase 0a redaction fixtures, produces the expected Tier 1 / Tier 2 results.
6. **Power-mode interaction test** — lane manifest does NOT override the power-mode lightweight check; if power mode is active, the lightweight path runs regardless of lane-manifest gates.

These tests live alongside existing hook tests at `packages/popkit-core/tests/hooks/`.

---

## 9. Terminology / deprecation map

Round-6 #6 directive: align language with ADR 0004 (`power-mode-is-legacy-language.md`). The audit is for `quality-gate.py` specifically (which is NOT power-mode code), but it touches power-mode adjacency:

| Legacy term in `quality-gate.py`                                  | Canonical concept (ADR 0004)                            | Action                                                                                                                                       |
| ----------------------------------------------------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `is_power_mode_active()`                                          | Multi-Agent Coordination active session                 | Keep the method name (it's external API to other hooks); document the deprecation in the docstring; rename when Phase 4 audits `power-mode/` |
| `run_lightweight_check()`                                         | Reduced-budget multi-agent gate path                    | Same                                                                                                                                         |
| Comment "Power Mode - runs lightweight 15s checks only" (line 24) | Multi-agent-coordination-mode lightweight path          | Rewrite at Phase 4                                                                                                                           |
| `.claude/quality-gates.json` config schema                        | Stays as-is — config schema is repo-stable user surface | No change                                                                                                                                    |

The verifier-pair wrapper does NOT introduce any new "power-mode" terminology. It refers to lanes via `lane_id` (Multi-Agent Coordination concept) only.

## 10. Wrap-vs-migrate recommendation

**Recommendation: WRAP.** `quality-gate.py` is well-designed for its current scope (file-header AUDIT NOTE 2026-03-19 calls out "high value, well-designed"). The verifier-pair work needs only a 30-50 LOC config-source override at `load_config`, plus the per-gate evidence-artifact capture (item 3 above).

**Why not migrate:**

- The hook is 886 LOC of careful state/checkpoint/rollback logic. Re-implementing risks losing edge cases (flaky-test detection, fail-fast semantics, destructive-ops gating).
- Existing PopKit consumers depend on the current `hooks.json` Stop entry shape. A migration changes the integration surface.
- The lane-manifest extension is purely additive — the existing config path still works for repos without lane manifests.

**Migrate condition:** if Phase 4 (Multi-Agent Coordination audit of `power-mode/`) decides to migrate `is_power_mode_active()` and `run_lightweight_check()` to the new contract, `quality-gate.py` updates as a downstream consumer of the new API. That's a Phase 4-or-later concern, not Phase 0/1.

**What the wrapper PR explicitly does NOT do:**

- Doesn't touch `__init__`, `detect_gates`, `run_gate`, `parse_errors`, `check_flaky_tests`, `present_failure_menu`, `create_checkpoint`, `rollback`, `update_manifest`, `cleanup_old_checkpoints`.
- Doesn't add new state files.
- Doesn't change the hook timeout.
- Doesn't introduce any compliance-class semantics into `quality-gate.py` (those live in the dispatcher, not the gate runner).
