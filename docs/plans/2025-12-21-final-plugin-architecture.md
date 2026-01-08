# PopKit Final Plugin Architecture
**Design Document | v2.0 | 2025-12-21**

---

## Executive Summary

**Decision:** Four focused plugins with skills-based code sharing, based on official Claude Code patterns research.

**Key Insight:** Skills and agents are globally available once installed by ANY plugin. This eliminates the need for cross-plugin dependencies while enabling true modularity.

**Architecture Constraint:** Claude Code does NOT support plugin dependencies. Each plugin must be self-contained.

---

## Final Plugin Structure

### Plugin Ecosystem (4 + 1 Meta)

```
popkit (foundation)
├── 7 commands: account, stats, privacy, bug, plugin, cache, upgrade
├── Purpose: System features, account management, premium validation
├── Installs: Everyone (required for other plugins)
└── Size: Tiny (~100 lines of command markdown)

popkit-dev (development)
├── 7 commands: dev, git, issue, milestone, worktree, routine, next
├── 10 skills: session-capture, brainstorming, planning, etc.
├── 5 agents: code-explorer, code-architect, code-reviewer, etc.
├── Purpose: Complete development workflow
└── Size: Medium

popkit-ops (operations)
├── 5 commands: assess, audit, debug, security, deploy
├── 6 skills: systematic-debugging, assessment-*, etc.
├── 6 agents: security-auditor, performance-optimizer, test-writer, etc.
├── Purpose: Quality assurance and deployment
└── Size: Medium

popkit-research (knowledge)
├── 2 commands: research, knowledge
├── 3 skills: research-capture, etc.
├── 1 agent: researcher
├── Purpose: Knowledge management and research workflows
└── Size: Small

popkit-suite (meta-plugin)
├── 0 commands (just installs others)
├── Purpose: Backwards compatibility, "install everything"
└── Recommends: All 4 plugins above
```

---

## Installation Scenarios

### Minimal User
```bash
/plugin install popkit
```
Gets: Account, stats, privacy, bug reporting (7 commands)

### Developer
```bash
/plugin install popkit
/plugin install popkit-dev
```
Gets: Foundation (7) + Development (7) = **14 commands**

### DevOps Engineer
```bash
/plugin install popkit
/plugin install popkit-dev
/plugin install popkit-ops
```
Gets: Foundation (7) + Dev (7) + Ops (5) = **19 commands**

### Power User
```bash
/plugin install popkit-suite
```
Gets: All 4 plugins = **21 commands total**

---

## Command Breakdown

### popkit (Foundation - 7 commands)

| Command | Description |
|---------|-------------|
| `/popkit:account` | Manage API key, subscription status |
| `/popkit:stats` | Usage metrics, efficiency tracking |
| `/popkit:privacy` | Privacy settings, data controls |
| `/popkit:bug` | Bug reporting, diagnostics |
| `/popkit:plugin` | Plugin testing, validation |
| `/popkit:cache` | Cache management, cleanup |
| `/popkit:upgrade` | Premium features, pricing info |

**Skills:** None (pure command execution)
**Agents:** None (pure command execution)
**Python Utils:** Minimal (API client, storage helpers)

### popkit-dev (Development - 7 commands)

| Command | Description |
|---------|-------------|
| `/popkit:dev` | 7-phase feature development |
| `/popkit:git` | Git operations (commit, push, pr, review, ci, release, publish) |
| `/popkit:issue` | GitHub issue management |
| `/popkit:milestone` | Milestone tracking |
| `/popkit:worktree` | Git worktree management |
| `/popkit:routine` | Morning health checks, nightly cleanup |
| `/popkit:next` | Context-aware recommendations |

**Skills:** 10
- pop-brainstorming
- pop-writing-plans
- pop-executing-plans
- pop-next-action
- pop-session-capture
- pop-session-resume
- pop-context-restore
- pop-routine-optimized
- pop-routine-measure
- pop-finish-branch

**Agents:** 5
- code-explorer (feature-workflow)
- code-architect (feature-workflow)
- code-reviewer (tier-1)
- refactoring-expert (tier-1)
- rapid-prototyper (tier-2)

### popkit-ops (Operations - 5 commands)

| Command | Description |
|---------|-------------|
| `/popkit:assess` | Code quality assessments |
| `/popkit:audit` | Quarterly/yearly health audits |
| `/popkit:debug` | Systematic debugging workflows |
| `/popkit:security` | Security scanning and fixes |
| `/popkit:deploy` | Deployment orchestration |

