# Benchmark Design Notes - 2025-12-15

## Key Observations

### Issue Quality Paradox

**Problem:** Our benchmark issues are TOO GOOD.

**Why:** PopKit has issue templates and encourages structured requirements. Real developers without PopKit often write vague issues:
- ❌ "make the app faster" (no metrics, no acceptance criteria)
- ❌ "fix that bug" (which bug? where?)
- ❌ "add dark mode" (no UX specs, no requirements)

**Our Issues:**
- ✅ Detailed acceptance criteria
- ✅ Clear success metrics
- ✅ Comprehensive requirements
- ✅ Test definitions

**This creates unfair comparison:** PopKit is being tested with PopKit-quality inputs.

### Solution: Test Multiple Issue Quality Levels

Create benchmark variants for each issue:

#### 1. **Vibe-Coded Issue** (Minimal Context)
```
Title: make it faster
Body: the app is slow. fix it.
```

#### 2. **Junior Dev Issue** (Some Context)
```
Title: Improve app performance
Body: Users are complaining about slow load times.
Can we optimize the API calls?
```

#### 3. **Senior Dev Issue** (Structured, PopKit-quality)
```
Title: Reduce API response time by 50%
Body:
## Problem
API endpoints taking 800ms average (P95: 1200ms)

## Success Criteria
- [ ] P95 response time < 600ms
- [ ] No N+1 queries
- [ ] Caching layer implemented

## Context
Endpoints: /users, /posts, /comments
Database: PostgreSQL 14
Current load: 1000 req/min
```

### Expected Outcomes

| Issue Quality | Vanilla | PopKit |
|--------------|---------|--------|
| **Vibe-Coded** | Struggles, asks questions | Brainstorms, plans, asks targeted questions |
| **Junior Dev** | Partial solution | Complete solution with context gathering |
| **Senior Dev** | Good solution | Equally good solution, possibly faster |

**Hypothesis:** PopKit's value increases with ambiguous inputs (brainstorming, context gathering, planning).

### Implementation Strategy

1. **Phase 1:** Test with structured issues (current)
   - Establishes baseline
   - Tests orchestration with clear requirements

2. **Phase 2:** Add "messy" variants
   - Same task, vague description
   - Tests PopKit's brainstorming/planning value
   - More realistic for actual development

3. **Phase 3:** Mixed prompt quality testing
   - Some issues detailed, some vague
   - Simulates real project work

## Action Items

- [ ] Run current benchmarks with structured prompts (todo-app, issue-239)
- [ ] Create vibe-coded variants of same tasks
- [ ] Document prompt quality as benchmark dimension
- [ ] Update benchmark schema to include `promptQuality` field

## Notes

- PopKit templates help users write better issues
- This is a feature, not a bug
- But it means we need to test with BOTH quality levels
- Real value proposition: "PopKit works with messy inputs AND structured ones"
