# Documentation & README Overhaul Design

**Date:** 2025-12-12
**Issue:** #184
**Status:** Design Complete

## Executive Summary

Comprehensive redesign of PopKit documentation with focus on:
1. **Beginner-friendly README** with before/after hook and bubblegum aesthetic
2. **Auto-generated sections** that sync with codebase
3. **Foundation for full documentation system** (future phases)

## Design Decisions

### Brand Identity

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Visual Style | Charmbracelet-inspired bubblegum | Playful, modern CLI tool aesthetic; "PopKit" name lends to pop/bubble theme |
| Opening Hook | Before/after comparison | Shows value immediately; story structure (tension → resolution) |
| Tone | Simply elegant but engaging | Every visual earns its place by showing value |
| Wordplay | Minimal | Let visuals speak; avoid forced puns |

### Audience

**Primary:** Broad appeal with progressive disclosure
- Beginners get clear narrative and quick start
- Advanced users find depth through collapsible sections
- Mirrors PopKit's "tiered loading" philosophy

### Generation Approach

**Hybrid:** Programmatic for data, AI for prose

| Content Type | Method | Rationale |
|--------------|--------|-----------|
| Command tables | Programmatic | Pure data, reliability matters |
| Agent lists | Programmatic | Structured data extraction |
| "What is PopKit?" | AI-written | Requires narrative craft |
| Feature descriptions | AI-polished | Context awareness needed |

### User Project Footprint

When PopKit manages a USER's documentation:
- Minimal footprint in their files (configs in `.popkit/`)
- Adapts to THEIR project's patterns and structure
- PopKit doesn't clutter their README

## README Structure

```
┌─────────────────────────────────────────────┐
│  BANNER (bubblegum aesthetic)               │
│  One-line tagline + badges                  │
├─────────────────────────────────────────────┤
│  BEFORE/AFTER HERO GIF                      │
│  "Without PopKit" → "With PopKit"           │
├─────────────────────────────────────────────┤
│  QUICK START (2 commands, restart, try it)  │
├─────────────────────────────────────────────┤
│  WHAT IS POPKIT? (narrative section)        │
│  3-4 sentences explaining vision            │
├─────────────────────────────────────────────┤
│  FEATURES (with demo GIFs)                  │
│  - Development Workflows                    │
│  - Morning/Nightly Routines                 │
│  - Power Mode                               │
├─────────────────────────────────────────────┤
│  <!-- AUTO-GEN:COMMANDS -->                 │
│  Commands table (collapsible)               │
├─────────────────────────────────────────────┤
│  <!-- AUTO-GEN:AGENTS -->                   │
│  Agents by tier (collapsible)               │
├─────────────────────────────────────────────┤
│  FAQ (collapsible sections)                 │
├─────────────────────────────────────────────┤
│  PREMIUM (free vs paid)                     │
├─────────────────────────────────────────────┤
│  CONTRIBUTING | LICENSE | LINKS             │
└─────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: PopKit's Own README (This Design)

**Scope:** Redesign PopKit's README

**Deliverables:**
- Visual assets (banner, demo GIFs)
- VHS tape files for reproducible recordings
- Rewritten README with new structure
- Auto-gen sync script
- CI integration

**Files to Create/Modify:**

| File | Action |
|------|--------|
| `packages/plugin/README.md` | Rewrite |
| `packages/plugin/assets/` | Create directory |
| `packages/plugin/assets/tapes/*.tape` | Create VHS tape files |
| `packages/plugin/scripts/sync-readme.py` | Create auto-gen script |
| `.github/workflows/sync-readme.yml` | Create CI workflow |

### Phase 2: `pop-docs-analyzer` Skill (Future)

- Analyzes any project's documentation
- Scores README quality (0-100)
- Suggests improvements

### Phase 3: `pop-readme-builder` Skill (Future)

- Guided README generation for new projects
- AI-written prose sections
- Adapts to project's tech stack

### Phase 4: Full Doc Sync System (Pro Feature)

- Upstash vector indexing
- Staleness detection
- Auto-update with human review

### Phase 5: Doc Recommendations Engine

- Collective learning from many projects
- Smart suggestions based on project type

## Visual Assets Specification

### VHS Tape Files

```
assets/tapes/
├── before-after.tape      # Hero comparison GIF
├── morning-routine.tape   # /popkit:routine morning demo
├── power-mode.tape        # Multi-agent collaboration
└── dev-workflow.tape      # /popkit:dev flow
```

### Color Palette (Bubblegum)

- Primary: Soft pinks, purples, teals
- Accent: Warm highlights
- Terminal: Custom theme matching brand

### Design Principle

> "Simply elegant but engaging" - every visual earns its place by demonstrating value, not just decoration.

## Auto-Generation System

### Pattern

```markdown
<!-- AUTO-GEN:SECTION_NAME START -->
[generated content]
<!-- AUTO-GEN:SECTION_NAME END -->
```

### Data Sources

| Section | Source |
|---------|--------|
| COMMANDS | `commands/*.md` frontmatter |
| AGENTS | `agents/**/AGENT.md` |
| VERSION | `plugin.json` |

### Sync Script

`scripts/sync-readme.py`:
- Scans source directories
- Extracts frontmatter/metadata
- Generates markdown tables
- Inserts into AUTO-GEN markers
- Can run as pre-commit hook or manually

## Future Documentation System Vision

```
┌─────────────────────────────────────────────────────────────┐
│                  PopKit Documentation System                │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │  Analyzer    │   │  Generator   │   │   Syncer     │    │
│  │  • Scans     │   │  • AI prose  │   │  • Watches   │    │
│  │  • Scores    │   │  • Templates │   │  • Updates   │    │
│  │  • Recommends│   │  • Adapts    │   │  • Commits   │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│         └──────────────────┼──────────────────┘             │
│                            ▼                                │
│            ┌──────────────────────────────┐                 │
│            │     Upstash Vector Index     │                 │
│            │  • Doc embeddings            │                 │
│            │  • Staleness detection       │                 │
│            └──────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Non-Negotiables (Vision Preservation)

These must be preserved in any documentation:

1. **Core Philosophy:** "PopKit orchestrates Claude Code's full power for real-world workflows"
2. **Tiered Architecture:** Always-active (Tier 1) + On-demand (Tier 2) + Generated (Tier 3)
3. **Non-Linear Development:** Support for branches, different paths, any project type
4. **Programmatic Chaining:** Simple tasks → orchestrated workflows
5. **AskUserQuestion Standard:** Interactive prompts, not plain text options
6. **Progressive Disclosure:** Don't overwhelm, reveal depth when needed

## Next Steps

1. **Create implementation plan** - Use `/popkit:dev plan` for Phase 1
2. **Create GitHub issues** - Break Phase 1 into trackable work items
3. **Set up assets structure** - Create directories and initial tape files
4. **Design banner** - Work on bubblegum aesthetic visual

---

*Design validated via `/popkit:dev brainstorm 184` on 2025-12-12*
