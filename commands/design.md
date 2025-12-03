---
description: Design and requirements - brainstorming sessions and PRD generation
---

# /popkit:design - Design & Requirements

Refine ideas into detailed designs and generate product requirements documents.

## Usage

```
/popkit:design <subcommand> [topic] [flags]
```

## Flags

| Flag | Description |
|------|-------------|
| `-T`, `--thinking` | Enable extended thinking mode for deeper analysis |
| `--no-thinking` | Disable extended thinking (use default) |
| `--think-budget N` | Set thinking token budget (default: 10000) |
| `--suite` | Generate full document suite (PRD, user stories, architecture, tech spec) |
| `--from FILE` | Generate from existing design document |

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `brainstorm` | Interactive design refinement (default) |
| `prd` | Generate Product Requirements Document |
| `suite` | Generate complete document suite (Issue #11) |

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

## Subcommand: suite (Issue #11)

Generate a complete document suite for comprehensive feature development. This supports the Unified Orchestration System (Issue #11) by producing all artifacts needed for the 10-phase development pipeline.

```
/popkit:design suite [topic]
/popkit:design prd [topic] --suite
/popkit:design suite "user authentication" -T
```

### Generated Documents

| Document | Location | Purpose |
|----------|----------|---------|
| `problem_statement.md` | `docs/discovery/` | Discovery phase - problem definition |
| `PRD.md` | `docs/prd/` | Product requirements document |
| `user_stories.md` | `docs/prd/` | User stories with acceptance criteria |
| `ARCHITECTURE.md` | `docs/architecture/` | High-level architecture decisions |
| `TECHNICAL_SPEC.md` | `docs/architecture/` | Detailed technical specification |

### Process

1. **Discovery Phase**
   - Run brainstorming session (or use existing design)
   - Extract problem statement and goals
   - Generate `problem_statement.md`

2. **Requirements Phase**
   - Structure requirements as PRD
   - Extract and organize user stories
   - Generate `PRD.md` and `user_stories.md`

3. **Architecture Phase**
   - Define high-level architecture
   - Document key decisions and trade-offs
   - Generate `ARCHITECTURE.md`

4. **Technical Design Phase**
   - Detail technical implementation
   - Specify APIs, data models, dependencies
   - Generate `TECHNICAL_SPEC.md`

### Document Templates

#### problem_statement.md

```markdown
# Problem Statement: [Topic]

**Date:** YYYY-MM-DD
**Author:** [Name]

---

## Executive Summary

[2-3 sentences describing the problem and proposed solution]

## Current State

### Pain Points
- [Pain point 1]
- [Pain point 2]

### Impact
[Description of current impact on users/business]

## Desired State

### Goals
1. [Goal 1]
2. [Goal 2]

### Success Criteria
- [Criterion 1]
- [Criterion 2]

## Scope

### In Scope
- [Item 1]
- [Item 2]

### Out of Scope
- [Item 1]
- [Item 2]

## Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| [Role] | [Name] | [Responsibility] |

## Constraints

- [Constraint 1]
- [Constraint 2]

## References

- [Reference 1]
```

#### user_stories.md

```markdown
# User Stories: [Topic]

**Date:** YYYY-MM-DD
**PRD Reference:** [Link to PRD]

---

## Epic 1: [Epic Name]

### Story 1.1: [Story Title]

**As a** [user role]
**I want to** [action/goal]
**So that** [benefit/value]

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

**Technical Notes:**
- [Note 1]

**Priority:** P0/P1/P2
**Story Points:** [N]

---

### Story 1.2: [Story Title]
[...]

## Epic 2: [Epic Name]
[...]

## Story Map

| Discovery | Architecture | Implementation | Testing | Release |
|-----------|--------------|----------------|---------|---------|
| Story 1.1 | Story 2.1    | Story 3.1      | Story 4.1 | Story 5.1 |
| Story 1.2 | Story 2.2    | Story 3.2      | Story 4.2 | Story 5.2 |

## Dependencies

```
Story 1.1 -> Story 2.1 -> Story 3.1
             Story 2.2 -> Story 3.2
```
```

#### ARCHITECTURE.md

```markdown
# Architecture: [Topic]

**Date:** YYYY-MM-DD
**PRD Reference:** [Link to PRD]
**Status:** Draft/Review/Approved

---

## Overview

[High-level description of the architecture]

## Goals

### Functional Goals
1. [Goal 1]
2. [Goal 2]

### Non-Functional Goals
- **Performance:** [Requirements]
- **Scalability:** [Requirements]
- **Security:** [Requirements]
- **Maintainability:** [Requirements]

## Architecture Diagram

```
[ASCII diagram or description]
```

## Components

### Component 1: [Name]

**Purpose:** [Description]
**Responsibilities:**
- [Responsibility 1]
- [Responsibility 2]

**Interfaces:**
- Input: [Description]
- Output: [Description]

### Component 2: [Name]
[...]

## Data Flow

1. [Step 1]
2. [Step 2]
3. [Step 3]

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Frontend | [Tech] | [Why] |
| Backend | [Tech] | [Why] |
| Database | [Tech] | [Why] |
| Infrastructure | [Tech] | [Why] |

## Key Decisions

### Decision 1: [Topic]

**Context:** [Background]
**Options Considered:**
1. [Option 1] - [Pros/Cons]
2. [Option 2] - [Pros/Cons]

**Decision:** [Chosen option]
**Rationale:** [Why this choice]
**Consequences:** [Impact of decision]

## Security Considerations

- [Consideration 1]
- [Consideration 2]

## Integration Points

| System | Integration Method | Data Exchanged |
|--------|-------------------|----------------|
| [System] | [API/Event/etc.] | [Description] |

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| [Risk] | High/Medium/Low | High/Medium/Low | [Strategy] |

## References

- [Reference 1]
```

#### TECHNICAL_SPEC.md

```markdown
# Technical Specification: [Topic]

**Date:** YYYY-MM-DD
**Architecture Reference:** [Link to ARCHITECTURE.md]
**Status:** Draft/Review/Approved

---

## Overview

[Detailed technical description]

## API Specification

### Endpoint 1: [Name]

**Method:** GET/POST/PUT/DELETE
**Path:** `/api/v1/[path]`
**Authentication:** Required/Optional

**Request:**
```json
{
  "field1": "type",
  "field2": "type"
}
```

**Response:**
```json
{
  "field1": "type",
  "field2": "type"
}
```

**Error Codes:**
| Code | Description |
|------|-------------|
| 400 | [Description] |
| 401 | [Description] |
| 404 | [Description] |

### Endpoint 2: [Name]
[...]

## Data Models

### Model 1: [Name]

```typescript
interface Model1 {
  id: string;
  field1: string;
  field2: number;
  createdAt: Date;
  updatedAt: Date;
}
```

**Validation Rules:**
- `field1`: Required, max 255 characters
- `field2`: Required, positive integer

### Model 2: [Name]
[...]

## Database Schema

```sql
CREATE TABLE table_name (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  field1 VARCHAR(255) NOT NULL,
  field2 INTEGER NOT NULL CHECK (field2 > 0),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_table_field1 ON table_name(field1);
```

## State Management

### State Shape

```typescript
interface AppState {
  feature: {
    items: Item[];
    loading: boolean;
    error: string | null;
  };
}
```

### Actions

| Action | Payload | Effect |
|--------|---------|--------|
| `FETCH_ITEMS` | none | Sets loading=true |
| `FETCH_ITEMS_SUCCESS` | `Item[]` | Sets items, loading=false |
| `FETCH_ITEMS_ERROR` | `string` | Sets error, loading=false |

## Error Handling

### Error Categories

| Category | HTTP Code | Handling |
|----------|-----------|----------|
| Validation | 400 | Show field errors |
| Authentication | 401 | Redirect to login |
| Authorization | 403 | Show permission denied |
| Not Found | 404 | Show not found page |
| Server Error | 500 | Show generic error, log details |

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": [
      {"field": "email", "message": "Invalid email format"}
    ]
  }
}
```

## Testing Strategy

### Unit Tests
- [Component/Function]: [What to test]
- [Component/Function]: [What to test]

### Integration Tests
- [Flow]: [What to test]
- [Flow]: [What to test]

### E2E Tests
- [Scenario]: [What to test]

## Performance Considerations

- [Consideration 1]
- [Consideration 2]

### Benchmarks

| Operation | Target | Measurement |
|-----------|--------|-------------|
| [Operation] | < 100ms | p95 latency |
| [Operation] | < 500ms | p99 latency |

## Deployment

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | Database connection string | - |
| `API_KEY` | Yes | External API key | - |

### Infrastructure Requirements

- [Requirement 1]
- [Requirement 2]

## Implementation Checklist

- [ ] Database migrations
- [ ] API endpoints
- [ ] Frontend components
- [ ] Unit tests
- [ ] Integration tests
- [ ] Documentation
- [ ] Deployment configuration

## References

- [Reference 1]
```

### Example

```
/popkit:design suite user authentication

Starting comprehensive document suite generation...

Phase 1: Discovery
[Interactive brainstorming to gather context]

Phase 2: Requirements
[Extracting and structuring requirements]

Phase 3: Architecture
[Defining high-level architecture]

Phase 4: Technical Design
[Detailing technical implementation]

Document Suite Generated:
├── docs/
│   ├── discovery/
│   │   └── 2025-01-15-user-authentication-problem.md
│   ├── prd/
│   │   ├── 2025-01-15-user-authentication-prd.md
│   │   └── 2025-01-15-user-authentication-stories.md
│   └── architecture/
│       ├── 2025-01-15-user-authentication-architecture.md
│       └── 2025-01-15-user-authentication-tech-spec.md

Summary:
- Problem statement documented
- 12 P0/P1/P2 requirements
- 15 user stories across 3 epics
- 5 key architecture decisions
- Full API specification (8 endpoints)

Next steps:
1. Review documents with stakeholders
2. Create GitHub issues from user stories
3. Generate implementation plan: /popkit:plan write
4. Set up worktree: /popkit:worktree create auth-feature
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

# Generate full document suite (Issue #11)
/popkit:design suite "user authentication"
/popkit:design prd "payment system" --suite
/popkit:design suite "notification system" -T  # With extended thinking
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
| User Stories | `docs/prd/YYYY-MM-DD-<topic>-stories.md` |
| Problem Statement | `docs/discovery/YYYY-MM-DD-<topic>-problem.md` |
| Architecture Docs | `docs/architecture/YYYY-MM-DD-<topic>-architecture.md` |
| Technical Specs | `docs/architecture/YYYY-MM-DD-<topic>-tech-spec.md` |
| Plan Generation | `/popkit:plan write` |
| Issue Workflow | `hooks/issue-workflow.py` (Phase transitions) |
| Quality Gates | `hooks/quality-gate.py` (Phase validation) |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:plan` | Create implementation plans |
| `/popkit:issue create` | Create issues from requirements |
| `/popkit:issue work` | Start issue-driven workflow with phase tracking |
| `/popkit:worktree create` | Create isolated workspace |
| `/popkit:power` | Multi-agent orchestration for complex work |
