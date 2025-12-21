# PopKit Plugin Modularization Architecture
**Design Document | v1.0 | 2025-12-20**

---

## Executive Summary

This document defines the architecture for splitting PopKit from a monolithic plugin (235 Python files, 73 skills, 36 agents, 27 commands) into **focused, workflow-based plugins** with optional **API key enhancements** via Upstash cloud stack.

**Core Insight**: All plugins are FREE with full local capabilities. API keys unlock **semantic intelligence** and **community knowledge** WITHIN each plugin - not separate paid plugins.

**Key Principle**: **Leverage native Claude Code capabilities** (async agents, extended thinking) - don't reinvent them. API key adds semantic routing and community patterns, not parallel execution.

---

## Problem Statement

### Current Issues

1. **Monolithic Complexity** - 235 Python files covering dev workflows, deployment, security, cloud orchestration, knowledge management, and more
2. **Tier Confusion** - Unclear what's free vs paid (conflicting documentation in Issues #353 vs #566)
3. **Cognitive Overload** - Users don't know what PopKit does or where to start
4. **Maintenance Burden** - Everything tightly coupled, hard to add features
5. **Marketplace Misalignment** - Anthropic's plugins are focused (document-skills, example-skills) while PopKit tries to do everything

### Related Work

- **Issue #567** - Investigation into modular plugin strategy
- **Issue #353** - Premium feature gating (source of tier confusion)
- **Issue #241** - Cross-platform architecture vision (Python CLI + Textual)
- **Research Doc**: `docs/research/2025-12-14-cross-platform-architecture-vision.md`

---

## Architecture Vision

### Core Principles

1. **Workflow-Based Plugins, Not Tier-Based**
   - Each plugin solves one workflow category (dev, deploy, quality, etc.)
   - All plugins FREE with local execution
   - API key enhances ALL plugins with semantic search + community knowledge

2. **Native Claude Code Integration**
   - Use native async agent spawning (5+ agents via Task tool)
   - Use extended thinking, tool use, MCP servers, hooks
   - **Don't reinvent** what Anthropic provides

3. **Shared Foundation**
   - Extract 69 utility modules into `@popkit/shared-py`
   - All plugins depend on shared package
   - Consistent API key detection and enhancement

4. **Enhancement Model (Not Separation)**
   - Same workflows with/without API key
   - API key adds: semantic routing, community knowledge, pattern learning
   - No feature gating - just intelligence amplification

---

## Plugin Structure

### Proposed Plugins

| Plugin | Commands | Purpose | Free Capabilities | Enhanced (w/ API Key) |
|--------|----------|---------|-------------------|----------------------|
| **popkit-dev** | dev, git, worktree, routine, next | Core development workflows | Local agents, keyword routing | Semantic agent selection, community templates |
| **popkit-github** | issue, milestone | GitHub project management | gh CLI operations | Pattern-based templates, smart labels |
| **popkit-quality** | assess, audit, debug, security | Code quality & security | Local analysis | Community bug fixes, similar issue search |
| **popkit-deploy** | deploy | Deployment automation | Basic deployment | Community configs, proven patterns |
| **popkit-research** | research, knowledge | Knowledge management | Local notes | Semantic search, cross-project knowledge |
| **popkit-core** | plugin, stats, privacy, account, upgrade, cache, bug | Meta/system features | All local | Usage analytics, bug pattern matching |

### Shared Package

**Name**: `@popkit/shared-py`

**Contents**:
```
packages/shared-py/popkit_shared/
├── utils/                  ← 69 utility modules from hooks/utils/
│   ├── context_carrier.py
│   ├── embedding_*.py
│   ├── cloud_client.py
│   ├── skill_context.py
│   └── ... (66 more)
├── types/                  ← Shared type definitions
│   ├── hook_context.py
│   └── agent_state.py
├── hooks/                  ← Base hook classes
│   ├── stateless_hook.py
│   └── message_builder.py
└── api/                    ← Upstash client (API key integration)
    ├── client.py
    ├── semantic_search.py
    └── pattern_store.py
```

**Installation**: `pip install popkit-shared`

**All plugins** list `popkit-shared` as dependency in their `requirements.txt`

---

## API Key Enhancement Model

### How Enhancements Work

Every plugin checks for API key and conditionally enhances:

```python
# In every skill/agent/command
from popkit_shared.api import get_api_client

client = get_api_client()  # Returns None if no API key

if client:
    # ENHANCED MODE
    # 1. Semantic Routing
    best_agent = client.semantic_search("add authentication", type="agent")
    # Returns: code-architect (0.95 confidence)

    # 2. Community Knowledge
    templates = client.search_templates("nextauth oauth")
    # Returns: 3 community templates, 2 bug fixes

    # 3. Pattern Learning
    client.log_pattern({
        "workflow": "feature-dev",
        "decision": "chose sessions over JWT",
        "context": "nextjs app"
    })

else:
    # FREE MODE
    # 1. Keyword Matching
    best_agent = keyword_match("authentication")  # → code-architect

    # 2. No Community Knowledge
    templates = []

    # 3. No Pattern Logging
    pass
```

**Key principle**: Workflow logic is **identical** - just enhanced when API key present.

### What the "Cloud" (Upstash Stack) Provides

```
Upstash Stack at api.thehouseofdeals.com:
├── Vector Database (Voyage embeddings)
│   ├── Skill embeddings → Find best skill for task
│   ├── Agent embeddings → Find best agent for code
│   ├── Code snippet embeddings → Community solutions
│   ├── Bug fix embeddings → Community fixes
│   └── Template embeddings → Starter code
│
├── Redis
│   ├── Session state (pause/resume workflows)
│   ├── Real-time sync (multi-device access)
│   └── Pattern cache (hot tier - 24hr TTL)
│
└── Pattern Storage (Postgres - cold tier)
    ├── User patterns (learned from your code)
    └── Community patterns (anonymized, aggregated)
```

**NOT used for**: Parallel agent execution (Claude Code handles that natively)

---

## Migration Strategy

### Phase 1: Extract Shared Foundation (Week 1-2)

**Goal**: Create `@popkit/shared-py` package

**Steps**:
1. Create package structure: `packages/shared-py/popkit_shared/`
2. Move 69 utility files from `packages/plugin/hooks/utils/` to `shared-py/popkit_shared/utils/`
3. Update imports across all files:
   - OLD: `from hooks.utils.context_carrier import HookContext`
   - NEW: `from popkit_shared.utils.context_carrier import HookContext`
4. Add `setup.py` with dependencies
5. Publish to PyPI or local registry
6. Update plugin's `requirements.txt` to depend on `popkit-shared`

**Validation**: All existing commands still work after import changes

### Phase 2: Extract popkit-dev (Week 2-3)

**Goal**: First plugin extraction as proof-of-concept

**Commands to extract**:
- dev.md → /popkit:dev
- git.md → /popkit:git
- worktree.md → /popkit:worktree
- routine.md → /popkit:routine
- next.md → /popkit:next

**Skills to extract** (from `packages/plugin/skills/`):
- pop-brainstorming
- pop-writing-plans
- pop-executing-plans
- pop-finish-branch
- pop-project-templates
- pop-routine-*
- pop-systematic-debugging
- pop-code-review

**Agents to extract** (from `packages/plugin/agents/`):
- code-reviewer
- code-architect
- code-explorer
- bug-whisperer

**Steps**:
1. Create `packages/popkit-dev/` directory
2. Copy command, skill, agent definitions
3. Update plugin.json manifest
4. Add `requirements.txt` with `popkit-shared` dependency
5. Test: `/popkit:dev brainstorm`, `/popkit:git commit`, etc.

**Validation**: All dev workflows work identically to monolith

### Phase 3: Extract Remaining Plugins (Week 3-6)

**Order** (simplest to most complex):
1. **popkit-github** (Week 3) - Just gh CLI wrapper, minimal deps
2. **popkit-deploy** (Week 3-4) - Self-contained deployment logic
3. **popkit-quality** (Week 4-5) - Moderate complexity (6 assessment skills)
4. **popkit-research** (Week 5) - Depends on vector DB (API key feature)
5. **popkit-core** (Week 6) - Meta features, cleanup

**For each plugin**:
1. Create package directory
2. Extract commands, skills, agents
3. Update manifest
4. Add shared dependency
5. Test all commands
6. Document migration notes

### Phase 4: Cleanup & Documentation (Week 7)

1. Archive old monolith package (`packages/plugin/` → `packages/plugin-legacy/`)
2. Update README with new plugin architecture
3. Create migration guide for users
4. Update CLAUDE.md with new structure
5. Publish all plugins to marketplace

---

## Plugin Communication & Shared Dependencies

### How Plugins Share Skills

**Problem**: Multiple plugins need the same skills (e.g., `pop-brainstorming` used by `dev`, `research`, `quality`)

