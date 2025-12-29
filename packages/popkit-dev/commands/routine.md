---
description: "morning | nightly [run|quick|generate|list|set|edit|delete]"
argument-hint: "<routine> [subcommand] [options]"
---

# /popkit:routine - Day Routines

Unified command for morning health checks and nightly maintenance routines. Supports project-specific customization with numbered routine slots.

## Primary Subcommands

| Subcommand | Description |
|------------|-------------|
| morning | Morning health check - Ready to Code score (0-100) |
| nightly | End-of-day cleanup - Sleep Score (0-100) |

---

## morning

Start your day with a comprehensive project health assessment.

### Subcommands

| Subcommand | Description |
|------------|-------------|
| (default) | Run the configured default routine |
| run [id] | Run a specific routine by ID |
| quick | Compact one-line summary |
| generate | Create a new project-specific routine |
| list | List available routines |
| set <id> | Set the default routine |
| edit <id> | Edit a project routine |
| delete <id> | Delete a project routine |

### Ready to Code Score (0-100)

| Check | Points | Criteria |
|-------|--------|----------|
| Clean working directory | 25 | No uncommitted changes |
| Tests passing | 25 | All tests pass |
| CI status | 20 | Last run successful |
| Dependencies | 15 | No critical vulnerabilities |
| Documentation | 15 | CLAUDE.md up to date |

### Flags

| Flag | Description |
|------|-------------|
| --simple | Use markdown tables instead of ASCII dashboard |
| --no-nightly | Skip "From Last Night" section |
| --no-debt | Skip technical debt check |
| --full | Include tests + security audit (slower) |
| --skip-tests | Skip test execution |
| --skip-services | Skip service health checks |
| --skip-deployments | Skip deployment status check |
| --measure | Track and report context usage, duration, and tool breakdown |
| --optimized | Use caching and selective execution (40-96% token reduction) |
| --no-cache | Force fresh execution, bypass cached results (use with --optimized) |

---

## nightly

End-of-day cleanup and maintenance with sleep score.

### Subcommands

Same as morning: (default), run [id], quick, generate, list, set <id>, edit <id>, delete <id>

### Sleep Score (0-100)

| Check | Points | Criteria |
|-------|--------|----------|
| Uncommitted work saved | 25 | No unsaved changes or committed |
| Branches cleaned | 20 | No stale branches |
| Issues updated | 20 | Today's issues have status |
| CI passing | 15 | Last run successful |
| Services stopped | 10 | Dev services shut down |
| Logs archived | 10 | Session logs saved |

### Flags

| Flag | Description |
|------|-------------|
| --simple | Use markdown tables instead of ASCII dashboard |
| --no-morning | Skip "Since This Morning" section |
| --skip-cleanup | Skip auto-cleanup actions |
| --skip-ip-scan | Skip IP leak scan |
| --measure | Track and report context usage |
| --optimized | Use caching and selective execution |
| --no-cache | Force fresh execution |

---

## Routine Measurement (--measure)

Track execution metrics for routine optimization.

**Metrics:** Duration, tool calls, token usage (input/output), cost estimates, per-tool breakdown.

**Storage:** `.claude/popkit/measurements/<routine>-<timestamp>.json`

**Implementation:** `hooks/utils/routine_measurement.py`, `hooks/post-tool-use.py`

---

## Project-Specific Routines

### Storage

`.claude/popkit/routines.json`:

```json
{
  "morning": {
    "default": "pk",
    "routines": {
      "pk": { "name": "PopKit Standard", "checks": [...] },
      "rc-1": { "name": "Full Stack", "checks": [...] }
    }
  },
  "nightly": {
    "default": "pk",
    "routines": {
      "pk": { "name": "PopKit Standard", "checks": [...] }
    }
  }
}
```

### Routine IDs

| ID | Type | Description |
|----|------|-------------|
| pk | Built-in | PopKit standard routine (always available) |
| rc-N | Custom | Project-specific routines (numbered 1-9) |

---

## Architecture

| Component | Integration |
|-----------|-------------|
| Morning Skill | skills/pop-morning/ |
| Nightly Skill | skills/pop-nightly/ |
| Optimized Skill | skills/pop-routine-optimized/ |
| Measurement | hooks/utils/routine_measurement.py |
| Routine Config | .claude/popkit/routines.json |
| Dashboard Style | output-styles/morning-dashboard.md |

**Related:** `/popkit:next`, `/popkit:stats`, `/popkit:project observe`
