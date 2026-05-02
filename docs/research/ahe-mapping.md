# Applying Agentic Harness Engineering (AHE) to PopKit

> **Status:** Research note. No code changes proposed in this document.
> **Source paper:** *Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent Harnesses* — Lin et al., Fudan / PKU / Qiji Zhifeng, [arXiv:2604.25850](https://arxiv.org/abs/2604.25850), April 2026. Code: [china-qijizhifeng/agentic-harness-engineering](https://github.com/china-qijizhifeng/agentic-harness-engineering).

---

## 1. Why this matters

AHE defines a method for automatically evolving the **harness** around a coding agent — system prompts, tool descriptions, tool implementations, middleware, skills, sub-agents, and long-term memory — while the base LLM stays fixed. The loop is driven by three matched observability pillars: **component**, **experience**, and **decision**. Empirically, ten AHE iterations lifted Terminal-Bench 2 pass@1 from **69.7 % → 77.0 %**, beating the human-designed Codex-CLI harness (71.9 %) and self-evolving baselines ACE and TF-GRPO.

**Thesis.** PopKit already supplies roughly 80 % of AHE's substrate. File-based components, a scanning registry, a feedback store, Upstash telemetry, and a hook system are all in place. What's missing is a thin layer that turns those raw signals into a layered evidence corpus, plus a convention for declaring *why* an edit was made and verifying it after the fact. Adding that layer would turn PopKit from a static plugin framework into a self-improving harness — without changing its LLM-agnostic, programmatic-first philosophy.

This sits naturally inside [`docs/VISION.md`](../VISION.md) Phase 4 (orchestration): once PopKit can route work across providers, AHE gives it a feedback signal to evolve *which* skills and prompts are routed.

---

## 2. Mapping the three pillars onto PopKit

### 2.1 Component observability

> *AHE: every editable harness piece is a file-level artifact, mapped to a failure-pattern class, and revertible.*

- **What PopKit has.** YAML-frontmatter component files (`SKILL.md`, `AGENT.md`, `commands/*.md`); a scanning registry in `packages/popkit-mcp/popkit_mcp/tool_registry.py` (`scan_skills`, `scan_agents`, `scan_commands`); a per-file `version:` field; full git history.
- **What's missing.** No explicit failure-pattern → component mapping. No central index answering "which component is the canonical home for fixing X?" No rollback affordance beyond `git revert`.
- **Proposed addition.** A single `failure_classes:` list in YAML frontmatter — e.g. `failure_classes: [tool-misuse, context-loss, premature-exit]` — plus a `popkit-package.yaml`-derived index keyed by failure class, generated at scan time. Reuses the existing scan; adds one field.

### 2.2 Experience observability

> *AHE: distill millions of raw trajectory tokens into a layered, drill-down evidence corpus that an evolving agent can actually consume.*

- **What PopKit has.** A SQLite feedback store at `~/.claude/config/feedback.db` (per-session ratings, `agent_name`, `tool_call_count`); Upstash Redis streams keyed `popkit:*:{session_id}:{traces|decisions|events|meta}`. Hooks (`session-start.py`, `post-tool-use.py`, `chain-metrics.py`, `feedback_hook.py`, `agent-observability.py`) already write to both.
- **What's missing.** The *layered drill-down corpus*. Today, raw traces and ratings exist but are not joined, aggregated, or indexed by component. A meta-agent has no way to drill from "skill X has the lowest rating" → "here are five representative failing trajectories" → "here is the tool sequence at the failure point."
- **Proposed addition.** A periodic aggregator that materialises four layers from existing sources:

  | Layer | Content | Source |
  |---|---|---|
  | **L0** | Raw trajectory digests | Upstash streams (compressed mirror in local SQLite for offline queries) |
  | **L1** | Per-component aggregates: invocation count, completion rate, mean rating, error rate, p50 / p95 duration | `feedback.db` JOIN trajectory data |
  | **L2** | Failure-class tags | Declared `failure_classes` ∪ LLM-tagged trajectory clusters |
  | **L3** | Top-K representative trajectories per (component, failure-class) cell | L0 sampled by L2 tag |

  Reuses `FeedbackStore`, `upstash_telemetry`, and the existing hooks. The new code is the aggregator and a small read API.

### 2.3 Decision observability

> *AHE: every edit is paired with a self-declared prediction, verified against the next round's task-level outcomes.*

- **What PopKit has.** Nothing structured. Edits to skills / agents / commands today are plain commits with no machine-readable claim about what they were trying to fix.
- **What's missing.** A **change manifest** that pairs each edit with `{target_failure_class, predicted_metric_delta, verification_window}`, then verifies it.
- **Proposed addition.** A sidecar convention — either `CHANGE.yaml` next to the edited file or a single append-only `~/.popkit/data/changes.jsonl` — written whenever a component file is edited. Schema sketch:

  ```yaml
  component: packages/popkit-dev/skills/pop-next-action/SKILL.md
  edit_id: 2026-05-02-a1b2c3
  target_failure_classes: [stale-recommendations]
  prediction:
    metric: mean_rating
    direction: up
    min_delta: 0.3
  verification:
    window_sessions: 25
    decided_at: null   # filled after window closes
    outcome: null      # accepted | reverted | inconclusive
  ```

  A future `popkit evolve verify` walks open manifests, reads L1 aggregates, and stamps `outcome`.

---

## 3. Gap table

| AHE concept | PopKit primitive that fits | Exists today | Missing | Effort |
|---|---|---|---|---|
| Component substrate | YAML-frontmatter components under `packages/popkit-*/{skills,agents,commands}/` | ✅ | — | none |
| Component → failure-class index | `tool_registry.py` scan output + new `failure_classes` field | partial | failure-class field; index | S |
| Raw trajectory storage (L0) | Upstash streams via `upstash_telemetry.py` | ✅ remote | local mirror; retention policy | S |
| Per-component aggregates (L1) | `feedback.db` (`feedback`, `feedback_aggregates`, `session_state`) | partial | join trajectory ↔ feedback; per-component rollups | M |
| Failure-class tags (L2) | `failure_classes` + LLM tagging over L0 | ❌ | tagger; storage | M |
| Drill-down corpus (L3) | Sampled subset of L0, indexed by L2 | ❌ | sampler; read API | S |
| Change manifest | `CHANGE.yaml` sidecar or `changes.jsonl` | ❌ | convention; writer | S |
| Verification loop | `popkit evolve verify` reading L1 against manifest | ❌ | CLI; statistical thresholds | M |
| Evolve sub-agent | New agent under a chosen package; reuses MCP layer | ❌ | agent definition; prompt | M |
| A/B harness via worktrees | `packages/popkit-dev/` worktree commands | ✅ | wiring to evolve loop | M |

---

## 4. Phased rollout

- **Phase 0 — this doc.** Establish vocabulary, gap analysis, and decisions to defer.
- **Phase 1 — Observability MVP.** L1/L2/L3 aggregator; `failure_classes` frontmatter field; new MCP tools `popkit_get_skill_stats`, `popkit_get_failure_modes`; `popkit evolve report` CLI command. **No auto-edits.** Useful on its own as a feedback dashboard.
- **Phase 2 — Decision observability.** Change-manifest convention; `popkit evolve record` and `popkit evolve verify` CLI subcommands. Edits stay human-authored; the system just remembers what each edit was *for* and grades it.
- **Phase 3 — Closed loop.** An `evolve` sub-agent that reads the corpus, proposes edits, writes a manifest, applies edits inside a worktree (using existing popkit-dev worktree machinery), runs A/B over K sessions, and accepts or reverts.

Phases 1 and 2 are independently shippable and provide value even if Phase 3 never lands.

---

## 5. Where the code could live (open question)

Three options, not yet decided:

- **(a) New `popkit-evolve` package.** Cleanest separation; matches the existing per-package shape (`popkit-core` / `popkit-dev` / `popkit-ops` / `popkit-research`). Opt-in install. Reads from `shared-py` and `popkit-mcp`, registers new MCP tools.
- **(b) Extend `popkit-research`.** Thematic adjacency: research already owns knowledge capture, embeddings, and semantic search. L2 trajectory clustering could reuse the existing embedding store at `~/.claude/embeddings/embeddings.db`.
- **(c) Extend `popkit-core` + `shared-py`.** Treat observability as foundational. Add tables to `feedback.db`, register MCP tools in the existing server. Lowest install friction; highest blast radius on the most-installed package.

Recommendation: defer this decision until Phase 1 scope is locked. The L1 aggregator and frontmatter changes are small enough to prototype in any of the three locations and move later.

---

## 6. Risks and open questions

- **Over-instrumentation cost.** A layered corpus must be lazy and sampled or local SQLite grows unbounded. Need a retention policy for L0 mirroring; reuse Upstash retention as the source of truth.
- **Privacy.** Trajectory digests can leak repo contents. Default policy must be local-only L0; remote sync gated by explicit user opt-in.
- **Verification statistical power.** Per-user session counts are small. `min_delta`-based verification will often be inconclusive on a single user's data. For shared `popkit-*` skills, opt-in cross-user aggregation could restore power; user-authored skills stay strictly local.
- **Failure-class taxonomy.** The paper does not enumerate one. Phase 1 should ship a starter taxonomy (`tool-misuse`, `context-loss`, `premature-exit`, `stale-state`, `hallucinated-API`, `infinite-loop`) and treat it as evolvable.
- **LLM-agnosticism.** AHE assumes a fixed base model. PopKit promises provider-agnostic operation. The evolve agent itself must run through the same MCP layer it's evolving so the loop works across Claude Code, Cursor, Codex, Copilot, etc.

---

## 7. Files referenced (for whoever picks this up)

- Components scanned: `packages/popkit-*/skills/`, `agents/`, `commands/`
- Registry: `packages/popkit-mcp/popkit_mcp/tool_registry.py`
- MCP server tool registration: `packages/popkit-mcp/popkit_mcp/server.py`
- Feedback store: `packages/shared-py/popkit_shared/utils/feedback_store.py`
- Upstash telemetry: `packages/shared-py/popkit_shared/utils/upstash_telemetry.py`
- Hooks already capturing data: `packages/popkit-core/hooks/{session-start.py,post-tool-use.py,chain-metrics.py,feedback_hook.py,agent-observability.py}`
- CLI entry for future `popkit evolve`: `packages/popkit-cli/popkit_cli/main.py`
- Worktree machinery (Phase 3 A/B): `packages/popkit-dev/` worktree commands
- Vision context: [`docs/VISION.md`](../VISION.md)
