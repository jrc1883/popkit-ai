# Research: Screenshot-Driven VHS Tape Generation System

**Status:** Proposal
**Version:** 1.0
**Date:** 2025-12-12
**Author:** Claude Code (via popkit)
**Branch:** `claude/add-readme-effects-01RcHFcfJG8LdF9tYF9WsdSK`

---

## Executive Summary

This research proposes a **screenshot-driven VHS tape generation system** that:

1. **Organizes VHS tapes** by feature/concept in a structured folder hierarchy
2. **Uses screenshots as ground truth** for VHS tape generation
3. **Enables automated regeneration** when screenshots are updated
4. **Provides a path toward v2 automation** as a PopKit feature

The immediate use case is demonstrating **slash command discovery** in Claude Code, showing how users can type `/dev` and have `popkit:dev` auto-suggest without typing the full prefix.

---

## Current State Analysis

### Existing Infrastructure

**Location:** `packages/plugin/assets/`

```
packages/plugin/assets/
├── images/
│   ├── .gitkeep
│   └── README-ASSETS.md
└── tapes/
    ├── before-after.tape
    └── morning-routine.tape
```

### VHS Tape Format

All tapes follow this pattern:

```tape
Output assets/images/{name}.gif
Set FontSize 14
Set Width 800
Set Height 500
Set Theme "Catppuccin Mocha"
Set Padding 20

Type "/popkit:routine morning"
Sleep 500ms
Enter
Sleep 2s
Type@50ms "output line 1"
Enter
Type@50ms "output line 2"
Enter
Sleep 2s
```

### Current Workflow

1. **Manual creation** - Developer writes `.tape` file by hand
2. **Manual generation** - Run `vhs {name}.tape` locally
3. **Manual verification** - Visual inspection of generated GIF
4. **Manual updates** - When UI changes, rewrite tape manually

### Problems with Current Approach

1. **No source of truth** - Tape files can drift from actual UI behavior
2. **Manual synchronization** - Screenshots show reality, tapes might not
3. **Fragile** - Easy to forget timing, exact wording, or visual layout
4. **No organization** - Flat structure doesn't scale to 20+ demos
5. **No regeneration workflow** - When PopKit changes, tapes become stale

---

## Proposed Architecture

### Folder Structure

```
packages/plugin/assets/
├── images/
│   └── [generated GIFs]
└── tapes/
    ├── core-features/
    │   ├── slash-command-discovery/
    │   │   ├── screenshots/
    │   │   │   ├── 01-type-slash.png
    │   │   │   ├── 02-type-dev.png
    │   │   │   ├── 03-dropdown-appears.png
    │   │   │   └── 04-popkit-dev-highlighted.png
    │   │   ├── metadata.json
    │   │   └── slash-command-discovery.tape
    │   ├── morning-routine/
    │   │   ├── screenshots/
    │   │   │   ├── 01-command-typed.png
    │   │   │   └── 02-output-displayed.png
    │   │   ├── metadata.json
    │   │   └── morning-routine.tape
    │   └── before-after/
    │       ├── screenshots/
    │       ├── metadata.json
    │       └── before-after.tape
    ├── workflows/
    │   ├── 7-phase-feature-dev/
    │   ├── power-mode-collaboration/
    │   └── git-workflow/
    ├── agents/
    │   ├── bug-whisperer-demo/
    │   ├── code-reviewer-demo/
    │   └── security-audit-demo/
    └── integration/
        ├── github-integration/
        ├── mcp-server-demo/
        └── cloud-sync-demo/
```

### Metadata Schema

Each tape directory contains a `metadata.json`:

```json
{
  "name": "Slash Command Discovery",
  "description": "Shows how typing /dev auto-suggests popkit:dev without full prefix",
  "category": "core-features",
  "output_file": "slash-command-discovery.gif",
  "dimensions": {
    "width": 800,
    "height": 500
  },
  "theme": "Catppuccin Mocha",
  "font_size": 14,
  "screenshots": [
    {
      "filename": "01-type-slash.png",
      "description": "User types '/' character",
      "timing": "0ms"
    },
    {
      "filename": "02-type-dev.png",
      "description": "User types 'd', 'e', 'v' characters",
      "timing": "500ms"
    },
    {
      "filename": "03-dropdown-appears.png",
      "description": "Dropdown shows all matching commands",
      "timing": "200ms"
    },
    {
      "filename": "04-popkit-dev-highlighted.png",
      "description": "popkit:dev is first in list, highlighted",
      "timing": "1000ms"
    }
  ],
  "key_insights": [
    "No need to type full 'popkit:' prefix",
    "Semantic search finds popkit:dev from just 'dev'",
    "Tab completion works instantly",
    "Works for all Claude Code plugins, not just popkit"
  ],
  "readme_sections": [
    "Quick Start",
    "Features > Development Workflows"
  ],
  "tags": ["ux", "discovery", "commands", "quick-start"]
}
```

