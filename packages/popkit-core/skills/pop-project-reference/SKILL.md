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

Invoke this skill when:

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

## Usage Patterns

### List Available Projects

```bash
/popkit:project reference
```

**Output:**
```
Found 13 projects in workspace:

| Name          | Type | Path                  |
|---------------|------|-----------------------|
| genesis       | app  | apps/genesis          |
| optimus       | app  | apps/optimus          |
| matrix-engine | pkg  | packages/matrix       |
| ...
```

### Load Project Context

```bash
/popkit:project reference genesis
/popkit:project reference apps/optimus
/popkit:project reference packages/matrix
```

**Output:**
```
===================================================================
                         Project: genesis
===================================================================

Path: /workspace/apps/genesis

## Overview
{package.json description}

## Instructions (CLAUDE.md)
{Full CLAUDE.md content}

## Dependencies (package.json)
{dependencies section from package.json}

## Current Status (.claude/STATUS.json)
{STATUS.json if exists}

## README
{README.md content}
```

## Implementation

### Step 1: Import Utilities

```python
import sys
from pathlib import Path

# Add shared-py to path
sys.path.insert(0, str(Path.home() / ".claude" / "popkit" / "packages" / "shared-py"))

try:
    from popkit_shared.utils.workspace_config import (
        find_workspace_root,
        get_workspace_projects,
        find_project_by_name,
        load_project_context,
        format_project_context,
    )
except ImportError:
    print("Error: PopKit shared utilities not available", file=sys.stderr)
    sys.exit(1)
```

### Step 2: Detect Workspace

```python
import os

workspace_root = find_workspace_root(os.getcwd())

if workspace_root is None:
    print("Not in a monorepo workspace.")
    print("\nWorkspace markers:")
    print("  - pnpm-workspace.yaml (pnpm)")
    print("  - package.json with 'workspaces' field (npm/yarn)")
    print("  - lerna.json (Lerna)")
    print("  - .claude/workspace.json (PopKit)")
    sys.exit(0)
```

### Step 3: List Projects (No Arguments)

```python
def list_projects():
    """List all projects in workspace."""
    projects = get_workspace_projects(workspace_root)

    if not projects:
        print("No projects found in workspace.")
        return

    print(f"\nFound {len(projects)} project(s) in workspace:\n")
    print("| Name | Type | Path |")
    print("|------|------|------|")

    for project in projects:
        name = project["name"]
        proj_type = project.get("type", "unknown")
        path = os.path.relpath(project["path"], workspace_root)
        print(f"| {name} | {proj_type} | {path} |")

    print("\nUsage: /popkit:project reference <project-name>")
```

### Step 4: Load Project Context (With Argument)

```python
def load_project(project_name: str):
    """Load and display project context."""
    # Find project
    project = find_project_by_name(project_name, workspace_root)

    if project is None:
        print(f"Project '{project_name}' not found.")
        print("\nAvailable projects:")
        projects = get_workspace_projects(workspace_root)
        for proj in projects[:10]:  # Show first 10
            print(f"  - {proj['name']}")
        if len(projects) > 10:
            print(f"  ... and {len(projects) - 10} more")
        sys.exit(1)

    # Load context files
    project_path = project["path"]
    context = load_project_context(project_path)

    # Format and display
    formatted = format_project_context(
        project["name"],
        project_path,
        context
    )
    print(formatted)
```

### Step 5: Main Entry Point

```python
import sys

def main():
    if len(sys.argv) < 2:
        # No project name provided - list projects
        list_projects()
    else:
        # Project name provided - load context
        project_name = sys.argv[1]
        load_project(project_name)

if __name__ == "__main__":
    main()
```

## Output Format

### Project Context Display

```
===================================================================
                         Project: {name}
===================================================================

Path: {absolute path}

## Overview
{package.json description}

## Instructions (CLAUDE.md)
{CLAUDE.md content}
[... full content of each file ...]

## Dependencies (package.json)
{dependencies section}

## Current Status (.claude/STATUS.json)
{STATUS.json if exists}

## README
{README.md content}
```

### Missing Files

If a file doesn't exist, skip it gracefully:
```
## Instructions (CLAUDE.md)
(No CLAUDE.md found in this project)
```

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

### Cross-Project Integration

```
User: "Load context from the genesis project"
→ Invoke pop-project-reference with argument "genesis"
→ Display CLAUDE.md, dependencies, README
```

### API Discovery

```
User: "What APIs does the optimus service expose?"
→ Invoke pop-project-reference with "optimus"
→ User reads API documentation from README/CLAUDE.md
```

### Dependency Analysis

```
User: "Show me what matrix-engine depends on"
→ Invoke pop-project-reference with "matrix-engine"
→ Display package.json dependencies section
```

## Architecture Integration

This skill integrates with:

- **Workspace Config Utilities**: `packages/shared-py/popkit_shared/utils/workspace_config.py`
- **Project Command**: `/popkit:project reference` command wrapper
- **Session Context**: Can read STATUS.json from other projects

## Testing

Test cases in `tests/skill-test.json`:

1. **List Projects**: Verify all workspace projects are detected
2. **Load Context**: Verify CLAUDE.md, package.json, README loaded
3. **Invalid Project**: Verify error handling for non-existent projects
4. **Not in Workspace**: Verify graceful handling when not in monorepo

## Performance

- **Fast**: Uses glob patterns for project discovery (< 100ms)
- **Lazy Loading**: Only reads files when project is requested
- **Caching**: Workspace root detection cached per session

## Related Skills

- `pop-project-init` - Initialize new monorepo projects
- `pop-analyze-project` - Analyze current project structure
- `pop-project-observe` - Watch for project changes

## Related Commands

- `/popkit:project reference` - User-facing command wrapper
- `/popkit:project init` - Create new projects
- `/popkit:project analyze` - Analyze project health

## Success Criteria

✅ Lists all projects in ElShaddai monorepo (13 apps)
✅ Loads context from named projects
✅ Handles missing files gracefully
✅ Error messages guide user to correct usage
✅ Works with pnpm/npm/yarn/Lerna workspaces
✅ Unicode handling works correctly

---

**Skill Type**: Utility
**Category**: Project Management
**Tier**: Core (Always Available)
**Version**: 1.0.0
