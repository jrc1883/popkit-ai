# GitHub Setup & Versioning Design

**Date:** 2025-12-10
**Status:** Approved

## Overview

This document captures decisions from brainstorming session about PopKit's GitHub setup, versioning strategy, and workflows.

## Decisions

### 1. Branch Strategy: Single-Branch Model

**Decision:** Use `main` as the only branch, delete stale `master` from public repo.

**Rationale:**
- Single developer currently
- Git worktrees provide feature isolation
- Less overhead to manage
- Matches GitHub modern conventions

**Actions:**
- [ ] Delete `master` branch from jrc1883/popkit-claude
- [ ] Optionally rename private repo branch to `main` (low priority)
- [ ] Update publish workflow to always push to `main`

### 2. Versioning Strategy: Roll Back to 0.x

**Decision:** Roll version back from 1.0.0 to 0.1.0.

**Rationale:**
- PopKit is not yet stable
- 1.0 signals "public API stable" which isn't true
- 0.x better communicates "preview" status

**Version Scheme:**
```
0.MAJOR.PATCH

0.1.0 → Initial public preview
0.2.0 → Major feature additions
0.9.0 → Release candidate
1.0.0 → Stable public launch
```

**Actions:**
- [ ] Update plugin.json version to 0.1.0
- [ ] Update marketplace.json version to 0.1.0
- [ ] Update CHANGELOG.md with version rollback note
- [ ] Publish new version to public repo

### 3. GitHub Projects: Full Setup

**Decision:** Create GitHub Project board AND Wiki.

**Project Board Structure:**
| Column | Purpose |
|--------|---------|
| Backlog | Open issues not being worked |
| In Progress | Active work (limit: 3) |
| Review | PRs awaiting review |
| Done | Recently completed |

**Wiki Pages:**
| Page | Content |
|------|---------|
| Home | Quick start guide |
| Commands | All /popkit: commands reference |
| Agents | Agent catalog and usage |
| Contributing | Guidelines for contributors |

**Actions:**
- [ ] Create GitHub Project "PopKit Roadmap"
- [ ] Configure project columns
- [ ] Add existing issues to project
- [ ] Create Wiki home page
- [ ] Create Wiki commands page
- [ ] Create Wiki agents page

### 4. Milestone Restructure

**New Milestones:**
| Milestone | Purpose |
|-----------|---------|
| 0.1.0 | Initial public preview |
| 0.2.0 | GitHub integration polish |
| 0.3.0 | Premium features |
| 1.0.0 | Stable release |

**Actions:**
- [ ] Rename v1.0.0 milestone to 0.1.0
- [ ] Create 0.2.0, 0.3.0 milestones
- [ ] Reassign issues to appropriate milestones

### 5. Repo Structure: Defer

**Decision:** Keep current structure, defer multi-platform decision.

**Current:**
- jrc1883/popkit (private) - Full monorepo
- jrc1883/popkit-claude (public) - Claude plugin only

**Future (when needed):**
- Add jrc1883/popkit-codex, jrc1883/popkit-gemini as separate repos
- Or consolidate into universal jrc1883/popkit

**Actions:**
- None for now

### 6. GitHub Actions: Four Workflows

**Workflows to Add:**

1. **validate-plugin.yml** - Test plugin structure on PR
2. **greetings.yml** - Welcome first-time contributors
3. **stale.yml** - Auto-close inactive issues
4. **release-drafter.yml** - Auto-generate release notes

**Actions:**
- [ ] Create .github/workflows/validate-plugin.yml
- [ ] Create .github/workflows/greetings.yml
- [ ] Create .github/workflows/stale.yml
- [ ] Create .github/workflows/release-drafter.yml

## Implementation Priority

### Phase 1: Quick Fixes (Now)
1. Delete master branch from public repo
2. Update version to 0.1.0
3. Commit and push

### Phase 2: GitHub Setup (Interactive)
1. Create Project board
2. Set up Wiki
3. Restructure milestones

### Phase 3: Workflows
1. Add all four workflows
2. Test with PRs

## Related Issues

- #111 - Multi-Model Foundation (future)
- #112 - Universal MCP Server (future)
- #113 - OpenAI Codex Integration (future)
- #114 - Google Gemini Integration (future)