---

## Screenshot-to-VHS Workflow

### Phase 1: Manual with Screenshots (Current)

**Developer workflow:**

1. **Capture screenshots** in Claude Code showing actual behavior
2. **Drop screenshots** into `tapes/{category}/{feature}/screenshots/`
3. **Create metadata.json** describing each screenshot
4. **Run generation command** (future: `/popkit:vhs generate`)
5. **VHS tape is auto-generated** from screenshot analysis

### Phase 2: Automated Regeneration (Near-term)

**When screenshots change:**

1. Developer updates screenshots in folder
2. Git detects changes to `screenshots/` directory
3. Pre-commit hook or CI workflow runs:
   ```bash
   /popkit:vhs regenerate --changed
   ```
4. Only modified tape directories are regenerated
5. Developer reviews diff of `.tape` file

### Phase 3: AI-Powered Generation (Future)

**Fully automated:**

1. Developer provides **video recording** or **screen recording**
2. AI analyzes video frame-by-frame
3. Extracts:
   - Exact typing sequences
   - Timing between keystrokes
   - Output that appears
   - Visual layout and formatting
4. Generates VHS tape that **exactly replicates** the recording
5. Developer approves or tweaks

---

## Example: Slash Command Discovery Demo

### Feature Description

**Goal:** Show users that they don't need to type the full `popkit:` prefix when using slash commands.

**User insight:**
> "If you wanted to get to say the 'popkit:dev work' command, you could just do a slash and then you start typing D E V. It actually does pull up... the PopKit dev work command is the first one up."

### Screenshots to Capture

1. **`01-type-slash.png`** - Cursor after typing `/`
2. **`02-type-d.png`** - After typing `/d`
3. **`03-type-de.png`** - After typing `/de`
4. **`04-type-dev.png`** - After typing `/dev` (dropdown appears)
5. **`05-popkit-highlighted.png`** - `popkit:dev` highlighted at top of list
6. **`06-tab-completion.png`** - After pressing Tab, full command appears
7. **`07-add-work.png`** - After typing `work`
8. **`08-add-issue-number.png`** - After typing `#57`
9. **`09-final-command.png`** - Complete command: `/popkit:dev work #57`

### Generated VHS Tape (Example)

```tape
# Slash Command Discovery Demo
# Shows how /dev auto-suggests popkit:dev

Output assets/images/slash-command-discovery.gif

Set FontSize 14
Set Width 900
Set Height 600
Set Theme "Catppuccin Mocha"
Set Padding 20

# Clear screen
Ctrl+L
Sleep 1s

# Type slash
Type "/"
Sleep 300ms

# Dropdown appears (simulated)
Type "d"
Sleep 200ms
Type "e"
Sleep 200ms
Type "v"
Sleep 500ms

# Show dropdown appearing (we'll need to simulate this in terminal)
# For VHS, we can't show actual dropdown, so we'll show it in comment form
Hide
Type "# Dropdown shows:"
Enter
Type "#   ✓ popkit:dev          (first match!)"
Enter
Type "#   - dev-server"
Enter
Type "#   - devtools"
Enter
Sleep 1s
Show

# Clear and show final command
Ctrl+L
Sleep 300ms

# Tab completion selects popkit:dev
Type "/popkit:dev"
Sleep 500ms

# Add subcommand
Type " work"
Sleep 300ms

# Add issue number
Type " #57"
Sleep 500ms
Enter

# Show output
Sleep 1s
Type@30ms "✓ Fetched issue #57: Implement user authentication"
Enter
Type@30ms "✓ Created worktree: .worktrees/issue-57"
Enter
Type@30ms "✓ Ready to start development!"
Enter

Sleep 2s
```

### Limitations of VHS for This Demo

**Problem:** VHS cannot show **actual dropdown menus** that appear in Claude Code's UI.

