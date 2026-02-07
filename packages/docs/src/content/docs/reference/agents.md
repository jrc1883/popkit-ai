---
title: Agents Reference
description: Complete reference for all 23 PopKit specialized agents
---

# Agents Reference

PopKit provides 23 specialized AI agents across 4 plugins. Agents are organized into tiers based on activation frequency.

## Agent Tiers

| Tier | Description | Activation |
|------|-------------|------------|
| **Tier 1: Always Active** | Core agents for common tasks | Automatically available in every session |
| **Tier 2: On-Demand** | Specialized agents for specific needs | Activated when relevant tasks are detected |
| **Feature Workflow** | Development phase agents | Used during feature development phases |

---

## popkit-core (9 agents)

Foundation agents for accessibility, API design, documentation, and orchestration.

### Tier 1: Always Active

#### accessibility-guardian

**Description:** Ensures web applications meet WCAG 2.1 AA/AAA compliance. Use when auditing accessibility, fixing a11y violations, or implementing inclusive design patterns.

**Tools:** Read, Grep, Glob, WebFetch

---

#### api-designer

**Description:** Expert in RESTful and GraphQL API design patterns. Use when designing new APIs, restructuring existing endpoints, or when you need guidance on API best practices, versioning, and integration patterns.

**Tools:** Read, Write, Edit, MultiEdit, Grep, WebFetch

---

#### documentation-maintainer

**Description:** Keeps documentation synchronized with codebase changes. Use after major feature updates, API changes, or when documentation drift is detected.

**Tools:** Read, Write, Edit, MultiEdit, Grep, Glob, WebFetch

---

#### migration-specialist

**Description:** Expert in planning and executing complex system migrations including database migrations, API version transitions, framework upgrades, and cloud migrations. Minimizes downtime and ensures data integrity.

**Tools:** Read, Write, Edit, MultiEdit, Grep, Glob, Bash (database migration tools, version management, testing, backup verification)

---

### Tier 2: On-Demand

#### bundle-analyzer

**Description:** Analyzes and optimizes JavaScript bundle sizes for web applications. Use for identifying bloated dependencies, implementing code splitting, and reducing bundle size.

**Tools:** Read, Write, Edit, MultiEdit, Grep, Glob, Bash (webpack-bundle-analyzer, vite-bundle-visualizer, source-map-explorer, build tools, dependency analysis)

---

#### dead-code-eliminator

**Description:** Intelligent dead code detection and elimination using advanced static analysis, dependency tracking, and safe removal strategies. Use for codebase cleanup, bundle size optimization, and maintainability improvement.

**Tools:** Read, Write, Edit, MultiEdit, Grep, Glob, Bash (ts-unused-exports, unimported, depcheck, knip, testing, type checking, linting)

---

#### feature-prioritizer

**Description:** Strategic backlog management and feature prioritization specialist. Use when making product roadmap decisions, prioritizing features, or managing development backlogs.

**Tools:** Read, Grep, Glob, Write, WebFetch

---

#### meta-agent

**Description:** Generates new, complete Claude Code agent configuration files from user descriptions. Use proactively when creating custom agents for specific project needs.

**Tools:** Write, WebFetch, MultiEdit, Read, Grep

---

#### power-coordinator

**Description:** Orchestrates multi-agent collaboration in Power Mode. Use when coordinating parallel agents working on complex tasks via Redis pub/sub mesh network.

**Tools:** Read, Write, Bash (redis-cli, system monitoring), Task, TodoWrite

---

## popkit-dev (7 agents)

Development workflow agents for code exploration, architecture, review, and conflict resolution.

### Feature Workflow

#### code-architect

**Description:** Designs feature architectures and implementation blueprints based on codebase patterns. Use during architecture phase when multiple implementation approaches exist and trade-offs need evaluation.

**Tools:** Read, Grep, Glob, Write

---

#### code-explorer

**Description:** Deeply analyzes existing codebase features by tracing execution paths, data flow, and dependencies. Use during exploration phase of feature development or when understanding unfamiliar code.

**Tools:** Read, Grep, Glob

---

### Tier 1: Always Active

#### code-reviewer

**Description:** Performs comprehensive code reviews focusing on TypeScript, React, and Node.js best practices. Use after implementing significant features or when code quality assessment is needed.

**Tools:** Read, Grep, Glob, Edit

---

#### refactoring-expert

**Description:** Code restructuring specialist focused on improving quality, maintainability, and performance without changing external behavior. Use for code smell detection, design pattern application, and systematic codebase improvements.

**Tools:** Read, Edit, MultiEdit, Grep, Glob, Bash (testing, linting, type checking)

---

### Tier 2: On-Demand

#### merge-conflict-resolver

