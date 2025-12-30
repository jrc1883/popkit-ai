# PopKit Command Inventory

**Version:** 1.0.0-beta.1
**Date:** 2025-12-30
**Total Commands:** 23

---

## Command Distribution by Plugin

### popkit-core (9 commands)

| Command | Description | Primary Use |
|---------|-------------|-------------|
| `/popkit:account` | Account management and cloud connection | API key, billing, usage |
| `/popkit:bug` | Bug reporting with context capture | Issue logging, pattern sharing |
| `/popkit:dashboard` | Multi-project management | Cross-project health |
| `/popkit:plugin` | Plugin self-management | Testing, docs, validation |
| `/popkit:power` | Multi-agent orchestration | Parallel workflows |
| `/popkit:privacy` | Privacy controls and GDPR | Data consent, anonymization |
| `/popkit:project` | Project lifecycle management | Init, analyze, MCP generation |
| `/popkit:record` | Session recording | Forensic analysis |
| `/popkit:stats` | Efficiency metrics | Token savings, routine stats |

### popkit-dev (7 commands)

| Command | Description | Primary Use |
|---------|-------------|-------------|
| `/popkit:dev` | Unified development workflows | Feature dev, brainstorming |
| `/popkit:git` | Git workflow management | Commit, PR, release, publish |
| `/popkit:issue` | GitHub issue management | Create, list, track |
| `/popkit:milestone` | Milestone tracking | Progress, health checks |
| `/popkit:next` | Context-aware recommendations | What to do next |
| `/popkit:routine` | Morning/nightly routines | Health checks, cleanup |
| `/popkit:worktree` | Git worktree management | Parallel workspaces |

### popkit-ops (5 commands)

| Command | Description | Primary Use |
|---------|-------------|-------------|
| `/popkit:assess` | Multi-perspective assessment | Quality audits |
| `/popkit:audit` | Project audit and review | Quarterly reviews, stale issues |
| `/popkit:debug` | Systematic debugging | Root cause analysis, routing |
| `/popkit:deploy` | Universal deployment | Docker, npm, Vercel, etc. |
| `/popkit:security` | Security vulnerability management | Scans, fixes, tracking |

### popkit-research (2 commands)

| Command | Description | Primary Use |
|---------|-------------|-------------|
| `/popkit:knowledge` | Knowledge source management | External docs, caching |
| `/popkit:research` | Research entry management | Findings, decisions, learnings |

---

## Command Categories

### Project Management (5)
- `/popkit:project` - Initialize, analyze, generate
- `/popkit:dashboard` - Multi-project view
- `/popkit:issue` - Issue tracking
- `/popkit:milestone` - Milestone management
- `/popkit:routine` - Health checks

### Development (4)
- `/popkit:dev` - Feature development
- `/popkit:git` - Version control
- `/popkit:worktree` - Parallel workspaces
- `/popkit:next` - Recommendations

### Quality & Operations (5)
- `/popkit:assess` - Quality assessments
- `/popkit:audit` - Project audits
- `/popkit:debug` - Debugging
- `/popkit:security` - Security scans
- `/popkit:deploy` - Deployments

### Intelligence & Learning (3)
- `/popkit:power` - Multi-agent orchestration
- `/popkit:knowledge` - External knowledge
- `/popkit:research` - Research tracking

### System & Meta (6)
- `/popkit:account` - Account management
- `/popkit:privacy` - Privacy controls
- `/popkit:plugin` - Plugin management
- `/popkit:stats` - Metrics
- `/popkit:record` - Session recording
- `/popkit:bug` - Bug reporting

---

## Subcommand Count by Command