**Solutions:**

1. **Annotated screenshot approach** - Show screenshot with arrows/highlights
2. **Side-by-side comparison** - Screenshot + VHS tape together
3. **Simulated dropdown** - Use ASCII art in terminal to show concept
4. **Video recording** - Use actual screen recording (not VHS) for this demo

**Recommendation:** For dropdown demo, use **screenshot with annotations** rather than VHS tape.

---

## Implementation Roadmap

### Phase 1: Foundation (Immediate)

**Goal:** Establish folder structure and metadata schema

- [x] Design folder structure
- [ ] Create `slash-command-discovery/` directory
- [ ] Capture 9 screenshots showing typing progression
- [ ] Write `metadata.json` for screenshots
- [ ] Document workflow in README-ASSETS.md

**Timeline:** 1 day
**Dependencies:** None
**Deliverable:** Organized screenshot library

### Phase 2: Manual Generation (Near-term)

**Goal:** Create VHS tapes from screenshot analysis

- [ ] Implement `/popkit:vhs analyze` command
  - Reads screenshots in directory
  - Analyzes using Claude vision
  - Extracts timing, text, layout
- [ ] Implement `/popkit:vhs generate` command
  - Takes metadata.json
  - Generates .tape file
  - Runs VHS to create GIF
- [ ] Test with 3-5 tape directories

**Timeline:** 1 week
**Dependencies:** Phase 1
**Deliverable:** Working command for tape generation

### Phase 3: Automated Regeneration (Future)

**Goal:** Auto-regenerate tapes when screenshots change

- [ ] Git hooks integration
  - Pre-commit hook detects screenshot changes
  - Auto-regenerates affected tapes
  - Prompts for review/approval
- [ ] CI/CD workflow
  - GitHub Actions workflow
  - Runs on PR creation
  - Comments with before/after GIF comparison

**Timeline:** 2 weeks
**Dependencies:** Phase 2
**Deliverable:** Automated tape regeneration

### Phase 4: AI-Powered Video Analysis (v2.0)

**Goal:** Generate VHS tapes from screen recordings

**Features:**

- [ ] Video upload to `/popkit:vhs from-video <file.mp4>`
- [ ] Frame-by-frame analysis
  - OCR for text extraction
  - Timing calculation
  - Layout detection
- [ ] Automatic tape generation
- [ ] Interactive refinement UI

**Timeline:** 1-2 months
**Dependencies:** Phase 3, video processing infrastructure
**Deliverable:** Full automation of VHS tape creation

---

## PopKit v2 Feature Spec

### Feature: `/popkit:vhs`

**Description:** Generate VHS tapes from screenshots, videos, or live recordings.

### Subcommands

| Subcommand | Description |
|------------|-------------|
| `analyze <dir>` | Analyze screenshots in directory, extract metadata |
| `generate <dir>` | Generate VHS tape from metadata.json |
| `regenerate [--changed]` | Regenerate all or changed tapes |
| `from-video <file>` | Generate tape from MP4/MOV screen recording |
| `record <name>` | Start interactive recording session |
| `preview <tape>` | Preview tape before generating GIF |
| `validate <tape>` | Check tape syntax and timing |
| `optimize <tape>` | Reduce file size, adjust timing |

### Examples

```bash
# Analyze screenshots and create metadata
/popkit:vhs analyze packages/plugin/assets/tapes/core-features/slash-command-discovery/

# Generate VHS tape from metadata
/popkit:vhs generate packages/plugin/assets/tapes/core-features/slash-command-discovery/

# Regenerate all tapes with changed screenshots
/popkit:vhs regenerate --changed

# Generate from video recording
/popkit:vhs from-video ~/Desktop/command-demo.mp4 --output slash-command-discovery

# Interactive recording (future)
/popkit:vhs record power-mode-demo
```

### Architecture

**MCP Server Integration:**

```typescript
// packages/plugin/templates/mcp-server/src/tools/vhs-tools.ts

export const vhsTools = {
  analyze_screenshots: {
    description: "Analyze screenshots and extract VHS metadata",
    parameters: {
      directory: "Path to screenshots directory",
      output: "Output path for metadata.json"
    }
  },

  generate_tape: {
    description: "Generate VHS tape from metadata",
    parameters: {
      metadata_path: "Path to metadata.json",
      output_path: "Output path for .tape file"
    }
  },

  from_video: {
    description: "Generate VHS tape from video recording",
    parameters: {
      video_path: "Path to MP4/MOV file",
      output_name: "Name for generated tape"
    }
  }
};
```

