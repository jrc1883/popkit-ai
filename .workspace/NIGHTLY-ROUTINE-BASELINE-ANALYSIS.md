# Nightly Routine Baseline Analysis

**Date**: 2025-12-28
**Session**: Baseline Manual Workflow Recording
**Purpose**: Document manual nightly routine workflow to design automated `pop-nightly` skill

---

## Executive Summary

Successfully executed manual nightly routine and documented the complete workflow. The recording system captured 25 events, though primarily from concurrent Genesis work rather than the nightly routine commands themselves. This provides valuable insight into both the workflow AND the recording system's behavior.

**Key Finding**: The manual workflow requires 11 tool calls and manual STATUS.json updates. An automated skill can reduce this to 3-4 operations with proper chaining.

---

## Manual Workflow Executed

### 1. Sleep Score Calculation (60/100)

#### Tool Calls Made:

1. `git status --porcelain` - Check uncommitted changes
   - **Result**: 3 files (1 deleted, 1 modified, 1 untracked)
   - **Points**: 0/25 (uncommitted work present)

2. `git branch --merged main | grep -v "^\*" | grep -v "main" | wc -l` - Count stale branches
   - **Result**: 0 stale branches
   - **Points**: 20/20 ✅

3. `git stash list | wc -l` - Count stashed changes
   - **Result**: 8 stashes
   - **Points**: N/A (informational)

4. `ps aux | grep -E "(node|npm|pnpm|redis|postgres|supabase)" | grep -v grep` - Check running services
   - **Result**: No dev services running
   - **Points**: 10/10 ✅

5. `ls ~/.claude/logs/*.log 2>/dev/null | wc -l` - Check for session logs
   - **Result**: 0 log files
   - **Points**: 10/10 ✅ (nothing to archive)

6. `gh issue list --state open --limit 5 --json number,title,updatedAt` - Check recent issues
   - **Result**: 5 issues updated today (2025-12-28)
   - **Points**: 20/20 ✅

7. `gh run list --limit 1 --json conclusion,status,createdAt` - Check CI status
   - **Result**: Latest run skipped
   - **Points**: 0/15 (not passing)

8. `git log -1 --format="%h - %s"` - Get latest commit
   - **Result**: "9c12c96b - docs(workspace): add security cleanup and skill development documentation"
   - **Points**: N/A (informational)

9. `git rev-parse --abbrev-ref HEAD` - Get current branch
   - **Result**: "fix/critical-build-blockers"
   - **Points**: N/A (informational)

10. **Read** `STATUS.json` - Load current state
    - **Purpose**: Understand existing context before updating

11. **Write** `STATUS.json` - Update with nightly routine data
    - **Purpose**: Manual session state capture

---

## Tool Usage Patterns

### Tool Call Breakdown:

| Tool | Count | Purpose |
|------|-------|---------|
| Bash | 9 | Git status, GitHub CLI, service checks |
| Read | 1 | Load STATUS.json |
| Write | 1 | Update STATUS.json |
| **Total** | **11** | **Complete nightly routine** |

### Time Analysis:

| Operation | Tool Calls | Estimated Time |
|-----------|------------|----------------|
| Git analysis | 3 | ~5 seconds |
| Service checks | 1 | ~2 seconds |
| GitHub checks | 2 | ~4 seconds |
| Git context | 2 | ~2 seconds |
| STATUS.json update | 2 (Read + Write) | ~3 seconds |
| **Total** | **11** | **~16 seconds** |

---

## Sleep Score Calculation Logic

```python
def calculate_sleep_score() -> int:
    score = 0

    # 1. Uncommitted work saved (25 points)
    uncommitted_files = run("git status --porcelain").count("\n")
    if uncommitted_files == 0:
        score += 25

    # 2. Branches cleaned (20 points)
    stale_branches = run("git branch --merged main | grep -v '^\*' | grep -v 'main' | wc -l")
    if stale_branches == 0:
        score += 20

    # 3. Issues updated (20 points)
    today = datetime.now().strftime("%Y-%m-%d")
    issues = run(f"gh issue list --state open --limit 5 --json updatedAt")
    if all(today in issue['updatedAt'] for issue in issues):
        score += 20

    # 4. CI passing (15 points)
    ci_status = run("gh run list --limit 1 --json conclusion")
    if ci_status['conclusion'] == 'success':
        score += 15

    # 5. Services stopped (10 points)
    services = run("ps aux | grep -E '(node|npm|pnpm|redis|postgres|supabase)' | grep -v grep")
    if not services:
        score += 10

    # 6. Logs archived (10 points)
    log_count = run("ls ~/.claude/logs/*.log 2>/dev/null | wc -l")
    if log_count == 0:
        score += 10

    return score
```

---

## STATUS.json Update Pattern

### Required Data Collection:

1. **Git Context**:
   - Current branch: `git rev-parse --abbrev-ref HEAD`
   - Last commit: `git log -1 --format="%h - %s"`
   - Uncommitted files: `git status --porcelain` (with parsing)
   - Stash count: `git stash list | wc -l`

2. **GitHub Context**:
   - Recent issues: `gh issue list --state open --limit 5 --json number,title,updatedAt`
   - CI status: `gh run list --limit 1 --json conclusion,status,createdAt`

3. **Service Context**:
   - Running services: `ps aux | grep -E "(node|npm|pnpm|redis|postgres|supabase)"`
   - Log files: `ls ~/.claude/logs/*.log 2>/dev/null`

4. **Session Context**:
   - Session ID: Auto-generated or from state
   - Timestamp: Current time
   - Focus area: From current work
   - Next steps: Derived from analysis

### STATUS.json Structure:

```json
{
  "session_id": "auto-generated",
  "timestamp": "ISO-8601",
  "phase": "Development phase name",
  "status": "Status code",
  "git_status": {
    "current_branch": "branch-name",
    "last_commit": "hash - message",
    "uncommitted_files": 3,
    "files": ["file1", "file2"],
    "stashes": 8
  },
  "in_progress_work": {
    "primary_focus": "What you're working on",
    "current_phase": "Current phase of work"
  },
  "next_steps": {
    "immediate": ["Action 1", "Action 2"],
    "this_session": ["Task 1", "Task 2"]
  },
  "metrics": {
    "sleep_score": "60/100"
  },
  "recommendations": {
    "before_leaving": ["Recommendation 1"],
    "next_session": ["Recommendation 2"]
  }
}
```

---

## Optimization Opportunities

### 1. Tool Call Reduction

**Current**: 11 tool calls
**Optimized**: 4 tool calls

```python
# Instead of 9 separate Bash calls, consolidate into 3:

# Call 1: Git analysis (single command)
git_data = """
git status --porcelain
echo "---SEPARATOR---"
git branch --merged main | grep -v "^\*" | grep -v "main" | wc -l
echo "---SEPARATOR---"
git stash list | wc -l
echo "---SEPARATOR---"
git log -1 --format="%h - %s"
echo "---SEPARATOR---"
git rev-parse --abbrev-ref HEAD
"""

# Call 2: GitHub analysis (single command)
gh_data = """
gh issue list --state open --limit 5 --json number,title,updatedAt
echo "---SEPARATOR---"
gh run list --limit 1 --json conclusion,status,createdAt
"""

# Call 3: Service analysis (single command)
service_data = """
ps aux | grep -E "(node|npm|pnpm|redis|postgres|supabase)" | grep -v grep || echo "None"
echo "---SEPARATOR---"
ls ~/.claude/logs/*.log 2>/dev/null | wc -l
"""

# Call 4: Use pop-session-capture skill (invokes capture_state.py)
# → Automatically reads current state and writes STATUS.json
```

**Reduction**: 11 calls → 4 calls (64% reduction)

### 2. Caching Strategy

Use `routine_cache.py` to cache values that don't change frequently:

- **Cache for 1 hour**: GitHub issue list
- **Cache for 15 minutes**: CI status
- **Never cache**: Git status (changes frequently)

### 3. Skill Chaining

```
pop-nightly
├─ capture_state.py  → Gather git + GitHub + service data
├─ calculate_score    → Compute Sleep Score
├─ generate_report    → Format nightly report
└─ pop-session-capture → Update STATUS.json
```

---

## Proposed `pop-nightly` Skill Architecture

### File Structure:

```
packages/popkit-dev/skills/pop-nightly/
├── SKILL.md                    # Skill definition
├── scripts/
│   ├── nightly_workflow.py    # Main orchestration
│   ├── sleep_score.py         # Score calculation logic
│   └── report_generator.py   # Report formatting
├── workflows/
│   └── nightly-workflow.json  # Workflow steps definition
└── tests/
    └── test_nightly.py        # Unit tests
```

### Integration Points:

| Utility | Purpose | Location |
|---------|---------|----------|
| `capture_state.py` | Git/GitHub/service data collection | `shared-py/popkit_shared/utils/` |
| `routine_measurement.py` | Performance tracking | `shared-py/popkit_shared/utils/` |
| `routine_cache.py` | Caching for efficiency | `shared-py/popkit_shared/utils/` |
| `session_recorder.py` | Recording support | `shared-py/popkit_shared/utils/` |
| `pop-session-capture` | STATUS.json updates | `popkit-dev/skills/` |

### Workflow Steps:

1. **Initialize**: Check if recording is active
2. **Collect Data**: Use `capture_state.py` to gather all context
3. **Calculate Score**: Compute Sleep Score (0-100)
4. **Generate Report**: Format nightly report with recommendations
5. **Capture State**: Invoke `pop-session-capture` skill
6. **Present Report**: Display to user

---

## Recording System Findings

### What We Learned:

1. **Recording Captures All Tool Calls**: The system recorded 25 events, including tool calls from concurrent work
2. **Hook Integration Works**: post-tool-use.py is firing and capturing events
3. **Timing Issue**: Tool calls made DURING recording weren't captured in expected sequence
4. **Session Isolation**: Recording captures the entire session, not just specific command execution

### Recording System Issues Discovered:

| Issue | Impact | Fix Priority |
|-------|--------|--------------|
| Tool calls from concurrent work captured | Noisy recording data | Medium |
| Nightly routine commands not isolated | Hard to analyze specific workflow | High |
| No filtering by command/skill context | Mixed event streams | Medium |

### Recommendations for Recording System:

1. **Add Context Filtering**: Tag events with skill/command context
2. **Isolate Workflows**: Option to record only specific skill executions
3. **Event Correlation**: Link tool calls to the command that triggered them
4. **Timestamp Validation**: Ensure events are captured in correct sequence

---

## Next Steps

### Immediate (Phase 3):

- [x] Complete baseline analysis (this document)
- [ ] Design `pop-nightly` skill structure
- [ ] Create SKILL.md with proper frontmatter
- [ ] Implement `nightly_workflow.py` orchestration
- [ ] Implement `sleep_score.py` calculation logic

### Short-term (Phase 4):

- [ ] Write unit tests for Sleep Score calculation
- [ ] Test skill with real nightly routine execution
- [ ] Record execution with new skill
- [ ] Compare manual vs. automated workflows

### Long-term (Phase 7):

- [ ] Create `pop-morning` skill using same methodology
- [ ] Document recording-driven development process
- [ ] Update `/popkit:routine` command to use new skills
- [ ] Submit PR with skills and documentation

---

## Success Criteria

### For `pop-nightly` Skill:

1. **Automation**: Reduces manual workflow from 11 to 4 tool calls
2. **Accuracy**: Sleep Score matches manual calculation
3. **Reliability**: STATUS.json always updated correctly
4. **Performance**: Completes in <20 seconds
5. **User Experience**: Clear, actionable nightly report

### For Recording System:

1. **Coverage**: Captures all tool calls made during nightly routine
2. **Isolation**: Can filter events by command/skill context
3. **Analysis**: Provides actionable performance metrics
4. **Validation**: Golden file comparison for workflow verification

---

**Document Status**: ✅ Complete
**Next Document**: Design specification for `pop-nightly` skill
**Session Recording**: `~/.claude/popkit/recordings/2025-12-28-152810-nightly-routine-baseline-20251228-152810-9aa2deb0.json`
**HTML Report**: [file:///C:/Users/Josep/.claude/popkit/recordings/2025-12-28-152810-nightly-routine-baseline-20251228-152810-9aa2deb0.html](file:///C:/Users/Josep/.claude/popkit/recordings/2025-12-28-152810-nightly-routine-baseline-20251228-152810-9aa2deb0.html)
