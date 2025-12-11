# PopKit Agents

PopKit uses a tiered agent system to orchestrate Claude Code's capabilities.

## Tier System

| Tier | Description | Count |
|------|-------------|-------|
| **Tier 1: Always-Active** | Core agents always available for routing | 11 |
| **Tier 2: On-Demand** | Specialized agents activated by triggers | 17 |
| **Feature Workflow** | 7-phase development agents | 3 |
| **Assessors** | Self-assessment agents | 6 |

---

## Tier 1: Always-Active Agents

These agents are always available and handle common development tasks.

### code-reviewer
Reviews code for quality, style, and best practices. Uses confidence-based filtering (80+ threshold).

**Triggers:** `review`, `pr`, `lint`, `eslint`, `format`, `style`

### bug-whisperer
Expert debugging specialist for complex issues. Systematic troubleshooting approach.

**Triggers:** `bug`, `error`

### security-auditor
Comprehensive security analysis including vulnerability assessment and threat analysis.

**Triggers:** `security`

### test-writer-fixer
Writes, fixes, and optimizes test suites. Supports Jest, Vitest, pytest, and more.

**Triggers:** `test`

### api-designer
Expert in RESTful and GraphQL API design patterns.

**Triggers:** `api`

### performance-optimizer
Elite performance engineering for web application optimization.

**Triggers:** `performance`, `optimize`, `slow`

### refactoring-expert
Code restructuring specialist focused on improving quality without changing behavior.

**Triggers:** `refactor`, `cleanup`

### documentation-maintainer
Keeps documentation synchronized with codebase changes.

**Triggers:** `docs`

### query-optimizer
Database query optimization for maximum performance.

**Triggers:** `database`, `optimize`, `slow`

### migration-specialist
Expert in database migrations, API transitions, and framework upgrades.

**Triggers:** `migration`, `migrate`

### accessibility-guardian
WCAG 2.1 AA/AAA compliance specialist.

**Triggers:** `accessibility`

---

## Tier 2: On-Demand Agents

Specialized agents activated by specific triggers or commands.

### ai-engineer
ML/AI integration, model development, and intelligent system architecture.

**Triggers:** `ai`

### devops-automator
CI/CD pipelines, cloud infrastructure, and deployment automation.

**Triggers:** `deploy`

### deployment-validator
Pre-deployment checks, smoke testing, and deployment verification.

**Triggers:** `deploy`

### bundle-analyzer
JavaScript bundle size analysis and optimization.

**Triggers:** `performance`

### log-analyzer
Parses and analyzes application logs across distributed systems.

**Triggers:** `logs`, `error`

### rollback-specialist
Rapid recovery procedures and safe rollback operations.

**Triggers:** `rollback`

### backup-coordinator
Comprehensive backup strategies and disaster recovery planning.

**Triggers:** `backup`

### data-integrity
Data consistency validation and anomaly detection.

**Triggers:** `database`

### dead-code-eliminator
Dead code detection and elimination using static analysis.

**Triggers:** `cleanup`

### rapid-prototyper
Fast MVP development and proof-of-concept implementations.

**Triggers:** `prototype`

### feature-prioritizer
Strategic backlog management and feature prioritization.

**Triggers:** `feature`

### user-story-writer
Requirements documentation and user story creation.

**Triggers:** `feature`

### feedback-synthesizer
Analyzes user feedback to extract actionable insights.

### metrics-collector
Telemetry gathering and observability implementation.

**Triggers:** `metrics`

### researcher
Meta-researcher that analyzes codebases to identify opportunities.

### meta-agent
Generates new Claude Code agent configuration files.

### power-coordinator
Orchestrates multi-agent collaboration in Power Mode.

**Triggers:** `power`, `orchestrate`, `coordinate`, `parallel`

---

## Feature Workflow Agents

Used in the 7-phase feature development workflow (`/popkit:dev`).

### code-explorer
**Phase 2: Exploration**

Deeply analyzes existing codebase features by tracing execution paths, data flow, and dependencies.

### code-architect
**Phase 4: Architecture**

Designs feature architectures and implementation blueprints based on codebase patterns.

### code-reviewer
**Phase 6: Review**

Reviews implementation against architecture design with confidence-based filtering.

---

## Assessor Agents

Self-assessment agents for multi-perspective review (`/popkit:assess`).

### anthropic-engineer-assessor
Validates Claude Code compliance, hook protocols, and Anthropic best practices.

### security-auditor-assessor
Identifies security vulnerabilities including command injection and unsafe patterns.

### performance-tester-assessor
Evaluates efficiency including context window usage and token consumption.

### ux-reviewer-assessor
Evaluates user experience including command naming and discoverability.

### technical-architect-assessor
Validates code quality including DRY principles and architectural patterns.

### documentation-auditor-assessor
Validates documentation quality including CLAUDE.md accuracy and examples.

---

## Agent Routing

Agents are automatically routed based on three mechanisms:

### 1. Keyword Routing

| Keywords | Primary Agents |
|----------|---------------|
| `bug`, `error` | bug-whisperer, test-writer-fixer |
| `security` | security-auditor |
| `performance`, `optimize` | performance-optimizer |
| `test` | test-writer-fixer |
| `api` | api-designer |
| `refactor` | refactoring-expert |
| `docs` | documentation-maintainer |
| `database` | query-optimizer |
| `migration` | migration-specialist |
| `deploy` | deployment-validator, devops-automator |
| `power`, `coordinate` | power-coordinator |

### 2. File Pattern Routing

| Pattern | Agents |
|---------|--------|
| `*.test.ts`, `*.spec.ts` | test-writer-fixer |
| `*.tsx` | code-reviewer, accessibility-guardian |
| `*.sql` | query-optimizer |
| `*.md` | documentation-maintainer |
| `package.json` | bundle-analyzer |
| `Dockerfile` | devops-automator |
| `.env*` | security-auditor |
| `eslint.config.*` | code-reviewer |

### 3. Error Pattern Routing

| Error Type | Agents |
|------------|--------|
| TypeError | bug-whisperer |
| SyntaxError | code-reviewer |
| SecurityError | security-auditor |
| PerformanceWarning | performance-optimizer |
| DeprecationWarning | migration-specialist |

---

## Power Mode Integration

In Power Mode, agents can work in parallel:
- Share discoveries via insights
- Coordinate through sync barriers
- Each agent focuses on its specialized area
- Coordinator manages phase transitions

### Example Power Mode Workflow

```
Phase 1: EXPLORE (parallel)
├── code-explorer → Analyzes codebase
├── researcher → Researches best practices
└── code-architect → Reviews structure

Phase 2: DESIGN
└── code-architect → Designs solution

Phase 3: IMPLEMENT (parallel)
├── rapid-prototyper → Implements features
├── test-writer-fixer → Writes tests
└── documentation-maintainer → Updates docs

Phase 4: REVIEW
└── code-reviewer → Reviews all changes
```

---

## Confidence Scoring

Code review uses confidence-based filtering:

| Score | Level | Action |
|-------|-------|--------|
| 90-100 | Critical | Must fix |
| 80-89 | Important | Should fix |
| 50-79 | Noted | Not reported |
| 0-49 | Ignored | False positive |

**Threshold: 80+** - Only issues with 80+ confidence are reported.

---

## Creating Custom Agents

Project-specific agents can be created in `.claude/agents/`:

```
.claude/
└── agents/
    └── my-custom-agent/
        └── AGENT.md
```

Use `/popkit:project generate` to auto-generate agents based on project patterns.

---

## See Also

- [[Commands]] - Command reference
- [[Home]] - Getting started
- [[Contributing]] - How to contribute
