# PopKit Installation Fix Guide

## Problems Identified

Based on the screenshots and analysis, three distinct issues were found:

### 1. **Marketplace Name Mismatch** ✅ FIXED
- **Problem:** marketplace.json said `popkit-marketplace`, but workflow said `popkit-claude`
- **Solution:** Changed marketplace.json to `popkit-claude` for consistency
- **Impact:** All installation commands now use `@popkit-claude`

### 2. **Missing Marketplace Registration** ⚠️ USER ACTION REQUIRED
- **Problem:** Marketplace not added to Claude Code
- **Error:** "Plugin 'X' not found in marketplace 'popkit-marketplace'"
- **Solution:** Must run `/plugin marketplace add jrc1883/popkit-claude` first

### 3. **MCP Server Errors** ℹ️ SEPARATE ISSUE
- **Problem:** "4 MCP servers failed"
- **Analysis:** Unrelated to PopKit (PopKit doesn't configure MCP servers)
- **Action:** Check `/mcp` tab in Claude Code for details

---

## Step-by-Step Installation Fix

### Step 1: Clean Uninstall

Remove all existing PopKit plugins:

```bash
/plugin uninstall popkit
/plugin uninstall popkit-core
/plugin uninstall popkit-dev
/plugin uninstall popkit-ops
/plugin uninstall popkit-research
/plugin uninstall popkit-suite
```

### Step 2: Restart Claude Code

Close and restart Claude Code to clear all plugin caches.

### Step 3: Add PopKit Marketplace

This is the missing step that was causing the errors:

```bash
/plugin marketplace add jrc1883/popkit-claude
```

You should see a confirmation that the marketplace was added.

### Step 4: Install Plugins

Now install from the marketplace:

**Option A: Complete Suite (Recommended)**
```bash
/plugin install popkit-suite@popkit-claude
```

**Option B: Individual Plugins**
```bash
/plugin install popkit-core@popkit-claude
/plugin install popkit-dev@popkit-claude
/plugin install popkit-ops@popkit-claude
/plugin install popkit-research@popkit-claude
```

### Step 5: Restart Claude Code Again

Restart to load the newly installed plugins.

### Step 6: Verify Installation

Run the plugin command to check status:

```bash
/plugin
```

You should see:
- ✅ popkit-core v1.0.0-beta.3
- ✅ popkit-dev v1.0.0-beta.3
- ✅ popkit-ops v1.0.0-beta.3
- ✅ popkit-research v1.0.0-beta.3

All versions should be **1.0.0-beta.3** (not v0.2.0 as shown in the screenshot).

---

## Alternative: Local Development Installation

If you're developing locally and want to test changes immediately, skip the marketplace and install directly:

```bash
# From repository root (C:\Users\Josep\popkit-claude)
/plugin install ./packages/popkit-core
/plugin install ./packages/popkit-dev
/plugin install ./packages/popkit-ops
/plugin install ./packages/popkit-research
```

Local installations take precedence over marketplace installations.

---

## Verification Checklist

After installation, verify everything works:

- [ ] All plugins show version **1.0.0-beta.3**
- [ ] No "plugin not found" errors
- [ ] Commands available under `/popkit:` namespace
- [ ] Run `/popkit:next` to test basic functionality
- [ ] Run `/popkit:stats` to verify plugin stats tracking

---

## Changes Made to Repository

All marketplace references have been updated:

1. ✅ `.claude-plugin/marketplace.json` - Changed name to `popkit-claude`
2. ✅ `CLAUDE.md` - Updated installation instructions with marketplace add step
3. ✅ `README.md` - Updated Quick Start with marketplace add step
4. ✅ All package READMEs - Changed `@popkit-marketplace` → `@popkit-claude`
5. ✅ All docs - Changed `@popkit-marketplace` → `@popkit-claude`
6. ✅ All skills and Python utilities - Changed `@popkit-marketplace` → `@popkit-claude`
7. ✅ GitHub workflows and templates - Changed `@popkit-marketplace` → `@popkit-claude`

**Total files updated:** 22+ files across the repository

---

## Documentation Resources

Updated documentation locations:

- [CLAUDE.md](../CLAUDE.md) - Complete developer guide
- [README.md](../README.md) - User-facing documentation
- [CHANGELOG.md](../CHANGELOG.md) - Version history
- Package READMEs in `packages/*/README.md`

---

## Need Help?

If you still encounter issues:

1. Check Claude Code version: Must be **v2.0.71+** for full compatibility
2. Verify marketplace was added: `/plugin marketplace list`
3. Check plugin errors tab in Claude Code
4. Review logs for detailed error messages
5. Try local installation method as fallback

---

---

## Update: popkit-suite Removed (2026-01-08)

**popkit-suite has been removed** from PopKit as of 2026-01-08 because:
- Claude Code doesn't support plugin dependency management
- The "suite" plugin couldn't automatically install other plugins
- It was non-functional and misleading to users

**Users should install the 4 core plugins individually:**
```bash
/plugin install popkit-core@popkit-claude
/plugin install popkit-dev@popkit-claude
/plugin install popkit-ops@popkit-claude
/plugin install popkit-research@popkit-claude
```

---

**Last Updated:** 2026-01-08
**PopKit Version:** 1.0.0-beta.3 (4 plugins)
**Marketplace ID:** popkit-claude
**Repository:** https://github.com/jrc1883/popkit-claude
