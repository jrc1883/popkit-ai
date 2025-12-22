# PopKit Package Cleanup Plan
**Date**: 2025-12-22
**Purpose**: Consolidate and clarify package structure

---

## Current State (21 Packages - Too Many!)

```
packages/
├── benchmarks
├── cloud
├── cloud-docs
├── docs
├── landing
├── plugin              ← OLD monolithic
├── popkit              ← OLD monolithic (duplicate?)
├── popkit-core         ← NEW foundation
├── popkit-deploy       ← OLD (consolidating)
├── popkit-dev          ← NEW modular
├── popkit-meta         ← Duplicate of suite?
├── popkit-ops          ← NEW modular (consolidates quality+deploy)
├── popkit-quality      ← OLD (consolidating)
├── popkit-research     ← NEW modular
├── popkit-suite        ← NEW meta-plugin
├── semantic-search
├── shared-config
├── shared-config-py
├── shared-py
├── ui
└── universal-mcp
```

---

## Target State (15 Packages - Cleaner!)

### Category 1: Published Plugins (5)
```
packages/
├── popkit-core         → jrc1883/popkit-core
├── popkit-dev          → jrc1883/popkit-dev
├── popkit-ops          → jrc1883/popkit-ops
├── popkit-research     → jrc1883/popkit-research
└── popkit-suite        → jrc1883/popkit-suite
```

### Category 2: Supporting Libraries (3)
```
packages/
├── shared-py           → pip install popkit-shared
├── shared-config       → Internal config utilities
└── shared-config-py    → Python config utilities
```

### Category 3: Infrastructure (7)
```
packages/
├── benchmarks          → Testing framework
├── cloud               → Cloudflare Workers API
├── cloud-docs          → Cloud documentation
├── docs                → General docs
├── landing             → Marketing site
├── semantic-search     → Semantic search feature
├── ui                  → UI components
└── universal-mcp       → MCP server
```

---

## Packages to Remove (6)

### 1. plugin (OLD monolithic)
**Reason**: Replaced by modular plugins (core, dev, ops, research)
**Action**:
```bash
# After confirming new plugins work
git rm -r packages/plugin
git commit -m "chore: remove old monolithic plugin (replaced by modular)"
```

### 2. popkit (OLD monolithic duplicate?)
**Reason**: Appears to be duplicate of `plugin`
**Action**:
```bash
# Check if this is actually used first
ls -la packages/popkit/
# If it's a duplicate, remove it
git rm -r packages/popkit
```

### 3. popkit-deploy (consolidated into popkit-ops)
**Reason**: Deploy commands now in popkit-ops
**Action**:
```bash
# Verify all deploy functionality moved to popkit-ops
git rm -r packages/popkit-deploy
git commit -m "chore: remove popkit-deploy (consolidated into popkit-ops)"
```

### 4. popkit-quality (consolidated into popkit-ops)
**Reason**: Quality/testing commands now in popkit-ops
**Action**:
```bash
# Verify all quality functionality moved to popkit-ops
git rm -r packages/popkit-quality
git commit -m "chore: remove popkit-quality (consolidated into popkit-ops)"
```

### 5. popkit-meta (duplicate of popkit-suite?)
**Reason**: Likely duplicate of popkit-suite
**Action**:
```bash
# Check if different from popkit-suite
diff -r packages/popkit-meta packages/popkit-suite
# If same, remove meta
git rm -r packages/popkit-meta
git commit -m "chore: remove popkit-meta (duplicate of popkit-suite)"
```

### 6. Consider: semantic-search
**Reason**: May be incomplete or experimental
**Action**: Decide if this is:
- Active development → Keep
- Experimental/abandoned → Move to separate repo or delete

---

## Publication Strategy

### Phase 1: Local Testing (Current)
```bash
# Test with local --plugin-dir
claude --plugin-dir ./packages/popkit-core \
      --plugin-dir ./packages/popkit-dev \
      --plugin-dir ./packages/popkit-ops \
      --plugin-dir ./packages/popkit-research
```

### Phase 2: Marketplace Testing (Next)
```bash
# Publish to test marketplace
/popkit:git publish --tag v1.0.0-beta.1

# Users install from marketplace
/plugin install popkit-core@jrc1883/popkit-claude
/plugin install popkit-dev@jrc1883/popkit-claude
/plugin install popkit-ops@jrc1883/popkit-claude
/plugin install popkit-research@jrc1883/popkit-claude
```

