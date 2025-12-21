---
name: deploy-init
description: "Analyze project deployment readiness and initialize deployment configuration. Use when user runs /popkit:deploy or /popkit:deploy init. Detects project state (GitHub, CI/CD, targets), collects user intent through AskUserQuestion, and creates .claude/popkit/deploy.json configuration file. Do NOT use if deploy.json already exists - use deploy-validate instead."
---

# Deploy Initialization

## Overview

Establish deployment infrastructure for any project state - from no GitHub to production-ready CI/CD.

**Core principle:** Progressive enhancement - start where the project is, guide to where it needs to be.

## Critical Rules

| Rule | Details |
|------|---------|
| **NEVER assume GitHub exists** | Offer to create repo if needed |
| **ALWAYS use AskUserQuestion** | Never guess deployment targets |
| **Create deploy.json** | Store configuration for future runs |
| **Check existing setup** | Don't overwrite working CI/CD |
| **Offer multiple paths** | Quick start vs full setup |

## Process

### Step 1: Detect Project State

Analyze current project infrastructure.

**Checks:**
- GitHub repository (remote)
- CI/CD workflows (.github/workflows/)
- Package configuration (package.json, pyproject.toml)
- Existing deploy config

[See detection script](examples/deploy-init/detect_state.py)

### Step 2: Ask About Deployment Intent

```
Use AskUserQuestion tool with:
- question: "Where do you want to deploy?"
- header: "Deploy Target"
- options:
  - label: "npm registry"
    description: "JavaScript/TypeScript package"
  - label: "PyPI"
    description: "Python package"
  - label: "Docker Hub / GHCR"
    description: "Container images"
  - label: "GitHub Releases"
    description: "Binary releases"
  - label: "Netlify / Vercel"
    description: "Static site or web app"
- multiSelect: true
```

### Step 3: Create Configuration

Generate `.claude/popkit/deploy.json` with selected targets and detected state.

### Step 4: Generate Workflows

Invoke target-specific skills based on configuration:
- `pop-deploy-npm` for npm
- `pop-deploy-pypi` for PyPI
- `pop-deploy-docker` for Docker
- `pop-deploy-github-releases` for releases
- `pop-deploy-netlify` for Netlify

## deploy.json Structure

[See schema](examples/deploy-init/deploy-schema.json)

```json
{
  "targets": ["npm", "docker"],
  "github": {
    "has_repo": true,
    "has_workflows": false
  },
  "project_type": "node",
  "created_at": "2025-01-15T10:00:00Z"
}
```

## Deployment Targets

| Target | Requirements | Skill |
|--------|--------------|-------|
| npm | package.json, NPM_TOKEN | `pop-deploy-npm` |
| PyPI | pyproject.toml | `pop-deploy-pypi` |
| Docker | Dockerfile or auto-generate | `pop-deploy-docker` |
| GitHub Releases | Git tags | `pop-deploy-github-releases` |
| Netlify | netlify.toml or auto-detect | `pop-deploy-netlify` |

## Output Format

```
Deployment Initialization
══════════════════════════

[1/3] Analyzing project...
      ✓ GitHub: Connected
      ✓ CI/CD: Not configured
      ✓ Type: Node.js package

[2/3] Deployment targets...
      Selected: npm, Docker

[3/3] Configuration created...
      → .claude/popkit/deploy.json

Next Steps:
1. Run /popkit:deploy setup npm
2. Run /popkit:deploy setup docker
3. Run /popkit:deploy validate

Would you like to setup npm deployment now?
```

## Integration

**Command:** `/popkit:deploy init`
**Agent:** `devops-automator`
**Followed by:**
- `/popkit:deploy setup <target>` - Configure specific target
- `/popkit:deploy validate` - Verify configuration

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `pop-deploy-npm` | Invoked for npm target |
| `pop-deploy-pypi` | Invoked for PyPI target |
| `pop-deploy-docker` | Invoked for Docker target |
| `pop-deploy-github-releases` | Invoked for releases |
| `pop-deploy-netlify` | Invoked for Netlify target |
