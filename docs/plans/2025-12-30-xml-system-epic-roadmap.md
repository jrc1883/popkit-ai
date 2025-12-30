# XML System Epic: Context Preservation & Structured Communication

**Status**: Scoped & Ready for Implementation
**Last Updated**: December 30, 2025
**Epic Maintainer**: jrc1883
**Related Issues**: #627, #215, #217, #218, #219, #220 (parent epic)

---

## Vision

PopKit will implement a unified XML-based communication system that fundamentally improves Claude's understanding of context, priorities, and relationships across all architectural layers. XML enables PopKit to:

1. **Preserve semantic intent** through structured tags instead of plain text
2. **Mark severity levels** so critical findings aren't buried among informational discoveries
3. **Enable multi-agent coordination** with explicit task dependencies and priorities
4. **Provide structured error recovery** with categorized blocks and guided recovery paths
5. **Support user-facing XML templates** that improve agent routing accuracy by 15-20%

**Expected Impact**:
- Agent routing accuracy: 80% → 95%+
- Hook decision quality: Unknown → 95%+ correct
- Multi-agent task completion: ~70% → ~90%
- Code review cycle time: -20% improvement
- User error satisfaction: >85%

---

## Current State

PopKit is a **JSON/YAML/Markdown-first system** with zero active XML usage:

- **Hook Communication**: Flat JSON (no severity levels, ambiguous blocks)
- **Power Mode Messages**: Python dataclasses serialized to JSON (no priority/urgency metadata)
- **Agent Handoffs**: JSON schemas treating all discoveries equally
- **User Input**: Plain text prompts with ambiguous structure
- **Error Handling**: Unstructured blocks without recovery guidance

### Existing XML Foundations

These already exist from prior development work and can be leveraged:

| Component | File | Status | Note |
|-----------|------|--------|------|
| **XML Generator** | `packages/shared-py/popkit_shared/utils/xml_generator.py` | Ready | Generates problem/project/findings XML |
| **Problem XML** | `xml_generator.generate_problem_xml()` | Ready | Infers category, severity, workflow |
| **Project Context XML** | `xml_generator.generate_project_context_xml()` | Ready | Structures stack, infrastructure, work |
| **Findings XML** | `xml_generator.generate_findings_xml()` | Ready | Tool results, issues, suggestions |
| **XML Tests** | `packages/popkit-core/hooks/test_xml_parsing.py` | Ready | Parsing and agent routing tests |
| **Findings Tests** | `packages/popkit-core/hooks/test_findings_xml.py` | Ready | XML generation validation |
| **Research Doc** | `docs/research/2025-12-16-xml-usage-research.md` | Complete | Comprehensive analysis (1070 lines) |

### Undiagnosed Issues Caused by Ambiguous Structure

The research document identified 5 classes of problems likely caused by lack of XML:

1. **Agent Routing Accuracy**: Multi-keyword prompts produce ambiguous routing (36+ agents competing for same keywords)
2. **Hook False Positives/Negatives**: Can't distinguish severity levels (security block vs. feature-gate block)
3. **Multi-Agent Context Loss**: Later agents revisit code patterns, missing connected issues
4. **Error Recovery Failures**: Workflows abort instead of retry/backoff with smart recovery
5. **Power Mode Coordination**: Agents don't coordinate effectively under constraints

---

## Proposed Phases

### Phase 1: Hook XML Integration (Effort: 1-2 days)

**Goal**: Add XML metadata to hook responses for improved routing and severity distinction

**Issues**: #219
**Priority**: P1-high (Foundation for all subsequent phases)
**Risk**: Low (backward compatible)

**Deliverables**:
- Add `_xml_metadata` field to all hook JSON responses
- Update 23 hook Python files to generate XML responses
- Create `packages/plugin/hooks/XML-PROTOCOL.md` documentation
- Extend `message_builder.py` with XML builder functions
- Add comprehensive tests for XML validation

**Key Components**:

1. **Backward Compatibility**
   - Hooks output standard JSON (unchanged)
   - XML added as optional `_xml_metadata` field
   - Existing code ignores new field

