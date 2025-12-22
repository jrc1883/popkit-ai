# Merge popkit-github into popkit-dev
**Design Document | v1.0 | 2025-12-21**

---

## Executive Summary

**Decision:** Merge `popkit-github` plugin back into `popkit-dev` plugin, reducing total plugin count from 6 to 5 focused workflow plugins.

**Rationale:** GitHub operations (issues, PRs, milestones) are integral to modern development workflows, not separate project management concerns. The artificial split creates confusion and breaks natural workflow continuity.

**Impact:**
- Plugin count: 6 → 5
- popkit-dev: 5 commands → 7 commands
- User confusion: Eliminated ("where do I manage issues?")
- Workflow coherence: Improved (Issues → Dev → PR → Merge → Close)

---

## Problem Statement

### Current State (Post-Modularization)

After completing Phase 3 of Epic #580, we have:

**popkit-dev** (5 commands):
- `/popkit:dev` - 7-phase feature development
- `/popkit:git` - commit, push, **pr**, review, ci, **release**
- `/popkit:worktree` - Branch isolation
- `/popkit:routine` - Morning/nightly checks
- `/popkit:next` - Recommendations

**popkit-github** (2 commands):
- `/popkit:issue` - Issue CRUD operations
- `/popkit:milestone` - Milestone tracking

### The Problem: Artificial Separation

1. **Workflow Fragmentation**
   - User flow: `/popkit:issue create` → `/popkit:dev work #N` → `/popkit:git pr` → `/popkit:issue close`
   - Switches between 2 plugins for one coherent workflow
   - Mental overhead: "Is this dev or GitHub?"

2. **Command Overlap**
   - `/popkit:dev work #N` → Starts from GitHub issue
   - `/popkit:git pr` → Creates GitHub pull request
   - `/popkit:git release` → Creates GitHub release
   - `/popkit:issue view` → Views GitHub issue

3. **GitHub Lock-In Already Exists**
   - `popkit-dev` already depends on `gh` CLI for PRs
   - Git operations require GitHub for remote
   - No GitLab/Bitbucket support anyway

4. **User Confusion**
   - "Should I use `/popkit:dev work #123` or `/popkit:issue view #123`?"
   - "Where do I close an issue after merging a PR?"
   - "Is milestone tracking part of development?"

### Why Original Split Happened

Looking at `docs/plans/2025-12-20-plugin-modularization-design.md`:

> **popkit-github** | issue, milestone | GitHub project management | gh CLI operations

**Reasoning** (from design doc):
1. Separation of concerns - Dev workflows vs project management
2. Support non-GitHub users (GitLab, Bitbucket)
3. Minimal plugin - "just gh CLI wrapper"

**Why These Reasons Are Weak:**
1. Modern development **IS** project management
2. No GitLab/Bitbucket support exists (Git operations already GitHub-specific)
3. "Just a wrapper" isn't architectural justification

---

## Proposed Solution

### Merge Architecture

**New popkit-dev structure:**
```
packages/popkit-dev/
├── .claude-plugin/
│   ├── plugin.json          # Updated: 7 commands (was 5)
│   └── marketplace.json     # Updated description
├── commands/
│   ├── dev.md               # Existing
│   ├── git.md               # Existing
│   ├── issue.md             # ← MOVED from popkit-github
│   ├── milestone.md         # ← MOVED from popkit-github
│   ├── worktree.md          # Existing
│   ├── routine.md           # Existing
│   └── next.md              # Existing
├── skills/                  # Existing (9 skills)
├── agents/                  # Existing (5 agents)
├── requirements.txt         # No change (already has popkit-shared)
├── README.md                # Updated: 7 commands
└── CHANGELOG.md             # New entry: v0.2.0 - Merged GitHub features
```

### Command Integration

| Command | Source | Status |
|---------|--------|--------|
| `/popkit:dev` | popkit-dev | No change |
| `/popkit:git` | popkit-dev | No change |
| `/popkit:worktree` | popkit-dev | No change |
| `/popkit:routine` | popkit-dev | No change |
| `/popkit:next` | popkit-dev | No change |
| `/popkit:issue` | **popkit-github** | **MOVE** |
| `/popkit:milestone` | **popkit-github** | **MOVE** |

### Updated Plugin Description

**Before:**
> Development workflow plugin - feature development, git operations, and daily routines

**After:**
> Complete development workflow plugin - feature development, git operations, GitHub management, and daily routines

