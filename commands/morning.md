---
description: "DEPRECATED → Use /popkit:routine morning"
deprecated: true
deprecated_in_favor_of: /popkit:routine
---

> **DEPRECATED:** This command is deprecated. Use `/popkit:routine morning` instead:
> - `/popkit:morning` → `/popkit:routine morning`
> - `/popkit:morning quick` → `/popkit:routine morning quick`
> - `/popkit:morning run pk` → `/popkit:routine morning run pk`
> - `/popkit:morning generate` → `/popkit:routine morning generate`
> - `/popkit:morning list` → `/popkit:routine morning list`
> - `/popkit:morning set <id>` → `/popkit:routine morning set <id>`
> - `/popkit:morning edit <id>` → `/popkit:routine morning edit <id>`
> - `/popkit:morning delete <id>` → `/popkit:routine morning delete <id>`

# /popkit:morning - Morning Health Check

Start your day with a comprehensive project health assessment. Supports numbered project-specific routines alongside the universal PopKit routine.

## Usage

```
/popkit:morning [subcommand] [options]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| (default) | Run the configured default routine |
| `run [id]` | Run a specific routine by ID |
| `quick` | Compact one-line summary |
| `generate` | Create a new project-specific routine |
| `list` | List available routines |
| `set <id>` | Set the default routine for this project |
| `edit <id>` | Edit a project routine |
| `delete <id>` | Delete a project routine |

## Flags

| Flag | Description |
|------|-------------|
| `--simple` | Use markdown tables instead of ASCII dashboard |
| `--no-nightly` | Skip "From Last Night" section |
| `--no-debt` | Skip technical debt check |
| `--full` | Include tests + security audit (slower) |
| `--skip-tests` | Skip test execution |
| `--skip-services` | Skip service health checks |

---

## Routine System

### PopKit Universal Routine (`pk`)

The built-in routine that works on any project:

- **ID:** `pk`
- **Mutable:** No - versioned with PopKit releases
- **Customization:** Use flags for variation (`--full`, `--skip-tests`, etc.)

### Project-Specific Routines

Custom routines stored in `.claude/popkit/routines/morning/`:

- **ID Format:** `<prefix>-<number>` (e.g., `rc-1`, `rc-2`)
- **Mutable:** Yes
- **Limit:** 5 custom routines per project

---

## Subcommand: (default)

Running `/popkit:morning` with no arguments executes the configured default routine.

### Process

1. Check for `.claude/popkit/config.json`
2. If exists, read `defaults.morning`
3. Run that routine
4. Display startup banner

### Startup Banner

```
+-------------------------------------------------------------+
| Morning Routine: rc-1 (Full E-Commerce Check)               |
| Project: Reseller Central                                   |
| Other routines: pk, rc-2 | Run: /popkit:morning list        |
+-------------------------------------------------------------+

+==================================================================+
|                  Morning Development Status                       |
...
```

If no config exists:

```
+-------------------------------------------------------------+
| Morning Routine: pk (PopKit Standard)                       |
| Project: Reseller Central                                   |
| Tip: Create a custom routine with /popkit:morning generate  |
+-------------------------------------------------------------+
```

---

## Subcommand: run [id]

Run a specific routine by ID.

```
/popkit:morning run pk        # Run popkit universal
/popkit:morning run rc-1      # Run project routine #1
/popkit:morning run rc-2      # Run project routine #2
```

### With Flags

```bash
/popkit:morning run pk --full          # Everything including slow checks
/popkit:morning run pk --skip-services # Just git + code quality
/popkit:morning run rc-1 --simple      # Project routine with markdown output
```

---

## Subcommand: quick

One-line compact summary.

```
/popkit:morning quick

Morning: 85/100 | Git (clean) | Lint (2 warnings) | Tests (passing) | Power Mode
Branch: main | Last: feat: add feature (2h ago)
```

---

## Subcommand: generate

Create a new project-specific routine.

```
/popkit:morning generate              # Interactive generation
/popkit:morning generate --nightly    # Also generate nightly counterpart
/popkit:morning generate --detect     # Preview stack detection only
/popkit:morning generate --bash       # Force bash-based generation
```

### Interactive Flow

```
/popkit:morning generate

Generating custom morning routine for: Reseller Central
Prefix: rc
Slot: rc-1 (first available)

Analyzing project...
Detected:
  - Framework: Next.js 14
  - Database: Supabase (local)
  - Services: Redis, eBay API
  - Tests: Jest

