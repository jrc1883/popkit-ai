---
name: pop-deploy-init
description: "Use when you need to manage project deployments - analyzes project structure to detect deployment targets (Docker, npm, Vercel, etc.), creates .claude/popkit/deploy.json config, and sets up deployment infrastructure. Do NOT use for actual deployment execution - use /popkit-ops:deploy execute for that."
inputs:
  - from: command
    field: subcommand
    required: false
  - from: any
    field: target
    required: false
outputs:
  - field: deploy_config
    type: file_path
  - field: detected_targets
    type: json
next_skills:
  - pop-deploy-setup
  - pop-deploy-validate
triggers:
  - deploy init
  - deployment configuration
  - setup deployment
workflow:
  id: deploy-init
  name: Deployment Initialization Workflow
  version: 1
  description: Analyze project and configure deployment targets
  steps:
    - id: detect_targets
      description: Detect available deployment targets
      type: script
      script: scripts/detect_deploy_targets.py
      next: target_decision
    - id: target_decision
      description: Confirm or select deployment targets
      type: user_decision
      question: "Which deployment targets do you want to configure?"
      header: "Targets"
      multiSelect: true
      options:
        - id: docker
          label: "Docker"
          description: "Containerized deployment with Dockerfile"
          next: priority_decision
        - id: npm
          label: "npm Registry"
          description: "Publish to npm as a package"
          next: priority_decision
        - id: pypi
          label: "PyPI Registry"
          description: "Publish to PyPI as a package"
          next: priority_decision
        - id: vercel
          label: "Vercel"
          description: "Deploy to Vercel platform"
          next: priority_decision
        - id: netlify
          label: "Netlify"
          description: "Deploy to Netlify platform"
          next: priority_decision
        - id: github_releases
          label: "GitHub Releases"
          description: "Create GitHub releases with assets"
          next: priority_decision
      next_map:
        docker: priority_decision
        npm: priority_decision
        pypi: priority_decision
        vercel: priority_decision
        netlify: priority_decision
        github_releases: priority_decision
    - id: priority_decision
      description: Set primary deployment target
      type: user_decision
      question: "Which target should be the primary deployment?"
      header: "Primary"
      options:
        - id: auto
          label: "Auto (Recommended)"
          description: "Use first selected target as primary"
          next: ci_decision
        - id: manual
          label: "Choose manually"
          description: "Select specific primary target"
          next: ci_decision
      next_map:
        auto: ci_decision
        manual: ci_decision
    - id: ci_decision
      description: Configure CI/CD integration
      type: user_decision
      question: "How should deployments be triggered?"
      header: "CI/CD"
      options:
        - id: github_actions
          label: "GitHub Actions (Recommended)"
          description: "Auto-deploy on push/tag via GitHub Actions"
          next: create_config
        - id: manual_only
          label: "Manual only"
          description: "Deploy via CLI commands only"
          next: create_config
        - id: both
          label: "Both"
          description: "CI/CD with manual override capability"
          next: create_config
      next_map:
        github_actions: create_config
        manual_only: create_config
        both: create_config
    - id: create_config
      description: Generate deploy.json configuration
      type: script
      script: scripts/create_deploy_config.py
      next: setup_decision
    - id: setup_decision
      description: Decide whether to run setup now
      type: user_decision
      question: "Configuration created. Run setup to generate deployment files?"
      header: "Next Step"
      options:
        - id: setup_now
          label: "Run setup now (Recommended)"
          description: "Generate Dockerfile, CI workflows, etc."
          next: run_setup
        - id: setup_later
          label: "Setup later"
          description: "Just save configuration for now"
          next: complete
      next_map:
        setup_now: run_setup
        setup_later: complete
    - id: run_setup
      description: Generate deployment infrastructure
      type: skill
      skill: pop-deploy-setup
      next: complete
    - id: complete
      description: Initialization workflow finished
      type: terminal
---

# Deploy Init Skill

Initialize deployment configuration for your project. Detects available targets and creates `.claude/popkit/deploy.json`.

## Overview

**Trigger:** `/popkit-ops:deploy init` or when setting up project deployments

**Purpose:** Analyze project structure to detect deployment capabilities, gather user preferences, and create a standardized deployment configuration.

## Critical Rules

1. **NEVER modify existing deploy.json without confirmation** - Always back up first
2. **ALWAYS use AskUserQuestion** for target selection - Don't assume targets
3. **ALWAYS validate detected targets** - Confirm with user before creating config
4. **Check for existing CI/CD workflows** - Don't overwrite without asking
5. **Preserve user customizations** - Merge, don't replace

## Required Decision Points

| Step | When                   | Decision ID        |
| ---- | ---------------------- | ------------------ |
| 1    | After target detection | `target_selection` |
| 2    | Multiple targets       | `priority_target`  |
| 3    | CI/CD configuration    | `ci_trigger_mode`  |
| 4    | After config creation  | `run_setup`        |

**Skipping these violates PopKit UX standard.**

## Process

### Step 1: Run Target Detection

```bash
python scripts/detect_deploy_targets.py --dir .
```

This analyzes:

- `package.json` / `pyproject.toml` for registry targets (npm/PyPI)
- `Dockerfile` / `docker-compose.yml` for Docker targets
- `vercel.json` / `netlify.toml` for platform targets
- `.github/workflows/` for existing CI/CD

Output JSON includes detected targets with confidence scores.

### Step 2: Target Selection (MANDATORY)

Present detected targets to user with confidence indicators:

```
Use AskUserQuestion:
- question: "Detected [targets]. Which deployment targets do you want to configure?"
- header: "Targets"
- multiSelect: true
- options: [Based on detection results, mark high-confidence as "(Detected)"]
```

### Step 3: Primary Target (if multiple selected)

```
Use AskUserQuestion:
- question: "Which target should be the primary deployment?"
- header: "Primary"
- options: [Selected targets from previous step]
```

### Step 4: CI/CD Mode

```
Use AskUserQuestion:
- question: "How should deployments be triggered?"
- header: "CI/CD"
- options:
  - "GitHub Actions (Recommended)" - Auto-deploy on push/tag
  - "Manual only" - Deploy via CLI commands
  - "Both" - CI/CD with manual override
```

### Step 5: Create Configuration

Generate `.claude/popkit/deploy.json`:

```json
{
  "version": "1.0",
  "project_name": "<detected>",
  "targets": {
    "docker": {
      "enabled": true,
      "primary": true,
      "config": {
        "image_name": "<project>",
        "registry": "ghcr.io",
        "build_context": ".",
        "dockerfile": "Dockerfile"
      }
    },
    "npm": {
      "enabled": true,
      "primary": false,
      "config": {
        "registry": "https://registry.npmjs.org",
        "access": "public"
      }
    }
  },
  "ci": {
    "provider": "github_actions",
    "triggers": {
      "push": ["main"],
      "tag": ["v*"]
    }
  },
  "history": []
}
```

### Step 6: Next Action (MANDATORY)

```
Use AskUserQuestion:
- question: "Configuration created. Run setup to generate deployment files?"
- header: "Next Step"
- options:
  - "Run setup now (Recommended)" - Generate Dockerfile, CI workflows
  - "Setup later" - Save config only
```

## Output Format

```
Deployment Initialization
═════════════════════════
[1/5] Detecting targets... ✓ Found 3 targets
[2/5] Confirming selection... ✓ Docker, npm selected
[3/5] Setting primary... ✓ Docker (primary)
[4/5] Configuring CI/CD... ✓ GitHub Actions
[5/5] Creating config... ✓ .claude/popkit/deploy.json

Summary:
  Targets: Docker (primary), npm
  CI/CD: GitHub Actions (push to main, tags v*)
  Config: .claude/popkit/deploy.json
  Next: /popkit-ops:deploy setup
```

## Target Detection

### Docker Target

Detected when:

- `Dockerfile` exists (high confidence)
- `docker-compose.yml` exists (high confidence)
- `package.json` has docker scripts (medium confidence)

Configuration:

- Image name from project name
- Registry from git remote (ghcr.io for GitHub)
- Multi-stage build template if TypeScript/compiled

### npm Target

Detected when:

- `package.json` exists with name field (high confidence)
- No "private": true (required)
- Has main/exports field (high confidence)

Configuration:

- Registry URL (default: npmjs.org)
- Access level (public/restricted)
- Publish directory (default: .)

### PyPI Target

Detected when:

- `pyproject.toml` exists (high confidence)
- Has `[project]` section with name (required)
- Has build system configuration (high confidence)

Configuration:

- Registry URL (default: pypi.org)
- Build backend (setuptools, hatch, poetry)
- Distribution format (wheel, sdist)

### Vercel Target

Detected when:

- `vercel.json` exists (high confidence)
- `package.json` has Next.js dependency (high confidence)
- `.vercel/` directory exists (medium confidence)

Configuration:

- Project ID (from vercel.json or CLI)
- Team ID (optional)
- Production branch

### Netlify Target

Detected when:

- `netlify.toml` exists (high confidence)
- Static site generator detected (medium confidence)

Configuration:

- Site ID
- Build command
- Publish directory

### GitHub Releases Target

Detected when:

- Git repository exists (required)
- Has version tags (v\*) (medium confidence)
- CHANGELOG.md exists (medium confidence)

Configuration:

- Release notes source (CHANGELOG, commits, manual)
- Asset patterns (binaries, archives)
- Draft vs publish immediately

## Integration

**Called by:**

- `/popkit-ops:deploy init` command
- Manual skill invocation

**Triggers:**

- deployment-validator agent (for pre-deploy checks)

**Followed by:**

- `pop-deploy-setup` - Generate deployment files
- `pop-deploy-validate` - Pre-deployment validation

## Related

| Component              | Relationship                  |
| ---------------------- | ----------------------------- |
| `deploy.md`            | Command documentation         |
| `deployment-validator` | Agent for validation          |
| `rollback-specialist`  | Agent for rollback operations |
| `pop-deploy-setup`     | Generates deployment files    |

## Examples

See `examples/` for:

- `docker-target.md` - Docker deployment setup
- `npm-target.md` - npm publishing setup
- `multi-target.md` - Multiple target configuration
