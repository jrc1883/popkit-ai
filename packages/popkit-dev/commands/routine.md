---
description: "morning | nightly [run|quick|generate|list|set|edit|delete]"
argument-hint: "<routine> [subcommand] [options]"
---

# /popkit-dev:routine - Day Routines

Unified command for morning health checks and nightly maintenance routines. Supports project-specific customization with numbered routine slots.

## Primary Subcommands

| Subcommand | Description                                        |
| ---------- | -------------------------------------------------- |
| morning    | Morning health check - Ready to Code score (0-100) |
| nightly    | End-of-day cleanup - Sleep Score (0-100)           |

---

## Profiles (Issue #105)

Use `--profile <name>` to apply preset flag combinations and reduce cognitive load:

| Profile | Flags | Use Case |
|---------|-------|----------|
| **minimal** | `--quick --skip-tests --skip-services --skip-deployments --simple` | Fast health check (< 10s) |
| **standard** | (defaults) | Normal daily routine (~20s) |
| **thorough** | `--full --measure` | Deep analysis with metrics (~60s) |
| **ci** | `--optimized --measure --simple --no-cache` | CI/CD pipelines |

**Examples:**
```bash
# Minimal profile - fast morning check
/popkit:routine morning --profile minimal

# Thorough profile - deep validation
/popkit:routine morning --profile thorough

# CI profile - optimized for automation
/popkit:routine morning --profile ci

# Override profile flags
/popkit:routine morning --profile minimal --measure
```

### Smart Defaults

- `--measure` automatically enables `--simple` for parseable output
- `--full` overrides `--optimized` (thorough checks can't be cached)

### Tiered Help

| Command | Description |
|---------|-------------|
| `--help` | Quick reference (default) |
| `--help-detailed` | Detailed examples and profile guide |
| `--help-full` | Complete documentation link |
| `--list-profiles` | List available profiles with descriptions |

---

## morning

Start your day with a comprehensive project health assessment.

### Subcommands

| Subcommand  | Description                           |
| ----------- | ------------------------------------- |
| (default)   | Run the configured default routine    |
| run [id]    | Run a specific routine by ID          |
| quick       | Compact one-line summary              |
| generate    | Create a new project-specific routine |
| list        | List available routines               |
| set <id>    | Set the default routine               |
| edit <id>   | Edit a project routine                |
| delete <id> | Delete a project routine              |

### Ready to Code Score (0-100)

| Check                   | Points | Criteria                    |
| ----------------------- | ------ | --------------------------- |
| Clean working directory | 25     | No uncommitted changes      |
| Tests passing           | 25     | All tests pass              |
| CI status               | 20     | Last run successful         |
| Dependencies            | 15     | No critical vulnerabilities |
| Documentation           | 15     | CLAUDE.md up to date        |

### Anthropic Upstream Check (Issue #215)

Morning routine automatically checks for Anthropic repository updates (Claude Code, official plugins, SDKs) and displays a brief summary if new items need research.

**Output Example**:
```
🔍 Anthropic Updates: 3 items need research
```

**Commands**:
- View pending items: `/popkit-core:upstream list pending`
- Research an item: `/popkit-core:upstream research <item-id>`
- Skip check: Add `--no-upstream` flag

See `/popkit-core:upstream` documentation for full details.

### Flags

| Flag               | Description                                                  |
| ------------------ | ------------------------------------------------------------ |
| --simple           | Use markdown tables instead of ASCII dashboard               |
| --no-nightly       | Skip "From Last Night" section                               |
| --no-debt          | Skip technical debt check                                    |
| --full             | Include tests + security audit (slower)                      |
| --skip-tests       | Skip test execution                                          |
| --skip-services    | Skip service health checks                                   |
| --skip-deployments | Skip deployment status check                                 |
| --measure          | Track and report context usage, duration, and tool breakdown |
| --optimized        | Use caching and selective execution (reduces token usage)    |
| --no-cache         | Force fresh execution, bypass cached results                 |
| --no-upstream      | Skip Anthropic upstream update check (Issue #215)            |

---

## nightly

End-of-day cleanup and maintenance with sleep score.

### Subcommands

Same as morning: (default), run [id], quick, generate, list, set <id>, edit <id>, delete <id>

### Sleep Score (0-100)

| Check                  | Points | Criteria                        |
| ---------------------- | ------ | ------------------------------- |
| Uncommitted work saved | 25     | No unsaved changes or committed |
| Branches cleaned       | 20     | No stale branches               |
| Issues updated         | 20     | Today's issues have status      |
| CI passing             | 15     | Last run successful             |
| Services stopped       | 10     | Dev services shut down          |
| Logs archived          | 10     | Session logs saved              |

### Flags

| Flag           | Description                                    |
| -------------- | ---------------------------------------------- |
| --simple       | Use markdown tables instead of ASCII dashboard |
| --no-morning   | Skip "Since This Morning" section              |
| --skip-cleanup | Skip auto-cleanup actions                      |
| --skip-ip-scan | Skip IP leak scan                              |
| --measure      | Track and report context usage                 |
| --optimized    | Use caching and selective execution            |
| --no-cache     | Force fresh execution                          |

---

## Routine Measurement (--measure)

Track execution metrics for routine optimization.

**Metrics:** Duration, tool calls, token usage (input/output), cost estimates, per-tool breakdown.

**Storage:** `.claude/popkit/measurements/<routine>-<timestamp>.json`

**Implementation:** `packages/shared-py/popkit_shared/utils/routine_measurement.py`, `packages/popkit-core/hooks/post-tool-use.py`

### Viewing Measurements

After running routines with `--measure`, view the dashboard:

```
# View latest measurement
/popkit-core:stats routine

# View measurements for specific routine
/popkit-core:stats routine morning
/popkit-core:stats routine nightly

# View all measurements summary
/popkit-core:stats routine --all
```

See `/popkit-core:stats` command and `pop-routine-measure` skill for full dashboard capabilities.

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

| ID   | Type     | Description                                |
| ---- | -------- | ------------------------------------------ |
| pk   | Built-in | PopKit standard routine (always available) |
| rc-N | Custom   | Project-specific routines (numbered 1-9)   |

---

## Architecture

| Component       | Integration                                                   |
| --------------- | ------------------------------------------------------------- |
| Morning Skill   | packages/popkit-dev/skills/pop-morning/                       |
| Nightly Skill   | packages/popkit-dev/skills/pop-nightly/                       |
| Optimized Skill | packages/popkit-dev/skills/pop-routine-optimized/             |
| Measurement     | packages/shared-py/popkit_shared/utils/routine_measurement.py |
| Routine Config  | .claude/popkit/routines.json                                  |
| Dashboard Style | packages/popkit-dev/output-styles/morning-dashboard.md        |

**Related:** `/popkit-dev:next`, `/popkit-core:stats`, `/popkit-core:project observe`
