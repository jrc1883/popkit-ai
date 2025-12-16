# PopKit Self-Testing Framework - Implementation Checklist

**Issue**: #258
**Design Doc**: [self-testing-framework-design.md](./self-testing-framework-design.md)
**Status**: Ready to Begin Implementation

## Phase 1: Foundation (Week 1) ⬜

### 1.1 Test Telemetry Module
- [ ] Create `packages/plugin/hooks/utils/test_telemetry.py`
  - [ ] `is_test_mode()` - Check TEST_MODE env var
  - [ ] `get_test_session_id()` - Get TEST_SESSION_ID
  - [ ] `create_event()` - Format telemetry event
  - [ ] `emit_event()` - Print TELEMETRY:{json} to stdout
  - [ ] `emit_routing_decision()` - Specific event emitter
  - [ ] `emit_agent_invocation()` - Specific event emitter
  - [ ] `emit_agent_completion()` - Specific event emitter
  - [ ] `emit_skill_start()` - Specific event emitter
  - [ ] `emit_skill_complete()` - Specific event emitter
  - [ ] `emit_phase_transition()` - Specific event emitter
  - [ ] Add comprehensive docstrings
  - [ ] Add unit tests

### 1.2 Hook Telemetry Integration
- [ ] Modify `packages/plugin/hooks/agent-orchestrator.py`
  - [ ] Import test_telemetry functions
  - [ ] Add `emit_routing_decision()` after routing logic
  - [ ] Add `emit_agent_invocation()` when Task tool invoked
  - [ ] Test with simple prompt

- [ ] Verify `packages/plugin/hooks/utils/skill_state.py`
  - [ ] ✅ Already has test_telemetry imports (lines 24-32)
  - [ ] ✅ Already has `_emit_telemetry_event()` method (lines 117-134)
  - [ ] ✅ Already emits skill_start (line 153)
  - [ ] ✅ Already emits skill_end (line 184)
  - [ ] ✅ Already emits phase_change (line 286)
  - [ ] Just verify it works in test mode

### 1.3 Behavior Schemas
- [ ] Create `packages/benchmarks/src/behavior/schema.ts`
  - [ ] `BehaviorCapture` interface
  - [ ] `RoutingDecision` interface
  - [ ] `AgentEvaluation` interface
  - [ ] `AgentInvocation` interface
  - [ ] `SkillExecution` interface
  - [ ] `PhaseTransition` interface
  - [ ] `WorkflowStatus` interface
  - [ ] `ToolPattern` interface
  - [ ] `SequenceAnalysis` interface
  - [ ] `UserDecision` interface
  - [ ] `AgentGroup` interface
  - [ ] `ToolCall` interface
  - [ ] Export all types

### 1.4 Behavior Capture Service
- [ ] Create `packages/benchmarks/src/behavior/capture.ts`
  - [ ] `BehaviorCaptureService` class
  - [ ] Constructor: taskId, mode, sessionId
  - [ ] `attachToProcess(stdout)` - Listen to subprocess
  - [ ] `processLine(line)` - Parse TELEMETRY: events
  - [ ] `buildBehaviorCapture()` - Aggregate into structure
  - [ ] `analyzeRouting()` - Process routing events
  - [ ] `analyzeAgents()` - Process agent events
  - [ ] `analyzeSkills()` - Process skill events
  - [ ] `analyzeWorkflows()` - Process workflow events
  - [ ] `analyzeTools()` - Process tool events
  - [ ] `analyzeDecisions()` - Process decision events
  - [ ] `analyzePerformance()` - Calculate metrics
  - [ ] `detectParallelGroups()` - Find parallel execution
  - [ ] `categorizeSkill()` - Categorize skills
  - [ ] Add unit tests

### 1.5 Basic Test
- [ ] Create test benchmark task
  - [ ] Simple task: "Create hello.txt with 'Hello World'"
  - [ ] Run with TEST_MODE=true
  - [ ] Verify TELEMETRY events appear in stdout
  - [ ] Verify BehaviorCaptureService parses events
  - [ ] Verify behavior.json structure is correct

