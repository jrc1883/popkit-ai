# Multi-Model Dispatch Investigation

**Branch**: `claude/pop-kit-script-execution-sOHL9`
**Epic**: #240 | **Issue**: #241
**Date**: 2025-12-15
**Status**: Complete Analysis

---

## Executive Summary

Investigation reveals well-researched multi-model dispatch feature with significant value for PopKit's platform expansion. The branch contains designs for:

1. **Runtime Complexity Scoring** - 5-dimension analysis (effort, testing, integration, dependencies)
2. **Cost Optimization Routing** - 20-40% potential savings
3. **Dynamic Task-to-Model Dispatch** - Route to optimal models (Opus/Sonnet/Haiku)
4. **Performance Analytics** - Track model success rates

### Recommendation: **SPLIT v1 + v2**

**v1.0 (Marketplace)**: Complexity scoring + cost estimation (2-3 sessions, informational)
**v2.0 (Platform)**: Full dispatch routing + analytics (6-8 sessions, requires cloud infrastructure)

---

## 1. What Exists Today (Master)

### Current Multi-Model Infrastructure

**Foundations**:
- `docs/MODEL_CAPABILITIES.md` - 6 AI tool capability matrix
- `docs/API_CONTRACT.md` - Model-agnostic endpoints
- `docs/PLATFORM_ROADMAP.md` - Phase 5 cost optimization commitment
- Cloud API with Upstash services

**Agent Routing**:
- Context-based keyword matching
- File pattern detection
- Confidence-based filtering (80+ threshold)

**Relevant Roadmap**:
Phase 5 - Orchestration Layer includes:
```
4. **Cost Optimization**
   - Route simple tasks to cheaper models
   - User-defined budget constraints
   - Cost analytics and recommendations
```

This branch **directly aligns** with v1.0 roadmap commitments.

---

## 2. What's New in Branch

### Multi-Dimensional Complexity Scoring

**Algorithm**: Score tasks on 5 dimensions (1-10 scale):
- **Effort**: Implementation complexity
- **Testing**: Test coverage requirements
- **Integration**: Risk of side effects
- **Dependencies**: External dependency count
- **Reasoning**: Human-readable explanation

**Examples**:
- "CSS styling" → Complexity 1 (use Haiku)
- "Bug fix" → Complexity 3 (use Haiku)
- "New feature" → Complexity 6 (use Sonnet)
- "Architecture redesign" → Complexity 8 (use Opus)

### Cost Optimization Routing

| Complexity | Model | Tokens (avg) | Cost |
|-----------|-------|------------|------|
| 1-2 | Haiku | 1000 | $0.02 |
| 3-4 | Haiku | 2500 | $0.04 |
| 5-6 | Sonnet | 4500 | $0.15 |
| 7-8 | Sonnet | 7000 | $0.24 |
| 9-10 | Opus | 10000 | $0.75 |

**Business Impact**: 20-40% cost savings through intelligent routing

### Cloud Integration

Architecture leverages existing infrastructure:
- Cloudflare Workers: `/v2/dispatch/score-task`
- Upstash Redis: Performance history
- Upstash Vector: Semantic task matching
- Upstash Workflows: Durable execution

---

## 3. Dependencies

### v1.0 Requirements
- ✅ Multi-Model Foundation (in progress)
- ✅ Unified Cloud API (documented)
- ✅ Tool detection & routing (headers defined)

### v2.0 Requirements
- ⏳ Phase 4: Cloud Platform Enhancement (~6-8 weeks away)
- ⏳ Model performance analytics infrastructure
- ⏳ Codex/Gemini integration (for actual dispatch)

---

## 4. Integration Complexity

### v1.0 Phase (Foundation)
- **Effort**: Medium (2-3 sessions)
- **Lines**: 2000-3000
- **Files**: 5-8 new + 2-3 modified
- **Tests**: ~30 unit + 10 integration + 3 E2E

### v2.0 Phase (Full Implementation)
- **Effort**: High (6-8 sessions)
- **Lines**: 5000-6700
- **Files**: 15-25 new + 4-6 modified
- **Tests**: +40 unit + 15 integration + 5 performance

---

## 5. Value Proposition