**Keywords:** development, workflow, git, github, issues, milestones, pr, feature, routine

---

## Implementation Plan

### Phase 1: Pre-Merge Validation ✅

- [x] Verify popkit-github has no Python code (only markdown files)
- [x] Verify dependencies are identical (both use popkit-shared)
- [x] Review command files for conflicts (none found)
- [x] Check Epic #580 status (Issue #572 CLOSED, plugin exists)

### Phase 2: File Operations

**Steps:**
1. Copy command files:
   ```bash
   cp packages/popkit-github/commands/issue.md packages/popkit-dev/commands/
   cp packages/popkit-github/commands/milestone.md packages/popkit-dev/commands/
   ```

2. Update `packages/popkit-dev/.claude-plugin/plugin.json`:
   ```json
   "commands": [
     {"name": "dev", "description": "...", "path": "commands/dev.md"},
     {"name": "git", "description": "...", "path": "commands/git.md"},
     {"name": "issue", "description": "GitHub issue management", "path": "commands/issue.md"},
     {"name": "milestone", "description": "Milestone tracking", "path": "commands/milestone.md"},
     {"name": "worktree", "description": "...", "path": "commands/worktree.md"},
     {"name": "routine", "description": "...", "path": "commands/routine.md"},
     {"name": "next", "description": "...", "path": "commands/next.md"}
   ]
   ```

3. Update `packages/popkit-dev/README.md`:
   - Command count: 5 → 7
   - Add issue/milestone sections
   - Update feature list

4. Update `packages/popkit-dev/CHANGELOG.md`:
   ```markdown
   ## [0.2.0] - 2025-12-21
   ### Added
   - Merged popkit-github plugin for unified workflow
   - `/popkit:issue` command - GitHub issue management
   - `/popkit:milestone` command - Milestone tracking

   ### Changed
   - Renamed from "Development workflows" to "Complete development workflow"
   - Updated description to include GitHub management
   ```

5. Delete `packages/popkit-github/` directory

### Phase 3: Documentation Updates

**Files to update:**

1. **`docs/plans/2025-12-20-plugin-modularization-design.md`**
   - Update plugin table (6 → 5 plugins)
   - Remove popkit-github row
   - Update popkit-dev row with 7 commands
   - Add note about merge decision

2. **Root `CLAUDE.md`**
   - Update plugin count in auto-generated sections
   - Update `packages/popkit-dev/` description

3. **`packages/popkit/CLAUDE.md`** (if exists)
   - Update modularization status

4. **Epic #580 body (Issue #580)**
   - Update plugin table
   - Add note about merge
   - Update success metrics

### Phase 4: Testing & Validation

**Test checklist:**
- [ ] Install popkit-dev: `/plugin install popkit-dev@file:./packages/popkit-dev`
- [ ] Verify 7 commands available
- [ ] Test `/popkit:issue list` works
- [ ] Test `/popkit:milestone list` works
- [ ] Test `/popkit:dev work #N` still works
- [ ] Test `/popkit:git pr` still works
- [ ] Verify no errors in Claude Code console
- [ ] Check context window usage (should be same or lower)

### Phase 5: Issue Tracking

**Create new issue:**
```markdown
Title: [Phase 3.5] Merge popkit-github into popkit-dev

Labels: P1-high, phase:now, Epic-580

Body:
## Overview

Merge popkit-github plugin back into popkit-dev for unified development workflow.

**Design Document:** `docs/plans/2025-12-21-merge-popkit-github-into-dev.md`

## Rationale

GitHub operations are integral to development workflows, not separate concerns. The split creates confusion and breaks workflow continuity.

## Scope

- Move 2 commands (issue, milestone) from popkit-github to popkit-dev
- Delete popkit-github package
- Update all documentation
- Update Epic #580 to reflect 5 plugins (not 6)

## Acceptance Criteria

- [ ] Commands moved to popkit-dev
- [ ] popkit-github deleted
- [ ] Documentation updated (design doc, CLAUDE.md, Epic #580)
- [ ] All tests pass
- [ ] Context window usage unchanged

## Related

- Parent: Epic #580 (Plugin Modularization)
- Supersedes: Issue #572 (Extract popkit-github)
```

**Update Epic #580:**
- Adjust plugin count in overview
- Update plugin breakdown table
- Add note about architecture pivot
- Keep Phase 3 Issue #572 closed (work was done, just reversed)

