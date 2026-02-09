# PopKit Initialization Script Overhaul - Design Document

**Date**: 2026-01-16
**Issue**: Related to #65 (Interactive questions in /popkit:project init)
**Status**: Design Complete, Ready for Implementation
**Author**: Joseph Cannon + Claude Sonnet 4.5

---

## Problem Statement

PopKit currently has fragmented initialization:

- Session-start hook auto-creates directories but not STATUS.json
- No clear "initialization ceremony" for new projects
- STATUS.json only created by explicit skills (morning/nightly/capture)
- No distinction between "installed" vs "initialized" states
- Issue #65 designed interactive questions but never implemented
- No support for worktree-based workflows (El Shaddai style)

**User Pain Points**:

1. "I have PopKit installed but not initialized, and I'm confused"
2. "STATUS.json doesn't exist, morning routine fails"
3. "I don't know what project type to choose - none fit my use case"
4. "Why do I need to answer 10 questions to get started?"

---

## Design Principles

1. **Separation of Concerns**: Session-start reads, /popkit:init writes
2. **Intelligence Over Questions**: Detect project type automatically, only ask when uncertain
3. **Inclusive Beyond Code**: Support research, medical, CAD, office work, not just programming
4. **Worktree-First**: Treat worktree workflow as first-class, not an afterthought
5. **Progressive Disclosure**: High confidence = no questions, low confidence = full UI
6. **Community Extensible**: Design for future community detector contributions

---

## Architecture Overview

### Two-Component System

```
┌─────────────────────────────────────────────────────────┐
│ Session-Start Hook (Lightweight, Read-Only)             │
│                                                          │
│  1. Check if STATUS.json exists                         │
│  2. If exists:                                           │
│     - Read and validate (check age < 24h, no corruption)│
│     - Load worktree/branch info                         │
│     - Pass to status line (enables live updates)        │
│     - Pass to morning routine (context restoration)     │
│  3. If missing or stale:                                │
│     - Warn: "Run /popkit:init to initialize project"   │
│  4. Never blocks, never creates files                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ /popkit:init Command (Comprehensive, Interactive)       │
│                                                          │
│  1. Detect current state (already initialized?)         │
│  2. If already initialized:                             │
│     - Show last init timestamp + version                │
│     - Detect what changed since init                    │
│     - Smart recommendations (update vs reconfigure)     │
│     - Offer: Update | Reconfigure | Skip                │
│  3. If not initialized:                                 │
│     - Comprehensive project detection (100+ file types) │
│     - Interactive questions (redesigned, minimal)       │
│     - Create directory structure (.claude/popkit/*)     │
│     - Generate config.json with smart defaults          │
│     - Initialize STATUS.json with proper schema         │
│     - Run initial project analysis                      │
│     - Optionally insert PopKit config into CLAUDE.md    │
│  4. Always confirms success with summary                │
└─────────────────────────────────────────────────────────┘
```

**Key Principle**: Session-start is passive (read-only), /popkit:init is active (creates/configures).

---

## Enhanced STATUS.json Schema

### New Schema with Worktree Support

```json
{
  "lastUpdate": "2026-01-16T10:30:00Z",
  "project": "popkit-claude",
  "sessionType": "Morning|Nightly|Capture|Development",

  "git": {
    "branch": "feat/init-overhaul",
    "worktree": {
      "path": "/path/to/worktree",
      "name": "feat-init-overhaul",
      "isMainWorktree": false,
      "baseRef": "main"
    },
    "lastCommit": "a1b2c3d - feat: Add initialization",
    "uncommittedFiles": 3,
    "stagedFiles": 1,
    "modifiedFiles": ["file1.py", "file2.md"],
    "untrackedFiles": ["file3.js"]
  },

  "tasks": {
    "inProgress": ["Design initialization script", "Update STATUS.json schema"],
    "completed": ["Create orchestrator PR"],
    "blocked": []
  },

  "services": {
    "devServer": { "running": true, "port": 3000 },
    "redis": { "running": false, "port": 6379 }
  },

  "context": {
    "focusArea": "PopKit initialization overhaul",
    "blocker": null,
    "nextAction": "Present design sections",
    "keyDecisions": [
      "Separate session-start (read) from /popkit:init (write)",
      "Add worktree info to STATUS.json"
    ]
  },

  "projectData": {
    "testStatus": "passing",
    "buildStatus": "passing",
    "lintErrors": 0
  },

  "popkit": {
    "initialized": true,
    "initializedAt": "2026-01-15T09:00:00Z",
    "version": "1.0.0-beta.5",
    "tier": "free",
    "features": {
      "powerMode": "configured",
      "customRoutines": true,
      "cloudSync": false
    }
  }
}
```