**Solution 1: Skill Marketplace (Recommended)**
```
Shared Skills Repository:
├── @popkit/skills-common → Core skills used by multiple plugins
│   ├── pop-brainstorming
│   ├── pop-writing-plans
│   ├── pop-executing-plans
│   └── pop-finish-branch
└── All plugins list as dependency
```

**Solution 2: Skill Duplication**
```
Each plugin bundles its own copy:
├── popkit-dev/skills/pop-brainstorming/
├── popkit-research/skills/pop-brainstorming/  ← Duplicate
└── popkit-quality/skills/pop-brainstorming/  ← Duplicate
```

**Recommendation**: Solution 1 (shared skills package) - avoids duplication, ensures consistency

### How Plugins Coordinate

**Scenario**: User runs `/popkit:dev work #123` which needs GitHub issue data

**Approach**: Plugins **don't directly call each other** - they use shared utilities

```python
# In popkit-dev
from popkit_shared.utils.github_api import fetch_issue

issue = fetch_issue(123)  # Uses shared utility
# Proceed with dev workflow
```

**Benefit**: Loose coupling - plugins can be installed/uninstalled independently

---

## API Key Pricing & Tiers

### Simplified Tier Structure

**FREE Tier** (No API key):
- All plugins, all commands
- Local execution only
- Keyword-based routing
- No community knowledge
- File-based state

**Pro Tier** ($9/month):
- Same plugins + API key
- Semantic routing (Vector DB + Voyage embeddings)
- Community knowledge (templates, bug fixes, patterns)
- Multi-device state sync (Redis)
- Pattern learning
- 1,000 API requests/day

**Team Tier** ($49/month):
- Everything in Pro
- Team coordination features
- Shared workflows
- Analytics dashboard
- 10,000 API requests/day
- Priority support

**Enterprise** (Custom pricing):
- Self-hosted Upstash stack
- Unlimited requests
- Custom integrations
- SLA support

### What Justifies Payment?

**Value proposition**:
- **Time saved** - Semantic routing finds best agent/skill faster
- **Community intelligence** - Leverage solutions from other users
- **Cross-project learning** - Patterns learned in one project apply to others
- **Multi-device sync** - Start on desktop, continue on laptop

**NOT gated**: Core workflows, agent capabilities, local execution

---

## Technical Decisions

### Language Choice: Python (Pragmatic)

**Rationale**:
- 235 Python files already working (no rewrite cost)
- Claude Code hooks are Python-based (JSON stdin/stdout protocol)
- Research doc proposes Python CLI (Textual framework)
- TypeScript only for MCP integration layer (`universal-mcp`)

**Architecture**:
```
Python Stack (Core):
├── @popkit/shared-py → Shared utilities
├── popkit-* plugins → Python hooks + skills
└── popkit-cli (future) → Python + Textual

TypeScript Stack (Integration):
├── @popkit/mcp → MCP server for IDEs
└── Thin wrapper calling Python core
```

### Hook Protocol: Unchanged

Claude Code hooks use JSON stdin/stdout:
```python
#!/usr/bin/env python3
import json
import sys

# Read hook input
hook_input = json.loads(sys.stdin.read())

# Execute hook logic
result = process_hook(hook_input)

# Write hook output
print(json.dumps(result))
```

**No changes needed** - extract and reorganize without protocol changes

### Shared Package Distribution