**Skills:** 6
- pop-assessment-anthropic
- pop-assessment-security
- pop-assessment-performance
- pop-assessment-ux
- pop-assessment-architect
- pop-systematic-debugging

**Agents:** 6
- security-auditor (tier-1)
- performance-optimizer (tier-1)
- test-writer-fixer (tier-1)
- bug-whisperer (tier-1)
- deployment-validator (tier-2)
- rollback-specialist (tier-2)

### popkit-research (Knowledge - 2 commands)

| Command | Description |
|---------|-------------|
| `/popkit:research` | Research capture and search |
| `/popkit:knowledge` | Knowledge base management |

**Skills:** 3
- pop-research-capture
- pop-research-search
- pop-knowledge-sync

**Agents:** 1
- researcher (tier-2)

---

## Code Sharing Strategy

### Problem: No Plugin Dependencies

Claude Code does **NOT** support plugin dependencies. Plugins are copied to cache locations and cannot reference files outside their directory.

### Solution: Three-Tier Sharing Model

#### Tier 1: Skills (No Duplication)
**How it works:** Skills installed by ANY plugin are globally available to ALL agents.

**Example:**
```bash
# User installs two plugins
/plugin install popkit-dev    # Provides "code-reviewer" agent
/plugin install popkit-ops    # Provides "security-scan" skill

# Now code-reviewer can use security-scan skill!
# No duplication needed
```

**PopKit implementation:**
- popkit-dev provides 10 skills
- popkit-ops provides 6 skills
- popkit-research provides 3 skills
- Total: 19 unique skills, ZERO duplication

#### Tier 2: Python Utilities (Bundle in Each)
**Strategy:** Copy `@popkit/shared-py` into each plugin during publish.

```
popkit/hooks/utils/               ← Source (private monorepo)
popkit-dev/hooks/utils/           ← Copied during publish
popkit-ops/hooks/utils/           ← Copied during publish
popkit-research/hooks/utils/      ← Copied during publish
```

**Size impact:**
- Shared utilities: ~70 Python files, ~5000 lines total
- Per plugin overhead: ~200KB
- Total duplication: 3 plugins × 200KB = 600KB (acceptable)

**Why this is okay:**
- Utilities are small (context_carrier.py, message_builder.py, etc.)
- Each plugin remains self-contained and portable
- No runtime dependencies or import errors
- Follows Anthropic's pattern (document-skills duplicates utilities)

#### Tier 3: Premium Features (External API)
**Strategy:** Cloud API validates entitlements.

```python
# In popkit plugin (foundation)
from hooks.utils.cloud_client import get_cloud_client

client = get_cloud_client()
if client.has_premium():
    enable_power_mode()
else:
    use_local_execution()
```

**How it works:**
1. User configures API key via `/popkit:account`
2. API key stored in `~/.popkit/config.json`
3. All plugins read this config file
4. Cloud API (Cloudflare Workers) validates subscription
5. Features enabled/disabled based on response

**No duplication:** Premium checking logic lives ONLY in `popkit` plugin.

---

## Publish Strategy

### Private Monorepo (Development)

```
jrc1883/popkit (private)
└── packages/
    ├── shared-py/           ← Shared utilities (development only)
    ├── popkit/              ← Foundation plugin
    ├── popkit-dev/          ← Dev plugin
    ├── popkit-ops/          ← Ops plugin
    ├── popkit-research/     ← Research plugin
    └── popkit-suite/        ← Meta-plugin
```

### Public Marketplace (Distribution)

```
jrc1883/popkit-marketplace (public)
└── plugins/
    ├── popkit/              ← Self-contained (utils bundled)
    ├── popkit-dev/          ← Self-contained (utils bundled)
    ├── popkit-ops/          ← Self-contained (utils bundled)
    ├── popkit-research/     ← Self-contained (utils bundled)
    └── popkit-suite/        ← Meta-plugin (just recommendations)
```

### Publish Process

```bash
# From private monorepo root
cd packages/popkit
python scripts/bundle-utils.py  # Copy shared-py → hooks/utils/
git add .
git commit -m "bundle: prepare popkit for publish"

# Push to public marketplace
git subtree push --prefix=packages/popkit plugin-public main

# Repeat for each plugin
```

---

## Migration Path (from Monolith)

### Current State (v0.2.5)
- Single plugin: `popkit`
- 27 commands, 73 skills, 31 agents
- Users: `/plugin install popkit@popkit-claude`

### Phase 1: Foundation Plugin (v1.0.0-beta.1)
**Extract popkit (foundation)**
- Issue #576
- 7 commands (account, stats, etc.)
- Publish to marketplace
- Users can install: `/plugin install popkit@popkit-claude`

