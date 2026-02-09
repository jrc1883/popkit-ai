# Registry Operations

Registry stored at: `~/.claude/popkit/projects.json`

## Load Registry

```python
from project_registry import load_registry, list_projects

# Load all registered projects
registry = load_registry()
projects = list_projects()

print(f"Total projects: {len(projects)}")
```

## Add Project

```python
from project_registry import add_project

# Add project with auto-detection
success, message = add_project("/path/to/project", tags=["active"])
print(message)

# Auto-detects:
# - Project name from package.json/pyproject.toml
# - GitHub repo from git remote
# - Initial health score
```

## Remove Project

```python
from project_registry import remove_project

success, message = remove_project("my-project")
print(message)
```

## Switch Project

```python
from project_registry import get_project, touch_project
import os

project = get_project("popkit")
if project:
    os.chdir(project["path"])
    touch_project(project["path"])
    print(f"Switched to: {project['name']}")
```

## Auto-Discovery

```python
from project_registry import discover_projects, add_project

# Search common dev directories
discovered = discover_projects()

for project in discovered:
    print(f"Found: {project['name']} at {project['path']}")

# Add discovered projects
for project in discovered:
    add_project(project["path"])
```

## Project Tags

```python
from project_registry import add_tag, get_projects_by_tag

# Add tags
add_tag("popkit", "active")
add_tag("reseller-central", "client-work")

# Filter by tag
active_projects = get_projects_by_tag("active")
```

## Refresh Issue Counts

```python
from project_registry import load_registry, refresh_project_issue_counts, save_registry

# Load registry
registry = load_registry()

# Fetch fresh issue counts for all projects
updated_count = refresh_project_issue_counts(registry)

# Save updated registry
save_registry(registry)

print(f"Updated issue counts for {updated_count} projects")
```

**Cache Behavior:**

- Issue counts cached for 15 minutes (TTL)
- Dashboard displays cached counts when fresh (`< 15 min`)
- Stale cache displays `'--'` until refreshed
- Non-GitHub projects always show `'--'`

**Performance:**

- Dashboard loads instantly (uses cache, no network calls)
- Refresh fetches sequentially (~0.5s per project)
- 10 projects refresh in ~5-10 seconds
- Falls back gracefully if `gh` CLI unavailable

## Unhealthy Project Alerts

```python
from project_registry import get_unhealthy_projects

# Projects with health < 70
unhealthy = get_unhealthy_projects(threshold=70)

if unhealthy:
    print("Projects needing attention:")
    for p in unhealthy:
        print(f"  ! {p['name']}: {p['healthScore']}/100")
```
