---
description: "init | setup | validate | execute | rollback [--target, --dry-run, --yes, --json]"
argument-hint: "<subcommand> [target] [options]"
---

# /popkit-ops:deploy - Unified Deployment Orchestration

Deploy to any target: Docker, npm/PyPI, Vercel/Netlify, or GitHub Releases. Orchestrates the full deployment pipeline from initialization to rollback.

## Usage

```bash
/popkit-ops:deploy                         # Show deployment status and next actions
/popkit-ops:deploy init                    # Initialize deployment config
/popkit-ops:deploy setup                   # Generate deployment artifacts
/popkit-ops:deploy validate                # Pre-deployment validation
/popkit-ops:deploy execute                 # Execute deployment
/popkit-ops:deploy rollback                # Emergency rollback
```

## Subcommands

| Subcommand       | Description                                      | Skill Invoked         |
| ---------------- | ------------------------------------------------ | --------------------- |
| (none)           | Show deployment status and available actions      | -                     |
| init             | Analyze project and configure deployment targets  | pop-deploy-init       |
| setup            | Generate CI/CD pipeline and target configuration  | pop-deploy-setup      |
| validate         | Run pre-deployment checks                         | pop-deploy-validate   |
| execute          | Deploy to target(s)                               | pop-deploy-execute    |
| rollback         | Undo a deployment                                 | pop-deploy-rollback   |

## Pipeline

The deployment workflow is a sequential pipeline. Each step builds on the previous:

```
init → setup → validate → execute
                              ↓
                          rollback (if needed)
```

Running `/popkit-ops:deploy` with no arguments inspects the current state and tells you where you are in the pipeline and what to do next.

---

## (no subcommand) - Deployment Status

Show current deployment pipeline status by inspecting `.claude/popkit/deploy.json` and project state.

**Process:**

1. Check if `.claude/popkit/deploy.json` exists
2. If missing: recommend `init` as the first step
3. If present: read config and determine pipeline progress
4. Check for generated deployment files (Dockerfile, workflows, etc.)
5. Check last deployment history entry
6. Present status summary with next recommended action

**Output:**

```
Deployment Status
=================
Project: my-project
Config: .claude/popkit/deploy.json

Pipeline Progress:
  [done] init        Configured 2 targets (Docker, npm)
  [done] setup       Generated 5 deployment files
  [    ] validate    Not yet run
  [    ] execute     -
  [    ] rollback    -

Targets:
  Docker (primary)   ghcr.io/myorg/myapp
  npm                @myorg/myapp

Last Deployment: (none)

Next Step: /popkit-ops:deploy validate
  Run pre-deployment checks before deploying.
```

**When no config exists:**

```
Deployment Status
=================
No deployment configuration found.

To get started, run:
  /popkit-ops:deploy init

This will analyze your project, detect deployment targets,
and create .claude/popkit/deploy.json.
```

**Options:** --json (output JSON format)

---

## init

Initialize deployment configuration. Analyzes project structure to detect deployment targets and creates `.claude/popkit/deploy.json`.

**Invokes:** `pop-deploy-init` skill

```bash
/popkit-ops:deploy init                    # Interactive initialization
/popkit-ops:deploy init --force            # Overwrite existing config
/popkit-ops:deploy init --skip-github      # Skip GitHub detection
/popkit-ops:deploy init --json             # JSON output
```

### Process

1. Run `scripts/detect_deploy_targets.py` to identify available targets
2. Present detected targets via AskUserQuestion (multiSelect)
3. Set primary target if multiple selected
4. Configure CI/CD trigger mode (GitHub Actions, manual, both)
5. Create `.claude/popkit/deploy.json` configuration
6. Offer to proceed to setup

### Required Decision Points

| Step | Decision                      | Type        |
| ---- | ----------------------------- | ----------- |
| 1    | Select deployment targets     | multiSelect |
| 2    | Set primary target            | select      |
| 3    | Configure CI/CD trigger mode  | select      |
| 4    | Proceed to setup?             | select      |

**Skipping these violates PopKit UX standard.**

### Detectable Targets

| Target          | Detection                                    |
| --------------- | -------------------------------------------- |
| Docker          | Dockerfile, docker-compose.yml               |
| npm             | package.json (not private, has main/exports) |
| PyPI            | pyproject.toml with [project] section        |
| Vercel          | vercel.json, Next.js dependency              |
| Netlify         | netlify.toml, static site generator          |
| GitHub Releases | Git repo with version tags, CHANGELOG.md     |

