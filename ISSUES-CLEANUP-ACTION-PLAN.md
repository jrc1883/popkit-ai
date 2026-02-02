# PopKit Issues Cleanup Action Plan
**Prepared:** 2026-01-31 | **Priority:** High | **Effort:** 30 minutes

---

## Quick Start: Immediate Actions

### STEP 1: Close Recently Completed Issues (5 mins)

These have merged PRs and verified implementations. Close them now:

```bash
# Issue #215 - Merged PR #219 (2026-01-31T20:50:38Z)
gh issue close 215 -c "Merged via PR #219. Anthropic upstream tracking system fully implemented with /popkit-core:upstream command and impact assessment system."

# Issue #216 - Merged PR #220 (2026-01-31T22:59:44Z)
gh issue close 216 -c "Merged via PR #220. GitHub cache status inspection command complete with CLI status reporting."

# Issue #217 - Merged PR #221 (2026-01-31T23:07:22Z)
gh issue close 217 -c "Merged via PR #221. GitHub CLI detection and graceful error handling implemented."

# Issue #213 - Merged PR #214 (2026-01-31T18:48:47Z)
gh issue close 213 -c "Merged via PR #214. Official plugin integration guidance added to CLAUDE.md documentation."
```

**Expected Time:** 5 minutes | **Impact:** 4 issues resolved | **Complexity:** Trivial

---

### STEP 2: Triage & Label High-Priority Stale Issues (10 mins)

These are HIGH priority but have no recent updates. Add status comments:

**Issue #81: PopKit Workflow Benchmark Testing**
- **Priority:** HIGH (explicit label)
- **Created:** 2026-01-10
- **Action:** Add comment requesting status update
- **Command:**
```bash
gh issue comment 81 -b "Status check: This HIGH-priority testing task hasn't been updated since creation. Please provide:
1. Current completion percentage
2. Blockers or challenges
3. Target completion date
4. Ownership/assignment

Related: Issue #82 (benchmark suite) is now closed. Does #82 completion address this issue's scope?"
```

**Issue #18: User Acceptance Testing (UAT)**
**Issue #11: Cross-Plugin Integration Testing**
**Issue #10: Agent Routing Accuracy Testing**
- **Priority:** HIGH (validation blockers)
- **Action:** Same - request status update
- **Command:**
```bash
gh issue comment 18 -b "Validation milestone status: Please provide current progress, blockers, and target completion for UAT."
gh issue comment 11 -b "Validation milestone status: Please provide current progress, blockers, and target completion for cross-plugin testing."
gh issue comment 10 -b "Validation milestone status: Please provide current progress, blockers, and target completion for agent routing testing."
```

**Expected Time:** 10 minutes | **Impact:** Unblocks decision-making | **Complexity:** Minimal

---

### STEP 3: Clarify Scope for Partial Implementations (10 mins)

These issues are partially implemented or have overlapping scope. Need clarification:

**Issue #68: Agent Expertise System (/popkit:expertise)**
- **Status:** Issue #80 (agent detection) completed and closed
- **Question:** Is the full expertise system still needed beyond what #80 provides?
- **Action:** Comment to clarify remaining scope
```bash
gh issue comment 68 -b "Clarification needed: Issue #80 (agent detection via POPKIT_ACTIVE_AGENT) is now complete.
Please clarify remaining scope for this issue:
- Is full /popkit:expertise command still needed?
- What features beyond automatic detection are required?
- Should this be split into focused subtasks?
- Target timeline and owner?"
```

**Issue #67: Cache Management System (/popkit:cache)**
- **Status:** Issue #216 (cache status inspection) just merged
- **Question:** Is broader cache management system still needed?
- **Action:** Comment to clarify scope vs. #216
```bash
gh issue comment 67 -b "Scope clarification needed: Issue #216 (cache status inspection) just merged.
This issue describes broader cache management. Please clarify:
- Is #216 sufficient for immediate needs?
- What additional cache features are required (invalidation, TTL management, etc.)?
- Should this be deferred or split into focused tasks?
- Priority and target timeline?"
```

**Issue #69: Create Generic Workspace Routine Templates**
- **Status:** Related to closed Issue #70 (nightly routine)
- **Action:** Check if #70 addressed this
```bash
gh issue comment 69 -b "Related issue status: Issue #70 (nightly routine) was completed and closed. Does that issue address this task's scope? If so, this can be closed. If additional morning routine templates are needed, please clarify scope."
```

**Expected Time:** 10 minutes | **Impact:** Prevents duplicate work | **Complexity:** Minimal

---

## Next Steps: Secondary Actions (Optional)

### STEP 4: Archive Old Investigation Issues (Optional, next week)

These are old (21+ days) with no sign of active work. Decision: Keep investigating or archive?

**Candidates for closure if investigation is complete:**
- #100: Code Commenting Standards Investigation
- #92: Track Anthropic SDK Patterns for Future Migration
- #102: Transcript Collection Automation

**Action:** Check if findings are documented
```bash
# Check if #100 findings are in codebase
grep -r "code-commenting" apps/popkit/docs/

# If documented, close with:
gh issue close 100 -c "Investigation findings documented in X. Closing as completed."
```

### STEP 5: Update Epic Descriptions (Optional, next week)

Issues #28 and #27 are vague epics. Clarify scope:

**Issue #28: Task Master Complementary Feature Integration**
```bash
gh issue edit 28 --body "# Task Master Integration Epic

## Objective
Integrate PopKit features with Task Master platform for task-driven development workflows.

## Sub-tasks
- [ ] Unclear - requires clarification with team

## Related Issues
- None linked yet

## Status
BLOCKED: Requires scope clarification"
```

**Issue #27: Auto Claude Competitive Feature Integration**
```bash
gh issue edit 27 --body "# Auto Claude Feature Integration Epic

## Objective
Integrate PopKit features with Auto Claude for complementary LLM workflows.

## Sub-tasks
- [ ] Unclear - requires clarification with team

## Related Issues
- None linked yet

## Status
BLOCKED: Requires scope clarification"
```

### STEP 6: Consolidate Power Mode Infrastructure Issues

Consider consolidating related issues into single epic:
- #78: True Redis coordination
- #76: Distributed agent coordination protocol
- #77: Agent thinking process visibility
- #79: Synthesize agent data into reports

**Action:** Create umbrella epic and link these as sub-issues.

---

## Recommended SLAs for Future

To prevent this situation recurring:

| Category | SLA |
|----------|-----|
| **Features (Merged PR)** | Close within 7 days |
| **Bugs (Fixed)** | Close within 3 days |
| **Investigations** | Close or update every 14 days |
| **Epics** | Update status monthly |
| **Stale Auto-Label** | 60+ days without activity |

---

## Expected Outcomes

### Immediate (Today)
- **4 issues closed** (merged features)
- **6 issues commented** (status requests)
- **3 issues clarified** (scope questions)

### This Week
- **~2 additional closures** (if investigations documented)
- **Better visibility** on validation testing blockers
- **Clear scope** for #68, #67, #69

### This Month
- **~6-8 issues archived** (stale investigations)
- **Epics updated** with progress
- **Cleanup audit** reduces open count from 40 to ~28

---

## Labels to Consider Adding

For future issue management:

```yaml
- `needs-scope-clarification` - Epic or feature needs scope definition
- `stale` - No update in 60+ days (auto-applied by bot)
- `awaiting-owner` - Assigned person needs to comment
- `release-blocker` - Blocks release milestone
- `investigation-complete` - Investigation done, findings documented
- `roadmap-future` - Deferred to future version
```

---

## Success Metrics

By end of this week:
- [ ] 4 recently-completed issues closed
- [ ] 6 high-priority issues with status comments
- [ ] 3 scope-ambiguous issues clarified
- [ ] Open issue count: 40 → 33
- [ ] All HIGH-priority issues with owner assignment and target date

---

## Contact & Escalation

If issues cannot be resolved during cleanup:
1. Assign owner and add to project board
2. Link to appropriate epic
3. Add milestone for target release
4. Mark with `awaiting-owner` label for follow-up

