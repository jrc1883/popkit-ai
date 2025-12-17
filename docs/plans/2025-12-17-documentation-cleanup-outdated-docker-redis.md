# Documentation Cleanup: Outdated Docker/Redis References

**Date:** 2025-12-17
**Status:** Planning
**Issue:** Multiple files incorrectly state Redis Mode requires Docker

## Problem

PopKit documentation is out of date regarding Power Mode infrastructure:

**Current Reality:**
1. **Native Async Mode** (Claude Code 2.0.64+) - Default, zero setup, 5+ agents
2. **Redis Cloud Mode** (Upstash) - Cloud-hosted, no Docker needed
3. **File-Based Mode** - Legacy fallback, 2 agents sequential

**Documentation Claims (WRONG):**
- "Redis Mode requires Docker"
- "Redis Mode: Full parallel agents (requires Docker)"
- Docker setup instructions presented as primary path

## Impact

- Users think they need Docker to use Power Mode
- Confusing onboarding experience
- Doesn't highlight Native Async Mode as the default
- Outdated migration guides

## Files Requiring Updates

### Critical (User-Facing)

| File | Lines | Issue |
|------|-------|-------|
| `CLAUDE.md` | 335-336 | Main docs say Redis requires Docker |
| `packages/plugin/commands/project.md` | 75, 94, 102, 109, 118 | Multiple Docker requirements |
| `packages/plugin/commands/power.md` | 47, 496, 843 | Mixed messages about Docker |
| `packages/plugin/skills/pop-project-init/SKILL.md` | 365, 368, 380 | Onboarding offers Docker Redis |
| `packages/plugin/skills/pop-power-mode/SKILL.md` | 149 | Redis listed as Docker-dependent |

### Important (Internal Docs)

| File | Issue |
|------|-------|
| `packages/plugin/power-mode/README.md` | Should highlight Native Async first |
| `packages/plugin/power-mode/QUICKSTART.md` | Docker Redis shown as upgrade path |
| `packages/plugin/power-mode/FALLBACK.md` | File mode presented as equal alternative |
| `docs/plans/2025-12-11-native-async-power-mode-design.md` | Should be canonical reference |

### Legacy (Keep for Advanced Users)

| File | Status |
|------|--------|
| `packages/plugin/power-mode/SETUP-REDIS.md` | Mark as "Advanced: Self-Hosted Redis" |
| Docker compose examples | Move to "Advanced Setup" section |

## Proposed Changes

### 1. Update Terminology

**Old:**
- Redis Mode (requires Docker)
- File Mode (simple)

**New:**
- Native Async Mode (default, Claude Code 2.0.64+)
- Cloud Mode (Pro, Upstash hosted)
- Self-Hosted Redis (Advanced, optional Docker)
- File-Based Mode (Legacy fallback)

### 2. Update Priority Order

All docs should present options in this order:
1. **Native Async Mode** (Recommended) - Zero setup
2. **Cloud Mode** (Pro tier) - Scale to 10+ agents
3. **Self-Hosted Redis** (Advanced) - Optional for enterprise
4. **File-Based Mode** (Fallback) - When nothing else available

### 3. Critical File Updates

**CLAUDE.md:**
```markdown
### Power Mode (Multi-Agent Orchestration)

Parallel agent collaboration via `/popkit:power`:
- **Native Async Mode** (Claude Code 2.0.64+): Default, zero setup, 5+ agents via background Task tool
- **Cloud Mode** (Pro tier): Scale to 10+ agents via Upstash Redis
- **Self-Hosted Redis** (Advanced): Optional Docker setup for enterprise use
- **File-Based Mode** (Fallback): Legacy sequential mode when other options unavailable
```

**commands/project.md:**
```markdown
Would you like to set up Power Mode for multi-agent orchestration?
  - Native Async: Zero setup, 5+ parallel agents (Recommended)
  - Cloud Mode: Scale to 10+ agents (Pro tier)
  - Skip: Set up later with /popkit:power init
```

**skills/pop-project-init/SKILL.md:**
```markdown
options:
  - label: "Native Async Mode (Recommended)"
    description: "Zero setup, 5+ parallel agents. Works with Claude Code 2.0.64+"
  - label: "Cloud Mode (Pro)"
    description: "Scale to 10+ agents via Upstash Redis. Requires subscription."
  - label: "Self-Hosted Redis (Advanced)"
    description: "Optional Docker setup for enterprise. You manage infrastructure."
  - label: "Skip for now"
    description: "Configure later with /popkit:power init"
```

### 4. Create Migration Guide

**New file:** `packages/plugin/power-mode/MIGRATION.md`

Contents:
- "If you're using Docker Redis, you can migrate to Native Async or Cloud Mode"
- Step-by-step migration instructions
- What to do with existing docker-compose.yml

## Implementation Plan

1. **Phase 1: Critical User-Facing Docs**
   - Update CLAUDE.md
   - Update commands/project.md
   - Update commands/power.md
   - Update skills/pop-project-init/SKILL.md

2. **Phase 2: Internal Documentation**
   - Update power-mode/README.md
   - Update QUICKSTART.md
   - Add deprecation notices to SETUP-REDIS.md

3. **Phase 3: Archive Legacy**
   - Move Docker compose files to `power-mode/legacy/`
   - Create MIGRATION.md guide
   - Add "Advanced Setup" section for self-hosted Redis

4. **Phase 4: Validate**
   - Search for remaining "requires Docker" references
   - Test onboarding flow with updated prompts
   - Verify all Power Mode paths work correctly

## Search Queries for Validation

After updates, these searches should return zero or only legacy files:

```bash
# Should be zero (except in SETUP-REDIS.md marked as Advanced)
grep -r "requires Docker" packages/plugin/

# Should be zero (except in legacy docs)
grep -r "Redis Mode.*Docker" packages/plugin/

# Should only find Native Async Mode mentions
grep -r "Native Async" packages/plugin/
```

## Success Criteria

- [ ] No user-facing docs mention Docker as requirement
- [ ] Native Async Mode presented as default
- [ ] Cloud Mode clearly labeled as Pro tier
- [ ] Self-hosted Redis marked as "Advanced" (optional)
- [ ] File-Based Mode presented as fallback only
- [ ] Migration guide available for Docker Redis users
- [ ] All Power Mode onboarding flows updated
- [ ] CLAUDE.md accurately reflects current architecture

## Related Issues

This cleanup should be part of:
- v1.0.0 Validation (Issue #224)
- Documentation audit
- Context optimization work (this brainstorming session)

## Notes

- Keep SETUP-REDIS.md but mark as "Advanced: Self-Hosted Redis (Optional)"
- Docker compose files are still valid for enterprise users
- Don't remove functionality, just update documentation priority
