---
name: pop-deploy-validate
description: "Pre-deployment validation - checks build, tests, security, dependencies, and deployment config against target environment. Generates a deployment readiness report with go/no-go recommendation. Use before any deployment execution."
inputs:
  - from: pop-deploy-setup
    field: generated_files
    required: false
  - from: pop-deploy-init
    field: deploy_config
    required: false
  - from: any
    field: target
    required: false
  - from: any
    field: environment
    required: false
outputs:
  - field: validation_report
    type: json
  - field: readiness_score
    type: number
  - field: go_no_go
    type: string
next_skills:
  - pop-deploy-execute
  - pop-deploy-setup
triggers:
  - deploy validate
  - deployment readiness
  - pre-deploy check
  - deployment validation
workflow:
  id: deploy-validate
  name: Deployment Validation Workflow
  version: 1
  description: Comprehensive pre-deployment validation and readiness assessment
  steps:
    - id: load_config
      description: Load deploy.json and determine validation scope
      type: script
      script: scripts/validate_deployment.py
      args: "--action load-config"
      next: scope_decision
    - id: scope_decision
      description: Select validation scope
      type: user_decision
      question: "What level of validation should I run?"
      header: "Scope"
      options:
        - id: quick
          label: "Quick check"
          description: "Config validation and build check only (~30s)"
          next: run_validation
        - id: standard
          label: "Standard (Recommended)"
          description: "Config, build, tests, dependency audit (~2-5min)"
          next: run_validation
        - id: full
          label: "Full validation"
          description: "All checks including security scan and integration tests (~5-15min)"
          next: run_validation
      next_map:
        quick: run_validation
        standard: run_validation
        full: run_validation
    - id: run_validation
      description: Execute validation checks
      type: script
      script: scripts/validate_deployment.py
      args: "--action validate"
      next: review_results
    - id: review_results
      description: Review validation results
      type: user_decision
      question: "Validation complete. How should I proceed?"
      header: "Results"
      options:
        - id: deploy
          label: "Proceed to deploy"
          description: "All checks passed - deploy now"
          next: run_deploy
        - id: fix
          label: "Fix issues"
          description: "Address validation failures first"
          next: complete
        - id: override
          label: "Deploy anyway"
          description: "Override warnings and deploy (not recommended)"
          next: run_deploy
        - id: abort
          label: "Abort"
          description: "Do not deploy"
          next: complete
      next_map:
        deploy: run_deploy
        fix: complete
        override: run_deploy
        abort: complete
    - id: run_deploy
      description: Proceed to deployment execution
      type: skill
      skill: pop-deploy-execute
      next: complete
    - id: complete
      description: Validation workflow finished
      type: terminal
---

# Deploy Validate Skill

Pre-deployment validation and readiness assessment. Ensures everything is in order before deploying.

## Overview

**Trigger:** `/popkit-ops:deploy validate` or before any deployment execution

**Purpose:** Run comprehensive checks against the project and deployment configuration to catch issues before they reach production. Produces a go/no-go recommendation with a readiness score.

## Critical Rules

1. **NEVER skip validation before production deploys** - Validation is mandatory
2. **ALWAYS report ALL failures** - Don't stop at first failure
3. **ALWAYS use AskUserQuestion** for scope and post-validation decisions
4. **Blocking failures must block deployment** - No overriding critical failures
5. **Non-blocking warnings should be surfaced** - Let user decide on warnings

## Required Decision Points

| Step | When              | Decision ID      |
| ---- | ----------------- | ---------------- |
| 1    | Before validation | `scope_level`    |
| 2    | After results     | `proceed_action` |

**Skipping these violates PopKit UX standard.**

## Validation Checks

### Quick Checks (always run)

| Check         | Description                                      | Blocking |
| ------------- | ------------------------------------------------ | -------- |
| Config exists | deploy.json present and valid                    | Yes      |
| Target config | All enabled targets have required fields         | Yes      |
| Version check | Version field present and valid                  | Yes      |
| Git status    | Working directory clean (no uncommitted changes) | Warning  |