### Phase 3: Public Release
```bash
# After beta testing
/popkit:git publish --tag v1.0.0

# Users install suite (all 4 plugins)
/plugin install popkit-suite@jrc1883/popkit-claude
```

---

## Git Subtree Publication Plan

Each modular plugin gets published to its own path in the public repo:

```bash
# Publish popkit-core
git subtree push --prefix=packages/popkit-core \
  plugin-public popkit-core:main

# Publish popkit-dev
git subtree push --prefix=packages/popkit-dev \
  plugin-public popkit-dev:main

# Publish popkit-ops
git subtree push --prefix=packages/popkit-ops \
  plugin-public popkit-ops:main

# Publish popkit-research
git subtree push --prefix=packages/popkit-research \
  plugin-public popkit-research:main

# Publish popkit-suite
git subtree push --prefix=packages/popkit-suite \
  plugin-public popkit-suite:main
```

**OR** publish each to separate public repos:
```
jrc1883/popkit-core
jrc1883/popkit-dev
jrc1883/popkit-ops
jrc1883/popkit-research
jrc1883/popkit-suite
```

---

## Decision: Single Repo vs Multiple Repos

### Option A: Single Public Repo (jrc1883/popkit-claude)
```
jrc1883/popkit-claude/
├── popkit-core/
├── popkit-dev/
├── popkit-ops/
├── popkit-research/
└── popkit-suite/
```

**Pros**:
- One marketplace entry
- Easier version coordination
- Simpler for users (one repo to star/watch)

**Cons**:
- Larger clone size
- Can't version plugins independently

### Option B: Multiple Public Repos (Recommended)
```
jrc1883/popkit-core
jrc1883/popkit-dev
jrc1883/popkit-ops
jrc1883/popkit-research
jrc1883/popkit-suite
```

**Pros**:
- Independent versioning (core v1.2.0, dev v1.5.0)
- Users can install only what they need
- Smaller clone sizes
- Marketplace can list them separately

**Cons**:
- More repos to maintain
- Version coordination harder

**Recommendation**: Option B (separate repos) for maximum flexibility.

---

## Verification Checklist

Before removing old packages:

- [ ] Verify `popkit-core` has all 25 hooks
- [ ] Verify `popkit-ops` has all commands from deploy + quality
- [ ] Verify no code references old packages
- [ ] Test all 4 modular plugins work together
- [ ] Run `/popkit:next` successfully
- [ ] Run `python scripts/validate-orchestration.py`
- [ ] Backup old packages to archive branch (just in case)

---

## Timeline

**Today (2025-12-22)**:
1. ✅ Foundation architecture implemented
2. ⏭️ Test modular plugins work (after restart)
3. ⏭️ Verify old packages can be removed

**This Week**:
1. Remove old/duplicate packages
2. Clean up package structure
3. Update documentation

**Next Week**:
1. Test publication to marketplace
2. Beta testing with clean install
3. Prepare v1.0.0 release

---

## Package Dependency Graph

```
┌─────────────┐
│ popkit-core │ ← Foundation (all hooks)
└──────┬──────┘
       │
       ├─────────┬─────────┬─────────────┐
       │         │         │             │
   ┌───▼───┐ ┌──▼──┐ ┌────▼─────┐ ┌────▼────┐
   │  dev  │ │ ops │ │ research │ │ (future)│
   └───────┘ └─────┘ └──────────┘ └─────────┘

All import from:
   ┌──────────┐
   │shared-py │ ← Python utilities (pip)
   └──────────┘
```

---

## Questions to Answer

1. **Is `packages/popkit` different from `packages/plugin`?**
   - Check contents
   - If duplicate, remove one

2. **Is `packages/popkit-meta` different from `packages/popkit-suite`?**
   - Check contents
   - If duplicate, remove one

3. **What is `packages/semantic-search`?**
   - Active feature in development?
   - Experimental/abandoned?
   - Decide: keep, move, or delete

4. **Publication strategy: Single repo or multiple?**
   - Recommend: Multiple repos for flexibility
   - But need to decide

---

## Next Steps

1. Restart Claude Code with new modular plugins
2. Test everything works
3. Investigate duplicate packages
4. Remove old packages
5. Clean up structure
6. Update documentation
7. Test publication flow

---

**Status**: Ready to clean up after testing
**Impact**: Reduce 21 packages → 15 packages (28% reduction)
**Benefit**: Clearer structure, easier maintenance