2. **XML Hook Response Standard**
   ```xml
   <hook-response>
     <action>block|continue</action>

     <!-- For blocks -->
     <block type="security|feature-gate|rate-limit|context">
       <severity>critical|high|medium|low</severity>
       <description>Human-readable message</description>
       <reason type="policy|entitlement|resource|boundary">
         Technical reason for the block
       </reason>
       <recovery>
         <suggestion priority="1" type="action">Suggested action</suggestion>
         <suggestion priority="2" type="information">Alternative approach</suggestion>
       </recovery>
     </block>

     <!-- For continues with metadata -->
     <metadata>
       <tool-context>Read|Write|Edit|Bash|etc</tool-context>
       <risk-level>safe|warning|elevated</risk-level>
     </metadata>
   </hook-response>
   ```

3. **Files to Modify**
   - 23 hook Python files (pre-tool-use, post-tool-use, etc.)
   - `hooks/utils/message_builder.py` (+50-100 lines)
   - `hooks/utils/context_carrier.py` (+30-50 lines)
   - `hooks/hooks.json` (document `_xml_metadata` field)

4. **Success Criteria**
   - All 895 hook tests still passing
   - New XML validation tests added
   - Hooks output valid XML in `_xml_metadata` field
   - Documentation updated
   - Backward compatibility verified

**Dependencies**: None

**Timeline**:
- Day 1: Implement XML generation in message_builder.py, update 5-10 hook files
- Day 2: Complete remaining hooks, add tests, document
- Day 1-2 overlap: Integrate with existing xml_generator.py

---

### Phase 2: Power Mode XML Protocol (Effort: 2 sprints)

**Goal**: Upgrade Power Mode message protocol to use XML for improved agent coordination

**Issues**: #218
**Priority**: P1-high
**Risk**: Medium (requires coordinator changes, but backward compatible)

**Deliverables**:
- XML message serialization/deserialization in `power-mode/protocol.py`
- Priority-based task scheduling with XML metadata
- Dependency tracking between tasks
- Coordinator optimization using XML metadata
- Comprehensive tests for XML protocol

**Key Components**:

1. **XML Power Mode Message Format**
   ```xml
   <power_mode_message priority="high" urgency="immediate">
     <task id="task-123" type="analysis">
       <objective>Analyze authentication security</objective>
       <dependencies>
         <depends_on>task-122</depends_on>
       </dependencies>
       <constraints>
         <time_limit>5m</time_limit>
         <agent_preference>security-auditor</agent_preference>
       </constraints>
     </task>
   </power_mode_message>
   ```

2. **Protocol Enhancements**
   - Add `priority` and `urgency` attributes to Message
   - Extend message types with XML context
   - Update coordinator to parse/route based on XML metadata
   - Maintain JSON fallback for existing messages

3. **Files to Modify**
   - `power-mode/protocol.py` (+150-200 lines)
   - `power-mode/coordinator.py` (+100-150 lines)
   - `power-mode/statusline.py` (+50 lines)
   - Create `power-mode/XML-MESSAGES.md` documentation

4. **Success Criteria**
   - Multi-agent task completion ≥90%
   - Priority-based scheduling working
   - Backward compatibility with JSON messages
   - All tests passing + new XML protocol tests
   - <5% performance impact

**Dependencies**: Requires Phase 1 (hooks) to provide context

**Timeline**:
- Sprint 1: Implement XML protocol, update coordinator
- Sprint 2: Testing, validation, performance optimization

---

### Phase 3: Agent XML Communication (Effort: 2-3 sprints)

**Goal**: Implement XML-based agent handoff protocol to preserve context and mark severity

**Issues**: #217
**Priority**: P1-high (Medium in isolation, but high value)
**Risk**: Medium (affects 36 agents and output styles)

**Deliverables**:
- XML agent handoff format with severity tagging
- Context preservation between agents
- Agent routing optimizations using severity
- Migration path for existing 36 agents
- Updated 27 output style templates
- Tests + documentation

**Key Components**:

1. **XML Agent Handoff Format**
   ```xml
   <agent_handoff from="code-reviewer" to="security-auditor">
     <findings severity="high">
       <finding id="f-001" type="security" priority="critical">
         <location>src/auth/login.py:42</location>
         <issue>SQL injection vulnerability</issue>
         <context>User input not sanitized</context>
       </finding>
     </findings>
     <recommendations>
       <recommendation priority="high">Review all database queries</recommendation>
     </recommendations>
   </agent_handoff>
   ```

2. **Agent Definition Updates**
   - Document XML input format in all 36 `AGENT.md` files
   - Create `agents/XML-AGENT-PROTOCOL.md` specification
   - Update `agents/_templates/AGENT.template.md` with XML section
   - Add XML examples to agent documentation

3. **Output Style Migration**
   - Update 27 markdown templates to reference XML
   - Create new `agent-handoff.md` template (XML-aware)
   - Update 6 JSON schemas to document XML relationships
   - Provide migration guide for custom output styles

4. **Files to Modify**
   - 36 agent AGENT.md definitions
   - `output-styles/agent-handoff.md` (create new)
   - `output-styles/schemas/agent-handoff.schema.json` (update)
   - `agents/config.json` (document XML-aware routing)
   - All 27 output style templates (update references)

5. **Success Criteria**
   - All 36 agents support XML handoff
   - Code review cycle time reduced ≥15%
   - Context preserved across agent chains
   - Tests + documentation complete
   - Backward compatibility maintained

**Dependencies**: Requires Phase 1 (hooks) and Phase 2 (power mode)

**Timeline**:
- Sprint 1: Create XML agent handoff format, update 15 agents
- Sprint 2: Complete remaining agents, output styles
- Sprint 3: Testing, validation, documentation

---

### Phase 4: User-Facing XML Templates (Effort: 1 sprint)

**Goal**: Provide user-friendly XML templates for common workflows

**Issues**: #215
**Priority**: P1-high (nice to have but high value after Phases 1-3)
**Risk**: Low (documentation only, no code changes)

**Deliverables**:
- `packages/plugin/XML-USER-GUIDE.md` with 4 workflow templates
- Integration examples showing XML → PopKit flow
- Best practices guide (when to use XML vs. plain text)
- Templates accessible from `/popkit:help`

**Key Components**:

1. **User-Facing Templates**

   **Debugging/Investigation Prompt**
   ```xml
   <investigation>
     <problem severity="high">
       <symptom>Login fails with 500 error</symptom>
       <reproduction>Click login → enter credentials → 500 error</reproduction>
       <constraints>
         <time_constraint>Production issue, urgent</time_constraint>
       </constraints>
     </problem>
     <context>
       <recent_changes>Updated auth library yesterday</recent_changes>
       <environment>Production</environment>
     </context>
   </investigation>
   ```

   **Feature Request Prompt**
   ```xml
   <feature_request priority="medium">
     <objective>Add dark mode toggle</objective>
     <requirements>
       <requirement type="functional">Toggle in settings page</requirement>
       <requirement type="ux">Persist user preference</requirement>
     </requirements>
     <constraints>
       <constraint type="compatibility">Support all browsers</constraint>
     </constraints>
   </feature_request>
   ```

   **Code Review Prompt**
   ```xml
   <code_review focus="security,performance">
     <files>
       <file priority="high">src/auth/login.py</file>
       <file priority="medium">src/auth/session.py</file>
     </files>
     <concerns>
       <concern>SQL injection vulnerabilities</concern>
       <concern>Performance of session queries</concern>
     </concerns>
   </code_review>
   ```

   **Performance Optimization Prompt**
   ```xml
   <optimization target="load_time">
     <current_performance>
       <metric name="page_load">3.5s</metric>
       <target>< 1s</target>
     </current_performance>
     <constraints>
       <constraint>No breaking changes</constraint>
     </constraints>
   </optimization>
   ```

2. **Documentation Structure**
   - Introduction (why XML matters)
   - 4 workflow templates with examples
   - When to use XML vs. plain text
   - Common mistakes to avoid
   - Integration with PopKit features

3. **Files to Create**
   - `packages/plugin/XML-USER-GUIDE.md` (~200 lines)
   - Template library with copy-paste examples
   - FAQ for common questions
   - Video tutorial (optional future enhancement)

