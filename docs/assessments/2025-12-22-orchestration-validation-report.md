# PopKit Orchestration Validation Report
**Date**: 2025-12-22
**Author**: Claude Code Analysis
**Status**: 🔴 CRITICAL ISSUES FOUND

---

## Executive Summary

**Question Asked**: "When I run `/popkit:next`, does it work programmatically through PopKit's orchestration (hooks → agents → skills) OR does the LLM just 'figure it out' by reading markdown files?"

**Answer**: **HYBRID - Partially Programmatic, Partially LLM Improvisation**

### Critical Findings

1. ✅ **Commands and skills load correctly** (32 skills found)
2. ✅ **Some modular plugins have hooks** (popkit-ops: 69, popkit-research: 69)
3. ❌ **Hooks are duplicated** (not centralized)
4. 🚨 **Invalid plugin dependencies declared** (`popkit-shared` doesn't exist)
5. ❌ **Execution path is NOT fully programmatic** (manual bash commands, no output style templates)

---

## Validation Results

### Test 1: Modular Plugin Hooks

| Plugin | Hooks | Status |
|--------|-------|--------|
| popkit-dev | 0 | ❌ NO HOOKS |
| popkit-ops | 69 | ✅ HAS HOOKS (duplicated) |
| popkit-research | 69 | ✅ HAS HOOKS (duplicated) |
| popkit-core | 0 | ❌ NO HOOKS |
| **plugin (monolithic)** | **25** | ✅ Original source |

**Analysis**:
- popkit-ops and popkit-research contain **duplicate copies** of all 69 utils + hooks
- This violates DRY principle (maintenance nightmare)
- popkit-dev has NO hooks (cannot orchestrate development workflows!)

### Test 2: Shared Python Package

| Component | Status |
|-----------|--------|
| shared-py utilities | ✅ 69 modules |
| popkit_shared importable | ✅ YES |

**Analysis**: The Python shared package EXISTS and works, but the plugin reference is wrong.

### Test 3: Plugin Dependencies

| Plugin | Dependency | Problem |
|--------|------------|---------|
| popkit-dev | popkit-shared >=0.1.0 | 🚨 Doesn't exist |
| popkit-ops | None | ✅ OK |
| popkit-research | None | ✅ OK |
| popkit-core | popkit-shared >=0.1.0 | 🚨 Doesn't exist |

**Analysis**:
- Claude Code **does NOT support plugin dependencies** (documented in architecture)
- Declaring them does nothing except create confusion
- `popkit-shared` as a PLUGIN doesn't exist (only Python package exists)

### Test 4: Skill Distribution

| Plugin | Skills | Examples |
|--------|--------|----------|
| popkit-dev | 12 | pop-brainstorming, pop-next-action, pop-session-capture |
| popkit-ops | 7 | pop-systematic-debugging, pop-assessment-* |
| popkit-research | 3 | pop-research-capture, pop-knowledge-lookup |
| popkit-core | 10 | pop-analyze-project, pop-bug-reporter, pop-power-mode |
| **TOTAL** | **32** | All skills loading correctly ✅ |

---

## Execution Path Analysis: /popkit:next

### Expected Flow (Programmatic)

```
User: /popkit:next
    ↓
[Command Loader] Loads commands/next.md
    ↓
[Skill Invocation] Invokes pop-next-action skill
    ↓
[Hook: pre-tool-use.py] Captures skill invocation, tracks state
    ↓
[Skill Execution] Auto-runs bash commands via templates
    ↓
[Agent Coordination] Uses priority-scorer, research-branch-detector
    ↓
[Output Style] Formats via output-styles/next-action-report.md
    ↓
[Hook: post-tool-use.py] Logs execution metrics, measures context
    ↓
Result: Structured recommendations with execution trail
```

### Actual Flow (What Happened)

```
User: /popkit:next
    ↓
[Command Loader] ✅ Loads commands/next.md
    ↓
[Skill Invocation] ✅ Invokes pop-next-action skill (PROGRAMMATIC)
    ↓
[Hook: pre-tool-use.py] ❌ NO HOOK FIRED (popkit-dev has no hooks!)
    ↓
[Skill Execution] ❌ LLM manually wrote bash commands
    ↓
[Agent Coordination] ❌ LLM manually analyzed, no agents used
    ↓
[Output Style] ❌ LLM manually formatted markdown
    ↓
[Hook: post-tool-use.py] ❌ NO HOOK FIRED
    ↓
Result: ✅ Correct output, ❌ Wrong process
```

**Verdict**: The LLM is "smart enough" to fake the orchestration by reading markdown files and executing the intent, but it's NOT using the programmatic workflow system.

---

## Root Cause Analysis

### Issue #1: Architectural Confusion

**Problem**: The architecture doc says "no plugin dependencies" but plugins declare them anyway.

**Evidence**:
```json
// packages/popkit-dev/.claude-plugin/plugin.json
"dependencies": {
  "popkit-shared": ">=0.1.0"  // ❌ Doesn't exist as a plugin
}
```

**Impact**:
- Dependencies never resolve
- Shared code never loads from supposed dependency
- Developers think dependencies work (they don't)

### Issue #2: Hook Distribution Confusion

**Problem**: Hooks are duplicated in some plugins, missing in others, with no clear strategy.

**Evidence**:
- popkit-dev: 0 hooks (development workflows can't orchestrate!)
- popkit-ops: 69 hooks (duplicate of all utils)
- popkit-research: 69 hooks (duplicate of all utils)
- popkit-core: 0 hooks (core features can't orchestrate!)

**Impact**:
- Maintenance nightmare (change must be made 3x)
- Inconsistent orchestration (some plugins work, others don't)
- Massive duplication (69 files × 2 = 138 duplicates!)

### Issue #3: Python Package vs Plugin Confusion

**Two Different Things**:

| Name | Type | Purpose | Status |
|------|------|---------|--------|
| `shared-py` | Python package | Utilities for hooks to import | ✅ EXISTS |
| `popkit-shared` | Claude Code plugin | Shared plugin dependency | ❌ DOESN'T EXIST |

**Problem**: Plugin.json references `popkit-shared` (plugin) but code imports from `popkit_shared` (Python package). These are DIFFERENT and the architecture confuses them.

---

## Architecture Options

### Option A: Duplicate Hooks (Current State - BROKEN)

**Structure**:
```
packages/
├── shared-py/              # Python utilities
├── popkit-dev/
│   ├── hooks/              # ALL 69 hook files (DUPLICATE)
│   └── skills/
├── popkit-ops/
│   ├── hooks/              # ALL 69 hook files (DUPLICATE)
│   └── skills/
├── popkit-research/
│   ├── hooks/              # ALL 69 hook files (DUPLICATE)
│   └── skills/
└── popkit-core/
    ├── hooks/              # ALL 69 hook files (DUPLICATE)
    └── skills/
```

**Pros**: Each plugin is truly independent
**Cons**:
- 69 files × 4 plugins = 276 duplicates
- Change one hook = update 4 places
- 4x the testing burden
- 4x the disk space

**Status**: ❌ UNSUSTAINABLE

---

### Option B: Foundation Plugin (RECOMMENDED)

**Structure**:
```
packages/
├── shared-py/              # Python utilities (pip install -e)
├── popkit-core/            # FOUNDATION (REQUIRED)
│   ├── hooks/              # ALL 25 hooks (SINGLE SOURCE)
│   └── commands/           # Core commands (account, stats, etc.)
├── popkit-dev/             # Feature plugin (NO hooks)
│   ├── skills/
│   ├── agents/
│   └── commands/
├── popkit-ops/             # Feature plugin (NO hooks)
│   ├── skills/
│   └── agents/
└── popkit-research/        # Feature plugin (NO hooks)
    ├── skills/
    └── agents/
```

**Installation**:
```bash
# Users MUST install core first
claude --plugin-dir ./packages/popkit-core \
      --plugin-dir ./packages/popkit-dev \
      --plugin-dir ./packages/popkit-ops \
      --plugin-dir ./packages/popkit-research
```

**Pros**:
- Single source of truth for hooks
- Easy maintenance (change once, affects all)
- Clear dependency model ("install core first")
- Hooks can detect ALL plugin events (cross-plugin orchestration)

**Cons**:
- Requires users to install foundation plugin
- Not 100% independent plugins
- Need clear documentation

**Status**: ✅ RECOMMENDED

---

### Option C: Skills-Only Architecture (Future)

**Structure**:
```
packages/
├── shared-py/              # Python utilities + hooks
├── popkit-dev/             # Commands + Skills (NO hooks)
├── popkit-ops/             # Commands + Skills (NO hooks)
├── popkit-research/        # Commands + Skills (NO hooks)
└── popkit-core/            # Commands + Skills (NO hooks)
```

**Hook Loading**: System-wide hooks installed separately (not per-plugin)

**Installation**:
```bash
# Install shared hooks once
pip install -e packages/shared-py

# Then load any plugins
claude --plugin-dir ./packages/popkit-dev
```

**Pros**:
- Truly independent plugins
- Hooks are system-wide (loaded once)
- Maximum flexibility

**Cons**:
- Requires pip install step
- Claude Code may not support system-wide hooks
- Experimental/unproven

**Status**: ⏸️ FUTURE EXPLORATION

---

## Immediate Action Items

### Priority 1: Fix Dependency Declarations 🚨

```bash
# Remove from popkit-dev/.claude-plugin/plugin.json
{
  "dependencies": {
    "popkit-shared": ">=0.1.0"  // ❌ DELETE THIS
  }
}

# Remove from popkit-core/.claude-plugin/plugin.json
{
  "dependencies": {
    "popkit-shared": ">=0.1.0"  // ❌ DELETE THIS
  }
}
```

**Why**: Claude Code doesn't support dependencies, so these do nothing except mislead.

---

### Priority 2: Choose Hook Distribution Strategy

**Decision Needed**: Option A (duplicate) vs Option B (foundation) vs Option C (system-wide)

**Recommendation**: **Option B (Foundation Plugin)** because:
1. Single source of truth
2. Easy maintenance
3. Works with Claude Code's model
4. Clear user mental model ("install core first")

---

### Priority 3: Install Shared Python Package

```bash
cd packages/shared-py
pip install -e .
```

**Why**: Hooks need to import utilities from `popkit_shared` package.

---

### Priority 4: Validate Hooks Fire

After fixing dependencies and choosing architecture, test hook execution:

```bash
# Set debug mode
export POPKIT_DEBUG=1

# Run a command
/popkit:next

# Check if hooks fired
cat ~/.claude/logs/*.jsonl | grep "hook_fired"
```

---

## Repo Structure Decision

### Question: "Should PopKit be standalone or in ElShaddai monorepo?"

**Current State**: PopKit is IN ElShaddai monorepo at `apps/popkit/`

**Options**:

#### Option 1: Keep in Monorepo (RECOMMENDED for development)

**Structure**:
```
elshaddai/
└── apps/
    └── popkit/               # Development happens here
        ├── packages/
        │   ├── popkit-dev/
        │   ├── popkit-ops/
        │   ├── popkit-research/
        │   └── popkit-core/
        └── scripts/
            └── publish-to-marketplace.sh  # Publishes to jrc1883/popkit-claude
```

**Workflow**:
1. Develop in `elshaddai/apps/popkit/`
2. Test with `claude --plugin-dir ./packages/popkit-*`
3. When ready, run `publish-to-marketplace.sh`
4. Script does `git subtree push` to public repo

**Pros**:
- Easy development (all your apps in one place)
- Can dogfood PopKit while building it
- Easy to test across ElShaddai apps
- Single git history

**Cons**:
- Large monorepo clone for contributors
- Coupled to ElShaddai release cycle

---

#### Option 2: Standalone Repo (RECOMMENDED for distribution)

**Structure**:
```
jrc1883/popkit/               # Public repo (marketplace)
├── packages/
│   ├── popkit-dev/
│   ├── popkit-ops/
│   ├── popkit-research/
│   └── popkit-core/
└── .github/
    └── workflows/
        └── publish-to-npm.yml  # Auto-publish on tag
```

**Workflow**:
1. Develop in `elshaddai/apps/popkit/`
2. When ready to release, run `./scripts/sync-to-standalone.sh`
3. Script clones `jrc1883/popkit`, copies packages, commits, pushes
4. GitHub Actions auto-publishes to marketplace

**Pros**:
- Clean contributor experience
- Easier for non-ElShaddai users to clone
- Can version independently

**Cons**:
- Two repos to maintain
- Sync complexity

---

#### Option 3: Both (HYBRID - CURRENT ACTUAL STATE)

**Keep development in monorepo, publish to standalone:**

```
Development:  elshaddai/apps/popkit/  (PRIVATE)
Distribution: jrc1883/popkit-claude   (PUBLIC)
```

**This is what you're already doing!**

Your architecture doc mentions:
> The public repo (`jrc1883/popkit-claude`) contains **only declarative content**:
> - Commands (markdown specs)
> - Skills (marketing stubs for premium, full prompts for free)
> - Agents (definitions and routing)

**Workflow** (already implemented):
```bash
# Manual publish from CLI
/popkit:git publish                    # Push current state
/popkit:git publish --tag v1.0.0       # With version tag

# Or via GitHub Actions
# Go to Actions → "Publish Plugin" → Run workflow
```

**Pros**:
- Best of both worlds
- Development stays in ElShaddai
- Distribution is clean public repo
- Already working!

**Cons**:
- Complexity of maintaining sync
- Must remember to publish

**Status**: ✅ THIS IS YOUR CURRENT MODEL - KEEP IT

---

## Recommendation: Hybrid Model with Foundation Architecture

### Proposed Structure

**Development** (elshaddai/apps/popkit/):
```
packages/
├── shared-py/              # Utilities (pip install -e)
├── popkit-core/            # Foundation (25 hooks)
├── popkit-dev/             # Feature plugin
├── popkit-ops/             # Feature plugin
└── popkit-research/        # Feature plugin
```

**Distribution** (jrc1883/popkit-claude):
```
# Git subtree split each package:
popkit-core/       → npm: @popkit/core
popkit-dev/        → npm: @popkit/dev
popkit-ops/        → npm: @popkit/ops
popkit-research/   → npm: @popkit/research
```

**User Installation**:
```bash
/plugin install popkit-core          # Foundation (REQUIRED)
/plugin install popkit-dev           # Development workflows
/plugin install popkit-ops           # Operations/QA
/plugin install popkit-research      # Knowledge management
```

**OR** (all at once):
```bash
/plugin install popkit-suite         # Meta-package (installs all 4)
```

---

## Next Steps

1. ✅ **Validate orchestration** (DONE - this report)
2. ⏭️ **Remove invalid dependency declarations** (`popkit-shared`)
3. ⏭️ **Choose hook strategy** (Foundation plugin recommended)
4. ⏭️ **Implement chosen strategy**
5. ⏭️ **Test full orchestration**
6. ⏭️ **Document for users**
7. ⏭️ **Publish to marketplace**

---

## Testing Checklist

After implementing fixes, validate these work programmatically:

- [ ] `/popkit:next` - Hooks fire, agents coordinate, output style applies
- [ ] `/popkit:dev work #42` - Issue-driven development with state tracking
- [ ] `/popkit:routine morning` - Health check with measurement hooks
- [ ] `/popkit:git commit` - Pre-commit hooks validate, post-commit logs
- [ ] `/popkit:assess anthropic` - Assessment agents coordinate
- [ ] Hook execution captured in `~/.claude/logs/*.jsonl`
- [ ] Skills can invoke other skills (skill_context.py)
- [ ] Agent coordination via power-mode
- [ ] Output styles apply correctly
- [ ] Metrics captured and reportable

---

## Conclusion

**The Good**:
- Commands and skills load correctly
- Shared Python package exists and works
- Some plugins have hooks (but duplicated)

**The Bad**:
- Execution is NOT fully programmatic (LLM compensates)
- Invalid dependency declarations confuse architecture
- Hooks are duplicated (maintenance nightmare)
- popkit-dev has NO hooks (dev workflows can't orchestrate!)

**The Fix**:
1. Remove invalid `popkit-shared` dependencies
2. Implement Foundation Plugin architecture (popkit-core with all hooks)
3. Keep hybrid repo model (develop in monorepo, publish to standalone)
4. Test full orchestration with validation checklist

**Timeline**:
- Immediate: Remove dependency declarations (5 min)
- Short-term: Implement foundation architecture (2-4 hours)
- Medium-term: Full testing and validation (1 day)
- Long-term: Publish to marketplace (when ready)

---

**Generated**: 2025-12-22
**Tool**: scripts/validate-orchestration.py
**Session**: Orchestration validation analysis