**Phase 1 Completion Criteria**:
- [ ] Test telemetry module working
- [ ] Hooks emitting events correctly
- [ ] Capture service aggregating data
- [ ] behavior.json file generated
- [ ] Can run: `TEST_MODE=true npm run benchmark -- hello-world`

---

## Phase 2: Validation Engine (Week 2) ⬜

### 2.1 Expectation Schema
- [ ] Create `packages/benchmarks/src/validator/expectations.ts`
  - [ ] `BehaviorExpectations` interface
  - [ ] Agent expectation types
  - [ ] Skill expectation types
  - [ ] Workflow expectation types
  - [ ] Routing expectation types
  - [ ] Tool expectation types
  - [ ] Performance expectation types
  - [ ] `loadExpectations(taskId)` function
  - [ ] Add JSON schema for validation

### 2.2 Validator Implementation
- [ ] Create `packages/benchmarks/src/validator/validator.ts`
  - [ ] `BehaviorValidator` class
  - [ ] Constructor: expectations, actual
  - [ ] `validate()` - Main validation entry point
  - [ ] `validateAgents()` - Agent validation logic
    - [ ] Check shouldInvoke
    - [ ] Check shouldNotInvoke
    - [ ] Check invocationCount
  - [ ] `validateSkills()` - Skill validation logic
  - [ ] `validateWorkflows()` - Workflow validation logic
  - [ ] `validateRouting()` - Routing validation logic
  - [ ] `validateTools()` - Tool validation logic
  - [ ] `validatePerformance()` - Performance validation logic
  - [ ] `generateWarnings()` - Warning generation
  - [ ] `generateInsights()` - Insight generation
  - [ ] `calculateScore()` - Score calculation (0-100)
  - [ ] `ValidationResult` interface
  - [ ] `Violation` interface
  - [ ] `Warning` interface
  - [ ] Add comprehensive tests

### 2.3 First Expectation File
- [ ] Create `packages/benchmarks/tasks/bouncing-balls.expectations.json`
  - [ ] Define agent expectations
    - [ ] shouldInvoke: ui-designer, rapid-prototyper
    - [ ] shouldNotInvoke: security-auditor, database-optimizer
    - [ ] invocationCount: min=1, max=3
  - [ ] Define skill expectations
    - [ ] shouldInvoke: pop-verify-completion
  - [ ] Define workflow expectations
    - [ ] shouldNotActivate: feature-dev
  - [ ] Define routing expectations
    - [ ] expectedTriggers: canvas|animation|ui
    - [ ] minimumConfidence: 50
  - [ ] Define tool expectations
    - [ ] forbiddenPatterns: TodoWrite
  - [ ] Define performance expectations
    - [ ] maxRoutingTime: 500ms

### 2.4 Validation Test
- [ ] Run bouncing-balls benchmark with --record-behavior
- [ ] Load expectation file
- [ ] Run validator
- [ ] Verify violations detected correctly
- [ ] Verify score calculation
- [ ] Verify insights generated

**Phase 2 Completion Criteria**:
- [ ] Expectation schema defined
- [ ] Validator implementation complete
- [ ] First expectation file created
- [ ] Validation runs successfully
- [ ] Can detect violations

---

## Phase 3: Integration & Reporting (Week 3) ⬜

### 3.1 Report Generator
- [ ] Create `packages/benchmarks/src/reports/behavior-report.ts`
  - [ ] `writeBehaviorReport()` function
  - [ ] `generateReport()` function
  - [ ] Executive Summary section
  - [ ] Key Insights section
  - [ ] Violations section (by severity)
  - [ ] Warnings section
  - [ ] Detailed Behavior Analysis section
    - [ ] Agent Routing
    - [ ] Agent Invocations
    - [ ] Skill Executions
    - [ ] Workflow Phases
  - [ ] Expected vs Actual Comparison table
  - [ ] Performance Metrics table
  - [ ] Recommendations section
  - [ ] Markdown formatting
  - [ ] Test report generation