4. **Success Criteria**
   - Documentation complete and clear
   - User feedback >85% satisfaction
   - Low adoption friction
   - Integration with `/popkit:help` verified

**Dependencies**: Requires Phases 1-3 for foundational work

**Timeline**:
- Days 1-2: Write templates and examples
- Day 3: Integrate with help system, gather user feedback
- Day 4: Iterate based on feedback

---

### Phase 5: Context Tracking System (Effort: 1-2 sprints)

**Goal**: Implement comprehensive context tracking with XML generation

**Issues**: #627
**Priority**: P2-medium (enhancement, not blocking)
**Risk**: Low (builds on existing xml_generator.py)

**Deliverables**:
- Context delta computation between sessions
- XML context generation in session-start hook
- Context-aware XML in user-prompt-submit hook
- Findings XML output in post-tool-use hook
- Session state management with XML persistence

**Key Components**:

1. **Context Delta Computation**
   - Detect changes between sessions
   - Track new files, modified code, deleted resources
   - Generate XML diff representation

2. **Files to Create/Modify**
   - `hooks/utils/context_delta.py` (new)
   - `hooks/utils/context_state_tracking.py` (new)
   - `session-start.py` (integrate XML generation)
   - `user-prompt-submit.py` (context-aware XML)
   - `post-tool-use.py` (findings XML output)

3. **Success Criteria**
   - Context changes accurately tracked
   - XML representations valid and parseable
   - Session state persisted correctly
   - Tests passing

**Dependencies**: Requires Phase 1 (hooks) foundation

**Timeline**:
- Sprint 1: Implement context delta and state tracking
- Sprint 2: Testing, session integration

---

## Quick Wins (Can Ship Independently)

### 1. XML Generator Library Enhancement (2-4 hours)

**Issue**: #627 (partially)
**Effort**: 2-4 hours
**Value**: High
**Dependencies**: None

**What**: Polish and document the existing `xml_generator.py` module
- Add comprehensive docstrings
- Create usage examples
- Write unit tests for all functions
- Publish as reusable utility in `shared-py`

**Files**:
- `packages/shared-py/popkit_shared/utils/xml_generator.py` (already exists!)
- Add tests in `packages/popkit-core/hooks/test_xml_parsing.py`
- Create `packages/shared-py/README.md` documenting XML utils

**Why Now**: This library already exists and is ready. Publishing it as an official utility unblocks other teams.

---

### 2. Hook Protocol Documentation (4-6 hours)

**Issue**: #219 (partially)
**Effort**: 4-6 hours
**Value**: Medium
**Dependencies**: None

**What**: Document the new XML hook response protocol
- Create `packages/plugin/hooks/XML-PROTOCOL.md`
- Add examples for each block type
- Document backward compatibility guarantees
- Create migration guide for hook developers

**Files**:
- `packages/plugin/hooks/XML-PROTOCOL.md` (new, ~150 lines)
- `packages/plugin/hooks/hooks.json` (update documentation)
- Hook developer guide

**Why Now**: Design already complete in research doc. This unblocks Phase 1 implementation.

---

### 3. XML Test Suite Establishment (1 day)

**Issue**: #627, #219
**Effort**: 1 day
**Value**: High (prevents regressions)
**Dependencies**: Phase 1 (hooks)

**What**: Create comprehensive XML validation test suite
- XML structure validation (well-formed, schema compliance)
- Payload parsing tests
- Round-trip serialization/deserialization
- Performance benchmarks

**Files**:
- `packages/popkit-core/tests/test_xml_protocols.py` (new, ~500 lines)
- `packages/popkit-core/tests/test_xml_validation.py` (new)
- CI/CD integration for continuous validation

**Why Now**: Tests already written for findings XML. Generalize and expand them.

---

### 4. Agent Routing Accuracy Baseline (1-2 days)

**Issue**: #217 (analysis phase)
**Effort**: 1-2 days
**Value**: Medium (enables success metrics)
**Dependencies**: Phase 1 (hooks)

