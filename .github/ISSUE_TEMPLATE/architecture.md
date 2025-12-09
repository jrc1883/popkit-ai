---
name: Architecture / Epic
about: Major architectural changes or multi-PR initiatives
title: "[Architecture] "
labels: architecture, epic
assignees: ''
---

## Priority & Phase

<!-- Epics are typically P1/P2 with phase:now or phase:next -->
**Priority:** `P0-critical` | `P1-high` | `P2-medium`
**Phase:** `phase:now` | `phase:next` | `phase:future`
**Milestone:** `v1.0.0` | `v2.0.0`

## Overview

High-level description of the architectural change or epic initiative.

## Problem Statement

What problem does this solve? Why is the current architecture insufficient?

## Goals

- Goal 1
- Goal 2
- Goal 3

## Non-Goals

What is explicitly out of scope?

- Non-goal 1
- Non-goal 2

## Proposed Architecture

### Current State

```
Describe or diagram current architecture
```

### Target State

```
Describe or diagram target architecture
```

### Migration Path

How do we get from current to target?

1. Phase 1: ...
2. Phase 2: ...
3. Phase 3: ...

## Components Affected

- [ ] Skills (`pop:*`)
- [ ] Agents (tier-1, tier-2, feature-workflow)
- [ ] Commands (`/popkit:*`)
- [ ] Hooks
- [ ] Output Styles
- [ ] Power Mode
- [ ] MCP Server Template
- [ ] Documentation

## Sub-Issues

This epic breaks down into:

- [ ] #issue - Description
- [ ] #issue - Description

## Acceptance Criteria

- [ ] Architecture documented
- [ ] Migration complete
- [ ] Tests passing
- [ ] Documentation updated
- [ ] No regressions

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Risk 1 | Medium | High | Mitigation approach |

## Related Issues

- #issue - relationship

---

## PopKit Guidance

<!-- This section helps Claude Code work on this epic effectively -->

### Workflow
- [x] **Brainstorm First** - Use `pop-brainstorming` skill before any implementation
- [x] **Plan Required** - Use `/popkit:write-plan` to create detailed implementation plan
- [ ] **PRD Generation** - Consider `/popkit:prd` for comprehensive requirements

### Development Phases
<!-- All phases typically apply to architecture changes -->
- [x] Discovery - Research existing patterns and constraints
- [x] Architecture - Design decisions and tradeoffs
- [x] Implementation - Incremental code changes
- [x] Testing - Comprehensive test coverage
- [x] Documentation - Architecture docs, README updates
- [x] Review - Multiple review checkpoints

### Suggested Agents
- Primary: `code-architect`, `refactoring-expert`
- Supporting: `migration-specialist`, `code-reviewer`, `documentation-maintainer`
- Quality: `test-writer-fixer`, `security-auditor`

### Quality Gates
<!-- All gates apply to architecture changes -->
- [x] TypeScript check (`tsc --noEmit`) after each phase
- [x] Build verification after each phase
- [x] Lint pass
- [x] Test pass with coverage threshold
- [x] Manual review checkpoint between phases
- [x] Architecture review before implementation

### Power Mode
- [x] **Recommended** - Multiple agents should work in parallel during implementation
- Phases that benefit from parallelization:
  - Implementation (different subsystems)
  - Testing (unit, integration, e2e)
  - Documentation (API docs, guides, examples)

### Estimated Complexity
- [x] Epic (multiple PRs, architectural changes)

### Rollback Strategy

If implementation causes issues:
- Checkpoint commits at each phase boundary
- Feature flags for gradual rollout (if applicable)
- Rollback commands documented for each phase

---

## Additional Context

Background, diagrams, research links, or prior art:
