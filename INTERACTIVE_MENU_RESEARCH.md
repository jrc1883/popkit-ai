# Interactive Menu Integration Strategy for PopKit

**Document Status:** Research & Architecture Planning
**Last Updated:** 2025-12-10
**Phase:** Discovery & Requirements Analysis

---

## Executive Summary

This document outlines a comprehensive strategy for integrating interactive menu sessions into PopKit, focusing on three primary areas:

1. **Interactive Menu Capabilities** - What Claude Code offers, current limitations, and workarounds
2. **Custom Routine Enhancement** - Allowing users to compose morning/nightly routines with interactive menu-based selection
3. **Automated Research Monitoring** - Integrating GitHub changelog automation with interactive menu displays for dynamic information gathering

The strategy leverages PopKit's existing `AskUserQuestion` tool (currently used for decisions) and extends it with checkbox-based multi-select flows for routine customization and research automation.

---

## Part 1: Interactive Menu Capabilities in Claude Code

### 1.1 Current State of AskUserQuestion Tool

PopKit currently implements the `AskUserQuestion` tool as its primary interactive menu mechanism. This tool supports:

#### Parameters

```json
{
  "questions": [
    {
      "question": "Clear question ending with a question mark?",
      "header": "Label (max 12 chars)",
      "options": [
        {
          "label": "Option A",
          "description": "Detailed description of what this does"
        },
        {
          "label": "Option B",
          "description": "What happens if you pick this"
        }
      ],
      "multiSelect": false
    }
  ]
}
```

#### Key Capabilities

| Feature | Status | Notes |
|---------|--------|-------|
| Single-select (radio buttons) | ✅ Fully supported | Default `multiSelect: false` |
| Multi-select (checkboxes) | ✅ Fully supported | Set `multiSelect: true` |
| Multiple questions per call | ✅ Fully supported | Use `questions` array |
| Option descriptions | ✅ Fully supported | Improves UX clarity |
| Custom text input | ✅ Automatic | "Other" option auto-added |
| Keyboard navigation | ✅ Vim-style (j/k) | Arrow keys also supported |
| Session persistence | ⚠️ Partial | Via hooks + STATUS.json |

#### Current Usage in PopKit

PopKit uses `AskUserQuestion` in these contexts:
- **Project initialization** - Next action selection (`pop-project-init`)
- **Brainstorming** - Design path selection (`pop-brainstorming`)
- **Plan execution** - Approach confirmation (`pop-executing-plans`)
- **Bug sharing** - Privacy level selection (`pop-bug-consent`)
- **Research capture** - Entry type selection (`pop-research-capture`)
- **Decision tracking** - Skill completion decisions (framework in `agents/config.json`)

### 1.2 Critical Limitations

#### Mode Restrictions (Bug #10229)

**Issue:** AskUserQuestion only works reliably in **Plan Mode**

```
Mode Support:
├─ Plan Mode:     ✅ Full support - user sees prompts, can interact
├─ Build Mode:    ❌ Tool executes but returns empty results
├─ Deploy Mode:   ❌ Tool executes but returns empty results
└─ No Mode:       ⚠️ Fallback behavior - may vary
```

**Workaround Strategy:**
- Always provide fallback text-based options in Build/Deploy modes
- Document as "Plan Mode recommended" in skills
- Use hooks to detect mode and adjust behavior

#### Not Currently Supported

| Feature | Alternative |
|---------|------------|
| **Tab-based interfaces** | Sequential questions or markdown with formatting |
| **Progress bars in prompts** | Status line widgets or inline progress (text) |
| **Sliders/toggles** | Multi-select checkboxes or radio buttons |
| **Nested/hierarchical menus** | Sequential questions (ask parent, then child) |
| **Conditional logic** | Pre-compute menu variants or use agents |
| **Real-time streaming** | Display results, then ask next question |
| **Session state replay** | Implement via hooks + STATUS.json (PopKit pattern) |

#### Status Line Tabs (Partial Alternative)

Claude Code 2.0 introduced a **three-tab status line** with Tab key navigation:
- Tab 1: Session metrics
- Tab 2: Configuration display
- Tab 3: Usage data

**Current limitation:** This is read-only status display, not interactive menu navigation. However, it provides inspiration for future multi-tab workflow designs.

### 1.3 Best Practices from PopKit Implementation

PopKit implements `AskUserQuestion` with these best practices:

#### 1. Decision Tracking Framework (agents/config.json)

```json
{
  "skill_decisions": {
    "skills": {
      "my-skill": {
        "completion_decisions": [
          {
            "id": "unique_decision_id",
            "question": "What would you like to do next?",
            "header": "Next Step",
            "options": [
              {
                "label": "Create plan",
                "description": "Use pop-writing-plans to develop detailed steps"
              },
              {
                "label": "Skip for now",
                "description": "I'll continue manually"
              }
            ]
          }
        ]
      }
    }
  }
}
```

**Why this matters:** Decisions are tracked via hooks (`pre-tool-use.py`, `post-tool-use.py`), enabling:
- Enforcement of required decision points
- Session continuity (STATUS.json can record choices)
- Skill state tracking (`SkillStateTracker` in hooks/utils)

#### 2. Always Use Descriptions

```python
# WRONG - Don't do this:
options = [
  {"label": "Option A"},
  {"label": "Option B"}
]

# CORRECT - Include descriptions:
options = [
  {
    "label": "Option A",
    "description": "This choice will do X and then Y"
  },
  {
    "label": "Option B",
    "description": "This choice will do Z instead"
  }
]
```

#### 3. Keep Header Labels Short (≤12 characters)

Valid headers:
- "Next Step" ✅
- "Config" ✅
- "Approach" ✅
- "Very Long Header Text Here" ❌

#### 4. Limit Options to 2-4 Choices

- 2-3 options: Ideal (minimal cognitive load)
- 4 options: Maximum (can include "Other")
- 5+ options: Break into multiple questions

#### 5. Multi-Select for Collections

When allowing users to select multiple items (checkboxes):

```python
Use AskUserQuestion tool with:
- question: "Select all that apply:"
- header: "Selection"
- options: [
    {"label": "Item 1", "description": "Description"},
    {"label": "Item 2", "description": "Description"},
    {"label": "Item 3", "description": "Description"},
  ]
- multiSelect: true  # Enable checkboxes
```

Result: User can select multiple items with checkboxes, confirm when done.

---

## Part 2: Extending Routines with Interactive Customization

### 2.1 Current Routine Architecture

PopKit's routine system is modular and extensible:

```
.claude/popkit/
├── config.json              # Project config
├── state.json              # Session state
└── routines/
    ├── morning/
    │   ├── pk/             # Built-in (read-only)
    │   └── rc-1/           # Custom (mutable)
    │       ├── routine.md
    │       ├── config.json
    │       └── checks/
    └── nightly/
        ├── pk/
        └── custom routines...
```

**Current Extensibility:**
- Users can create custom routines via `/popkit:routine morning generate`
- Routines stored in project-specific folders (.claude/popkit/routines/)
- Limited to 5 custom routines per type (morning/nightly)
- Each routine has YAML metadata + markdown documentation + JSON config

### 2.2 Proposed: Interactive Routine Composition

**Vision:** Allow users to build custom morning/nightly routines via interactive menu selection.

#### Scenario 1: Research-Enabled Morning Routine

A user wants a morning routine that:
1. Runs standard git/code quality checks ✅ (already supported)
2. **NEW**: Automatically checks for updates to Claude Code documentation
3. **NEW**: Shows a summary of new features/changes that day
4. **NEW**: Allows selection of specific research to review

**Flow:**

```
/popkit:routine morning generate

[Step 1] Project detected: popkit
[Step 2] Standard checks selected:
  ✓ Git status
  ✓ TypeScript errors
  ✓ Tests passing
  ✓ Services running

[Step 3] Use AskUserQuestion tool with:
- question: "Add research monitoring to this routine?"
- header: "Research"
- options:
  - label: "Yes, track Claude Code updates"
    description: "Daily changelog from jrc1883/claude-code GitHub"
  - label: "Yes, track PopKit updates"
    description: "Daily changelog from jrc1883/popkit GitHub"
  - label: "Track both"
    description: "Monitor both Claude Code and PopKit updates"
  - label: "No research"
    description: "Skip research integration"
- multiSelect: false

[Step 4] Use AskUserQuestion tool with:
- question: "Configure research options (select all that apply):"
- header: "Research"
- options:
  - label: "Show summary only"
    description: "Display changelog summary without details"
  - label: "Highlight breaking changes"
    description: "Emphasize changes that might affect current work"
  - label: "Show performance metrics"
    description: "Include benchmark improvements/regressions"
  - label: "Interactive review mode"
    description: "Allow selecting specific entries to review"
- multiSelect: true

[Step 5] Interactive research review enabled!
When you run `/popkit:routine morning`, you'll be shown:
  - Summary of new changes since last run
  - Interactive menu to review specific entries
  - Ability to save findings to /popkit:research database
```

#### Data Flow for Research Integration

```
┌─────────────────────────────────────────┐
│ /popkit:routine morning                 │
│ (with research enabled)                 │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ [1] Run standard checks (git, tests)    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ [2] Check research_config.json          │
│     - enabled repositories              │
│     - last_checked timestamp            │
│     - options (summary, interactive)    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ [3] Call GitHub API                     │
│     - Get latest releases               │
│     - Filter by date since last run     │
│     - Extract changelog summary         │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ [4] Render findings                     │
│     If interactive: AskUserQuestion     │
│       "Review these changes?"            │
│       - Change 1 (New feature)          │
│       - Change 2 (Bug fix)              │
│       - Change 3 (Breaking change)      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ [5] User selects changes to review     │
│     (multiSelect: true)                 │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ [6] Display full details + save option  │
│     "Save to research database?"        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ [7] Continue with Ready to Code score   │
│     (existing routine finalization)     │
└─────────────────────────────────────────┘
```

### 2.3 Implementation: Interactive Routine Config Schema

**New file:** `.claude/popkit/routines/morning/rc-1/research.json`

```json
{
  "enabled": true,
  "type": "github_changelog",
  "repositories": [
    {
      "owner": "jrc1883",
      "repo": "claude-code",
      "display_name": "Claude Code",
      "check_interval_hours": 24,
      "last_checked": "2025-12-09T08:00:00Z"
    },
    {
      "owner": "anthropics",
      "repo": "claude-code",
      "display_name": "Claude Code (Official)",
      "check_interval_hours": 24,
      "last_checked": "2025-12-09T08:00:00Z"
    }
  ],
  "options": {
    "show_summary_only": false,
    "highlight_breaking_changes": true,
    "show_performance_metrics": true,
    "interactive_review": true,
    "auto_save_to_research": true
  },
  "filtering": {
    "exclude_prerelease": false,
    "exclude_draft": true,
    "min_importance_level": "low"  // low, medium, high
  }
}
```

### 2.4 Interactive Menu Flow for Routine Customization

**During routine generation**, use `AskUserQuestion` with `multiSelect: true` to allow users to build their routine:

```
Use AskUserQuestion tool with:
- question: "Which checks should this routine include? (select all that apply)"
- header: "Routine"
- options:
  - label: "Git status & branch sync"
    description: "Check for uncommitted changes, remote updates"
  - label: "Code quality (TypeScript/Lint)"
    description: "Type errors and linting issues"
  - label: "Tests"
    description: "Run test suite and report failures"
  - label: "Services (dev server, DB)"
    description: "Check if dev server, database, and services are running"
  - label: "Research monitoring"
    description: "Track GitHub changelogs for your dependencies"
  - label: "Custom checks"
    description: "Project-specific health checks (eBay API, Stripe keys)"
- multiSelect: true
```

**User selects:** [Git status, Code quality, Services, Research monitoring]

**Then prompt:** (if Research monitoring selected)

```
Use AskUserQuestion tool with:
- question: "Configure research monitoring:"
- header: "Research"
- options:
  - label: "Track Claude Code updates"
    description: "Daily updates from Claude Code GitHub"
  - label: "Track PopKit updates"
    description: "Daily updates from PopKit GitHub"
  - label: "Track custom repos"
    description: "Add your own GitHub repositories"
- multiSelect: true
```

---

## Part 3: Automated Research Monitoring Architecture

### 3.1 GitHub API Integration for Changelog Automation

PopKit can integrate with GitHub's REST API to automatically fetch and process changelogs.

#### API Endpoints

**Latest Release (Simple):**
```
GET /repos/{owner}/{repo}/releases/latest
```

Returns the most recent non-prerelease, non-draft release with:
- `tag_name` - Version tag
- `name` - Release title
- `body` - Full release notes (markdown)
- `created_at` - When released
- `published_at` - When published

**All Releases (With Filtering):**
```
GET /repos/{owner}/{repo}/releases?per_page=5&page=1
```

Returns paginated list of releases. Can filter by:
- Prerelease status
- Draft status
- Created date range

**Auto-Generated Release Notes (Most Powerful):**
```
POST /repos/{owner}/{repo}/releases/generate-notes
{
  "tag_name": "v2.0.0",
  "previous_tag_name": "v1.9.0"
}
```

Returns GitHub's AI-powered analysis of:
- New features (extracted from PR titles and labels)
- Bug fixes
- Breaking changes
- New contributors
- Full formatted markdown changelog

#### Rate Limiting

| Endpoint Type | Authenticated | Rate Limit |
|---------------|---------------|-----------|
| Releases API | ✅ With token | 5,000/hour |
| Releases API | ❌ Anonymous | 60/hour |
| Auth not required | For public repos | Higher limits |

**Recommendation:** Implement token support in PopKit Cloud API for reliable access.

### 3.2 Change Detection Strategy

**Problem:** Compare changelogs between runs and only show what's NEW.

**Solution: Timestamp-Based Comparison**

```python
def get_new_releases(repo_owner, repo_name, last_checked_timestamp):
    """
    Fetch releases since last check.

    Args:
        repo_owner: GitHub username (e.g., "jrc1883")
        repo_name: Repository name (e.g., "claude-code")
        last_checked_timestamp: ISO 8601 timestamp of last check

    Returns:
        List of new releases since last_checked_timestamp
    """
    # Fetch releases (will be returned in reverse chronological order)
    releases = github_api_call(f"/repos/{repo_owner}/{repo_name}/releases")

    # Filter releases newer than last check
    new_releases = []
    for release in releases:
        published = datetime.fromisoformat(release['published_at'])
        last_checked = datetime.fromisoformat(last_checked_timestamp)

        if published > last_checked:
            new_releases.append(release)
        else:
            break  # Releases are in reverse chronological order

    return new_releases
```

**Storage:** Update `research.json` with new `last_checked` timestamp

```json
{
  "repositories": [
    {
      "owner": "jrc1883",
      "repo": "claude-code",
      "last_checked": "2025-12-10T10:30:00Z"  // Updated after each check
    }
  ]
}
```

### 3.3 Interactive Research Review Flow

**When user runs `/popkit:routine morning` with research enabled:**

```
Step 1: Fetch changelogs
  ✓ Claude Code: 3 new releases since 2025-12-09
  ✓ PopKit: 0 new releases

Step 2: Use AskUserQuestion to show findings
  Use AskUserQuestion tool with:
  - question: "Review these changes from the last 24 hours?"
  - header: "Research"
  - options:
    - label: "Claude Code v2.0.21 - New: Extended Thinking in Haiku"
      description: "Enable 5k token thinking budget in Claude Haiku mode (-T flag)"
    - label: "Claude Code v2.0.20 - Fix: AskUserQuestion reliability"
      description: "Improved tool response handling in Plan Mode"
    - label: "Claude Code v2.0.19 - Feature: Status line tabs"
      description: "Navigate session/config/usage data with Tab key"
  - multiSelect: true

Step 3: User selects items to learn about
  User selects: [v2.0.21, v2.0.19]

Step 4: Display detailed information
  For each selected item:
  - Full changelog text
  - Links to documentation
  - Impact assessment ("affects your workflow" / "good to know")

Step 5: Offer research capture
  Use AskUserQuestion tool with:
  - question: "Save these to your research database?"
  - header: "Save"
  - options:
    - label: "Yes, save all selected"
      description: "Create research entries for each selected change"
    - label: "Save specific entries"
      description: "Choose which ones to save"
    - label: "Skip for now"
      description: "Just display, don't save"
  - multiSelect: false

Step 6: Continue routine
  Display morning summary and Ready to Code score
```

### 3.4 Research Capture Integration

When user selects "Save," PopKit should:

1. **Create research entries** via existing `pop-research-capture` skill
2. **Auto-populate fields:**
   - `type`: "learning" (for changelogs)
   - `title`: Release title with version
   - `content`: Full changelog text
   - `context`: "Found while monitoring {repo} changelog"
   - `tags`: ["research", "automation", repo_name, version_tag]
   - `project`: Current project name
   - `references`: [GitHub release URL]

**Example entry:**

```json
{
  "id": "r042",
  "type": "learning",
  "title": "Claude Code v2.0.21 - Extended Thinking in Haiku",
  "content": "Enable 5k token thinking budget in Claude Haiku mode with -T flag...",
  "context": "Found while monitoring Claude Code changelog during morning routine",
  "tags": ["research", "automation", "claude-code", "v2.0.21", "thinking"],
  "project": "popkit",
  "references": ["https://github.com/anthropics/claude-code/releases/tag/v2.0.21"],
  "createdAt": "2025-12-10T08:15:00Z"
}
```

---

## Part 4: Multi-Tab Interface Alternatives

### 4.1 Current Limitations

Claude Code does **NOT** support interactive multi-tab menus for custom tools. The status line has tabs but they're read-only status display.

### 4.2 Workarounds for Multi-Step Workflows

Instead of tabs, use **sequential interactive prompts**:

**Pattern: Sequential Questions with Context**

```python
# Step 1: Ask first question
Use AskUserQuestion tool with:
- question: "Choose a configuration category:"
- header: "Config"
- options:
  - label: "Research sources"
    description: "Select repositories to monitor"
  - label: "Display options"
    description: "Configure how results are shown"
  - label: "Review settings"
    description: "See current configuration"
- multiSelect: false

# User selects: "Research sources"

# Step 2: Based on previous selection, ask next question
Use AskUserQuestion tool with:
- question: "Which repositories to monitor?"
- header: "Sources"
- options:
  - label: "Claude Code"
    description: "jrc1883/claude-code"
  - label: "PopKit"
    description: "jrc1883/popkit"
  - label: "Custom repos"
    description: "Add your own"
- multiSelect: true
```

This creates a "wizard" flow without requiring actual tabs.

### 4.3 Visual Organization via Markdown

Use markdown formatting to organize information visually:

```markdown
# Research Configuration

## 📍 Step 1: Select Repositories

You've chosen to configure research monitoring.

Use this flow to set up which GitHub repositories to monitor:

### Available Sources

- **Claude Code** (`jrc1883/claude-code`)
  Daily updates on the latest Claude Code features and fixes

- **PopKit** (`jrc1883/popkit`)
  Stay synchronized with PopKit development

- **Anthropic** (`anthropics/claude-code`)
  Official releases and announcements

### Your Selection

When you respond with your choice, we'll move to Step 2.
```

Then use `AskUserQuestion` immediately below for the actual selection.

---

## Part 5: Implementation Roadmap

### Phase 1: Checkbox-Based Routine Customization (Weeks 1-2)

**Goal:** Allow users to interactively build morning/nightly routines via checkboxes

**Tasks:**
1. ✅ Extend `routine_storage.py` to support `research.json` schema
2. ✅ Modify `pop-morning-generator` skill to prompt for research integration
3. ✅ Update `/popkit:routine morning generate` flow:
   - After detecting tech stack
   - Show AskUserQuestion with `multiSelect: true` for routine components
   - Show second AskUserQuestion for research-specific options
4. ✅ Create `research_runner.py` hook utility
5. ✅ Add research config validation in `routine.md` template

**Deliverables:**
- Users can select which components to include in custom routines
- Research monitoring is optional, configurable via JSON
- Generator creates `research.json` when research is selected

### Phase 2: GitHub API Integration (Weeks 2-3)

**Goal:** Fetch and display GitHub changelog updates in morning routine

**Tasks:**
1. ✅ Implement `github_api.py` utility in hooks/utils
   - Fetch latest releases endpoint
   - Parse release metadata
   - Filter by date/importance
   - Handle rate limiting
2. ✅ Create `changelog_processor.py` for change detection
   - Compare timestamps
   - Generate summary text
   - Categorize changes (feature, bugfix, breaking)
3. ✅ Add GitHub token support to PopKit Cloud API (optional)
4. ✅ Integrate into morning routine execution flow

**Deliverables:**
- Morning routine can fetch changelogs from GitHub
- Only NEW changes are shown (timestamp-based)
- Changes are categorized and summarized

### Phase 3: Interactive Research Review (Weeks 3-4)

**Goal:** Use AskUserQuestion to show changelog summaries and allow selection

**Tasks:**
1. ✅ Build `research_review_flow.py` with AskUserQuestion integration
2. ✅ Create changelog formatting for menu display
3. ✅ Integrate with `pop-research-capture` skill
4. ✅ Add "save to research database" flow
5. ✅ Testing with mock changelog data

**Deliverables:**
- Morning routine shows interactive menu of new changes
- Users can select which changes to review
- Selected changes can be saved to research database
- Full changelog details displayed for selected items

### Phase 4: Extension & Polish (Weeks 4+)

**Goal:** Extend to other routines and use cases

**Tasks:**
1. ✅ Add research monitoring to nightly routines
2. ✅ Support custom GitHub repositories
3. ✅ Create `/popkit:research-monitor` command for standalone use
4. ✅ Add filtering options (exclude prerelease, draft, etc.)
5. ✅ Performance optimization (caching, rate limit handling)
6. ✅ Documentation and examples

---

## Part 6: Code Examples

### 6.1 Extended Routine Config with Research

**File:** `.claude/popkit/routines/morning/rc-1/routine.md`

```markdown
---
id: rc-1
name: Popkit Development Morning Check
type: morning
research_enabled: true
research_repos:
  - owner: jrc1883
    repo: claude-code
  - owner: anthropics
    repo: claude-code
---

# Morning Routine: Popkit Development Check

## Automated Checks

1. Git status and remote sync
2. TypeScript compilation
3. Lint validation
4. Test suite
5. Service health checks (Next.js, Supabase, Redis)

## Research Monitoring

When you run this routine, you'll be notified of:
- New Claude Code releases and features
- Updates to the official Claude Code repository
- Breaking changes that might affect PopKit

You can interactively select which changes to review and save them to your research database.
```

### 6.2 Research Integration in Morning Generator Skill

```python
# In pop-morning-generator skill prompt

def generate_with_research_option():
    """Generate routine with optional research monitoring."""

    # After detecting tech stack...

    # Prompt 1: Should we add research monitoring?
    Use AskUserQuestion tool with:
    - question: "Add research monitoring to this routine?"
    - header: "Research"
    - options:
      - label: "Yes, track Claude Code"
        description: "Monitor jrc1883/claude-code for updates"
      - label: "Yes, track official Claude"
        description: "Monitor anthropics/claude-code updates"
      - label: "Track both"
        description: "Get updates from both repositories"
      - label: "No research"
        description: "Skip research integration"
    - multiSelect: false

    # If research selected, Prompt 2: Configure options
    if user_selected_research:
        Use AskUserQuestion tool with:
        - question: "Configure research display:"
        - header: "Display"
        - options:
          - label: "Show summary only"
            description: "Brief list of new changes"
          - label: "Interactive review"
            description: "Select which changes to examine"
          - label: "Auto-save findings"
            description: "Automatically save to research database"
        - multiSelect: true

        # Create research.json with user selections
        research_config = {
            "enabled": True,
            "repositories": selected_repos,
            "options": {
                "show_summary": "summary" in user_options,
                "interactive_review": "interactive" in user_options,
                "auto_save": "auto-save" in user_options
            }
        }
        save_to_file(".claude/popkit/routines/morning/rc-1/research.json", research_config)
```

### 6.3 Morning Routine Execution with Research

```python
# In routine execution hook

def run_morning_routine_with_research(routine_id):
    """Execute morning routine including research monitoring."""

    # Load routine config
    config = load_routine_config(routine_id)

    # Run standard checks
    results = run_standard_checks(config)

    # Check for research config
    if has_research_enabled(routine_id):
        research_config = load_research_config(routine_id)

        # Fetch changelogs
        changelogs = []
        for repo in research_config['repositories']:
            changelog = fetch_github_changelog(
                repo['owner'],
                repo['name'],
                last_checked=research_config['last_checked']
            )
            changelogs.append((repo, changelog))

        # If interactive review enabled
        if research_config['options']['interactive_review']:
            selected = show_research_review_menu(changelogs)

            # Display details for selected items
            for changelog_item in selected:
                print_full_changelog_details(changelog_item)

            # Offer to save
            if should_save_findings():
                for item in selected:
                    create_research_entry_from_changelog(item)

        # Update last_checked timestamp
        research_config['last_checked'] = datetime.now().isoformat() + 'Z'
        save_research_config(routine_id, research_config)

    # Display final results
    display_ready_to_code_score(results)
```

---

## Part 7: Practical Recommendations

### 7.1 Recommended Approach

**Start simple, iterate based on feedback:**

1. **Month 1:** Implement Phase 1 & 2 (routine customization + GitHub API)
   - Users can build interactive routines via checkboxes
   - Morning routine can fetch changelogs
   - No complex interactive review yet (just display summary)

2. **Month 2:** Add Phase 3 (interactive research review)
   - AskUserQuestion-based changelog review
   - Multi-select for choosing which changes to examine
   - Integration with research database

3. **Beyond:** Extend to other use cases
   - Nightly routine research
   - Standalone `/popkit:research-monitor` command
   - Custom repository support

### 7.2 User Experience Progression

**For different user types:**

#### Beginner
- Use default `/popkit:routine morning`
- No research integration
- Simple summary output

#### Intermediate
- Generate custom routine with `morning generate`
- Select which checks to include (interactive menu)
- Enable research monitoring with defaults

#### Advanced
- Custom research repositories
- Filtering options (exclude prerelease, min importance)
- Automated research entry creation
- Custom bash scripts + research integration

### 7.3 Fallback Patterns for Plan Mode Limitation

Since `AskUserQuestion` only works reliably in Plan Mode:

```python
def ask_user_with_fallback(question, header, options, multiSelect=False):
    """
    Try AskUserQuestion first, fall back to text if needed.
    """
    try:
        # Try interactive
        Use AskUserQuestion tool with:
        - question: {question}
        - header: {header}
        - options: {options}
        - multiSelect: {multiSelect}

    except Exception:
        # Fallback to text
        print(f"{header}: {question}")
        for i, opt in enumerate(options, 1):
            print(f"{i}. {opt['label']}")
            print(f"   {opt['description']}")
        print("\nEnter choice (text-based fallback)")
```

---

## Part 8: GitHub API References

### 8.1 Useful Endpoints

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `GET /repos/{owner}/{repo}/releases/latest` | Get latest release | Quick check for newest version |
| `GET /repos/{owner}/{repo}/releases` | List all releases | Paginated with filters |
| `POST /repos/{owner}/{repo}/releases/generate-notes` | AI-powered changelog | Auto-categorize changes |
| `GET /repos/{owner}/{repo}/commits` | Get commit history | Fine-grained change tracking |
| `GET /user` | Verify auth | Check token validity |

### 8.2 Response Format Example

```json
{
  "id": 163104139,
  "tag_name": "v2.0.21",
  "target_commitish": "main",
  "name": "v2.0.21 - Extended Thinking in Haiku",
  "draft": false,
  "prerelease": false,
  "created_at": "2025-12-10T10:30:00Z",
  "published_at": "2025-12-10T10:35:00Z",
  "body": "## New Features\n\n- Extended thinking budget in Haiku mode (5k tokens)\n\n## Bug Fixes\n\n- Fixed AskUserQuestion tool reliability",
  "author": {
    "login": "octocat",
    "id": 1,
    "type": "User"
  },
  "assets": []
}
```

---

## Part 9: Testing & Validation Strategy

### 9.1 Unit Tests

```python
# Test timestamp comparison
def test_get_new_releases_filters_by_date():
    last_checked = "2025-12-09T00:00:00Z"
    releases = [
        {"published_at": "2025-12-10T10:00:00Z"},  # NEW
        {"published_at": "2025-12-08T10:00:00Z"},  # OLD
    ]
    result = filter_new_releases(releases, last_checked)
    assert len(result) == 1

# Test research config schema
def test_research_config_validation():
    config = load_research_config("rc-1")
    assert "repositories" in config
    assert "options" in config
    for repo in config['repositories']:
        assert "owner" in repo
        assert "repo" in repo
```

### 9.2 Integration Tests

```python
# Test full morning routine with research
def test_morning_routine_with_research():
    # Mock GitHub API
    mock_releases = [
        {"published_at": "2025-12-10T10:00:00Z", "name": "v2.0.21"}
    ]

    # Run routine
    results = run_morning_routine("rc-1")

    # Verify research was included
    assert "research" in results
    assert len(results["research"]["new_releases"]) == 1

# Test interactive menu
def test_research_review_menu():
    # Simulate user selecting items
    user_selection = ["v2.0.21", "v2.0.20"]

    # Run menu and capture selection
    selected = show_research_review_menu(mock_changelogs)
    assert selected == user_selection
```

### 9.3 Manual Testing Checklist

- [ ] Generate custom routine with research enabled
- [ ] Run morning routine and see research menu
- [ ] Select multiple changelog items
- [ ] View full details for selected items
- [ ] Save findings to research database
- [ ] Verify last_checked timestamp updated
- [ ] Run routine again, verify only NEW items shown
- [ ] Test with both repositories (Claude Code + PopKit)
- [ ] Test fallback behavior in non-Plan mode

---

## Part 10: Future Expansion Ideas

### 10.1 Beyond GitHub Changelogs

The architecture can extend to monitor:
- **npm package updates** - Monitor dependencies for security updates
- **Documentation changes** - Track docs.anthropic.com updates
- **Blog posts** - Follow Anthropic's engineering blog
- **Community resources** - Monitor popular Claude Code extensions
- **Custom webhooks** - User-defined monitoring endpoints

### 10.2 Smart Recommendations

Could add ML-powered recommendations:
- "You use Next.js, here's what's new in Next.js"
- "Your dependencies have 3 new versions available"
- "Breaking changes detected in your stack"

### 10.3 Team Sync

For multi-developer teams:
- Shared research database (already supports this)
- Daily digest email of team's researched changes
- Highlight changes relevant to team's current sprint

### 10.4 Marketplace Integration

Could integrate with PopKit marketplace:
- "New PopKit skills available"
- "Popular skills your team should know about"
- "Templates matching your project type"

---

## Conclusion

Interactive menus in PopKit are ready to be enhanced beyond simple decision prompts. By leveraging `AskUserQuestion`'s checkbox support (`multiSelect: true`), PopKit can enable:

1. **Interactive routine customization** - Users build routines via menus
2. **Automated research monitoring** - GitHub changelog automation
3. **Dynamic information discovery** - Select and save relevant changes

The proposed architecture is pragmatic, building on existing PopKit patterns (hooks, decision tracking, STATUS.json), and accounts for current Claude Code limitations (Plan Mode requirement, no tabs).

Implementation should proceed iteratively, validating each phase with users before moving to the next.

---

## Appendix: Key Files & References

### PopKit Source Files
- `packages/plugin/hooks/utils/routine_storage.py` - Routine management
- `packages/plugin/skills/pop-morning-generator/SKILL.md` - Morning generation
- `packages/plugin/commands/routine.md` - Routine command documentation
- `packages/plugin/agents/config.json` - Decision framework
- `packages/plugin/hooks/utils/skill_state.py` - Decision tracking

### GitHub API Documentation
- [REST API Releases Endpoint](https://docs.github.com/en/rest/releases/releases)
- [Automatically Generated Release Notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes)
- [Releases | GitHub Docs](https://docs.github.com/en/rest/releases)

### Claude Code References
- AskUserQuestion tool (used throughout PopKit)
- Plan Mode (required for interactive menus)
- Status line (read-only tabs in Claude Code 2.0)

### External Resources
- [changelog-from-release - GitHub Tool](https://github.com/rhysd/changelog-from-release)
- [GitHub Changelog Blog](https://github.blog/changelog/)
- [release-it - Version Management](https://github.com/release-it/release-it)

---

**Document Version:** 1.0
**Author:** PopKit Research Team
**Date:** 2025-12-10
**Status:** Ready for Architecture Review
