---
description: Morning health check and project-specific generator - Ready to Code score 0-100
---

# /popkit:morning - Morning Health Check

Start your day with a comprehensive project health assessment.

## Usage

```
/popkit:morning [subcommand] [options]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| (default) | Full morning health report |
| `quick` | Compact one-line summary |
| `generate` | Create project-specific morning command |

---

## Default: Health Report

```
/popkit:morning           # Full morning report
/popkit:morning quick     # Compact summary only
```

### Process

#### Step 1: Git Status

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

#### Step 2: Code Quality (if configured)

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

#### Step 3: Service Health (Power Mode)

Check if Redis is available for Power Mode:

```bash
# Check if Docker is running
docker ps 2>/dev/null

# Check if Redis container is running
docker ps --filter name=popkit-redis --format "{{.Names}}" 2>/dev/null

# Test Redis connectivity (Python)
python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping()" 2>/dev/null
```

#### Step 4: Calculate Ready to Code Score

| Check | Points | Criteria |
|-------|--------|----------|
| Clean working directory | 25 | No uncommitted changes |
| Up to date with remote | 15 | Not behind origin |
| TypeScript clean | 20 | No type errors (or no tsconfig) |
| Lint clean | 15 | No lint errors (or no eslint) |
| Tests passing | 25 | All tests pass (or no tests) |

**Total: 100 points**

Projects without certain tools get full points for those checks.

#### Step 5: Generate Recommendations

Based on issues found:
- "Pull latest changes" if behind remote
- "Commit or stash changes" if dirty working tree
- "Fix type errors" if TypeScript fails
- "Fix lint issues" if ESLint fails
- "Fix failing tests" if tests fail
- "Start Redis: /popkit:power init" if Redis not running

### Output Format

```
Morning Report - [Project Name]
[Date]

Ready to Code Score: [XX/100]

Git Status:
  Branch: main
  Last commit: abc123 - feat: add feature
  Working tree: clean
  Remote: up to date

Code Quality:
  TypeScript: No errors
  Lint: Clean
  Tests: All passing

Services (Power Mode):
  Docker: Running
  Redis: Running (localhost:6379)
  Power Mode: Ready

Recommendations:
  None - you're ready to code!
```

### Quick Mode

```
/popkit:morning quick

Morning: 85/100 | Git (clean) | Lint (2 warnings) | Tests (passing) | Power Mode
Branch: main | Last: feat: add feature (2h ago)
```

---

## Subcommand: generate

Create a project-specific morning health check command.

```
/popkit:morning generate              # Auto-detect MCP vs bash
/popkit:morning generate --nightly    # Also generate nightly cleanup
/popkit:morning generate --detect     # Show MCP detection only (don't generate)
/popkit:morning generate --bash       # Force bash-based generation (skip MCP)
/popkit:morning generate --mcp-wrapper # Force MCP wrapper generation
```

### MCP-Aware Generation

The generator automatically detects MCP infrastructure and adapts:

| Detection | Action |
|-----------|--------|
| MCP + health tools | Generate MCP wrapper commands (10-20 lines) |
| MCP, no health tools | Generate hybrid commands |
| No MCP | Generate bash commands (100+ lines) |

**MCP Detection Checks:**
- `@modelcontextprotocol/sdk` in package.json
- `.mcp.json` configuration file
- MCP server directories (`packages/*/mcp/`, etc.)
- Health tool patterns (`morning_routine`, `check_*`, etc.)

**Use `--detect` to preview without generating:**
```
/popkit:morning generate --detect

MCP Infrastructure Detected!
Server: mcp__project-dev
Health Tools: morning_routine, check_database, check_api
Recommendation: Generate MCP wrapper commands
```

### What Gets Detected

| Category | Examples |
|----------|----------|
| Frameworks | Next.js, Express, Vue, Django, FastAPI |
| Databases | PostgreSQL, MongoDB, Supabase, Prisma |
| Cache | Redis, Memcached |
| Services | Docker, eBay API, Stripe, AWS |
| Quality | TypeScript, ESLint, Jest, Pytest |

### Process

1. Detect tech stack (frameworks, databases, services)
2. Identify health check requirements
3. Determine project command prefix
4. Generate `.claude/commands/[prefix]:morning.md`
5. Report findings and offer customization

### Example Output

```
/popkit:morning generate

Analyzing project...

Tech Stack Detected:
  Framework: Next.js 14
  Database: Supabase (local, port 54322)
  Cache: Redis (port 6379)
  Quality: TypeScript, ESLint, Jest

Project Prefix: "genesis" (from package.json)

Generating .claude/commands/genesis:morning.md...

Health checks configured:
  - Next.js dev server (port 3000)
  - Supabase services (ports 54321-54334)
  - Redis connection
  - TypeScript validation
  - Jest test suite

Command created!

You can now run:
  /genesis:morning         # Full report
  /genesis:morning quick   # Quick status
```

### Generated Command Features

- **Service Health Checks**: Port availability, process status, connection testing
- **Git Integration**: Branch info, uncommitted changes, remote sync
- **Quality Gates**: TypeScript errors, lint status, test results
- **Ready to Code Score**: 0-100 with color-coded status

---

## Output Style

Uses `output-styles/morning-report.md` for formatting.

## Architecture Integration

| Component | Integration Point |
|-----------|------------------|
| **Morning Report Output Style** | `output-styles/morning-report.md` |
| **Git Tools** | Bash commands for git status |
| **Quality Checks** | TypeScript, ESLint, Test detection |
| **Power Mode Integration** | Redis status check |
| **Score Calculation** | 100-point system |
| **Generator Skill** | `pop-morning-generator` |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:power init` | Setup Redis for Power Mode |
| `/popkit:power` | Manage multi-agent orchestration |
| `/popkit:next` | Get context-aware recommendations |
