# Dashboard Subcommands

## Show Dashboard (Default)

```bash
/popkit:dashboard
```

Display full dashboard with all projects, health scores, and quick actions.

**Output format:**

```
+===============================================================+
|                      PopKit Dashboard                          |
+===============================================================+

  Total: 5  |  Healthy: 3  |  Warning: 1  |  Critical: 1

  -------------------------------------------------------------
  | Project          | Health | Issues | Last Active   |
  -------------------------------------------------------------
  | popkit           | + 92   |   5    | 2 min ago     |
  | popkit-cloud     | ~ 78   |   3    | 1 hour ago    |
  | reseller-central | + 88   |  12    | 3 days ago    |
  | my-website       | ! 45   |   0    | 2 weeks ago   |
  -------------------------------------------------------------

  Commands: add <path> | remove <name> | refresh | switch <name>
```

## Add Project

```bash
/popkit:dashboard add /path/to/project
/popkit:dashboard add . # Current directory
```

Register project in global registry.

## Remove Project

```bash
/popkit:dashboard remove project-name
```

Remove project from registry (does not delete files).

## Refresh Health Scores

```bash
/popkit:dashboard refresh           # Refresh all
/popkit:dashboard refresh popkit    # Refresh one
```

Recalculate health scores for all or specific projects.

## Switch Project

```bash
/popkit:dashboard switch project-name
```

Change context to different project. Updates activity timestamp and provides project summary.

## Interactive Switch

Use AskUserQuestion for interactive project selection:

```
question: "Which project would you like to switch to?"
header: "Switch"
options:
  - label: "popkit"
    description: "Health: 92 | Last active: 2 min ago"
  - label: "popkit-cloud"
    description: "Health: 78 | Last active: 1 hour ago"
  - label: "reseller-central"
    description: "Health: 88 | Last active: 3 days ago"
multiSelect: false
```

## Cross-Project Activity Feed

```
Recent Activity (across all projects)
-------------------------------------
| Project          | Action           | Time       |
|------------------|------------------|------------|
| popkit           | Closed #117      | 2 min ago  |
| popkit-cloud     | Pushed main      | 1 hour ago |
| reseller-central | Failed build     | 3 days ago |
```

## Settings Configuration

Configure in `~/.claude/popkit/projects.json`:

```json
{
  "settings": {
    "autoDiscover": true,
    "healthCheckInterval": "daily",
    "maxInactiveProjects": 20
  }
}
```

## Error Handling

| Situation              | Response                          |
| ---------------------- | --------------------------------- |
| No projects registered | Suggest `/popkit:dashboard add .` |
| Project path not found | Remove from registry with warning |
| Health check fails     | Show "--" for health, log error   |
| gh CLI unavailable     | Skip issue counts                 |