**What**: Establish baseline metrics for agent routing accuracy
- Audit current keyword matching in `agents/config.json`
- Create test suite of 50-100 prompt variants
- Measure current routing accuracy (~80% expected)
- Document baseline for Phase 3 improvements

**Files**:
- `docs/metrics/2025-12-30-agent-routing-baseline.md` (new)
- `packages/popkit-core/benchmarks/agent_routing.py` (new)
- Test prompts library

**Why Now**: Enables Phase 3 to measure impact of XML agent handoffs. Should be done before Phase 1 completes.

---

## Recommended Approach

### Start Here: Phase 1 (Hooks) → Phase 2 (Power Mode) → Phase 3 (Agents)

**Rationale**:

1. **Phase 1 (Hooks)** is lowest risk, highest foundation value
   - Only adds optional metadata field
   - Existing code unaffected
   - Ready to ship immediately
   - Other phases depend on it

2. **Phase 2 (Power Mode)** builds on Phase 1
   - Coordinator becomes more intelligent
   - Improves multi-agent efficiency
   - Medium-high value for distributed workflows

3. **Phase 3 (Agents)** is highest impact but requires Phases 1-2
   - Affects routing, discovery, collaboration
   - Requires all agent definitions updated
   - Worth it after foundation is solid

4. **Phase 4 (User Templates)** is documentation work after phases 1-3
   - Low risk, nice to have
   - Improves user experience with XML
   - Can ship anytime after foundation

5. **Phase 5 (Context Tracking)** is polish/enhancement
   - Lower priority, can come later
   - Already have foundations from #627 work

### Execution Timeline

```
Week 1:  Phase 1 (Hooks) + Quick Wins #1-2
Week 2:  Phase 1 completion + Early Phase 2 setup
Week 3-4: Phase 2 (Power Mode) implementation
Week 5-6: Phase 2 testing + Early Phase 3 setup
Week 7-9: Phase 3 (Agent Communication) implementation
Week 10: Phase 4 (User Templates) documentation
Week 11+: Phase 5 (Context Tracking) enhancement
```

---

## Dependencies & Blockers

### Phase 1 Dependencies
- None (independent)

### Phase 2 Dependencies
- Requires Phase 1 hooks in place
- Requires understanding of Power Mode coordinator
- No external blockers

### Phase 3 Dependencies
- Requires Phases 1-2 complete
- Requires audit of all 36 agents
- Requires output style migration planning

### Phase 4 Dependencies
- Requires Phases 1-3 for concrete examples
- User testing required for validation

### Phase 5 Dependencies
- Requires Phase 1 (hooks)
- Builds on existing xml_generator.py

---

## Success Metrics

| Phase | Metric | Target | Validation Method |
|-------|--------|--------|-------------------|
| **1 (Hooks)** | All 895 tests passing | 100% | CI/CD run |
| **1 (Hooks)** | Hook decision quality | 95%+ correct | Manual audit |
| **2 (Power Mode)** | Task completion rate | ≥90% | Test suite |
| **2 (Power Mode)** | Performance impact | <5% overhead | Benchmark |
| **3 (Agents)** | Routing accuracy | 95%+ (from 80%) | A/B test |
| **3 (Agents)** | Code review cycle | -20% improvement | Metrics tracking |
| **4 (Templates)** | User satisfaction | >85% | Survey |
| **Overall** | Context loss in handoffs | Eliminate | Workflow tests |

---

## Risk Assessment

### Low Risk
- Phase 1 (Hooks): Backward compatible, optional field
- Phase 4 (User Templates): Documentation only
- Phase 5 (Context Tracking): Builds on proven xml_generator.py

### Medium Risk
- Phase 2 (Power Mode): Requires coordinator changes, but backward compatible
- Phase 3 (Agents): Affects 36 agents, but rollback possible with wrapper layer

### Mitigation Strategies
1. **Backward Compatibility**: All changes maintain JSON output; XML is additional metadata
2. **Gradual Rollout**: New agents use XML, old agents get wrapper layer during Phase 3
3. **Comprehensive Testing**: Phase 1-3 all have extensive test suites before shipping
4. **Rollback Plan**: Each phase can be reverted independently without affecting others

---

## Open Questions

