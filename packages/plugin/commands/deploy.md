---
description: "init | setup | validate | execute | rollback [--target, --all, --dry-run]"
argument-hint: "<subcommand> [target] [options]"
---

# /popkit:deploy - Universal Deployment Orchestration

Deploy to any target: Docker, npm/PyPI, Vercel/Netlify, or GitHub Releases.

## Subcommands

| Subcommand | Description |
|------------|-------------|
| init (default) | Analyze project and configure deployment targets |
| setup | Generate CI/CD pipeline and target configuration |
| validate | Run pre-deployment checks |
| execute | Deploy to target(s) |
| rollback | Undo a deployment |

---

## init (default)

Analyze project state, identify deployment targets, configure `.claude/popkit/deploy.json`.

**Process:** Check PopKit → Front-load user intent (AskUserQuestion: project type, targets, state) → Store configuration.

**Output:** Configuration summary, next steps for setup.

**Options:** --force, --skip-github, --json

---

## setup

Generate CI/CD and target configuration. Invokes **devops-automator** agent.

| Target | Files Generated |
|--------|-----------------|
| Docker | Dockerfile, docker-compose.yml, .dockerignore, CI workflow |
| Vercel | vercel.json, preview deployment workflow |
| Netlify | netlify.toml, deployment workflow |
| npm | Validates package.json, npm-publish.yml |
| PyPI | Validates pyproject.toml, pypi-publish.yml |
| GitHub Releases | release.yml, asset configuration |

**Templates:** minimal (basic), standard (+ CI), production (+ caching, security).

**Options:** --dry-run, --no-commit, --template <level>, --all

---

## validate

Run pre-deployment checks. Invokes **deployment-validator** agent.

**Checks:** Build, Tests, Lint, TypeCheck, Security, Secrets, Config, Dependencies.

**Output:** Validation report with pass/fail/warnings, auto-fix option.

**Options:** --target <name>, --quick, --fix, --strict

---

## execute

Deploy to configured target(s).

**Process:** Pre-flight validation → Confirm (AskUserQuestion) → Execute per target → Post-deploy validation → Record history.

**Execution by target:**
- Docker: Build and push image
- Vercel: Trigger deployment via CLI/CI
- npm: Publish to registry

**Output:** Deployment progress, completion summary, rollback availability.

**Options:** --target <name>, --all, --dry-run, --yes, --version <ver>, --skip-validate, --watch

---

## rollback

Undo deployment and restore previous version. Invokes **rollback-specialist** agent.

**Process:** Load history → Present options (AskUserQuestion) → Execute rollback → Verify.

**Rollback by target:**
- Docker: Re-tag previous image
- Vercel: Revert to previous deployment
- npm: Deprecate current, unpublish if within 24h

**Options:** --to <version>, --target <name>, --list, --yes

---

## Premium Features

| Feature | Free | Pro | Team |
|---------|------|-----|------|
| init, validate | ✅ | ✅ | ✅ |
| setup (basic) | ✅ | ✅ | ✅ |
| setup (custom) | ❌ | ✅ | ✅ |
| execute (local) | ✅ | ✅ | ✅ |
| execute (cloud) | ❌ | ✅ | ✅ |
| rollback | ❌ | ✅ | ✅ |
| Multi-target deploy | ❌ | ✅ | ✅ |
| Deploy history (cloud) | ❌ | 7-day | 90-day |

---

## Workflow Integration

```
/popkit:project init       → PopKit configuration
         ↓
/popkit:deploy init        → Deployment targets
         ↓
/popkit:deploy setup       → Generate configs
         ↓
/popkit:deploy validate    → Pre-flight checks
         ↓
/popkit:deploy execute     → Ship it!
         ↓
/popkit:deploy rollback    → Undo if needed
```

---

## Architecture

| Component | Integration |
|-----------|-------------|
| Deploy Init Skill | skills/pop-deploy-init/ |
| Deploy Config | .claude/popkit/deploy.json |
| DevOps Agent | agents/tier-2-on-demand/devops-automator/ |
| Validator Agent | agents/tier-2-on-demand/deployment-validator/ |
| Rollback Agent | agents/tier-2-on-demand/rollback-specialist/ |
| Premium Gating | hooks/utils/premium_checker.py |

**Related:** /popkit:git pr, /popkit:git release, /popkit:routine morning

## Examples

See examples/deploy/ for: init-examples.md, setup-examples.md, validate-execute-rollback.md, targets.md.