What should this routine check? (select all that apply)
  [x] Git status
  [x] TypeScript errors
  [x] Lint status
  [x] Supabase connection
  [x] Redis connection
  [x] eBay API credentials
  [ ] Run full test suite (slow)
  [ ] Security audit (slow)

Routine name: Full E-Commerce Check
Description (optional): eBay API, Redis, Supabase health checks

Creating .claude/popkit/routines/morning/rc-1/...
Updating .claude/popkit/config.json...

Routine rc-1 created!

Set as default? [Y/n] y
Default morning routine set to rc-1

Run it now? [Y/n] y
```

### Storage Structure Created

```
.claude/popkit/routines/morning/rc-1/
  routine.md         # Main routine definition
  config.json        # Routine-specific settings
  checks/
    git-status.sh
    typescript.sh
    supabase.sh
    ebay-api.sh
```

---

## Subcommand: list

List all available routines.

```
/popkit:morning list

Morning Routines for: Reseller Central

| ID    | Name                  | Default | Created    |
|-------|-----------------------|---------|------------|
| pk    | PopKit Standard       |         | (built-in) |
| rc-1  | Full E-Commerce Check | yes     | 2025-12-03 |
| rc-2  | Quick API Check       |         | 2025-12-03 |

Slots available: 3 of 5

Commands:
  /popkit:morning run <id>     Run specific routine
  /popkit:morning set <id>     Change default
  /popkit:morning generate     Create new routine
  /popkit:morning edit <id>    Edit routine
  /popkit:morning delete <id>  Delete routine
```

---

## Subcommand: set <id>

Set the default routine.

```
/popkit:morning set rc-2

Default morning routine changed: rc-1 -> rc-2

Next time you run /popkit:morning, it will use:
  rc-2: Quick API Check
```

---

## Subcommand: edit <id>

Edit an existing project routine.

```
/popkit:morning edit rc-1

Opening routine for editing: rc-1 (Full E-Commerce Check)

Current checks:
  [x] Git status
  [x] TypeScript errors
  [x] Lint status
  [x] Supabase connection
  [x] Redis connection
  [x] eBay API credentials
  [ ] Run full test suite
  [ ] Security audit

Toggle checks or describe changes:
> Add BullMQ queue health check

Adding BullMQ health check...
Routine rc-1 updated
```

**Note:** Cannot edit `pk` (built-in).

---

## Subcommand: delete <id>

Delete a project routine.

```
/popkit:morning delete rc-2

Delete routine rc-2 (Quick API Check)? [y/N] y

Routine rc-2 deleted
Folder removed: .claude/popkit/routines/morning/rc-2/

Note: rc-1 is still your default morning routine.
```

**Protection:**
- Cannot delete `pk` (built-in)
- Cannot delete current default without changing default first

---

## Health Check Process

### Step 0: From Last Night

Load previous session state from STATUS.json:

```bash
# Check if STATUS.json exists and read sleep score
cat .claude/STATUS.json 2>/dev/null | grep -E "(sleep_score|session_type|focus)"
```

Displays:
- Last night's Sleep Score (if `/popkit:nightly` was run)
- Session type (nightly_backup, session_capture, etc.)
- Previous focus area
- Any uncommitted work from last session

### Step 1: Git Status

```bash
git status --porcelain
git log --oneline -3
git rev-parse --abbrev-ref HEAD
git remote show origin 2>/dev/null | grep -E "(behind|ahead)" || echo "up to date"
```

Checks:
- Current branch
- Uncommitted changes (staged/unstaged)
- Last 3 commits
- Remote sync status

### Step 2: Code Quality (if configured)

Detect and run quality tools if present:

**TypeScript** (if tsconfig.json exists):
```bash
npx tsc --noEmit 2>&1 | head -20
```

**ESLint** (if .eslintrc* or eslint.config.* exists):
```bash
npx eslint . --max-warnings 10 2>&1 | tail -5
```

**Tests** (if package.json has test script):
```bash
npm test 2>&1 | tail -10
```

Note: Skip checks for tools not configured in the project.

### Step 3: Service Health (Power Mode)

Check if Redis is available for Power Mode:

```bash
# Check if Docker is running
docker ps 2>/dev/null

# Check if Redis container is running
docker ps --filter name=popkit-redis --format "{{.Names}}" 2>/dev/null

