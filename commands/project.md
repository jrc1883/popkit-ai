---
description: Project analysis and setup tools - analyze codebase, generate MCP servers, configure pre-commit hooks, create custom skills
---

# /popkit:project - Project Analysis & Setup

Tools for understanding, configuring, and customizing projects after initial setup.

## Usage

```
/popkit:project <subcommand> [options]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `analyze` | Deep codebase analysis (default) |
| `mcp` | Generate project-specific MCP server |
| `setup` | Configure pre-commit hooks and quality gates |
| `skills` | Generate custom skills from project patterns |

---

## Subcommand: analyze (default)

Comprehensive codebase analysis discovering architecture, patterns, dependencies, and improvement opportunities.

```
/popkit:project                       # Full analysis
/popkit:project analyze               # Same as above
/popkit:project analyze --quick       # Quick summary only
/popkit:project analyze --focus arch  # Focus on architecture
```

### Process

Invokes the **pop-analyze-project** skill:

1. **Structure Discovery**
   - Project type detection (Node.js, Python, Rust, Go, etc.)
   - Framework identification (React, Next.js, Express, Django, etc.)
   - Directory structure analysis

2. **Pattern Recognition**
   - Code organization patterns
   - Naming conventions
   - Import/export patterns
   - State management approaches

3. **Dependency Analysis**
   - Package dependencies and versions
   - Outdated or vulnerable packages
   - Unused dependencies

4. **Quality Assessment**
   - Test coverage estimation
   - Documentation completeness
   - Code complexity hotspots

5. **Improvement Opportunities**
   - Suggested refactorings
   - Missing best practices
   - Performance optimization targets

### Output

```
## Project Analysis: [Project Name]

### Identity
- Type: Next.js 14 with TypeScript
- Framework: React 18
- Database: Supabase (PostgreSQL)
- Testing: Jest + React Testing Library

### Architecture
- Pattern: Feature-based organization
- State: React Query + Context
- API: REST (App Router)

### Quality Metrics
- Test Coverage: ~65%
- TypeScript Strict: Yes
- Linting: ESLint + Prettier

### Patterns Detected
1. Server components for data fetching
2. Client components for interactivity
3. Supabase RLS for authorization

### Improvement Opportunities
1. [High] Add error boundaries to key routes
2. [Medium] Consolidate duplicate API error handling
3. [Low] Document the auth flow

### Recommended Next Steps
- Run `/popkit:project setup` to configure pre-commit hooks
- Run `/popkit:project mcp` to generate project-specific MCP server
```

### Options

| Flag | Description |
|------|-------------|
| `--quick` | Quick summary only (5-10 lines) |
| `--focus <area>` | Focus analysis: `arch`, `deps`, `quality`, `patterns` |
| `--output <file>` | Save analysis to file |
| `-T`, `--thinking` | Enable extended thinking for deep analysis |
| `--no-thinking` | Disable extended thinking (use default) |
| `--think-budget N` | Set thinking token budget (default: 10000) |

---

## Subcommand: mcp

Generate a project-specific MCP server with semantic tools, health checks, and project awareness.

```
/popkit:project mcp                   # Generate MCP server
/popkit:project mcp --name myproject  # Custom server name
/popkit:project mcp --minimal         # Minimal toolset
```

### Process

Invokes the **pop-mcp-generator** skill:

1. **Analyze Project**
   - Detect tech stack and frameworks
   - Identify key entry points
   - Find test and build commands

2. **Generate Tools**
   - Health check tools (dev server, database, services)
   - Git tools (status, diff, recent commits)
   - Quality tools (typecheck, lint, tests)
   - Project-specific tools based on stack

3. **Create MCP Server**
   - TypeScript implementation
   - Tool discovery via embeddings
   - Configuration for Claude Code

4. **Configure Integration**
   - Add to `.mcp.json`
   - Create npm scripts
   - Document available tools

### Output

```
Generating MCP server for [Project Name]...

Detected Stack:
- Framework: Next.js 14
- Database: Supabase
- Tests: Jest

Tools Generated:
- health:dev-server - Check Next.js dev server (port 3000)
- health:database - Check Supabase connection
- git:status - Show working tree status
- git:recent - Show recent commits
- quality:typecheck - Run TypeScript check
- quality:lint - Run ESLint
- quality:test - Run Jest tests

Files Created:
- .claude/mcp-server/index.ts
- .claude/mcp-server/package.json
- .claude/mcp-server/tsconfig.json

Configuration Added:
- .mcp.json updated with server entry

