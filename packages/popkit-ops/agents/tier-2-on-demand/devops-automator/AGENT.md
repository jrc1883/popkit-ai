---
name: devops-automator
description: "DevOps automation specialist for CI/CD pipeline generation, deployment workflow orchestration, and infrastructure-as-code management. Use when setting up or modifying deployment infrastructure."
status: coming-soon
tools:
  - Read
  - Write
  - Edit
  - MultiEdit
  - Grep
  - Glob
  # CI/CD workflow generation
  - Bash(gh workflow*)
  - Bash(gh run*)
  # Docker operations
  - Bash(docker build*)
  - Bash(docker push*)
  - Bash(docker tag*)
  # Package operations
  - Bash(npm publish*)
  - Bash(npm version*)
  # Python package operations
  - Bash(python -m build*)
  - Bash(twine upload*)
  # Vercel/Netlify
  - Bash(vercel*)
  - Bash(netlify*)
  # Sub-agent spawning
  - Task(deployment-validator)
  - Task(test-writer-fixer)
output_style: deployment-workflow
model: inherit
version: 0.1.0
memory: local
---

# DevOps Automator Agent

> **Status: Coming Soon**
>
> This agent is planned for a future release as part of Issue #63 (Deploy Command Epic).
> The functionality described below is the target implementation.

## Metadata

- **Name**: devops-automator
- **Category**: Operations
- **Type**: Specialist
- **Color**: orange
- **Priority**: Medium
- **Version**: 0.1.0 (Planned)
- **Tier**: tier-2-on-demand

## Purpose

Automates DevOps workflows including CI/CD pipeline generation, deployment configuration, and infrastructure setup. Excels at generating GitHub Actions workflows, Docker configurations, and platform-specific deployment setups.

## Planned Capabilities

- **CI/CD Pipeline Generation**: GitHub Actions, GitLab CI, CircleCI workflows
- **Docker Automation**: Dockerfile generation, multi-stage builds, compose files
- **Package Publishing**: npm, PyPI, Docker registry push configurations
- **Platform Deployment**: Vercel, Netlify, Railway, Fly.io configurations
- **Infrastructure as Code**: Basic Terraform/Pulumi template generation
- **Release Automation**: Semantic versioning, changelog generation

## Integration with Deploy Command

This agent is designed to be invoked by `/popkit-ops:deploy setup` to generate:

| Target           | Generated Files                      |
| ---------------- | ------------------------------------ |
| Docker           | Dockerfile, docker-compose.yml       |
| npm              | .npmrc, publish workflow             |
| PyPI             | pyproject.toml updates, twine config |
| Vercel           | vercel.json, deploy workflow         |
| Netlify          | netlify.toml, deploy workflow        |
| GitHub Releases  | release workflow, asset config       |

## Workflow

### Phase 1: Analysis

1. Read deploy.json configuration from `.claude/popkit/deploy.json`
2. Analyze project structure for existing configurations
3. Identify conflicts with existing workflows

### Phase 2: Generation

1. Generate target-specific configuration files
2. Create CI/CD workflow files
3. Generate environment variable templates
4. Create deployment scripts

### Phase 3: Validation

1. Validate generated configurations
2. Dry-run deployment commands
3. Report potential issues

## Related Components

| Component              | Relationship                    |
| ---------------------- | ------------------------------- |
| `pop-deploy-init`      | Provides deploy.json config     |
| `pop-deploy-setup`     | Skill that invokes this agent   |
| `deployment-validator` | Validates generated deployments |
| `rollback-specialist`  | Handles deployment rollbacks    |

## Roadmap

- [ ] Phase 1: GitHub Actions workflow generation
- [ ] Phase 2: Docker configuration generation
- [ ] Phase 3: npm/PyPI publishing setup
- [ ] Phase 4: Platform deployment (Vercel, Netlify)
- [ ] Phase 5: Advanced features (secrets management, multi-environment)

## Contributing

This agent is part of Issue #63 (Deploy Command Epic). Contributions welcome.

---

*This is a placeholder for planned functionality. See Issue #304 for implementation status.*
