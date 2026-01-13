# PopKit Agent Routing Guide

## Table of Contents

1. [Overview](#overview)
2. [The Tier System](#the-tier-system)
3. [Routing Mechanisms](#routing-mechanisms)
4. [Confidence Scoring](#confidence-scoring)
5. [Agent Selection Flow](#agent-selection-flow)
6. [Routing Examples](#routing-examples)
7. [Power Mode Orchestration](#power-mode-orchestration)
8. [Troubleshooting](#troubleshooting)
9. [Configuration Reference](#configuration-reference)

---

## Overview

PopKit uses a sophisticated **two-tier agent routing system** to intelligently activate specialized agents based on context, keywords, file patterns, and error signatures. This ensures optimal agent selection while minimizing token overhead.

### Key Principles

- **Context-Aware Activation**: Agents load based on user intent and code context
- **Token Efficiency**: Only load agents relevant to the current task
- **Semantic Understanding**: Uses embeddings and pattern matching for intelligent routing
- **Confidence-Based Filtering**: 80+ threshold prevents false positives
- **Tiered Loading**: Always-active core agents + on-demand specialists

### Architecture at a Glance

```
User Request
    ↓
Query Analysis (keywords, files, errors)
    ↓
┌─────────────────────────────────────────┐
│  Tier 1: Always Active (10 agents)     │
│  - Core capabilities available 24/7     │
└─────────────────────────────────────────┘
    ↓
Routing Decision (pattern matching + embeddings)
    ↓
┌─────────────────────────────────────────┐
│  Tier 2: On-Demand (9 agents)          │
│  - Activated by triggers and context    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Feature Workflow (2 agents)            │
│  - Multi-phase feature development      │
└─────────────────────────────────────────┘
```

---

## The Tier System

PopKit organizes agents into three tiers to optimize context usage and ensure relevant expertise is always available.

### Tier 1: Always Active (10 Agents)

These agents are **always loaded** in every session, providing foundational capabilities across all workflows.

| Agent                        | Plugin      | Purpose                    | Trigger Keywords                         | File Patterns              |
| ---------------------------- | ----------- | -------------------------- | ---------------------------------------- | -------------------------- |
| **accessibility-guardian**   | popkit-core | WCAG compliance and a11y   | accessibility, a11y, wcag, aria          | _.tsx, _.jsx, \*.html      |
| **api-designer**             | popkit-core | RESTful and GraphQL design | api, rest, graphql, endpoint, openapi    | _api_.ts, _routes_.ts      |
| **documentation-maintainer** | popkit-core | Documentation sync         | docs, readme, documentation              | \*.md, CLAUDE.md           |
| **migration-specialist**     | popkit-core | System migrations          | migration, upgrade, version, deprecation | package.json, migration*.* |
| **code-reviewer**            | popkit-dev  | Code quality assessment    | review, quality, refactor                | _.ts, _.tsx, _.js, _.jsx   |
| **refactoring-expert**       | popkit-dev  | Code restructuring         | refactor, technical debt, restructure    | _.ts, _.tsx, _.js, _.jsx   |
| **bug-whisperer**            | popkit-ops  | Complex debugging          | bug, error, crash, issue, debugging      | - (error-based)            |
| **performance-optimizer**    | popkit-ops  | Performance tuning         | slow, performance, optimize, bottleneck  | - (semantic)               |
| **security-auditor**         | popkit-ops  | Security analysis          | security, auth, vulnerability, xss, sql  | _auth_.ts, _security_.\*   |
| **test-writer-fixer**        | popkit-ops  | Test creation and fixes    | test, spec, coverage, assertion          | _.test._, _.spec._         |

**Why Always Active?**

- Core skills needed across ALL projects (code review, testing, debugging)
- Minimal token overhead (baseline ~15.3k tokens after optimization)
- Immediate response without activation delay
- Cover 90% of common development tasks

### Tier 2: On-Demand (9 Agents)

These **specialized agents activate only when triggered** by specific keywords, file patterns, or error signatures.

| Agent                    | Plugin          | Purpose                   | Trigger Keywords                  | File Patterns                   | Token Cost |
| ------------------------ | --------------- | ------------------------- | --------------------------------- | ------------------------------- | ---------- |
| **bundle-analyzer**      | popkit-core     | Bundle size optimization  | bundle, webpack, vite, build size | webpack.config._, vite.config._ | ~0.3k      |
| **dead-code-eliminator** | popkit-core     | Unused code removal       | dead code, unused, tree shaking   | -                               | ~0.3k      |
| **feature-prioritizer**  | popkit-core     | Backlog management        | prioritize, backlog, roadmap      | -                               | ~0.3k      |
| **meta-agent**           | popkit-core     | Agent generator           | create agent, custom agent        | AGENT.md                        | ~0.3k      |
| **power-coordinator**    | popkit-core     | Multi-agent orchestration | `/popkit-core:power`              | power-mode/\*.json              | ~0.3k      |
| **rapid-prototyper**     | popkit-dev      | Quick prototyping         | prototype, mockup, spike          | -                               | ~0.3k      |
| **deployment-validator** | popkit-ops      | Deployment validation     | deploy, release, production       | \*.yml (CI/CD)                  | ~0.3k      |
| **rollback-specialist**  | popkit-ops      | Rollback operations       | rollback, revert deployment       | -                               | ~0.3k      |
| **researcher**           | popkit-research | Web research and analysis | research, investigate, find docs  | -                               | ~0.3k      |

**Why On-Demand?**

- Specialized skills not needed for every task
- Reduces baseline token usage by 87.5% (2.4k → 0.3k tokens)
- Activates instantly when needed via keyword or semantic search
- Each agent loads only ~300 tokens when triggered

### Feature Workflow (2 Agents)

These agents participate in the **7-phase feature development workflow** (`/popkit:feature-dev`).

| Agent              | Plugin     | Purpose               | Phase                 |
| ------------------ | ---------- | --------------------- | --------------------- |
| **code-explorer**  | popkit-dev | Codebase exploration  | Phase 2: Exploration  |
| **code-architect** | popkit-dev | Architecture planning | Phase 4: Architecture |

**Workflow Phases:**

1. **Discovery** - Requirements gathering
2. **Exploration** - code-explorer analyzes codebase
3. **Questions** - Clarification
4. **Architecture** - code-architect designs solution
5. **Implementation** - Implementation
6. **Review** - code-reviewer validates
7. **Summary** - Documentation

---

## Routing Mechanisms

PopKit uses **four complementary mechanisms** to route requests to the right agents.

### 1. Keyword Matching

The simplest routing mechanism - agents activate when specific keywords appear in user messages.

**Example Agent: bug-whisperer**

```yaml
keywords:
  - bug
  - error
  - crash
  - issue
  - debugging
  - trace
  - exception
```

**Example:**

```
User: "There's a bug in the login form"
       ^^^
PopKit → Activates bug-whisperer (keyword match)
```

### 2. File Pattern Matching

Agents activate when working with specific file types or patterns.

**Example Agent: test-writer-fixer**

```yaml
file_patterns:
  - "*.test.ts"
  - "*.test.js"
  - "*.spec.ts"
  - "*.spec.js"
  - "**/__tests__/**"
  - "**/tests/**"
```

**Example:**

```
User: "Review src/auth/login.test.ts"
                        ^^^^^
PopKit → Activates test-writer-fixer (file pattern match)
```

### 3. Error Pattern Matching

Agents activate when specific error types or stack traces are mentioned.

**Example Agent: security-auditor**

```yaml
error_patterns:
  - "SecurityError"
  - "Unauthorized"
  - "CORS"
  - "SQL injection"
  - "XSS"
  - "CSRF"
```

**Example Agent: bug-whisperer**

```yaml
error_patterns:
  - "TypeError"
  - "ReferenceError"
  - "Cannot read property"
  - "undefined is not"
  - "null reference"
```

**Example Agent: performance-optimizer**

```yaml
error_patterns:
  - "Maximum call stack"
  - "Out of memory"
  - "Timeout exceeded"
  - "429 Too Many Requests"
```

**Examples:**

```
User: "Getting CORS errors on API calls"
                ^^^^
PopKit → Activates security-auditor (CORS pattern)

User: "TypeError: Cannot read property 'map' of undefined"
       ^^^^^^^^^
PopKit → Activates bug-whisperer (TypeError pattern)

User: "Query timeout after 30 seconds"
              ^^^^^^^
PopKit → Activates performance-optimizer (timeout pattern)
```

### 4. Semantic Embeddings (Enhanced)

Uses **Voyage AI embeddings** to understand intent beyond keywords. Requires `VOYAGE_API_KEY`.

**How It Works:**

1. User query is embedded (vector representation)
2. Agent descriptions are pre-embedded
3. Cosine similarity ranks relevance
4. Top 10 agents are loaded (always includes Tier 1)

**Example:**

```
User: "The app is slow when scrolling large lists"
      (no direct keyword match)

Embedding Analysis:
- "slow" → performance-related
- "scrolling large lists" → rendering optimization

PopKit → Activates performance-optimizer (semantic match)
```

**Configuration:**

```bash
# Enable semantic routing
export VOYAGE_API_KEY="your-key-here"

# Generate embeddings (one-time)
/popkit-core:project embed
```

---

## Confidence Scoring

PopKit uses a **confidence-based filtering system** to reduce noise and false positives. This is most prominent in the **code-reviewer** agent.

### The 80+ Threshold

Only issues with **80+ confidence** are reported to the user. This prevents low-quality suggestions from cluttering the output.

### Confidence Levels

| Score Range | Meaning               | Action             |
| ----------- | --------------------- | ------------------ |
| **0-25**    | Likely false positive | Skip entirely      |
| **26-49**   | Low confidence        | Internal note only |
| **50-74**   | Moderate confidence   | Note for context   |
| **75-79**   | High confidence       | Consider reporting |
| **80-100**  | Certain / Critical    | Always report      |

### Example: Code Review Filtering

```typescript
// Issue detected: Missing error boundary
// Confidence: 95 → REPORT ✅

// Issue detected: Variable name could be clearer
// Confidence: 60 → SKIP (below threshold)

// Issue detected: SQL injection risk
// Confidence: 100 → REPORT ✅ + ESCALATE
```

### Benefits of Confidence Filtering

1. **Reduces Noise**: Filters out ~30-40% of low-value suggestions
2. **Builds Trust**: Users see only high-quality findings
3. **Saves Time**: No need to evaluate questionable issues
4. **Focuses Attention**: Critical issues stand out

### Adjusting Thresholds

You can override the default threshold in agent frontmatter:

```yaml
# In AGENT.md
confidence_threshold: 75 # Lower threshold for this agent
```

---

## Agent Selection Flow

Here's the complete decision tree for how PopKit selects and activates agents:

```
                    ┌─────────────────────────────────────┐
                    │     USER REQUEST RECEIVED           │
                    │  "Fix bug in login.test.ts"         │
                    └──────────────┬──────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 1: LOAD TIER 1 AGENTS (ALWAYS ACTIVE)                          │
│                                                                      │
│ ✓ accessibility-guardian    ✓ bug-whisperer                         │
│ ✓ api-designer              ✓ performance-optimizer                 │
│ ✓ documentation-maintainer  ✓ security-auditor                      │
│ ✓ migration-specialist      ✓ test-writer-fixer                     │
│ ✓ code-reviewer             ✓ refactoring-expert                    │
│                                                                      │
│ Token Cost: ~15.3k (baseline)                                        │
└──────────────────────────────┬───────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 2: ANALYZE REQUEST                                             │
│                                                                      │
│ ┌────────────────┐  ┌─────────────────┐  ┌────────────────────┐    │
│ │ Keywords       │  │ File Patterns   │  │ Error Patterns     │    │
│ ├────────────────┤  ├─────────────────┤  ├────────────────────┤    │
│ │ "bug" ✓        │  │ *.test.ts ✓     │  │ TypeError? ✗       │    │
│ │ "login"        │  │                 │  │ SecurityError? ✗   │    │
│ │ "fix"          │  │                 │  │                    │    │
│ └────────────────┘  └─────────────────┘  └────────────────────┘    │
└──────────────────────────────┬───────────────────────────────────────┘
                               ↓
                    ┌──────────┴───────────┐
                    ↓                      ↓
        ┌───────────────────────┐  ┌───────────────────────┐
        │  KEYWORD MATCH?       │  │  FILE PATTERN MATCH?  │
        │  "bug" → YES ✓        │  │  *.test.ts → YES ✓    │
        └───────────┬───────────┘  └───────────┬───────────┘
                    │                           │
                    ↓                           ↓
        ┌───────────────────────┐  ┌───────────────────────┐
        │  bug-whisperer        │  │  test-writer-fixer    │
        │  (Tier 1 - loaded)    │  │  (Tier 1 - loaded)    │
        └───────────────────────┘  └───────────────────────┘
                    │                           │
                    └───────────┬───────────────┘
                                ↓
        ┌────────────────────────────────────────────────┐
        │  CHECK FOR TIER 2 TRIGGERS                     │
        │  "bundle"? ✗  "deploy"? ✗  "research"? ✗       │
        │  No Tier 2 agents needed                       │
        └────────────────┬───────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 3: SEMANTIC FALLBACK (if VOYAGE_API_KEY set)                   │
│                                                                      │
│ Query: "Fix bug in login.test.ts"                                   │
│   ↓ Embed with Voyage AI                                            │
│ Vector: [0.234, -0.521, 0.873, ...]                                 │
│   ↓ Compare to agent embeddings                                     │
│ Relevance Scores:                                                    │
│   - test-writer-fixer: 0.92 (already loaded)                        │
│   - bug-whisperer: 0.89 (already loaded)                            │
│   - code-reviewer: 0.75 (already loaded)                            │
│   - security-auditor: 0.45 (already loaded)                         │
│                                                                      │
│ Result: No additional agents needed (top matches already active)    │
└──────────────────────────────┬───────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 4: EXECUTE WITH ACTIVE AGENT POOL                              │
│                                                                      │
│ Primary Agent: test-writer-fixer                                    │
│   - Reads login.test.ts                                             │
│   - Identifies failing assertions                                   │
│   - Proposes fixes                                                  │
│                                                                      │
│ Supporting Agent: bug-whisperer                                     │
│   - Analyzes test failure root cause                                │
│   - Checks if bug is in test or implementation                      │
│                                                                      │
│ Power Mode: PUSH/PULL Insights                                      │
│   ↑ test-writer: "Found assertion expecting wrong value" [test]     │
│   ↑ bug-whisperer: "Implementation correct, test needs update" [bug] │
└──────────────────────────────┬───────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 5: APPLY CONFIDENCE FILTERING                                  │
│                                                                      │
│ Issue 1: "Test assertion expects 200, should be 201 Created"        │
│   Confidence: 95 → REPORT ✓                                         │
│                                                                      │
│ Issue 2: "Consider adding more edge case tests"                     │
│   Confidence: 60 → SKIP (below 80 threshold)                        │
│                                                                      │
│ Issue 3: "Missing test for empty password validation"               │
│   Confidence: 85 → REPORT ✓                                         │
│                                                                      │
│ Final Output: 2 high-confidence issues reported                     │
└──────────────────────────────────────────────────────────────────────┘
                               ↓
                    ┌──────────────────────┐
                    │   RESPONSE TO USER   │
                    │   - 2 issues found   │
                    │   - Fixes proposed   │
                    └──────────────────────┘
```

### Routing Decision Matrix

Quick reference for common scenarios:

| Input                      | Keywords           | Files      | Errors    | Tier 1 Agents                    | Tier 2 Agents        |
| -------------------------- | ------------------ | ---------- | --------- | -------------------------------- | -------------------- |
| "Fix TypeError in auth.ts" | bug                | auth.ts    | TypeError | bug-whisperer, security-auditor  | -                    |
| "Optimize bundle size"     | bundle, optimize   | -          | -         | performance-optimizer            | bundle-analyzer      |
| "Review login.test.ts"     | review, test       | \*.test.ts | -         | code-reviewer, test-writer-fixer | -                    |
| "Deploy to production"     | deploy, production | -          | -         | security-auditor                 | deployment-validator |
| "Research GraphQL caching" | research, GraphQL  | -          | -         | api-designer                     | researcher           |

### Decision Examples

**Scenario 1: Bug Report**

```
Input: "There's a TypeError when clicking the login button"

Analysis:
- Keyword: "TypeError" → bug-whisperer (Tier 1)
- Keyword: "button" → accessibility-guardian (Tier 1)
- File: None specified

Result: bug-whisperer takes lead, accessibility-guardian assists
```

**Scenario 2: Test File Edit**

```
Input: "Update src/auth/login.test.ts to cover new validation"

Analysis:
- File pattern: "*.test.ts" → test-writer-fixer (Tier 1)
- Keyword: "validation" → security-auditor (Tier 1)
- File: "auth/login.test.ts" → security context

Result: test-writer-fixer takes lead, security-auditor reviews
```

**Scenario 3: Performance Issue**

```
Input: "The dashboard is slow when rendering 1000+ rows"

Analysis:
- Keyword: "slow" → performance-optimizer (Tier 1)
- Keyword: "rendering" → performance context
- Semantic: "1000+ rows" → bundle-analyzer (Tier 2)

Result: performance-optimizer + bundle-analyzer collaboration
```

**Scenario 4: Deployment**

```
Input: "Need to deploy v2.1.0 to production"

Analysis:
- Keyword: "deploy" → deployment-validator (Tier 2)
- Keyword: "production" → security-auditor (Tier 1)
- Context: Version release

Result: deployment-validator activated, security-auditor reviews
```

---

## Routing Examples

### Example 1: Bug Report Routing

**User Request:**

```
"Getting a TypeError: Cannot read property 'map' of undefined
 in src/components/UserList.tsx when data is loading"
```

**Routing Analysis:**

1. **Keyword Detection:**
   - "TypeError" → bug-whisperer (Tier 1) ✅
   - "undefined" → bug-whisperer (Tier 1) ✅
   - "components" → code-reviewer (Tier 1) ✅

2. **File Pattern Detection:**
   - "UserList.tsx" → React component
   - No direct file pattern trigger

3. **Error Pattern Detection:**
   - "TypeError" → bug-whisperer ✅
   - "Cannot read property" → Common null reference

4. **Semantic Understanding:**
   - "data is loading" → async/race condition
   - "map of undefined" → missing null check

**Agents Activated:**

- **bug-whisperer** (Primary) - Tier 1
- **code-reviewer** (Support) - Tier 1

**Workflow:**

1. bug-whisperer investigates TypeError root cause
2. code-reviewer suggests defensive coding patterns
3. test-writer-fixer proposes test to catch regression

---

### Example 2: Test Coverage Request

**User Request:**

```
"Add tests to src/api/auth.test.ts for the new password reset flow"
```

**Routing Analysis:**

1. **Keyword Detection:**
   - "tests" → test-writer-fixer (Tier 1) ✅
   - "password" → security-auditor (Tier 1) ✅

2. **File Pattern Detection:**
   - "auth.test.ts" → test-writer-fixer (Tier 1) ✅

3. **Domain Context:**
   - "auth" → security-auditor (Tier 1) ✅
   - "password reset" → security-critical feature

**Agents Activated:**

- **test-writer-fixer** (Primary) - Tier 1
- **security-auditor** (Support) - Tier 1

**Workflow:**

1. test-writer-fixer creates test structure
2. security-auditor reviews for security test coverage
3. code-reviewer validates test quality

---

### Example 3: Performance Optimization

**User Request:**

```
"The app bundle is 5MB and initial load takes 8 seconds.
 Need to optimize bundle size."
```

**Routing Analysis:**

1. **Keyword Detection:**
   - "bundle" → bundle-analyzer (Tier 2) ✅
   - "optimize" → performance-optimizer (Tier 1) ✅
   - "load" → performance-optimizer (Tier 1) ✅

2. **Metric Detection:**
   - "5MB" → Large bundle size
   - "8 seconds" → Slow load time

3. **Semantic Understanding:**
   - "initial load" → Code splitting opportunity
   - "bundle size" → Tree shaking, compression

**Agents Activated:**

- **bundle-analyzer** (Primary) - Tier 2 🔥
- **performance-optimizer** (Support) - Tier 1
- **dead-code-eliminator** (Support) - Tier 2 🔥

**Workflow:**

1. bundle-analyzer analyzes webpack/vite configuration
2. dead-code-eliminator identifies unused dependencies
3. performance-optimizer measures before/after metrics

---

### Example 4: Security Audit

**User Request:**

```
"Getting CORS errors when calling /api/users from localhost:3000"
```

**Routing Analysis:**

1. **Keyword Detection:**
   - "CORS" → security-auditor (Tier 1) ✅
   - "errors" → bug-whisperer (Tier 1) ✅

2. **Error Pattern Detection:**
   - "CORS errors" → security-auditor (Tier 1) ✅

3. **Context Detection:**
   - "/api/users" → API endpoint
   - "localhost:3000" → Development environment

**Agents Activated:**

- **security-auditor** (Primary) - Tier 1
- **api-designer** (Support) - Tier 1
- **bug-whisperer** (Support) - Tier 1

**Workflow:**

1. security-auditor analyzes CORS configuration
2. api-designer reviews API security headers
3. bug-whisperer confirms fix resolves error

---

### Example 5: Feature Development

**User Request:**

```
"/popkit:feature-dev 'Add real-time notifications using WebSockets'"
```

**Routing Analysis:**

1. **Command Detection:**
   - `/popkit:feature-dev` → Feature workflow ✅

2. **Keyword Detection:**
   - "real-time" → performance-optimizer (Tier 1) ✅
   - "WebSockets" → api-designer (Tier 1) ✅

3. **Workflow Phases:**
   - Phase 1: Discovery
   - Phase 2: Exploration → code-explorer (Feature Workflow) 🔥
   - Phase 3: Questions
   - Phase 4: Architecture → code-architect (Feature Workflow) 🔥
   - Phase 5: Implementation
   - Phase 6: Review → code-reviewer (Tier 1)
   - Phase 7: Summary

**Agents Activated (Sequential):**

1. **code-explorer** (Phase 2)
2. **code-architect** (Phase 4)
3. **code-reviewer** (Phase 6)
4. **test-writer-fixer** (Phase 6)
5. **security-auditor** (Phase 6) - if applicable

**Workflow:**
Multi-phase orchestration with sync barriers between phases.

---

## Power Mode Orchestration

Power Mode enables **parallel multi-agent workflows** with sophisticated coordination.

### Modes of Operation

| Mode             | Agents | Setup                      | Use Case                       |
| ---------------- | ------ | -------------------------- | ------------------------------ |
| **Native Async** | 5-10   | Zero (Claude Code 2.0.64+) | Default mode, background tasks |
| **File Mode**    | 2      | Zero                       | Fallback, sequential workflows |

### Check-In Protocol

Agents participate in **check-ins every 5 tool calls** to share insights and coordinate.

**Check-In Format:**

```
🔌 api-designer T:22 P:70% | Design: 12 endpoints with OpenAPI spec
```

Where:

- **T**: Total tool calls
- **P**: Progress percentage
- **Phase**: Current phase name
- **Focus**: Current task description

### PUSH/PULL Pattern

Agents communicate via tagged insights:

**PUSH (Outgoing):**

```
↑ "Found SQL injection risk in src/api/users.ts:45" [security, critical]
↑ "moment.js (300kb) → date-fns (20kb) saves 280kb" [bundle, optimization]
```

**PULL (Incoming):**

```
Agents subscribe to tags:
- security-auditor listens for [security]
- bundle-analyzer listens for [bundle, performance]
- test-writer-fixer listens for [test, coverage]
```

### Sync Barriers

Agents can **wait for dependencies** before proceeding:

```yaml
sync_barriers:
  - phase: "architecture"
    wait_for: ["code-explorer"]
    timeout: 120 # seconds

  - phase: "review"
    wait_for: ["security-auditor", "test-writer-fixer"]
    timeout: 180
```

### Plan Mode (Claude Code 2.0.70+)

Agents present **implementation plans for approval** before executing:

```
┌─────────────────────────────────────────────────────────┐
│ 🎯 code-reviewer IMPLEMENTATION PLAN                    │
├─────────────────────────────────────────────────────────┤
│ Goal: Review src/auth/login.ts for security issues     │
│                                                          │
│ Steps:                                                   │
│ 1. Scan for SQL injection risks                        │
│ 2. Check password hashing implementation               │
│ 3. Verify session management                            │
│ 4. Report findings with 80+ confidence                  │
│                                                          │
│ Estimated: 15 minutes, 8k tokens                        │
└─────────────────────────────────────────────────────────┘

Approve plan? [Yes / No / Modify]
```

**Configuration:**

```json
// power-mode/config.json
"plan_mode": {
  "enabled": true,
  "timeout_seconds": 300,
  "auto_approve_on_timeout": false
}
```

---

## Troubleshooting

### Issue: Wrong Agent Activated

**Symptom:** Agent doesn't match the task (e.g., bundle-analyzer for a test issue)

**Diagnosis:**

1. Check if keywords are ambiguous
2. Verify file patterns in request
3. Review semantic embeddings (if enabled)

**Solution:**

```bash
# Regenerate embeddings
/popkit-core:project embed

# Or explicitly specify agent
"@bug-whisperer investigate this TypeError"
```

---

### Issue: No Tier 2 Agent Loaded

**Symptom:** Expected specialist agent didn't activate

**Diagnosis:**

1. Tier 2 agents require trigger keywords
2. Semantic routing may not be enabled

**Solution:**

```bash
# Check if VOYAGE_API_KEY is set
echo $VOYAGE_API_KEY

# If not set, use explicit keywords
"Need bundle analysis" → bundle-analyzer activates
```

---

### Issue: Too Many Low-Confidence Issues

**Symptom:** code-reviewer reports 20+ minor issues below 80 threshold

**Diagnosis:**
Code-reviewer circuit breaker should prevent this, but if it happens:

**Solution:**

1. code-reviewer automatically stops after 10 low-confidence issues
2. Refocuses on high-priority findings only
3. Reports filtered count for transparency

---

### Issue: Agent Routing Loop

**Symptom:** Multiple agents activate and conflict

**Diagnosis:**
Power Mode coordination issue or overlapping triggers

**Solution:**

```bash
# Check Power Mode status
/popkit-core:power status

# Stop Power Mode if stuck
/popkit-core:power stop

# Restart with specific agent
"@test-writer-fixer fix this test"
```

---

### Issue: Semantic Routing Not Working

**Symptom:** Agents don't activate for semantic queries

**Diagnosis:**

1. VOYAGE_API_KEY not set
2. Embeddings not generated

**Solution:**

```bash
# Set API key
export VOYAGE_API_KEY="your-key-here"

# Generate embeddings (one-time)
/popkit-core:project embed

# Verify generation
ls .claude/popkit/embeddings/
```

---

## Configuration Reference

### Agent Routing Configuration

Each agent's routing rules are defined in its **AGENT.md frontmatter**:

```yaml
---
name: agent-name
description: "Agent description used for semantic matching"
tools: Read, Write, Edit, Bash
output_style: agent-output-style
model: inherit
version: 1.0.0
tier: tier-1-always-active # or tier-2-on-demand
keywords: # Keyword triggers
  - keyword1
  - keyword2
file_patterns: # File pattern triggers
  - "*.test.ts"
  - "**/__tests__/**"
error_patterns: # Error signature triggers
  - "TypeError"
  - "SecurityError"
confidence_threshold: 80 # Minimum confidence to report
---
```

### Power Mode Configuration

Located in `packages/popkit-core/power-mode/config.json`:

```json
{
  "native": {
    "enabled": true,
    "max_parallel_agents": 5,
    "poll_interval_ms": 500
  },
  "intervals": {
    "checkin_every_n_tools": 5,
    "heartbeat_seconds": 15,
    "sync_timeout_seconds": 120
  },
  "guardrails": {
    "human_required_actions": ["delete_production_data", "modify_security_config"]
  }
}
```

### Semantic Routing Configuration

Enable semantic agent selection via embeddings:

```bash
# 1. Set Voyage AI API key
export VOYAGE_API_KEY="your-key-here"

# 2. Generate embeddings (one-time setup)
/popkit-core:project embed

# 3. Embeddings stored in:
# .claude/popkit/embeddings/agents.json
```

**Embedding Process:**

1. Agent descriptions are embedded using Voyage AI
2. User query is embedded on each request
3. Cosine similarity ranks agent relevance
4. Top 10 agents loaded (always includes Tier 1)

---

## Quick Reference Tables

### Common Routing Scenarios

| User Request                          | Expected Agent(s)                      | Routing Mechanism                    | Tier   |
| ------------------------------------- | -------------------------------------- | ------------------------------------ | ------ |
| "Fix bug in UserList component"       | bug-whisperer                          | Keyword: "bug"                       | Tier 1 |
| "Review src/auth/login.test.ts"       | test-writer-fixer, code-reviewer       | File: \*.test.ts + Keyword: "review" | Tier 1 |
| "TypeError in API call"               | bug-whisperer                          | Error: "TypeError"                   | Tier 1 |
| "Optimize bundle size for production" | bundle-analyzer, performance-optimizer | Keyword: "bundle"                    | Tier 2 |
| "Deploy v2.0 to production"           | deployment-validator, security-auditor | Keyword: "deploy"                    | Tier 2 |
| "Research GraphQL best practices"     | researcher, api-designer               | Keyword: "research"                  | Tier 2 |
| "Add accessibility to modal"          | accessibility-guardian                 | Keyword: "accessibility"             | Tier 1 |
| "Refactor legacy API endpoints"       | refactoring-expert, api-designer       | Keyword: "refactor"                  | Tier 1 |

### Error Pattern → Agent Mapping

| Error Pattern             | Agent                 | Tier | Example                                 |
| ------------------------- | --------------------- | ---- | --------------------------------------- |
| TypeError, ReferenceError | bug-whisperer         | 1    | "TypeError: Cannot read property 'map'" |
| SecurityError, CORS, XSS  | security-auditor      | 1    | "CORS policy blocked request"           |
| Timeout, Out of memory    | performance-optimizer | 1    | "Query timeout after 30s"               |
| Test assertion failed     | test-writer-fixer     | 1    | "Expected 200, got 404"                 |
| SQL injection, CSRF       | security-auditor      | 1    | "SQL injection vulnerability detected"  |

### File Pattern → Agent Mapping

| File Pattern                    | Agent                                 | Tier | Example File      |
| ------------------------------- | ------------------------------------- | ---- | ----------------- |
| _.test.ts, _.spec.js            | test-writer-fixer                     | 1    | login.test.ts     |
| _.tsx, _.jsx                    | accessibility-guardian, code-reviewer | 1    | UserList.tsx      |
| _api_.ts, _routes_.ts           | api-designer                          | 1    | api/users.ts      |
| webpack.config._, vite.config._ | bundle-analyzer                       | 2    | webpack.config.js |
| _auth_.ts, _security_.\*        | security-auditor                      | 1    | auth/oauth.ts     |
| \*.md, CLAUDE.md                | documentation-maintainer              | 1    | README.md         |
| package.json                    | migration-specialist                  | 1    | package.json      |

### Confidence Threshold Quick Guide

| Issue Type                    | Typical Confidence | Will Report? |
| ----------------------------- | ------------------ | ------------ |
| SQL injection risk            | 95-100             | Yes ✓        |
| Missing error boundary        | 85-95              | Yes ✓        |
| Type safety issue (any usage) | 80-90              | Yes ✓        |
| Performance bottleneck        | 75-85              | Yes ✓        |
| Variable naming clarity       | 50-70              | No ✗         |
| Subjective style preference   | 20-40              | No ✗         |

---

## Summary

PopKit's agent routing system provides:

1. **Intelligent Activation**: Right agent for the right task
2. **Token Efficiency**: 40.5% reduction in baseline context (25.7k → 15.3k)
3. **Quality Filtering**: 80+ confidence threshold eliminates noise
4. **Scalable Orchestration**: 2-10 agents in parallel via Power Mode
5. **Semantic Understanding**: Beyond keywords with embeddings

**Key Metrics:**

- **Tier 1**: 10 always-active core agents (~15.3k tokens)
- **Tier 2**: 9 on-demand specialists (~0.3k tokens when not loaded)
- **Feature Workflow**: 2 agents for 7-phase development
- **Total**: 21 specialized agents across 4 plugins

**Performance Impact:**

- Baseline context: 15.3k tokens (Tier 1 only)
- With 3 Tier 2 agents: ~16.2k tokens
- Maximum (all agents): ~18k tokens
- Savings vs. always loading all: 40.5% reduction

**Next Steps:**

- Review [Package README](../packages/popkit-core/README.md) for agent catalog
- Explore [Power Mode Configuration](../packages/popkit-core/power-mode/config.json)
- Test routing with `/popkit-ops:debug routing` (if available)
- Enable semantic routing with `/popkit-core:project embed`
- Read agent definitions in `packages/popkit-*/agents/*/AGENT.md`