Next Steps:
1. cd .claude/mcp-server && npm install && npm run build
2. Restart Claude Code to load the MCP server
3. Tools will appear as mcp__[project]__[tool]
```

### Options

| Flag | Description |
|------|-------------|
| `--name <name>` | Custom server name (default: project name) |
| `--minimal` | Generate minimal toolset (health + git only) |
| `--no-install` | Skip npm install step |
| `-T`, `--thinking` | Enable extended thinking for semantic tool generation |
| `--no-thinking` | Disable extended thinking (use default) |
| `--think-budget N` | Set thinking token budget (default: 10000) |

---

## Subcommand: setup

Configure pre-commit hooks and quality gates for the project.

```
/popkit:project setup                 # Full setup with prompts
/popkit:project setup --level standard
/popkit:project setup --level strict
/popkit:project setup --ci            # Also configure CI workflow
```

### Process

Invokes the **pop-setup-precommit** skill:

1. **Detect Project Type**
   - Node.js: Husky + lint-staged + commitlint
   - Python: pre-commit framework
   - Rust: cargo-husky

2. **Install Dependencies**
   - Pre-commit hook framework
   - Linting tools (if not present)
   - Commit message validator

3. **Configure Hooks**
   - Pre-commit: Type check, lint, format, test (staged files)
   - Commit-msg: Conventional commit validation

4. **Optional CI Integration**
   - GitHub Actions workflow
   - Same checks as local hooks

### Quality Levels

| Level | Checks |
|-------|--------|
| `basic` | Whitespace, file endings, YAML/JSON syntax |
| `standard` | Basic + lint, format, type check |
| `strict` | Standard + tests, coverage check, commit validation |
| `enterprise` | Strict + security scan, license check, dependency audit |

### Output

```
Setting up pre-commit hooks...

Project Type: Node.js (TypeScript)
Quality Level: standard

Installing:
- husky (pre-commit framework)
- lint-staged (staged file linting)
- @commitlint/cli (commit validation)

Configuring:
- .husky/pre-commit: tsc + lint-staged
- .husky/commit-msg: commitlint
- .lintstagedrc.json: ESLint + Prettier
- commitlint.config.js: Conventional commits

Hooks installed! Testing...
[ok] Pre-commit hook working
[ok] Commit-msg hook working

Commands:
- Skip once: git commit --no-verify
- Run manually: npx lint-staged
```

### Options

| Flag | Description |
|------|-------------|
| `--level <level>` | Quality level: `basic`, `standard`, `strict`, `enterprise` |
| `--ci` | Also generate CI workflow |
| `--no-test` | Skip hook verification |

---

## Subcommand: skills

Generate custom skills from project patterns and common workflows.

```
/popkit:project skills                # Analyze and suggest skills
/popkit:project skills generate       # Generate recommended skills
/popkit:project skills list           # List existing project skills
```

### Process

Invokes the **pop-skill-generator** skill:

1. **Analyze Patterns**
   - Common command sequences you run
   - Project-specific conventions
   - Repeated code patterns

2. **Suggest Skills**
   - Skills that would save time
   - Skills matching project domain
   - Skills for complex workflows

3. **Generate Skills**
   - Create SKILL.md files
   - Add to `.claude/skills/`
   - Document usage

### Output

```
Analyzing project patterns...

Suggested Skills:

1. project:deploy
   - Detected: Manual deploy steps in DEPLOYMENT.md
   - Would automate: Build, test, deploy to Vercel
   - Confidence: High

2. project:db-migration
   - Detected: Prisma migration commands used frequently
   - Would automate: Generate, apply, push migrations
   - Confidence: Medium

3. project:feature-flag
   - Detected: LaunchDarkly integration
   - Would automate: Create/toggle feature flags
   - Confidence: Medium

Generate these skills? [y/N]

Generating skills...
[ok] .claude/skills/deploy/SKILL.md created
[ok] .claude/skills/db-migration/SKILL.md created
[ok] .claude/skills/feature-flag/SKILL.md created

Skills are now available via the Skill tool.
```

---

## Examples

```bash
# Analyze current project
/popkit:project
/popkit:project analyze

# Quick analysis focused on architecture
/popkit:project analyze --quick --focus arch

# Generate MCP server
/popkit:project mcp

# Setup pre-commit hooks (standard level)
/popkit:project setup --level standard

# Setup with CI integration
/popkit:project setup --level strict --ci

# Generate project-specific skills
/popkit:project skills generate
```

---

## Workflow Integration

This command fits into the project lifecycle:

1. **New Project**: `/popkit:init-project` → Create .claude/ structure
2. **Understand Project**: `/popkit:project analyze` → Codebase analysis
3. **Configure Quality**: `/popkit:project setup` → Pre-commit hooks
4. **Enhance Tooling**: `/popkit:project mcp` → Project-specific MCP
5. **Customize**: `/popkit:project skills` → Project-specific skills

---

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Analysis Skill | `skills/pop-analyze-project/SKILL.md` |
| MCP Generator Skill | `skills/pop-mcp-generator/SKILL.md` |
| Setup Skill | `skills/pop-setup-precommit/SKILL.md` |
| Skills Generator | `skills/pop-skill-generator/SKILL.md` |
| MCP Template | `templates/mcp-server/` |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:init-project` | Initial project setup |
| `/popkit:morning` | Daily health check |
| `/popkit:next` | Context-aware recommendations |
