# XML System Epic: Executive Summary

**Date**: December 30, 2025
**Status**: Scoped & Ready for Implementation
**Target Start**: Week of January 6, 2026

---

## The Opportunity

PopKit has a critical architectural gap: it uses **flat JSON for all inter-component communication**, which forces Claude to infer relationships, priorities, and severity levels from unstructured text. This causes:

1. **Agent Routing Accuracy ~80%** when optimal is 95%+
2. **Context Loss in Multi-Agent Workflows** - agents don't understand which discoveries are critical
3. **Hook False Positives/Negatives** - can't distinguish security blocks from feature-gate blocks
4. **Error Recovery Failures** - workflows abort instead of retrying with smart recovery
5. **Power Mode Coordination Issues** - agents don't know task priorities/dependencies

XML fixes these issues by making **semantic intent explicit through structured tags** instead of implicit in plain text.

---

## Why This Matters

**PopKit's core value proposition is intelligent orchestration.** XML enables PopKit to orchestrate more intelligently by:

| Problem | Current | With XML | Impact |
|---------|---------|----------|--------|
| **Agent Routing** | 80% accuracy | 95%+ accuracy | Faster problem resolution |
| **Hook Decisions** | Ambiguous | Clear severity levels | Fewer false positives |
| **Multi-Agent Context** | Lost between agents | Preserved with priorities | Shorter code review cycles |
| **Error Recovery** | Workflows abort | Smart recovery options | Higher success rates |
| **User Understanding** | Implicit intent | Explicit XML structure | Better agent routing |

---

## The Plan: 5 Phases

### Phase 1: Hook XML Integration (1-2 days)
- Add optional `_xml_metadata` field to hook responses
- Distinguish security blocks from feature gates
- **Foundation** for all subsequent phases
- Low risk (backward compatible)

### Phase 2: Power Mode XML Protocol (2 sprints)
- Add priority/urgency to agent messages
- Enable dependency tracking between tasks
- Improve multi-agent coordination
- Medium risk (coordinator changes)

### Phase 3: Agent XML Communication (2-3 sprints)
- Mark severity on agent discoveries
- Preserve context through agent chains
- Improve routing accuracy
- Medium risk (affects 36 agents)

### Phase 4: User-Facing XML Templates (1 sprint)
- Debugging, feature request, code review, optimization templates
- Improve user routing accuracy by 15-20%
- Low risk (documentation only)

### Phase 5: Context Tracking System (1-2 sprints)
- Track context changes between sessions
- Generate XML diffs
- Foundation for advanced features
- Low risk (builds on existing code)

---

## What Already Exists

These components are **ready to use immediately** from prior development work:

| Component | Status | File | Use Case |
|-----------|--------|------|----------|
| **XML Generator Library** | Ready | `packages/shared-py/popkit_shared/utils/xml_generator.py` | Generate structured XML from Python |
| **Problem XML Generation** | Ready | `xml_generator.generate_problem_xml()` | Structure user problems with category, severity, workflow |
| **Project Context XML** | Ready | `xml_generator.generate_project_context_xml()` | Capture stack, infrastructure, current work |
| **Findings XML** | Ready | `xml_generator.generate_findings_xml()` | Tool results, issues, suggestions, recommendations |
| **XML Test Suite** | Ready | `test_xml_parsing.py`, `test_findings_xml.py` | Parsing, agent routing, structure validation |
| **Research & Design** | Complete | `docs/research/2025-12-16-xml-usage-research.md` | 1070-line comprehensive analysis |

**This is not theoretical.** Core XML generation code already exists and has been tested.

---

## Success Metrics

| Target | Metric | Current | Goal | Timeline |
|--------|--------|---------|------|----------|
| **Agent Routing** | Accuracy | ~80% | 95%+ | Phase 3 (Week 7-9) |
| **Hook Decisions** | Quality | Unknown | 95%+ | Phase 1 (Week 1) |
| **Power Mode** | Task completion | ~70% | 90%+ | Phase 2 (Week 3-4) |
| **Code Review** | Cycle time | Baseline | -20% | Phase 3 (Week 7-9) |
| **User Satisfaction** | Error clarity | Unknown | >85% | Phase 4 (Week 8) |

**Measurement approach**: Baseline metrics before Phase 1, validate improvements at each phase completion.

---

## Key Design Decisions

### 1. Backward Compatibility First
- XML is **added metadata**, not replacement for JSON
- All existing code continues working unchanged
- Gradual rollout possible without breaking changes

### 2. Internal Use + User-Facing
- **Internal**: Hooks, Power Mode, agents use XML automatically
- **User-Facing**: Templates are optional but recommended
- Mixed JSON/XML allows transition period

