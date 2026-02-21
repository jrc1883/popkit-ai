---
title: Skills Reference
description: Complete reference for all 44 PopKit skills
---

# Skills Reference

PopKit provides 44 reusable skills across 4 plugins. Skills provide specialized automation for common development tasks.

## Invocation Modes

PopKit intentionally exposes skills in both direct and orchestrated forms:

| Mode                    | Typical syntax                        | Use case                |
| ----------------------- | ------------------------------------- | ----------------------- |
| Workflow command        | `/popkit-<plugin>:<command>`          | Daily/default usage     |
| Direct skill invocation | `/pop-...` or `/skill invoke pop-...` | Advanced/targeted usage |

Examples:

- `/popkit-dev:next` wraps `pop-next-action` with command-level parsing and formatted output.
- `/popkit-ops:assess security` routes into the `pop-assessment-security` skill.

Note: depending on client/version, you may see direct-skill entries as bare `/pop-*` aliases.

## popkit-core (15 skills)

Foundation skills for project management, embedding, and plugin operations.

### pop-analyze-project

**Description:** Comprehensive codebase analysis discovering architecture, patterns, dependencies, testing coverage, and improvement opportunities.

**Use when:** Starting work on an unfamiliar project or needing to understand a codebase.

```bash
/popkit-core:pop-analyze-project
```

---

### pop-auto-docs

**Description:** Generate comprehensive documentation from codebase analysis - creates README sections, API docs, migration guides, and examples.

```bash
/popkit-core:pop-auto-docs
```

---

### pop-bug-reporter

**Description:** Capture bug context, generate reports, and optionally create GitHub issues or share patterns.

```bash
/popkit-core:pop-bug-reporter
```

---

### pop-cloud-signup

**Description:** Create PopKit Cloud account, generate API key, and configure local connection.

```bash
/popkit-core:pop-cloud-signup
```

---

### pop-dashboard

**Description:** Multi-project dashboard showing health scores, recent activity, and quick actions across all registered projects.

**Use when:** Switching between projects, checking overall status, or managing project registry.

```bash
/popkit-core:pop-dashboard
```

---

### pop-doc-sync

**Description:** Synchronize documentation with codebase - updates AUTO-GEN sections in CLAUDE.md, validates cross-references, and reports stale documentation.

```bash
/popkit-core:pop-doc-sync
```

---

### pop-embed-content

**Description:** Manage project embeddings - embed skills, agents, commands, and MCP tools for semantic discovery. Handles rate limiting, incremental updates, and status reporting.

```bash
/popkit-core:pop-embed-content
```

---

### pop-embed-project

**Description:** Embed project-local skills, agents, and commands for semantic search. Use after creating items manually or to update embeddings.

```bash
/popkit-core:pop-embed-project
```

---

### pop-mcp-generator

**Description:** Generate custom MCP server with semantic search, project-aware tools, and health monitoring capabilities.

**Use when:** Setting up project-specific development tools or after analyzing a codebase.

```bash
/popkit-core:pop-mcp-generator
```

---

### pop-plugin-test

**Description:** Run comprehensive tests on plugin components. Validates hooks, agents, skills, and plugin structure across all PopKit packages.

```bash
/popkit-core:pop-plugin-test
```

---

### pop-power-mode

**Description:** Multi-agent orchestration system using Claude Code's native background agents for true parallel collaboration. Enables shared context, sync barriers between phases, and coordinator oversight.

**Use when:** Complex tasks benefiting from parallel execution (epics, large refactors, multi-phase features).

```bash
/popkit-core:pop-power-mode
```

---

### pop-project-init

**Description:** Initialize .claude/ structure and add PopKit section to CLAUDE.md without overwriting. Detects conflicts, creates config, prompts for Power Mode.

```bash
/popkit-core:pop-project-init
```

---

### pop-project-reference

**Description:** Load cross-project context in monorepos. Lists available workspace projects or loads specific project context. Supports pnpm, npm/yarn, Lerna workspaces.

```bash
/popkit-core:pop-project-reference
```

---

### pop-project-templates

**Description:** Curated project templates that guide feature-dev Phase 3 questions with research-backed technology choices. Provides standardized options for common project types (SaaS API, ML Service, CLI Tool, Full-Stack).

```bash
/popkit-core:pop-project-templates
```

---

### pop-skill-generator

**Description:** Generate custom skills based on codebase patterns, common workflows, and team conventions discovered during analysis.

**Use when:** You want to capture project-specific patterns as reusable skills.

```bash
/popkit-core:pop-skill-generator
```

---

### pop-validation-engine

**Description:** Validate plugin integrity and offer safe auto-fixes for common issues - checks agents, skills, hooks, routing config, and plugin structure.

```bash
/popkit-core:pop-validation-engine
```

---

## popkit-dev (16 skills)

Development workflow skills for git operations, routines, and feature development.

### pop-brainstorming

**Description:** Collaborative design refinement that transforms rough ideas into fully-formed specifications through Socratic questioning. Explores alternatives, validates incrementally, and presents designs in digestible chunks.

**Use when:** Before writing code when requirements are unclear or multiple approaches exist.

```bash
/popkit-dev:pop-brainstorming
```

---

### pop-changelog-automation

**Description:** Enhanced changelog generation with semantic versioning, auto-categorization, and release notes. Parses conventional commits, determines version bump, categorizes changes by type.

**Use when:** Before releases or on PR merge to automate version management.

```bash
/popkit-dev:pop-changelog-automation
```

---

### pop-complexity-analyzer

**Description:** Analyzes task/feature complexity (1-10) and recommends subtask breakdown for planning and prioritization. Provides actionable recommendations for agent selection and risk assessment.

```bash
/popkit-dev:pop-complexity-analyzer
```

---

### pop-context-restore

**Description:** Fully restore working context from a previous session - loads STATUS.json, reads key files, rebuilds mental model of current work state.

```bash
/popkit-dev:pop-context-restore
```

---

### pop-executing-plans

**Description:** Controlled batch execution of implementation plans with review checkpoints between phases. Loads plan, critically reviews for issues, executes tasks in batches, then pauses for feedback.

**Use when:** You have a complete implementation plan and want structured execution with quality gates.

```bash
/popkit-dev:pop-executing-plans
```

---

### pop-finish-branch

**Description:** Guide completion of development work by presenting structured options: merge locally, create PR, keep as-is, or discard.

**Use when:** Implementation is complete, all tests pass, and you need to decide how to integrate the work.

```bash
/popkit-dev:pop-finish-branch
```

---

### pop-morning

**Description:** Start-of-day setup routine. Calculates Ready to Code Score (0-100) based on session restoration, service health, dependency updates, branch sync, PR reviews, and issue triage.

```bash
/popkit-dev:pop-morning
```

---

### pop-next-action

**Description:** Context-aware recommendation engine that analyzes git status, TypeScript errors, GitHub issues, and technical debt to suggest prioritized next actions.

**Use when:** Unsure what to work on next, starting a session, or feeling stuck.

```bash
/popkit-dev:pop-next-action
```

---

### pop-nightly

**Description:** End-of-day cleanup routine. Calculates Sleep Score (0-100) based on uncommitted work, branch cleanup, issue updates, CI status, and service shutdown.

```bash
/popkit-dev:pop-nightly
```

---

### pop-routine-measure

**Description:** Display routine measurement dashboard with metrics, costs, trends, and visualization.

```bash
/popkit-dev:pop-routine-measure
```

---

### pop-routine-optimized

**Description:** Token-optimized morning/nightly routine using caching and selective execution.

```bash
/popkit-dev:pop-routine-optimized
```

---

### pop-session-capture

**Description:** Save complete session state to STATUS.json for seamless continuation across conversations. Captures git context, in-progress tasks, service status, focus area, and next actions.

**Use when:** End of work sessions, before context limits, or when switching tasks.

```bash
/popkit-dev:pop-session-capture
```

---

### pop-session-resume

**Description:** Restore context from STATUS.json at session start. Loads previous state, displays session type, shows what to continue working on.

```bash
/popkit-dev:pop-session-resume
```

---

### pop-worktree-manager

**Description:** Python-based git worktree manager with 8 operations: list, create, remove, switch, update-all, prune, init, analyze. Handles cross-platform paths and STATUS.json integration.

```bash
/popkit-dev:pop-worktree-manager
```

---

### pop-worktrees

**Description:** Create isolated git worktrees with smart directory selection and safety verification. Verifies .gitignore, runs project setup, confirms clean test baseline.

**Use when:** Starting feature work that needs isolation from current workspace.

```bash
/popkit-dev:pop-worktrees
```

---

### pop-writing-plans

**Description:** Create comprehensive implementation plans with exact file paths, complete code examples, and verification steps for engineers with zero codebase context.

**Use when:** After brainstorming/design is complete when handing off to another developer or planning complex multi-step work.

```bash
/popkit-dev:pop-writing-plans
```

---

## popkit-ops (8 skills)

Operations and quality skills for assessments, testing, debugging, and benchmarking.

### pop-assessment-anthropic

**Description:** Validates PopKit compliance with Claude Code patterns using concrete standards and automated checks.

```bash
/popkit-ops:pop-assessment-anthropic
```

---

### pop-assessment-architecture

**Description:** Validates code quality using concrete metrics for DRY, coupling, cohesion, and architectural patterns.

```bash
/popkit-ops:pop-assessment-architecture
```

---

### pop-assessment-performance

**Description:** Evaluates efficiency using concrete metrics for context usage, token consumption, and lazy loading validation.

```bash
/popkit-ops:pop-assessment-performance
```

---

### pop-assessment-security

**Description:** Validates security posture using concrete vulnerability patterns, automated secret scanning, and OWASP-aligned checklists.

```bash
/popkit-ops:pop-assessment-security
```

---

### pop-assessment-ux

**Description:** Evaluates user experience using concrete heuristics for command naming, error messages, and interaction patterns.

```bash
/popkit-ops:pop-assessment-ux
```

---

### pop-benchmark-runner

**Description:** Orchestrates benchmark execution comparing PopKit vs baseline Claude Code.

```bash
/popkit-ops:pop-benchmark-runner
```

---

### pop-code-review

**Description:** Confidence-based code review that filters issues to 80+ threshold, eliminating false positives. Reviews implementation against plan or requirements for bugs, quality issues, and project conventions.

**Use when:** After completing major features, before merging to main, or after each task in multi-step workflows.

```bash
/popkit-ops:pop-code-review
```

---

### pop-systematic-debugging

**Description:** Four-phase debugging: root cause, patterns, hypothesis, implement. For complex bugs, test failures, and multi-component issues.

```bash
/popkit-ops:pop-systematic-debugging
```

---

## popkit-research (3 skills)

Knowledge management skills for research capture and retrieval.

### pop-knowledge-lookup

**Description:** Query cached external documentation and blog content for authoritative, up-to-date information. Sources include Claude Code docs, engineering blog, and configured knowledge bases with 24-hour TTL caching.

**Use when:** You need current information about Claude Code features, hooks, or best practices.

```bash
/popkit-research:pop-knowledge-lookup
```

---

### pop-research-capture

**Description:** Capture research insights, decisions, and learnings during development. Prompts for context and rationale, stores with embeddings for later semantic retrieval.

**Use when:** After completing spikes, making architectural decisions, or discovering important patterns.

```bash
/popkit-research:pop-research-capture
```

---

### pop-research-merge

**Description:** Process research branches from Claude Code Web sessions - merges content, moves docs to .claude/research/, and creates GitHub issues.

**Use when:** `/popkit-dev:next` detects research branches or when manually processing research from mobile sessions.

```bash
/popkit-research:pop-research-merge
```

---

## Skill Conventions

### Context Modes

Skills declare their execution context:

- **Default context**: Runs in the main conversation (most skills)
- **Forked context** (`context: fork`): Runs in an isolated context to reduce token overhead. Used for expensive operations like embeddings and web research.

### The PopKit Way

All skills end with `AskUserQuestion` to maintain workflow control. This ensures:

- Context-aware next action options
- Continuous workflow engagement
- Intentional user decisions at every step

## Next Steps

- Learn about [Agents Reference](/reference/agents/)
- Explore [Commands Reference](/reference/commands/)
- Read the [Getting Started Guide](/guides/getting-started/)
