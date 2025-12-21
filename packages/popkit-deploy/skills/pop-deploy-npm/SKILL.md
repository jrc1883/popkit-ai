---
name: deploy-npm
description: "Use when publishing packages to npm - validates package.json, generates publish workflows, handles version bumps, and supports scoped packages and private registries. Includes changelog integration and dry-run support."
---

# npm Package Publishing

## Overview

Configure npm package publishing with proper validation, versioning, and secure authentication. Generates GitHub Actions workflows for automated releases.

**Core principle:** Never publish broken packages. Validate everything before release.

## Critical Rules

| Rule | Details |
|------|---------|
| **ALWAYS validate package.json** | Required fields must be present and correct |
| **NEVER publish without tests** | CI must gate releases |
| **Use NPM_TOKEN for auth** | Never commit tokens, use GitHub secrets |
| **Respect semver** | Breaking = major, features = minor, fixes = patch |
| **Include only necessary files** | Use `files` field or `.npmignore` |

## Process

### Step 1: Validate package.json

Run validation script to check for required/recommended fields.

**Required:** name, version, description
**Recommended:** main, repository, license, keywords, author

[See validation script](examples/npm/validate_package.py)

### Step 2: Ask About Package Type

```
Use AskUserQuestion tool with:
- question: "What type of npm package are you publishing?"
- header: "Package Type"
- options:
  - label: "Public package"
    description: "Standard npm package, open source"
  - label: "Scoped package (@org/package)"
    description: "Organization or user-scoped package"
  - label: "TypeScript package"
    description: "Package with TypeScript definitions"
  - label: "Private package"
    description: "Requires npm Pro/Teams subscription"
- multiSelect: false
```

### Step 3: Generate Files

| File | Purpose |
|------|---------|
| `.github/workflows/npm-publish.yml` | Automated publish on release |
| `.github/workflows/npm-publish-manual.yml` | Manual publish with version selection |
| `.npmrc` | npm configuration (registry, scope) |
| `.npmignore` | Exclude dev files from package |

[See workflow templates](examples/npm/workflows/)

## package.json Enhancements

[See examples](examples/npm/package-json-templates.md):
- Minimal valid package.json
- TypeScript package configuration
- Scoped package (@org/package)

## GitHub Actions Workflows

[See workflow templates](examples/npm/workflows/):
- `npm-publish.yml` - Automated publish on release trigger
- `npm-publish-manual.yml` - Manual publish with version selection
- `npm-publish-tag.yml` - Publish from git tag

## npm Configuration

[See templates](examples/npm/npm-config.md):
- `.npmrc` - Registry and scope configuration
- `.npmignore` - Exclude patterns for dev files

## Version Bump Helper

### Using npm

```bash
npm version patch   # 1.0.0 → 1.0.1
npm version minor   # 1.0.0 → 1.1.0
npm version major   # 1.0.0 → 2.0.0
```

### Prerelease Tags

| Tag | Example | Use Case |
|-----|---------|----------|
| `alpha` | `1.0.0-alpha.1` | Early testing |
| `beta` | `1.0.0-beta.1` | Feature complete, testing |
| `rc` | `1.0.0-rc.1` | Release candidate |
| `next` | `1.0.0-next.1` | Next major version preview |

[See full version bump guide](examples/npm/version-bumping.md)

## npm Token Setup

### Required Secrets

| Secret | Purpose |
|--------|---------|
| `NPM_TOKEN` | npm automation token for publish |

### Creating npm Token

1. Log in to https://www.npmjs.com/
2. Profile → Access Tokens → Generate New Token
3. Select "Automation" type
4. Copy token (shown once)

### Adding to GitHub

1. Repository → Settings → Secrets → New repository secret
2. Name: `NPM_TOKEN`
3. Value: [paste token]

### For Scoped Packages

If publishing `@org/package`, ensure:
- npm token has access to org
- package.json has `"name": "@org/package"`
- Workflow uses correct scope

[See scoped package setup](examples/npm/scoped-packages.md)

## Output Format

```
npm Package Publishing Setup
════════════════════════════

[1/3] Validating package.json...
      ✓ Name: my-package
      ✓ Version: 1.0.0
      ✓ License: MIT

[2/3] Package type: Public package
      ✓ Standard npm publish

[3/3] Generating workflows...
      → .github/workflows/npm-publish.yml
      → .npmrc
      → .npmignore

Next Steps:
1. Create NPM_TOKEN on npmjs.com
2. Add NPM_TOKEN to GitHub Secrets
3. Create release to trigger publish

Would you like to commit these files?
```

## Verification Checklist

| Check | Command |
|-------|---------|
| package.json valid | `npm pack --dry-run` |
| Build succeeds | `npm run build` |
| Tests pass | `npm test` |
| Types check | `npm run type-check` (if TypeScript) |
| Package size | `npm pack` (check .tgz size) |

## Integration

**Command:** `/popkit:deploy setup npm`
**Agent:** `devops-automator`
**Followed by:**
- `/popkit:deploy validate` - Pre-publish checks
- `/popkit:deploy execute npm` - Publish to registry

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `pop-deploy-init` | Run first to configure targets |
| `pop-deploy-pypi` | Python package equivalent |
| `pop-deploy-github-releases` | For binary releases |
