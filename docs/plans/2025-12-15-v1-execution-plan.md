# PopKit v1.0 Execution Plan

**Date**: 2025-12-15
**Status**: Planning Phase
**Epic**: #240 (Branch Investigation & Integration Strategy)

---

## Executive Summary

Following the completion of Epic #240's investigation phase (12 branches analyzed), this document outlines the execution strategy for PopKit v1.0 marketplace launch. The plan prioritizes quick wins and high-value features identified during investigation.

**Total Timeline**: 4-6 weeks
**Parallel Work**: Quick wins + Documentation site

---

## v1.0 Goals

**Primary Goal**: Launch PopKit on Claude Code marketplace with:
1. Stable, performant plugin (no startup lag)
2. Professional documentation website
3. Clear value proposition visible to users
4. Windows compatibility (no Docker requirement)

**Success Metrics**:
- Plugin startup < 50ms (currently ~100-150ms)
- Documentation site live at `docs.popkit.dev`
- All quick wins implemented and tested
- v1.0.0 release published

---

## Feature Prioritization

### Priority Matrix (Effort vs Value)

```
High Value │ #251 Docs Site       │ #242 Native Async
           │ (2-3 weeks)          │ (1-2 weeks)
           │                      │
           ├──────────────────────┼───────────────────
           │ #245 Startup         │ #253 Batch Status
           │ (2-3 days)           │ (1-2 hours)
           │ #252 Commenting      │ #241 Complexity
Medium     │ (1-2 days)           │ (4-6 hours)
Value      │                      │
           └──────────────────────┴───────────────────
             Medium Effort          Low Effort
```

### Sequencing Strategy

**Phase 4A: Quick Wins** (Week 1-2)
- Execute in parallel where possible
- Build momentum with visible improvements
- Validate infrastructure for larger features

**Phase 4B: High-Value Features** (Week 3-6)
- Documentation site (can start in parallel with 4A)
- Native async mode (requires 4A validation)

---

## Phase 4A: Quick Wins (Week 1-2)

### Feature 1: PopKit Startup Optimization (#245)
**Priority**: P0-Critical
**Effort**: 2-3 days
**Value**: Fixes user-facing lag, enables smooth marketplace experience

**Implementation**:
```
Day 1: Lazy loading implementation
  - Defer tier-2 agent loading until needed
  - Move heavy imports to functions
  - Profile and identify bottlenecks

Day 2: Validation and testing
  - Benchmark startup time (target <50ms)
  - Test agent activation triggers
  - Verify no functionality breaks

Day 3: Documentation and polish
  - Update CLAUDE.md
  - Add performance notes to README
  - Create benchmark comparison
```

**Files Affected**:
- `packages/plugin/agents/config.json` (lazy loading config)
- `packages/plugin/hooks/session-start.py` (deferred initialization)
- `packages/plugin/hooks/utils/*.py` (import optimization)

**Success Criteria**:
- [ ] Startup time < 50ms (measured via benchmark)
- [ ] All agents still activate correctly
- [ ] No functionality regression

---

### Feature 2: Batch Spawning Status (#253)
**Priority**: P1-High (Quick Win)
**Effort**: 1-2 hours
**Value**: Better Power Mode transparency

**Implementation**:
```
Hour 1: Widget implementation
  - Add widget_batch_status() to statusline.py (+50 lines)
  - Add batch tracking to coordinator.py (+20 lines)
  - Update state schema (add batch_number field)

Hour 2: Testing and configuration
  - Test with Power Mode workflow
  - Update config.json to enable widget
  - Verify real-time updates
```

**Files Affected**:
- `packages/plugin/power-mode/statusline.py`
- `packages/plugin/power-mode/coordinator.py`
- `.claude/popkit/power-mode-state.json` (schema)

**Success Criteria**:
- [ ] Widget displays batch number and agent count
- [ ] Updates in real-time during Power Mode
- [ ] Works with both file-based and Redis modes

---

### Feature 3: Complexity Scoring (#241)
**Priority**: P2-Medium
**Effort**: 4-6 hours
**Value**: Cost transparency for users

**Implementation**:
```
Hour 1-2: Complexity calculator
  - Implement complexity_scorer.py
  - Define scoring rubric (LOC, files, dependencies)
  - Add model cost estimates

Hour 3-4: Integration
  - Add to /popkit:dev workflow
  - Display in issue list
  - Add to status line (optional)

Hour 5-6: Testing and calibration
  - Test against known issues
  - Calibrate scoring thresholds
  - Document methodology
```

**Files Affected**:
- `packages/plugin/hooks/utils/complexity_scorer.py` (new)
- `packages/plugin/commands/dev.md` (display scores)
- `packages/plugin/hooks/utils/issue_list.py` (integration)

**Success Criteria**:
- [ ] Complexity scores accurate for test issues
- [ ] Cost estimates within 20% of actual
- [ ] Displayed in /popkit:dev and /popkit:issue list

---