---

## Impact Analysis

### Benefits

1. **Workflow Coherence**
   - Single plugin for entire development lifecycle
   - Issues → Dev → PR → Merge → Close (all in one place)

2. **Reduced Cognitive Load**
   - No "which plugin?" questions
   - Clear mental model: "popkit-dev does development"

3. **Simpler Architecture**
   - 5 focused plugins (not 6)
   - Fewer dependencies to manage
   - Easier maintenance

4. **Better User Experience**
   - Natural command discovery
   - Consistent naming (`/popkit:dev`, `/popkit:issue`, `/popkit:git`)
   - One plugin to install for development

### Tradeoffs

1. **Larger Plugin**
   - 7 commands (was 5)
   - But still focused on development lifecycle
   - Context window: ~15k tokens (acceptable)

2. **GitHub Lock-In**
   - Explicit GitHub dependency
   - But already existed via `/popkit:git pr`
   - No GitLab/Bitbucket support anyway

3. **Naming Clarity**
   - "popkit-dev" might not suggest GitHub features
   - Mitigated by good documentation
   - Description updated to mention GitHub

### Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Commands don't work after merge | Low | High | Thorough testing checklist |
| Context window increase | Low | Medium | Measure before/after |
| User confusion about deleted plugin | Medium | Low | Clear changelog, migration notes |
| Breaking existing workflows | Low | High | Maintain all command signatures |

---

## Future Workflow System (Phase 7)

This merge **enables** future workflow templates:

```
popkit-dev/
├── workflows/
│   ├── github-flow/      ← Default (current commands)
│   ├── gitflow/          ← Feature/develop/release
│   ├── trunk-based/      ← Main + feature flags
│   ├── bmad/             ← Build-Measure-Analyze-Deploy
│   ├── spec-driven/      ← PRD → Design → Impl
│   └── tdd/              ← Test → Red → Green → Refactor
└── commands/             ← Route to active workflow
```

**User customization:**
```bash
/popkit:dev init --workflow github-flow  # Default
/popkit:dev init --workflow bmad         # Lean startup
/popkit:dev init --workflow spec-driven  # Enterprise
```

Each workflow template customizes:
- Command behavior
- Required tools (issues, PRs, milestones, CI/CD)
- Workflow phases
- Success criteria

**Example:** BMAD workflow
- `/popkit:dev build` → MVP implementation
- `/popkit:dev measure` → Analytics review
- `/popkit:dev analyze` → Data-driven decisions
- `/popkit:dev deploy` → Ship iteration

---

## Timeline

**Total Duration:** 1-2 hours

| Phase | Duration | Task |
|-------|----------|------|
| 1 | 15 min | Pre-merge validation ✅ |
| 2 | 20 min | File operations |
| 3 | 30 min | Documentation updates |
| 4 | 20 min | Testing & validation |
| 5 | 15 min | Issue tracking |

---

## Success Metrics

- [ ] All 7 commands work identically
- [ ] popkit-github directory deleted
- [ ] Documentation reflects 5 plugins (not 6)
- [ ] Epic #580 updated
- [ ] No context window regression
- [ ] Zero functionality loss
- [ ] User feedback: "makes more sense now"

---

## Appendix: File Inventory

### Files Being Moved

| File | Source | Destination |
|------|--------|-------------|
| `issue.md` | `packages/popkit-github/commands/` | `packages/popkit-dev/commands/` |
| `milestone.md` | `packages/popkit-github/commands/` | `packages/popkit-dev/commands/` |

### Files Being Updated

| File | Change |
|------|--------|
| `packages/popkit-dev/.claude-plugin/plugin.json` | Add 2 commands |
| `packages/popkit-dev/README.md` | Update command list, features |
| `packages/popkit-dev/CHANGELOG.md` | Add v0.2.0 entry |
| `docs/plans/2025-12-20-plugin-modularization-design.md` | Update plugin table |
| Root `CLAUDE.md` | Update plugin count |
| Epic #580 body | Update plugin breakdown |

### Directory Being Deleted

```
packages/popkit-github/         ← DELETE ENTIRE DIRECTORY
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── commands/
│   ├── issue.md
│   └── milestone.md
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

---

**Decision Authority:** Architecture Lead (user approved)
**Implementation:** Claude Code AI Assistant
**Review:** Post-implementation validation
**Rollback Plan:** Git revert (all changes in single commit)
