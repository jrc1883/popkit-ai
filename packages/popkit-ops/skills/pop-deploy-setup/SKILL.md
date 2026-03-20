---
name: pop-deploy-setup
description: "Use after pop-deploy-init to generate deployment infrastructure files - creates Dockerfiles, docker-compose configs, Kubernetes manifests, CI/CD pipeline workflows, and platform-specific configs based on deploy.json targets. Do NOT use for actual deployment execution - use /popkit-ops:deploy execute for that."
inputs:
  - from: pop-deploy-init
    field: deploy_config
    required: false
  - from: any
    field: target
    required: false
  - from: any
    field: template
    required: false
outputs:
  - field: generated_files
    type: json
  - field: setup_report
    type: file_path
next_skills:
  - pop-deploy-validate
  - pop-deploy-execute
triggers:
  - deploy setup
  - generate deployment files
  - create dockerfile
  - setup ci pipeline
workflow:
  id: deploy-setup
  name: Deployment Setup Workflow
  version: 1
  description: Generate deployment infrastructure from deploy.json configuration
  steps:
    - id: load_config
      description: Load and validate deploy.json
      type: script
      script: scripts/generate_deploy_files.py
      args: "--action load-config"
      next: review_config
    - id: review_config
      description: Review deployment configuration
      type: user_decision
      question: "Deploy config loaded. Which targets should I generate files for?"
      header: "Targets"
      multiSelect: true
      options:
        - id: all
          label: "All configured targets"
          description: "Generate files for every enabled target"
          next: template_decision
        - id: docker
          label: "Docker only"
          description: "Dockerfile and docker-compose"
          next: template_decision
        - id: ci
          label: "CI/CD only"
          description: "GitHub Actions workflows"
          next: template_decision
        - id: k8s
          label: "Kubernetes only"
          description: "K8s manifests (deployment, service, ingress)"
          next: template_decision
      next_map:
        all: template_decision
        docker: template_decision
        ci: template_decision
        k8s: template_decision
    - id: template_decision
      description: Choose template complexity
      type: user_decision
      question: "What level of deployment configuration?"
      header: "Template"
      options:
        - id: minimal
          label: "Minimal"
          description: "Basic configs, no extras"
          next: generate_files
        - id: standard
          label: "Standard (Recommended)"
          description: "Production-ready with health checks and logging"
          next: generate_files
        - id: advanced
          label: "Advanced"
          description: "Multi-stage, multi-env, monitoring, secrets management"
          next: generate_files
      next_map:
        minimal: generate_files
        standard: generate_files
        advanced: generate_files
    - id: generate_files
      description: Generate deployment infrastructure files
      type: script
      script: scripts/generate_deploy_files.py
      args: "--action generate"
      next: review_files
    - id: review_files
      description: Review generated files
      type: user_decision
      question: "Deployment files generated. How should I proceed?"
      header: "Review"
      options:
        - id: accept
          label: "Accept all"
          description: "Keep all generated files as-is"
          next: complete
        - id: customize
          label: "Customize"
          description: "Let me review and modify before proceeding"
          next: complete
        - id: validate
          label: "Run validation"
          description: "Validate generated files before accepting"
          next: run_validate
      next_map:
        accept: complete
        customize: complete
        validate: run_validate
    - id: run_validate
      description: Validate generated deployment files
      type: skill
      skill: pop-deploy-validate
      next: complete
    - id: complete
      description: Setup workflow finished
      type: terminal
---

# Deploy Setup Skill

Generate deployment infrastructure files from your project's `deploy.json` configuration.

## Overview

**Trigger:** `/popkit-ops:deploy setup` or after completing deploy-init

**Purpose:** Read `.claude/popkit/deploy.json` and generate all necessary deployment files: Dockerfiles, docker-compose configs, Kubernetes manifests, CI/CD workflows, and platform-specific configuration.

## Critical Rules

1. **NEVER overwrite existing files without confirmation** - Always check for existing files first
2. **ALWAYS use AskUserQuestion** for template selection - Don't assume complexity level
3. **ALWAYS read deploy.json first** - Never generate files without valid config
4. **Preserve existing customizations** - Merge new config into existing files when possible
5. **Generate .gitignore entries** - Add generated secrets/env files to .gitignore

## Required Decision Points

| Step | When              | Decision ID        |
| ---- | ----------------- | ------------------ |
| 1    | After config load | `target_selection` |
| 2    | Before generation | `template_level`   |
| 3    | After generation  | `review_action`    |

**Skipping these violates PopKit UX standard.**

## Process

### Step 1: Load Configuration

```bash
python scripts/generate_deploy_files.py --dir . --action load-config
```

Reads `.claude/popkit/deploy.json` and validates structure. Reports:

- Configured targets and their settings
- Existing deployment files found
- Potential conflicts

### Step 2: Target Selection (MANDATORY)

```
Use AskUserQuestion:
- question: "Deploy config loaded. Which targets should I generate files for?"
- header: "Targets"
- multiSelect: true
- options: [Based on deploy.json targets]
```

### Step 3: Template Level (MANDATORY)

```
Use AskUserQuestion:
- question: "What level of deployment configuration?"
- header: "Template"
- options:
  - "Minimal" - Basic configs, no extras
  - "Standard (Recommended)" - Production-ready with health checks
  - "Advanced" - Multi-stage, monitoring, secrets management
```

### Step 4: Generate Files

```bash
python scripts/generate_deploy_files.py --dir . --action generate --targets TARGET1,TARGET2 --template standard
```

### Step 5: Review (MANDATORY)

```
Use AskUserQuestion:
- question: "Deployment files generated. How should I proceed?"
- header: "Review"
- options:
  - "Accept all" - Keep generated files
  - "Customize" - Review and modify
  - "Run validation" - Validate before accepting
```

## Generated Files by Target

### Docker Target

| Template | Files Generated                                                                     |
| -------- | ----------------------------------------------------------------------------------- |
| minimal  | `Dockerfile`                                                                        |
| standard | `Dockerfile`, `docker-compose.yml`, `.dockerignore`                                 |
| advanced | Above + `docker-compose.prod.yml`, `docker-compose.dev.yml`, multi-stage Dockerfile |

### CI/CD (GitHub Actions)

| Template | Files Generated                                                                |
| -------- | ------------------------------------------------------------------------------ |
| minimal  | `.github/workflows/deploy.yml`                                                 |
| standard | Above + `.github/workflows/test.yml`                                           |
| advanced | Above + `.github/workflows/release.yml`, environment-specific deploy workflows |

### Kubernetes

| Template | Files Generated                                                              |
| -------- | ---------------------------------------------------------------------------- |
| minimal  | `k8s/deployment.yml`, `k8s/service.yml`                                      |
| standard | Above + `k8s/ingress.yml`, `k8s/configmap.yml`                               |
| advanced | Above + `k8s/hpa.yml`, `k8s/pdb.yml`, `k8s/secrets.yml`, Helm chart skeleton |

### Platform (Vercel/Netlify)

| Template | Files Generated                                   |
| -------- | ------------------------------------------------- |
| minimal  | Platform config file only                         |
| standard | Config + environment setup                        |
| advanced | Config + preview environments + headers/redirects |

## Output Format

```
Deployment Setup
================
[1/4] Loading config... Found 2 targets (Docker, npm)
[2/4] Checking existing... 1 conflict (Dockerfile exists)
[3/4] Generating files...
  - Dockerfile (created)
  - docker-compose.yml (created)
  - .dockerignore (created)
  - .github/workflows/deploy.yml (created)
  - .github/workflows/test.yml (created)
[4/4] Complete

Summary:
  Generated: 5 files
  Skipped: 0 (no conflicts)
  Template: standard
  Next: /popkit-ops:deploy validate
```

## Integration

**Called by:**

- `/popkit-ops:deploy setup` command
- `pop-deploy-init` workflow (run_setup step)

**Triggers:**

- deployment-validator agent (for post-setup validation)

**Followed by:**

- `pop-deploy-validate` - Validate generated deployment files
- `pop-deploy-execute` - Execute the deployment

## Related

| Component              | Relationship               |
| ---------------------- | -------------------------- |
| `pop-deploy-init`      | Creates deploy.json config |
| `pop-deploy-validate`  | Validates generated files  |
| `deployment-validator` | Agent for validation       |
| `deploy.json`          | Input configuration        |
