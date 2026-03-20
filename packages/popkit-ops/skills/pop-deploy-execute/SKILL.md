---
name: pop-deploy-execute
description: "Execute deployment to target environment - supports dry-run mode, captures deployment metrics and logs, handles rollback on failure. Use after pop-deploy-validate confirms readiness. Do NOT use without validating first."
inputs:
  - from: pop-deploy-validate
    field: validation_report
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
  - from: any
    field: version
    required: false
outputs:
  - field: deployment_result
    type: json
  - field: deploy_url
    type: string
  - field: deployment_id
    type: string
next_skills:
  - pop-deploy-rollback
  - pop-deploy-validate
triggers:
  - deploy execute
  - deploy now
  - deploy to production
  - deploy to staging
  - run deployment
workflow:
  id: deploy-execute
  name: Deployment Execution Workflow
  version: 1
  description: Execute deployment with dry-run support and rollback on failure
  steps:
    - id: load_config
      description: Load deploy.json and prepare deployment
      type: script
      script: scripts/execute_deployment.py
      args: "--action prepare"
      next: target_decision
    - id: target_decision
      description: Confirm deployment target
      type: user_decision
      question: "Which target should I deploy?"
      header: "Target"
      options:
        - id: primary
          label: "Primary target"
          description: "Deploy to the primary configured target"
          next: mode_decision
        - id: all
          label: "All targets"
          description: "Deploy to all enabled targets"
          next: mode_decision
        - id: specific
          label: "Choose target"
          description: "Select a specific target"
          next: mode_decision
      next_map:
        primary: mode_decision
        all: mode_decision
        specific: mode_decision
    - id: mode_decision
      description: Choose deployment mode
      type: user_decision
      question: "How should I deploy?"
      header: "Mode"
      options:
        - id: dry_run
          label: "Dry run (Recommended first)"
          description: "Simulate deployment without executing"
          next: execute_deploy
        - id: deploy
          label: "Deploy"
          description: "Execute the deployment"
          next: confirm_deploy
        - id: canary
          label: "Canary deploy"
          description: "Deploy to small percentage first"
          next: confirm_deploy
      next_map:
        dry_run: execute_deploy
        deploy: confirm_deploy
        canary: confirm_deploy
    - id: confirm_deploy
      description: Final deployment confirmation
      type: user_decision
      question: "Ready to deploy? This will push changes to the target environment."
      header: "Confirm"
      options:
        - id: proceed
          label: "Deploy now"
          description: "Execute the deployment"
          next: execute_deploy
        - id: dry_run_first
          label: "Dry run first"
          description: "Run a dry run before deploying"
          next: execute_deploy
        - id: abort
          label: "Abort"
          description: "Cancel deployment"
          next: complete
      next_map:
        proceed: execute_deploy
        dry_run_first: execute_deploy
        abort: complete
    - id: execute_deploy
      description: Execute the deployment
      type: script
      script: scripts/execute_deployment.py
      args: "--action execute"
      next: review_result
    - id: review_result
      description: Review deployment result
      type: user_decision
      question: "Deployment complete. What next?"
      header: "Result"
      options:
        - id: verify
          label: "Verify deployment"
          description: "Run health checks on deployed service"
          next: run_verify
        - id: rollback
          label: "Rollback"
          description: "Something went wrong, roll back"
          next: run_rollback
        - id: done
          label: "Done"
          description: "Deployment successful, finish"
          next: complete
      next_map:
        verify: run_verify
        rollback: run_rollback
        done: complete
    - id: run_verify
      description: Verify deployment health
      type: script
      script: scripts/execute_deployment.py
      args: "--action verify"
      next: complete
    - id: run_rollback
      description: Initiate rollback
      type: skill
      skill: pop-deploy-rollback
      next: complete
    - id: complete
      description: Execution workflow finished
      type: terminal
---

# Deploy Execute Skill

Execute deployment to target environment with safety controls.

## Overview

**Trigger:** `/popkit-ops:deploy execute` or after validation passes

**Purpose:** Execute the actual deployment to the target environment. Supports dry-run mode for safe testing, captures deployment metrics and logs, and handles automatic rollback on failure.

## Critical Rules

1. **ALWAYS run validation before production deploys** - Skip only for dry-run
2. **ALWAYS confirm before live deployment** - Require explicit user confirmation
3. **ALWAYS support dry-run mode** - Default to dry-run for first deployment
4. **NEVER deploy with blocking validation failures** - Respect go/no-go
5. **ALWAYS record deployment in history** - Update deploy.json after every attempt
6. **ALWAYS capture rollback info** - Save previous version for potential rollback

## Required Decision Points

| Step | When               | Decision ID      |
| ---- | ------------------ | ---------------- |
| 1    | Target selection   | `deploy_target`  |
| 2    | Mode selection     | `deploy_mode`    |
| 3    | Before live deploy | `confirm_deploy` |
| 4    | After deployment   | `post_deploy`    |

**Skipping these violates PopKit UX standard.**

## Process

### Step 1: Prepare Deployment

```bash
python scripts/execute_deployment.py --dir . --action prepare --target docker
```

This:

- Loads deploy.json configuration
- Identifies target and environment
- Checks last deployment for rollback reference
- Prepares deployment plan

### Step 2: Target Selection (MANDATORY)

```
Use AskUserQuestion:
- question: "Which target should I deploy?"
- header: "Target"
- options:
  - "Primary target" - Deploy to primary configured target
  - "All targets" - Deploy to all enabled targets
  - "Choose target" - Select specific target
```

### Step 3: Mode Selection (MANDATORY)

```
Use AskUserQuestion:
- question: "How should I deploy?"
- header: "Mode"
- options:
  - "Dry run (Recommended first)" - Simulate without executing
  - "Deploy" - Execute the deployment
  - "Canary deploy" - Deploy to small percentage first
```

### Step 4: Confirmation for Live Deploy (MANDATORY)

```
Use AskUserQuestion:
- question: "Ready to deploy? This will push changes to the target environment."
- header: "Confirm"
- options:
  - "Deploy now" - Execute
  - "Dry run first" - Simulate first
  - "Abort" - Cancel
```

### Step 5: Execute

```bash
python scripts/execute_deployment.py --dir . --action execute --target docker --mode deploy --version 1.2.0
```

### Step 6: Post-Deploy (MANDATORY)

```
Use AskUserQuestion:
- question: "Deployment complete. What next?"
- header: "Result"
- options:
  - "Verify deployment" - Health checks
  - "Rollback" - Something went wrong
  - "Done" - Deployment successful
```

## Deployment Modes

### Dry Run

- Simulates all deployment steps without executing
- Validates commands, configs, and access
- Reports what would happen
- No changes to target environment

### Standard Deploy

- Full deployment execution
- Captures start/end timestamps
- Records deployment in history
- Triggers post-deploy verification

### Canary Deploy

- Deploys to small subset (e.g., 10% of instances)
- Monitors for errors during canary period
- Promotes to full deployment or rolls back
- Only available for Kubernetes/Docker Swarm targets

## Output Format

```
Deployment Execution
====================
Target: docker (primary)
Mode: deploy
Version: 1.2.0
Environment: production

Steps:
  [1/5] Building image... done (45s)
  [2/5] Pushing to registry... done (12s)
  [3/5] Updating deployment... done (3s)
  [4/5] Waiting for rollout... done (30s)
  [5/5] Health check... passed

Result: SUCCESS
Duration: 90s
Deployment ID: deploy-20260318-143022
Image: ghcr.io/myorg/myapp:1.2.0

History updated in .claude/popkit/deploy.json
Next: Verify with /popkit-ops:deploy validate or rollback with /popkit-ops:deploy rollback
```

## Failure Handling

When deployment fails:

1. **Capture error details** - Full error message and stack trace
2. **Determine failure point** - Which step failed
3. **Auto-rollback if configured** - Roll back to previous version
4. **Record failure in history** - Status: "failed" with error details
5. **Present options to user** - Fix and retry, rollback, or abort

## Integration

**Called by:**

- `/popkit-ops:deploy execute` command
- `pop-deploy-validate` workflow (proceed to deploy step)

**Triggers:**

- deployment-validator agent (post-deploy verification)

**Followed by:**

- `pop-deploy-rollback` - If deployment fails or needs rollback
- `pop-deploy-validate` - Post-deploy verification

## Related

| Component              | Relationship              |
| ---------------------- | ------------------------- |
| `pop-deploy-validate`  | Pre-deploy validation     |
| `pop-deploy-rollback`  | Rollback on failure       |
| `deployment-validator` | Agent for verification    |
| `deploy.json`          | Configuration and history |
