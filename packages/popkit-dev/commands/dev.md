---
description: 'work #N | brainstorm | plan | execute | prd | suite | "description" [--mode quick|full] [--provider auto|popkit|feature-dev] [-T, --power]'
argument-hint: "[subcommand|description] [flags]"
---

# /popkit-dev:dev - Development Workflows

Unified entry point for development workflows.

**Intelligent routing:** Auto-selects quick (5-step) or full (7-phase) workflow.

## Usage

```bash
/popkit-dev:dev "add dark mode"           # Auto-routed
/popkit-dev:dev work #123                 # Issue-driven
/popkit-dev:dev brainstorm               # Idea refinement
/popkit-dev:dev plan "feature"           # Write plan
/popkit-dev:dev execute                  # Run plan
/popkit-dev:dev "task" --mode quick      # Override
/popkit-dev:dev "task" --provider feature-dev
```

## Subcommands

| Subcommand   | Description          | Use Case             |
| ------------ | -------------------- | -------------------- |
| `work #N`    | Issue-driven dev     | GitHub issue         |
| `brainstorm` | Socratic questioning | Unclear requirements |
| `plan`       | Implementation plan  | Planning             |
| `execute`    | Execute plan         | Implementation       |
| `prd`        | Generate PRD         | Requirements         |
| `suite`      | Full doc suite       | Complete docs        |

## Modes

| Mode    | When          | Process                                                                                |
| ------- | ------------- | -------------------------------------------------------------------------------------- |
| `quick` | Simple, clear | 5 steps: Understand → Find → Fix → Verify → Commit                                     |
| `full`  | Complex       | 7 phases: Discovery → Exploration → Questions → Architecture → Impl → Review → Summary |

**Override:** `--mode quick|full`

## Flags

| Flag               | Short | Description                     |
| ------------------ | ----- | ------------------------------- |
| `--mode`           |       | `quick` or `full`               |
| `--provider`       |       | `auto`, `popkit`, `feature-dev` |
| `--thinking`       | `-T`  | Extended thinking               |
| `--think-budget N` |       | Token budget (10000)            |
| `--from FILE`      |       | From design/plan                |
| `--issue N`        |       | Reference issue                 |
| `--power`          | `-p`  | Power Mode                      |
| `--solo`           | `-s`  | Sequential                      |

---

## Orchestrator

**Quick:** Simple, greenfield, few files
**Full:** Complex, architecture, multi-domain

Details: `commands/examples/dev/routing-examples.md`

### Provider Strategy (Issue #218)

`--provider auto` (default) uses first-principles resolution:

1. Choose the simplest provider that satisfies required capabilities.
2. Prefer official upstream for commodity flows.
3. Require PopKit when workflow needs PopKit-only orchestration.
4. Reassess when failure rate or cycle time regresses.

Use explicit overrides for experimentation:

- `--provider popkit` - force native PopKit orchestration
- `--provider feature-dev` - force upstream workflow (fallback to PopKit if unavailable)

Implementation references:

- `packages/shared-py/popkit_shared/utils/dev_provider_resolver.py`
- `packages/shared-py/popkit_shared/utils/dev_workflow_router.py`

---

## Mode: full

7-phase workflow.

| Phase             | Goal            | Agent/Skill                            |
| ----------------- | --------------- | -------------------------------------- |
| 1. Discovery      | What to build   | pop-brainstorming                      |
| 2. Exploration    | Understand code | code-explorer                          |
| 3. Questions      | Clarify         | pop-project-templates                  |
| 4. Architecture   | Design          | code-architect                         |
| 5. Implementation | Build           | pop-writing-plans, pop-executing-plans |
| 6. Review         | Quality         | code-reviewer                          |
| 7. Summary        | Complete        | pop-finish-branch                      |

Details: `commands/examples/dev/full-mode-walkthrough.md`

---

## Mode: work

Issue-driven with Power Mode.

```bash
/popkit-dev:dev work #57 -p
```

### Process

1. Fetch issue
2. Parse PopKit Guidance
3. Determine mode
4. Execute phases
5. Complete (pop-finish-branch)
6. Next actions (AskUserQuestion)

**CRITICAL:** Always present next actions (Issue #118)

Details: `commands/examples/dev/work-mode-completion.md`

---

## Mode: brainstorm

Socratic design refinement via `pop-brainstorming`.

Details: `commands/examples/dev/brainstorm-session.md`

---

## Mode: plan

Implementation plans via `pop-writing-plans`.

Details: `commands/examples/dev/plan-structure.md`

---

## Mode: execute

Batch execution via `pop-executing-plans`.

```bash
/popkit-dev:dev execute --batch-size 5 --start-at 4
```

Details: `commands/examples/dev/execute-batch-flow.md`

---

## Mode: quick

5-step minimal ceremony.

```bash
/popkit-dev:dev "fix timezone bug"
```

### Quality Checks

| Task Type          | Checks                 |
| ------------------ | ---------------------- |
| Animations/Physics | Energy, collision      |
| UI Components      | A11y, responsive       |
| API Endpoints      | Validation, security   |
| Data Processing    | Edge cases, perf       |
| Bug Fixes          | Regression, root cause |

Details: `commands/examples/dev/quick-mode-examples.md`

---

## Mode: prd

Generate PRD with Summary, Problem, Goals, Requirements (P0/P1/P2), Stories, Tech, Risks.

---

## Mode: suite

Generate complete docs:

| Document               | Location             | Purpose      |
| ---------------------- | -------------------- | ------------ |
| `problem_statement.md` | `docs/discovery/`    | Problem      |
| `PRD.md`               | `docs/prd/`          | Requirements |
| `user_stories.md`      | `docs/prd/`          | Stories      |
| `ARCHITECTURE.md`      | `docs/architecture/` | Design       |
| `TECHNICAL_SPEC.md`    | `docs/architecture/` | Tech details |

---

## Executables

```bash
# Full
Use Task tool (Explore|Plan|code-reviewer)
git worktree add .worktrees/feature-<name> -b feature/<name>

# Work
gh issue view <number> --json number,title,body,labels,state,author

# Skills
Use Skill tool (pop-brainstorming|pop-writing-plans|pop-executing-plans)
```

---

## Migration

| Old                   | New                          |
| --------------------- | ---------------------------- |
| `/popkit:design`      | `/popkit-dev:dev brainstorm` |
| `/popkit:plan`        | `/popkit-dev:dev plan`       |
| `/popkit:feature-dev` | `/popkit-dev:dev full`       |

---

## Related

- `/popkit-dev:git` - Version control
- `/popkit-dev:issue` - Issue management
- `/popkit-dev:worktree` - Worktree management
- `/popkit-core:power` - Multi-agent orchestration
