# Context Optimization Strategy - Design Document

**Date:** 2025-12-17
**Status:** Design Complete → Ready for Planning
**Context:** Brainstorming session on reducing PopKit's context usage

## Executive Summary

Reduce PopKit's context baseline from ~35k to ~25k tokens (30% reduction) through two-phase optimization while tracking future Anthropic SDK patterns for readiness.

## Current State Analysis

### Context Breakdown (80k/200k used)
- **System Prompt:** 3.2k tokens (Claude Code core instructions)
- **System Tools:** 23.3k tokens (Task tool = ~15k, other tools = ~8k)
- **Memory Files:** 5.9k tokens (CLAUDE.md)
- **Custom Agents:** 2.4k tokens (40+ agent definitions)
- **Free Space:** 120k tokens (60%)

### Problem Statement

1. **Task Tool Bloat:** All 40+ PopKit agents loaded upfront (~15k tokens)
2. **No Tool Filtering:** All tools available for every task (unnecessary context)
3. **Future Risk:** Anthropic SDK patterns (tool_runner, @beta_tool) may change architecture

### Existing Infrastructure (Already Built!)

PopKit has partial implementations that were never fully activated:

- ✅ `embedding_store.py` - SQLite vector storage with cosine similarity
- ✅ `cloud_agent_search.py` - Upstash Vector semantic agent discovery
- ✅ `voyage_client.py` - Voyage AI embeddings client
- ✅ `agents/config.json` - tool_choice configuration (marked "advisory")

**Just needs enforcement hooks and integration!**

## Proposed Solution

### Three-Track Strategy

#### Track 1: Main Branch (Stable, Production)
Complete existing partial implementations with stable features.

#### Track 2: Experimental Branch (Future-Ready)
Prototype Anthropic SDK patterns in isolation.

#### Track 3: Monitoring (Ongoing)
Track Anthropic releases for SDK pattern changes.

## Architecture Design

### Phase 1: Tool Choice Enforcement (Quick Win)

**Goal:** Reduce available tools per task using existing config.json structure.

**Current State:**
```json
// agents/config.json:374-424
"tool_choice": {
  "enforcement": "Currently advisory - full enforcement requires hook implementation"
}
```

**Implementation:**
1. Hook reads `tool_choice` from agents/config.json
2. Filters tools before passing to Claude API
3. Reduces System Tools context by 30-50% (5-8k tokens)

**Example:**
```python
# Hook: pre-tool-use.py
def filter_tools(task_context, available_tools):
    config = load_agent_config()
    workflow = determine_workflow(task_context)

    # Get required tools for this workflow
    required = config['tool_choice']['workflow_steps'][workflow]['required_tools']

    # Filter to only required tools
    return [t for t in available_tools if t.name in required]
```

**Files to Create/Modify:**
- `packages/plugin/hooks/utils/tool_filter.py` (NEW)
- `packages/plugin/hooks/pre-tool-use.py` (MODIFY)
- `packages/plugin/agents/config.json` (UPDATE enforcement status)

**Impact:** -5 to -8k tokens (System Tools: 23.3k → 15-18k)

### Phase 2: Embedding-Based Agent Loading (Bigger Impact)

**Goal:** Only load relevant agents using semantic search.

**Current Infrastructure:**
- SQLite vector store with cosine similarity (embedding_store.py)
- Cloud agent search via Upstash Vector (cloud_agent_search.py)
- Voyage AI embeddings (voyage_client.py)

**Implementation:**
1. Pre-compute embeddings for all 40+ agent descriptions
2. Store in SQLite (local) and Upstash Vector (cloud)
3. On task start, embed user query
4. Load only top 5-10 most relevant agents
5. Fallback to keyword matching if embeddings fail

**Example Flow:**
```
User: "fix the login bug"

1. Embed query → [0.23, -0.41, 0.89, ...]
2. Semantic search → Top matches:
   - bug-whisperer (similarity: 0.92)
   - security-auditor (similarity: 0.78)
   - test-writer-fixer (similarity: 0.71)
3. Load only those 3 agents (not all 40)
4. Context saved: ~10k tokens
```

**Files to Create/Modify:**
- `packages/plugin/hooks/utils/agent_loader.py` (NEW)
- `packages/plugin/hooks/session-start.py` (MODIFY)
- `packages/plugin/agents/config.json` (ADD agent embeddings)
- `packages/plugin/scripts/generate-agent-embeddings.py` (NEW)

**Impact:** -10k tokens (Custom Agents: 2.4k → ~0.8k)

### Phase 3: SDK Pattern Tracking (Lightweight)

**Goal:** Document and track Anthropic SDK patterns without active development.

**Patterns to Monitor:**
1. `@beta_tool` decorator - Replacing manual tool schemas
2. SDK `tool_runner` - Replacing manual agentic loops
3. Native tool filtering - SDK-level tool_choice support

**Tracking Strategy:**
- Create GitHub issue: "Track Anthropic SDK Patterns for Future Migration"
- Labels: `research`, `phase:future`, `blocked`, `architecture`
- Quarterly review (or when major SDK releases)
- Link to anthropic-sdk-python releases and cookbooks

**Migration Path (Documented Only):**
```markdown
## When SDK Patterns Stabilize

### Power Mode coordinator.py
- Before: Manual while loops with message building
- After: SDK tool_runner handles loop automatically

### Hook tool schemas
- Before: Manual JSON schemas in hooks
- After: @beta_tool decorators on Python functions

### Context optimization
- Before: Custom embedding-based filtering
- After: SDK native tool_choice (if available)
```

**Files to Create:**
- GitHub issue body with migration documentation
- `docs/research/anthropic-sdk-patterns-tracking.md`

**Impact:** Zero code changes, just awareness and readiness

## Implementation Phases

### Phase 1: Tool Choice Enforcement (1-2 weeks)

**Tasks:**
1. Create tool_filter.py utility module
2. Implement hook integration in pre-tool-use.py
3. Update agents/config.json enforcement status
4. Test with sample workflows
5. Measure context reduction

**Success Criteria:**
- [ ] Tool filtering works for all workflow types
- [ ] Config override flag available for debugging
- [ ] Context reduced by 5-8k tokens
- [ ] No functionality regressions

### Phase 2: Embedding-Based Agent Loading (2-3 weeks)

**Tasks:**
1. Generate embeddings for all agent descriptions
2. Store embeddings in SQLite + Upstash Vector
3. Create agent_loader.py utility module
4. Integrate with session-start hook
5. Implement keyword fallback
6. Test semantic matching accuracy

**Success Criteria:**
- [ ] Embedding generation script works
- [ ] Top 5-10 agents loaded per task
- [ ] Keyword fallback functions correctly
- [ ] Context reduced by ~10k tokens
- [ ] Agent routing accuracy >90%

### Phase 3: SDK Tracking (Ongoing)

**Tasks:**
1. Create GitHub tracking issue
2. Document current vs. future patterns
3. Link to Anthropic resources
4. Set quarterly review reminder

**Success Criteria:**
- [ ] Tracking issue created with clear migration path
- [ ] Links to anthropic-sdk-python and cookbooks
- [ ] Migration documentation complete
- [ ] Review cadence established

## Success Metrics

### Quantitative
- Context baseline: 35k → 25k tokens (30% reduction)
- System Tools: 23.3k → 15k tokens
- Custom Agents: 2.4k → 0.8k tokens
- Agent routing accuracy: >90%
- Fallback success rate: >95%

### Qualitative
- No user-facing functionality changes
- Tool filtering transparent to users
- Agent selection feels "smart"
- Fast fallback when embeddings fail
- Clear path for SDK migration when ready

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Embeddings fail or slow | Keyword fallback with <100ms latency |
| Tool filtering breaks workflow | Config override flag + comprehensive testing |
| Wrong agents loaded | Keyword fallback + user feedback loop |
| SDK patterns change before stable | Documented migration path, no active work |
| Upstash Vector unavailable | Local SQLite fallback |
| Voyage AI rate limits | Cache embeddings, batch generation |

## Future-Proofing

### Anthropic SDK Changes
- Quarterly review of anthropic-sdk-python releases
- Watch anthropics/claude-cookbooks for patterns
- Documented migration ready when patterns stabilize
- No active experimental work until stable

### Scaling Considerations
- Embedding store supports project-specific agents
- Tool filtering config supports per-project overrides
- Cloud agent search scales to 1000+ agents
- SQLite fallback works offline

## Technical Decisions

### Why SQLite for Embeddings?
- Fast local cosine similarity (<10ms)
- No external dependencies
- Works offline
- Syncs with Upstash Vector for cloud benefits

### Why Upstash Vector?
- Hosted vector search (Pro tier benefit)
- Cross-project pattern learning
- No maintenance overhead
- Fast semantic search at scale

### Why Voyage AI?
- Best-in-class embeddings for tool discovery
- Generous free tier for development
- Easy integration (existing voyage_client.py)

### Why Not Build Experimental Branch Now?
- SDK patterns still in beta (cookbooks show changes)
- Risk of wasted effort if patterns change
- Lightweight tracking achieves readiness goal
- Can build experimental branch when patterns stabilize

## Related Work

### Existing Issues
- Issue #224: v1.0.0 Validation Audit
- Issue #265: XML Integration Epic (context preservation)
- Issue #101: Upstash Vector Integration (completed)

### Documentation
- `packages/plugin/agents/config.json` - Tool choice configuration
- `packages/plugin/hooks/utils/embedding_store.py` - Vector storage
- `packages/plugin/hooks/utils/cloud_agent_search.py` - Agent discovery
- `docs/plans/2025-12-17-documentation-cleanup-outdated-docker-redis.md` - Separate doc issue

## Next Steps

1. **Approve this design** ✅
2. **Create implementation plan** (invoke pop-writing-plans skill)
3. **Generate GitHub issues** with proper labels:
   - Phase 1: `enhancement`, `P1-high`, `phase:now`, `hooks`, `performance`
   - Phase 2: `enhancement`, `P1-high`, `phase:now`, `agents`, `performance`
   - Phase 3: `research`, `P3-low`, `phase:future`, `architecture`, `blocked`
   - Doc cleanup: `documentation`, `P2-medium`, `phase:now`, `plugin`

---

**Design approved:** 2025-12-17
**Ready for planning:** Yes
**Ready for implementation:** After plan review