### Standard Checks (default)

| Check        | Description                               | Blocking |
| ------------ | ----------------------------------------- | -------- |
| Build        | Project builds successfully               | Yes      |
| Tests        | Test suite passes                         | Yes      |
| Dependencies | No known vulnerable dependencies          | Warning  |
| Lockfile     | Lock file present and up to date          | Warning  |
| ENV vars     | Required environment variables documented | Warning  |

### Full Checks (comprehensive)

| Check         | Description                          | Blocking |
| ------------- | ------------------------------------ | -------- |
| Security scan | Static security analysis             | Warning  |
| License audit | Dependency license compatibility     | Warning  |
| Docker lint   | Dockerfile best practices (hadolint) | Warning  |
| K8s validate  | Kubernetes manifest validation       | Warning  |
| Size check    | Build artifact size within limits    | Warning  |
| Integration   | Integration test suite passes        | Yes      |

## Process

### Step 1: Load Configuration

```bash
python scripts/validate_deployment.py --dir . --action load-config
```

Loads deploy.json and reports current state.

### Step 2: Scope Selection (MANDATORY)

```
Use AskUserQuestion:
- question: "What level of validation should I run?"
- header: "Scope"
- options:
  - "Quick check" - Config and build only (~30s)
  - "Standard (Recommended)" - Config, build, tests, deps (~2-5min)
  - "Full validation" - All checks including security (~5-15min)
```

### Step 3: Run Validation

```bash
python scripts/validate_deployment.py --dir . --action validate --scope standard --target docker
```

### Step 4: Review Results (MANDATORY)

```
Use AskUserQuestion:
- question: "Validation complete. How should I proceed?"
- header: "Results"
- options:
  - "Proceed to deploy" - All passed, deploy now
  - "Fix issues" - Address failures first
  - "Deploy anyway" - Override warnings (not recommended)
  - "Abort" - Do not deploy
```

## Readiness Score

Score is calculated from check results:

| Score | Meaning                    | Recommendation                   |
| ----- | -------------------------- | -------------------------------- |
| 100   | All checks passed          | GO - Deploy                      |
| 80-99 | Passed with warnings       | GO - Deploy with awareness       |
| 60-79 | Some non-blocking failures | CONDITIONAL - Fix warnings first |
| 40-59 | Significant issues         | NO-GO - Fix before deploying     |
| 0-39  | Critical failures          | NO-GO - Blocking issues          |

## Output Format

```
Deployment Validation
=====================
Target: docker (primary)
Scope: standard
Environment: production

Checks:
  [PASS] Config valid
  [PASS] Build succeeds
  [PASS] Tests pass (142/142)
  [WARN] 2 moderate vulnerabilities in dependencies
  [PASS] Lock file up to date
  [WARN] .env.example missing DATABASE_URL

Score: 85/100
Recommendation: GO (with warnings)

Warnings:
  1. npm audit: 2 moderate vulnerabilities (run npm audit fix)
  2. .env.example incomplete: DATABASE_URL not documented

Next: /popkit-ops:deploy execute --target docker
```

## Integration

**Called by:**

- `/popkit-ops:deploy validate` command
- `pop-deploy-setup` workflow (validate step)
- `pop-deploy-execute` workflow (pre-deploy validation)

**Triggers:**

- deployment-validator agent

**Followed by:**

- `pop-deploy-execute` - Execute the deployment
- `pop-deploy-setup` - Fix configuration issues

## Related

| Component              | Relationship                   |
| ---------------------- | ------------------------------ |
| `pop-deploy-init`      | Creates deploy.json config     |
| `pop-deploy-setup`     | Generates deployment files     |
| `pop-deploy-execute`   | Executes deployment            |
| `deployment-validator` | Agent for automated validation |
