---
name: analyze-project
description: "Use when starting work on an unfamiliar project or needing to understand a codebase - performs comprehensive analysis discovering architecture, patterns, dependencies, testing coverage, and improvement opportunities. Do NOT use on projects you already know well or for targeted questions about specific files - use direct exploration instead for focused queries."
---

# Analyze Project

## Overview

Perform deep analysis of a codebase to understand its architecture, patterns, dependencies, and opportunities for improvement.

**Core principle:** Understand before changing. Map before navigating.

**Trigger:** `/analyze-project` command or when starting work on unfamiliar project

## Analysis Areas

### 1. Project Structure

```bash
# Map directory structure
find . -type d -name "node_modules" -prune -o -type d -print | head -50

# Find main entry points
ls index.* main.* app.* src/index.* src/main.* 2>/dev/null

# Count files by type
find . -name "node_modules" -prune -o -type f -print | \
  sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20
```

### 2. Technology Stack

**Detect package managers:**
```bash
ls package.json yarn.lock pnpm-lock.yaml Cargo.toml pyproject.toml go.mod 2>/dev/null
```

**Detect frameworks:**
- Next.js: `next.config.*`, `app/` or `pages/`
- React: `react` in dependencies
- Vue: `vue.config.*`
- Express: `express` in dependencies
- FastAPI: `fastapi` in dependencies
- Rust: `Cargo.toml`

**Detect databases:**
- Supabase: `@supabase/supabase-js`
- Prisma: `prisma/schema.prisma`
- MongoDB: `mongoose`
- PostgreSQL: `pg` or `postgres`

### 3. Architecture Patterns

**Frontend:**
- Component structure (atomic design, feature-based, etc.)
- State management (Redux, Zustand, Context)
- Routing patterns

**Backend:**
- API design (REST, GraphQL, tRPC)
- Service layer organization
- Database access patterns

**Common:**
- Error handling patterns
- Logging approach
- Configuration management

### 4. Code Quality

```bash
# Check for linting config
ls .eslintrc* eslint.config.* .prettierrc* biome.json 2>/dev/null

# Check TypeScript config
ls tsconfig.json 2>/dev/null && grep "strict" tsconfig.json

# Find TODO/FIXME comments
grep -r "TODO\|FIXME" --include="*.ts" --include="*.tsx" --include="*.py" . | wc -l
```

### 5. Testing Coverage

```bash
# Find test files
find . -name "*.test.*" -o -name "*.spec.*" -o -name "test_*" 2>/dev/null | wc -l

# Check test config
ls jest.config.* vitest.config.* pytest.ini 2>/dev/null

# Find coverage reports
ls coverage/ .coverage htmlcov/ 2>/dev/null
```

### 6. Dependencies

```bash
# Count dependencies
jq '.dependencies | length' package.json 2>/dev/null
jq '.devDependencies | length' package.json 2>/dev/null

# Check for outdated
npm outdated 2>/dev/null | head -10

# Check for vulnerabilities
npm audit --json 2>/dev/null | jq '.metadata.vulnerabilities'
```

### 7. CI/CD and DevOps

```bash
# Find CI config
ls .github/workflows/*.yml .gitlab-ci.yml Jenkinsfile .circleci/config.yml 2>/dev/null

# Find Docker
ls Dockerfile docker-compose.yml 2>/dev/null

# Find deployment config
ls vercel.json netlify.toml fly.toml 2>/dev/null
```

## Output Format

```markdown
# [Project Name] Analysis Report

## Summary
- **Type**: [Web App / API / CLI / Library]
- **Stack**: [Primary technologies]
- **Size**: [Files, Lines of code]
- **Health**: [Good / Needs attention / Critical issues]

## Technology Stack

### Frontend
- Framework: [Next.js 14 / React / Vue / etc.]
- Styling: [Tailwind / styled-components / etc.]
- State: [Redux / Zustand / Context]

### Backend
- Runtime: [Node.js / Python / Rust / Go]
- Framework: [Express / FastAPI / Actix]
- Database: [PostgreSQL / MongoDB / etc.]

### DevOps
- CI/CD: [GitHub Actions / GitLab CI / etc.]
- Deployment: [Vercel / AWS / etc.]
- Container: [Docker / etc.]

## Architecture

### Directory Structure
\`\`\`
[Tree output of main directories]
\`\`\`

### Key Patterns
- [Pattern 1]: [Where used]
- [Pattern 2]: [Where used]

### Entry Points
- Main: `[path]`
- API: `[path]`
- Tests: `[path]`

## Code Quality

| Metric | Value | Status |
|--------|-------|--------|
| Linting | [Configured/Missing] | [OK/Warning] |
| TypeScript Strict | [Yes/No] | [OK/Warning] |
| Test Coverage | [X%] | [OK/Warning] |
| TODO Comments | [N] | [OK/Warning] |

## Dependencies

### Production ([N] packages)
Top 5:
- [package]: [version]

### Security
- Vulnerabilities: [Low: X, Medium: Y, High: Z]

## Recommendations

### Critical
1. [Issue requiring immediate attention]

### High Priority
1. [Important improvement]

### Nice to Have
1. [Enhancement suggestion]

## Agent Opportunities

Based on analysis, these agents would be valuable:
- [agent-name]: [why]
- [agent-name]: [why]

## Next Steps

1. Run `/generate-mcp` to create project-specific tools
2. Run `/generate-skills` to capture discovered patterns
3. Run `/setup-precommit` to configure quality gates
```

## Integration

**Called by:**
- Manual `/analyze-project` command
- After `/init-project`

**Informs:**
- **/generate-mcp** - What tools to create
- **/generate-skills** - What patterns to capture
- **/setup-precommit** - What checks to configure