### 3.2 Benchmark Runner Integration
- [ ] Modify `packages/benchmarks/src/runner.ts`
  - [ ] Add `recordBehavior?: boolean` to BenchmarkOptions
  - [ ] Set TEST_MODE env var when recordBehavior=true
  - [ ] Set TEST_SESSION_ID env var
  - [ ] Initialize BehaviorCaptureService
  - [ ] Attach capture to subprocess stdout
  - [ ] Build behavior capture after execution
  - [ ] Save behavior.json to results directory
  - [ ] Load expectation file
  - [ ] Run validator
  - [ ] Save behavior report
  - [ ] Add behaviorValidation to result
  - [ ] Update return type

### 3.3 CLI Flag Support
- [ ] Modify `packages/benchmarks/src/cli.ts`
  - [ ] Add `--record-behavior` flag to run command
  - [ ] Pass flag to runner
  - [ ] Display behavior validation in output
    - [ ] Show score
    - [ ] Show pass/fail status
    - [ ] Show violation count
    - [ ] Show report path
  - [ ] Update help text

### 3.4 More Expectation Files
- [ ] Create `packages/benchmarks/tasks/hello-world.expectations.json`
  - [ ] Simple task expectations
  - [ ] Should NOT invoke many agents
  - [ ] Should NOT activate workflows

- [ ] Create `packages/benchmarks/tasks/todo-app.expectations.json`
  - [ ] Complex task expectations
  - [ ] Should invoke multiple agents
  - [ ] Should activate feature-dev workflow

- [ ] Create `packages/benchmarks/tasks/api-endpoint.expectations.json`
  - [ ] API-specific expectations
  - [ ] Should invoke api-designer agent

### 3.5 End-to-End Test
- [ ] Run benchmark suite with --record-behavior
- [ ] Verify all behavior.json files generated
- [ ] Verify all validation reports generated
- [ ] Verify violations detected correctly
- [ ] Verify reports are readable and actionable

**Phase 3 Completion Criteria**:
- [ ] Report generator working
- [ ] Benchmark runner integrated
- [ ] CLI flag functional
- [ ] 3-5 expectation files created
- [ ] End-to-end flow working
- [ ] Can run: `npm run benchmark -- {task} --record-behavior`

---

## Phase 4: Enhancement (Week 4) ⬜

### 4.1 Sequence Analysis
- [ ] Enhance tool sequence detection
  - [ ] Common sequences: Write → Bash → Edit
  - [ ] Anti-patterns: repeated failed attempts
  - [ ] Pattern counting and ranking

### 4.2 Parallel Group Detection
- [ ] Improve parallel agent detection
  - [ ] Time-based grouping (within N seconds)
  - [ ] Coordination pattern detection (mesh/star/chain)

### 4.3 Comparative Analysis
- [ ] Compare vanilla vs popkit behavior
  - [ ] Side-by-side comparison in report
  - [ ] Highlight PopKit-specific features
  - [ ] Show efficiency differences

### 4.4 Behavior Diff Visualization
- [ ] Create behavior diff tool
  - [ ] Compare two behavior.json files
  - [ ] Show added/removed/changed agents
  - [ ] Show routing changes
  - [ ] Generate diff report

### 4.5 Performance Optimization
- [ ] Profile telemetry overhead
- [ ] Optimize JSON parsing
- [ ] Lazy load expectations
- [ ] Stream processing for large outputs

**Phase 4 Completion Criteria**:
- [ ] Sequence analysis working
- [ ] Parallel detection improved
- [ ] Comparative analysis implemented
- [ ] Diff tool created
- [ ] Performance overhead <5%

---

## Documentation ⬜

### User Documentation
- [ ] Quick Start guide
  - [ ] How to run with --record-behavior
  - [ ] How to read behavior reports
  - [ ] Common use cases

- [ ] Expectation Writing Guide
  - [ ] Schema reference
  - [ ] Examples for each type
  - [ ] Best practices
  - [ ] Templates

- [ ] Report Interpretation Guide
  - [ ] Understanding violations
  - [ ] Score meaning
  - [ ] Taking action on violations

- [ ] Troubleshooting Guide
  - [ ] Common issues
  - [ ] Debug tips
  - [ ] FAQ

### Developer Documentation
- [ ] Architecture overview
- [ ] Data flow diagrams
- [ ] Schema reference
- [ ] Hook integration guide
- [ ] Validator extension guide
- [ ] Contributing guidelines

