---
name: pop-deploy-rollback
description: "Emergency rollback to previous deployment version - supports automatic and manual rollback triggers, validates rollback success, and creates incident report. Use when a deployment fails or needs to be reverted."
inputs:
  - from: pop-deploy-execute
    field: deployment_result
    required: false
  - from: pop-deploy-init
    field: deploy_config
    required: false
  - from: any
    field: target
    required: false
  - from: any
    field: rollback_version
    required: false
outputs:
  - field: rollback_result
    type: json
  - field: incident_report
    type: file_path
  - field: rollback_success
    type: boolean
next_skills:
  - pop-deploy-validate
  - pop-deploy-execute
triggers:
  - deploy rollback
  - rollback deployment
  - revert deployment
  - emergency rollback
workflow:
  id: deploy-rollback
  name: Deployment Rollback Workflow
  version: 1
  description: Emergency rollback with validation and incident reporting
  steps:
    - id: assess_situation
      description: Load config and assess current deployment state
      type: script
      script: scripts/rollback_deployment.py
      args: "--action assess"
      next: rollback_decision
    - id: rollback_decision
      description: Choose rollback strategy
      type: user_decision
      question: "How should I roll back?"
      header: "Strategy"
      options:
        - id: previous
          label: "Previous version (Recommended)"
          description: "Roll back to last successful deployment"
          next: confirm_rollback
        - id: specific
          label: "Specific version"
          description: "Roll back to a specific version"
          next: confirm_rollback
        - id: investigate
          label: "Investigate first"
          description: "Gather more info before rolling back"
          next: run_investigate
      next_map:
        previous: confirm_rollback
        specific: confirm_rollback
        investigate: run_investigate
    - id: run_investigate
      description: Investigate the failed deployment
      type: script
      script: scripts/rollback_deployment.py
      args: "--action investigate"
      next: rollback_decision
    - id: confirm_rollback
      description: Confirm rollback execution
      type: user_decision
      question: "Confirm rollback? This will revert the deployment."
      header: "Confirm"
      options:
        - id: proceed
          label: "Roll back now"
          description: "Execute the rollback immediately"
          next: execute_rollback
        - id: dry_run
          label: "Dry run first"
          description: "Simulate the rollback"
          next: execute_rollback
        - id: abort
          label: "Abort"
          description: "Do not roll back"
          next: complete
      next_map:
        proceed: execute_rollback
        dry_run: execute_rollback
        abort: complete
    - id: execute_rollback
      description: Execute the rollback
      type: script
      script: scripts/rollback_deployment.py
      args: "--action rollback"
      next: verify_rollback
    - id: verify_rollback
      description: Verify rollback was successful
      type: script
      script: scripts/rollback_deployment.py
      args: "--action verify"
      next: incident_decision
    - id: incident_decision
      description: Create incident report
      type: user_decision
      question: "Rollback complete. Create incident report?"
      header: "Report"
      options:
        - id: create_report
          label: "Create report (Recommended)"
          description: "Generate incident report for post-mortem"
          next: create_report
        - id: skip_report
          label: "Skip report"
          description: "No incident report needed"
          next: complete
      next_map:
        create_report: create_report
        skip_report: complete
    - id: create_report
      description: Generate incident report
      type: script
      script: scripts/rollback_deployment.py
      args: "--action report"
      next: complete
    - id: complete
      description: Rollback workflow finished
      type: terminal
---

# Deploy Rollback Skill

Emergency rollback to a previous deployment version with verification and incident reporting.

## Overview

**Trigger:** `/popkit-ops:deploy rollback` or when a deployment fails

**Purpose:** Safely revert a deployment to the last known good version. Validates rollback success and generates an incident report for post-mortem analysis.

## Critical Rules

1. **ALWAYS assess before rolling back** - Understand what failed and why
2. **ALWAYS confirm before executing rollback** - Require explicit user confirmation
3. **ALWAYS verify after rollback** - Confirm the rollback was successful
4. **ALWAYS record rollback in history** - Update deploy.json with rollback status
5. **RECOMMEND incident report** - Always offer to create one after rollback

## Required Decision Points

| Step | When                | Decision ID          |
| ---- | ------------------- | -------------------- |
| 1    | Strategy selection  | `rollback_strategy`  |
| 2    | Before execution    | `confirm_rollback`   |
| 3    | After rollback      | `incident_report`    |

**Skipping these violates PopKit UX standard.**

## Process

### Step 1: Assess Situation

```bash
python scripts/rollback_deployment.py --dir . --action assess --target docker
```

This:
- Loads deploy.json and deployment history
- Identifies current deployed version
- Finds last successful deployment (rollback target)
- Assesses impact and risk

### Step 2: Rollback Strategy (MANDATORY)

```
Use AskUserQuestion:
- question: "How should I roll back?"
- header: "Strategy"
- options:
  - "Previous version (Recommended)" - Last successful deployment
  - "Specific version" - Choose a specific version
  - "Investigate first" - Gather more info
```

### Step 3: Confirm Rollback (MANDATORY)

```
Use AskUserQuestion:
- question: "Confirm rollback? This will revert the deployment."
- header: "Confirm"
- options:
  - "Roll back now" - Execute immediately
  - "Dry run first" - Simulate the rollback
  - "Abort" - Cancel rollback
```

### Step 4: Execute Rollback

```bash
python scripts/rollback_deployment.py --dir . --action rollback --target docker --version 1.1.0
```

### Step 5: Verify

```bash
python scripts/rollback_deployment.py --dir . --action verify --target docker
```

### Step 6: Incident Report (MANDATORY)

```
Use AskUserQuestion:
- question: "Rollback complete. Create incident report?"
- header: "Report"
- options:
  - "Create report (Recommended)" - Generate for post-mortem
  - "Skip report" - No report needed
```

## Rollback Strategies

### Docker Rollback
1. Pull previous image tag from registry
2. Stop current container(s)
3. Start container(s) with previous image
4. Verify health checks pass

### npm Rollback
1. Deprecate failed version
2. Point `latest` dist-tag to previous version
3. Publish notice if public package

### Kubernetes Rollback
1. Use `kubectl rollout undo` for deployments
2. Verify pod health
3. Check service endpoints

### Platform Rollback (Vercel/Netlify)
1. Promote previous deployment to production
2. Verify domain routes correctly

## Output Format

```
Deployment Rollback
===================
Target: docker
Current: 1.2.0 (FAILED)
Rollback to: 1.1.0 (last successful)

Steps:
  [1/4] Pulling previous image... done
  [2/4] Stopping current... done
  [3/4] Starting rollback version... done
  [4/4] Health check... passed

Result: ROLLBACK SUCCESS
Duration: 25s

Incident Report: .claude/popkit/incidents/incident-20260318-143500.md
Next: Investigate root cause, then /popkit-ops:deploy execute when fixed
```

## Incident Report Format

Generated at `.claude/popkit/incidents/incident-{timestamp}.md`:

```markdown
# Deployment Incident Report

## Summary
- **Date:** 2026-03-18T14:35:00Z
- **Target:** docker
- **Failed Version:** 1.2.0
- **Rolled Back To:** 1.1.0
- **Duration of Outage:** ~5 minutes
- **Severity:** P2

## Timeline
- 14:30:00 - Deployment of v1.2.0 initiated
- 14:30:45 - Deployment completed
- 14:31:00 - Health check failures detected
- 14:33:00 - Rollback initiated
- 14:35:00 - Rollback completed, service restored

## Root Cause
[To be filled during post-mortem]

## Impact
[To be filled during post-mortem]

## Action Items
- [ ] Investigate root cause
- [ ] Add regression test
- [ ] Update deployment validation checks
```

## Integration

**Called by:**
- `/popkit-ops:deploy rollback` command
- `pop-deploy-execute` workflow (on failure)
- rollback-specialist agent

**Triggers:**
- rollback-specialist agent

**Followed by:**
- `pop-deploy-validate` - Re-validate after fixing issues
- `pop-deploy-execute` - Re-deploy when fixed

## Related

| Component              | Relationship                   |
| ---------------------- | ------------------------------ |
| `pop-deploy-execute`   | Deployment that may need rollback |
| `pop-deploy-validate`  | Post-rollback validation       |
| `rollback-specialist`  | Agent for rollback operations  |
| `deploy.json`          | Configuration and history      |
