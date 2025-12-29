---
description: "init | analyze | board | embed | generate | mcp | setup | skills | observe | reference [--power, --json]"
argument-hint: "<subcommand> [options]"
---

# /popkit:project - Project Lifecycle

Initialize, analyze, configure, and customize projects. Cross-project observability for monorepos.

## Subcommands

| Subcommand | Description |
|------------|-------------|
| init | Initialize .claude/ with Power Mode options |
| analyze | Deep codebase analysis (default) |
| board | GitHub Projects board management |
| embed | Embed project items for semantic search |
| generate | Full pipeline: analyze → skills → mcp → embed |
| mcp | Generate project-specific MCP server |
| setup | Configure pre-commit hooks |
| skills | Generate custom skills from patterns |
| observe | Cross-project dashboard (monorepo) |
| reference | Load context from another project |

---

## init

Initialize new project with Claude Code config and optional Power Mode.

Invokes **pop-project-init**: Detect type → Create .claude/ → CLAUDE.md → Config → Power Mode.

**Output:** Type detected, directories created, Power Mode tiers shown.

**Options:** --power (show tiers), --skip-power

---

## analyze (default)

Comprehensive codebase analysis: architecture, patterns, dependencies, improvements.

Invokes **pop-analyze-project**: Structure → Patterns → Dependencies → Quality → Improvements.

**Output:** Identity, Architecture, Quality metrics, Patterns, Improvements.

**Options:** --quick (summary), --focus (arch/deps/quality/patterns), -T (thinking)

---

## board

View/manage GitHub Projects board.

Uses \ CLI. Shows Todo/In Progress/Done with issue counts.

**Prerequisites:** 
---

## embed

Embed project items for semantic search.

Scan .claude/{skills,agents,commands} → Check hashes → Embed via Voyage API (3 RPM).

**Output:** Found 8, Embedded 5, Skipped 3, Errors 0.

---

## generate

Full pipeline: analyze → skills → mcp → embed.

**Output:** Step 1/4 Analyze → 2/4 Skills (4) → 3/4 MCP (8 tools) → 4/4 Embed.

---

## mcp

Generate project-specific MCP server.

Analyze stack → Generate health/git/quality tools → TypeScript server → Configure .mcp.json.

See \ for templates.

---

## setup

Configure pre-commit hooks.

**Levels:** basic (whitespace), standard (+lint/format), strict (+tests), enterprise (+security).

---

## skills

Generate custom skills from patterns.

Analyzes command sequences, conventions, repeated patterns.

---

## observe

Cross-project dashboard (requires POPKIT_API_KEY).

Shows all registered projects with activity, health, Power Mode status.

---

## reference

Load context from another project in monorepo.

Read workspace config → Load CLAUDE.md, package.json, README → Output to chat.

**Errors:** Not found (show available), Not monorepo (needs workspace config).

---

## Workflow

1. New: /popkit:project init
2. Understand: /popkit:project analyze
3. Quality: /popkit:project setup
4. Enhance: /popkit:project mcp
5. Customize: /popkit:project skills
6. Search: /popkit:project embed

**One-Command:** /popkit:project generate (steps 2,4,5,6)

---

## Architecture

| Component | Integration |
|-----------|-------------|
| Init | skills/pop-project-init/ |
| Analysis | skills/pop-analyze-project/ |
| Embed | skills/pop-embed-project/, hooks/utils/embedding_project.py |
| MCP | skills/pop-mcp-generator/, templates/mcp-server/ |
| Board | gh project CLI |
| Observe | packages/cloud/src/routes/projects.ts |

## Related

- /popkit:routine morning - Daily health check
- /popkit:power init - Power Mode setup
- /popkit:next - Context-aware recommendations

## Examples

See examples/ for: project-init-flow.md, mcp/ templates, quality-gates.md, monorepo-reference.md.