**Option A: PyPI** (Public package index)
- ✅ Standard Python workflow
- ✅ Easy installation: `pip install popkit-shared`
- ❌ Public (can't include proprietary code)

**Option B: Private PyPI** (Self-hosted)
- ✅ Can include proprietary code
- ✅ Same workflow as public PyPI
- ❌ Requires hosting infrastructure

**Option C: Git submodules**
- ✅ No hosting needed
- ✅ Works with private repos
- ❌ Complex dependency management

**Recommendation**: Start with PyPI (public) for v1.0, migrate to private PyPI if needed

---

## Migration Path for Existing Users

### Backwards Compatibility Strategy

**Goal**: Existing users continue working without changes

**Approach**: Monolith → Meta-plugin (umbrella)

```
Old (v0.2.5):
└── Install popkit → Get everything

New (v1.0.0):
└── Install popkit → Auto-installs all sub-plugins
    ├── popkit-dev
    ├── popkit-github
    ├── popkit-quality
    ├── popkit-deploy
    ├── popkit-research
    └── popkit-core
```

**Implementation**:
```json
// packages/popkit/plugin.json (meta-plugin)
{
  "name": "popkit",
  "version": "1.0.0",
  "description": "Complete PopKit suite (installs all plugins)",
  "dependencies": [
    "popkit-dev",
    "popkit-github",
    "popkit-quality",
    "popkit-deploy",
    "popkit-research",
    "popkit-core"
  ]
}
```

**User experience**:
- Existing users: `/plugin update popkit` → Seamlessly upgrades to modular architecture
- New users (selective): `/plugin install popkit-dev` → Install only what they need
- New users (complete): `/plugin install popkit` → Install everything (like before)

### Deprecation Timeline

**v0.2.5** (Current):
- Monolithic plugin
- Full functionality
- Mark as "legacy" in marketplace

**v1.0.0** (Q1 2026):
- Modular plugins released
- Monolith becomes meta-plugin (auto-installs modules)
- Backwards compatible

**v1.1.0** (Q2 2026):
- Deprecate monolith meta-plugin
- Encourage users to install individual plugins
- Monolith shows deprecation warning

**v2.0.0** (Q3 2026):
- Remove monolith entirely
- Only modular plugins available

---

## Testing & Validation

### Acceptance Criteria

**Phase 1 (Shared Package)**:
- [ ] All 69 utilities extracted to `@popkit/shared-py`
- [ ] Import paths updated across codebase
- [ ] All existing commands still work
- [ ] No functionality regression

**Phase 2 (popkit-dev)**:
- [ ] `/popkit:dev`, `/popkit:git`, `/popkit:worktree`, `/popkit:routine`, `/popkit:next` work identically
- [ ] Skills (brainstorming, plans, etc.) function correctly
- [ ] Agents (code-reviewer, etc.) route properly
- [ ] API key enhancements work (semantic search, community knowledge)

**Phase 3 (Remaining Plugins)**:
- [ ] Each plugin installable independently
- [ ] All commands work in isolation
- [ ] Shared dependencies resolved correctly
- [ ] No cross-plugin breaking changes

**Phase 4 (Integration)**:
- [ ] Meta-plugin installs all sub-plugins
- [ ] Existing users seamlessly upgrade
- [ ] New users can selectively install
- [ ] Marketplace listings accurate

### Testing Strategy

**Unit Tests**:
- Test each utility function in `@popkit/shared-py`
- Test each skill invocation
- Test each command execution

**Integration Tests**:
- Test workflows across plugins (e.g., `/popkit:dev work #123` which uses GitHub data)
- Test API key enhancements (semantic search, community knowledge)
- Test multi-plugin installations

**User Acceptance Testing**:
- Existing users upgrade and verify no breakage
- New users install individual plugins and verify functionality
- API key users verify enhanced features work

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Breaking existing users** | High | Meta-plugin auto-installs all modules, maintains backwards compatibility |
| **Import path hell** | Medium | Shared package with stable API, semantic versioning |
| **Plugin dependency conflicts** | Medium | All plugins pin `popkit-shared` version, coordinated releases |
| **API key feature leakage** | Low | Clear separation in code (if client else fallback) |
| **Marketplace confusion** | Medium | Clear naming (popkit-dev, popkit-github), good descriptions |
| **Over-modularization** | Low | Start with 6 plugins (not 20), merge if needed |

---

## Success Metrics

**Technical**:
- ✅ Reduced plugin size (< 50 files per plugin vs 235 monolith)
- ✅ Faster install times (selective installation)
- ✅ Improved maintainability (focused modules)

**User Experience**:
- ✅ Clear understanding of what each plugin does
- ✅ Selective feature adoption (install only what you need)
- ✅ Smooth upgrade path (no breaking changes)

**Business**:
- ✅ API key value proposition clear (semantic search, community knowledge)
- ✅ Increased conversions (free to paid via enhancements)
- ✅ Reduced support burden (focused plugins easier to debug)

---

## Implementation Checklist

### Week 1-2: Shared Package
- [ ] Create `packages/shared-py/` structure
- [ ] Move 69 utilities from `hooks/utils/`
- [ ] Create `setup.py` and package metadata
- [ ] Update imports across codebase
- [ ] Test: All commands still work
- [ ] Publish to PyPI (or private registry)

### Week 3: popkit-dev Plugin
- [ ] Create `packages/popkit-dev/` structure
- [ ] Extract commands: dev, git, worktree, routine, next
- [ ] Extract skills: brainstorming, plans, finish, etc.
- [ ] Extract agents: code-reviewer, code-architect, etc.
- [ ] Create plugin.json manifest
- [ ] Add requirements.txt with shared dependency
- [ ] Test: All dev workflows work
- [ ] Document migration notes

### Week 4: Remaining Plugins
- [ ] Create popkit-github (issue, milestone)
- [ ] Create popkit-deploy (deploy)
- [ ] Create popkit-quality (assess, audit, debug, security)
- [ ] Create popkit-research (research, knowledge)
- [ ] Create popkit-core (plugin, stats, privacy, etc.)
- [ ] Test each plugin independently
- [ ] Test plugins together

### Week 5: Meta-Plugin & Integration
- [ ] Create popkit meta-plugin (auto-installs all)
- [ ] Test upgrade path (v0.2.5 → v1.0.0)
- [ ] Create migration guide for users
- [ ] Update CLAUDE.md and README
- [ ] Prepare marketplace listings

### Week 6: Documentation & Release
- [ ] Write user migration guide
- [ ] Update all documentation
- [ ] Create release notes
- [ ] Publish to marketplace
- [ ] Announce v1.0.0 release

---

## Open Questions

1. **Skill sharing**: Should we create `@popkit/skills-common` package or duplicate skills?
2. **Versioning**: How do we coordinate releases across 7 packages (shared + 6 plugins)?
3. **Marketplace**: Should meta-plugin be featured, or individual plugins?
4. **API key UI**: Where should users configure API key (each plugin, or centrally)?
5. **Migration tooling**: Do we need a script to help users migrate custom configs?

---

## Next Steps

1. **Review this design** with stakeholders
2. **Create GitHub issues** for each phase (Week 1-6)
3. **Prototype Phase 1** (shared package extraction)
4. **Validate** no functionality regression
5. **Proceed** with plugin extraction

---

## Appendix: Command-to-Plugin Mapping

| Command | Current Location | New Plugin | Shared Skills Needed |
|---------|------------------|------------|----------------------|
| dev | packages/plugin/commands/dev.md | popkit-dev | pop-brainstorming, pop-writing-plans, pop-executing-plans, pop-finish-branch |
| git | packages/plugin/commands/git.md | popkit-dev | pop-finish-branch, pop-code-review |
| worktree | packages/plugin/commands/worktree.md | popkit-dev | pop-worktrees |
| routine | packages/plugin/commands/routine.md | popkit-dev | pop-morning, pop-nightly, pop-routine-optimized |
| next | packages/plugin/commands/next.md | popkit-dev | pop-next-action |
| issue | packages/plugin/commands/issue.md | popkit-github | (none - uses gh CLI) |
| milestone | packages/plugin/commands/milestone.md | popkit-github | (none - uses gh CLI) |
| assess | packages/plugin/commands/assess.md | popkit-quality | pop-assessment-* (6 skills) |
| audit | packages/plugin/commands/audit.md | popkit-quality | pop-assessment-* |
| debug | packages/plugin/commands/debug.md | popkit-quality | pop-systematic-debugging, pop-root-cause-tracing |
| security | packages/plugin/commands/security.md | popkit-quality | pop-security-scan, pop-defense-in-depth |
| deploy | packages/plugin/commands/deploy.md | popkit-deploy | pop-deploy-* (7 deployment skills) |
| research | packages/plugin/commands/research.md | popkit-research | pop-research-capture |
| knowledge | packages/plugin/commands/knowledge.md | popkit-research | pop-knowledge-lookup, pop-pattern-share |
| plugin | packages/plugin/commands/plugin.md | popkit-core | pop-plugin-test |
| stats | packages/plugin/commands/stats.md | popkit-core | (none - reads metrics files) |
| privacy | packages/plugin/commands/privacy.md | popkit-core | (none - config management) |
| account | packages/plugin/commands/account.md | popkit-core | (none - API key management) |
| upgrade | packages/plugin/commands/upgrade.md | popkit-core | pop-upgrade-prompt |
| cache | packages/plugin/commands/cache.md | popkit-core | (none - cache management) |
| bug | packages/plugin/commands/bug.md | popkit-core | pop-bug-reporter |
| cloud | packages/plugin/commands/cloud.md | popkit-core | pop-cloud-signup |
| power | packages/plugin/commands/power.md | popkit-core | pop-power-mode |
| dashboard | packages/plugin/commands/dashboard.md | popkit-core | pop-dashboard |
| workflow-viz | packages/plugin/commands/workflow-viz.md | popkit-core | (none - visualization) |

---

**Document Status**: Ready for review and implementation planning
**Related**: Issue #567, Issue #353, Issue #241
**Next**: Create implementation issues, prototype Phase 1
