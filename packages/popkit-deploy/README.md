# PopKit Deploy

Universal deployment automation plugin for PopKit - orchestrate deployments to Docker, npm/PyPI, Vercel/Netlify, Cloudflare Workers/Pages, and GitHub Releases.

## Overview

PopKit Deploy provides a unified deployment workflow across multiple platforms:

- **Universal Orchestration**: Single workflow for all deployment targets
- **Pre-flight Validation**: Comprehensive checks before deployment
- **Multi-target Deployment**: Deploy to multiple platforms simultaneously
- **Rollback Support**: Undo deployments with one command
- **CI/CD Integration**: Generate GitHub Actions workflows

## Command

| Command | Description |
|---------|-------------|
| `/popkit:deploy` | Universal deployment orchestration (init, setup, validate, execute, rollback) |

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `init` | Analyze project and configure deployment targets |
| `setup` | Generate CI/CD pipeline and target configuration |
| `validate` | Run pre-deployment checks |
| `execute` | Deploy to configured target(s) |
| `rollback` | Undo a deployment |

## Skills

### Core Deployment (3)
- `pop-deploy-init` - Initialize deployment configuration
- `pop-deploy-history` - Track deployment history
- `pop-deploy-rollback` - Rollback management

### Platform-Specific (10)
- `pop-cloudflare-dns-manage` - Cloudflare DNS management
- `pop-cloudflare-pages-deploy` - Deploy to Cloudflare Pages
- `pop-cloudflare-worker-deploy` - Deploy to Cloudflare Workers
- `pop-deploy-docker` - Docker image build and push
- `pop-deploy-github-releases` - GitHub Releases deployment
- `pop-deploy-netlify` - Deploy to Netlify
- `pop-deploy-npm` - Publish to npm registry
- `pop-deploy-pypi` - Publish to PyPI
- `pop-deploy-vercel` - Deploy to Vercel
- `_deploy-shared` - Shared deployment utilities

## Agents

### Tier 2 - On-Demand (3)
- `devops-automator` - CI/CD pipeline generation and automation
- `deployment-validator` - Pre-deployment validation and checks
- `rollback-specialist` - Emergency recovery and rollback

## Supported Deployment Targets

| Target | Build | Publish | Rollback | CI/CD |
|--------|-------|---------|----------|-------|
| **Docker** | ✅ | ✅ | ✅ | ✅ |
| **npm** | ✅ | ✅ | ⚠️ | ✅ |
| **PyPI** | ✅ | ✅ | ❌ | ✅ |
| **Vercel** | ✅ | ✅ | ✅ | ✅ |
| **Netlify** | ✅ | ✅ | ✅ | ✅ |
| **Cloudflare Workers** | ✅ | ✅ | ✅ | ✅ |
| **Cloudflare Pages** | ✅ | ✅ | ✅ | ✅ |
| **GitHub Releases** | ✅ | ✅ | ✅ | ✅ |

## Installation

This plugin is part of the PopKit ecosystem and depends on `popkit-shared`.

```bash
# Install via Claude Code plugin manager
/plugin install popkit-deploy@popkit-marketplace
```

## Usage Examples

```bash
# Initialize deployment configuration
/popkit:deploy init

# Generate CI/CD pipelines
/popkit:deploy setup --template production

# Validate before deployment
/popkit:deploy validate

# Deploy to configured targets
/popkit:deploy execute

# Deploy to specific target
/popkit:deploy execute --target docker

# Deploy to all targets
/popkit:deploy execute --all

# Rollback a deployment
/popkit:deploy rollback

# Rollback to specific version
/popkit:deploy rollback --to v1.2.3
```

## Workflow

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

## Pre-deployment Validation

The `deployment-validator` agent checks:

- ✅ Build succeeds
- ✅ Tests pass
- ✅ Linting passes
- ✅ Type checking passes
- ✅ Security scan clean
- ✅ No hardcoded secrets
- ✅ Configuration valid
- ✅ Dependencies resolved

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

## Dependencies

- `popkit-shared>=0.1.0` - Shared utilities package
- Platform-specific CLIs as needed:
  - Docker CLI for Docker deployments
  - Vercel CLI for Vercel deployments
  - Netlify CLI for Netlify deployments
  - Wrangler CLI for Cloudflare deployments

## Development Status

**Version**: 0.1.0 (Beta)
**Phase**: 5 of 8 (Plugin Modularization - Epic #580)

## License

MIT

## Author

Joseph Cannon <joseph@thehouseofdeals.com>