1. **XML vs. JSON Trade-offs**
   - Should we eventually move away from JSON entirely? (Probably not - JSON still needed for Claude Code protocol compliance)
   - How to balance XML explicitness vs. JSON compactness? (Use XML for metadata, JSON for primary protocol)

2. **User Adoption**
   - Will users naturally start using XML templates? (Probably not initially - need good examples and education)
   - Should XML be required or optional? (Optional for users, internal for hooks/power-mode)

3. **Cloud API Integration**
   - When should PopKit Cloud be updated to consume XML? (Phase 4 or later - current API works well without it)
   - Should we version the API separately? (Yes - maintain backward compatibility)

4. **Performance at Scale**
   - What's the XML parsing overhead at high throughput? (Test in Phase 2)
   - How does this affect latency-sensitive operations? (Measure and optimize)

5. **Documentation Standards**
   - Should every agent have XML examples? (Yes, by end of Phase 3)
   - How to keep documentation in sync with code? (Automated validation scripts)

---

## Related Epics & Issues

| Issue | Title | Status | Relation |
|-------|-------|--------|----------|
| **#220** | XML Integration for Enhanced Claude Understanding | Parent Epic | Umbrella for all 5 issues |
| **#627** | Context Tracking and XML Generation System | OPEN | Phase 5 |
| **#219** | Hook XML Integration for Improved Routing | OPEN | Phase 1 |
| **#218** | Power Mode XML Protocol for Coordinated Multi-Agent Workflows | OPEN | Phase 2 |
| **#217** | Agent XML Communication for Context Preservation | OPEN | Phase 3 |
| **#215** | User-Facing XML Templates for Enhanced Prompting | OPEN | Phase 4 |

**Previous Research**:
- `docs/research/2025-12-16-xml-usage-research.md` (1070 lines, comprehensive analysis)

---

## Implementation Checklist

### Pre-Implementation
- [ ] Review this roadmap with team
- [ ] Assign Phase 1 and Quick Wins leads
- [ ] Set up project milestone tracking
- [ ] Create GitHub issues for each phase with detailed acceptance criteria

### Phase 1 (Week 1-2)
- [ ] Publish xml_generator.py as utility (Quick Win #1)
- [ ] Document Hook XML Protocol (Quick Win #2)
- [ ] Implement hook XML generation in message_builder.py
- [ ] Update 23 hook Python files
- [ ] Add comprehensive tests
- [ ] Update hooks.json documentation
- [ ] Code review + merge to main

### Phase 2 (Week 3-4)
- [ ] Design Power Mode XML protocol
- [ ] Implement protocol.py updates
- [ ] Update coordinator.py
- [ ] Integration testing
- [ ] Performance benchmarking
- [ ] Code review + merge

### Phase 3 (Week 5-7)
- [ ] Establish routing accuracy baseline (Quick Win #4)
- [ ] Create XML agent handoff format
- [ ] Update 36 agent definitions
- [ ] Migrate 27 output styles
- [ ] Agent routing optimization
- [ ] Integration testing
- [ ] Code review + merge

### Phase 4 (Week 8)
- [ ] Write XML user guide
- [ ] Create 4 workflow templates
- [ ] Create integration examples
- [ ] Integrate with help system
- [ ] Gather user feedback
- [ ] Iterate and publish

### Phase 5 (Week 9+)
- [ ] Implement context delta computation
- [ ] Create context state tracking
- [ ] Integration with session hooks
- [ ] Testing and validation
- [ ] Code review + merge

---

## Success Criteria Summary

**This epic is complete when:**

1. **Phase 1**: All hooks output XML in `_xml_metadata`, 895 tests passing
2. **Phase 2**: Power Mode messages use XML priority/urgency, 90%+ task completion
3. **Phase 3**: All 36 agents support XML handoff, routing accuracy 95%+
4. **Phase 4**: XML user guide available, >85% user satisfaction
5. **Phase 5**: Context tracking working, delta computation accurate
6. **Overall**: Code review cycle time reduced 20%, context loss eliminated in multi-agent workflows

---

**Document Status**: Ready for brainstorming & implementation planning
**Next Step**: Team review and Phase 1 kickoff