**Key Changes**:

1. **Added `git.worktree` object**: Tracks worktree path, name, whether it's main worktree, base ref
2. **Added `popkit` top-level section**: PopKit-specific metadata (initialized flag, version, tier, features)
3. **Backward compatible**: All existing fields preserved

---

## /popkit:init Command Flow

### Command Structure

```bash
/popkit:init                    # Full initialization wizard
/popkit:init --skip-questions   # Use smart defaults
/popkit:init --check            # Check init status without changing
/popkit:init --update           # Update existing initialization
```

### Initialization Phases

#### Phase 1: Pre-Flight Checks

```
• Check if .git exists (require git repo)
• Check if already initialized:
  - config.json exists?
  - STATUS.json exists?
  - .claude/popkit/ exists?
• If already initialized:
  ├─ Show last init: "2026-01-15 @ 09:00"
  ├─ Show version: "1.0.0-beta.5"
  ├─ Detect changes since init (new files, framework updates)
  └─ AskUserQuestion: [Update] | [Reconfigure] | [Skip]
```

#### Phase 2: Smart Detection (Intelligence Layer)

**Auto-detect from codebase**:

```python
def intelligent_project_detection():
    """Three-tier detection strategy."""

    # Tier 1: File Type Scanning (fast)
    file_counts = scan_project_files()
    # Returns: {"programming": 450, "cad": 0, "medical": 0, ...}

    primary_category = max(file_counts, key=file_counts.get)
    confidence = file_counts[primary_category] / sum(file_counts.values())

    # Tier 2: Drill-Down within Category
    if primary_category == "programming":
        specifics = detect_programming_specifics()
        # Returns: ["nextjs_app", "react_spa", "monorepo"]
    elif primary_category == "research":
        specifics = detect_research_specifics()
        # Returns: ["latex_paper", "jupyter_notebook"]
    # ... etc for all categories

    # Tier 3: Context from CLAUDE.md + Git
    context = {
        "claude_md": read_claude_md_smart(),  # Iterative, early-exit
        "monorepo": detect_monorepo(),
        "worktrees": detect_worktrees(),
        "git_flow": detect_git_workflow(),
    }

    return {
        "primary": primary_category,
        "confidence": confidence,
        "specifics": specifics,
        "context": context,
        "skip_questions": confidence > 0.85,  # High confidence = zero questions
    }
```

**Smart CLAUDE.md Reading** (no token bloat):

```python
def read_claude_md_smart():
    """Read CLAUDE.md intelligently without reading entire file."""

    markers_to_find = {
        "overview": False,
        "tech_stack": False,
        "workflow": False,
        "popkit_config": False,
    }

    extracted = {}
    lines_read = 0
    max_lines = 2000  # Safety limit for huge files

    with open("CLAUDE.md") as f:
        for line in f:
            lines_read += 1

            # Extract on the fly
            if "## overview" in line.lower():
                markers_to_find["overview"] = True
                # Read next 10 lines for overview

            if any(tech in line.lower() for tech in
                   ["typescript", "python", "react", "django", "nextjs"]):
                markers_to_find["tech_stack"] = True
                extracted.setdefault("tech_stack", []).append(line)

            if "worktree" in line.lower() or "git flow" in line.lower():
                markers_to_find["workflow"] = True
                extracted.setdefault("workflow", []).append(line)

            # Early exit if we found everything
            if all(markers_to_find.values()):
                break

            if lines_read >= max_lines:
                break

    return extracted
```

#### Phase 3: Interactive Questions (NEW DESIGN)

**Progressive Disclosure Strategy**:

- **Confidence > 85%**: Skip all questions, show confirmation
- **Confidence 60-85%**: Ask 1-2 questions for clarification
- **Confidence < 60%**: Full question flow

**Question 1: Workflow Style**

