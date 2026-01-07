---
name: Research / Investigation
about: Research tasks, spikes, or investigation work
title: "[Research] "
labels: ''
assignees: ''

---

## Priority & Phase

<!-- Research is typically phase:now or phase:next -->
**Priority:** `P1-high` | `P2-medium` | `P3-low`
**Phase:** `phase:now` | `phase:next` | `phase:future`
**Milestone:** `v1.0.0` | `v2.0.0`

## Research Question

What are we trying to learn or understand?

## Background

Why is this research needed? What decision does it inform?

## Scope

### In Scope

- Area to investigate 1
- Area to investigate 2

### Out of Scope

- Not investigating X
- Not investigating Y

## Research Approach

How will we investigate?

1. Step 1
2. Step 2
3. Step 3

## Expected Deliverables

- [ ] Summary document
- [ ] Proof of concept (if applicable)
- [ ] Recommendation with tradeoffs
- [ ] Follow-up issues created

## Time Box

This research should be completed within: [X hours/days]

## Related Issues

- #issue - this research informs

---

## PopKit Guidance

<!-- This section helps Claude Code conduct this research effectively -->

### Workflow
- [ ] **Exploration Mode** - Use `code-explorer` agent for codebase analysis
- [ ] **Web Research** - Use WebSearch/WebFetch for external research
- [ ] **Document Findings** - Create summary in appropriate location

### Research Phases
- [x] Discovery - Gather information
- [ ] Analysis - Synthesize findings
- [ ] Recommendation - Propose path forward

### Suggested Agents
- Primary: `researcher`, `code-explorer`
- Supporting: `documentation-maintainer`

### Output Location

Where should findings be documented?
- [ ] `docs/research/[topic].md`
- [ ] Comment on this issue
- [ ] New architecture issue
- [ ] CLAUDE.md update

### Quality Gates
- [ ] Research question answered
- [ ] Sources cited
- [ ] Tradeoffs documented
- [ ] Follow-up issues created

### Power Mode
- [ ] **Not Needed** - Research is typically sequential exploration

---

## Notes

Space for ongoing research notes:
