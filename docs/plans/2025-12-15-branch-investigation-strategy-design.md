# Branch Investigation & Integration Strategy - Design Document

**Date:** 2025-12-15
**Status:** Approved
**Epic:** #240
**Type:** Process Design

---

## Executive Summary

PopKit has 9 feature branches containing significant research, designs, and implementations that need systematic investigation to determine their integration path into v1.0 (marketplace launch) or v2.0 (platform expansion).

**Key Decision:** We will **evaluate all branches equally** without pre-judging v1.0 vs v2.0 assignment, using a structured per-branch analysis template to make informed, documented decisions.

---

## Background

### The Challenge

During development, multiple Claude sessions created feature branches containing:
- Comprehensive research documents
- Architecture designs
- Partial implementations
- Market analysis
- Performance optimizations

Without systematic investigation, we risk:
- Losing valuable work
- Duplicating effort
- Making uninformed roadmap decisions
- Missing critical dependencies between features

### Branch Catalog (9 total)

#### Platform Vision (v2.0 Potential)
1. **Multi-Model Dispatch** (`claude/pop-kit-script-execution-sOHL9`)
   - Dynamic routing across Claude models
   - Cost optimization (20-40% savings)
   - Runtime complexity scoring

2. **Async Orchestration** (`claude/async-agent-orchestration-egT0Y`)
   - GitHub-triggered agents
   - Spawn location intelligence (home → server → cloud)
   - Long-running task handoffs

3. **Cross-Platform CLI** (`claude/research-cli-tools-Dg3ui`)
   - Standalone CLI via Textual framework
   - Multi-IDE integration (VS Code, Cursor, etc.)
   - Platform-agnostic orchestration

#### Architecture Improvements
4. **Skill Structure** (`claude/skill-structure-organization-01PzL9WuqrVfUnwReHMfa2eX`)
   - Tiered routing architecture
   - Lazy loading optimization

5. **PopKit Initialization** (`claude/analyze-popkit-startup-lr32y`)
   - Entry point optimization
   - Startup performance analysis

#### Features
6. **Scratch Pad** (`claude/add-scratch-pad-feature-tTEcB`)
   - Enhanced session capture/restore
   - State management improvements

7. **Slack Notifications** (`claude/analyze-slack-notification-GCaQZ`)
   - Auto-formatter for Power Mode messages
   - Consistent notification formatting

8. **Terminal Helper** (`claude/keep-terminal-helper-text-zVY23`)
   - Tier-based color coding
   - Visual clarity improvements

#### Research
9. **Vibe Engineering** (`claude/research-vibe-engineering-a0J4y`)
   - Market positioning
   - Competitive analysis

---

## Design Principles

### 1. Equal Evaluation

**No pre-judging v1.0 vs v2.0:**
- Each branch gets the same analytical rigor
- Decisions based on evidence, not assumptions
- Complex features may split (basic in v1, advanced in v2)

**Example:** Async orchestration has:
- **v1 component**: Existing async agent support (already in Claude Code)
- **v2 component**: Cloud-based GitHub triggers (new infrastructure)

### 2. Comprehensive Analysis Template

For each branch, document:

```markdown
### 1. What Exists Today (Master)
- Current capabilities
- Infrastructure already built
- Overlaps with existing features

### 2. What's New in Branch
- Novel ideas/implementations
- Research findings
- Design decisions

### 3. Dependencies
- Other branches/features required
- Infrastructure needs
- External service dependencies

### 4. Integration Complexity
- **Effort**: Low / Medium / High / Epic
- Files affected (estimate)
- Testing requirements
- Breaking changes?
- Migration needed?

### 5. Value Proposition
- Problems solved
- User impact (high/medium/low)
- Primary use cases
- Alignment with roadmap

### 6. Risks
- **Technical**: Complexity, performance, reliability
- **Business**: User confusion, support burden
- **Maintenance**: Technical debt, testing surface area

### 7. Recommendation
- [ ] Merge to v1.0 - Ready now, high value, low risk
- [ ] Defer to v2.0 - Good idea, not critical for launch
- [ ] Split v1+v2 - Basic version now, advanced later
- [ ] Archive - Not aligned with roadmap

**Rationale**: [Document decision reasoning]
```

### 3. Systematic Process

**Phase 1: Infrastructure Setup** (1 session)
- [x] Create epic #240
- [x] Create 9 child issues (#241-249)
- [ ] Set up research document template

**Phase 2: Branch-by-Branch Analysis** (2-3 sessions)
- [ ] Investigate each branch using template
- [ ] Document findings in `docs/research/`
- [ ] Identify blockers and dependencies
- [ ] Note valuable patterns

**Phase 3: Synthesis & Planning** (1-2 sessions)
- [ ] Compile master findings document
- [ ] Create dependency graph
- [ ] Build value vs effort matrix
- [ ] Make v1.0 vs v2.0 decisions

**Phase 4: Execution Planning** (1 session)
- [ ] Create implementation issues
- [ ] Update milestones
- [ ] Archive non-integrated branches
- [ ] Document all decisions

### 4. Power Mode for Parallel Investigation

**Recommended for Phase 2:**
- Independent branches can be investigated in parallel
- Use `researcher` agent per branch
- Sync insights between agents
- Faster completion (2-3 sessions vs 5-6 sequential)

**Agent allocation example:**
```
researcher-1 → Multi-model dispatch (#241)
researcher-2 → Async orchestration (#242)
researcher-3 → Cross-platform CLI (#243)
[sync barrier - share findings]
researcher-1 → Skill structure (#244)
researcher-2 → PopKit startup (#245)
researcher-3 → Scratch pad (#246)
[sync barrier - dependency mapping]
...
```

---

## Investigation Workflow

### Per-Branch Investigation Process

```
1. Checkout branch
   ↓
2. Review commits and research docs
   ↓
3. Identify new vs existing capabilities
   ↓
4. Analyze dependencies
   ↓
5. Assess integration complexity
   ↓
6. Document value proposition
   ↓
7. Identify risks
   ↓
8. Make recommendation (keep/defer/split/archive)
   ↓
9. Document rationale
   ↓
10. Create research doc in docs/research/
```

### Deliverables Per Branch

- Research document: `docs/research/2025-12-15-<branch-name>-investigation.md`
- Updated child issue with findings
- Recommendation with rationale

### Synthesis Deliverables

- Master findings: `docs/research/2025-12-15-branch-investigation-synthesis.md`
- Dependency graph (Mermaid diagram)
- Value vs effort matrix (table)
- Roadmap decisions document

---

## Decision Framework

### Value vs Effort Matrix

```
         │ Low Effort │ Medium Effort │ High Effort
─────────┼────────────┼───────────────┼─────────────
High     │ v1.0 NOW   │ v1.0 PLANNED  │ v2.0 or Split
Value    │            │               │
─────────┼────────────┼───────────────┼─────────────
Medium   │ v1.0 NICE  │ Evaluate      │ v2.0 or Defer
Value    │            │               │
─────────┼────────────┼───────────────┼─────────────
Low      │ Optional   │ Defer         │ Archive
Value    │            │               │
```

### v1.0 vs v2.0 Criteria

**v1.0 (Marketplace Launch):**
- Critical for core functionality
- Enhances existing capabilities
- Low integration risk
- Well-tested and documented
- Aligns with Claude Code plugin scope

**v2.0 (Platform Expansion):**
- Multi-platform vision
- Requires new infrastructure
- High complexity/risk
- Nice-to-have, not essential
- Cross-IDE, multi-model capabilities

**Split v1 + v2:**
- Basic version provides immediate value
- Advanced features require more infrastructure
- Clear separation between basic and advanced
- Example: Async agents (v1: local) + GitHub triggers (v2: cloud)

### Archive Criteria

- Doesn't align with roadmap
- Superseded by better approach
- Technical debt outweighs benefits
- Maintenance burden too high
- User value unclear

---

## Validation Strategy

### How We Validate Decisions

**Benchmark Testing:**
- Currently running benchmarks to validate PopKit workflows
- Use benchmark results to inform complexity estimates
- Test integration feasibility with real workflows

**Documentation Review:**
- Ensure all decisions are documented with "why"
- Get feedback from benchmarking Claude (second perspective)
- Update CLAUDE.md with roadmap clarity

**Dependency Validation:**
- Map all inter-branch dependencies
- Ensure no circular dependencies
- Identify critical path features

---

## Success Metrics

- [ ] 100% of branches investigated (9/9)
- [ ] Zero valuable work lost
- [ ] Clear v1.0 vs v2.0 boundaries
- [ ] All decisions documented with rationale
- [ ] Dependency map complete
- [ ] Integration roadmap created
- [ ] No rushed decisions (thoroughness over speed)

---

## Timeline

**Target:** 5-7 sessions for complete investigation

| Phase | Sessions | Status |
|-------|----------|--------|
| Phase 1: Setup | 1 | ✅ Complete |
| Phase 2: Investigation | 2-3 | ⏳ Pending |
| Phase 3: Synthesis | 1-2 | ⏳ Pending |
| Phase 4: Execution Planning | 1 | ⏳ Pending |

---

## Risk Mitigation

### Risk: Analysis Paralysis

**Mitigation:**
- Time-box each branch investigation (90 minutes max)
- Use structured template to stay focused
- Make decisions even with incomplete information
- Document uncertainties and revisit later if needed

### Risk: Valuable Work Lost

**Mitigation:**
- Systematic investigation of every branch
- Research documents preserve all findings
- "Archive" doesn't mean delete - branches stay in repo
- Can resurrect ideas in v2.0+ if validated later

### Risk: Integration Conflicts

**Mitigation:**
- Dependency mapping in Phase 3
- Test integrations with benchmark workflows
- Identify blockers early
- Staged rollout plan

---

## Next Steps

After this design is approved:

1. **Begin Phase 2 Investigation**
   - Use `/popkit:dev work #241` to start with multi-model dispatch
   - Or use `/popkit:power start` for parallel investigation
   - Follow per-branch analysis template

2. **Document Findings**
   - Create research docs for each branch
   - Update child issues with findings
   - Note cross-branch dependencies

3. **Synthesize Results**
   - Compile master findings
   - Create dependency graph
   - Build value vs effort matrix
   - Make roadmap decisions

4. **Execute Integration**
   - Create implementation issues for accepted features
   - Update milestones (v1.0.0, v2.0.0)
   - Archive non-integrated branches

---

## Appendix: Investigation Template

```markdown
# [Branch Name] Investigation

**Branch**: `<git-branch-name>`
**Child Issue**: #<number>
**Parent Epic**: #240
**Date**: 2025-12-15

## 1. What Exists Today (Master)
[Document current capabilities]

## 2. What's New in Branch
[Novel ideas/implementations]

## 3. Dependencies
[Requirements]

## 4. Integration Complexity
- **Effort**: Low / Medium / High / Epic
- **Files affected**: <count>
- **Testing**: Unit / Integration / E2E
- **Breaking changes**: Yes / No
- **Migration**: Yes / No

## 5. Value Proposition
- **Problems solved**: [list]
- **User impact**: High / Medium / Low
- **Use cases**: [primary scenarios]

## 6. Risks
- **Technical**: [list]
- **Business**: [list]
- **Maintenance**: [list]

## 7. Recommendation
- [ ] Merge to v1.0
- [ ] Defer to v2.0
- [ ] Split v1+v2
- [ ] Archive

**Rationale**: [decision reasoning]

## 8. Integration Plan (if keep/merge)
[Step-by-step integration approach]
```
