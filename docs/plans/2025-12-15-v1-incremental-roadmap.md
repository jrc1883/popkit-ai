# PopKit v1.0 Incremental Roadmap

**Current Version**: 0.2.4
**Target**: 1.0.0 (Marketplace Launch)
**Strategy**: Incremental releases every 1-2 weeks
**Timeline**: 8-10 weeks total

---

## Release Philosophy

Each minor version (0.3, 0.4, etc.) represents a **shippable increment** with:
- Clear, focused scope
- Fully tested features
- Updated documentation
- Changelog entry
- Git tag and GitHub release

This allows us to:
- Ship value continuously
- Get early feedback
- Reduce risk of big-bang release
- Maintain velocity
- Celebrate wins along the way

---

## Version Roadmap

### 0.3.0 - Performance & Quick Wins (Week 1-2)
**Theme**: Fast, visible improvements
**Timeline**: 1-2 weeks
**Scope**: Critical performance + UX transparency

**Features**:
- ✅ **#245 PopKit Startup Optimization** (P0-Critical)
  - Lazy loading of tier-2 agents
  - Import optimization
  - Target: <50ms startup (from ~100-150ms)
  - Files: `hooks/session-start.py`, `agents/config.json`

- ✅ **#253 Batch Spawning Status** (P1-High, Quick Win)
  - Status line widget for Power Mode
  - Display batch number and agent names
  - Real-time updates
  - Files: `power-mode/statusline.py`, `coordinator.py`

**Success Criteria**:
- [ ] Startup time <50ms (benchmarked)
- [ ] Batch widget displays correctly in Power Mode
- [ ] No functionality regressions
- [ ] Performance benchmarks updated

**Release Notes**:
```markdown
## 0.3.0 - Performance & Transparency

### Performance
- **Startup Optimization**: Plugin now loads in <50ms (66% faster)
- Lazy loading for tier-2 agents improves responsiveness

### Power Mode
- **Batch Status Widget**: Real-time visibility into spawned agents
- Display: `Batch:2 Agents:4 | Code Explorers | #45 Phase 3/7`

### Benchmarks
- Startup: 150ms → 45ms (-70%)
- Power Mode transparency: Batch/agent info now visible
```

---

### 0.4.0 - Cost Transparency & Standards (Week 2-3)
**Theme**: User empowerment & quality foundations
**Timeline**: 1 week
**Scope**: Cost visibility + internal quality

**Features**:
- ✅ **#241 Complexity Scoring** (P2-Medium)
  - Display issue complexity before starting work
  - Estimate model costs (tokens, time)
  - Integration: `/popkit:dev`, `/popkit:issue list`
  - Files: `hooks/utils/complexity_scorer.py`, `commands/dev.md`

- ✅ **#252 Code Commenting Standards** (P2-Medium)
  - Adopt `COMMENTING-STANDARD.md`
  - Apply to 3-5 sample files
  - Update CLAUDE.md with reference
  - Foundation for v2.0 enforcement tooling

**Success Criteria**:
- [ ] Complexity scores displayed in issue workflows
- [ ] Cost estimates within 20% accuracy
- [ ] Commenting standards adopted and documented
- [ ] Sample files updated with standards

**Release Notes**:
```markdown
## 0.4.0 - Transparency & Quality

### Cost Transparency
- **Complexity Scoring**: See estimated effort before starting work
- Display in `/popkit:dev work #N` and `/popkit:issue list`
- Accuracy: Within 20% of actual token usage

### Code Quality
- **Commenting Standards**: Three-tier verbosity system adopted
- Standards: Sparse (TypeScript), Moderate (Python), Verbose (Complex)
- Sample implementations in `packages/plugin/hooks/utils/`
```

---

### 0.5.0 - Documentation Site Foundation (Week 3-4)
**Theme**: Professional presentation
**Timeline**: 2 weeks
**Scope**: Docs site MVP + core content

**Features**:
- ✅ **#251 Documentation Website - Phase 1** (P1-High)
  - Astro + Starlight setup
  - Domain: `docs.popkit.dev`
  - Core pages: Getting Started, Guides, Architecture
  - Cloudflare Pages deployment
  - GitHub Actions auto-deploy
  - Files: `packages/docs/` (new package)

**Content Created**:
- Index / Landing page
- Getting Started (Installation, Quick Start)
- Guides (Issue-driven dev, Feature workflow, Power Mode)
- Architecture overview
- Basic search (Starlight built-in)

**Success Criteria**:
- [ ] Site live at docs.popkit.dev
- [ ] Core getting started content complete
- [ ] GitHub Actions deploying on push
- [ ] Lighthouse score >90
- [ ] Search functional

**Release Notes**:
```markdown
## 0.5.0 - Documentation Foundation

