---
description: Morning health check via MCP (Ready to Code score 0-100)
---

# /popkit:morning - Morning Health Check

Start your day with a comprehensive project health assessment.

## Usage

```
/popkit:morning           # Full morning report
/popkit:morning quick     # Compact summary only
```

## Output Style

Uses `output-styles/morning-report.md` for formatting.

## Process

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

Service status:
- Docker: running/not installed
- Redis: running/stopped/not configured
- Power Mode: ready/unavailable

### Step 4: Calculate Ready to Code Score

| Check | Points | Criteria |
|-------|--------|----------|
| Clean working directory | 25 | No uncommitted changes |
| Up to date with remote | 15 | Not behind origin |
| TypeScript clean | 20 | No type errors (or no tsconfig) |
| Lint clean | 15 | No lint errors (or no eslint) |
| Tests passing | 25 | All tests pass (or no tests) |

**Total: 100 points**

Projects without certain tools get full points for those checks (don't penalize simpler projects).

Note: Service health (Redis/Power Mode) is informational only and doesn't affect score.

### Step 5: Generate Recommendations

Based on issues found:
- "Pull latest changes" if behind remote
- "Commit or stash changes" if dirty working tree
- "Fix type errors" if TypeScript fails
- "Fix lint issues" if ESLint fails
- "Fix failing tests" if tests fail
- "Start Redis: /popkit:power-init start" if Redis not running (when Power Mode available)

### Step 6: Output Report

Use the morning-report output style:

```
┌─────────────────────────────────────────────────────────────┐
│ 🌅 Morning Report - [Project Name]                          │
│ [Date] [Time]                                               │
├─────────────────────────────────────────────────────────────┤
│ Ready to Code Score: [XX/100] 🟢/🟡/🟠/🔴                   │
├─────────────────────────────────────────────────────────────┤
│ Git Status                                                   │
│ Branch: main                                                 │
│ Last commit: abc123 - feat: add feature (2 hours ago)       │
│ Working tree: clean                                         │
│ Remote sync: up to date                                     │
├─────────────────────────────────────────────────────────────┤
│ Code Quality                                                 │
│ TypeScript: ✓ No errors                                     │
│ Lint: ✓ Clean                                               │
│ Tests: ✓ All passing                                        │
├─────────────────────────────────────────────────────────────┤
│ Services (Power Mode)                                        │
│ Docker: ✓ Running                                           │
│ Redis: ✓ Running (localhost:6379)                          │
│ Power Mode: ✓ Ready                                         │
├─────────────────────────────────────────────────────────────┤
│ Recommendations                                              │
│ None - you're ready to code!                                │
└─────────────────────────────────────────────────────────────┘
```

If Redis not running:

```
├─────────────────────────────────────────────────────────────┤
│ Services (Power Mode)                                        │
│ Docker: ✓ Running                                           │
│ Redis: ✗ Not running                                        │
│ Power Mode: ⚠ Unavailable                                   │
├─────────────────────────────────────────────────────────────┤
│ Recommendations                                              │
│ 1. Start Redis: /popkit:power-init start                    │
└─────────────────────────────────────────────────────────────┘
```

If Docker not installed:

```
├─────────────────────────────────────────────────────────────┤
│ Services (Power Mode)                                        │
│ Docker: ✗ Not installed                                     │
│ Redis: - (requires Docker)                                  │
│ Power Mode: - (requires Docker)                             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Mode

For quick status (with `quick` argument):

```
Morning Report: 85/100 🟢
✓ Git (clean) | ⚠ Lint (2 warnings) | ✓ Tests (passing) | ✓ Power Mode
Branch: main | Last: feat: add feature (2h ago)
```

With Redis down:

```
Morning Report: 85/100 🟢
✓ Git (clean) | ✓ Lint | ✓ Tests | ⚠ Power Mode (Redis down)
Branch: main | Last: feat: add feature (2h ago)
Tip: /popkit:power-init start
```

## Project-Specific Extension

For project-specific health checks (database, services, etc.), use `/popkit:generate-morning` to create a customized version that includes:
- Service health checks (Redis, database, etc.)
- Framework-specific checks (Next.js, Express, etc.)
- Domain-specific validations (API keys, etc.)

## Examples

**Full report:**
```
/popkit:morning

🌅 Morning Report - my-project
2025-01-15 09:00

Ready to Code Score: 75/100 🟡

Git Status:
  Branch: feature/auth
  Last commit: abc123 - feat: add login
  Uncommitted: 3 files modified
  Remote: up to date

Code Quality:
  TypeScript: 2 errors
  Lint: clean
  Tests: 45/45 passing

Services (Power Mode):
  Docker: running
  Redis: running (localhost:6379)
  Power Mode: ready

Recommendations:
1. Fix 2 TypeScript errors before committing
2. Commit or stash your current changes
```

**Quick mode:**
```
/popkit:morning quick

Morning: 75/100 🟡 | ⚠ TS (2 errors) | ✓ Lint | ✓ Tests | ✓ Power Mode
Branch: feature/auth | 3 uncommitted files
```

**With Redis unavailable:**
```
/popkit:morning

🌅 Morning Report - my-project
2025-01-15 09:00

Ready to Code Score: 100/100 🟢

Git Status:
  Branch: main
  Last commit: def456 - docs: update readme
  Working tree: clean
  Remote: up to date

Code Quality:
  TypeScript: no errors
  Lint: clean
  Tests: all passing

Services (Power Mode):
  Docker: running
  Redis: not running
  Power Mode: unavailable

Recommendations:
1. Start Redis for Power Mode: /popkit:power-init start
```

## Architecture Integration

| Component | Integration Point |
|-----------|------------------|
| **Morning Report Output Style** | `output-styles/morning-report.md` defines format |
| **Git Tools** | Bash commands for git status, log, remote |
| **Quality Checks** | TypeScript, ESLint, Test detection and execution |
| **Power Mode Integration** | Checks Redis status via `setup-redis.py status` |
| **Recommendations** | Context-aware suggestions including Power Mode setup |
| **Score Calculation** | 100-point system for codebase readiness |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:power-init` | Setup Redis for Power Mode |
| `/popkit:power-mode` | Activate multi-agent orchestration |
| `/popkit:generate-morning` | Create project-specific morning check |
| `/popkit:next` | Get context-aware next action recommendations |