### Options

| Flag            | Description                              |
| --------------- | ---------------------------------------- |
| `--force`       | Overwrite existing config without backup |
| `--skip-github` | Skip GitHub-related detection            |
| `--json`        | Output JSON instead of formatted text    |

### Output

```
Deployment Initialization
=========================
[1/5] Detecting targets... Found 3 targets
[2/5] Confirming selection... Docker, npm selected
[3/5] Setting primary... Docker (primary)
[4/5] Configuring CI/CD... GitHub Actions
[5/5] Creating config... .claude/popkit/deploy.json

Summary:
  Targets: Docker (primary), npm
  CI/CD: GitHub Actions (push to main, tags v*)
  Config: .claude/popkit/deploy.json
  Next: /popkit-ops:deploy setup
```

**Pipeline state after init:** `[done] init → [next] setup`

---

## setup

Generate deployment infrastructure files from `deploy.json` configuration.

**Invokes:** `pop-deploy-setup` skill

```bash
/popkit-ops:deploy setup                       # Interactive setup
/popkit-ops:deploy setup --template standard   # Set template level
/popkit-ops:deploy setup --dry-run             # Preview without writing files
/popkit-ops:deploy setup --all                 # All configured targets
/popkit-ops:deploy setup --no-commit           # Skip auto-commit
```

### Process

1. Load and validate `.claude/popkit/deploy.json`
2. Present targets for file generation (AskUserQuestion, multiSelect)
3. Select template level (minimal, standard, advanced)
4. Generate deployment files
5. Review generated files (accept, customize, or validate)

### Required Decision Points

| Step | Decision                        | Type        |
| ---- | ------------------------------- | ----------- |
| 1    | Select targets for generation   | multiSelect |
| 2    | Choose template level           | select      |
| 3    | Review generated files          | select      |

**Skipping these violates PopKit UX standard.**

### Generated Files by Target

| Target          | Files Generated                                            |
| --------------- | ---------------------------------------------------------- |
| Docker          | Dockerfile, docker-compose.yml, .dockerignore, CI workflow |
| Vercel          | vercel.json, preview deployment workflow                   |
| Netlify         | netlify.toml, deployment workflow                          |
| npm             | Validates package.json, npm-publish.yml                    |
| PyPI            | Validates pyproject.toml, pypi-publish.yml                 |
| GitHub Releases | release.yml, asset configuration                           |

### Templates

| Level    | Description                                                 |
| -------- | ----------------------------------------------------------- |
| minimal  | Basic configs, no extras                                    |
| standard | Production-ready with health checks and logging             |
| advanced | Multi-stage, multi-env, monitoring, secrets management      |

### Options

| Flag               | Description                           |
| ------------------ | ------------------------------------- |
| `--dry-run`        | Preview files without writing         |
| `--no-commit`      | Skip auto-commit of generated files   |
| `--template`       | Template level: minimal/standard/advanced |
| `--all`            | Generate for all configured targets   |

### Output

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

**Pipeline state after setup:** `[done] init → [done] setup → [next] validate`

---

## validate

Run pre-deployment validation checks. Produces a readiness score and go/no-go recommendation.

**Invokes:** `pop-deploy-validate` skill

```bash
/popkit-ops:deploy validate                    # Standard validation
/popkit-ops:deploy validate --quick            # Config and build only
/popkit-ops:deploy validate --target docker    # Validate specific target
/popkit-ops:deploy validate --fix              # Auto-fix where possible
/popkit-ops:deploy validate --strict           # Treat warnings as failures
```

### Process

1. Load `deploy.json` and determine validation scope
2. Select validation scope (AskUserQuestion: quick, standard, full)
3. Execute validation checks
4. Present results with go/no-go recommendation
5. Decide next action (deploy, fix, override, abort)

### Required Decision Points

| Step | Decision                      | Type   |
| ---- | ----------------------------- | ------ |
| 1    | Select validation scope       | select |
| 2    | Post-validation action        | select |

**Skipping these violates PopKit UX standard.**

### Validation Checks

| Scope    | Checks                                                      | Time     |
| -------- | ----------------------------------------------------------- | -------- |
| quick    | Config exists, target config valid, version check, git status | ~30s     |
| standard | Above + build, tests, dependencies, lockfile, env vars      | ~2-5min  |
| full     | Above + security scan, license audit, Docker lint, size check | ~5-15min |

### Readiness Score

| Score | Meaning                    | Recommendation                 |
| ----- | -------------------------- | ------------------------------ |
| 100   | All checks passed          | GO - Deploy                    |
| 80-99 | Passed with warnings       | GO - Deploy with awareness     |
| 60-79 | Some non-blocking failures | CONDITIONAL - Fix warnings     |
| 40-59 | Significant issues         | NO-GO - Fix before deploying   |
| 0-39  | Critical failures          | NO-GO - Blocking issues        |

### Options

| Flag       | Description                        |
| ---------- | ---------------------------------- |
| `--target` | Validate specific target           |
| `--quick`  | Config and build check only        |
| `--fix`    | Auto-fix where possible            |
| `--strict` | Treat warnings as blocking         |
| `--json`   | Output JSON format                 |

### Output

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

**Pipeline state after validate:** `[done] init → [done] setup → [done] validate → [next] execute`

---

## execute

Deploy to configured target(s) with safety controls.

**Invokes:** `pop-deploy-execute` skill

```bash
/popkit-ops:deploy execute                     # Deploy primary target
/popkit-ops:deploy execute --dry-run           # Simulate deployment
/popkit-ops:deploy execute --target docker     # Deploy specific target
/popkit-ops:deploy execute --all               # Deploy all targets
/popkit-ops:deploy execute --yes               # Skip confirmation
/popkit-ops:deploy execute --version 1.2.0     # Specify version
/popkit-ops:deploy execute --watch             # Watch deployment progress
```

### Process

1. Load `deploy.json` and prepare deployment
2. Select target (AskUserQuestion: primary, all, specific)
3. Select mode (AskUserQuestion: dry-run, deploy, canary)
4. Confirm deployment (AskUserQuestion, skipped with --yes)
5. Execute deployment
6. Post-deployment action (verify, rollback, done)

### Required Decision Points

| Step | Decision                     | Type   |
| ---- | ---------------------------- | ------ |
| 1    | Select deployment target     | select |
| 2    | Select deployment mode       | select |
| 3    | Confirm live deployment      | select |
| 4    | Post-deployment action       | select |

**Skipping these violates PopKit UX standard.**

### Deployment Modes

| Mode    | Description                                  |
| ------- | -------------------------------------------- |
| dry-run | Simulate all steps without executing         |
| deploy  | Full deployment execution                    |
| canary  | Deploy to small subset first (K8s/Docker)    |

### Execution by Target

| Target          | Steps                                            |
| --------------- | ------------------------------------------------ |
| Docker          | Build image, push to registry, update deployment |
| npm             | Version bump, publish to registry                |
| PyPI            | Build wheel/sdist, publish to registry           |
| Vercel          | Trigger deployment via CLI/CI                    |
| Netlify         | Trigger deployment via CLI/CI                    |
| GitHub Releases | Create release, upload assets                    |

### Options

| Flag              | Description                         |
| ----------------- | ----------------------------------- |
| `--target`        | Deploy specific target              |
| `--all`           | Deploy all enabled targets          |
| `--dry-run`       | Simulate without executing          |
| `--yes`           | Skip confirmation prompt            |
| `--version`       | Specify version to deploy           |
| `--skip-validate` | Skip pre-deploy validation          |
| `--watch`         | Watch deployment progress           |

### Output

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
Deployment ID: deploy-20260319-143022
Image: ghcr.io/myorg/myapp:1.2.0

History updated in .claude/popkit/deploy.json
```

### Failure Handling

When deployment fails:

1. Capture error details and failure point
2. Auto-rollback if configured in deploy.json
3. Record failure in deployment history
4. Present options: fix and retry, rollback, or abort

**Pipeline state after execute:** `[done] init → [done] setup → [done] validate → [done] execute`

---

## rollback

Emergency rollback to a previous deployment version with verification and incident reporting.

**Invokes:** `pop-deploy-rollback` skill

```bash
/popkit-ops:deploy rollback                    # Roll back primary target
/popkit-ops:deploy rollback --target docker    # Roll back specific target
/popkit-ops:deploy rollback --to 1.1.0         # Roll back to specific version
/popkit-ops:deploy rollback --list             # List rollback targets
/popkit-ops:deploy rollback --yes              # Skip confirmation
```

### Process

1. Assess current deployment state and rollback options
2. Select rollback strategy (AskUserQuestion: previous, specific, investigate)
3. Confirm rollback (AskUserQuestion)
4. Execute rollback
5. Verify rollback success
6. Offer incident report creation

### Required Decision Points

| Step | Decision                     | Type   |
| ---- | ---------------------------- | ------ |
| 1    | Rollback strategy            | select |
| 2    | Confirm rollback             | select |
| 3    | Create incident report?      | select |

**Skipping these violates PopKit UX standard.**

### Rollback by Target

| Target          | Rollback Strategy                              |
| --------------- | ---------------------------------------------- |
| Docker          | Re-tag previous image, restart containers      |
| npm             | Deprecate current, point latest to previous    |
| PyPI            | Yank current version                           |
| Vercel          | Promote previous deployment to production      |
| Netlify         | Promote previous deployment to production      |
| GitHub Releases | Mark current as pre-release, restore previous  |

### Options

| Flag       | Description                       |
| ---------- | --------------------------------- |
| `--target` | Roll back specific target         |
| `--to`     | Roll back to specific version     |
| `--list`   | List available rollback targets   |
| `--yes`    | Skip confirmation                 |

### Output

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

Incident Report: .claude/popkit/incidents/incident-20260319-143500.md
Next: Investigate root cause, then /popkit-ops:deploy execute when fixed
```

**Pipeline state after rollback:** Reverts execute state; re-run validate before next execute.

---

## Orchestration Logic

When a subcommand is invoked, the command verifies pipeline prerequisites:

| Subcommand | Prerequisite                                   | On Missing                                         |
| ---------- | ---------------------------------------------- | -------------------------------------------------- |
| init       | None                                           | -                                                  |
| setup      | deploy.json must exist (init completed)        | Prompt: "Run init first? Y/n"                      |
| validate   | Deployment files must exist (setup completed)  | Prompt: "Run setup first? Y/n"                     |
| execute    | Validation should pass (validate completed)    | Prompt: "Run validate first? Y/n" (or --skip-validate) |
| rollback   | Deployment history must exist                  | Error: "No deployment history. Nothing to roll back." |

If a prerequisite is missing, the command offers to run the missing step first, then continues to the requested step. This allows running `/popkit-ops:deploy execute` from a fresh project -- it will walk through init, setup, and validate before executing.

---

## Premium Features

| Feature                | Free | Pro   | Team   |
| ---------------------- | ---- | ----- | ------ |
| init, validate         | yes  | yes   | yes    |
| setup (basic)          | yes  | yes   | yes    |
| setup (custom)         | no   | yes   | yes    |
| execute (local)        | yes  | yes   | yes    |
| execute (cloud)        | no   | yes   | yes    |
| rollback               | no   | yes   | yes    |
| Multi-target deploy    | no   | yes   | yes    |
| Deploy history (cloud) | no   | 7-day | 90-day |

---

## Architecture

| Component              | Integration                                                       |
| ---------------------- | ----------------------------------------------------------------- |
| Deploy Init Skill      | packages/popkit-ops/skills/pop-deploy-init/                       |
| Deploy Setup Skill     | packages/popkit-ops/skills/pop-deploy-setup/                      |
| Deploy Validate Skill  | packages/popkit-ops/skills/pop-deploy-validate/                   |
| Deploy Execute Skill   | packages/popkit-ops/skills/pop-deploy-execute/                    |
| Deploy Rollback Skill  | packages/popkit-ops/skills/pop-deploy-rollback/                   |
| Deploy Config          | .claude/popkit/deploy.json                                        |
| DevOps Agent           | packages/popkit-ops/agents/tier-2-on-demand/devops-automator/     |
| Validator Agent        | packages/popkit-ops/agents/tier-2-on-demand/deployment-validator/ |
| Rollback Agent         | packages/popkit-ops/agents/tier-2-on-demand/rollback-specialist/  |

## Related

| Command                       | Purpose                        |
| ----------------------------- | ------------------------------ |
| `/popkit-core:project init`   | PopKit configuration           |
| `/popkit-dev:git pr`          | Pull request management        |
| `/popkit-dev:git release`     | GitHub releases                |
| `/popkit-dev:routine morning` | Morning routine (deploy check) |
| `/popkit-ops:security scan`   | Pre-deploy security audit      |

## Examples

See examples/deploy/ for: init-examples.md, setup-examples.md, validate-execute-rollback.md, targets.md.