### 3. Build on Proven Code
- Use existing `xml_generator.py` (already tested)
- Reuse existing test suite
- Research document provides complete design
- No need for prototype or exploratory phase

### 4. Start with Lowest-Risk Phase
- Phase 1 (Hooks) is purely additive
- No coordinator changes, no agent updates needed
- Can ship independently in 1-2 days
- Builds confidence for harder phases

---

## Quick Wins (Can Ship This Week)

These can be completed independently while planning Phase 1:

1. **XML Generator Library Enhancement** (2-4 hours)
   - Polish and document `xml_generator.py`
   - Publish as official utility in `shared-py`
   - Unblocks other teams

2. **Hook Protocol Documentation** (4-6 hours)
   - Create `packages/plugin/hooks/XML-PROTOCOL.md`
   - Document backward compatibility
   - Design already complete

3. **XML Test Suite** (1 day)
   - Generalize and expand existing tests
   - Create comprehensive validation suite
   - Prevent regressions

4. **Agent Routing Baseline** (1-2 days)
   - Establish current routing accuracy (~80%)
   - Document baseline for Phase 3
   - Enables success metrics

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Backward Compatibility** | Medium | All changes maintain JSON; XML is additional metadata |
| **Agent Definition Updates** | Medium | Gradual migration; new agents use XML, old get wrapper layer |
| **Performance Impact** | Low | XML parsing has <5% overhead; Phase 2 benchmarking validates |
| **User Adoption** | Low | Start optional; templates make XML easy to use |
| **Complexity** | Medium | Design already complete; focus on implementation |

**Risk Profile**: Overall LOW-MEDIUM for all 5 phases combined. No single phase is high-risk.

---

## Implementation Timeline

### Week 1: Foundation (Phase 1 Start)
- Quick Wins #1-2 (Hook documentation, XML library)
- Phase 1 implementation begins
- Test suite established

### Weeks 2-3: Hooks + Power Mode Planning
- Phase 1 completion and merge
- Early Phase 2 design review
- Routing baseline measurement

### Weeks 3-4: Power Mode
- Phase 2 implementation
- Coordinator updates
- Integration testing

### Weeks 5-7: Agent Communication
- Routing accuracy baseline established
- Phase 3 implementation
- 36 agent definitions updated
- Output styles migrated

### Week 8: User-Facing Features
- Phase 4 (XML user guide)
- Templates and documentation
- User feedback collection

### Weeks 9+: Polish & Enhancement
- Phase 5 (context tracking)
- Performance optimization
- Production deployment

**Total Timeline**: ~12 weeks from start to full rollout

---

## Why Now?

1. **Research Complete**: 1070-line analysis document finished (Dec 16)
2. **Code Ready**: XML generator and tests already written
3. **Design Proven**: All 5 phases designed, dependencies mapped
4. **Problem Clear**: Undiagnosed issues identified in research
5. **Team Alignment**: All 5 issues linked to parent epic #220

**There is no blocker to starting Phase 1 this week.**

---

## Next Steps

### Immediate (This Week)
1. Review this roadmap with team
2. Identify Phase 1 lead and Phase 2-3 leads
3. Schedule Phase 1 kickoff planning meeting
4. Create GitHub issues for Quick Wins

### Short Term (Week of Jan 6)
1. Phase 1 kickoff
2. Complete Quick Wins #1-2
3. Begin hook XML generation implementation
4. Set up metrics tracking

### Medium Term (Weeks 2-4)
1. Phase 1 completion and merge
2. Phase 2 implementation begins
3. Routing accuracy baseline established

---

## Success Definition

**This epic succeeds when:**

1. ✅ Phase 1: All hooks output XML, 895 tests passing
2. ✅ Phase 2: Power Mode messages prioritized, 90%+ task completion
3. ✅ Phase 3: All agents support XML, routing accuracy 95%+
4. ✅ Phase 4: XML guide published, >85% user satisfaction
5. ✅ Phase 5: Context tracking working, delta computation accurate
6. ✅ **Overall**: Code review cycle time reduced 20%, context loss eliminated

---

## Resources

### Documentation
- **Complete Roadmap**: `docs/plans/2025-12-30-xml-system-epic-roadmap.md` (this repo)
- **Research & Analysis**: `docs/research/2025-12-16-xml-usage-research.md` (1070 lines)
- **Phase Issues**: #627, #215, #217, #218, #219 (all linked to #220)

### Existing Code
- **XML Generator**: `packages/shared-py/popkit_shared/utils/xml_generator.py`
- **Tests**: `packages/popkit-core/hooks/test_xml_parsing.py`, `test_findings_xml.py`
- **Hook Examples**: 23 Python hook files ready for updates

---

**Recommendation**: Start with Phase 1 immediately. It's low-risk, high-value, and unblocks the entire system. Week 1 kickoff is feasible.

