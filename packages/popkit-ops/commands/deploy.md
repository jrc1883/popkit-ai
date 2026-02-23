---
description: "init | setup | validate | execute | rollback [--target, --all, --dry-run]"
argument-hint: "<subcommand> [target] [options]"
---

# /popkit-ops:deploy - Universal Deployment Orchestration

Deploy to any target: Docker, npm/PyPI, Vercel/Netlify, or GitHub Releases.

## Subcommands

| Subcommand     | Description                                      | Status         |
| -------------- | ------------------------------------------------ | -------------- |
| init (default) | Analyze project and configure deployment targets | ✅ Available   |
| setup          | Generate CI/CD pipeline and target configuration | 🚧 Coming Soon |
| validate       | Run pre-deployment checks                        | 🚧 Coming Soon |
| execute        | Deploy to target(s)                              | 🚧 Coming Soon |
| rollback       | Undo a deployment                                | 🚧 Coming Soon |

---

## init (default)

Analyze project state, identify deployment targets, configure `.claude/popkit/deploy.json`.

**Invokes:** `pop-deploy-init` skill

**Process:**

1. Run `scripts/detect_deploy_targets.py` to identify available targets
2. Present detected targets via AskUserQuestion (multiSelect)
3. Set primary target if multiple selected
4. Configure CI/CD trigger mode (GitHub Actions, manual, both)
5. Create `.claude/popkit/deploy.json` configuration
6. Optionally proceed to setup

**Output:** Configuration summary, next steps for setup.

**Options:**

| Flag            | Description                              |
| --------------- | ---------------------------------------- |
| `--force`       | Overwrite existing config without backup |
| `--skip-github` | Skip GitHub-related detection            |
| `--json`        | Output JSON instead of formatted text    |

---

## setup

> **🚧 Coming Soon** - This subcommand is planned. See Issue #305 for status.

Generate CI/CD and target configuration. Invokes **devops-automator** agent.

| Target          | Files Generated                                            |
| --------------- | ---------------------------------------------------------- |
| Docker          | Dockerfile, docker-compose.yml, .dockerignore, CI workflow |
| Vercel          | vercel.json, preview deployment workflow                   |
| Netlify         | netlify.toml, deployment workflow                          |
| npm             | Validates package.json, npm-publish.yml                    |
| PyPI            | Validates pyproject.toml, pypi-publish.yml                 |
| GitHub Releases | release.yml, asset configuration                           |

**Templates:** minimal (basic), standard (+ CI), production (+ caching, security).

**Options:** --dry-run, --no-commit, --template <level>, --all

---

## validate

> **🚧 Coming Soon** - This subcommand is planned. See Issue #305 for status.

Run pre-deployment checks. Invokes **deployment-validator** agent.

**Checks:** Build, Tests, Lint, TypeCheck, Security, Secrets, Config, Dependencies.

**Output:** Validation report with pass/fail/warnings, auto-fix option.

**Options:** --target <name>, --quick, --fix, --strict

---

## execute

> **🚧 Coming Soon** - This subcommand is planned. See Issue #305 for status.

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

> **🚧 Coming Soon** - This subcommand is planned. See Issue #305 for status.

Undo deployment and restore previous version. Invokes **rollback-specialist** agent.

**Process:** Load history → Present options (AskUserQuestion) → Execute rollback → Verify.

**Rollback by target:**

- Docker: Re-tag previous image
- Vercel: Revert to previous deployment
- npm: Deprecate current, unpublish if within 24h

**Options:** --to <version>, --target <name>, --list, --yes

---

## Premium Features

| Feature                | Free | Pro   | Team   |
| ---------------------- | ---- | ----- | ------ |
| init, validate         | ✅   | ✅    | ✅     |
| setup (basic)          | ✅   | ✅    | ✅     |
| setup (custom)         | ❌   | ✅    | ✅     |
| execute (local)        | ✅   | ✅    | ✅     |
| execute (cloud)        | ❌   | ✅    | ✅     |
| rollback               | ❌   | ✅    | ✅     |
| Multi-target deploy    | ❌   | ✅    | ✅     |
| Deploy history (cloud) | ❌   | 7-day | 90-day |

---

## Workflow Integration

```
/popkit-core:project init       → PopKit configuration
         ↓
/popkit-ops:deploy init        → Deployment targets
         ↓
/popkit-ops:deploy setup       → Generate configs
         ↓
/popkit-ops:deploy validate    → Pre-flight checks
         ↓
/popkit-ops:deploy execute     → Ship it!
         ↓
/popkit-ops:deploy rollback    → Undo if needed
```

---

## Architecture

| Component         | Integration                                                       |
| ----------------- | ----------------------------------------------------------------- |
| Deploy Init Skill | packages/popkit-ops/skills/pop-deploy-init/                       |
| Deploy Config     | .claude/popkit/deploy.json                                        |
| DevOps Agent      | packages/popkit-ops/agents/tier-2-on-demand/devops-automator/     |
| Validator Agent   | packages/popkit-ops/agents/tier-2-on-demand/deployment-validator/ |
| Rollback Agent    | packages/popkit-ops/agents/tier-2-on-demand/rollback-specialist/  |

**Related:** /popkit-dev:git pr, /popkit-dev:git release, /popkit-dev:routine morning

## Examples

See examples/deploy/ for: init-examples.md, setup-examples.md, validate-execute-rollback.md, targets.md.
