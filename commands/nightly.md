---
description: End-of-day cleanup, maintenance, and session state preservation - Sleep Score 0-100
---

# /popkit:nightly - Nightly Maintenance

End your development day with cleanup, maintenance, and state preservation. Supports numbered project-specific routines alongside the universal PopKit routine.

## Usage

```
/popkit:nightly [subcommand] [options]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| (default) | Run the configured default routine |
| `run [id]` | Run a specific routine by ID |
| `quick` | One-line summary |
| `cleanup` | Caches, artifacts, temp files |
| `git` | gc, branch cleanup, orphans |
| `security` | npm audit, secrets scan |
| `backup` | Save session state for tomorrow |
| `generate` | Create a new project-specific routine |
| `list` | List available routines |
| `set <id>` | Set the default routine for this project |
| `edit <id>` | Edit a project routine |
| `delete <id>` | Delete a project routine |

## Flags

| Flag | Description |
|------|-------------|
| `--simple` | Use markdown tables instead of ASCII dashboard |
| `--skip-cleanup` | Skip cleanup recommendations |
| `--skip-security` | Skip security audit |
| `--full` | Include aggressive cleanup options (slower) |

---

## Routine System

### PopKit Universal Routine (`pk`)

The built-in routine that works on any project:

- **ID:** `pk`
- **Mutable:** No - versioned with PopKit releases
- **Customization:** Use flags for variation (`--full`, `--skip-cleanup`, etc.)

### Project-Specific Routines

Custom routines stored in `.claude/popkit/routines/nightly/`:

- **ID Format:** `<prefix>-<number>` (e.g., `rc-1`, `rc-2`)
- **Mutable:** Yes
- **Limit:** 5 custom routines per project

---

## Subcommand: (default)

Running `/popkit:nightly` with no arguments executes the configured default routine.

### Process

1. Check for `.claude/popkit/config.json`
2. If exists, read `defaults.nightly`
3. Run that routine
4. Display startup banner

### Startup Banner

```
+-------------------------------------------------------------+
| Nightly Routine: rc-1 (Full E-Commerce Cleanup)             |
| Project: Reseller Central                                   |
| Other routines: pk, rc-2 | Run: /popkit:nightly list        |
+-------------------------------------------------------------+

Nightly Report - Reseller Central
...
```

If no config exists:

```
+-------------------------------------------------------------+
| Nightly Routine: pk (PopKit Standard)                       |
| Project: Reseller Central                                   |
| Tip: Create a custom routine with /popkit:nightly generate  |
+-------------------------------------------------------------+
```

---

## Subcommand: run [id]

Run a specific routine by ID.

```
/popkit:nightly run pk        # Run popkit universal
/popkit:nightly run rc-1      # Run project routine #1
/popkit:nightly run rc-2      # Run project routine #2
```

### With Flags

```bash
/popkit:nightly run pk --full           # Everything including aggressive cleanup
/popkit:nightly run pk --skip-security  # Just cleanup, no security audit
/popkit:nightly run rc-1 --simple       # Project routine with markdown output
```

---

## Subcommand: quick

One-line compact summary.

```
/popkit:nightly quick

Nightly: 85/100 | Uncommitted (clean) | State (saved) | Caches (234MB) | Security (ok)
Sleep safe - session captured, no blockers
```

---

## Subcommand: generate

Create a new project-specific nightly routine.

```
/popkit:nightly generate              # Interactive generation
/popkit:nightly generate --morning    # Also generate morning counterpart
/popkit:nightly generate --detect     # Preview stack detection only
```

### Interactive Flow

```
/popkit:nightly generate

Generating custom nightly routine for: Reseller Central
Prefix: rc
Slot: rc-1 (first available)

Analyzing project...
Detected:
  - Framework: Next.js 14
  - Database: Supabase (local)
  - Services: Redis, eBay API
  - Build artifacts: .next/, dist/

What should this routine clean? (select all that apply)
  [x] Build artifacts (.next, dist)
  [x] Cache files (.eslintcache, .tsbuildinfo)
  [x] Test coverage reports
  [x] eBay API cache
  [ ] node_modules (requires npm install)
  [ ] Supabase local data

What should this routine check? (select all that apply)
  [x] Security audit (npm audit)
  [x] API token expiration
  [x] Database backup status
  [ ] Full test suite (slow)

