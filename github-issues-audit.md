# PopKit GitHub Issues Audit Report

**Generated:** 2026-01-31 | **Total Open Issues:** 40

---

## Executive Summary

This audit identifies 40 open GitHub issues across the PopKit repository, categorizing them by completion status, staleness, labeling quality, and cleanup opportunities. Key findings:

- **Recently Completed Features (4):** Issues #215, #216, #217 have merged PRs but remain open
- **Stale Issues (21):** Created 2026-01-10 or earlier with last update on 2026-01-10 (21+ days old)
- **Very Recent Issues (5):** Created today (2026-01-31)
- **Epic/Meta Issues (5):** Parent issues tracking multiple sub-tasks
- **Issues Needing Closure (4):** Implementation verified, PRs merged

---

## Section 1: ISSUES READY TO CLOSE

These issues have clear evidence of completion through merged PRs or implementation in recent releases.

### 1.1 Recently Completed Features (PRs Merged, Issues Still Open)

**Issue #215: [PopKit Core] Feature: Anthropic upstream tracking system (/popkit-core:upstream)**

- **Status:** COMPLETE
- **Merged PR:** #219 (2026-01-31T20:50:38Z)
- **CHANGELOG Entry:** Yes (unreleased section)
- **Features Implemented:**
  - New `/popkit-core:upstream` command with 5 subcommands: check, list, research, synthesize, stats
  - Monitors 4 repositories: claude-code, claude-plugins-official, anthropic-sdk-python, anthropic-sdk-typescript
  - Impact assessment system: critical/high/medium/low/none/alignment
  - Data storage: `.claude/popkit/upstream-tracking.json`
- **Action:** CLOSE - Feature is fully implemented and merged
- **Recommended Label:** None needed (has appropriate labels: priority:high, type:enhancement, cloud)

**Issue #216: [Shared] Enhancement: Add cache status inspection command**

- **Status:** COMPLETE
- **Merged PR:** #220 (2026-01-31T22:59:44Z)
- **CHANGELOG Entry:** Yes (unreleased section)
- **Features Implemented:**
  - New `status` command for `github_cache.py` CLI
  - Shows cache state, freshness, count, TTL, and health metrics
- **Action:** CLOSE - Feature is fully implemented and merged
- **Related:** Issue #96 (cache management - also closed)

**Issue #217: [Shared] Enhancement: Graceful handling when GitHub CLI not installed**

- **Status:** COMPLETE
- **Merged PR:** #221 (2026-01-31T23:07:22Z)
- **CHANGELOG Entry:** Yes (unreleased section)
- **Features Implemented:**
  - New `is_gh_cli_available()` function in shared module
  - New `ensure_gh_cli()` with platform-specific error messages
  - Integration into GitHubCache methods
- **Action:** CLOSE - Feature is fully implemented and merged

**Issue #213: Integrate official code-review plugin into PopKit workflows**

- **Status:** INVESTIGATION STAGE
- **Related Merged PR:** #214 (2026-01-31T18:48:47Z) - "docs: Add official plugin integration guidance"
- **CHANGELOG Entry:** Documented in release notes
- **Features:** Official plugin integration guidance added to CLAUDE.md
- **Action:** CLOSE or clarify scope - Documentation completed, implementation guidance provided
- **Note:** Original issue scope appears addressed through documentation; if additional implementation needed, create new focused issue

---

### 1.2 Historical Completion (Already Implemented, Verified)

**Issue #80: Agent Routing: Set POPKIT_ACTIVE_AGENT environment variable**

- **Status:** COMPLETE - CLOSED (2026-01-31T05:14:18Z)
- **Merged PR:** #210 (2026-01-31T05:14:17Z)
- **Implementation:** Integrated semantic_router into post-tool-use.py hook
- **Note:** Already closed - referenced in audit for context

**Issue #96: [PopKit] Feature: Implement GitHub metadata caching**

- **Status:** COMPLETE - CLOSED (2026-01-31T03:24:53Z)
- **Merged PR:** #192 (2026-01-26 via #208)
- **Features:** Two-tier caching system for GitHub labels, milestones, team members
- **Note:** Already closed - provides foundation for issues #216, #217

---

## Section 2: STALE ISSUES REQUIRING TRIAGE

Issues created 2026-01-10 or earlier with no updates since 2026-01-10 (21+ days old). These are candidates for clarification, refinement, or closure.

### 2.1 Completely Stale - No Updates in 21 Days (12 issues)

These issues have not been touched since creation date or earlier and need triage decisions.

| #   | Title                                                             | Created | Updated | Status | Priority | Type          | Action                                                                    |
| --- | ----------------------------------------------------------------- | ------- | ------- | ------ | -------- | ------------- | ------------------------------------------------------------------------- |
| 102 | Transcript Collection Automation                                  | Jan 10  | Jan 10  | OPEN   | Low      | Enhancement   | Clarify scope, link to Power Mode transcript parsing (Issue #110, closed) |
| 100 | Code Commenting Standards Investigation                           | Jan 10  | Jan 10  | OPEN   | Low      | Feature       | Check if findings documented; if complete, close as completed             |
| 95  | Optimize Redis Stream reading efficiency                          | Jan 10  | Jan 10  | OPEN   | Low      | Performance   | Verify if any optimization work started; otherwise defer or close         |
| 94  | Upstash Vector Upload + Enhanced Agent Embeddings                 | Jan 10  | Jan 10  | OPEN   | Medium   | Feature       | Cloud feature - assess priority with team; may need roadmap update        |
| 92  | Track Anthropic SDK Patterns for Future Migration                 | Jan 10  | Jan 10  | OPEN   | Low      | Documentation | Investigation task - check if findings documented                         |
| 84  | Run vibe-coded benchmarks to test ambiguity handling              | Jan 10  | Jan 10  | OPEN   | Low      | Testing       | Related to benchmark suite (Issue #82, closed); verify scope              |
| 83  | Build Workflow Metrics Analyzer                                   | Jan 10  | Jan 10  | OPEN   | Medium   | Feature       | Power Mode metrics - check if Issue #82 completed this                    |
| 81  | PopKit Workflow Benchmark Testing                                 | Jan 10  | Jan 10  | OPEN   | High     | Testing       | CRITICAL: High priority feature - why no progress? Needs review           |
| 79  | Synthesize raw agent data into human-readable coordination report | Jan 10  | Jan 10  | OPEN   | Medium   | Feature       | Power Mode reporting - assess status                                      |
| 78  | Implement true Redis coordination for Power Mode                  | Jan 10  | Jan 10  | OPEN   | Low      | Feature       | Cloud/Power Mode infrastructure - assess priority                         |
| 77  | Agent thinking process visibility in Redis coordination           | Jan 10  | Jan 10  | OPEN   | Medium   | Feature       | Power Mode observability - related to #82 (closed)                        |
| 76  | Distributed agent coordination protocol with work acknowledgment  | Jan 10  | Jan 10  | OPEN   | Medium   | Feature       | Cloud feature - verify if needed for current roadmap                      |

**Recommendation for Section 2.1:**

- Close #100, #92 if investigation findings are documented elsewhere
- Review #81 status (HIGH priority - needs attention)
- Consolidate #78, #76, #77, #79 into a single "Power Mode infrastructure" epic if still relevant
- Verify #82 (benchmark suite, now closed) addressed #83, #84 concerns

### 2.2 Old Issues with Some Activity (9 issues)

Created Jan 9-10 but touched during the automation period (last update Jan 10).

| #     | Title                                                   | Created  | Priority   | Status  | Next Action                                                                                                    |
| ----- | ------------------------------------------------------- | -------- | ---------- | ------- | -------------------------------------------------------------------------------------------------------------- |
| 72    | PopKit should invoke UI/design agents                   | Jan 10   | Low        | OPEN    | Design system roadmap item - defer or archive                                                                  |
| 71    | Add encouraging Bible verses to nightly routine         | Jan 10   | Low        | FEATURE | In progress (merged #206) - **CLOSE: Feature complete**                                                        |
| 69    | Create Generic Workspace Routine Templates              | Jan 10   | Medium     | OPEN    | Morning routine - check if #70 covered this (now closed)                                                       |
| 68    | Feature: Agent Expertise System (/popkit:expertise)     | Jan 10   | Medium     | OPEN    | **Complex:** Partially implemented (status #80 complete); full feature needs work. Split into tracked subtasks |
| 67    | Feature: Cache Management System (/popkit:cache)        | Jan 10   | Medium     | OPEN    | Partially addressed (#216 cache inspection); full cache mgmt system still needed - clarify scope               |
| 65    | Implement interactive questions in /popkit:project init | Jan 10   | Medium     | OPEN    | UI enhancement - assess priority for next cycle                                                                |
| 64    | Phase 4: PopKit Integration - /popkit:env Commands      | Jan 10   | Low        | OPEN    | Long-term planning - clarify scope and ownership                                                               |
| 63    | Epic: User Deployment Command (/popkit:deploy)          | Jan 10   | Medium     | EPIC    | Meta-issue - document progress and dependencies                                                                |
| 53-47 | Various strategy/roadmap issues                         | Jan 9-10 | Low-Medium | OPEN    | Strategic planning - keep but lower priority than current features                                             |

**Recommendation for Section 2.2:**

- Close #71 (Bible verses - implemented in beta.6)
- Clarify #68 (Expertise System) - document what's complete vs. remaining work
- Clarify #67 (Cache System) - distinguish from #216 (cache inspection) which is narrower scope
- Consolidate #63 subfeatures (65, 64) with clear dependencies

---

## Section 3: STRATEGIC/PLANNING ISSUES (Keep Open, Lower Priority)

These are intentionally open for long-term planning and roadmap management.

| #   | Title                                                   | Type          | Owner        | Status                                                   |
| --- | ------------------------------------------------------- | ------------- | ------------ | -------------------------------------------------------- |
| 50  | Quality Improvements Roadmap                            | Epic          | Core team    | Strategic planning                                       |
| 49  | Onboarding & Deployment Strategy                        | Documentation | Core team    | Strategic                                                |
| 52  | Workspaces Investigation for Multi-Project Support      | Feature       | Research     | Investigation                                            |
| 51  | Agent SDK v2 Monitoring & Compatibility                 | Documentation | Integration  | Monitoring                                               |
| 53  | v2.0 Platform Expansion Analysis                        | Documentation | Architecture | Future planning                                          |
| 47  | Slack Integration for Team Collaboration                | Feature       | Integration  | Backlog                                                  |
| 46  | VHS Screenshot System for Terminal Recording            | Feature       | DX           | Enhancement idea                                         |
| 45  | Capture reasoning tokens in session recordings          | Feature       | Core         | Backlog                                                  |
| 44  | Implement /popkit:worktree for issue-driven development | Feature       | Dev          | High-Priority (merged #177) - **VERIFY IF CLOSE NEEDED** |
| 43  | Unify account management under /popkit:account          | Feature       | Core         | Backlog                                                  |
| 38  | Security Hardening Epic                                 | Epic          | Security     | Ongoing                                                  |
| 28  | Epic: Task Master Complementary Feature Integration     | Epic          | Integration  | Backlog                                                  |
| 27  | Epic: Auto Claude Competitive Feature Integration       | Epic          | Integration  | Backlog                                                  |
| 18  | [Validation] User Acceptance Testing (UAT)              | Testing       | QA           | High-Priority                                            |
| 11  | [Validation] Cross-Plugin Integration Testing           | Testing       | QA           | High-Priority                                            |
| 10  | [Validation] Agent Routing Accuracy Testing             | Testing       | QA           | High-Priority                                            |

**Note:** Issues #18, #11, #10 are validation/testing tasks marked HIGH priority. Status unclear - these should have progress indicators.

---

## Section 4: ISSUES WITH MERGED FEATURES (Closed PRs)

Cross-referencing with merged PRs from the last 50 merges shows several issues may reference completed work.

### Features Merged This Week:

- #219: Issue #215 (Upstream tracking) - Issue status: OPEN
- #220: Issue #216 (Cache status) - Issue status: OPEN
- #221: Issue #217 (GH CLI detection) - Issue status: OPEN
- #214: Issue #213 (Plugin integration docs) - Issue status: OPEN
- #210: Issue #80 (Agent expertise) - Issue status: CLOSED (correct)
- #209: Issue #193 (Priority scheduling) - Issue status: CLOSED (correct)
- #208: Issue #96 (GitHub cache) - Issue status: CLOSED (correct)
- #207: Issue #21 (Skill optimization) - Issue status: CLOSED (correct)
- #176: Issue #82 (Benchmark suite) - Issue status: CLOSED (correct)
- #177: Issue #44 (Git worktree) - Issue status: OPEN - **CHECK IF NEEDS CLOSE**

### Analysis:

Issues #215, #216, #217, #213 have recent merged PRs but remain OPEN. These should be evaluated for closure.

---

## Section 5: LABEL QUALITY AUDIT

### Issues Missing Key Labels (Improved Since Migration)

**Good News:** Label coverage is excellent. Most issues have:

- Priority label (High/Medium/Low)
- Type label (Feature/Enhancement/Bug/Testing/Documentation)
- Component/Workstream label

**Minor Issues:**

- Issue #218 has 7 labels - consider if all are necessary (possible label inflation)
- Some issues have both "feature" and "enhancement" (redundant classification)
- "cloud" label on #218, #215 missing description - inherited from migration?

**Recommendation:**

- Keep current labeling system - very well maintained
- Document label usage guidelines to prevent future redundancy

---

## Section 6: EPIC/META ISSUES STATUS

Issues designed to track multiple sub-issues:

| Epic                         | #       | Status | Child Issues               | Completeness                          |
| ---------------------------- | ------- | ------ | -------------------------- | ------------------------------------- |
| Quality Improvements Roadmap | 50      | OPEN   | Multiple quality features  | ~70% (many closed)                    |
| Security Hardening           | 38      | OPEN   | CodeQL, testing, reporting | ~80% (CodeQL closed, testing ongoing) |
| User Deployment              | 63      | OPEN   | #65, #64 (env/init)        | ~30% (core feature needed)            |
| Task Master Integration      | 28      | OPEN   | Unclear scope              | NEEDS CLARIFICATION                   |
| Auto Claude Integration      | 27      | OPEN   | Unclear scope              | NEEDS CLARIFICATION                   |
| v1.0.0 Release Blockers      | Various | CLOSED | Test coverage, validation  | 100% (all completed)                  |

**Recommendation:**

- Update epic descriptions in #28, #27 to clarify scope and ownership
- Document epic progress for #50, #38, #63 to show stakeholders current status

---

## Section 7: RECOMMENDATIONS FOR CLEANUP

### Immediate Actions (This Week)

**CLOSE (4 issues):**

1. Issue #215 - Upstream tracking (merged #219)
2. Issue #216 - Cache status (merged #220)
3. Issue #217 - GH CLI detection (merged #221)
4. Issue #213 - Plugin integration (merged #214, docs complete)

**Commands to close:**

```bash
gh issue close 215 --reason completed
gh issue close 216 --reason completed
gh issue close 217 --reason completed
gh issue close 213 --reason completed
```

### Short-Term Actions (Next 2 Weeks)

**TRIAGE & CLARIFY (12 issues):**

1. Issue #81 (Benchmark Testing) - HIGH priority, no recent work
   - Action: Review current progress, update scope, assign owner

2. Issue #68 (Agent Expertise System) - COMPLEX
   - Current: Partially implemented (#80 complete)
   - Action: Break into sub-issues, document what's remaining (full system vs. current implementation)

3. Issue #67 (Cache Management System) - SCOPE CONFLICT
   - Current: #216 addressed cache inspection (narrower scope)
   - Action: Clarify scope - is this still needed for broader cache invalidation/TTL management?

4. Issues #28, #27 (Epics) - CLARITY NEEDED
   - Action: Update descriptions to clarify scope, status, ownership

5. Issues #71 (Bible verses) - IMPLEMENTED
   - Action: Close (feature merged in beta.6)

6. Issues #45, #46, #47 - BACKLOG ITEMS
   - Action: Confirm these are strategic backlog or move to project board

**VERIFY CLOSURE (2 issues):** 7. Issue #44 - Worktree feature (merged #177) - verify can close 8. Issue #69 - Routine templates (related to closed #70) - verify can close

### Long-Term Actions (Monthly Audit)

1. **Implement Issue Review Process:**
   - Monthly audit of issues older than 30 days
   - Require status update comments from assigned owner
   - Auto-label issues without updates in 60+ days with "stale" label

2. **Restructure Roadmap:**
   - Move long-term items (#52, #53, etc.) to GitHub Project Board instead of issues
   - Maintain only "current cycle" and "next cycle" issues as open
   - Use issue templates to require status field on creation

3. **Consolidate Related Issues:**
   - #78, #76, #77, #79 → Consolidate into "Power Mode Infrastructure" epic
   - #100, #92 → Link with research documentation or close if findings documented

4. **Establish SLAs:**
   - Features: Close within 7 days of merged PR
   - Bugs: Confirm fixed/won't-fix within 14 days
   - Investigations: Provide status update or closure/refinement every 2 weeks

---

## Section 8: DUPLICATE/SIMILAR ISSUES

No obvious duplicates detected. Label system and clear titling prevent most duplication.

**Closely Related (Consider Linking):**

- #216 (cache status inspection) and #67 (cache management system) - Related but different scope
- #68 (Expertise System) and #80 (now closed) - Expertise activation complete, system still in progress
- #82 (benchmark suite, closed) and #81, #83, #84 - May have addressed these partially
- #75 (Power Mode XML protocol, closed) and #78, #76, #77 - Foundational work for coordination

---

## Section 9: ISSUES NEEDING BETTER DESCRIPTIONS

No critical issues found. Most descriptions are detailed. Minor improvements:

| Issue | Current                         | Improvement Needed                                                |
| ----- | ------------------------------- | ----------------------------------------------------------------- |
| #28   | "Epic: Task Master Integration" | Clarify what "Task Master" refers to and what integration entails |
| #27   | "Epic: Auto Claude Integration" | Clarify scope - which Auto Claude features?                       |
| #52   | "Workspaces Investigation"      | Add findings/recommendations once investigation complete          |
| #53   | "v2.0 Platform Expansion"       | Update with v2.0 roadmap items as defined                         |

---

## Section 10: VALIDATION TESTING ISSUES

**Important Note:** Three HIGH-priority validation testing issues remain open:

- Issue #18: User Acceptance Testing (UAT)
- Issue #11: Cross-Plugin Integration Testing
- Issue #10: Agent Routing Accuracy Testing

These are blockers for release validation. Current status unclear - recommend:

1. Add milestone labels indicating target release
2. Add "progress" comments if partially complete
3. Convert to project board tasks if work is in-progress but issues are stale

---

## SUMMARY TABLE

| Category                 | Count | Action                                 |
| ------------------------ | ----- | -------------------------------------- |
| **Ready to Close**       | 4     | Close immediately (recently merged)    |
| **Stale & Needs Triage** | 12    | Review, clarify scope, update or close |
| **Strategic/Planning**   | 16    | Keep open, lower priority              |
| **Validation Testing**   | 3     | High priority - verify status          |
| **Possibly Complete**    | 2     | Verify merge status                    |
| **Needs Better Scope**   | 3     | Epic clarification needed              |
| **TOTAL OPEN**           | 40    | 15% ready for closure, 30% need triage |

---

## APPENDIX: Complete Issue List by Status

### READY TO CLOSE (4)

- #215: Upstream tracking system (merged #219)
- #216: Cache status inspection (merged #220)
- #217: GH CLI detection (merged #221)
- #213: Official plugin integration (merged #214)

### HIGH PRIORITY - VERIFY STATUS (3)

- #18: User Acceptance Testing (High priority, validation)
- #11: Cross-Plugin Integration Testing (High priority, validation)
- #81: PopKit Workflow Benchmark Testing (High priority, no recent updates)

### NEEDS TRIAGE (12)

- #102, #100, #95, #94, #92, #84, #83, #79, #78, #77, #76, #72

### ONGOING/STRATEGIC (16)

- #71, #70 (routine features), #69, #68, #67, #65, #64, #63, #53, #52, #51, #50, #49, #47, #46, #45, #44, #43, #38, #28, #27

### VERIFICATION NEEDED (2)

- #44: Worktree implementation (merged #177)
- #71: Bible verses (merged #206)

---

**Report Generated:** 2026-01-31 by GitHub Issues Audit Tool
**Repository:** anthropics/popkit-claude
**Next Audit Recommended:** 2026-03-02 (monthly review)
