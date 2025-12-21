---
name: deploy-pypi
description: "Use when publishing packages to PyPI - validates pyproject.toml, generates publish workflows with Trusted Publisher support, handles version bumps, and supports both PyPI and TestPyPI. Includes changelog integration and dry-run support."
---

# PyPI Package Publishing

## Overview

Configure Python package publishing with proper validation, versioning, and secure authentication. Generates GitHub Actions workflows for automated releases using PyPI Trusted Publishers (OIDC).

**Core principle:** Modern Python packaging (pyproject.toml) with Trusted Publisher authentication.

## Critical Rules

| Rule | Details |
|------|---------|
| **ALWAYS use pyproject.toml** | Modern Python packaging standard (PEP 518, 621) |
| **NEVER use passwords** | Use Trusted Publishers (OIDC) for secure auth |
| **Test on TestPyPI first** | Verify package before production release |
| **Include py.typed** | For type-annotated packages |
| **Use src/ layout** | Prevents import issues during development |

## Process

### Step 1: Validate pyproject.toml

Run validation script to check for required/recommended fields.

**Required:** name, version, description, build-system
**Recommended:** authors, readme, license, classifiers, keywords

[See validation script](examples/pypi/validate_pyproject.py)

### Step 2: Ask About Build Backend

```
Use AskUserQuestion tool with:
- question: "Which build backend should we configure?"
- header: "Build Backend"
- options:
  - label: "Hatchling (Recommended)"
    description: "Modern, fast, extensible - used by pip itself"
  - label: "Setuptools"
    description: "Classic, well-documented, wide compatibility"
  - label: "PDM"
    description: "PEP 582 support, lockfiles, monorepo friendly"
  - label: "Poetry"
    description: "Dependency management + publishing"
- multiSelect: false
```

### Step 3: Generate Files

| File | Purpose |
|------|---------|
| `.github/workflows/pypi-publish.yml` | Trusted Publisher workflow (release trigger) |
| `.github/workflows/pypi-publish-manual.yml` | Manual publish with version selection |
| `.github/workflows/test.yml` | Test matrix (Python 3.9-3.12) |
| `docs/PYPI_SETUP.md` | Trusted Publisher setup guide |

[See workflow templates](examples/pypi/workflows/)

## pyproject.toml Templates

[See template examples](examples/pypi/pyproject-templates.md):
- Hatchling configuration with dynamic versioning
- Setuptools configuration with static metadata
- Dynamic version from __version__.py or git tags

## Trusted Publisher Setup

PyPI Trusted Publishers use OIDC for secure, tokenless publishing from GitHub Actions.

### Configuration Steps

| Step | Action |
|------|--------|
| 1. Create PyPI account | https://pypi.org/account/register/ (enable 2FA) |
| 2. Add pending publisher | https://pypi.org/manage/account/publishing/ |
| 3. Create GitHub environments | Repository → Settings → Environments (`pypi`, `testpypi`) |

### Publisher Configuration

| Field | Value |
|-------|-------|
| PyPI project name | `my-package` |
| Owner | GitHub username/org |
| Repository | `repo-name` |
| Workflow | `pypi-publish.yml` |
| Environment | `pypi` (recommended) |

### Why Trusted Publishers?

| Aspect | API Tokens | Trusted Publishers |
|--------|------------|----------------------|
| Rotation | Manual | Automatic |
| Scope | Package or account | Workflow-specific |
| Storage | GitHub Secrets | None needed |
| Security | Token can leak | Cryptographic proof |

## Version Bump Helper

### Using Hatch

```bash
hatch version              # Show current
hatch version patch        # 1.0.0 → 1.0.1
hatch version minor        # 1.0.0 → 1.1.0
hatch version major        # 1.0.0 → 2.0.0
```

### Prerelease Versions

| Format | Meaning |
|--------|---------|
| `1.0.0a1` | Alpha |
| `1.0.0b1` | Beta |
| `1.0.0rc1` | Release candidate |
| `1.0.0` | Final release |

[See full version bump guide](examples/pypi/version-bumping.md)

## Output Format

```
PyPI Package Publishing Setup
═════════════════════════════

[1/4] Validating pyproject.toml...
      ✓ Name: my-package
      ✓ Version: 1.0.0
      ✓ Build system: hatchling

[2/4] Build backend: Hatchling
      ✓ Source layout: src/

[3/4] Generating workflows...
      ✓ Trusted Publisher (OIDC)
      → .github/workflows/pypi-publish.yml
      → .github/workflows/test.yml

[4/4] Setup guide...
      → docs/PYPI_SETUP.md

Next Steps:
1. Configure Trusted Publisher on PyPI
2. Create GitHub environments
3. Add py.typed marker

Would you like to commit these files?
```

## Verification Checklist

| Check | Command |
|-------|---------|
| pyproject.toml valid | `python -m build --dry-run` |
| Build succeeds | `python -m build` |
| Package checks pass | `twine check dist/*` |
| Tests pass | `pytest` |
| Types check | `mypy src` |

## Integration

**Command:** `/popkit:deploy setup pypi`
**Agent:** `devops-automator`
**Followed by:**
- `/popkit:deploy validate` - Pre-publish checks
- `/popkit:deploy execute pypi` - Publish to registry

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `pop-deploy-init` | Run first to configure targets |
| `pop-deploy-npm` | JavaScript package equivalent |
| `pop-deploy-github-releases` | For binary releases |
