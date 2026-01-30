# Implementation

Complete Python implementation for project reference loading.

## Import Utilities

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

## Detect Workspace

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

## List Projects (No Arguments)

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

## Load Project Context (With Argument)

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

## Main Entry Point

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