### Phase 2: Development Plugin (v1.0.0-beta.2)
**Extract popkit-dev**
- Issue #571 (already done locally, needs publish)
- 7 commands (dev, git, issue, etc.)
- Depends on popkit foundation (documented, not enforced)
- Users install both: `/plugin install popkit && /plugin install popkit-dev`

### Phase 3: Operations Plugin (v1.0.0-beta.3)
**Extract popkit-ops** (merge quality + deploy)
- Issue #573 + #574
- 5 commands (assess, audit, debug, security, deploy)
- Merges former popkit-quality and popkit-deploy concepts

### Phase 4: Research Plugin (v1.0.0-beta.4)
**Extract popkit-research**
- Issue #575
- 2 commands (research, knowledge)

### Phase 5: Meta-Plugin (v1.0.0)
**Create popkit-suite**
- Issue #577
- Provides backwards compatibility
- Users who want "everything" install this
- Marketplace description: "Complete PopKit suite (all plugins)"

---

## Backwards Compatibility

### For Existing Users

**v0.2.5 (current monolith):**
```bash
/plugin install popkit@popkit-claude
# Gets: Everything in one plugin
```

**v1.0.0 (modular):**
```bash
# Option 1: Install suite (everything)
/plugin install popkit-suite@popkit-claude

# Option 2: Install selectively
/plugin install popkit@popkit-claude
/plugin install popkit-dev@popkit-claude
```

**Migration message:**
```
PopKit v1.0.0 is now modular!

Install what you need:
- popkit         - Foundation (account, stats)
- popkit-dev     - Development workflows
- popkit-ops     - Quality & deployment
- popkit-research - Knowledge management

Or install everything:
- popkit-suite   - All plugins

Previous "popkit" plugin is now "popkit-suite"
```

---

## Success Metrics

### Architecture Goals
- ✅ No plugin dependencies (Claude Code limitation respected)
- ✅ No skill/agent duplication (skills globally available)
- ✅ Minimal Python utility duplication (600KB total, acceptable)
- ✅ Clear plugin boundaries (foundation vs workflows)
- ✅ User choice (install only what you need)

### User Experience Goals
- ✅ Simple installation for beginners (`/plugin install popkit`)
- ✅ Modular installation for power users (selective plugins)
- ✅ Backwards compatibility (popkit-suite = old monolith)
- ✅ Clear command namespace (all start with `/popkit:`)

### Maintenance Goals
- ✅ Independent plugin versioning
- ✅ Skills shared across plugins (no sync issues)
- ✅ Premium features centralized in foundation
- ✅ Each plugin can evolve independently

---

## Implementation Order

1. **Extract popkit (foundation)** - Issue #576
   - FIRST (others depend on this conceptually)
   - Contains: account, stats, privacy, bug, plugin, cache, upgrade
   - Smallest plugin, easiest to test

2. **Update popkit-dev** - Already extracted (Issue #571)
   - Verify it works standalone
   - Add note: "Install popkit for account management"

3. **Extract popkit-ops** - Issue #573 (merge with #574)
   - Merge quality + deploy concepts
   - Contains: assess, audit, debug, security, deploy

4. **Extract popkit-research** - Issue #575
   - Contains: research, knowledge
   - Smallest workflow plugin

5. **Create popkit-suite** - Issue #577
   - Meta-plugin for backwards compatibility
   - Just recommends other 4 plugins

---

## Open Questions

1. ~~Should plugins have dependencies on each other?~~ ✅ RESOLVED: No (not supported)
2. ~~How to share code between plugins?~~ ✅ RESOLVED: Bundle utils, share skills
3. ~~How to handle premium features?~~ ✅ RESOLVED: Cloud API validation
4. **NEW:** What's the upgrade path for existing users? (Migration tooling needed?)
5. **NEW:** Should we create a /popkit:migrate command to help transition?

---

## References

- **Research:** Claude Code plugin dependency investigation (2025-12-21)
- **Pattern:** Anthropic's document-skills and example-skills architecture
- **Constraint:** No cross-plugin dependencies in Claude Code
- **Solution:** Skills globally available, utilities bundled per plugin
- **Epic:** #580 (Plugin Modularization)
- **Merge Decision:** #583 (popkit-github → popkit-dev)

---

**Status:** Architecture finalized, ready for implementation
**Next Step:** Extract popkit (foundation) plugin
**Timeline:** 4 plugins over 2-3 weeks
