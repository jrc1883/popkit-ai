# /popkit:deploy Command Design

**Date:** 2025-12-10
**Status:** Design Complete - Ready for Implementation
**Author:** Claude Code (Opus 4.5) + Joseph Cannon
**Related Research:** `RESEARCH_ONBOARDING_DEPLOYMENT.md`

---

## Executive Summary

Create a universal deployment command that adapts to any project state - from no GitHub to professional CI/CD - and supports multiple deployment targets (Docker, npm, Vercel, GitHub Releases).

**Key Decisions:**
- 5 core subcommands: `init`, `setup`, `validate`, `execute`, `rollback`
- 4 deployment targets for v1: Docker, npm/PyPI, Vercel/Netlify, GitHub Releases
- Progressive disclosure based on detected project state
- Complements `/popkit:git` (deploy = targets, git = workflow)
- Premium feature gating for advanced features

---

## Table of Contents

1. [Command Philosophy](#1-command-philosophy)
2. [Subcommand Reference](#2-subcommand-reference)
3. [Deployment Targets](#3-deployment-targets)
4. [Premium Feature Gating](#4-premium-feature-gating)
5. [Agent Orchestration](#5-agent-orchestration)
6. [Hook Integration](#6-hook-integration)
7. [State Management](#7-state-management)
8. [Gap Fixes Required](#8-gap-fixes-required)
9. [Implementation Epics](#9-implementation-epics)

---

## 1. Command Philosophy

### Progressive Disclosure

The command adapts based on detected project state:

| User State | What They See |
|------------|---------------|
| No GitHub, no CI/CD | Guided setup from scratch |
| GitHub exists, no CI/CD | CI/CD generation focus |
| CI/CD exists, no deploy config | Target configuration focus |
| Everything exists | Orchestration shortcuts |

### Relationship to Other Commands

```
/popkit:project init    → PopKit plugin configuration
         ↓
/popkit:deploy init     → Deployment infrastructure
         ↓
/popkit:deploy setup    → Target-specific configs
         ↓
/popkit:git pr          → Code workflow (separate concern)
```

**Key principle:** Deploy focuses on WHERE code goes. Git focuses on HOW code moves.

### Power Mode Naming (Updated)

| Old Name | New Name | Description |
|----------|----------|-------------|
| Redis Mode | **PopKit Cloud** | Hosted infrastructure (Pro/Team) |
| File Mode | **Local Mode** | File-based coordination (Free) |

Users don't need to know our tech stack (Upstash Redis). They just see "Cloud = zero setup" vs "Local = works offline."

---

## 2. Subcommand Reference

### 2.1 `init` (default)

**Purpose:** Analyze project state and establish deployment readiness.

```bash
/popkit:deploy                        # Auto-runs init if unconfigured
/popkit:deploy init                   # Explicit init
/popkit:deploy init --force           # Re-analyze even if configured
```

**Process:**

1. **Check PopKit Initialization**
   - Verify `.claude/popkit/` exists
   - Verify CLAUDE.md has PopKit markers
   - Offer to fix gaps if found

2. **Front-load User Intent** (single multi-question AskUserQuestion)

   ```
   Q1: "What type of project are you deploying?" [header: "Project"]
   Options:
   - Web application (frontend/fullstack/SSR)
   - Backend API/service
   - CLI tool or library
   - Other (describe your project type)

   Q2: "Where do you want to deploy?" [header: "Targets", multiSelect: true]
   Options:
   - Docker (universal - any server/cloud)
   - Vercel/Netlify (frontend hosting)
   - npm/PyPI registry (package publishing)
   - GitHub Releases (binary artifacts)

   Q3: "What's your current deployment setup?" [header: "State"]
   Options:
   - Starting fresh (no GitHub, no CI/CD)
   - Have GitHub, need CI/CD
   - Have CI/CD, need target config
   - Everything exists (just orchestrate)
   ```

3. **Store Configuration**
   ```json
   // .claude/popkit/deploy.json
   {
     "version": "1.0",
     "project_type": "web-app",
     "targets": ["docker", "vercel"],
     "state": "needs-cicd",
     "initialized_at": "2025-12-10T...",
     "initialized_by": "popkit-1.2.0",
     "github": {
       "repo": "owner/repo",
       "default_branch": "main",
       "has_actions": true
     },
     "history": []
   }
   ```

**Flags:**

| Flag | Description |
|------|-------------|
| `--force` | Re-run analysis even if config exists |
| `--skip-github` | Don't offer GitHub setup |
| `--json` | Output config as JSON |

---

### 2.2 `setup`

**Purpose:** Configure CI/CD pipeline and deployment target(s).

```bash
/popkit:deploy setup                  # Interactive setup for all targets
/popkit:deploy setup docker           # Setup Docker specifically
/popkit:deploy setup vercel           # Setup Vercel specifically
/popkit:deploy setup npm              # Setup npm publishing
/popkit:deploy setup pypi             # Setup PyPI publishing
/popkit:deploy setup github-releases  # Setup GitHub Releases
/popkit:deploy setup --all            # Setup all configured targets
```

**Process:**

1. Load config from `deploy.json`
2. For each target, generate appropriate files (see Section 3)
3. Optionally commit generated files

**Files Generated Per Target:**

| Target | Files Generated |
|--------|-----------------|
| Docker | `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.github/workflows/docker-publish.yml` |
| Vercel | `vercel.json`, `.github/workflows/preview-deploy.yml` |
| Netlify | `netlify.toml`, `.github/workflows/netlify-deploy.yml` |
| npm | Validates `package.json`, `.github/workflows/npm-publish.yml`, `.npmrc` template |
| PyPI | Validates `pyproject.toml`, `.github/workflows/pypi-publish.yml` |
| GitHub Releases | `.github/workflows/release.yml`, asset configuration |

**Flags:**

| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would be generated |
| `--no-commit` | Generate files but don't commit |
| `--template <name>` | Use template: `minimal`, `standard`, `production` |

**Agent Integration:** Uses `devops-automator` agent for infrastructure generation.

---

### 2.3 `validate`

**Purpose:** Pre-deployment checks.

```bash
/popkit:deploy validate               # Run all checks
/popkit:deploy validate --target docker
/popkit:deploy validate --quick       # Fast checks only
/popkit:deploy validate --fix         # Auto-fix what's possible
```

**Checks Performed:**

| Check | Description | Auto-fix? |
|-------|-------------|-----------|
| Build | Project builds successfully | No |
| Tests | Test suite passes | No |
| Lint | No lint errors | Yes |
| TypeCheck | No type errors | No |
| Security | No critical vulnerabilities | Partial |
| Secrets | No exposed credentials | No |
| Config | Deployment config valid | Yes |
| Dependencies | All deps available | Yes |

**Output:**
```
Validation Report:
├─ Build:      ✅ Pass (12s)
├─ Tests:      ✅ 47/47 passing (45s)
├─ Lint:       ⚠️ 2 warnings (auto-fixed)
├─ TypeCheck:  ✅ No errors
├─ Security:   ✅ No vulnerabilities
├─ Secrets:    ✅ No exposure detected
├─ Config:     ✅ Valid for docker, vercel
└─ Deps:       ✅ All available

Ready to deploy: Yes
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--target <name>` | Validate for specific target |
| `--quick` | Skip slow checks (full test suite) |
| `--fix` | Auto-fix fixable issues |
| `--strict` | Fail on warnings too |

**Agent Integration:** Uses `deployment-validator` agent.

---

### 2.4 `execute`

**Purpose:** Run deployment to target(s).

```bash
/popkit:deploy execute                # Deploy to default target
/popkit:deploy execute docker         # Deploy Docker image
/popkit:deploy execute vercel         # Deploy to Vercel
/popkit:deploy execute npm            # Publish to npm
/popkit:deploy execute --all          # Deploy to all targets
/popkit:deploy execute --dry-run      # Show what would happen
```

**Process:**

1. **Pre-flight** (automatic validate)
2. **Confirm** (unless `--yes`)
   ```
   Deploy to: docker, vercel
   Version: 1.2.0
   Branch: main

   Proceed? [Y/n]
   ```
3. **Execute** per target
4. **Post-deploy validation** (health checks, smoke tests)
5. **Record history** for rollback

**Flags:**

| Flag | Description |
|------|-------------|
| `--target <name>` | Deploy to specific target |
| `--all` | Deploy to all configured targets |
| `--dry-run` | Show what would happen |
| `--yes` | Skip confirmation |
| `--version <ver>` | Override version |
| `--skip-validate` | Skip pre-flight checks (dangerous) |
| `--watch` | Watch deployment progress |

**Agent Integration:**
- `deployment-validator` for pre/post checks
- May trigger `/popkit:git ci watch` for CI-based deploys
- May call `/popkit:git release create` for GitHub releases

---

### 2.5 `rollback`

**Purpose:** Undo a deployment.

```bash
/popkit:deploy rollback               # Rollback last deployment
/popkit:deploy rollback docker        # Rollback Docker specifically
/popkit:deploy rollback --to v1.1.0   # Rollback to specific version
/popkit:deploy rollback --list        # Show rollback history
```

**Process:**

1. Load history from `deploy.json`
2. Show options via AskUserQuestion
3. Execute rollback per target
4. Verify with health checks

**Flags:**

| Flag | Description |
|------|-------------|
| `--to <version>` | Rollback to specific version |
| `--target <name>` | Rollback specific target only |
| `--list` | Show rollback history |
| `--yes` | Skip confirmation |

**Agent Integration:** Uses `rollback-specialist` agent if available.

---

## 3. Deployment Targets

### 3.1 Docker (Universal)

**Scope:** Any server/cloud that runs containers

**Generated Files:**
- `Dockerfile` (multi-stage, optimized)
- `docker-compose.yml` (dev environment)
- `.dockerignore`
- `.github/workflows/docker-publish.yml`

**Execution:**
- Build image locally or trigger CI
- Push to registry (Docker Hub, GHCR, ECR)
- Optionally deploy to cloud (AWS ECS, GCP Cloud Run, etc.)

### 3.2 Vercel/Netlify (Frontend)

**Scope:** Static sites, SSR, serverless functions

**Generated Files:**
- `vercel.json` or `netlify.toml`
- Environment variable templates
- `.github/workflows/preview-deploy.yml`

**Execution:**
- Trigger deployment via CLI or CI
- Handle preview deployments for PRs
- Production deployment on main branch

### 3.3 npm/PyPI (Packages)

**Scope:** Library/package publishing

**Generated Files:**
- Validates `package.json` / `pyproject.toml`
- `.github/workflows/npm-publish.yml` or `pypi-publish.yml`
- `.npmrc` / `~/.pypirc` template instructions

**Execution:**
- Version bump assistance
- Changelog generation
- Registry publish (directly or via CI)

### 3.4 GitHub Releases (Binaries)

**Scope:** CLI tools, compiled artifacts

**Generated Files:**
- `.github/workflows/release.yml`
- Release asset configuration
- Changelog automation

**Execution:**
- Create GitHub release
- Upload compiled assets
- Generate release notes from commits

---

## 4. Premium Feature Gating

### Tier Matrix

| Feature | Free | Pro ($9/mo) | Team ($29/mo) |
|---------|------|-------------|---------------|
| `deploy init` | ✅ | ✅ | ✅ |
| `deploy validate` | ✅ | ✅ | ✅ |
| `deploy setup` (basic templates) | ✅ | ✅ | ✅ |
| `deploy setup` (custom configs) | ❌ | ✅ | ✅ |
| `deploy execute` (local) | ✅ | ✅ | ✅ |
| `deploy execute` (cloud trigger) | ❌ | ✅ | ✅ |
| `deploy rollback` | ❌ | ✅ | ✅ |
| Multi-target deploy | ❌ | ✅ | ✅ |
| Deploy history (cloud) | ❌ | 7-day | 90-day |
| Team deploy coordination | ❌ | ❌ | ✅ |

### Implementation

```python
# In hooks/utils/premium_checker.py
DEPLOY_FEATURES = {
    "deploy:init": "free",
    "deploy:validate": "free",
    "deploy:setup:basic": "free",
    "deploy:setup:custom": "pro",
    "deploy:execute:local": "free",
    "deploy:execute:cloud": "pro",
    "deploy:rollback": "pro",
    "deploy:multi-target": "pro",
    "deploy:history:7day": "pro",
    "deploy:history:90day": "team",
    "deploy:team-coordination": "team"
}
```

---

## 5. Agent Orchestration

### Primary Agents

| Agent | Role in Deploy |
|-------|----------------|
| `devops-automator` | Generate CI/CD configs, Dockerfiles, infrastructure |
| `deployment-validator` | Pre/post deployment checks, smoke tests, canary |
| `rollback-specialist` | Recovery procedures, safe rollback |
| `security-auditor` | Secrets scanning, vulnerability checks |

### Orchestration Pattern

```
deploy init
    └─→ (no agent - config gathering only)

deploy setup
    └─→ devops-automator
        ├─ Analyze project
        ├─ Generate Dockerfile
        ├─ Generate CI/CD workflow
        └─ Configure target

deploy validate
    └─→ deployment-validator
        ├─ Pre-flight checks
        ├─ Security scan
        └─ Config validation

deploy execute
    └─→ deployment-validator (pre)
    └─→ devops-automator (if CI trigger)
    └─→ deployment-validator (post)

deploy rollback
    └─→ rollback-specialist
        ├─ Version selection
        ├─ Safe rollback
        └─ Verification
```

### Power Mode Integration

When Power Mode is active, deploy can coordinate multiple agents:

```
deploy execute --all (with Power Mode)
    ├─→ Agent 1: Docker deployment
    ├─→ Agent 2: Vercel deployment (parallel)
    └─→ Agent 3: npm publish (parallel)

    Sync barrier: Wait for all targets

    └─→ All agents: Post-deploy verification
```

---

## 6. Hook Integration

### Pre-Tool-Use Hook

```python
# In pre-tool-use.py
def check_deploy_command(tool_input):
    """Validate deploy commands before execution."""

    if tool_input.get("command", "").startswith("/popkit:deploy"):
        # Check PopKit initialization
        if not check_popkit_initialized():
            return {
                "decision": "block",
                "message": "PopKit not fully initialized. Run /popkit:project init first."
            }

        # Check premium features
        subcommand = parse_deploy_subcommand(tool_input)
        if requires_premium(subcommand):
            tier = get_user_tier()
            if not has_access(tier, subcommand):
                return {
                    "decision": "block",
                    "message": f"This feature requires {required_tier(subcommand)}. Upgrade at /popkit:upgrade"
                }

    return {"decision": "allow"}
```

### Post-Tool-Use Hook

```python
# In post-tool-use.py
def track_deployment(tool_output):
    """Record deployment for history and metrics."""

    if is_deploy_execute(tool_output):
        deployment = {
            "version": extract_version(tool_output),
            "targets": extract_targets(tool_output),
            "timestamp": datetime.now().isoformat(),
            "status": extract_status(tool_output),
            "duration": extract_duration(tool_output)
        }

        # Update deploy.json history
        update_deploy_history(deployment)

        # Send to PopKit Cloud (Pro+)
        if get_user_tier() in ["pro", "team"]:
            send_to_cloud("/v1/deployments", deployment)
```

### Session-Start Hook

```python
# In session-start.py
def check_deployment_state():
    """Check for pending deployments or rollback needs."""

    deploy_config = load_deploy_config()

    if deploy_config and deploy_config.get("last_deployment"):
        last = deploy_config["last_deployment"]

        # Check if last deployment had issues
        if last.get("status") == "failed":
            return {
                "reminder": f"Last deployment to {last['targets']} failed. Consider /popkit:deploy rollback"
            }
```

---

## 7. State Management

### Configuration Storage

```
.claude/
├── popkit/
│   ├── config.json          # Project-wide PopKit config
│   ├── state.json           # Session state
│   └── deploy.json          # Deployment configuration ← NEW
```

### deploy.json Schema

```json
{
  "version": "1.0",
  "project_type": "web-app",
  "targets": ["docker", "vercel"],
  "state": "configured",
  "initialized_at": "2025-12-10T10:00:00Z",
  "initialized_by": "popkit-1.2.0",

  "github": {
    "repo": "owner/repo",
    "default_branch": "main",
    "has_actions": true
  },

  "target_configs": {
    "docker": {
      "registry": "ghcr.io",
      "image_name": "owner/repo",
      "dockerfile": "Dockerfile"
    },
    "vercel": {
      "project_id": "prj_xxx",
      "team_id": null
    }
  },

  "history": [
    {
      "version": "1.2.0",
      "targets": ["docker", "vercel"],
      "timestamp": "2025-12-10T15:00:00Z",
      "status": "success",
      "duration_seconds": 154,
      "commit": "abc123",
      "rollback_available": true
    }
  ],

  "last_deployment": {
    "version": "1.2.0",
    "timestamp": "2025-12-10T15:00:00Z",
    "status": "success"
  }
}
```

---

## 8. Gap Fixes Required

### Critical Issues from Daniel-Son Analysis

| Issue | Severity | Description | Fix Location |
|-------|----------|-------------|--------------|
| **No `.claude/popkit/` directory** | HIGH | PopKit runtime directory not created | `pop-project-init` skill |
| **CLAUDE.md missing markers** | HIGH | No `<!-- POPKIT:START/END -->` markers | `pop-project-init` skill |
| **settings.json missing PopKit fields** | MEDIUM | No tier, features, competency fields | `pop-project-init` skill |
| **STATUS.json schema mismatch** | MEDIUM | Doesn't match pop-session-capture expectations | `pop-project-init` skill |
| **Power Mode naming** | LOW | "Redis Mode" confusing - should be "PopKit Cloud" | All references |

### Deploy-Init Gap Handling

The `deploy init` command must check and offer to fix these gaps:

```
PopKit deployment readiness check:

⚠️ Missing: .claude/popkit/ directory
⚠️ Missing: CLAUDE.md PopKit markers
⚠️ Missing: PopKit fields in settings.json

These are required for deployment features to work properly.

Would you like to fix these now?
- Yes, fix and continue (Recommended)
- Skip, continue anyway (may cause issues)
- Cancel
```

---

## 9. Implementation Epics

### Epic 1: Fix Project Initialization (Blocking)

**Priority:** P0-Critical (blocks all other work)

| Issue | Description | Estimate |
|-------|-------------|----------|
| 1.1 | Create `.claude/popkit/` directory in project init | S |
| 1.2 | Add PopKit markers to CLAUDE.md (surgical update) | M |
| 1.3 | Add PopKit fields to settings.json schema | S |
| 1.4 | Update STATUS.json schema to match session capture | S |
| 1.5 | Rename "Redis Mode" → "PopKit Cloud" everywhere | S |
| 1.6 | Update Power Mode prompt to use new naming | S |

### Epic 2: Deploy Command Core

**Priority:** P1-High

| Issue | Description | Estimate |
|-------|-------------|----------|
| 2.1 | Create `commands/deploy.md` with subcommand routing | M |
| 2.2 | Implement `deploy init` with gap checking | L |
| 2.3 | Implement `deploy validate` with check framework | M |
| 2.4 | Create deploy.json schema and storage | S |
| 2.5 | Add premium feature gating for deploy | M |

### Epic 3: Docker Target

**Priority:** P1-High

| Issue | Description | Estimate |
|-------|-------------|----------|
| 3.1 | `deploy setup docker` - Dockerfile generation | L |
| 3.2 | Docker Compose generation for dev | M |
| 3.3 | GitHub Actions workflow for Docker publish | M |
| 3.4 | `deploy execute docker` implementation | L |
| 3.5 | Docker rollback support | M |

### Epic 4: Vercel/Netlify Target

**Priority:** P2-Medium

| Issue | Description | Estimate |
|-------|-------------|----------|
| 4.1 | `deploy setup vercel` - vercel.json generation | M |
| 4.2 | `deploy setup netlify` - netlify.toml generation | M |
| 4.3 | Preview deployment workflow | M |
| 4.4 | `deploy execute vercel/netlify` implementation | M |

### Epic 5: Package Registry Targets (npm/PyPI)

**Priority:** P2-Medium

| Issue | Description | Estimate |
|-------|-------------|----------|
| 5.1 | `deploy setup npm` - package.json validation | M |
| 5.2 | `deploy setup pypi` - pyproject.toml validation | M |
| 5.3 | npm publish workflow | M |
| 5.4 | PyPI publish workflow | M |
| 5.5 | Version bump assistance | S |

### Epic 6: GitHub Releases Target

**Priority:** P2-Medium

| Issue | Description | Estimate |
|-------|-------------|----------|
| 6.1 | `deploy setup github-releases` | M |
| 6.2 | Release workflow generation | M |
| 6.3 | Asset upload configuration | S |
| 6.4 | Integration with `/popkit:git release` | M |

### Epic 7: Rollback & History

**Priority:** P2-Medium (Pro feature)

| Issue | Description | Estimate |
|-------|-------------|----------|
| 7.1 | Deployment history tracking | M |
| 7.2 | `deploy rollback` implementation | L |
| 7.3 | Cloud history sync (Pro+) | M |
| 7.4 | Rollback verification | M |

### Epic 8: Documentation & Morning Routine

**Priority:** P3-Low

| Issue | Description | Estimate |
|-------|-------------|----------|
| 8.1 | Auto-documentation for deploy changes | M |
| 8.2 | Morning routine: check deployment dependencies | S |
| 8.3 | Research monitoring for Vercel/npm/Docker changes | M |

---

## Appendix A: Research Integration

Per Taskmaster competitor analysis, consider future additions:

- **Research-backed deployment** - Query current best practices before generating configs
- **Complexity analysis** - Score deployment complexity to recommend approach
- **Preflight validation** - Comprehensive pre-deployment checks

These are post-v1 enhancements documented in `docs/taskmaster-innovation-gaps.md`.

---

## Appendix B: Power Mode Deployment

When Power Mode is active, multi-target deployments can parallelize:

```
/popkit:deploy execute --all

Agent Mesh:
├─ docker-deploy-agent: Building and pushing image
├─ vercel-deploy-agent: Triggering Vercel deployment
├─ npm-publish-agent: Publishing to npm registry
│
├─ [SYNC BARRIER: All targets complete]
│
└─ validation-agent: Running smoke tests on all targets
```

This requires Power Mode v2 (Issue #66) to be complete.

---

## Approval

- [ ] Design reviewed
- [ ] Epics created in GitHub
- [ ] Linked to project board
- [ ] Ready for implementation

---

*Document generated during PopKit brainstorming session. See skill `pop-brainstorming` for methodology.*