### Feature 4: Code Commenting Standards (#252)
**Priority**: P2-Medium
**Effort**: 1-2 days
**Value**: Internal quality improvement, foundation for v2.0 enforcement

**Implementation**:
```
Day 1: Standards adoption
  - Move COMMENTING-STANDARD.md to root
  - Update CLAUDE.md with reference
  - Team review and feedback

Day 2: Initial application
  - Apply to 3-5 recent files as examples
  - Create PR with commentary
  - Document learnings
```

**Files Affected**:
- `COMMENTING-STANDARD.md` (new, move from branch)
- `CLAUDE.md` (add section)
- Sample files (apply standards as examples)

**Success Criteria**:
- [ ] Standards document adopted
- [ ] CLAUDE.md updated
- [ ] 3-5 example files updated
- [ ] Team consensus achieved

---

## Phase 4B: High-Value Features (Week 3-6)

### Feature 5: Documentation Website (#251)
**Priority**: P1-High (Critical for Marketplace)
**Effort**: 2-3 weeks
**Value**: Professional presentation, user discovery, SEO

**Implementation Plan**:
```
Week 1: Foundation (MVP)
  - Set up Astro + Starlight
  - Migrate Getting Started from README
  - Create basic guides (issue-driven dev, workflows)
  - Deploy to Cloudflare Pages

Week 2: Auto-generation
  - Build sync-plugin-content.ts
  - Build sync-benchmarks.ts
  - Generate API reference pages (24 commands, 30 agents, 66 skills)
  - Validate auto-sync accuracy

Week 3: Visualization & Polish
  - Create BenchmarkChart.astro component
  - Add benchmark comparison pages
  - Configure search (Starlight built-in)
  - Set up custom domain (docs.popkit.dev)
  - GitHub Actions auto-deploy
```

**Files Created**:
- `packages/docs/` (new package, ~40 files)
- `.github/workflows/deploy-docs.yml`
- DNS configuration for subdomain

**Success Criteria**:
- [ ] Site live at docs.popkit.dev
- [ ] All 24 commands documented with auto-sync
- [ ] All 30 agents listed
- [ ] Benchmark charts showing 3x performance
- [ ] Search works across all content
- [ ] Lighthouse score >90

**Parallel Work**: Can start Week 1 in parallel with Phase 4A

---

### Feature 6: Native Async Power Mode (#242)
**Priority**: P1-High (Windows Compatibility)
**Effort**: 1-2 weeks
**Value**: Removes Docker requirement, 30% user base expansion

**Implementation Plan**:
```
Week 1: File-based coordinator enhancement
  - Implement atomic file operations
  - Add file locking mechanism
  - Create agent heartbeat system
  - Test on Windows, macOS, Linux

Week 2: Validation and fallback
  - Comprehensive testing with 2-6 agents
  - Performance benchmarking vs Redis
  - Auto-fallback from Redis to file-based
  - Documentation updates
```

**Files Affected**:
- `packages/plugin/power-mode/coordinator.py` (file ops)
- `packages/plugin/power-mode/statusline.py` (mode detection)
- `.claude/popkit/power-mode-state.json` (lock files)

**Success Criteria**:
- [ ] Works on Windows without Docker
- [ ] Supports 2-6 agents reliably
- [ ] Auto-detects and falls back from Redis
- [ ] Performance within 20% of Redis mode
- [ ] All existing workflows compatible

**Dependencies**: Requires Phase 4A startup optimization complete

---

## Implementation Sequence

### Week 1: Quick Wins + Docs Foundation
**Parallel Tracks**:
- Track A: #245 Startup Optimization (2-3 days) → #253 Batch Status (1-2 hours) → #241 Complexity (4-6 hours)
- Track B: #251 Docs Site Week 1 (foundation)
- Track C: #252 Commenting Standards (1-2 days)

**Deliverables**:
- ✅ Startup < 50ms
- ✅ Batch status widget live
- ✅ Complexity scoring working
- ✅ Commenting standards adopted
- ✅ Docs site MVP deployed

---

### Week 2: Docs Auto-generation + Planning
**Parallel Tracks**:
- Track A: #251 Docs Site Week 2 (auto-generation scripts)
- Track B: Native Async planning and design

**Deliverables**:
- ✅ API reference auto-generated
- ✅ Benchmark data synced
- ✅ Native Async design validated

---

### Week 3-4: Native Async + Docs Polish
**Parallel Tracks**:
- Track A: #242 Native Async implementation and testing
- Track B: #251 Docs Site Week 3 (visualization, polish)

**Deliverables**:
- ✅ Native Async working on Windows
- ✅ Docs site complete with search
- ✅ Custom domain configured

---

### Week 5-6: Testing, Polish, Release
**Sequential Work**:
1. Comprehensive testing of all v1.0 features
2. Performance benchmarking
3. Documentation review and updates
4. CHANGELOG.md preparation
5. v1.0.0 release

**Deliverables**:
- ✅ All features tested
- ✅ Performance benchmarks updated
- ✅ CHANGELOG.md complete
- ✅ v1.0.0 released

---

## Risk Mitigation

| Risk | Severity | Mitigation |
|------|----------|------------|
| Startup optimization breaks functionality | High | Comprehensive testing, feature flags for lazy loading |
| Docs site build time grows | Medium | Astro's fast build, incremental generation |
| Native Async race conditions on Windows | High | Atomic file operations, extensive Windows testing |
| Timeline slippage | Medium | Quick wins can ship independently, docs can be v1.1 |
| Scope creep | Medium | Strict adherence to plan, defer new ideas to v2.0 |

---

## Testing Strategy

### Quick Wins (Phase 4A)
- **Unit Tests**: Complexity scorer, batch tracking
- **Integration Tests**: Startup performance, widget display
- **Manual Testing**: Power Mode workflows, issue workflows

### High-Value Features (Phase 4B)
- **Docs Site**:
  - Build validation
  - Link checker
  - Lighthouse audits
  - Cross-browser testing
- **Native Async**:
  - Windows/macOS/Linux testing
  - Race condition testing
  - Performance benchmarking
  - Fallback testing

---

## v1.0 Release Checklist

### Code Quality
- [ ] All quick wins implemented and tested
- [ ] Documentation site live and validated
- [ ] Native Async working on Windows
- [ ] No performance regressions
- [ ] All benchmarks passing

### Documentation
- [ ] CLAUDE.md updated with new features
- [ ] README.md refreshed
- [ ] CHANGELOG.md v1.0.0 section complete
- [ ] Docs site comprehensive and accurate

### Marketplace Readiness
- [ ] plugin.json version updated to 1.0.0
- [ ] marketplace.json updated
- [ ] All assets (screenshots, videos) prepared
- [ ] Pricing tiers documented (if applicable)

### Testing
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Manual testing complete on Windows/macOS/Linux
- [ ] Performance benchmarks meet targets

### Release Process
- [ ] Create v1.0.0 git tag
- [ ] Publish to public repo (jrc1883/popkit-claude)
- [ ] Create GitHub release with notes
- [ ] Update Claude Code marketplace
- [ ] Announce on social/community channels

---

## Post-v1.0 (v1.1 Candidates)

**Conditional Merges**:
- #248 Terminal Helper Text (if color support confirmed)

**Low Priority**:
- Additional benchmark visualizations
- More doc site content (case studies, tutorials)
- Community-requested features

---

## v2.0 Planning (Deferred)

The following features are explicitly deferred to v2.0:
- #243 Cross-Platform CLI (4-6 months)
- #244 Skill Structure enhancements
- #241 Full Model Dispatch with analytics
- #242 Upstash Workflow integration
- #247 Slack Notifications
- #249 Vibe Engineering
- #253 Batch Spawning Phase 2-3 (notification hooks, coordinator)
- #252 Code Commenting Enforcement (pre-commit, GitHub Actions)

**v2.0 Kick-off**: Q1 2026 after v1.0 marketplace validation

---

## Success Metrics

### Technical Metrics
- Startup time: <50ms (currently ~100-150ms)
- Docs site Lighthouse score: >90
- Native Async performance: Within 20% of Redis
- Test coverage: >80% for new code

### User Metrics
- Marketplace install rate
- User retention after 7 days
- Documentation site traffic
- Issue/PR velocity

### Business Metrics
- Marketplace approval status
- User feedback sentiment
- Premium tier conversion (if applicable)

---

## Timeline Summary

```
Week 1-2: Quick Wins + Docs Foundation
  ├── #245 Startup Optimization ✅
  ├── #253 Batch Status ✅
  ├── #241 Complexity Scoring ✅
  ├── #252 Commenting Standards ✅
  └── #251 Docs Site (Week 1) ✅

Week 3-4: Native Async + Docs Auto-gen
  ├── #242 Native Async ✅
  └── #251 Docs Site (Week 2-3) ✅

Week 5-6: Polish + Release
  ├── Testing ✅
  ├── Documentation ✅
  └── v1.0.0 Release ✅
```

**Total**: 4-6 weeks to v1.0.0 release

---

## Next Steps (Immediate)

1. **This Week**:
   - Begin #245 Startup Optimization
   - Set up #251 Docs Site infrastructure
   - Adopt #252 Commenting Standards

2. **Create Implementation Issues**:
   - One issue per feature with detailed checklist
   - Link to Epic #240 and this execution plan
   - Assign to v1.0.0 milestone

3. **Update Project Board**:
   - Move features from "Investigation" to "Ready for Dev"
   - Set up v1.0 project board with phases

4. **Kick-off**:
   - Review this plan with team (if applicable)
   - Confirm timeline and resource allocation
   - Begin implementation

---

**Document Status**: Execution Plan Complete
**Ready for**: Implementation Kick-off
**Next**: Create implementation issues for each feature
