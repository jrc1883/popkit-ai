# `/popkit:project reference` Command Test Report

**Date:** 2025-12-30
**Issue:** #471 (validation request)
**Tester:** Claude Code Validation
**Status:** FAILED - Implementation Missing

---

## Executive Summary

The `/popkit:project reference` subcommand is **documented but not implemented**. The command definition exists in `packages/popkit-core/commands/project.md`, but there is no corresponding skill, agent, or implementation code to execute the documented functionality.

**Severity:** HIGH - Documented feature is non-functional
**Impact:** Users attempting to use this command will receive no response or error
**Recommendation:** Either implement the feature or remove the documentation

---

## Test Results

### 1. Command Definition: ✅ PASS

**Location:** `packages/popkit-core/commands/project.md` (lines 112-119)

**Documentation Found:**
```markdown
## reference

Load context from another project in monorepo.

Read workspace config → Load CLAUDE.md, package.json, README → Output to chat.

**Errors:** Not found (show available), Not monorepo (needs workspace config).
```

**Analysis:**
- Command is listed in frontmatter description
- Clear documentation of intended behavior
- Error handling documented
- Expected workflow defined

### 2. Skill Implementation: ❌ FAIL

**Expected:** `packages/popkit-core/skills/pop-project-reference/` or similar
**Found:** None

**Search Results:**
- No `pop-project-reference` skill directory
- No `pop-reference-project` skill directory
- No skill files containing "reference" related to this feature

**Comparison to Other Subcommands:**
- `init` → `pop-project-init/` ✅ EXISTS
- `analyze` → `pop-analyze-project/` ✅ EXISTS
- `embed` → `pop-embed-project/` ✅ EXISTS
- `observe` → No dedicated skill (uses cloud API) ⚠️ DIFFERENT PATTERN
- `board` → No dedicated skill (uses `gh` CLI) ⚠️ DIFFERENT PATTERN
- `reference` → **MISSING** ❌

### 3. Architecture Documentation: ❌ FAIL

**Location:** `packages/popkit-core/commands/project.md` (lines 135-144)

**Current Architecture Table:**
```markdown
| Component | Integration |
|-----------|-------------|
| Init | skills/pop-project-init/ |
| Analysis | skills/pop-analyze-project/ |
| Embed | skills/pop-embed-project/, hooks/utils/embedding_project.py |
| MCP | skills/pop-mcp-generator/, templates/mcp-server/ |
| Board | gh project CLI |
| Observe | packages/cloud/src/routes/projects.ts |
```

**Missing:** No entry for `reference` subcommand

### 4. Example Documentation: ❌ FAIL

**Expected:** `packages/popkit-core/examples/monorepo-reference.md` (mentioned in line 154)
**Found:** None

**Search Results:**
- No `monorepo-reference.md` file exists
- Only 2 example files in `examples/plugin/`: `sync-detect-version.md`, `test-examples.md`

### 5. Utility Module Check: ❌ FAIL

**Searched:** `packages/shared-py/popkit_shared/utils/`
**Found:** No monorepo reference utilities

**Related Utilities Checked:**
- No `monorepo_loader.py`
- No `workspace_parser.py`
- No `project_reference.py`

### 6. Cloud API Endpoint: ❌ FAIL

**Searched:** `packages/cloud/src/routes/`
**Found:** No `/reference` endpoint

**Existing Routes:**
- `projects.ts` - Project metadata and registration
- No reference loading functionality

### 7. Test Coverage: ❌ FAIL

**Expected:** Test definition in `packages/popkit-core/tests/`
**Found:** None

**Search Results:**
- No test files containing "reference"
- No validation for this subcommand

---

## Detailed Analysis

### What Works

1. **Documentation Quality**: The command description is clear and well-structured
2. **Error Handling Design**: Expected error cases are documented
3. **User Experience**: Documented workflow makes sense for monorepo use cases

### What's Broken

1. **No Implementation**: Zero code exists to execute this feature
2. **Missing Architecture Entry**: Not listed in component mapping
3. **Missing Examples**: Referenced example file doesn't exist
4. **No Test Coverage**: No way to validate if implemented

### What's Missing

1. **Skill Directory**: `packages/popkit-core/skills/pop-project-reference/`
2. **Skill Definition**: `SKILL.md` with implementation instructions
3. **Utility Module**: Monorepo workspace parser
4. **Example File**: `monorepo-reference.md`
5. **Test Definition**: Validation test in test suite
6. **Architecture Documentation**: Integration mapping