**Skill Implementation:**

```yaml
# packages/plugin/skills/pop-vhs-generate.md

---
name: pop-vhs-generate
description: Generate VHS tapes from screenshots or videos
category: utilities
premium: false
version: 1.0.0
---

# VHS Tape Generator

## Purpose

Analyzes screenshots or video recordings to generate VHS tape definitions.

## Usage

Invoke via:
- `/popkit:vhs generate <directory>`
- Direct skill invocation: `Use pop-vhs-generate skill`

## Process

1. Read metadata.json from directory
2. Analyze each screenshot using vision
3. Extract:
   - Text being typed
   - Output appearing
   - Timing between frames
   - Visual layout
4. Generate .tape file with proper syntax
5. Run VHS to create GIF
6. Validate output matches screenshots

## Output

- `{name}.tape` file
- `{name}.gif` generated image
- Validation report
```

### Integration Points

1. **Commands:** `/popkit:vhs` command family
2. **Skills:** `pop-vhs-generate`, `pop-vhs-analyze`, `pop-vhs-validate`
3. **MCP Server:** VHS tools in project-specific MCP server
4. **Hooks:** Pre-commit hook for regeneration
5. **Agents:** `vhs-generator` specialist agent (Tier 2)

---

## Alternative Approaches

### Option 1: Pure Screenshot Approach (Recommended for Now)

**Pros:**
- No VHS dependency
- Works with actual UI (dropdowns, menus)
- Easier to maintain
- Screenshots are source of truth

**Cons:**
- Static images, no animation
- Less engaging than GIFs

**Use case:** Slash command discovery demo

### Option 2: Hybrid Approach

**Pros:**
- Screenshots for UI elements (dropdowns)
- VHS for terminal sequences
- Best of both worlds

**Cons:**
- More complex workflow
- Need both tools

**Use case:** Complex workflows (7-phase feature dev)

### Option 3: Full Video Recording

**Pros:**
- Captures everything exactly
- No simulation needed
- Real user interaction

**Cons:**
- Large file sizes
- Hard to edit/update
- Not reproducible

**Use case:** Marketing materials, not docs

---

## Recommendations

### Immediate Actions (This Week)

1. **Create folder structure** for `slash-command-discovery/`
2. **Capture 9 screenshots** showing typing progression
3. **Write metadata.json** documenting each screenshot
4. **Create annotated screenshot** showing dropdown (not VHS)
5. **Update README** with screenshot instead of VHS for this demo

### Near-term (Next Sprint)

1. **Implement `/popkit:vhs analyze`** as a skill
2. **Test with 3 existing tapes** (morning-routine, before-after, power-mode)
3. **Document workflow** in README-ASSETS.md
4. **Create 5 more demos** using new structure

### Long-term (v2.0)

1. **Build video analysis pipeline**
2. **Create VHS agent** (Tier 2 specialist)
3. **Integrate with MCP server** template
4. **Add to marketplace** as standalone feature
5. **Enable community contributions** (users submit their own tapes)

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| VHS can't show real UI | High | Certain | Use screenshots for UI demos |
| Screenshots drift from reality | Medium | Medium | Automated validation in CI |
| Manual workflow too slow | Medium | High | Prioritize automation (Phase 2) |
| Video files too large | Low | Medium | Use compression, optimize format |
| Community submissions low quality | Low | Low | Review process, quality guidelines |

---

## Success Metrics

### Phase 1 (Foundation)

- [ ] 10+ tape directories with screenshots
- [ ] Metadata schema finalized
- [ ] Documentation complete

### Phase 2 (Manual Generation)

- [ ] `/popkit:vhs analyze` command working
- [ ] 5+ tapes generated using new workflow
- [ ] Time to create tape reduced by 50%

### Phase 3 (Automation)

- [ ] Git hooks auto-regenerate tapes
- [ ] CI validates all tapes on PR
- [ ] 100% of tapes have screenshot source of truth

### Phase 4 (AI-Powered)

- [ ] Video-to-tape conversion working
- [ ] Community contributions enabled
- [ ] 50+ tapes in marketplace

---

## Appendix A: VHS Limitations

### What VHS Can Do