**Description:** AI-powered merge conflict resolution with complexity-based prioritization and architectural intelligence. Detects conflicts, analyzes complexity, prioritizes resolution order, proposes intelligent fixes with reasoning, validates with tests.

**Triggers:** "merge conflict", "resolve conflicts", "fix merge issues", "git conflicts"

**Tools:** Read, Write, Edit, Bash (git operations, testing), Task, TodoWrite, AskUserQuestion

---

#### prd-parser

**Description:** Transforms Product Requirements Documents into structured, actionable tasks with automatic complexity analysis and technology research. Parses markdown PRDs, extracts features, scores complexity, and generates implementation roadmap.

**Triggers:** "parse this PRD", "analyze requirements document", "break down this spec", "turn this into tasks"

**Tools:** Read, Write, Grep, Glob, TodoWrite, WebSearch, Bash (gh, python)

---

#### rapid-prototyper

**Description:** Fast MVP development specialist for quick proof-of-concept implementations. Use when building prototypes, validating ideas, or creating minimal viable features quickly.

**Tools:** Read, Write, Edit, MultiEdit, Grep, Glob, Bash (npm, dev servers, testing, build), WebFetch

---

## popkit-ops (6 agents)

Operations agents for debugging, performance, security, testing, and deployment.

### Tier 1: Always Active

#### bug-whisperer

**Description:** Expert debugging specialist for complex issues. Use when facing hard-to-reproduce bugs, performance anomalies, or mysterious system behaviors that require deep investigation and systematic troubleshooting.

**Tools:** Read, Grep, Edit, MultiEdit, Bash (debugging, testing, log inspection, git operations), WebFetch

---

#### performance-optimizer

**Description:** Elite performance engineering specialist that analyzes, diagnoses, and optimizes web application performance across all metrics. Use for performance audits, bottleneck identification, and optimization strategies.

**Tools:** Read, Grep, Glob, Bash (performance testing, build analysis, profiling, load testing, lighthouse), WebFetch

---

#### security-auditor

**Description:** Comprehensive security specialist for vulnerability assessment, threat analysis, and defensive security implementation. Use when auditing code, analyzing security risks, or implementing security measures.

**Tools:** Read, Grep, Glob, Bash (security scanning, dependency audits, linting), WebFetch

---

#### test-writer-fixer

**Description:** Comprehensive testing specialist for writing, fixing, and optimizing test suites. Use when implementing tests, debugging test failures, or improving test coverage.

**Tools:** Read, Write, Edit, MultiEdit, Grep, Glob, Bash (testing frameworks, coverage analysis)

**Hooks:** PostToolUse auto-run-tests

---

### Tier 2: On-Demand

#### deployment-validator

**Description:** Ensures safe, reliable deployments through comprehensive validation and verification. Use for pre-deployment checks, smoke testing, and deployment verification.

**Tools:** Read, Grep, Write, Bash (build, CI/CD workflows, container inspection, Kubernetes, health checks), WebFetch, Task

---

#### rollback-specialist

**Description:** Expert in rapid recovery procedures and safe rollback operations. Use when deployments fail, production issues arise, or emergency recovery is needed.

**Tools:** Read, Write, Edit, Bash (git rollback, CI/CD, container management, Kubernetes, health verification), WebFetch, Task

---

## popkit-research (1 agent)

Knowledge management agent for codebase analysis and agent discovery.

### Tier 2: On-Demand

#### researcher

**Description:** Meta-researcher that analyzes codebases to identify beneficial agents and development opportunities. Use when discovering what agents would be most helpful for a project or expanding the agent ecosystem.

**Tools:** Read, Grep, Glob, WebFetch, WebSearch, Task

---

## Agent Summary

| Plugin | Tier 1 | Tier 2 | Feature Workflow | Total |
|--------|--------|--------|------------------|-------|
| popkit-core | 4 | 5 | - | 9 |
| popkit-dev | 2 | 3 | 2 | 7 |
| popkit-ops | 4 | 2 | - | 6 |
| popkit-research | - | 1 | - | 1 |
| **Total** | **10** | **11** | **2** | **23** |

## Agent Memory (CC 2.1.33+)

Agents support persistent memory through expertise files stored in `.claude/expertise/<agent-id>/`. Memory includes:

- **Patterns**: Recurring code patterns the agent has observed
- **Preferences**: Project-specific conventions and style guidelines
- **Common Issues**: Frequently encountered problems and their solutions
- **Project Context**: Framework, architecture, and dependency information

Memory is loaded automatically when an agent starts and updated after significant interactions.

## Next Steps

- Learn about [Skills Reference](/reference/skills/)
- Explore [Commands Reference](/reference/commands/)
- Read the [Getting Started Guide](/guides/getting-started/)
