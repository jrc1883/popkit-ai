# Changelog

All notable changes to the PopKit Deploy plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-20

### Added
- **Initial Release** - Extracted from monolithic PopKit plugin (Issue #574, Epic #580)
- **Command** (1):
  - `/popkit:deploy` - Universal deployment orchestration
    - `init` - Analyze and configure deployment targets
    - `setup` - Generate CI/CD pipelines
    - `validate` - Pre-deployment checks
    - `execute` - Deploy to targets
    - `rollback` - Undo deployments
- **Skills** (13):
  - Core: deploy-init, deploy-history, deploy-rollback, _deploy-shared
  - Cloudflare: cloudflare-dns-manage, cloudflare-pages-deploy, cloudflare-worker-deploy
  - Platforms: deploy-docker, deploy-github-releases, deploy-netlify, deploy-npm, deploy-pypi, deploy-vercel
- **Agents** (3):
  - `devops-automator` - CI/CD automation
  - `deployment-validator` - Pre-deployment validation
  - `rollback-specialist` - Emergency recovery
- **Supported Targets**: Docker, npm, PyPI, Vercel, Netlify, Cloudflare Workers/Pages, GitHub Releases
- **Dependencies**: popkit-shared>=0.1.0

[Unreleased]: https://github.com/jrc1883/popkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jrc1883/popkit/releases/tag/v0.1.0
