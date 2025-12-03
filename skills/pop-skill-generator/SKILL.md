---
name: skill-generator
description: "Use when you want to capture project-specific patterns as reusable skills - generates custom skills based on codebase patterns, common workflows, and team conventions discovered during analysis. Creates skills for patterns, testing, deployment, debugging, and setup. Do NOT use for generic skills that would work across any project - those belong in popkit core, not project-specific generation."
---

# Skill Generator

## Overview

Create custom skills tailored to the specific project's patterns, workflows, and conventions. Skills become part of the project's .claude/skills/ directory.

**Core principle:** Capture project wisdom as reusable, teachable skills.

**Trigger:** `/generate-skills` command after project analysis

## What Gets Generated

```
.claude/skills/
├── [project]-patterns.md     # Project coding patterns
├── [project]-testing.md      # Testing conventions
├── [project]-deployment.md   # Deployment workflow
├── [project]-debugging.md    # Common debug scenarios
└── [project]-setup.md        # Dev environment setup
```

## Generation Process

### Step 1: Analyze Codebase

Discover patterns and conventions:

```bash
# Find common patterns
grep -r "// Pattern:" --include="*.ts" .
grep -r "# Pattern:" --include="*.py" .

# Find test patterns
ls tests/ __tests__/ spec/ 2>/dev/null

# Find CI/CD
ls .github/workflows/ .gitlab-ci.yml Jenkinsfile 2>/dev/null

# Find documentation
ls docs/ README.md CONTRIBUTING.md 2>/dev/null
```

### Step 2: Identify Skill Opportunities

Analyze for:

| Area | Look For | Skill Generated |
|------|----------|-----------------|
| Components | Repeated component patterns | component-patterns |
| API | REST/GraphQL patterns | api-patterns |
| State | Redux/Context/Zustand usage | state-management |
| Testing | Test file patterns | testing-conventions |
| Auth | Auth patterns | authentication-flow |
| Database | ORM patterns | database-patterns |

### Step 3: Generate Pattern Skill

```markdown
---
name: [project]-patterns
description: Coding patterns and conventions for [project]
---

# [Project] Coding Patterns

## Component Pattern

[Based on analysis of existing components]

### Standard Component Structure
\`\`\`typescript
// [Pattern discovered from codebase]
\`\`\`

### When to Use
- [Discovered use cases]

### Examples in Codebase
- `src/components/[Example1].tsx`
- `src/components/[Example2].tsx`

## API Pattern

[Based on analysis of API routes]

### Standard Route Structure
\`\`\`typescript
// [Pattern discovered from API routes]
\`\`\`

## Naming Conventions

- Components: [Discovered convention]
- Files: [Discovered convention]
- Functions: [Discovered convention]
```

### Step 4: Generate Testing Skill

```markdown
---
name: [project]-testing
description: Testing conventions and patterns for [project]
---

# [Project] Testing Conventions

## Test Framework
[Detected: Jest/Vitest/Pytest/etc.]

## Test Structure

### Unit Tests
Location: `[discovered test path]`
Pattern:
\`\`\`typescript
// [Pattern from existing tests]
\`\`\`

### Integration Tests
Location: `[discovered test path]`
Pattern:
\`\`\`typescript
// [Pattern from existing tests]
\`\`\`

## Running Tests

\`\`\`bash
# All tests
[discovered command]

# Single file
[discovered command]

# Watch mode
[discovered command]
\`\`\`

## Mocking Conventions

[Based on analysis of test files]
```

### Step 5: Generate Deployment Skill

```markdown
---
name: [project]-deployment
description: Deployment workflow for [project]
---

# [Project] Deployment

## Environments

| Environment | URL | Branch |
|-------------|-----|--------|
| [Discovered environments from CI/CD] |

## Deployment Process

### Pre-Deployment Checklist
- [ ] Tests passing
- [ ] Lint clean
- [ ] Build successful
- [ ] [Project-specific checks]

### Deploy Commands

\`\`\`bash
# [Commands discovered from CI/CD or package.json]
\`\`\`

## Rollback Process

[Based on CI/CD analysis or documented process]
```

### Step 6: Generate Setup Skill

```markdown
---
name: [project]-setup
description: Development environment setup for [project]
---

# [Project] Dev Setup

## Prerequisites

- [Node.js/Python/Rust version]
- [Database requirements]
- [Other dependencies]

## Quick Start

\`\`\`bash
# Clone
git clone [repo]

# Install dependencies
[detected install command]

# Setup environment
[detected setup steps]

# Start development
[detected dev command]
\`\`\`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| [From .env.example analysis] |

## Common Issues

[Based on README or docs analysis]
```

## Post-Generation

After generating:

```
Skills generated at .claude/skills/

Skills created:
- [project]-patterns.md - Coding patterns (47 patterns found)
- [project]-testing.md - Test conventions
- [project]-deployment.md - Deployment workflow
- [project]-setup.md - Dev environment setup

These skills are now available for this project.

Would you like me to review and refine any of them?
```

## Customization

Generated skills can be:
1. Edited to add more patterns
2. Extended with team-specific conventions
3. Linked from CLAUDE.md for automatic loading

## Integration

**Requires:**
- Project analysis (via analyze-project skill)

**Enables:**
- Project-specific guidance
- Consistent coding patterns
- Faster onboarding
- Team convention enforcement