### Problems Solved (v1.0)
1. "Which model should I use?" → Complexity score guides selection
2. "How much will this cost?" → Cost estimation before execution
3. "Does PopKit understand my work?" → Analysis demonstrates comprehension

### Problems Solved (v2.0)
1. "How do I optimize costs?" → Team-wide analytics
2. "Which model is best for US?" → Performance data per project
3. "Can I automate routing?" → Auto-route to optimal model

### User Impact

**v1.0**: Individual developers (Medium impact)
- 40-60% adoption
- Better cost transparency
- Low friction (informational)

**v2.0**: Teams & enterprises (High impact)
- 70-90% adoption
- 20-40% cost savings
- Data-driven decisions

---

## 6. Risks

### Technical Risks (v1.0)
- **Complexity Scoring Accuracy** (Medium): Heuristics may not capture true difficulty
- **Cost Estimation Drift** (Medium): Model pricing changes over time

### Technical Risks (v2.0)
- **Model Performance Variability** (High): Quality varies by task type
- **Performance Analytics at Scale** (Medium): Storing data for millions of tasks

### Mitigation
- v1: Start simple, add feedback loop in v2
- v1: Show actual costs retrospectively
- v2: Aggregate summaries, not individual records

---

## 7. Recommendation

### SPLIT v1 + v2 IMPLEMENTATION

```
v1.0 (Marketplace Phase) - APPROVED
├── Complexity Scoring ✅
├── Cost Estimation ✅
├── Basic Routing Logic (informational) ✅
├── Preference System ✅
└── Documentation ✅
    Timeline: 2-3 sessions (~800-1200 lines)
    Blocking: None
    Value: Medium
    Risk: Low

v2.0 (Platform Expansion) - PLANNED
├── Model Performance Analytics ✅
├── Advanced A/B Testing ✅
├── Multi-Model Routing ✅
├── Team Budget Management ✅
└── Cost Dashboard ✅
    Timeline: 6-8 sessions (~3800-5500 lines)
    Blocking: Epic 5 Cloud Platform Enhancement
    Value: High
    Risk: Medium
```

### Why This Split

**v1.0 Inclusion**:
- Complexity scoring valuable immediately
- Cost transparency builds trust
- Informational (recommendations), not mandatory
- Zero breaking changes
- Aligns with Phase 5 roadmap

**v2.0 Deferral**:
- Performance analytics (Epic 5) not ready
- Multi-model routing depends on Codex/Gemini integration
- Better to validate v1 before v2 implementation

---

## v1.0 Implementation Plan

### Session 1: Core Utilities
- Create `complexity_analyzer.py` (500-800 LOC)
- Create `cost_estimator.py` (600-900 LOC)
- Tests: 15+ cases

### Session 2: Hook Integration
- Update `pre-tool-use.py`
- Create `complexity-report.md` output style

### Session 3: Documentation
- Enhance `pop-task-breakdown` skill
- Create examples and guides

---

## Success Metrics

### v1.0 Acceptance Criteria
- [ ] Complexity scoring available for major commands
- [ ] Cost estimates shown before execution
- [ ] Scores consistent (same task → same score)
- [ ] Reasoning provided for all scores
- [ ] <100ms overhead
- [ ] >80% test coverage

### v2.0 Foundation
- [ ] Complexity data flowing to cloud API
- [ ] Cost history available for analysis
- [ ] User preferences persisted
- [ ] Performance tracking infrastructure ready

---

## Alignment with Roadmap

**PLATFORM_ROADMAP.md - Phase 5**:
```
Features:
1. Task-to-Model Routing
2. Multi-Model Workflows
3. Unified Command Interface
4. **Cost Optimization** ← This branch provides this
```

**Branch Alignment**:
- Runtime complexity scoring → Task-to-Model Routing foundation
- Cost estimation → Cost Optimization feature
- Preference system → User-defined constraints

---

## Next Steps

1. Create implementation issues (#250-253)
2. Assign v1.0 phase to current work stream
3. Plan v2.0 phase for post-Phase 4 timeline
4. Update PLATFORM_ROADMAP.md with split details

---

**Document Status**: Ready for implementation planning
**Recommendation**: Split v1.0 + v2.0
**Implementation Owner**: TBD (post-approval)