### Documentation Website
- **Live Site**: https://docs.popkit.dev
- Astro + Starlight framework
- Auto-deployment via GitHub Actions
- Core content: Getting Started, Guides, Architecture

### Search
- Full-text search across all documentation
- Keyboard shortcuts (Ctrl+K / Cmd+K)

### Performance
- Lighthouse score: 95+
- Page load: <2s
```

---

### 0.6.0 - API Reference & Benchmarks (Week 4-5)
**Theme**: Comprehensive documentation
**Timeline**: 1-2 weeks
**Scope**: Auto-generated API docs + visualizations

**Features**:
- ✅ **#251 Documentation Website - Phase 2** (P1-High)
  - Auto-generated API reference (24 commands, 30 agents, 66 skills)
  - Benchmark visualization with charts
  - Case studies and examples
  - Advanced guides
  - Files: `packages/docs/src/scripts/sync-*.ts`, `components/*.astro`

**Auto-Generation**:
- Command reference from `packages/plugin/commands/*.md`
- Agent catalog from `packages/plugin/agents/config.json`
- Skill documentation from `packages/plugin/skills/*/SKILL.md`
- Benchmark data from `packages/benchmarks/results/`

**Visualizations**:
- Benchmark charts (Chart.js integration)
- Performance comparisons (baseline vs PopKit)
- Agent workflow diagrams

**Success Criteria**:
- [ ] All 24 commands documented with auto-sync
- [ ] All 30 agents listed with descriptions
- [ ] All 66 skills cataloged
- [ ] Benchmark charts showing 3x performance improvement
- [ ] Auto-sync scripts validated

**Release Notes**:
```markdown
## 0.6.0 - Complete API Reference

### API Documentation
- **24 Commands**: Full reference with examples
- **30 Agents**: Descriptions, triggers, use cases
- **66 Skills**: Comprehensive catalog
- Auto-synced from source (never stale)

### Benchmarks
- **Performance Charts**: Visual proof of 3x improvement
- Baseline vs PopKit comparisons
- Methodology documentation

### Advanced Content
- Case studies from real workflows
- Multi-agent orchestration guides
- Power Mode deep dive
```

---

### 0.7.0 - Native Async Power Mode (Week 5-6)
**Theme**: Windows compatibility
**Timeline**: 1-2 weeks
**Scope**: File-based Power Mode coordination

**Features**:
- ✅ **#242 Native Async Power Mode** (P1-High)
  - File-based coordination (no Docker required)
  - Windows/macOS/Linux compatibility
  - Auto-fallback from Redis to file-based
  - Support 2-6 agents reliably
  - Files: `power-mode/coordinator.py`, `statusline.py`

**Implementation**:
- Atomic file operations
- File locking mechanism
- Agent heartbeat system
- Cross-platform testing

**Success Criteria**:
- [ ] Works on Windows without Docker
- [ ] Performance within 20% of Redis mode
- [ ] Supports 2-6 agents reliably
- [ ] Auto-detection and fallback
- [ ] All existing workflows compatible

**Release Notes**:
```markdown
## 0.7.0 - Windows Power Mode

### Power Mode Enhancement
- **Native Async**: No Docker required on Windows
- File-based coordination for 2-6 agents
- Auto-fallback from Redis when unavailable
- Cross-platform: Windows, macOS, Linux

### Performance
- File-based mode: Within 20% of Redis performance
- Tested with 6 parallel agents
- Atomic operations prevent race conditions

### Compatibility
- Existing Redis workflows unchanged
- Automatic mode detection
- Seamless transition between modes
```

---

### 0.8.0 - Polish & Integration (Week 6-7)
**Theme**: Refinement & testing
**Timeline**: 1 week
**Scope**: Bug fixes, edge cases, final integrations

**Features**:
- ✅ Integration testing across all v1.0 features
- ✅ Performance regression testing
- ✅ Documentation review and polish
- ✅ CLAUDE.md comprehensive update
- ✅ README.md refresh
- ✅ Edge case handling

**Conditional Features**:
- ⚠️ **#248 Terminal Helper Text** (if color support confirmed)
  - Enhanced terminal output formatting
  - Color-coded status messages
  - Conditional on terminal capability detection

**Testing Focus**:
- Cross-platform validation (Windows, macOS, Linux)
- Power Mode stress testing (2-6 agents)
- Documentation accuracy verification
- Link checking across docs site
- Performance benchmarks validation

**Success Criteria**:
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Manual testing complete on all platforms
- [ ] Documentation comprehensive and accurate
- [ ] No known P0/P1 bugs
- [ ] Performance benchmarks meet targets

**Release Notes**:
```markdown
## 0.8.0 - Polish & Refinement