Routine name: Full E-Commerce Cleanup
Description (optional): eBay cache, build artifacts, security audit

Creating .claude/popkit/routines/nightly/rc-1/...
Updating .claude/popkit/config.json...

Routine rc-1 created!

Set as default? [Y/n] y
Default nightly routine set to rc-1

Run it now? [Y/n] y
```

### Storage Structure Created

```
.claude/popkit/routines/nightly/rc-1/
  routine.md         # Main routine definition
  config.json        # Routine-specific settings
  scripts/
    cleanup.sh
    security-check.sh
    backup.sh
```

---

## Subcommand: list

List all available routines.

```
/popkit:nightly list

Nightly Routines for: Reseller Central

| ID    | Name                    | Default | Created    |
|-------|-------------------------|---------|------------|
| pk    | PopKit Standard         |         | (built-in) |
| rc-1  | Full E-Commerce Cleanup | yes     | 2025-12-03 |

Slots available: 4 of 5

Commands:
  /popkit:nightly run <id>     Run specific routine
  /popkit:nightly set <id>     Change default
  /popkit:nightly generate     Create new routine
  /popkit:nightly edit <id>    Edit routine
  /popkit:nightly delete <id>  Delete routine
```

---

## Subcommand: set <id>

Set the default routine.

```
/popkit:nightly set pk

Default nightly routine changed: rc-1 -> pk

Next time you run /popkit:nightly, it will use:
  pk: PopKit Standard
```

---

## Subcommand: edit <id>

Edit an existing project routine.

```
/popkit:nightly edit rc-1

Opening routine for editing: rc-1 (Full E-Commerce Cleanup)

Current cleanup targets:
  [x] Build artifacts (.next, dist)
  [x] Cache files
  [x] Test coverage
  [x] eBay API cache
  [ ] node_modules
  [ ] Supabase local data

Current checks:
  [x] Security audit
  [x] API token expiration
  [x] Database backup status
  [ ] Full test suite

Toggle items or describe changes:
> Add Redis cache cleanup

Adding Redis cache cleanup...
Routine rc-1 updated
```

**Note:** Cannot edit `pk` (built-in).

---

## Subcommand: delete <id>

Delete a project routine.

```
/popkit:nightly delete rc-1

Delete routine rc-1 (Full E-Commerce Cleanup)? [y/N] y

Routine rc-1 deleted
Folder removed: .claude/popkit/routines/nightly/rc-1/

Note: Default nightly routine reset to pk.
```

**Protection:**
- Cannot delete `pk` (built-in)
- Cannot delete current default without changing default first

---

## Nightly Report Process

### Step 1: Uncommitted Work Check

**Critical safety check before any cleanup:**

```bash
git status --porcelain
git stash list
```

If uncommitted changes exist:
- Display prominent warning
- Cap Sleep Score at 49 (cannot achieve "good" score)
- Require confirmation before proceeding with cleanup

### Step 2: Session State Assessment

Check if session state was captured:

```bash
# Check STATUS.json exists and is recent
cat .claude/STATUS.json 2>/dev/null | head -5

# Check last modification time
stat .claude/STATUS.json 2>/dev/null
```

### Step 3: Git Maintenance Status

```bash
# Check for orphaned objects
git fsck --full 2>/dev/null | head -5

# Check for merged branches that can be deleted
git branch --merged main | grep -v "^\*\|main\|master"

# Check for stale remote tracking branches
git remote prune origin --dry-run 2>/dev/null
```

### Step 4: Cache and Artifact Assessment

Detect and report cleanup opportunities:

```bash
# Node.js caches
du -sh node_modules/.cache 2>/dev/null
du -sh .eslintcache 2>/dev/null
du -sh .tsbuildinfo 2>/dev/null

# Build artifacts
du -sh dist 2>/dev/null
du -sh build 2>/dev/null
du -sh .next 2>/dev/null
du -sh out 2>/dev/null
du -sh coverage 2>/dev/null

# Python caches
du -sh .pytest_cache 2>/dev/null
du -sh __pycache__ 2>/dev/null

# Log files older than 7 days
find . -name "*.log" -mtime +7 -type f 2>/dev/null | wc -l
```

### Step 5: Security Status

```bash
# npm audit (if package.json exists)
npm audit --json 2>/dev/null | head -20