```
What's your development workflow?

┌─────────────────────────────────────────────┐
│ [ ] Feature Branch (Git Flow)               │
│     Create branches, PR to main             │
│                                              │
│ [✓] Worktree-Based (El Shaddai style) ⭐    │
│     Multiple worktrees, parallel work       │
│                                              │
│ [ ] Trunk-Based (main only)                 │
│     Direct commits to main, rapid iteration │
│                                              │
│ [ ] Custom (describe)                        │
└─────────────────────────────────────────────┘
```

**Question 2: Project Type** (auto-detected, user confirms)

```
We detected: Node.js Monorepo (95% confidence)

Details:
• Monorepo with pnpm workspaces
• 4 apps, 12 shared packages
• TypeScript + React + Next.js
• Worktree workflow detected

Is this correct?
[✓ Yes, looks good]  [✗ Let me specify]
```

If user clicks "Let me specify":

```
┌─────────────────────────────────────────────┐
│ Select project type(s) (arrow keys, space)  │
│                                              │
│ [✓] Node.js Application (detected)          │
│ [✓] Monorepo (detected)                     │
│ [✓] TypeScript                               │
│ [ ] Python                                   │
│ [ ] React SPA                                │
│ [ ] Research/Writing                         │
│ [ ] CAD/Engineering                          │
│ [ ] Medical/Healthcare                       │
│ [ ] Workflow Automation                      │
│ [ ] Other (describe)                         │
│                                              │
│ ↓ Arrow down for more (30+ options)         │
│                                              │
│ [Continue]  [Cancel]                         │
└─────────────────────────────────────────────┘
```

**Question 3: Quality Standards**

```
What quality standards should PopKit enforce?

┌─────────────────────────────────────────────┐
│ [ ] Strict                                   │
│     Tests required, lint enforced, no errors │
│                                              │
│ [✓] Balanced (Recommended)                   │
│     Tests encouraged, warnings allowed       │
│                                              │
│ [ ] Flexible                                 │
│     Suggestions only, no enforcement         │
└─────────────────────────────────────────────┘
```

**Question 4: PopKit Tier** (only if authenticated)

```
Which PopKit tier are you using?

┌─────────────────────────────────────────────┐
│ [✓] Free (basic features)                    │
│     Local files, core skills, no cloud       │
│                                              │
│ [ ] Cloud (embeddings, history, team)        │
│     Semantic search, benchmark history       │
│                                              │
│ [ ] Not sure (explain options)               │
└─────────────────────────────────────────────┘
```

#### Phase 4: Directory Structure Creation

```bash
.claude/
├── popkit/
│   ├── config.json              # Generated from answers
│   ├── routines/
│   │   ├── morning/
│   │   │   └── .gitkeep
│   │   └── nightly/
│   │       └── .gitkeep
│   ├── recordings/              # For benchmark suite
│   └── embeddings/              # For semantic search (cloud tier)
└── STATUS.json                  # Initial state capture
```

#### Phase 5: Config Generation

**config.json**:

```json
{
  "version": "1.0",
  "project_name": "popkit-claude",
  "project_prefix": "pk",
  "project_type": ["nodejs", "monorepo", "typescript"],
  "workflow": "worktree",
  "quality_standard": "balanced",
  "default_routines": {
    "morning": "pk",
    "nightly": "pk"
  },
  "initialized_at": "2026-01-16T10:30:00Z",
  "popkit_version": "1.0.0-beta.5",
  "tier": "free",
  "features": {
    "power_mode": "not_configured",
    "custom_routines": [],
    "cloud_sync": false,
    "semantic_search": false
  },
  "detection_metadata": {
    "auto_detected": true,
    "confidence": 0.95,
    "manual_overrides": []
  }
}
```

**STATUS.json** (initial state):