### Quality
- Comprehensive cross-platform testing
- Edge case handling improvements
- Performance regression suite

### Documentation
- CLAUDE.md fully updated
- README refreshed
- All links validated

### Bug Fixes
- (List specific fixes from testing)
```

---

### 0.9.0 - Release Candidate (Week 7-8)
**Theme**: Final validation
**Timeline**: 1 week
**Scope**: Release preparation & validation

**Features**:
- ✅ Final performance benchmarking
- ✅ CHANGELOG.md complete for v1.0
- ✅ Marketplace assets prepared (screenshots, videos)
- ✅ Public repo (`jrc1883/popkit-claude`) sync
- ✅ Community testing / beta release

**Preparation**:
- Release notes draft
- Version bumps coordinated
- Migration guide (if needed)
- Known issues documented

**Beta Testing**:
- Invite community testers
- Gather feedback
- Fix critical issues
- Validate marketplace readiness

**Success Criteria**:
- [ ] All v1.0 features validated
- [ ] No P0 bugs remaining
- [ ] Performance targets met
- [ ] Documentation complete
- [ ] Marketplace assets ready
- [ ] Public repo synced

**Release Notes**:
```markdown
## 0.9.0 - Release Candidate

### Status
- **Release Candidate**: Final testing before 1.0
- All v1.0 features implemented and validated
- Community testing in progress

### What's Coming in 1.0
- Marketplace launch
- Professional documentation
- Windows Power Mode support
- Enhanced performance and transparency

### Known Issues
- (Document any remaining non-critical issues)
```

---

### 1.0.0 - Marketplace Launch (Week 8-10)
**Theme**: Official release
**Timeline**: Launch day
**Scope**: Public marketplace availability

**Final Steps**:
- ✅ Address RC feedback
- ✅ Final version bumps (`plugin.json`, `marketplace.json`)
- ✅ Create v1.0.0 git tag
- ✅ GitHub release with comprehensive notes
- ✅ Marketplace submission
- ✅ Public announcement

**1.0.0 Deliverables**:
- Plugin startup <50ms
- Documentation site at docs.popkit.dev
- Native async Power Mode (Windows compatible)
- Complexity scoring and cost transparency
- Batch status visibility
- Comprehensive API reference (24 commands, 30 agents, 66 skills)
- Benchmark proof (3x performance)

**Success Criteria**:
- [ ] Marketplace approval
- [ ] Documentation site live and comprehensive
- [ ] All performance targets met
- [ ] Zero known P0/P1 bugs
- [ ] Community feedback positive

**Release Notes**:
```markdown
## 1.0.0 - Marketplace Launch 🎉

### Major Features

**Performance**
- Startup time <50ms (66% improvement)
- 3x faster development workflows (benchmarked)

**Power Mode**
- Native async coordination (no Docker on Windows)
- Batch status transparency
- 2-6 parallel agents supported

**Documentation**
- Professional site: https://docs.popkit.dev
- Auto-generated API reference
- Comprehensive guides and tutorials
- Benchmark visualizations

**Cost Transparency**
- Complexity scoring before starting work
- Token usage estimates
- Informed decision-making

### Breaking Changes
- None (fully backward compatible from 0.2.x)

### Migration Guide
- No migration needed
- Existing workflows continue to work
- New features opt-in

### What's Next (v2.0)
- Cross-platform CLI
- Multi-model support (GPT, Gemini)
- Advanced orchestration
- Enhanced tooling

---

**Thank you** to all contributors and testers!

🤖 Generated with Claude Code
```

---

## Milestone Management

### Creating Milestones

```bash
# Create missing milestones
gh api repos/jrc1883/popkit/milestones -f title="0.4.0" -f description="Cost Transparency & Standards"
gh api repos/jrc1883/popkit/milestones -f title="0.5.0" -f description="Documentation Site Foundation"
gh api repos/jrc1883/popkit/milestones -f title="0.6.0" -f description="API Reference & Benchmarks"
gh api repos/jrc1883/popkit/milestones -f title="0.7.0" -f description="Native Async Power Mode"
gh api repos/jrc1883/popkit/milestones -f title="0.8.0" -f description="Polish & Integration"
gh api repos/jrc1883/popkit/milestones -f title="0.9.0" -f description="Release Candidate"
```

### Mapping Issues to Milestones

```bash
# 0.3.0 - Performance & Quick Wins
gh api repos/jrc1883/popkit/issues/245 -X PATCH -f milestone=<milestone_number>  # Startup
gh api repos/jrc1883/popkit/issues/253 -X PATCH -f milestone=<milestone_number>  # Batch Status

# 0.4.0 - Cost Transparency & Standards
gh api repos/jrc1883/popkit/issues/241 -X PATCH -f milestone=<milestone_number>  # Complexity
gh api repos/jrc1883/popkit/issues/252 -X PATCH -f milestone=<milestone_number>  # Commenting

# 0.5.0 + 0.6.0 - Documentation Site
gh api repos/jrc1883/popkit/issues/251 -X PATCH -f milestone=<milestone_number>  # Docs Site

# 0.7.0 - Native Async
gh api repos/jrc1883/popkit/issues/242 -X PATCH -f milestone=<milestone_number>  # Async

# 0.8.0 - Polish
gh api repos/jrc1833/popkit/issues/248 -X PATCH -f milestone=<milestone_number>  # Terminal (conditional)
```

---

## Project Board Structure

**Project**: PopKit Development

**Columns**:
1. **Backlog** - All investigated features (from Epic #240)
2. **0.3.0 - Performance** - Ready for immediate implementation
3. **0.4.0 - Transparency** - Next sprint
4. **0.5.0 - Docs Foundation** - Following sprint
5. **0.6.0 - Docs Complete** - Auto-generation
6. **0.7.0 - Native Async** - Windows compatibility
7. **0.8.0 - Polish** - Testing & refinement
8. **0.9.0 - RC** - Final validation
9. **Done** - Completed features

**View Types**:
- **Board View**: Kanban with milestone columns
- **Table View**: Sortable by priority, milestone, assignee
- **Roadmap View**: Timeline visualization

---

## Release Process (for each version)

### Pre-Release Checklist
- [ ] All milestone issues closed
- [ ] Tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md entry added
- [ ] Version bumped in `plugin.json` and `marketplace.json`

### Release Steps
1. Create git tag: `git tag -a v0.X.0 -m "Release 0.X.0"`
2. Push tag: `git push origin v0.X.0`
3. Create GitHub release: `gh release create v0.X.0 --notes-file release-notes.md`
4. Update plugin: `/plugin update popkit@popkit-marketplace`
5. Announce in community channels (if significant)

### Post-Release
- [ ] Close milestone
- [ ] Create next milestone if needed
- [ ] Move project board cards
- [ ] Gather feedback
- [ ] Plan next version

---

## Version Timeline Summary

```
Week 1-2:   0.3.0 ✅ Performance & Quick Wins
Week 2-3:   0.4.0 ✅ Cost Transparency & Standards
Week 3-4:   0.5.0 ✅ Documentation Foundation
Week 4-5:   0.6.0 ✅ API Reference & Benchmarks
Week 5-6:   0.7.0 ✅ Native Async Power Mode
Week 6-7:   0.8.0 ✅ Polish & Integration
Week 7-8:   0.9.0 ✅ Release Candidate
Week 8-10:  1.0.0 🎉 Marketplace Launch
```

**Total**: 8-10 weeks from 0.2.4 to 1.0.0

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Scope creep between versions | Strict milestone boundaries, defer to next version |
| Timeline slippage | Each version can ship independently, adjust later milestones |
| Breaking changes | Maintain backward compatibility, test against existing workflows |
| Documentation lag | Update docs incrementally with each version |
| Testing debt | 0.8.0 dedicated to quality, continuous testing throughout |

---

## Success Metrics (per version)

### Technical
- All tests passing
- Performance benchmarks met (if applicable)
- No regression in existing features

### User Experience
- Changelog clear and accurate
- Documentation up to date
- Smooth upgrade path

### Process
- Released on schedule (±3 days)
- All issues closed in milestone
- Feedback loop active

---

## Next Steps

1. **Immediate** (This Week):
   - Create missing GitHub milestones (0.4-0.9)
   - Map existing issues to milestones
   - Set up project board columns
   - Begin 0.3.0 implementation (#245 Startup)

2. **Week 2**:
   - Complete 0.3.0
   - Tag and release 0.3.0
   - Begin 0.4.0

3. **Ongoing**:
   - Update project board weekly
   - Review milestone progress
   - Adjust timeline as needed
   - Celebrate each release!

---

**Document Status**: Incremental Roadmap Complete
**Ready for**: Milestone creation and issue mapping
**Next**: Execute milestone setup and begin 0.3.0 implementation