# Test Redis connectivity (Python)
python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping()" 2>/dev/null
```

### Step 4: Calculate Ready to Code Score

| Check | Points | Criteria |
|-------|--------|----------|
| Clean working directory | 25 | No uncommitted changes |
| Up to date with remote | 15 | Not behind origin |
| TypeScript clean | 20 | No type errors (or no tsconfig) |
| Lint clean | 15 | No lint errors (or no eslint) |
| Tests passing | 25 | All tests pass (or no tests) |

**Total: 100 points**

Projects without certain tools get full points for those checks.

### Step 5: Technical Debt Check

Scan for technical debt indicators:

```bash
# Check TECHNICAL_DEBT.md if exists
test -f TECHNICAL_DEBT.md && wc -l TECHNICAL_DEBT.md

# Count TODO/FIXME comments in source
grep -r "TODO\|FIXME\|HACK\|XXX" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" . 2>/dev/null | wc -l

# Check for eslint-disable comments
grep -r "eslint-disable" --include="*.ts" --include="*.tsx" --include="*.js" . 2>/dev/null | wc -l
```

### Step 6: PR Review Queue

Check for PRs needing attention:

```bash
# PRs awaiting your review
gh pr list --search "review-requested:@me" --json number,title,createdAt 2>/dev/null

# Your PRs needing attention
gh pr list --author @me --json number,title,reviews 2>/dev/null
```

### Step 7: Generate Recommendations

Based on issues found:
- "Pull latest changes" if behind remote
- "Commit or stash changes" if dirty working tree
- "Fix type errors" if TypeScript fails
- "Fix lint issues" if ESLint fails
- "Fix failing tests" if tests fail
- "Start Redis: /popkit:power init" if Redis not running
- "Address technical debt" if > 10 TODOs found
- "Review PRs" if PRs awaiting review

---

## Output Format (ASCII Dashboard - Default)

```
+==================================================================+
|                  Morning Development Status                       |
+==================================================================+
| Ready to Code: 85/100                                             |
+------------------------------------------------------------------+
| From Last Night:                                                  |
|   Sleep Score: 92/100                                             |
|   Session: Saved                                                  |
|   Focus: User authentication                                      |
+------------------------------------------------------------------+
| Git Status:           Clean                                       |
| TypeScript:           No errors                                   |
| Lint:                 Clean                                       |
| Tests:                All passing (142/142)                       |
+------------------------------------------------------------------+
| Technical Debt:       5 TODOs, 2 FIXMEs                           |
| PR Review Queue:      1 awaiting your review                      |
+------------------------------------------------------------------+
| Services (Power Mode):                                            |
|   Docker: Running | Redis: Ready | Power Mode: Available          |
+------------------------------------------------------------------+
| Recommendations:                                                  |
|   None - you're ready to code!                                    |
+==================================================================+
```

## Output Format (Markdown Tables - --simple)

```
Morning Report - [Project Name]
[Date]

Ready to Code Score: [XX/100]

From Last Night:
  Sleep Score: 92/100
  Session: Saved
  Focus: User authentication

Git Status:
  Branch: main
  Last commit: abc123 - feat: add feature
  Working tree: clean
  Remote: up to date

Code Quality:
  TypeScript: No errors
  Lint: Clean
  Tests: All passing

Technical Debt:
  TODOs: 5
  FIXMEs: 2
  eslint-disable: 3

PR Review Queue:
  Awaiting your review: 1
  Your PRs needing attention: 0

Services (Power Mode):
  Docker: Running
  Redis: Running (localhost:6379)
  Power Mode: Ready

Recommendations:
  None - you're ready to code!
```

---

## Architecture Integration

| Component | Integration Point |
|-----------|------------------|
| **Routine Storage** | `hooks/utils/routine_storage.py` |
| **Project Config** | `.claude/popkit/config.json` |
| **Routine Files** | `.claude/popkit/routines/morning/` |
| **Morning Report Output Style** | `output-styles/morning-report.md` |
| **Git Tools** | Bash commands for git status |
| **Quality Checks** | TypeScript, ESLint, Test detection |
| **Power Mode Integration** | Redis status check |
| **Score Calculation** | 100-point system |
| **Generator Skill** | `pop-morning-generator` |
| **Nightly Integration** | Loads Sleep Score from STATUS.json |
| **Technical Debt** | Scans TECHNICAL_DEBT.md and TODOs |
| **PR Queue** | Uses `gh pr list` for review status |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:nightly` | End-of-day cleanup and state save |
| `/popkit:nightly list` | List nightly routines |
| `/popkit:power init` | Setup Redis for Power Mode |
| `/popkit:power` | Manage multi-agent orchestration |
| `/popkit:next` | Get context-aware recommendations |
