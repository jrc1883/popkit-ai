# PopKit Initialization & Entry Point Analysis

**Date:** 2025-12-14
**Author:** Claude Code
**Status:** Research Complete
**Urgency:** P1 - Critical for v1.0 user experience

---

## Executive Summary

PopKit has a **two-tier initialization system** that is not transparent to new users. This creates confusion and degraded capabilities when users start using PopKit without explicit initialization.

### Key Findings

1. **Two-Tier Initialization Exists**
   - **Tier 1 (Automatic):** `SessionStart` hook silently creates `.claude/popkit/` directories
   - **Tier 2 (Explicit):** `/popkit:project init` creates full `.claude/` structure + project metadata

2. **No Entry Point Messaging**
   - When users install PopKit and restart Claude Code, nothing indicates they should run `/popkit:project init`
   - No "welcome" message or onboarding flow
   - Commands work in "degraded mode" without user awareness

3. **Capabilities Degrade Silently**
   - Commands like `/popkit:next` and `/popkit:routine morning` work with reduced awareness
   - No warnings that initialization would unlock full capabilities
   - Users may think PopKit isn't working properly when it's actually working with limited context

4. **Critical Gaps in Current Flow**
   - No way to detect if a project has been "properly" initialized
   - Commands don't suggest init when it would help
   - No progress indicators or checklists for the user
   - Post-init guidance is ambiguous

---

## Current Initialization Flow

### Tier 1: Automatic (SessionStart Hook)

**When:** Every Claude Code session starts
**Where:** `packages/plugin/hooks/session-start.py`
**What:** Silent, idempotent auto-initialization

```
User installs PopKit
         ↓
Restart Claude Code
         ↓
[SessionStart Hook Fires]
         ├─→ Log session start
         ├─→ Check for updates (non-blocking)
         ├─→ Register with PopKit Cloud (non-blocking)
         └─→ Auto-create .claude/popkit/ (idempotent)
                ├─ .claude/popkit/
                ├─ .claude/popkit/routines/morning/
                ├─ .claude/popkit/routines/nightly/
                └─ .claude/popkit/config.json
```

**What Gets Created:**

| File | Purpose | Auto-Init | Tier 1 | Tier 2 |
|------|---------|-----------|--------|--------|
| `.claude/popkit/config.json` | Project configuration | ✅ YES | ✅ | ✅ |
| `.claude/popkit/routines/morning/` | Morning routine directory | ✅ YES | ✅ | ✅ |
| `.claude/popkit/routines/nightly/` | Nightly routine directory | ✅ YES | ✅ | ✅ |
| `.claude/STATUS.json` | Session state tracking | ❌ NO | ❌ | ✅ |
| `.claude/settings.json` | Claude settings + PopKit fields | ❌ NO | ❌ | ✅ |
| `CLAUDE.md` (PopKit section) | Project instructions | ❌ NO | ❌ | ✅ |
| `.claude/agents/` | Custom agent definitions | ❌ NO | ❌ | ✅ |
| `.claude/skills/` | Custom project skills | ❌ NO | ❌ | ✅ |
| `.claude/hooks/` | Custom hooks | ❌ NO | ❌ | ✅ |

**Conditions for Auto-Init:**
- Only creates if `.git/` OR `CLAUDE.md` exists (avoids polluting random directories)
- Idempotent - safe to run multiple times
- All failures are silent (never blocks session start)

**Code Behavior:**
```python
# From session-start.py line 136-140
if not (cwd / ".git").exists() and not (cwd / "CLAUDE.md").exists():
    return None  # Skip if not in a real project
```

### Tier 2: Explicit (`/popkit:project init`)

**When:** User explicitly runs `/popkit:project init`
**Where:** `packages/plugin/skills/pop-project-init/SKILL.md`
**What:** Full project initialization with user decision points

**8-Step Process:**

```
User runs: /popkit:project init
         ↓
[Step 0] Check for plugin conflicts
         ├─→ [MANDATORY DECISION] Plugin conflict handling
         └─→ Continue or cancel
         ↓
[Step 1] Detect project type
         ├─→ Check for package.json, Cargo.toml, pyproject.toml, go.mod
         └─→ Identify project type (Node, Rust, Python, Go, etc.)
         ↓
[Step 2] Create .claude/ structure
         ├─→ Create agents/, commands/, hooks/, skills/, scripts/, logs/, plans/
         ├─→ Create .claude/popkit/ and subdirectories (idempotent)
         └─→ Add .gitkeep files
         ↓
[Step 2b] Create PopKit config
         ├─→ .claude/popkit/config.json with:
         │   - project_name
         │   - project_prefix (auto-generated)
         │   - tier: "free"
         │   - features: {power_mode: "not_configured", ...}
         └─→ Only creates if doesn't exist
         ↓
[Step 3] Surgically update CLAUDE.md
         ├─→ If exists: Read → Check for <!-- POPKIT:START --> markers
         │   ├─ Has markers: Edit between markers only
         │   └─ No markers: Append PopKit section at end
         ├─→ If not exists: Create minimal file with PopKit section
         └─→ CRITICAL: Never overwrites existing user content
         ↓
[Step 4] Create STATUS.json
         ├─→ Session state tracking with:
         │   - git: {branch, lastCommit, uncommittedFiles}
         │   - tasks: {inProgress: [], completed: []}
         │   - context: {focusArea, nextAction}
         │   - powerMode: {enabled, type, agents}
         └─→ Only creates if doesn't exist
         ↓
[Step 5] Create settings.json
         ├─→ Claude settings with PopKit fields:
         │   - model version
         │   - permissions (allowBash, allowFileOperations, allowGit)
         │   - popkit: {tier, competency_level, features_available}
         └─→ Only creates if doesn't exist
         ↓
[Step 6] Ask about Power Mode setup
         ├─→ [MANDATORY DECISION] Power Mode configuration
         ├─→ Options: File Mode / Redis Self-Hosted / Redis Cloud (Pro) / Skip
         └─→ Update config based on selection
         ↓
[Step 7] Update .gitignore
         ├─→ Add PopKit runtime/session file patterns
         └─→ Only add lines that don't already exist
         ↓
[Step 8] Post-init recommendations
         ├─→ [MANDATORY DECISION] What's next?
         ├─→ Options: Analyze / Setup / View Issues / Done
         └─→ Execute follow-up command or end gracefully
```

---

## Entry Points & Activation

### Where Users First Encounter PopKit

1. **Plugin Installation**
   ```bash
   /plugin marketplace add jrc1883/popkit-claude
   /plugin install popkit@popkit-claude
   # User restarts Claude Code
   ```
   → No message. SessionStart hook silently creates `.claude/popkit/`.

2. **First `/popkit:` Command**
   - User tries `/popkit:next` or `/popkit:routine morning`
   - Command works with degraded capabilities
   - No indication that initialization would help

3. **Manual Initialization**
   - User discovers `/popkit:project init` through docs or experimentation
   - Skill prompts for decisions (Power Mode, next action)
   - Full project awareness is now available

### Hook System (Always Active)

| Hook | Event | Purpose | Idempotent |
|------|-------|---------|-----------|
| `SessionStart` | Every session starts | Auto-init `.claude/popkit/` | ✅ YES |
| `UserPromptSubmit` | Every user message | Detect keywords, route agents, enhance prompt | ✅ YES |
| `PreToolUse` | Before tool execution | Safety checks, premium enforcement | ✅ YES |
| `PostToolUse` | After tool execution | Cleanup, validation, metrics | ✅ YES |

**Key Insight:** Hooks run EVERY session. The SessionStart hook is the only place where auto-initialization happens, and it's completely silent.

---

## Command Degradation Without Initialization

### Commands That Work Without Full Init

#### 1. `/popkit:next` (Context-Aware Recommendations)

**What It Should Do:**
- Analyze git status, TypeScript errors, open issues
- Recommend: commit changes, push branches, work on issues
- Base recommendations on project context from CLAUDE.md

**What Happens Without Init (Degraded Mode):**
- ✅ Detects: git status, uncommitted files, branch sync
- ❌ Missing: Project context from CLAUDE.md
- ❌ Missing: Custom project routines
- ⚠️ Result: Generic recommendations instead of context-aware ones

**Error Handling Code:** `packages/plugin/commands/next.md` lines 179-183
```markdown
| Not a git repo | Skip git analysis, note in output |
| No package.json | Skip Node checks |
| gh CLI unavailable | Skip issue recommendations |
| Empty project | Recommend `/popkit:init-project` |
```

#### 2. `/popkit:routine morning` (Health Check)

**What It Should Do:**
- Show git status, TypeScript health, lint status, tests
- Display deployment health (if configured)
- Show "From Last Night" section (from nightly routine)
- Calculate "Ready to Code" score (0-100)

**What Happens Without Init (Degraded Mode):**
- ✅ Detects: git status, TypeScript, lint, tests (if tools exist)
- ❌ Missing: Deployment status (no `.claude/popkit/config.json` deployments section)
- ⚠️ Missing: "From Last Night" section (no STATUS.json)
- ✅ Works: Basic checks still execute

**Actual Behavior:**
```
Without init:                     With init:
$ /popkit:routine morning         $ /popkit:routine morning

Ready to Code: 85/100             Ready to Code: 85/100
├─ Git Status: Clean              ├─ From Last Night:
├─ TypeScript: No errors          │  ├─ Sleep Score: 92/100
├─ Lint: Clean                    │  └─ Focus: Auth module
├─ Tests: 142 passed              ├─ Git Status: Clean
└─ (missing deployments)          ├─ Deployments: npm, Vercel OK
                                  └─ [Full health dashboard]
```

#### 3. `/popkit:power` (Multi-Agent Mode)

**What It Should Do:**
- Configure Redis (self-hosted or cloud)
- Enable 6+ parallel agents
- Set up Power Mode for orchestration

**What Happens Without Init (Degraded Mode):**
- ✅ File Mode works (2-3 agents, no setup)
- ❌ Redis Mode unavailable (requires `.claude/popkit/config.json` configuration)
- ❌ Cloud Mode unavailable (requires Pro subscription check)
- ⚠️ Result: Limited to file-based coordination

---

## State Management & Context

### STATUS.json Structure (Tier 2 Only)

Created by `/popkit:project init` (never auto-init):

```json
{
  "lastUpdate": "2025-12-14T10:30:00Z",
  "project": "popkit",
  "sessionType": "Fresh",
  "git": {
    "branch": "main",
    "lastCommit": "abc123...",
    "uncommittedFiles": 0
  },
  "tasks": {
    "inProgress": ["issue-42", "feature-auth"],
    "completed": ["setup-tests", "add-linting"]
  },
  "context": {
    "focusArea": "authentication",
    "nextAction": "/popkit:dev work 42"
  },
  "powerMode": {
    "enabled": false,
    "type": null,
    "agents": 0
  },
  "services": {
    "dev_server": "running:3000",
    "database": "connected",
    "redis": "not_configured"
  }
}
```

**What This Enables:**
- `/popkit:routine morning` shows "From Last Night" context
- Commands remember previous session's focus area
- Power Mode knows what agents are active
- Service health tracking across sessions

### .claude/popkit/config.json (Both Tiers)

Auto-created by SessionStart hook, updated by init skill:

```json
{
  "version": "1.0",
  "project_name": "popkit",
  "project_prefix": "pk",
  "initialized_at": "2025-12-14T10:30:00Z",
  "popkit_version": "1.2.0",
  "tier": "free",
  "features": {
    "power_mode": "not_configured",
    "deployments": [],
    "custom_routines": []
  }
}
```

**What This Enables:**
- Project-aware features
- Deployment status tracking
- Custom routine storage
- Tier-gated features (Pro, Free)

---

## Gap Analysis: First-Run Experience

### Gap #1: No Welcome Message

**Problem:**
- User installs PopKit, restarts Claude Code
- SessionStart hook silently creates `.claude/popkit/`
- User sees: Nothing. No message, no guidance.
- User may not even know PopKit is installed

**Current Behavior:**
```python
# From session-start.py line 237
if dirs or config:
    parts = []
    if dirs:
        parts.append(f"directories: {len(dirs)}")
    if config:
        parts.append("config.json")
    print(f"PopKit auto-init: {', '.join(parts)}", file=sys.stderr)

# Output: "PopKit auto-init: directories: 3, config.json"
# → User probably doesn't see this or doesn't understand it
```

**Recommendation:**
Add a "Welcome to PopKit" message on first-ever session that:
- Congratulates user on installation
- Explains two-tier system
- Suggests running `/popkit:project init` for full setup
- Links to quick-start guide

### Gap #2: No Capability Matrix in Docs

**Problem:**
- README shows `/popkit:next` and `/popkit:routine morning` as "quick start" examples
- Doesn't explain what works without init
- User runs these commands, gets generic results, thinks PopKit isn't working

**Current Documentation:**
```markdown
# Quick Start
...
After restart, try:
  /popkit:routine morning    # Morning health check
  /popkit:dev brainstorm     # Start brainstorming a feature
  /popkit:git commit         # Smart commit with auto-message
```

**Missing:**
- Explanation of what "full setup" means
- Capability matrix: what works at each level
- When to run `/popkit:project init`
- Expected output with/without init

**Recommendation:**
Add section to README:

```markdown
## Initialization Levels

PopKit works immediately after install, but with **two levels of capability**:

### Level 1: Auto-Initialized (Default)
After restart, PopKit automatically creates `.claude/popkit/` and you can:
- Use all `/popkit:` commands
- Get generic recommendations from `/popkit:next`
- Run `/popkit:routine morning` (basic health checks)
- Use `/popkit:power` in File Mode (limited agents)

### Level 2: Fully Initialized (Recommended)
After running `/popkit:project init`, you unlock:
- Project-aware recommendations based on your CLAUDE.md
- Full deployment status tracking
- Multi-agent Power Mode (Redis)
- Custom routines and project-specific skills
- Session state persistence via STATUS.json

To upgrade to Level 2, run:
  /popkit:project init
```

### Gap #3: No Detection of Initialization Status

**Problem:**
- Commands don't know if project has been "properly" initialized
- No way to check: `ls .claude/STATUS.json` exists?
- Commands can't suggest init when it would help

**Example:**
```bash
# Without init:
/popkit:next
> [generic recommendations]
> (No message that init would help)

# With init:
/popkit:next
> [context-aware recommendations]
> (No indication this is better because of init)
```

**Recommendation:**
Add initialization status checking to commands:

```python
def check_initialization_status():
    """Check if project has been fully initialized."""
    has_status_json = Path(".claude/STATUS.json").exists()
    has_claude_md = Path("CLAUDE.md").exists() and \
                    "<!-- POPKIT:START -->" in Path("CLAUDE.md").read_text()
    has_full_structure = all([
        Path(".claude/agents").exists(),
        Path(".claude/skills").exists(),
        Path(".claude/hooks").exists()
    ])

    return {
        "auto_init": Path(".claude/popkit/config.json").exists(),
        "full_init": has_status_json and has_claude_md,
        "complete": has_full_structure
    }
```

Then in commands:
```python
status = check_initialization_status()
if not status["full_init"]:
    print("💡 Run /popkit:project init for full project awareness",
          file=sys.stderr)
```

### Gap #4: Unclear Decision Flow After Init

**Problem:**
- After `/popkit:project init`, skill asks: "What's next?"
- Options are: Analyze / Setup / View Issues / Done
- Not clear which option is recommended for first-time users

**Current Decision Point:**
```
Use AskUserQuestion tool with:
- options:
  - label: "Analyze codebase"
    description: "Run /popkit:project analyze for deep codebase analysis"
  - label: "Setup quality gates"
    description: "Run /popkit:project setup for pre-commit hooks"
  - label: "View issues"
    description: "Run /popkit:issue list to see GitHub issues"
  - label: "Done for now"
    description: "I'll explore on my own"
```

**Problem:**
- No guidance on which is "best" for someone starting out
- If user selects "Done", they don't know what comes next
- "Analyze codebase" is 3+ minutes, might overwhelm new user

**Recommendation:**
Reorder options with better guidance:

```
- label: "Analyze codebase"
  description: "Deep dive (5 min) - Recommended first step"
- label: "Start working on issue"
  description: "Jump to Issue #N - Skip analysis for now"
- label: "Just explore"
  description: "I prefer to discover on my own"
```

### Gap #5: Power Mode Decision Without Cost Clarity

**Problem:**
- Step 6 of init asks about Power Mode
- Shows 3 options: File Mode, Redis Self-Hosted, Redis Cloud (Pro)
- "Pro" cost isn't mentioned initially
- User might select Cloud option then be surprised at checkout

**Current Wording:**
```
- label: "Redis Mode - PopKit Cloud (Pro $9/mo)"
  description: "Full power, zero setup. We manage Redis. Run /popkit:upgrade first."
```

**Improvement Needed:**
- Make it clearer this requires subscription
- Show benefits vs cost
- Explain what "free" options include
- Link to pricing page

**Recommendation:**
```
- label: "File Mode (Recommended - Free)"
  description: "Simple coordination, works offline, 2-3 agents. No setup needed."

- label: "Redis Self-Hosted (Advanced - Free)"
  description: "Full parallel agents (6+), requires Docker/Redis. You manage infrastructure."

- label: "Redis Cloud (Pro - $9/mo)"
  description: "Full power with zero setup. Hosted by us. Includes pattern sharing."

- label: "Decide later"
  description: "Skip for now - set up with /popkit:power init anytime"
```

### Gap #6: Post-Init Onboarding is Incomplete

**Problem:**
- After init and Power Mode setup, there's one more AskUserQuestion
- That's the last touch point for new user
- What happens if they select "Done"? No further guidance.
- They might not discover `/popkit:power`, `/popkit:routine morning`, etc.

**Recommendation:**
Add post-init onboarding message:

```markdown
## PopKit is Ready! 🎉

You're now at **Level 2: Fully Initialized**

### Next Steps (Pick One)

1. **Get oriented** - Run `/popkit:routine morning` for project health
2. **Start developing** - Run `/popkit:next` for recommendations
3. **Learn the features** - Explore `/popkit:` commands
4. **Configure Power Mode** - Run `/popkit:power init` for multi-agent setup

### Quick Commands

| Command | What it does |
|---------|-------------|
| `/popkit:next` | Get context-aware next steps |
| `/popkit:routine morning` | Daily health check |
| `/popkit:dev brainstorm` | Start feature planning |
| `/popkit:git commit` | Smart commit with auto-message |
| `/popkit:power` | Multi-agent orchestration |

### Resources

- [PopKit Documentation](https://github.com/jrc1883/popkit-claude)
- [Quick Tutorials](https://github.com/jrc1883/popkit-claude/wiki)
- [Report Issues](https://github.com/jrc1883/popkit-claude/issues)
```

---

## Hook-Based Auto-Triggers

### Opportunity: First-Run Detection

Current SessionStart hook could detect:
- Is this the very first session? (No `logs/session_start.json`)
- Is this a new project? (Just created `.claude/popkit/`)
- Has user initialized? (Check for STATUS.json)

```python
# Proposed addition to session-start.py
def detect_first_run():
    """Detect if this is the user's first session ever."""
    logs_file = Path("logs/session_start.json")
    status_file = Path(".claude/STATUS.json")

    if not logs_file.exists():
        return "very_first_session"

    if logs_file.exists() and not status_file.exists():
        return "auto_init_only"  # Tier 1 only

    if status_file.exists():
        return "fully_initialized"  # Tier 2

    return "unknown"

# Output welcome message on first run
if detect_first_run() == "very_first_session":
    print("🎉 Welcome to PopKit! Run /popkit:project init for full setup.",
          file=sys.stderr)
```

### Opportunity: Command Context Enhancement

Current UserPromptSubmit hook enhances prompts with detected agents and skills. Could also:
- Detect if command would benefit from full init
- Suggest init in stderr message
- Track which commands fail due to missing state

---

## Initialization Checklist (Current)

From `pop-project-init/SKILL.md`:

```markdown
## Verification Checklist

After initialization, verify these files/directories exist:

| Path | Purpose |
|------|---------|
| `.claude/` | Root Claude Code config |
| `.claude/popkit/` | PopKit runtime state |
| `.claude/popkit/config.json` | Project PopKit config |
| `.claude/popkit/routines/` | Custom routines |
| `.claude/STATUS.json` | Session state |
| `.claude/settings.json` | Claude settings with PopKit fields |
| `CLAUDE.md` | Has `<!-- POPKIT:START -->` markers |
```

**Problem:** This checklist is at the END of the skill document. New users might not see it. And there's no automated way to verify the checklist.

**Recommendation:**
- Add a command: `/popkit:project verify` that checks all required files
- Show visual checkmark/X for each item
- Suggest fixes if any are missing

```bash
/popkit:project verify

✅ .claude/ exists
✅ .claude/popkit/config.json exists
❌ .claude/STATUS.json missing (run /popkit:project init)
✅ CLAUDE.md has PopKit markers
❌ .claude/skills/ empty (optional)

Status: Mostly initialized (4/5 required items)
```

---

## Recommendations (Prioritized)

### P0 - Critical (v1.0 Must-Have)

1. **Add SessionStart welcome message**
   - Detect first-ever session
   - Print friendly message suggesting `/popkit:project init`
   - Link to quick-start guide
   - Effort: 1-2 hours

2. **Add initialization status detection to commands**
   - Create utility function: `check_initialization_status()`
   - Suggest init when command would benefit
   - Show hint in stderr: "💡 Run `/popkit:project init` for full project awareness"
   - Effort: 2-3 hours

3. **Update README with "Initialization Levels" section**
   - Explain two-tier system clearly
   - Show capability matrix: what works at each level
   - Recommend when to run `/popkit:project init`
   - Include before/after examples
   - Effort: 2-3 hours

### P1 - High (v1.0 Should-Have)

4. **Improve Power Mode decision UX**
   - Clarify costs and benefits
   - Show tier indicators
   - Link to pricing page
   - Effort: 1-2 hours

5. **Better post-init guidance**
   - Add onboarding message after init
   - Suggest next commands
   - Quick reference table
   - Effort: 1-2 hours

6. **Add verification command**
   - `/popkit:project verify` - Check all required files
   - Show visual status
   - Suggest fixes if missing
   - Effort: 2-3 hours

### P2 - Medium (v1.1)

7. **Improve post-init decision flow**
   - Reorder "What's next?" options
   - Add "recommended" indicator
   - Explain time commitment for each
   - Effort: 1-2 hours

8. **Interactive onboarding skill**
   - `/popkit:onboarding` - Walk through all features
   - Show before/after examples
   - Let user try commands in context
   - Effort: 4-6 hours

9. **Initialization metrics**
   - Track how many users reach Level 2
   - Track which post-init path they choose
   - Identify drop-off points
   - Effort: 3-4 hours

### P3 - Nice-to-Have (Future)

10. **Marketplace listing improvements**
    - Show "2-tier initialization" clearly
    - Video walkthrough of setup
    - FAQ about when to init
    - Effort: 2-3 hours

11. **Auto-init progression**
    - Detect degraded mode usage
    - After N commands, prompt for init
    - "You've used PopKit 5 times. Ready to initialize?"
    - Effort: 2-3 hours

---

## Implementation Roadmap

### Phase 1: Detection & Messaging (1-2 weeks)

- [ ] Add welcome message to SessionStart hook
- [ ] Add initialization detection to command system
- [ ] Add initialization status util to shared modules
- [ ] Update README with Initialization Levels section
- [ ] Add stderr hints to commands that need full init

### Phase 2: Verification & Guidance (2-3 weeks)

- [ ] Create `/popkit:project verify` command
- [ ] Improve Power Mode UX in init skill
- [ ] Add post-init onboarding message
- [ ] Update decision flow in init skill
- [ ] Add quick reference in output

### Phase 3: Analytics & Iteration (3-4 weeks)

- [ ] Add initialization tracking to hooks
- [ ] Build analytics dashboard
- [ ] Identify usage patterns and drop-off points
- [ ] Iterate based on user feedback
- [ ] A/B test welcome messages and post-init flows

### Phase 4: Interactive Onboarding (4-6 weeks)

- [ ] Design interactive onboarding experience
- [ ] Create `/popkit:onboarding` command
- [ ] Build context-aware tutorials
- [ ] Record video walkthroughs
- [ ] Integrate with feature discovery

---

## Key Metrics for Success

1. **Initialization Rate**
   - % of new users who run `/popkit:project init` within first 3 sessions
   - Target: 80%+ (current likely: 20-30%)

2. **Time to Initialization**
   - Average sessions before full initialization
   - Target: ≤ 1 session (currently: Unknown)

3. **Command Effectiveness**
   - Users report PopKit "working well" after init
   - Comparison: degraded mode vs full init
   - Target: 2x+ improvement in satisfaction

4. **Feature Discovery**
   - % of users discovering `/popkit:next`, `/popkit:routine`, `/popkit:power`
   - Target: 70%+ (currently: Unknown)

5. **Support Load**
   - Reduction in "PopKit isn't working" support issues
   - Reduction in "How do I set up PopKit" questions
   - Target: 80% reduction

---

## Open Questions

1. **SessionStart Welcome Message**
   - Should it be printed to stdout or stderr?
   - How verbose? One line or a paragraph?
   - Link to docs or just suggest command?

2. **Command Enhancement Scope**
   - Which commands should suggest init? (All? Or just key ones?)
   - Should we auto-run quick init? Or just prompt?
   - Should we track which commands users try before init?

3. **User Preference**
   - Some users might prefer degraded mode (simpler, faster)
   - Should we respect a "don't suggest init" preference?
   - How to detect when init is truly optional vs recommended?

4. **OnboardingFlow Timing**
   - Show onboarding immediately after install? (might overwhelm)
   - After first command? (might interrupt)
   - On demand via `/popkit:onboarding`? (might go undiscovered)

5. **Backward Compatibility**
   - How do we handle projects that already have `.claude/`?
   - Should `/popkit:project init` warn about overwriting?
   - How to migrate old init format to new one?

---

## Related Issues

- #173: Skill automation architecture (SessionStart hook auto-init)
- #159: AskUserQuestion enforcement (mandatory decisions in init skill)
- #2: Marketplace readiness (v1.0 user experience)
- #224: v1.0 validation audit (first-run experience validation)

---

## Appendix A: File Structure Comparison

### Without `/popkit:project init` (Tier 1 Only)

```
project/
├── .git/
├── .claude/
│   └── popkit/
│       ├── config.json
│       └── routines/
│           ├── morning/
│           └── nightly/
└── (no STATUS.json, no CLAUDE.md PopKit section)
```

### After `/popkit:project init` (Tier 2 Complete)

```
project/
├── .git/
├── .claude/
│   ├── popkit/
│   │   ├── config.json
│   │   └── routines/
│   │       ├── morning/
│   │       └── nightly/
│   ├── agents/
│   ├── commands/
│   ├── hooks/
│   ├── skills/
│   ├── scripts/
│   ├── logs/
│   ├── plans/
│   ├── STATUS.json         ← Session state
│   └── settings.json       ← Claude settings
├── CLAUDE.md               ← Updated with PopKit section
└── .gitignore             ← Updated with PopKit patterns
```

---

## Appendix B: Hook Execution Timeline

```
User installs PopKit & restarts Claude Code
                    ↓
            [SessionStart Hook]
                    │
        ┌───────────┼───────────┐
        │           │           │
   Log session   Check updates  Register with cloud
        │           │           │
        └───────────┼───────────┘
                    │
        ┌───────────▼───────────┐
        │ Auto-create .claude/  │
        │  (idempotent)         │
        │ - .claude/popkit/     │
        │ - routines/           │
        │ - config.json         │
        └───────────┬───────────┘
                    │
            Session ready
        (NO message to user!)
                    │
            User types anything
                    ↓
            [UserPromptSubmit Hook]
                    │
        ┌───────────┼───────────┐
        │           │           │
     Detect       Detect      Load project
     keywords     skills      context
        │           │           │
        └───────────┼───────────┘
                    │
        Enhance prompt with
        detected agents & skills
                    │
        [User still doesn't know about /popkit:project init]
```

---

**Document Status:** Complete
**Ready for:** Code review, issue creation, implementation planning
**Next Steps:** Create GitHub issues based on this research