| Command | Subcommands | Total Operations |
|---------|-------------|------------------|
| `/popkit:account` | 6 | 6 |
| `/popkit:bug` | 4 | 4 |
| `/popkit:dashboard` | 4 | 4 |
| `/popkit:plugin` | 5 | 5 |
| `/popkit:power` | 7 | 7 |
| `/popkit:privacy` | 5 | 5 |
| `/popkit:project` | 10 | 10 |
| `/popkit:record` | 3 | 3 |
| `/popkit:stats` | 7 | 7 |
| `/popkit:dev` | 7 | 7 |
| `/popkit:git` | 9 | 9 |
| `/popkit:issue` | 7 | 7 |
| `/popkit:milestone` | 5 | 5 |
| `/popkit:next` | 3 | 3 |
| `/popkit:routine` | 9 | 9 |
| `/popkit:worktree` | 5 | 5 |
| `/popkit:assess` | 7 | 7 |
| `/popkit:audit` | 6 | 6 |
| `/popkit:debug` | 2 | 2 |
| `/popkit:deploy` | 5 | 5 |
| `/popkit:security` | 4 | 4 |
| `/popkit:knowledge` | 6 | 6 |
| `/popkit:research` | 7 | 7 |
| **TOTAL** | **142** | **142** |

---

## Command Complexity

### Simple (1-3 subcommands)
- `/popkit:record` - 3 subcommands
- `/popkit:next` - 3 subcommands
- `/popkit:debug` - 2 subcommands

### Medium (4-7 subcommands)
- `/popkit:bug` - 4 subcommands
- `/popkit:dashboard` - 4 subcommands
- `/popkit:plugin` - 5 subcommands
- `/popkit:privacy` - 5 subcommands
- `/popkit:worktree` - 5 subcommands
- `/popkit:milestone` - 5 subcommands
- `/popkit:deploy` - 5 subcommands
- `/popkit:security` - 4 subcommands
- `/popkit:account` - 6 subcommands
- `/popkit:audit` - 6 subcommands
- `/popkit:knowledge` - 6 subcommands
- `/popkit:power` - 7 subcommands
- `/popkit:stats` - 7 subcommands
- `/popkit:dev` - 7 subcommands
- `/popkit:issue` - 7 subcommands
- `/popkit:research` - 7 subcommands
- `/popkit:assess` - 7 subcommands

### Complex (8+ subcommands)
- `/popkit:git` - 9 subcommands
- `/popkit:routine` - 9 subcommands
- `/popkit:project` - 10 subcommands

---

## Most Used Commands (Estimated)

### Daily Use
1. `/popkit:routine morning`
2. `/popkit:git commit`
3. `/popkit:next`
4. `/popkit:dev`
5. `/popkit:issue`

### Weekly Use
1. `/popkit:routine nightly`
2. `/popkit:git pr`
3. `/popkit:milestone`
4. `/popkit:security`
5. `/popkit:stats`

### Monthly Use
1. `/popkit:audit quarterly`
2. `/popkit:assess all`
3. `/popkit:deploy`
4. `/popkit:project analyze`
5. `/popkit:dashboard`

---

## Command Dependencies

### Core Dependencies (Always Available)
- `/popkit:account` - No dependencies
- `/popkit:plugin` - No dependencies
- `/popkit:stats` - No dependencies
- `/popkit:privacy` - No dependencies
- `/popkit:record` - No dependencies

### Git Dependencies (Requires git repo)
- `/popkit:git` - git CLI
- `/popkit:worktree` - git CLI
- `/popkit:dev` - git CLI (optional)

### GitHub Dependencies (Requires gh CLI)
- `/popkit:issue` - gh CLI
- `/popkit:milestone` - gh CLI
- `/popkit:git pr` - gh CLI
- `/popkit:git ci` - gh CLI
- `/popkit:git release` - gh CLI

### API Dependencies (Requires POPKIT_API_KEY)
- `/popkit:power` (Upstash mode) - Upstash Redis
- `/popkit:project embed` - Voyage AI
- `/popkit:research search` - Voyage AI
- `/popkit:stats cloud` - PopKit Cloud

### Optional Dependencies
- `/popkit:deploy` - Docker, npm, vercel, etc. (target-specific)
- `/popkit:security` - npm (for npm projects)
- `/popkit:debug routing` - VOYAGE_API_KEY (for semantic routing)

---

## Version History

- **v1.0.0-beta.1** (2025-12-30): Initial inventory, 23 commands, 142 operations