# Check for potential secrets
grep -r -l "api_key\|secret\|password" --include="*.env*" . 2>/dev/null
```

### Step 6: Calculate Sleep Score

| Check | Points | Criteria |
|-------|--------|----------|
| No uncommitted changes | 30 | **Critical** - caps score at 49 if fails |
| Session state saved | 20 | STATUS.json updated within last hour |
| Git maintenance done | 15 | No orphans, gc run recently |
| Security audit clean | 15 | No critical/high vulnerabilities |
| Caches under limit | 10 | < 500MB total cache size |
| Logs rotated | 10 | No logs older than 7 days |

**Total: 100 points**

**Score Interpretation:**
- 80-100: Safe to sleep - everything is clean
- 60-79: Minor cleanup recommended
- 40-59: Cleanup needed before leaving
- 0-39: **Do not leave** - uncommitted work or issues

---

## Output Format

```
Nightly Report - [Project Name]
[Date]

Sleep Score: [XX/100]

Uncommitted Work:
  Status: Clean (or UNCOMMITTED CHANGES - resolve before leaving!)
  Stashes: 0

Session State:
  STATUS.json: Updated 30 minutes ago
  Last focus: Implementing user auth

Git Maintenance:
  Orphans: None
  Merged branches: 2 ready for cleanup
  Stale remotes: 1

Cleanup Opportunities:
  Caches: 234 MB (node_modules/.cache, .next)
  Artifacts: 45 MB (dist, coverage)
  Old logs: 3 files

Security:
  npm audit: 0 critical, 0 high, 2 moderate
  Exposed secrets: None detected

Recommendations:
  - Run `/popkit:nightly cleanup --auto-fix` to clear 279 MB
  - Run `/popkit:nightly git --auto-fix` to clean branches
```

---

## Subcommand: cleanup

Clean caches, artifacts, and temporary files.

```
/popkit:nightly cleanup              # Report only (default)
/popkit:nightly cleanup --auto-fix   # Execute cleanup
/popkit:nightly cleanup --dry-run    # Show what would be deleted
```

### Flags

| Flag | Description |
|------|-------------|
| `--auto-fix` | Execute cleanup (required for destructive operations) |
| `--dry-run` | Show what would be deleted without deleting |
| `--aggressive` | Include node_modules (will require npm install) |

### Process

**Report mode (default):**
```bash
# List cleanup targets with sizes
du -sh dist build .next out coverage 2>/dev/null
du -sh node_modules/.cache .eslintcache .tsbuildinfo 2>/dev/null
du -sh .pytest_cache __pycache__ 2>/dev/null
find . -name "*.tmp" -type f 2>/dev/null | wc -l
find . -name "*.log" -mtime +7 -type f 2>/dev/null | wc -l
find . -name ".DS_Store" -type f 2>/dev/null | wc -l
```

**Execute mode (with --auto-fix):**
```bash
# Build artifacts
rm -rf dist/ build/ .next/ out/ coverage/

# Caches
rm -rf node_modules/.cache .eslintcache .tsbuildinfo .pytest_cache __pycache__

# Temp files
find . -name "*.tmp" -type f -delete
find . -name "*.log" -mtime +7 -type f -delete
find . -name ".DS_Store" -type f -delete
```

### Safety

- Never runs cleanup without `--auto-fix` flag
- Checks for uncommitted work before cleanup
- Preserves source files and node_modules (unless --aggressive)
- Reports space recovered after cleanup

---

## Subcommand: git

Git repository maintenance and cleanup.

```
/popkit:nightly git                  # Report only (default)
/popkit:nightly git --auto-fix       # Execute maintenance
/popkit:nightly git --dry-run        # Show what would happen
```

### Flags

| Flag | Description |
|------|-------------|
| `--auto-fix` | Execute git maintenance |
| `--dry-run` | Show what would be cleaned |
| `--keep-branches` | Skip branch cleanup |

### Process

**Report mode (default):**
```bash
git fsck --full 2>/dev/null
git branch --merged main | grep -v "^\*\|main\|master"
git remote prune origin --dry-run 2>/dev/null
git count-objects -vH
```

**Execute mode (with --auto-fix):**
```bash
# Garbage collection
git gc --auto

# Prune stale remote tracking branches
git fetch --prune