```json
{
  "lastUpdate": "2026-01-16T10:30:00Z",
  "project": "popkit-claude",
  "sessionType": "Init",
  "git": {
    "branch": "main",
    "worktree": {
      "path": "/Users/josep/popkit-claude",
      "name": "main",
      "isMainWorktree": true,
      "baseRef": null
    },
    "lastCommit": "42d3e0e - feat: Complete Phase 2",
    "uncommittedFiles": 0,
    "stagedFiles": 0,
    "modifiedFiles": [],
    "untrackedFiles": []
  },
  "tasks": {
    "inProgress": [],
    "completed": ["PopKit initialization"],
    "blocked": []
  },
  "services": {},
  "context": {
    "focusArea": "Getting started with PopKit",
    "blocker": null,
    "nextAction": "Run /popkit-dev:next to see recommendations",
    "keyDecisions": []
  },
  "projectData": {
    "testStatus": "unknown",
    "buildStatus": "unknown",
    "lintErrors": -1
  },
  "popkit": {
    "initialized": true,
    "initializedAt": "2026-01-16T10:30:00Z",
    "version": "1.0.0-beta.5",
    "tier": "free",
    "features": {
      "powerMode": "not_configured",
      "customRoutines": false,
      "cloudSync": false
    }
  }
}
```

#### Phase 6: CLAUDE.md Enhancement (Optional)

Offer to surgically insert PopKit config section at beginning of CLAUDE.md:

```markdown
# CLAUDE.md

<!-- PopKit Configuration -->

## PopKit Setup

**Project Type**: Node.js Monorepo (TypeScript + React + Next.js)
**Workflow**: Worktree-Based
**Quality Standard**: Balanced
**Initialized**: 2026-01-16

**PopKit Features Enabled**:

- Morning/Nightly routines
- Worktree management
- Project analysis

<!-- End PopKit Configuration -->

## Overview

[rest of existing CLAUDE.md content...]
```

**Benefits**:

- Fast context loading (top of file)
- Human-readable metadata
- No need to read entire file
- Easy to update manually

#### Phase 7: Success Summary

```
✅ PopKit Initialization Complete!

📁 Created:
  • .claude/popkit/config.json
  • .claude/STATUS.json
  • .claude/popkit/routines/ (morning, nightly)

🎯 Detected:
  • Node.js Monorepo with TypeScript
  • Worktree-based workflow
  • 4 apps, 12 packages

⚙️ Configuration:
  • Quality: Balanced
  • Tier: Free
  • Prefix: pk

🚀 Next Steps:
  1. Run /popkit-dev:morning to start your day
  2. Run /popkit-dev:next to see smart recommendations
  3. Visit docs/getting-started.md for tutorials

PopKit is ready to accelerate your development!
```

---

## Comprehensive File Type Detection

### Detection Categories (100+ File Types)

Based on research from industry sources:

#### 1. Programming (50+ languages)

```python
PROGRAMMING_DETECTORS = {
    # Frontend (30+ frameworks)
    "react": [".jsx", ".tsx", "package.json→react"],
    "nextjs": ["next.config.js", "app/", "pages/"],
    "vue": [".vue", "package.json→vue"],
    "nuxt": ["nuxt.config.js"],
    "angular": [".component.ts", "angular.json"],
    "svelte": [".svelte", "svelte.config.js"],
    "sveltekit": ["svelte.config.js + @sveltejs/kit"],
    "solid": ["package.json→solid-js"],
    "qwik": ["package.json→@builder.io/qwik"],
    "astro": [".astro", "astro.config.mjs"],
    "remix": ["remix.config.js"],
    "gatsby": ["gatsby-config.js"],
    "preact": ["package.json→preact"],
    "lit": ["package.json→lit"],
    "alpine": ["package.json→alpinejs"],
    "htmx": [".html with htmx attributes"],
    "ember": ["ember-cli-build.js"],
    "backbone": ["package.json→backbone"],
    "polymer": ["polymer.json"],
    # Static site generators
    "eleventy": [".eleventy.js"],
    "jekyll": ["_config.yml + Gemfile→jekyll"],
    "hugo": ["config.toml + hugo"],
    # Mobile
    "react_native": ["package.json→react-native"],
    "expo": ["app.json + expo"],
    "ionic": ["ionic.config.json"],
    "flutter": ["pubspec.yaml + flutter"],

    # Backend (30+ frameworks)
    "express": ["package.json→express"],
    "fastify": ["package.json→fastify"],
    "koa": ["package.json→koa"],
    "nestjs": ["nest-cli.json"],
    "hapi": ["package.json→@hapi/hapi"],
    "django": ["manage.py", "requirements.txt→django"],
    "flask": ["requirements.txt→flask"],
    "fastapi": ["requirements.txt→fastapi"],
    "tornado": ["requirements.txt→tornado"],
    "aiohttp": ["requirements.txt→aiohttp"],
    "bottle": ["requirements.txt→bottle"],
    "pyramid": ["requirements.txt→pyramid"],
    "ruby_on_rails": ["Gemfile→rails"],
    "sinatra": ["Gemfile→sinatra"],
    "go_gin": ["go.mod→github.com/gin-gonic/gin"],
    "go_echo": ["go.mod→github.com/labstack/echo"],
    "fiber": ["go.mod→github.com/gofiber/fiber"],
    "spring_boot": ["pom.xml→spring-boot"],
    "laravel": ["composer.json→laravel/framework"],
    "symfony": ["composer.json→symfony"],

    # CLI/Tools
    "python_cli": ["cli.py", "requirements.txt→click|typer"],
    "nodejs_cli": ["bin/", "package.json→commander|yargs"],
    "go_cli": ["go.mod + main.go with cobra|urfave"],
}
```

