---
name: Feature Request
about: Suggest a new feature or enhancement for popkit
title: "[Feature] "
labels: enhancement
assignees: ''
---

## Priority & Phase

<!-- Select ONE from each category -->
**Priority:** `P0-critical` | `P1-high` | `P2-medium` | `P3-low`
**Phase:** `phase:now` | `phase:next` | `phase:future`
**Milestone:** `v1.0.0` | `v2.0.0`

## Summary

A clear, concise description of the feature you'd like.

## Use Case

Why do you need this feature? What problem does it solve?

## Proposed Solution

If you have ideas on how this could be implemented:

## Alternatives Considered

Any alternative approaches you've thought about:

## Component

Which part of popkit does this relate to?
- [ ] Skills (`pop:*`)
- [ ] Agents (tier-1, tier-2, feature-workflow)
- [ ] Commands (`/popkit:*`)
- [ ] Hooks
- [ ] Output Styles
- [ ] Power Mode
- [ ] MCP Server Template
- [ ] Documentation
- [ ] Other

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Related Issues

- #issue_number - relationship

---

## PopKit Guidance

<!-- This section helps Claude Code work on this issue effectively -->

### Workflow
- [ ] **Brainstorm First** - Use `pop-brainstorming` skill before implementation
- [ ] **Plan Required** - Use `/popkit:write-plan` to create implementation plan
- [ ] **Direct Implementation** - Can proceed directly to code

### Development Phases
<!-- Check which phases apply to this feature -->
- [ ] Discovery - Research and context gathering
- [ ] Architecture - Design decisions needed
- [ ] Implementation - Code changes
- [ ] Testing - Test coverage required
- [ ] Documentation - Docs updates needed
- [ ] Review - Code review checkpoint

### Suggested Agents
<!-- Agents that should be involved -->
- Primary: `[agent-name]`
- Supporting: `[agent-name]`, `[agent-name]`

### Quality Gates
<!-- Validation required between phases -->
- [ ] TypeScript check (`tsc --noEmit`)
- [ ] Build verification
- [ ] Lint pass
- [ ] Test pass
- [ ] Manual review checkpoint

### Power Mode
- [ ] **Recommended** - Multiple agents should work in parallel
- [ ] **Optional** - Can benefit from coordination
- [ ] **Not Needed** - Sequential work is fine

### Estimated Complexity
- [ ] Small (1-2 files, < 100 lines)
- [ ] Medium (3-5 files, 100-500 lines)
- [ ] Large (6+ files, 500+ lines)
- [ ] Epic (multiple PRs, architectural changes)

---

## Additional Context

Any other context, screenshots, or examples:
