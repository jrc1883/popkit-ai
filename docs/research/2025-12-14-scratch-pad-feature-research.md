# PopKit Scratch Pad Feature Research

**Date:** December 14, 2025
**Author:** Claude Code Research
**Status:** Research Document for Planning Review
**Branch:** `claude/add-scratch-pad-feature-tTEcB`

## Executive Summary

This document explores the concept of a **Scratch Pad** feature for PopKit—a lightweight, temporary task tracking system designed for the messy initial setup phase of new projects before formally committing to GitHub issue tracking. The research identifies PopKit's existing task management capabilities, Claude Code's TodoWrite limitations, and proposes an integrated solution that bridges the gap between initial brainstorming and formal GitHub workflow.

### Problem Statement

When starting new projects, developers face a chicken-and-egg problem:
1. Initial setup is chaotic, requirements constantly change, and structure is unclear
2. Creating formal GitHub issues too early creates false hope about project maturity (false positive at v0.0.1)
3. Tracking every task through GitHub during setup phase creates noise and overhead
4. Once the project stabilizes on solid foundations, developers want to transition to GitHub-based tracking
5. Eventually, projects need formal dev/test/prod environment management with GitHub

**Current Experience:**
- Teams skip GitHub tracking initially (lost context)
- Or create excessive issues that clutter the board (noise)
- Or try using local notes (scattered, unsearchable)
- No clear transition path from "brainstorming" to "ready for formal tracking"

### Proposed Solution