**Sources**: [Programming Languages and File Extensions](https://gist.github.com/ppisarczyk/43962d06686722d26d176fad46879d41)

#### 2. CAD/Engineering (30+ formats)

```python
CAD_DETECTORS = {
    "autocad": [".dwg", ".dxf"],
    "solidworks": [".sldprt", ".sldasm", ".slddrw"],
    "catia": [".catpart", ".catproduct"],
    "parasolid": [".x_t", ".x_b"],
    "acis": [".sat", ".sab"],
    "step": [".step", ".stp"],
    "iges": [".iges", ".igs"],
    "stl": [".stl"],
    "microstation": [".psf", ".dgn"],
    "inventor": [".ipt", ".iam"],
    "fusion360": [".f3d"],
    "onshape": [".onshape"],
    "creo": [".prt", ".asm"],
}
```

**Sources**: [Understanding CAD File Types](https://www.wevolver.com/article/understanding-cad-file-types-a-comprehensive-guide-for-digital-design-and-hardware-engineers)

#### 3. Medical/Healthcare (10+ formats)

```python
MEDICAL_DETECTORS = {
    "dicom": [".dcm", ".dicom"],
    "nifti": [".nii", ".nii.gz"],
    "analyze": [".hdr", ".img"],
    "minc": [".mnc"],
    "nrrd": [".nrrd", ".nhdr"],
}
```

**Sources**: [Medical Image File Formats](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3948928/)

#### 4. Research/Scientific (20+ formats)

```python
RESEARCH_DETECTORS = {
    "latex": [".tex", ".bib", ".cls", ".sty"],
    "r_markdown": [".Rmd", ".Rnw"],
    "jupyter": [".ipynb"],
    "hdf5": [".h5", ".hdf5"],
    "netcdf": [".nc", ".nc4"],
    "fits": [".fits", ".fit"],
    "root": [".root"],
    "igor": [".ibw"],
    "matlab": [".mat", ".m"],
}
```

**Sources**: [Scientific Data Formats](https://programmingforresearch.wordpress.com/2011/06/17/file-formats-for-scientific-data/)

#### 5. Business/Office

```python
OFFICE_DETECTORS = {
    "word": [".doc", ".docx"],
    "excel": [".xls", ".xlsx", ".xlsm"],
    "powerpoint": [".ppt", ".pptx"],
    "access": [".mdb", ".accdb"],
    "onenote": [".one"],
    "visio": [".vsd", ".vsdx"],
    "project": [".mpp"],
}
```

#### 6. Workflow/Automation

```python
AUTOMATION_DETECTORS = {
    "n8n": [".n8n"],
    "github_actions": [".github/workflows/*.yml"],
    "ansible": [".ansible", "playbook.yml"],
    "terraform": [".tf", ".tfvars"],
}
```

#### 7. Personal Organization

```python
ORGANIZATION_DETECTORS = {
    "journal": ["journal/", "diary/"],
    "notes": ["notes/", ".md files"],
    "knowledge_base": [".obsidian/", "zettelkasten/"],
}
```

**Total**: 100+ file type detectors across 7 major categories.

**Community Extensibility** (Future):

- Allow `.claude/detectors/` directory for custom detectors
- Simple Python module API
- Submit PRs to add new detectors to core

---

## UI Implementation Strategy

### Tier 1: Textual TUI (Preferred)

**Library**: Python Textual (https://textual.textualize.io/)

**Features**:

- Rich terminal UI with arrow navigation
- Multi-select checkboxes
- Live search/filter
- Responsive design
- Cross-platform (Windows/Mac/Linux)

**Example Implementation**:

```python
from textual.app import App
from textual.widgets import Checkbox, Button, Static

class ProjectTypeSelector(App):
    """Interactive project type selection."""

    def compose(self):
        yield Static("Select project type(s) (space to check, enter to continue)")
        yield Checkbox("Node.js Application", value=True)
        yield Checkbox("Monorepo", value=True)
        yield Checkbox("Python")
        yield Checkbox("Research/Writing")
        yield Checkbox("CAD/Engineering")
        # ... 30+ options
        yield Button("Continue")
        yield Button("Cancel")
```

### Tier 2: Claude Code Plugin Menu API (If Available)

**Investigation Needed**: Check if Agent SDK exposes plugin menu API

**Potential**: Use same UI as `/plugin` command for consistency

### Tier 3: AskUserQuestion (Fallback)

**When**: Textual not available or user prefers simple prompts

**Strategy**: Show top 3 detected types + "Other" option

**Example**:

```
Question: What type of project is this?
- Node.js Monorepo (detected)
- TypeScript Application (detected)
- React SPA (detected)
- Other (see full list)
```

---

## Session-Start Hook Enhancements

### Updated Responsibilities

```python
def session_start_hook(data):
    """Enhanced session-start with STATUS.json integration."""

    # 1. Check if STATUS.json exists
    status_path = find_status_json()  # Check .claude/, root, ~

    if not status_path:
        # Not initialized
        print("⚠️  PopKit not initialized. Run /popkit:init to set up.", file=sys.stderr)
        return {"status_check": "not_initialized"}

    # 2. Read and validate STATUS.json
    try:
        status = json.loads(status_path.read_text())

        # Validate freshness (< 24h)
        last_update = datetime.fromisoformat(status["lastUpdate"].rstrip("Z"))
        age_hours = (datetime.now() - last_update).total_seconds() / 3600

        if age_hours > 24:
            print(f"⚠️  STATUS.json is stale ({age_hours:.0f}h old). Consider running /popkit-dev:morning.", file=sys.stderr)

        # 3. Extract key info for status line
        git_info = status.get("git", {})
        worktree_info = git_info.get("worktree", {})
        popkit_info = status.get("popkit", {})

        # 4. Pass to morning routine (if running)
        # Morning routine will use this context

        # 5. Update status line (via environment or output)
        # Status line will show: branch, worktree, focus area

        return {
            "status_check": "valid",
            "branch": git_info.get("branch"),
            "worktree": worktree_info.get("name"),
            "focus_area": status.get("context", {}).get("focusArea"),
            "tier": popkit_info.get("tier"),
            "age_hours": age_hours,
        }

    except Exception as e:
        print(f"⚠️  Failed to read STATUS.json: {e}", file=sys.stderr)
        return {"status_check": "corrupted"}
```

**Status Line Integration**:

- Display: `[feat-init-overhaul | init-overhaul worktree | Free]`
- Live updates: Poll git status every 30s, update status line
- Indicator: Show 🔵 when PopKit skill is running

---

## Personas Integration (Future)

**Related Issue**: TBD (user mentioned personas issue exists)

**Concept**: Auto-select personas based on detected project type

**Example**:

```python
PERSONA_MAPPING = {
    "medical_imaging": {
        "personas": ["medical_researcher", "radiologist"],
        "skills": ["pop-medical-analysis", "pop-dicom-viewer"],
    },
    "academic_paper": {
        "personas": ["academic_researcher", "technical_writer"],
        "skills": ["pop-latex-helper", "pop-citation-manager"],
    },
    "cad_mechanical": {
        "personas": ["mechanical_engineer", "cad_specialist"],
        "skills": ["pop-cad-validator", "pop-drawing-checker"],
    },
}

def select_personas(project_type):
    """Auto-select personas based on project type."""
    return PERSONA_MAPPING.get(project_type, {})
```

**During Init**:

1. Detect project type
2. Look up recommended personas
3. Ask user: "Enable recommended personas? [Researcher, Writer]"
4. Load persona-specific skills

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

- [ ] Update session-start.py: Add STATUS.json checking (read-only)
- [ ] Create /popkit:init command skeleton
- [ ] Implement file type detector registry (100+ types)
- [ ] Update STATUS.json schema (add worktree, popkit sections)
- [ ] Write unit tests for detectors

### Phase 2: Smart Detection (Week 2)

- [ ] Implement three-tier detection (file scan → drill-down → CLAUDE.md)
- [ ] Smart CLAUDE.md reader (iterative, early-exit)
- [ ] Confidence calculation logic
- [ ] Programming specifics drill-down (30+ frameworks)
- [ ] Test with real projects (code, research, CAD, etc.)

### Phase 3: Interactive UI (Week 3)

- [ ] Implement Textual TUI for project type selection
- [ ] Multi-select checkboxes, arrow navigation
- [ ] Fallback to AskUserQuestion
- [ ] Redesigned 4 questions (workflow, type, quality, tier)
- [ ] Progressive disclosure based on confidence

### Phase 4: Config Generation (Week 4)

- [ ] Generate config.json from detection + answers
- [ ] Initialize STATUS.json with proper schema
- [ ] Create directory structure (.claude/popkit/\*)
- [ ] Optional CLAUDE.md enhancement (surgical insert)
- [ ] Success summary display

### Phase 5: Testing & Polish (Week 5)

- [ ] Integration tests: code projects, research, CAD, office
- [ ] Test reinit scenarios (already initialized)
- [ ] Test low confidence scenarios (full questions)
- [ ] Documentation: getting-started.md, video tutorial
- [ ] Community feedback and iteration

---

## Success Criteria

1. **Intelligence**: 85%+ of projects auto-detected without questions
2. **Inclusivity**: Works for code, research, CAD, medical, office projects
3. **UX**: Users say "that was fast and accurate"
4. **Worktree Support**: El Shaddai-style workflow is first-class
5. **Status Line**: Live updates showing branch/worktree/focus
6. **Morning Routine**: Uses STATUS.json to restore context
7. **Backward Compat**: Existing PopKit projects continue working

---

## Open Questions

1. **Textual Dependency**: Should Textual be a required dependency or optional?
   - **Recommendation**: Optional, fall back to AskUserQuestion

2. **CLAUDE.md Insertion**: Always ask, or auto-insert with opt-out?
   - **Recommendation**: Ask user, default to Yes

3. **Reinit Logic**: How aggressive should update detection be?
   - **Recommendation**: Conservative, only suggest update if major changes

4. **Personas**: Implement now or wait for separate issue?
   - **Recommendation**: Wait, focus on core init first

5. **Community Detectors**: Build extensibility now or later?
   - **Recommendation**: Later, add detectors manually as needed for now

---

## Related Issues

- **Issue #65**: Interactive questions in /popkit:project init (basis for this design)
- **Personas Issue**: TBD (mentioned by user, not found in search)

---

## References

- [Programming Languages File Extensions](https://gist.github.com/ppisarczyk/43962d06686722d26d176fad46879d41)
- [CAD File Types Guide](https://www.wevolver.com/article/understanding-cad-file-types-a-comprehensive-guide-for-digital-design-and-hardware-engineers)
- [Medical Image File Formats](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3948928/)
- [Scientific Data Formats](https://programmingforresearch.wordpress.com/2011/06/17/file-formats-for-scientific-data/)
- [List of File Formats - Wikipedia](https://en.wikipedia.org/wiki/List_of_file_formats)
- [Python Textual Library](https://textual.textualize.io/)

---

## Conclusion

This design provides a comprehensive overhaul of PopKit initialization that:

1. Separates concerns (session-start reads, /popkit:init writes)
2. Intelligently detects project types across 7 categories (100+ file types)
3. Minimizes user questions through high-confidence auto-detection
4. Supports worktree workflows as a first-class citizen
5. Creates proper STATUS.json and config.json
6. Integrates with status line for live git/worktree visibility
7. Provides foundation for future personas integration

**Ready for implementation in 5 phases over 5 weeks.**
