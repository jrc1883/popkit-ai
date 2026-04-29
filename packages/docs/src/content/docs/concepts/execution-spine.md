---
title: Execution Spine
description: A small PopKit contract for connecting context, sandboxed execution, and evaluation
---

# Execution Spine

PopKit should treat execution as a spine, not as another pile of commands:

```text
Context -> Sandbox or worktree execution -> Verification and eval -> Handoff
```

The useful lesson from Sandcastle, Evalite, and Matt Pocock's skills is not
"install another repo." It is that the strongest systems keep a small,
inspectable artifact at the center of the workflow.

## What We Learn

| Source                                                 | Useful pattern                                                                 | PopKit application                                                                                        |
| ------------------------------------------------------ | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| [Sandcastle](https://github.com/mattpocock/sandcastle) | Objective-driven execution that produces logs, commits, and reviewable output. | Keep a canonical lane result that records objective, backend, branch, artifacts, checks, and next action. |
| [Evalite](https://github.com/mattpocock/evalite)       | Evals are part of development, not an afterthought.                            | Score skill and lane outputs before adding a runtime eval dependency.                                     |
| [skills](https://github.com/mattpocock/skills)         | Small focused skills with explicit scope and reusable methodology.             | Keep PopKit skills protocol-shaped; avoid broad magic commands with unclear output.                       |
| PopKit skill authoring standards                       | Rubrics and graders make recommendations testable.                             | Reuse rubric/grader thinking for execution results and sandbox choices.                                   |

## Current Overlap

PopKit already has meaningful pieces:

- Worktree commands for local branch isolation.
- Power Mode protocols for multi-agent objectives and coordination.
- `pop-sandbox` for E2B-backed sandbox operations.
- Skill authoring guidance that expects rubrics, graders, and explicit output contracts.

The gap is not another sandbox provider. The gap is one result artifact that
connects these pieces after each lane runs.

## Contract

The execution spine starts with `ExecutionLaneResult`:

- `objective`: the user-facing job the lane attempted.
- `sandboxBackend`: `none`, `local-worktree`, `e2b`, `vercel-sandbox`, or `cloudflare-sandbox`.
- `status`: `planned`, `running`, `succeeded`, `failed`, `blocked`, or `canceled`.
- `branch`, `worktreePath`, `logPath`, and `providerRunId`: traceability.
- `commits` and `artifacts`: reviewable outputs.
- `validation`: tests, evals, reviews, and smoke checks.
- `summary` and `nextAction`: handoff-ready decision text.

That contract is implemented in
`packages/popkit-core/power-mode/execution_spine.py` and mirrored by
`packages/popkit-core/output-styles/schemas/execution-lane-result.schema.json`.

## Provider Posture

| Backend              | Use now? | Why                                                                 |
| -------------------- | -------- | ------------------------------------------------------------------- |
| `local-worktree`     | Yes      | Highest-control default for PopKit development and repo-local work. |
| `e2b`                | Yes      | Already present through `pop-sandbox`; keep it provider-contained.  |
| `vercel-sandbox`     | Watch    | Relevant if Vercel remains the production/deploy center.            |
| `cloudflare-sandbox` | Watch    | Relevant if ElShaddai shifts more execution to Cloudflare.          |
| `none`               | Yes      | Useful for research, planning, docs-only work, and blocked lanes.   |

Do not add a provider dependency until the result contract is being emitted
from real PopKit flows. Provider choice should be an adapter decision, not a
workflow rewrite.

## Adversarial Review

| Risk                                           | Objection                                                                 | Response                                                                                         |
| ---------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| This could become PopKit bloat.                | A new contract can become another artifact nobody reads.                  | Keep it one dataclass, one schema, and one score gate. Delete it if workflows do not emit it.    |
| Provider enums can pretend integrations exist. | Listing Vercel and Cloudflare could imply supported adapters prematurely. | The enum records candidate backends only; no package or runtime dependency is added here.        |
| A local score is not a real eval suite.        | `score_execution_lane_result` is weaker than Evalite-style examples.      | Correct. It is a pre-Evalite quality gate so PopKit can measure output shape before model evals. |
| Sandcastle may be simpler than PopKit.         | Sandcastle's narrow scope can deliver more bang for the buck.             | PopKit should copy the narrow execution artifact, not the whole product boundary.                |

## Priority

| Priority | Keep / Try / Avoid | Decision                                                                              |
| -------- | ------------------ | ------------------------------------------------------------------------------------- |
| P0       | Keep               | Use `ExecutionLaneResult` as the shared handoff artifact for execution lanes.         |
| P0       | Keep               | Keep local worktrees as the default PopKit sandbox for repo work.                     |
| P1       | Try                | Emit execution results from Power Mode and plan execution flows.                      |
| P1       | Try                | Add Evalite-style examples after PopKit has real result fixtures.                     |
| P2       | Watch              | Spike Vercel and Cloudflare sandbox adapters only after local/E2B flows emit results. |
| P3       | Avoid              | Rewriting PopKit around Sandcastle, Evalite, or any single hosted sandbox provider.   |

## Next Implementation Step

Wire the contract into the lane coordinator or plan executor so every lane
finishes with one `ExecutionLaneResult`. That gives PopKit the Sandcastle-style
trace, the Evalite-style measurement surface, and the small-skill discipline
without bloating the runtime.
