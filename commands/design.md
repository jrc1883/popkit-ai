---
description: Design and requirements - brainstorming sessions and PRD generation
---

# /popkit:design - Design & Requirements

Refine ideas into detailed designs and generate product requirements documents.

## Usage

```
/popkit:design <subcommand> [topic]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `brainstorm` | Interactive design refinement (default) |
| `prd` | Generate Product Requirements Document |

---

## Subcommand: brainstorm (default)

Refine rough ideas into fully-formed designs through collaborative Socratic questioning.

```
/popkit:design [topic]
/popkit:design brainstorm [topic]
/popkit:design "user authentication"
/popkit:design brainstorm "real-time notifications"
```

### Process

Invokes the **pop-brainstorming** skill:

1. **Understand context** - Review project state, docs, recent commits
2. **Ask questions** - One at a time, prefer multiple choice
3. **Explore approaches** - Present 2-3 options with trade-offs
4. **Present design** - In 200-300 word sections, validate each
5. **Document** - Save to `docs/plans/YYYY-MM-DD-<topic>-design.md`
6. **Implementation** - Offer worktree setup and plan creation

### Example Session

```
/popkit:design user authentication

Claude: Let me check the current project state...

Found: Next.js 14, Supabase, no existing auth

First question: What type of authentication do you need?
1. Email/password only
2. OAuth providers (Google, GitHub, etc.)
3. Magic link (passwordless)
4. Multiple options for users

> 2

Which OAuth providers should we support initially?
1. Google only (fastest to implement)
2. Google + GitHub
3. All major providers (Google, GitHub, Apple, Microsoft)

> 2

Let me present the design in sections...

## Section 1: Architecture
We'll use NextAuth.js with Supabase adapter for session management...

Does this section look right so far?

> yes

## Section 2: Components...
```

### Output

Creates design document at `docs/plans/YYYY-MM-DD-<topic>-design.md`:

```markdown
# User Authentication Design

> Created: 2025-01-15 via /popkit:design

## Summary
OAuth authentication with Google and GitHub providers...

## Architecture
[Validated design sections]

## Components
[Component breakdown]

## Implementation Notes
[Technical decisions made during brainstorm]
```

### After Design Approval

Offers:
- Create worktree for implementation
- Generate implementation plan via `/popkit:plan write`
- Create GitHub issue from design

---

## Subcommand: prd

Generate a Product Requirements Document from a brainstorming session or feature description.

```
/popkit:design prd [topic]
/popkit:design prd "task management app"
/popkit:design prd --from design.md   # Generate from design doc
```

### Process

1. Run brainstorming session (if not provided)
2. Extract requirements
3. Structure as PRD
4. Save to `docs/prd/YYYY-MM-DD-<topic>.md`

### PRD Template

```markdown
# Product Requirements Document: [Product Name]

**Version:** 1.0
**Date:** YYYY-MM-DD
**Author:** [Name]

---

## Executive Summary

[2-3 sentences describing the product/feature]

## Problem Statement

### Current Pain Points
- [Pain point 1]
- [Pain point 2]

### Target Users
- [User persona 1]
- [User persona 2]

## Goals and Objectives

### Primary Goals
1. [Goal 1]
2. [Goal 2]

### Success Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| [Metric] | [Value] | [How measured] |

## Requirements

### Functional Requirements

#### Must Have (P0)
- [ ] [Requirement 1]
- [ ] [Requirement 2]

#### Should Have (P1)
- [ ] [Requirement 3]

#### Nice to Have (P2)
- [ ] [Requirement 4]

### Non-Functional Requirements

- **Performance:** [Requirements]
- **Security:** [Requirements]
- **Accessibility:** [Requirements]
- **Scalability:** [Requirements]

## User Stories

### Epic: [Epic Name]

**Story 1:** As a [user], I want to [action] so that [benefit]
- Acceptance Criteria:
  - [ ] [Criterion 1]
  - [ ] [Criterion 2]

## Technical Considerations

### Architecture
[High-level architecture decisions]

### Dependencies
- [Dependency 1]
- [Dependency 2]

### Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk] | [Impact] | [Mitigation] |

## Timeline

### Phase 1: MVP
- Deliverables: [List]

### Phase 2: Enhancement
- Deliverables: [List]

## Appendix

### Glossary
- **Term:** Definition

### References
- [Reference 1]
```

### Example

```
/popkit:design prd task management app

Starting brainstorming session...
[Interactive session to gather requirements]

Generating PRD...

PRD created: docs/prd/2025-01-15-task-management.md

Summary:
- 5 P0 requirements
- 8 P1 requirements
- 3 P2 requirements
- 12 user stories

Would you like to:
1. Review and edit the PRD
2. Generate implementation plan
3. Create GitHub issues from requirements
```

---

## Examples

```bash
# Start brainstorming session
/popkit:design
/popkit:design brainstorm
/popkit:design "real-time notifications"

# Generate PRD
/popkit:design prd "task management"
/popkit:design prd --from docs/plans/auth-design.md
```

---

## Integration with Other Commands

| After Design | Next Step |
|--------------|-----------|
| Design approved | `/popkit:plan write` - Create implementation plan |
| PRD complete | `/popkit:issue create` - Create issues from requirements |
| Ready to start | `/popkit:worktree create` - Create isolated workspace |

---

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Brainstorming Skill | `skills/pop-brainstorming/SKILL.md` |
| Design Documents | `docs/plans/YYYY-MM-DD-<topic>-design.md` |
| PRD Documents | `docs/prd/YYYY-MM-DD-<topic>.md` |
| Plan Generation | `/popkit:plan write` |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:plan` | Create implementation plans |
| `/popkit:issue create` | Create issues from requirements |
| `/popkit:worktree create` | Create isolated workspace |
