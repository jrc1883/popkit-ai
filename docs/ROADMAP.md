# PopKit Roadmap

**Last Updated**: 2026-02-06
**Current Version**: 1.0.0-beta.7
**Claude Code Compatibility**: 2.1.33+

---

## Overview

This roadmap consolidates all active development priorities into a single source of truth. Issues marked with PR references will auto-close on merge.

---

## Phase 1: Foundation Hardening (Current)

Priority: Close pending PRs, stabilize core, update to Claude Code 2.1.33.

### In Progress (PRs Open)

| Issue | PR   | Title                                          | Status     |
| ----- | ---- | ---------------------------------------------- | ---------- |
| #65   | #232 | Interactive project init questions             | CI running |
| #10   | #233 | Agent routing accuracy (file + error patterns) | CI running |
| #72   | #234 | Frontend design integration strategy           | CI running |
| #100  | #235 | Code commenting standards v1.0                 | CI running |
| --    | #236 | Claude Code 2.1.7-2.1.33 version audit         | CI running |

### Ready to Merge (Dependabot)

| PR   | Title                                                  | CI Status |
| ---- | ------------------------------------------------------ | --------- |
| #222 | Bump @typescript-eslint/eslint-plugin 8.53.0 to 8.54.0 | Passed    |
| #223 | Bump @astrojs/starlight 0.37.4 to 0.37.5               | Passed    |
| #224 | Bump astro 5.16.15 to 5.17.1                           | Pending   |

---

## Phase 2: Claude Code 2.1.33 Integration (Next)

Priority: Leverage new Claude Code features to enhance PopKit's capabilities.

### Critical Updates

| Priority | Feature                       | Claude Code Version | Effort | Description                                                                                   |
| -------- | ----------------------------- | ------------------- | ------ | --------------------------------------------------------------------------------------------- |
| P0       | PreToolUse additionalContext  | 2.1.9               | Medium | Update `pre-tool-use.py` to inject safety warnings and agent suggestions into model reasoning |
| P0       | Setup Hook Event              | 2.1.10              | Medium | Add `Setup` hook for `--init`/`--maintenance` flags, integrate with `pop-project-init`        |
| P0       | Agent Memory Frontmatter      | 2.1.33              | Small  | Add `memory: user\|project\|local` to all 22 AGENT.md files                                   |
| P0       | Task(agent_type) Restrictions | 2.1.33              | Small  | Add sub-agent type restrictions to agent frontmatter                                          |
| P1       | TeammateIdle Hook             | 2.1.33              | Medium | Add hook handler for idle teammate agents                                                     |
| P1       | TaskCompleted Hook            | 2.1.33              | Medium | Add hook handler for task completion events                                                   |
| P1       | Command Argument Syntax       | 2.1.19              | Small  | Audit commands for `$ARGUMENTS.0` → `$ARGUMENTS[0]`                                           |

### Strategic Assessments

| Priority | Topic                          | Related Issues | Description                                                                                  |
| -------- | ------------------------------ | -------------- | -------------------------------------------------------------------------------------------- |
| P1       | Power Mode vs Agent Teams      | #84            | Evaluate native Agent Teams (2.1.32) overlap with Power Mode. Document differentiators.      |
| P1       | Knowledge Sync vs Agent Memory | --             | Evaluate native Agent Memory (2.1.32) overlap with `knowledge-sync.py`. Plan simplification. |
| P2       | Native Task System Integration | --             | Evaluate native task management (2.1.16) overlap with PopKit workflow tracking.              |

---

## Phase 3: Quality & Validation (Q1 2026)

Priority: Consolidation of testing and quality issues.

### Consolidated Issues

| Issue | Title                               | Status | Notes                                                                  |
| ----- | ----------------------------------- | ------ | ---------------------------------------------------------------------- |
| #11   | Cross-Plugin Integration Testing    | Open   | Consolidate with #18 into v1.0 Validation Checklist                    |
| #18   | User Acceptance Testing (UAT)       | Open   | Consolidate with #11 into v1.0 Validation Checklist                    |
| #50   | Quality Improvements Roadmap        | Open   | Meta-tracking issue, update with current priorities                    |
| #84   | Vibe-coded benchmarks for ambiguity | Open   | Benchmark design doc exists on `docs/issue-81-benchmark-design` branch |

### Action Items

1. **Consolidate #11 + #18** into a single "v1.0 Validation Checklist" issue
2. **Update #50** to reference this roadmap
3. **Merge benchmark design** from `docs/issue-81-benchmark-design` branch

---

## Phase 4: User Experience & Deployment (Q1-Q2 2026)

Priority: Improve onboarding and deployment story.

### Consolidated Issues

| Issue | Title                                 | Status | Notes                                 |
| ----- | ------------------------------------- | ------ | ------------------------------------- |
| #49   | Onboarding & Deployment Strategy      | Open   | Consolidate with #43                  |
| #43   | Unify account management              | Open   | Cloud-dependent, consolidate with #49 |
| #63   | Deploy Command Epic                   | Open   | Large epic, needs breakdown           |
| #218  | Hybrid PopKit/feature-dev integration | Open   | Architecture exploration              |

### Action Items

1. **Consolidate #43 + #49** into a single "User Onboarding & Account" issue
2. **Break down #63** into smaller, actionable sub-issues
3. **Resolve #218** with architecture decision

---

## Phase 5: Cloud & Integration (Q2 2026)

Priority: Features requiring cloud infrastructure. Deferred until cloud is available.

### Cloud-Dependent Issues

| Issue | Title                                  | Status | Notes                              |
| ----- | -------------------------------------- | ------ | ---------------------------------- |
| #45   | Capture reasoning tokens in recordings | Open   | Requires cloud storage             |
| #47   | Slack Integration                      | Open   | Low priority, external integration |
| #52   | Workspaces multi-project support       | Open   | Investigation needed               |
| #67   | Cache Management System                | Open   | Requires cloud caching             |
| #68   | Agent Expertise System                 | Open   | Requires cloud tracking            |

---

## Issue Summary

| Category                  | Count   | Issues                         |
| ------------------------- | ------- | ------------------------------ |
| **Closing via PRs**       | 4       | #10, #65, #72, #100            |
| **CC 2.1.33 Integration** | 7 tasks | (new work, no existing issues) |
| **Quality/Validation**    | 4       | #11, #18, #50, #84             |
| **UX/Deployment**         | 4       | #43, #49, #63, #218            |
| **Cloud-Deferred**        | 5       | #45, #47, #52, #67, #68        |
| **Total Open**            | 17      | After PR merges: 13            |

---

## Decision Log

| Date       | Decision                                                          | Rationale                                                                                                                                            |
| ---------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-02-06 | Closed 17 stale/superseded issues                                 | Issue triage: superseded (#77, #92, #51), completed (#38, #81), stale (#27, #28, #46, #102, #64, #53), cloud-deferred (#76, #78, #79, #83, #94, #95) |
| 2026-02-06 | Use official `frontend-design` plugin instead of custom UI agents | Anthropic has production-grade frontend-design skill; orchestrate rather than rebuild                                                                |
| 2026-02-06 | Commenting standards as guidelines, not enforced                  | v1.0 is documentation-only; enforcement tooling deferred to separate issue                                                                           |
| 2026-02-06 | Recommended CC version updated to 2.1.33+                         | 27 versions behind; critical features include Agent Teams, Agent Memory, new hooks                                                                   |