### Examples
- [ ] Simple task example
- [ ] Complex task example
- [ ] Custom validator example
- [ ] Behavior analysis example

---

## Testing ⬜

### Unit Tests
- [ ] test_telemetry.py tests
- [ ] BehaviorCaptureService tests
- [ ] BehaviorValidator tests
- [ ] Report generator tests

### Integration Tests
- [ ] Full capture → validate → report flow
- [ ] Multiple benchmark tasks
- [ ] Edge cases (no agents, errors, etc.)

### Regression Tests
- [ ] Existing benchmarks maintain behavior
- [ ] No performance degradation

### Performance Tests
- [ ] Measure overhead with/without recording
- [ ] Verify <5% increase in runtime

---

## Deployment ⬜

### Package Updates
- [ ] Update package.json dependencies
- [ ] Update TypeScript types
- [ ] Update tsconfig.json if needed

### CI/CD Integration
- [ ] Add behavior testing to CI pipeline
- [ ] Run on PR validation
- [ ] Generate behavior reports in CI
- [ ] Fail on critical violations

### Documentation Deploy
- [ ] Add to main README
- [ ] Add to benchmark README
- [ ] Publish design docs
- [ ] Create video walkthrough

---

## Success Metrics ⬜

### Functional Metrics
- [ ] 100% of agent invocations captured
- [ ] 100% of skill executions captured
- [ ] >95% validation precision
- [ ] <5% false positive rate

### Performance Metrics
- [ ] <5% benchmark runtime increase
- [ ] <100ms routing time overhead
- [ ] <500ms validation time

### Quality Metrics
- [ ] 5+ expectation files created
- [ ] 90%+ team satisfaction with reports
- [ ] 0 critical bugs in production

---

## Known Limitations & Future Work

### Current Limitations
- Tool sequence analysis is heuristic-based
- Parallel group detection uses time windows
- No real-time monitoring during execution
- Limited to benchmark context (not production)

### Future Enhancements (v1.1+)
- [ ] Visual dashboards for behavior
- [ ] Trend analysis across versions
- [ ] Expectation generator (auto-generate from successful runs)
- [ ] ML-based behavior prediction
- [ ] Anomaly detection
- [ ] Real-time monitoring
- [ ] Production telemetry support

---

## Issue References

- **#258**: PopKit Self-Testing Framework (this issue)
- **#159**: AskUserQuestion enforcement (skill_state.py already tracks this)
- **#183**: Required decisions on error (skill_state.py already supports this)
- **#188**: Activity ledger publishing (skill_state.py already does this)
- **#226**: Test telemetry (basis for this framework)

---

## Checklist Summary

### Phase 1: Foundation ⬜ (Week 1)
- [ ] test_telemetry.py module
- [ ] Hook integration
- [ ] Behavior schemas
- [ ] Capture service
- [ ] Basic test

### Phase 2: Validation ⬜ (Week 2)
- [ ] Expectation schema
- [ ] Validator implementation
- [ ] First expectation file
- [ ] Validation test

### Phase 3: Integration ⬜ (Week 3)
- [ ] Report generator
- [ ] Runner integration
- [ ] CLI flag
- [ ] More expectation files
- [ ] End-to-end test

### Phase 4: Enhancement ⬜ (Week 4)
- [ ] Sequence analysis
- [ ] Parallel detection
- [ ] Comparative analysis
- [ ] Diff visualization
- [ ] Performance optimization

### Documentation ⬜
- [ ] User docs
- [ ] Developer docs
- [ ] Examples

### Testing ⬜
- [ ] Unit tests
- [ ] Integration tests
- [ ] Regression tests
- [ ] Performance tests

### Deployment ⬜
- [ ] Package updates
- [ ] CI/CD integration
- [ ] Docs deploy

---

**Total Estimated Effort**: 4 weeks
**Priority**: P1-high
**Issue**: #258
**Status**: Ready to Begin ⬜

## Next Action

Start Phase 1.1: Create `test_telemetry.py` module

```bash
cd packages/plugin/hooks/utils
# Create test_telemetry.py
# Implement is_test_mode, emit_event, etc.
# Add unit tests
```