A **Scratch Pad** system that:
- Provides temporary, session-aware task tracking without GitHub overhead
- Integrates with Claude Code's TodoWrite for immediate visibility
- Stores persistent project-level scratch state (unlike TodoWrite's session-only focus)
- Transitions tasks to GitHub when project stabilizes
- Sets foundation for dev/test/prod environment management

---

## Part 1: Current PopKit Task Management Capabilities

### 1.1 Existing Systems

PopKit already has sophisticated task/project tracking systems:

| System | Purpose | Scope | Persistence | Integration |
|--------|---------|-------|------------|-------------|
| **STATUS.json** | Session state capture | Per-project | File-based (survives sessions) | Manual restore via skill |
| **Checkpoint System** | Long-running operation snapshots | Per-session | File-based (`~/.claude/popkit/checkpoints/`) | Manual create/restore |
| **Workflow Engine** | Multi-step skill orchestration | Per-workflow | State machine (`.popkit/workflows/`) | Skill execution |
| **TodoWrite (Claude Code)** | Session task tracking | Per-conversation | Temp (conversation memory only) | Real-time visibility |
| **AskUserQuestion** | Structured user input | Per-decision point | Via hooks/routing | Decision branching |

### 1.2 Existing Commands for Project Setup

**Relevant Commands:**
- `/popkit:project init` - Initialize new project with metadata
- `/popkit:project analyze` - Analyze existing codebase structure
- `/popkit:project setup` - Configure development environment
- `/popkit:routine` - Daily health checks and "Ready to Code" scores
- `/popkit:next` - Context-aware next action recommendations
- `/popkit:git` - Git workflow orchestration

**Key Skills:**
- `pop-session-capture` - Saves project state to STATUS.json
- `pop-session-resume` - Restores previous session state
- `pop-checkpoint` - Create/restore long-running operation checkpoints
- `pop-executing-plans` - Batch execution with review checkpoints
- `pop-writing-plans` - Create implementation plans

### 1.3 Limitations of Existing Systems

1. **STATUS.json** - Designed for session state, not ongoing project task tracking
2. **TodoWrite** - Session-only (not cross-session), single-task-in-progress limit, overwrites entire list
3. **Workflow Engine** - Designed for multi-step orchestration, not open-ended task lists
4. **AskUserQuestion** - Decision points only, not task tracking

**Gap:** No project-level task list that:
- Persists across sessions
- Doesn't require formal GitHub issue creation
- Can transition to GitHub when ready
- Provides scratch/draft status for exploratory work

---

## Part 2: Claude Code TodoWrite Analysis

### 2.1 TodoWrite Capabilities

**Strengths:**
- Real-time visibility in Claude Code UI
- Structured format (status, content, activeForm)
- Good for session planning
- Integrates with system prompt (frequently recommended by Claude)
- Includes priority levels and metadata

**Critical Limitations:**
1. **Session-Only Persistence:** Dies when Claude Code restarts or conversation closes
2. **Single In-Progress Task:** Only one task can be `in_progress` at once
3. **Complete List Replacement:** Overwrites entire todo list on each update (overwriting bug)
4. **No Filtering/Searching:** Cannot query by status, priority, or category
5. **No Workspace Scope:** Each conversation has its own isolated todo list
6. **No Dependency Tracking:** No task relationships or blocking semantics
7. **No Cross-Project View:** Cannot see todos across multiple projects

### 2.2 Why TodoWrite Alone Isn't Sufficient

TodoWrite excels at **session planning** (what Claude will do in the next 30 minutes), but fails at **project planning** (what the team needs to accomplish over days/weeks before GitHub):

```
TodoWrite Timeline:
Session A (1 hour) → Session B (1 hour) → [LOST] → Session C (1 hour)
                     Different todo list

Scratch Pad Timeline:
Session A → Session B → [PRESERVED] → Session C → [GRADUATE TO GITHUB]
            Persistent project-level
```

---

## Part 3: Scratch Pad Feature Design

### 3.1 Core Concept

The **Scratch Pad** is a lightweight, persistent project-level task list designed for the "messy phase" before formal GitHub tracking:

**Characteristics:**
- **Persistent:** Survives session restarts
- **Project-Scoped:** One scratch pad per project
- **Lightweight:** Minimal overhead, text/JSON based
- **Transitional:** Tasks can be promoted to GitHub issues
- **Integrated:** Works alongside Claude Code's TodoWrite
- **Non-Binding:** Indicates intent, not commitments

### 3.2 Proposed Data Model

```json
{
  "version": "1.0",
  "project_id": "popkit",
  "created_at": "2025-12-14T10:00:00Z",
  "maturity_level": "research",
  "metadata": {
    "phase": "setup",
    "focus_area": "Project initialization",
    "key_decision": "Architecture pattern selection"
  },
  "tasks": [
    {
      "id": "scratch-001",
      "title": "Set up development environment",
      "description": "Install dependencies, configure editor, setup local DB",
      "status": "in_progress",
      "priority": "high",
      "category": "infrastructure",
      "tags": ["setup", "dev-env"],
      "estimated_effort": "2h",
      "blocked_by": null,
      "blocks": null,
      "created_at": "2025-12-14T10:00:00Z",
      "updated_at": "2025-12-14T10:15:00Z",
      "completed_at": null,
      "notes": "Need to document for team",
      "github_issue": null
    }
  ],
  "decisions": [
    {
      "id": "decision-001",
      "question": "Monorepo or Polyrepo?",
      "decision": "Monorepo with npm workspaces",
      "reasoning": "Easier coordination during setup phase",
      "made_at": "2025-12-14T10:30:00Z"
    }
  ],
  "blockers": [
    {
      "id": "blocker-001",
      "description": "Waiting for API credentials",
      "impact": "Cannot set up cloud integration",
      "since": "2025-12-14T09:00:00Z",
      "resolution_owner": "team-lead"
    }
  ]
}
```

### 3.3 Scratch Pad States

Projects transition through maturity levels, each with different tracking needs:

```
BRAINSTORM → RESEARCH → SETUP → FOUNDATION → DEVELOPMENT → STABLE → PRODUCTION
(NO TRACKING)  (SP)       (SP)      (SP+GH)       (GH)         (GH)       (GH)

SP = Scratch Pad
GH = GitHub Issues
```

**State Definitions:**

| Level | Duration | Tracking | Characteristics | Graduation |
|-------|----------|----------|-----------------|------------|
| **brainstorm** | Hours | Notes only | Ideas, no commitments | Clear direction emerges |
| **research** | Days | Scratch Pad | Exploring options, testing | Architecture agreed |
| **setup** | Days | Scratch Pad | Building foundations | Core structure in place |
| **foundation** | Weeks | Scratch Pad + GitHub | Both systems active, transitioning | Ready for team development |
| **development** | Ongoing | GitHub only | Formal tracking, PRs, reviews | Release candidate |
| **stable** | Ongoing | GitHub + milestones | Versioned, release-managed | Production-ready |
| **production** | Ongoing | GitHub + CI/CD | Full DevOps pipeline | Mature |

### 3.4 Integration with TodoWrite

**Scratch Pad ≠ TodoWrite, but they complement each other:**

```
Scratch Pad (Project Level):
├── Set up CI/CD pipeline [task-001]
│   ├── Research CI options
│   ├── Choose GitHub Actions
│   └── Configure workflows
└── Design database schema [task-002]

↓ (Claude creates session plan)

TodoWrite (Session Level):
├── Implement GitHub Actions workflow [from task-001.2]
├── Define database schema in Prisma [from task-002]
└── Write migration tests
```

**How They Work Together:**

1. **Scratch Pad** is created manually or via `/popkit:scratch new`
2. **TodoWrite** is populated during sessions from Scratch Pad items
3. As session tasks complete, Scratch Pad reflects updates
4. Developer reviews Scratch Pad at session end to plan next steps
5. `/popkit:routine morning` can show Scratch Pad status and "Ready to Code" score

### 3.5 Scratch Pad Workflow

```
1. Initialize Scratch Pad
   /popkit:scratch init
   → Creates ~/.popkit/projects/{project-id}/scratch.json

2. Add Tasks (Interactive)
   /popkit:scratch add
   → Prompts: title, description, priority, category
   → Auto-assigns ID, timestamp

3. Session Planning
   During session, developer/Claude pulls tasks from Scratch Pad
   /popkit:scratch view --priority high
   → Shows high-priority items
   → Claude can populate TodoWrite from Scratch Pad

4. Session Update
   As work progresses:
   /popkit:scratch update task-001 --status in_progress
   /popkit:scratch update task-001 --status completed

5. Decision Recording
   /popkit:scratch decision "Monorepo pattern?"
   → Records architectural decisions with reasoning

6. Blocker Tracking
   /popkit:scratch block "Waiting for API key"
   → Tracks impediments and resolution owners

7. Review & Plan Next Steps
   /popkit:routine nightly
   → Shows Scratch Pad summary
   → Identifies blocked items
   → Recommends next focus area

8. Graduate to GitHub (When Ready)
   /popkit:scratch graduate --to-github
   → Converts Scratch Pad items to GitHub issues
   → Links issues back to Scratch Pad
   → Changes project maturity level
   → Archives old Scratch Pad
```

### 3.6 File Structure

```
~/.popkit/projects/
├── {project-id}/
│   ├── scratch.json           # Scratch Pad data
│   ├── scratch.history.json   # Version history
│   ├── decisions.md           # Generated decision log
│   └── blockers.md            # Generated blocker report
```

Or co-located with STATUS.json:

```
{project-root}/
├── .popkit/
│   ├── scratch.json
│   ├── scratch.history.json
│   └── decisions.md
├── STATUS.json                # Session state
└── ...
```

### 3.7 Command Structure

Proposed `/popkit:scratch` command:

```
/popkit:scratch init                    # Initialize scratch pad for project
/popkit:scratch view [--priority HIGH]  # Display tasks, optionally filtered
/popkit:scratch add                     # Interactive task creation
/popkit:scratch update ID --status X    # Update task status
/popkit:scratch edit ID                 # Edit task details
/popkit:scratch remove ID               # Delete task
/popkit:scratch decision "Question"     # Record architectural decision
/popkit:scratch block "Description"     # Record blocker
/popkit:scratch resolve BLOCKER_ID      # Mark blocker as resolved
/popkit:scratch search "query"          # Search tasks and decisions
/popkit:scratch stats                   # Show progress metrics
/popkit:scratch graduate --to-github    # Promote items to GitHub issues
/popkit:scratch report                  # Generate markdown report
/popkit:scratch review                  # Interactive review mode
```

---

## Part 4: Integration with PopKit Architecture

### 4.1 Integration Points

**1. Skills Integration**
- New skill: `pop-scratch-pad-init` - Project initialization with scratch pad setup
- New skill: `pop-scratch-review` - Daily/nightly review of scratch pad status
- Updated skill: `pop-session-capture` - Also captures scratch pad changes
- Updated skill: `pop-executing-plans` - Can pull tasks from scratch pad

**2. Routine Integration**
- Morning routine: Show scratch pad status, identify blockers, plan day
- Nightly routine: Archive completed tasks, update decisions, prepare next session

**3. Agent Integration**
- **Project Setup Agent** - Create and seed scratch pad
- **Session Manager Agent** - Sync TodoWrite with scratch pad
- **Blocker Handler Agent** - Monitor and escalate blockers

**4. Hooks Integration**
- `post-tool-use.py` - Track when scratch pad is accessed/modified
- `skill_state.py` - Track scratch pad completion decisions
- New hook: `scratch_pad_sync.py` - Sync TodoWrite ↔ Scratch Pad

**5. Output Styles**
- New style: `scratch-pad-summary` - Progress report format
- New style: `decision-log` - Architecture decisions
- New style: `blocker-report` - Impediments and owners

### 4.2 MCP Server Integration

The MCP server generated via `/popkit:project generate` could include:
- Scratch pad management tools
- Decision/blocker queries
- Health check for project maturity level

### 4.3 Power Mode Coordination

In Power Mode multi-agent scenarios:
- One agent could manage Scratch Pad
- Others read Scratch Pad to understand project context
- Agents coordinate via shared decision/blocker state

---

## Part 5: Brainstorming - Dev/Test/Prod Environments

### 5.1 The Challenge

PopKit currently focuses on development workflow, but doesn't address:
1. How to manage separate dev/test/prod environments
2. How to track environment-specific configuration
3. How to prevent accidental production changes
4. How to coordinate deployments across environments

### 5.2 Proposed Direction: Environment Profiles

**Concept:** Each GitHub repository can define environment profiles:

```yaml
# .popkit/environments.yaml
environments:
  development:
    branch: develop
    registry: ghcr.io/{org}/dev/
    deploy_target: staging.thehouseofdeals.com
    environment_vars:
      NODE_ENV: development
      LOG_LEVEL: debug
    ci: true
    requires_approval: false

  testing:
    branch: test
    registry: ghcr.io/{org}/test/
    deploy_target: testing.thehouseofdeals.com
    environment_vars:
      NODE_ENV: testing
      LOG_LEVEL: info
    ci: true
    requires_approval: false

  production:
    branch: main
    registry: ghcr.io/{org}/prod/
    deploy_target: api.thehouseofdeals.com
    environment_vars:
      NODE_ENV: production
      LOG_LEVEL: error
    ci: true
    requires_approval: true
    deployment_window: "business hours"
    approval_roles: ["lead", "ops"]
```

### 5.3 GitHub-Integrated Workflow

**Proposal:** Add GitHub Actions integration via `/popkit:github`:

```
/popkit:github init                      # Detect repo, create .popkit/environments.yaml
/popkit:github deploy --env development  # Deploy to dev, verify, report
/popkit:github promote dev → test        # Promote build from dev to test
/popkit:github status                    # Show deployment status across environments
```

### 5.4 Workflow Example

```
1. Developer pushes to feature branch
   → CI runs in GitHub Actions (tests, lint, build)

2. Open PR to develop branch
   → Merge runs deploy to development environment
   → Smoke tests verify deployment

3. When ready for testing:
   /popkit:github promote develop → test
   → Creates PR to test branch
   → Merges and deploys to test environment
   → QA team validates

4. When ready for production:
   /popkit:github promote test → main
   → Creates PR to main branch
   → Requires lead/ops approval
   → Deploys during business hours window
   → Monitors deployment

5. Hotfix in production:
   /popkit:github hotfix "Production issue"
   → Creates emergency branch from main
   → Sets up fast-track approval process
   → Deploys immediately
```

### 5.5 Integration with Scratch Pad

Environment management becomes a **foundational task**:

```
Scratch Pad (Setup Phase):
├── Set up CI/CD pipeline
│   ├── Configure GitHub Actions
│   ├── Define environments.yaml
│   └── Test dev deployment
├── Set up test environment
│   └── Deploy staging infrastructure
└── Set up production environment
    └── Configure secrets and monitoring
```

Once infrastructure is stable (foundation level), environment management moves to GitHub-based deployment tracking.

---

## Part 6: Implementation Roadmap

### Phase 1: Scratch Pad MVP (v0.2.2)
- [ ] Implement scratch.json data model
- [ ] Create `/popkit:scratch init` command
- [ ] Create `/popkit:scratch add/view/update/remove` commands
- [ ] Integrate with `pop-session-capture` skill
- [ ] Add scratch pad summary to morning routine

### Phase 2: Decision & Blocker Tracking (v0.3.0)
- [ ] Add decision recording to scratch pad
- [ ] Add blocker tracking and escalation
- [ ] Create decision log output style
- [ ] Create blocker report output style

### Phase 3: GitHub Graduation (v0.3.1)
- [ ] Implement `/popkit:scratch graduate` command
- [ ] Create GitHub issue from scratch pad tasks
- [ ] Link issues back to scratch pad
- [ ] Archive scratch pad after graduation

### Phase 4: Environment Management (v0.4.0)
- [ ] Design environments.yaml format
- [ ] Implement `/popkit:github init` command
- [ ] Implement deployment workflow commands
- [ ] Add environment status tracking

### Phase 5: Advanced Features (v0.5.0)
- [ ] Cross-project scratch pad analytics
- [ ] Team collaboration on scratch pads
- [ ] Pattern learning from past projects
- [ ] Automatic graduation suggestions

---

## Part 7: Key Design Decisions

### 7.1 Storage Location

**Option A:** Project root (`.popkit/scratch.json`)
- ✅ Visible to all team members
- ❌ Requires project to be initialized
- ✅ Survives project clones

**Option B:** Home directory (`~/.popkit/projects/{id}/scratch.json`)
- ✅ Works even before project initialized
- ❌ Not shared with team members
- ❌ Need project ID mapping

**Decision:** **Option A (project root)** - Better for team coordination, visible in VCS

### 7.2 Single vs. Multiple Scratch Pads

**Option A:** One per project
- ✅ Simpler mental model
- ✅ Single file to manage
- ❌ Large projects get cluttered

**Option B:** Organize by phase/epic
- ✅ Can focus on one area
- ❌ More complex to manage
- ❌ Task dependencies cross-scratch-pad

**Decision:** **Option A** - Start simple, split by tags if needed later

### 7.3 Sync Behavior with TodoWrite

**Option A:** Manual (developer chooses which tasks to work on)
- ✅ Maximum flexibility
- ❌ Requires discipline to update

**Option B:** Automatic (Claude syncs on session start)
- ✅ Always up-to-date
- ❌ Breaks if offline

**Option C:** Hybrid (Claude suggests, developer confirms)
- ✅ Balances flexibility and automation
- ✅ Clear user control

**Decision:** **Option C** - Respect user autonomy while providing assistance

---

## Part 8: Key Questions for Planning Meeting

1. **User Expectations:** Should the scratch pad show "confidence level" (how sure we are about tasks)?

2. **Team Collaboration:** Should multiple team members be able to edit the same scratch pad concurrently?

3. **Automation Triggers:** Should graduating to GitHub happen automatically or require explicit command?

4. **Environment Complexity:** Do you want branching strategies (git-flow, trunk-based) defined in environments.yaml?

5. **Maturity Scoring:** Should PopKit calculate a "project maturity score" based on scratch pad completion?

6. **Third-Party Integration:** Should we support Jira/Linear migration in addition to GitHub?

7. **Analytics:** Do you want cross-project scratch pad analytics (e.g., "average time from brainstorm to production")?

8. **Offline Support:** Must scratch pads work offline, or is network access acceptable?

---

## Part 9: Reference Implementations

### 9.1 Similar Tools & Patterns

**GitHub Project Boards:**
- ✅ Same basic feature set
- ❌ Requires GitHub account
- ❌ Heavier UI
- ❌ Better for formal tracking

**Notion/Obsidian:**
- ✅ Flexible formatting
- ❌ Not integrated with code
- ❌ Hard to automate

**Linear Issues:**
- ✅ Modern interface
- ❌ Paid service
- ❌ Learning curve

**Kanban (simple):**
- ✅ Visual, easy to understand
- ❌ Limited relationships
- ❌ Difficult to track details

**Scratch Pad (proposed):**
- ✅ Lightweight, no setup
- ✅ Integrated with PopKit
- ✅ Transitional to GitHub
- ✅ Supports decisions & blockers
- ✅ No external dependencies

### 9.2 Architecture Decision Log Pattern

PopKit can record architectural decisions alongside tasks:

```markdown
# Architecture Decisions

## ADR-001: Monorepo Strategy
**Date:** 2025-12-14
**Status:** Accepted
**Decision:** Use npm workspaces for monorepo organization

### Context
Multiple packages need coordination during setup phase. Considered polyrepo but chose monorepo for:
- Shared versioning
- Easier cross-package refactoring
- Single CI/CD pipeline
- Better for plugin ecosystem

### Consequences
- Simpler initial setup
- Requires workspace management later
- Single change can affect multiple packages

### Alternatives Considered
- Polyrepo with git subtrees
- Yarn workspaces
- Lerna
```

---

## Part 10: Success Criteria

A successful Scratch Pad implementation should:

1. **Reduce Setup Overhead:** Projects can skip GitHub tracking during chaotic initial phase
2. **Enable Transitions:** Clear path from scratch pad → GitHub without losing context
3. **Preserve Decisions:** Architectural decisions captured and reviewable
4. **Track Blockers:** Team can identify and resolve impediments
5. **Work Offline:** No dependency on external services during ideation
6. **Scale Gracefully:** Works for 1-person projects and 50-person teams
7. **Integrate Naturally:** Feels like part of PopKit, not a plugin
8. **Migrate Easily:** Can export to GitHub, Jira, Linear
9. **Teach:** Helps new developers understand project evolution

---

## Part 11: Recommended Next Steps

### For Planning Meeting:

1. **Validate Problem:** Is the "false hope at v0.0.1" problem real? How many projects hit this?

2. **Confirm Scope:** Do you want scratch pad MVP only, or include environment management?

3. **Design Review:** Does the proposed data model match your team's mental model?

4. **Timeline:** Phase 1 MVP realistic for next sprint?

5. **Team Input:** Should scratch pads be individual or shared? How to handle merge conflicts?

6. **Success Metrics:** How will we know this feature is working?

7. **Graduation Rules:** When should teams be encouraged to migrate to GitHub?

### For Implementation (After Approval):

1. Create `/popkit:scratch` command in `packages/plugin/commands/`
2. Implement scratch pad utilities in `packages/plugin/hooks/utils/`
3. Create `pop-scratch-pad-init` skill
4. Update `pop-session-capture` to include scratch pad
5. Add scratch pad review to routine (morning/nightly)
6. Write tests in `packages/plugin/tests/`
7. Update documentation with examples

---

## Part 12: Appendices

### A. Example Scratch Pad (Real Project)

```json
{
  "version": "1.0",
  "project_id": "popkit",
  "maturity_level": "foundation",
  "created_at": "2025-12-01T09:00:00Z",
  "tasks": [
    {
      "id": "scratch-001",
      "title": "Set up monorepo structure",
      "description": "Create npm workspaces for plugin, cloud, billing",
      "status": "completed",
      "priority": "high",
      "category": "infrastructure",
      "tags": ["setup", "npm"],
      "created_at": "2025-12-01T09:00:00Z",
      "completed_at": "2025-12-02T14:30:00Z"
    },
    {
      "id": "scratch-002",
      "title": "Implement hook system",
      "description": "Create pre-tool-use and post-tool-use hooks for tool orchestration",
      "status": "completed",
      "priority": "high",
      "category": "architecture",
      "blocked_by": "scratch-001",
      "blocks": ["scratch-003"],
      "created_at": "2025-12-02T09:00:00Z",
      "completed_at": "2025-12-04T16:00:00Z"
    },
    {
      "id": "scratch-003",
      "title": "Build agent routing system",
      "description": "Implement confidence-based agent selection with keyword/pattern matching",
      "status": "in_progress",
      "priority": "high",
      "category": "architecture",
      "estimated_effort": "16h",
      "created_at": "2025-12-04T09:00:00Z",
      "blocked_by": "scratch-002"
    }
  ],
  "decisions": [
    {
      "id": "dec-001",
      "question": "Monorepo or Polyrepo?",
      "decision": "Monorepo with npm workspaces",
      "rationale": "Better coordination during plugin development",
      "made_at": "2025-12-01T10:00:00Z"
    },
    {
      "id": "dec-002",
      "question": "Hook protocol (stdin/stdout vs sockets)?",
      "decision": "stdin/stdout with JSON",
      "rationale": "Simpler, more portable, follows Claude Code conventions",
      "made_at": "2025-12-02T11:00:00Z"
    }
  ]
}
```

### B. Command Examples

```bash
# Session start - check scratch pad
/popkit:scratch view --priority high
# Output:
# 📋 PopKit Scratch Pad (Foundation Phase)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔴 HIGH PRIORITY
# 1. [IN PROGRESS] Build agent routing system (16h)
#    Blocked by: scratch-002 ✅
#    Next: Implement confidence scoring
#
# ⚠️  BLOCKERS: None
# 📊 Progress: 2/5 tasks complete (40%)
# 💾 Decisions: 2 recorded
#
# Suggestion: Continue with agent routing (unblocked)

# Add task
/popkit:scratch add
# Interactive prompts...
# Created: scratch-004 "Implement skill system"

# Update progress
/popkit:scratch update scratch-003 --status completed

# Record decision
/popkit:scratch decision "Use Python for hooks instead of TypeScript?"
# Followed by: decision reason explanation

# Record blocker
/popkit:scratch block "Waiting for API credentials from infrastructure team"

# View decisions
/popkit:scratch decisions
# Output:
# 📋 Architectural Decisions (PopKit)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✅ ADR-001: Monorepo with npm workspaces
#    Made: 2025-12-01 | By: Claude
#    Rationale: Better coordination...
#
# ✅ ADR-002: stdin/stdout JSON hooks
#    Made: 2025-12-02 | By: Claude
#    Rationale: Simpler, more portable...

# Graduate to GitHub (when foundation is solid)
/popkit:scratch graduate --to-github
# Creates issues, links back, archives scratch pad
```

### C. Related PopKit Features

Scratch Pad connects to:
- **Project Analysis:** `/popkit:project analyze`
- **Routine Tracking:** `/popkit:routine morning|nightly`
- **Session Capture:** `pop-session-capture` skill
- **Execution Plans:** `pop-executing-plans` skill
- **Next Actions:** `/popkit:next`

---

## Conclusion

The **Scratch Pad** feature addresses a real gap in PopKit's workflow: supporting the chaotic, exploratory phase of new projects before GitHub tracking makes sense. By providing lightweight, persistent task tracking with clear graduation paths to GitHub and eventual environment management, Scratch Pad helps teams move from brainstorming to production with confidence.

The design leverages PopKit's existing architecture (STATUS.json patterns, skill orchestration, session capture) while maintaining the lightweight philosophy that makes PopKit valuable. Integration with Claude Code's TodoWrite creates a two-tier system: Scratch Pad for project-level planning, TodoWrite for session-level execution.

**Recommended:** Proceed with Phase 1 MVP implementation after planning meeting feedback.

---

**Document Status:** ✅ Ready for Planning Meeting Review
**Next Action:** Schedule planning meeting to discuss findings and make implementation decisions