---

## Implementation Requirements

If this feature is to be implemented, the following components are needed:

### 1. Skill Structure

```
packages/popkit-core/skills/pop-project-reference/
├── SKILL.md                    # Main skill definition
├── scripts/
│   ├── detect_workspace.py     # Detect pnpm/yarn/npm workspace
│   ├── parse_workspace.py      # Parse workspace config
│   └── load_context.py         # Load project files
└── templates/
    └── reference-output.md     # Formatted output template
```

### 2. Key Implementation Logic

**Workspace Detection:**
- Check for `pnpm-workspace.yaml`
- Check for `package.json` with `workspaces` field
- Check for `lerna.json`
- Check for `nx.json`

**Context Loading:**
- Read workspace configuration
- Parse available projects
- If project specified: Load CLAUDE.md, package.json, README.md
- If no project specified: List available projects

**Output Format:**
```markdown
# Project: {name}

## Overview
{package.json description}

## Structure
{directory structure}

## Instructions
{CLAUDE.md content}

## Dependencies
{package.json dependencies}
```

### 3. Error Handling

- **Not a monorepo**: Display helpful message, suggest available commands
- **Project not found**: List available projects in workspace
- **Missing files**: Show what's available, skip missing files gracefully

### 4. Example File

Create `packages/popkit-core/examples/monorepo-reference.md` demonstrating:
- Basic usage: `/popkit:project reference <project-name>`
- Listing projects: `/popkit:project reference`
- Error scenarios

---

## Recommendations

### Option 1: Implement the Feature (Recommended if valuable)

**Effort:** Medium (2-3 hours)
**Priority:** HIGH (documented but non-functional is confusing for users)

**Steps:**
1. Create skill directory structure
2. Implement workspace detection logic
3. Implement context loading
4. Create example file
5. Add architecture documentation entry
6. Add test coverage
7. Update CHANGELOG.md

**Value:**
- Useful for monorepo users (like ElShaddai monorepo)
- Completes documented feature set
- Enables cross-project context sharing

### Option 2: Remove Documentation (If not valuable)

**Effort:** Low (15 minutes)
**Priority:** MEDIUM (prevents user confusion)

**Steps:**
1. Remove `reference` from command description frontmatter
2. Remove `reference` section from project.md
3. Remove mention of `monorepo-reference.md` from examples
4. Update CHANGELOG.md noting removal

**When to Choose:**
- Feature not needed for v1.0.0
- Low usage expectation
- Focus on other priorities

### Option 3: Mark as Planned (Defer to v2.0.0)

**Effort:** Low (10 minutes)
**Priority:** LOW

**Steps:**
1. Add "🚧 Planned for v2.0.0" badge to documentation
2. Create GitHub issue for v2.0.0 milestone
3. Keep documentation as specification

---

## GitHub Issue Update

**Recommended Actions:**

1. **If Issue #471 exists:** Comment with this report and close with resolution:
   - If implementing: Close as "will be fixed by PR #XXX"
   - If removing: Close as "wontfix - feature deferred"
   - If deferring: Close and reopen under v2.0.0 milestone

2. **If Issue #471 doesn't exist:** The issue number may be incorrect or from a different repository

---

## Cross-Reference

**Related Issues:**
- #580 - Plugin Modularization (may have affected this feature)
- #578 - Phase 5 Testing (should have caught this)

**Related Files:**
- `packages/popkit-core/commands/project.md` - Command definition
- `packages/popkit-core/skills/pop-project-init/` - Similar pattern to follow
- `docs/plans/2025-12-20-plugin-modularization-design.md` - Architecture changes

---

## Conclusion

The `/popkit:project reference` command is **documented but completely unimplemented**. This represents a gap in the plugin's feature set that should be addressed before v1.0.0 release.

**Recommended Path:** Implement the feature (Option 1) given:
1. Clear use case for monorepo users
2. Well-defined specification already exists
3. Medium implementation effort
4. Consistent with other project subcommands

**Alternative Path:** If timeline is tight, mark as planned for v2.0.0 (Option 3) to prevent user confusion while preserving the specification.

---

**Test Report Status:** COMPLETE
**Next Steps:** Await decision on implementation vs. removal vs. deferral
