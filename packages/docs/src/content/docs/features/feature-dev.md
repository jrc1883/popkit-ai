---
title: Feature Development
description: 7-phase guided feature development workflow
---

# Feature Development

PopKit's feature development workflow guides you through a structured 7-phase process from discovery to implementation.

## The 7 Phases

### Phase 1: Discovery

**Goal**: Understand the feature request

**Activities**:
- Parse feature description
- Identify key requirements
- List assumptions and constraints

**Output**: Feature brief document

### Phase 2: Exploration

**Goal**: Explore the codebase

**Activities**:
- Search for related code
- Identify integration points
- Review existing patterns

**Output**: Context map of relevant files

### Phase 3: Questions

**Goal**: Clarify ambiguities

**Activities**:
- Generate clarifying questions
- Identify edge cases
- Propose design alternatives

**Output**: Q&A document for user

### Phase 4: Architecture

**Goal**: Design the solution

**Activities**:
- Create technical design
- Plan file structure
- Identify dependencies

**Output**: Architecture document

### Phase 5: Implementation

**Goal**: Write the code

**Activities**:
- Create/modify files
- Implement features
- Add error handling

**Output**: Working code

### Phase 6: Review

**Goal**: Validate the implementation

**Activities**:
- Run tests
- Check edge cases
- Review code quality

**Output**: Test results and fixes

### Phase 7: Summary

**Goal**: Document the work

**Activities**:
- Summarize changes
- Document decisions
- List next steps

**Output**: Feature summary document

## Using the Workflow

### Basic Usage

```bash
/popkit-dev:dev "Add user authentication"
```

This starts the 7-phase workflow with interactive prompts at each phase.

### With Power Mode

```bash
/popkit-dev:dev "Add user authentication" --power
```

Enables multiple agents for faster exploration and implementation.

### Quick Mode

```bash
/popkit-dev:dev "Add user authentication" --mode quick
```

Skips exploratory phases for simple features.

## Phase Transitions

Between each phase, PopKit:

1. **Summarizes Progress**: What was accomplished
2. **Shows Next Phase**: What comes next
3. **Asks Permission**: User approves before continuing
4. **Preserves Context**: Maintains state across phases

## Workflow Control

### Skip Phases

```bash
# Skip to architecture phase
/popkit-dev:dev "Add auth" --start-phase architecture
```

### Pause and Resume

```bash
# Save state
/popkit-core:project capture

# Resume later
/popkit-core:project restore
```

### Customize Workflow

Create custom workflow templates in `.popkit/workflows/`.

## Best Practices

1. **Clear Descriptions**: Provide detailed feature descriptions
2. **Answer Questions**: Take time in Phase 3 to clarify
3. **Review Architecture**: Approve design before implementation
4. **Test Thoroughly**: Use Phase 6 to validate
5. **Document Decisions**: Phase 7 is critical for team knowledge

## Example Workflow

```bash
# Start feature development
/popkit-dev:dev "Implement OAuth2 authentication with Google provider"

# Phase 1: Discovery
# PopKit analyzes requirements
# [User reviews and approves]

# Phase 2: Exploration
# PopKit scans codebase for auth patterns
# [User reviews context map]

# Phase 3: Questions
# PopKit asks:
# - Which OAuth2 library should we use?
# - Should we support refresh tokens?
# - Where should we store tokens?
# [User answers questions]

# Phase 4: Architecture
# PopKit designs solution
# [User reviews and approves architecture]

# Phase 5: Implementation
# PopKit writes code
# [User reviews changes]

# Phase 6: Review
# PopKit runs tests, checks edge cases
# [User reviews test results]

# Phase 7: Summary
# PopKit generates summary document
# [User reviews and closes workflow]
```

## Next Steps

- Explore [Git Workflows](/features/git-workflows/)
- Learn about [Routines](/features/routines/)
- Understand [Power Mode](/features/power-mode/)