- Simulate terminal input/output
- Control timing precisely
- Create reproducible GIFs
- Show typing animations
- Display terminal output

### What VHS Cannot Do

- Show GUI dropdowns/menus
- Capture mouse interactions
- Display non-terminal UI
- Show multiple windows
- Interactive elements (buttons, links)

### Workarounds

| Limitation | Workaround |
|------------|------------|
| Dropdowns | Use annotated screenshots |
| Mouse clicks | Show command result instead |
| Multiple windows | Side-by-side screenshots |
| Interactive UI | Static screenshot + description |
| Complex layouts | Simplify to terminal view |

---

## Appendix B: Example Metadata Files

### Simple Demo (Morning Routine)

```json
{
  "name": "Morning Routine Health Check",
  "description": "Shows daily health check with Ready to Code score",
  "category": "core-features",
  "output_file": "morning-routine.gif",
  "dimensions": {"width": 800, "height": 500},
  "theme": "Catppuccin Mocha",
  "font_size": 14,
  "screenshots": [
    {
      "filename": "01-command.png",
      "description": "User types /popkit:routine morning",
      "timing": "0ms"
    },
    {
      "filename": "02-output.png",
      "description": "Health check results displayed",
      "timing": "3000ms"
    }
  ],
  "tags": ["routine", "health-check", "quick-start"]
}
```

### Complex Demo (7-Phase Feature Dev)

```json
{
  "name": "7-Phase Feature Development",
  "description": "Complete workflow from idea to implementation",
  "category": "workflows",
  "output_file": "7-phase-feature-dev.gif",
  "dimensions": {"width": 1000, "height": 700},
  "theme": "Catppuccin Mocha",
  "font_size": 13,
  "screenshots": [
    {
      "filename": "01-start-command.png",
      "description": "User starts with /popkit:dev",
      "timing": "0ms"
    },
    {
      "filename": "02-discovery-phase.png",
      "description": "Phase 1: Discovery begins",
      "timing": "2000ms"
    },
    {
      "filename": "03-exploration-phase.png",
      "description": "Phase 2: Code exploration",
      "timing": "5000ms"
    },
    {
      "filename": "04-questions-phase.png",
      "description": "Phase 3: Clarifying questions",
      "timing": "8000ms"
    },
    {
      "filename": "05-architecture-phase.png",
      "description": "Phase 4: Architecture design",
      "timing": "12000ms"
    },
    {
      "filename": "06-implementation-phase.png",
      "description": "Phase 5: Implementation",
      "timing": "16000ms"
    },
    {
      "filename": "07-review-phase.png",
      "description": "Phase 6: Code review",
      "timing": "20000ms"
    },
    {
      "filename": "08-summary-phase.png",
      "description": "Phase 7: Summary and next steps",
      "timing": "24000ms"
    }
  ],
  "key_insights": [
    "Structured progression through phases",
    "Each phase has specific purpose",
    "Can jump between phases if needed",
    "Automatic architecture review before coding"
  ],
  "tags": ["workflow", "feature-dev", "7-phase", "advanced"]
}
```

---

## Conclusion

This research proposes a **screenshot-driven VHS tape generation system** that:

1. **Solves the drift problem** - Screenshots are ground truth
2. **Enables automation** - Regenerate tapes when screenshots change
3. **Scales to many demos** - Organized folder structure
4. **Provides path to v2** - Future AI-powered video analysis

**Immediate next step:** Create the `slash-command-discovery/` directory with screenshots demonstrating the `/dev` → `popkit:dev` auto-suggestion behavior.

For the slash command demo specifically, **recommend using annotated screenshots** rather than VHS, since VHS cannot accurately show dropdown menus.

**Decision needed:** Should we proceed with:
- **Option A:** Screenshot-based approach for slash command demo
- **Option B:** VHS with simulated dropdown in comments
- **Option C:** Hybrid (screenshot for dropdown, VHS for command execution)

---

**Related Files:**
- `packages/plugin/assets/tapes/` - Current VHS tape location
- `packages/plugin/assets/images/README-ASSETS.md` - Asset management docs
- `packages/plugin/README.md` - Where GIFs are embedded
- `packages/plugin/scripts/sync-readme.py` - README auto-generation

**Next Steps:**
1. Review and approve this research
2. Create folder structure
3. Capture screenshots
4. Implement generation command (or manual workflow first)
5. Add to v2.0 roadmap
