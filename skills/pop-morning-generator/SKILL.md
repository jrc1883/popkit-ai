---
name: morning-generator
description: "Use when you want to create a project-specific morning health check command - analyzes the project's tech stack and generates customized health checks for services, databases, and domain-specific validations. Detects Next.js, Express, Supabase, Redis, etc. and creates appropriate checks. Do NOT use if the generic /popkit:morning is sufficient - only generate custom commands for projects with unique health check requirements."
---

# Morning Generator

## Overview

Generate a project-specific morning health check command based on the project's tech stack, services, and domain. The generated command extends `/popkit:morning` with project-aware checks.

**Core principle:** Detect what matters for THIS project and check it every morning.

**Trigger:** `/popkit:generate-morning` command or as part of `/popkit:init-project`

## What Gets Generated

```
.claude/commands/
├── [project]:morning.md     # Project-specific morning check
└── [project]:nightly.md     # Project-specific nightly cleanup (optional)
```

## Detection Process

### Step 1: Detect Tech Stack

Analyze project for frameworks and services:

```bash
# Package managers
ls package.json Cargo.toml pyproject.toml go.mod requirements.txt 2>/dev/null

# Framework detection
grep -l "next" package.json 2>/dev/null && echo "Next.js"
grep -l "express" package.json 2>/dev/null && echo "Express"
grep -l "react" package.json 2>/dev/null && echo "React"
grep -l "vue" package.json 2>/dev/null && echo "Vue"
grep -l "django" requirements.txt 2>/dev/null && echo "Django"
grep -l "fastapi" requirements.txt 2>/dev/null && echo "FastAPI"

# Database detection
ls prisma/ 2>/dev/null && echo "Prisma"
ls supabase/ 2>/dev/null && echo "Supabase"
grep -l "mongoose" package.json 2>/dev/null && echo "MongoDB"
grep -l "pg" package.json 2>/dev/null && echo "PostgreSQL"
grep -l "redis" package.json 2>/dev/null && echo "Redis"

# Docker/services
ls docker-compose.yml docker-compose.yaml 2>/dev/null && echo "Docker Compose"
```

### Step 2: Identify Health Checks

Based on detected stack, determine checks:

| Detection | Health Check Added |
|-----------|-------------------|
| Next.js | Dev server on port 3000/3001/3002 |
| Express | API server on configured port |
| Vite | Dev server on port 5173 |
| Supabase local | Supabase services (54321-54334) |
| PostgreSQL | Database connection |
| Redis | Redis connection |
| MongoDB | MongoDB connection |
| Docker Compose | Container status |
| Prisma | Database schema sync |
| eBay SDK | eBay API credentials/OAuth |
| Stripe | Stripe API key validation |

### Step 3: Detect Project Prefix

Determine command prefix from project:

```bash
# From package.json name
jq -r '.name' package.json | tr -d '@/' | cut -d'-' -f1

# From directory name
basename $(pwd)

# From existing commands
ls .claude/commands/*:*.md 2>/dev/null | head -1 | cut -d':' -f1
```

Examples:
- genesis → `/genesis:morning`
- reseller-central → `/rc:morning`
- my-app → `/myapp:morning`

### Step 4: Generate Command

Create `.claude/commands/[prefix]:morning.md`:

```markdown
---
description: Morning health check for [Project Name] (Ready to Code score 0-100)
---

# /[prefix]:morning - [Project] Morning Check

Comprehensive health check for [Project Name] development.

## Usage

\`\`\`
/[prefix]:morning           # Full morning report
/[prefix]:morning quick     # Compact summary
\`\`\`

## Checks

### Services
[Generated based on detection]
- [ ] [Service 1] on port [X]
- [ ] [Service 2] on port [Y]
- [ ] [Database] connection

### Git Status
- Branch, uncommitted changes, remote sync

### Code Quality
[Based on detected tools]
- [ ] TypeScript errors
- [ ] Lint status
- [ ] Test results

### Domain-Specific
[Based on project type]
- [ ] [API credentials]
- [ ] [External service status]

## Ready to Code Score

| Check | Points |
|-------|--------|
| Services running | 30 |
| Clean working directory | 20 |
| Remote sync | 10 |
| TypeScript clean | 15 |
| Tests passing | 25 |

## Commands Reference

\`\`\`bash
# Start services
[Detected start commands]

# Check specific service
[Service-specific commands]

# Quick fixes
[Common fix commands]
\`\`\`
```

## Stack-Specific Templates

### Next.js + Supabase

```markdown
## Services

| Service | Port | Check Command |
|---------|------|---------------|
| Next.js | 3000 | `curl -s localhost:3000 > /dev/null` |
| Supabase API | 54321 | `curl -s localhost:54321/health` |
| Supabase DB | 54322 | `psql -h localhost -p 54322 -U postgres -c '\q'` |
| Supabase Studio | 54323 | `curl -s localhost:54323` |

## Start All Services

\`\`\`bash
# Start Supabase
npx supabase start

# Start Next.js
npm run dev
\`\`\`
```

### Express + Redis + PostgreSQL

```markdown
## Services

| Service | Port | Check Command |
|---------|------|---------------|
| Express API | 5001 | `curl -s localhost:5001/health` |
| PostgreSQL | 5432 | `pg_isready -h localhost -p 5432` |
| Redis | 6379 | `docker exec <container> redis-cli ping` |

## Start All Services

\`\`\`bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Start API
npm run dev:server
\`\`\`
```

### E-Commerce (with eBay)

```markdown
## Services

| Service | Port | Check Command |
|---------|------|---------------|
| API Server | 5001 | `curl -s localhost:5001/health` |
| Redis | 6379 | `docker exec <container> redis-cli ping` |
| Database | 5432 | `pg_isready` |

## Domain Checks

| Check | Description |
|-------|-------------|
| eBay OAuth | Token expiry and refresh |
| Cloudflare Tunnel | Required for webhooks |
| BullMQ | Job queue status |

## Critical Validations

- eBay OAuth token expires in: [X hours]
- Redis required for token refresh: [status]
- Webhook tunnel: [status]
```

## Post-Generation

After generating:

```
Morning command generated!

Created:
  .claude/commands/[prefix]:morning.md

Detected stack:
  - Framework: Next.js 14
  - Database: Supabase (local)
  - Cache: Redis
  - Tests: Jest

Health checks included:
  ✓ Next.js dev server (port 3000)
  ✓ Supabase services (ports 54321-54334)
  ✓ Redis connection
  ✓ TypeScript validation
  ✓ Jest test suite

You can now run:
  /[prefix]:morning

Would you like me to also generate /[prefix]:nightly?
```

## Integration

**Requires:**
- Project structure (package.json, etc.)
- Optional: Existing service configuration

**Enables:**
- Daily health checks
- Quick issue detection
- Consistent development startup
- Team-wide morning routine

## Customization

After generation, customize by:
1. Adding project-specific checks
2. Adjusting port numbers
3. Adding API credential validations
4. Including external service checks
