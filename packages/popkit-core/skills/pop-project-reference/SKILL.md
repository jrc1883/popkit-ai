---
name: pop-project-reference
description: "Load cross-project context in monorepos. Lists available workspace projects or loads specific project context (CLAUDE.md, package.json, README, STATUS.json). Supports pnpm, npm/yarn, Lerna workspaces. Use when working in monorepo and need context from sibling projects."
---

# Project Reference - Monorepo Context Loading

## Overview

Enables loading context from other projects in a monorepo workspace. Essential for cross-project development where you need to understand dependencies, APIs, or architecture of sibling applications.

**Core principle:** Seamless context switching in monorepos without manual file reading.

**Trigger:** Working in monorepo and need context from another project, or user runs `/popkit:project reference`.

## When to Use

Invoke when:

- User asks to "load context from [project-name]"
- Working on integration between multiple monorepo projects
- User runs `/popkit:project reference` command
- Need to understand dependencies or APIs from sibling project
- Reviewing cross-project changes

## Supported Workspace Types

- **pnpm**: `pnpm-workspace.yaml`
- **npm/yarn**: `package.json` with `workspaces` field
- **Lerna**: `lerna.json`
- **PopKit**: `.claude/workspace.json`

## Usage

### List Available Projects

```bash
/popkit:project reference
```

Shows all workspace projects with name, type, and path.

### Load Project Context

```bash
/popkit:project reference genesis
/popkit:project reference apps/optimus
/popkit:project reference packages/matrix
```

Displays:

- Project overview (from package.json)
- CLAUDE.md instructions (if exists)
- Dependencies (package.json)
- Current status (.claude/STATUS.json, if exists)
- README content

**Note**: Missing files are skipped gracefully with "(No [file] found in this project)" message.

## Implementation

See [examples/implementation.md](examples/implementation.md) for complete Python implementation.

**Key utilities from** `packages/shared-py/popkit_shared/utils/workspace_config.py`:

- `find_workspace_root()` - Detect workspace root
- `get_workspace_projects()` - List all projects
- `find_project_by_name()` - Find specific project
- `load_project_context()` - Load project files
- `format_project_context()` - Format output

## Output Format

See [examples/output-formats.md](examples/output-formats.md) for complete output examples.

**Context display includes:**

- Project header with path
- Overview from package.json
- Full CLAUDE.md content
- Dependencies section
- STATUS.json (if exists)
- README content

## Error Handling

### Not in Workspace

```
Not in a monorepo workspace.

Workspace markers:
  - pnpm-workspace.yaml (pnpm)
  - package.json with 'workspaces' field (npm/yarn)
  - lerna.json (Lerna)
  - .claude/workspace.json (PopKit)
```

### Project Not Found

```
Project 'invalid-name' not found.

Available projects:
  - genesis
  - optimus
  - matrix-engine
  ... and 10 more
```

### Import Error

```
Error: PopKit shared utilities not available

Install shared-py package:
  pip install -e packages/shared-py
```

## Use Cases

See [examples/use-cases.md](examples/use-cases.md) for detailed scenarios.

**Common patterns:**

- **Cross-Project Integration**: Load context from another project for integration work
- **API Discovery**: Check what APIs a service exposes
- **Dependency Analysis**: See what packages a project depends on

## Performance

- **Fast**: Glob patterns for discovery (< 100ms)
- **Lazy Loading**: Only reads files when project requested
- **Caching**: Workspace root detection cached per session

## Related Skills

- **pop-project-init**: Initialize new monorepo projects
- **pop-analyze-project**: Analyze current project structure
- **pop-project-observe**: Watch for project changes

## Related Commands

- `/popkit:project reference` - User-facing command wrapper
- `/popkit:project init` - Create new projects
- `/popkit:project analyze` - Analyze project health

## Testing

Test cases in `tests/skill-test.json`:

1. List all workspace projects
2. Load context from named project
3. Handle invalid project names
4. Handle non-monorepo directories

## Success Criteria

✅ Lists all projects in monorepo
✅ Loads context from named projects
✅ Handles missing files gracefully
✅ Error messages guide user to correct usage
✅ Works with pnpm/npm/yarn/Lerna workspaces

---

**Skill Type**: Utility
**Category**: Project Management
**Tier**: Core (Always Available)
**Version**: 1.0.0