# Delete merged branches (except main/master)
git branch --merged main | grep -v "^\*\|main\|master" | xargs -r git branch -d

# Verify integrity
git fsck --full 2>/dev/null
```

---

## Subcommand: security

Run security audits and checks.

```
/popkit:nightly security             # Full security report
/popkit:nightly security --fix       # Auto-fix vulnerabilities where possible
```

### Flags

| Flag | Description |
|------|-------------|
| `--fix` | Run `npm audit fix` for auto-fixable vulnerabilities |
| `--json` | Output in JSON format |

### Process

```bash
# npm audit (if package.json exists)
npm audit 2>/dev/null

# Check for exposed secrets in common locations
grep -r -l "api_key\|secret\|password\|token" --include="*.env*" . 2>/dev/null
grep -r -l "PRIVATE KEY" --include="*.pem" --include="*.key" . 2>/dev/null

# Check .gitignore for sensitive patterns
grep -E "\.env|credentials|secrets" .gitignore 2>/dev/null || echo "WARNING: No .env in .gitignore"
```

### Output

```
Security Audit - [Project Name]

npm audit:
  Critical: 0
  High: 0
  Moderate: 2
  Low: 5
  Total: 7 vulnerabilities

Secret Scan:
  .env files: 2 found (all in .gitignore)
  Exposed secrets: None detected

Recommendations:
  - Run `npm audit fix` to resolve 3 auto-fixable issues
  - Review remaining 4 vulnerabilities manually
```

---

## Subcommand: backup

Save session state for the next day.

```
/popkit:nightly backup               # Save to STATUS.json
/popkit:nightly backup --auto-fix    # Also commit the state file
/popkit:nightly backup --message "..."  # Custom session note
```

### Flags

| Flag | Description |
|------|-------------|
| `--auto-fix` | Commit STATUS.json after saving |
| `--message` | Add custom note to session state |
| `--include-todos` | Include current todo list in state |

### Process

Invokes the **pop-session-capture** skill with nightly-specific additions:

1. **Capture Current State**
   - Git branch and last commit
   - Open files and focus area
   - In-progress tasks from todo list
   - Environment status (services, ports)

2. **Add Nightly Fields**
   - Sleep Score from current report
   - Cleanup actions taken
   - Tomorrow's recommended focus

3. **Save to STATUS.json**
```json
{
  "session_type": "nightly_backup",
  "timestamp": "2025-01-15T23:45:00Z",
  "sleep_score": 85,
  "git": {
    "branch": "feature/user-auth",
    "last_commit": "abc123 - feat: add login form",
    "uncommitted": false
  },
  "focus": "Implementing user authentication",
  "next_actions": [
    "Continue with OAuth integration",
    "Add tests for login flow"
  ],
  "cleanup_performed": {
    "caches_cleared": "234 MB",
    "branches_pruned": 2
  }
}
```

---

## Distributed Safety Checks

PopKit uses multiple checkpoints to prevent data loss from uncommitted work:

| Location | Check | Action |
|----------|-------|--------|
| `/popkit:nightly` | Primary | Warning + Score cap at 49 |
| `/popkit:morning` | "From Last Night" | Shows stash status |
| `/popkit:git push` | Before push | Warns about uncommitted |
| `/popkit:git finish` | Branch completion | Requires clean state |
| Sleep Score | Continuous | Cannot achieve 80+ with uncommitted |

---

## Architecture Integration

| Component | Integration Point |
|-----------|------------------|
| **Routine Storage** | `hooks/utils/routine_storage.py` |
| **Project Config** | `.claude/popkit/config.json` |
| **Routine Files** | `.claude/popkit/routines/nightly/` |
| **Nightly Summary Output Style** | `output-styles/nightly-summary.md` |
| **Session Capture Skill** | `skills/pop-session-capture` |
| **Nightly Generator Skill** | `skills/pop-nightly-generator` |
| **Security Auditor Agent** | For security subcommand |
| **Backup Coordinator Agent** | For backup subcommand |
| **Dead Code Eliminator Agent** | For aggressive cleanup |
| **STATUS.json** | Session state persistence |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:morning` | Start-of-day health check |
| `/popkit:morning list` | List morning routines |
| `/popkit:git prune` | Git branch cleanup |
| `/popkit:plugin sync` | Plugin integrity check |
| `/popkit:next` | Get context-aware recommendations |
