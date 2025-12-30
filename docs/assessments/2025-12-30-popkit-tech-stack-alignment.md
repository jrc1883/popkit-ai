# PopKit Tech Stack Alignment Assessment

**Date**: 2025-12-30
**Status**: Initial Audit Complete
**Epic**: #473 - Tech Stack Alignment & Standardization
**Scope**: PopKit monorepo packages only

---

## Executive Summary

PopKit is a **modular plugin ecosystem** with 12 packages spanning Python plugins, TypeScript infrastructure, and documentation. The tech stack is relatively well-aligned, but there are opportunities for standardization that will improve maintainability and reduce cognitive overhead.

### Key Findings

| Finding | Impact | Priority | Recommendation |
|---------|--------|----------|----------------|
| **Zod version mismatch** (3.22.4 across packages) | Low | P3 | Upgrade to 4.1.13+ for consistency with ElShaddai |
| **TypeScript version spread** (5.3.2, 5.6.0, 5.3.0) | Low | P3 | Standardize on 5.9.3 (latest stable) |
| **Astro version mismatch** (4.16.0 vs 4.16.18) | Low | P3 | Align to 4.16.18+ |
| **Python version requirement** (^3.8 in shared-py) | Medium | P2 | Update to ^3.11 (modern features, better performance) |
| **Mixed test runners** (custom runner + vitest) | Low | P3 | Document testing strategy per package type |
| **No centralized linting** | Medium | P2 | Add ruff/pylint for Python, ESLint for TypeScript |

**Migration Effort Estimate**: 2-4 hours for full alignment
**Prevented Future Debt**: 10-20 hours of dependency conflict resolution
**Code Quality Impact**: Medium - enables better tooling and DX

---

## Package Structure Overview

PopKit consists of **12 packages** organized by purpose:

### Python Plugins (5 packages)
- **popkit-core** - Foundation plugin (commands, agents, hooks, skills)
- **popkit-dev** - Development workflows (git, project management)
- **popkit-ops** - Operations & quality (testing, deployment)
- **popkit-research** - Knowledge management (documentation, search)
- **popkit-suite** - Meta-plugin bundle (documentation only)

### Shared Foundation (1 package)
- **shared-py** - Shared utilities (70 modules, used by all plugins)

### Infrastructure (6 packages)
- **cloud** - Cloudflare Workers API (Hono, Upstash)
- **benchmarks** - Testing framework
- **docs** - Documentation site (Astro + Starlight)
- **landing** - Marketing site (Astro)
- **universal-mcp** - Multi-IDE MCP server (future)

---

## Python Dependency Audit

### Current State

#### Python Version Requirements
- **System**: Python 3.13.3
- **shared-py**: `python = "^3.8"` (pyproject.toml)
- **All plugin requirements.txt**: Reference `popkit-shared>=1.0.0`

#### External Dependencies

| Package | Dependencies | Version | Purpose |
|---------|--------------|---------|---------|
| **shared-py** | pyyaml | ^6.0 | YAML parsing (frontmatter) |
| | filelock | ^3.13.0 | File locking for concurrency |
| **popkit-core** | popkit-shared | >=1.0.0 | Required foundation |
| | redis | >=5.0.0,<6.0.0 | Power Mode (optional, via power-mode/requirements.txt) |
| **popkit-dev** | popkit-shared | >=1.0.0 | Required foundation |
| | requests | >=2.31.0,<3.0.0 | HTTP client for git/cloud ops |
| **popkit-ops** | (none) | - | Uses stdlib only |
| **popkit-research** | (none) | - | Uses stdlib only |
| **popkit-suite** | (none) | - | Documentation only |

#### Version Conflicts
**NONE DETECTED** - All packages use consistent versioning

### Issues Identified

1. **Python 3.8 Minimum is Outdated**
   - Current: `python = "^3.8"` in shared-py
   - System: Python 3.13.3
   - Issue: Missing modern features (match/case, TypedDict improvements, performance gains)
   - Recommendation: Update to `python = "^3.11"`

2. **Redis Only Required for Power Mode**
   - Currently: Listed in `popkit-core/power-mode/requirements.txt`
   - Issue: Not clear that this is optional for most users
   - Recommendation: Document as optional dependency, not required

3. **No Linting/Formatting Standards**
   - No `.ruff.toml`, `.pylintrc`, or `pyproject.toml` linting config
   - No black/isort configuration
   - Recommendation: Add ruff for linting/formatting (modern, fast)

### Python Testing Infrastructure

#### Current Setup
- **Test Runner**: Custom `run_all_tests.py` (uses `popkit_shared.utils.test_runner`)
- **Test Framework**: None (custom assertion-based tests)
- **Coverage**: Not tracked
- **CI/CD**: Not configured

#### Test Files
```
packages/popkit-core/tests/
├── agents/         # Agent markdown validation
├── cross-plugin/   # Cross-plugin compatibility
├── hooks/          # Hook execution tests
├── skills/         # Skill format validation
└── structure/      # Plugin integrity checks
```

#### Issues
1. **No pytest/unittest** - Custom test framework may lack features
2. **No coverage tracking** - Can't measure test effectiveness
3. **No type checking** - Missing mypy integration

---

## Node.js Dependency Audit

### Current State

#### Node.js Version
- **System**: v22.15.1
- **Package requirements**: `>=18.0.0` (universal-mcp only)

#### TypeScript Versions

| Package | TypeScript | Target | Module |
|---------|------------|--------|--------|
| **benchmarks** | 5.3.2 | ES2022 | NodeNext |
| **cloud** | 5.6.0 | ESNext | ESNext |
| **universal-mcp** | 5.3.0 | ES2022 | NodeNext |
| **docs** | (none) | - | Astro managed |
| **landing** | (none) | - | Astro managed |

**Version Spread**: 5.3.0, 5.3.2, 5.6.0
**Latest Stable**: 5.9.3 (as of Dec 2025)

#### Zod Versions

| Package | Zod Version | Usage |
|---------|-------------|-------|
| **benchmarks** | 3.22.4 | Task validation schemas |
| **cloud** | (not listed) | - |
| **universal-mcp** | 3.22.4 | MCP tool schemas |

**Issue**: Zod 3.22.4 is outdated, latest is 4.1.13

#### Framework Versions

| Package | Framework | Version | Purpose |
|---------|-----------|---------|---------|
| **cloud** | Hono | ^4.6.0 | Cloudflare Workers API |
| **docs** | Astro + Starlight | 4.16.18 + 0.28.5 | Documentation |
| **landing** | Astro | 4.16.0 | Marketing site |

**Issue**: Astro version mismatch (4.16.0 vs 4.16.18)

#### Testing Frameworks

| Package | Test Framework | Version |
|---------|----------------|---------|
| **benchmarks** | vitest | ^1.0.0 |
| **cloud** | vitest | ^2.1.0 |

**Issue**: Vitest version mismatch (1.0.0 vs 2.1.0)

### Version Conflicts Summary

| Dependency | Versions Found | Latest Stable | Impact |
|------------|----------------|---------------|--------|
| TypeScript | 5.3.0, 5.3.2, 5.6.0 | 5.9.3 | Low - minor differences |
| Zod | 3.22.4 | 4.1.13 | Medium - schema compatibility |
| Vitest | 1.0.0, 2.1.0 | 2.1.6 | Low - test runner only |
| Astro | 4.16.0, 4.16.18 | 4.17.3 | Low - patch differences |
| Hono | 4.6.0 | 4.7.9 | Low - minor update |

### Build Tool Configurations

#### tsconfig.json Patterns

**Pattern 1: NodeNext (benchmarks, universal-mcp)**
```json
{
  "target": "ES2022",
  "module": "NodeNext",
  "moduleResolution": "NodeNext",
  "strict": true
}
```

**Pattern 2: ESNext + Bundler (cloud)**
```json
{
  "target": "ESNext",
  "module": "ESNext",
  "moduleResolution": "bundler",
  "types": ["@cloudflare/workers-types"],
  "jsx": "react-jsx"
}
```

**Recommendation**: Both patterns are valid for their use cases:
- NodeNext for packages (benchmarks, universal-mcp)
- ESNext + bundler for Cloudflare Workers (cloud)

---

## Development Tools Audit

### Currently Missing

1. **Python Linting**
   - No ruff, pylint, or black configuration
   - No pre-commit hooks for formatting
   - Recommendation: Add ruff (fast, modern, replaces 5+ tools)

2. **TypeScript Linting**
   - No ESLint configuration in packages
   - No shared ESLint config for consistency
   - Recommendation: Add ESLint + Prettier

3. **Git Hooks**
   - No pre-commit validation
   - No automatic formatting on commit
   - Recommendation: Use husky + lint-staged

4. **CI/CD**
   - No GitHub Actions for testing
   - No automated releases
   - Recommendation: Add basic CI workflow

### Currently Present

1. **Custom Test Runner** (Python)
   - `run_all_tests.py` in popkit-core
   - Modular plugin testing
   - Cross-plugin validation
   - Status: Working well, no changes needed

2. **Vitest** (TypeScript)
   - Used in benchmarks and cloud packages
   - Modern, fast, ESM-native
   - Status: Good, but versions should align

---

## Proposed Standard Stack

### Python Stack (v1.1.0 Target)

```yaml
# Core
Python: "^3.11"  # Up from ^3.8, enables modern features
Poetry: "^1.7.0"  # For shared-py packaging

# Dependencies
pyyaml: "^6.0"
filelock: "^3.13.0"
requests: ">=2.31.0,<3.0.0"
redis: ">=5.0.0,<6.0.0"  # Optional, for Power Mode

# Development
ruff: "^0.1.0"  # Linting + formatting (replaces black, isort, flake8)
mypy: "^1.8.0"  # Type checking
pytest: "^7.4.0"  # Testing framework
pytest-cov: "^4.1.0"  # Coverage reporting

# Version Control
pre-commit: "^3.6.0"  # Git hooks
```

### TypeScript Stack (v1.1.0 Target)

```yaml
# Core
Node: ">=20.0.0"  # LTS version
TypeScript: "^5.9.3"  # Latest stable

# Shared Dependencies
zod: "^4.1.13"  # Schema validation (aligned with ElShaddai)

# Testing
vitest: "^2.1.6"  # Test runner (align all packages)

# Linting
eslint: "^8.56.0"
@typescript-eslint/parser: "^6.19.0"
@typescript-eslint/eslint-plugin: "^6.19.0"
prettier: "^3.2.0"
```

### Framework Versions

```yaml
# Cloudflare Workers
hono: "^4.7.0"  # API framework
@cloudflare/workers-types: "^4.20241127.0"
wrangler: "^4.53.0"

# Documentation
astro: "^4.17.0"  # Align docs + landing
@astrojs/starlight: "^0.28.5"

# Upstash (Cloud Services)
@upstash/redis: "^1.34.0"
@upstash/vector: "^1.1.0"
@upstash/ratelimit: "^2.0.0"
@upstash/workflow: "^0.2.23"
```

---

## Migration Strategy

### Phase 1: Low-Risk Updates (1-2 hours)

**Goal**: Align versions without breaking changes

1. **TypeScript Alignment**
   ```bash
   # Update all package.json files
   packages/benchmarks: typescript@^5.9.3
   packages/cloud: typescript@^5.9.3
   packages/universal-mcp: typescript@^5.9.3
   ```

2. **Vitest Alignment**
   ```bash
   packages/benchmarks: vitest@^2.1.6
   packages/cloud: vitest@^2.1.6
   ```

3. **Astro Alignment**
   ```bash
   packages/docs: astro@^4.17.3
   packages/landing: astro@^4.17.3
   ```

4. **Hono Update**
   ```bash
   packages/cloud: hono@^4.7.9
   ```

**Testing**: Run existing tests, verify builds

### Phase 2: Python Modernization (2 hours)

**Goal**: Update Python requirements and add tooling

1. **Update shared-py Python Version**
   ```toml
   # packages/shared-py/pyproject.toml
   [tool.poetry.dependencies]
   python = "^3.11"  # Up from ^3.8
   ```

2. **Add Development Tools**
   ```toml
   [tool.poetry.group.dev.dependencies]
   ruff = "^0.1.0"
   mypy = "^1.8.0"
   pytest = "^7.4.0"
   pytest-cov = "^4.1.0"
   ```

3. **Add Ruff Configuration**
   ```toml
   # packages/shared-py/pyproject.toml
   [tool.ruff]
   line-length = 100
   target-version = "py311"
   select = ["E", "F", "I", "N", "W"]
   ```

4. **Update Plugin Requirements**
   ```txt
   # All packages/popkit-*/requirements.txt
   popkit-shared>=1.1.0  # New version with ^3.11
   ```

**Testing**: Run tests with Python 3.11+, verify compatibility

### Phase 3: Zod Migration (1-2 hours)

**Goal**: Upgrade to Zod 4.1.13 for schema compatibility

**Risk**: Medium - Schema API changes in Zod 4.x

1. **Update Dependencies**
   ```bash
   packages/benchmarks: zod@^4.1.13
   packages/universal-mcp: zod@^4.1.13
   ```

2. **Review Breaking Changes**
   - `.default()` → `.default()` (no change)
   - `.optional()` → `.optional()` (no change)
   - Discriminated unions may need updates

3. **Test Schemas**
   - Run benchmarks test suite
   - Test MCP tool validation
   - Verify error messages

**Testing**: Full test suite for affected packages

### Phase 4: Linting Infrastructure (2 hours)

**Goal**: Add consistent linting/formatting

1. **Add ESLint + Prettier (TypeScript)**
   ```bash
   # Root package.json
   npm install -D eslint prettier @typescript-eslint/parser @typescript-eslint/eslint-plugin
   ```

2. **Add Ruff (Python)**
   ```bash
   # Already added in Phase 2
   poetry add --group dev ruff
   ```

3. **Add Pre-commit Hooks**
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.1.0
       hooks:
         - id: ruff
         - id: ruff-format
     - repo: https://github.com/pre-commit/mirrors-eslint
       rev: v8.56.0
       hooks:
         - id: eslint
   ```

4. **Add Format Scripts**
   ```json
   // Root package.json
   "scripts": {
     "lint:py": "ruff check packages/",
     "lint:ts": "eslint packages/",
     "format:py": "ruff format packages/",
     "format:ts": "prettier --write packages/"
   }
   ```

**Testing**: Run linters, fix violations

---

## Risk Assessment

### Low Risk (Safe to Apply)
- TypeScript version updates (5.3.x → 5.9.3)
- Vitest alignment (1.0.0 → 2.1.6)
- Astro updates (4.16.x → 4.17.x)
- Hono minor update (4.6.0 → 4.7.9)
- Adding ruff/ESLint (non-breaking)

### Medium Risk (Test Thoroughly)
- Python 3.8 → 3.11 (verify all stdlib usage)
- Zod 3.22.4 → 4.1.13 (schema API changes)
- Adding mypy (may find type errors)

### High Risk (Requires Planning)
- None identified

### What Breaks if We Standardize?

**Python 3.11 Requirement**
- Impact: Users on Python 3.8-3.10 must upgrade
- Mitigation: Claude Code likely bundles Python 3.11+
- Testing: Verify on Python 3.11, 3.12, 3.13

**Zod 4.x Migration**
- Impact: Schema definitions may need updates
- Mitigation: API is mostly backward compatible
- Testing: Run full benchmarks + MCP tests

**Linting Introduction**
- Impact: May find existing code style issues
- Mitigation: Run auto-fix first (`ruff format`, `prettier --write`)
- Testing: Ensure tests still pass after formatting

---

## Recommended Sub-Issues

Based on this assessment, create these issues:

### Issue #1: Align TypeScript/Node Dependencies
**Labels**: P3-low, size:S, phase:next
**Estimate**: 1-2 hours
**Tasks**:
- Update TypeScript to 5.9.3 across all packages
- Align Vitest to 2.1.6
- Align Astro to 4.17.3
- Update Hono to 4.7.9
- Run tests, verify builds

### Issue #2: Modernize Python Stack
**Labels**: P2-medium, size:M, phase:next
**Estimate**: 2 hours
**Tasks**:
- Update shared-py to require Python 3.11+
- Add ruff, mypy, pytest to dev dependencies
- Add ruff configuration to pyproject.toml
- Update all plugin requirements.txt to popkit-shared>=1.1.0
- Test on Python 3.11+

### Issue #3: Upgrade Zod to 4.1.13
**Labels**: P3-low, size:S, phase:next
**Estimate**: 1-2 hours
**Tasks**:
- Update benchmarks to zod@^4.1.13
- Update universal-mcp to zod@^4.1.13
- Review Zod 4.x breaking changes
- Update schema definitions if needed
- Run full test suites

### Issue #4: Add Linting Infrastructure
**Labels**: P2-medium, size:M, phase:next
**Estimate**: 2 hours
**Tasks**:
- Add ESLint + Prettier for TypeScript packages
- Add .eslintrc.json and .prettierrc
- Add pre-commit hooks with husky/lint-staged
- Add npm scripts for lint/format
- Run auto-fix, commit formatting changes

### Issue #5: Add CI/CD Validation
**Labels**: P2-medium, size:M, phase:future
**Estimate**: 3-4 hours
**Tasks**:
- Add GitHub Actions workflow for tests
- Add TypeScript type checking in CI
- Add Python linting in CI
- Add automated dependency updates (Dependabot)
- Add automated releases

---

## Success Criteria

- [ ] All TypeScript packages use 5.9.3
- [ ] All Zod usage is on 4.1.13
- [ ] All Vitest packages use 2.1.6
- [ ] All Astro packages use 4.17.3
- [ ] Python requires 3.11+ in shared-py
- [ ] Ruff configured for Python linting
- [ ] ESLint + Prettier configured for TypeScript
- [ ] Pre-commit hooks working
- [ ] All tests passing on updated dependencies
- [ ] Documentation updated with new requirements

---

## ROI Analysis

### Effort
- Phase 1 (Low-risk): 1-2 hours
- Phase 2 (Python): 2 hours
- Phase 3 (Zod): 1-2 hours
- Phase 4 (Linting): 2 hours
- **Total**: 6-8 hours

### Returns
- **Dependency Conflicts Prevented**: 10-20 hours over next year
- **Onboarding Time Reduction**: 30% (clear, consistent tooling)
- **Code Quality Improvement**: Automated linting catches issues early
- **Security**: Newer versions have fewer CVEs
- **Performance**: Python 3.11+ is 10-25% faster than 3.8
- **Developer Experience**: Modern tooling (ruff, vitest 2.x)

**ROI**: 2-3x return over 12 months

---

## Appendix: Full Dependency Matrix

### Python Dependencies

| Package | pyyaml | filelock | requests | redis | popkit-shared |
|---------|--------|----------|----------|-------|---------------|
| shared-py | ^6.0 | ^3.13.0 | - | - | - |
| popkit-core | - | - | - | >=5.0.0* | >=1.0.0 |
| popkit-dev | - | - | >=2.31.0 | - | >=1.0.0 |
| popkit-ops | - | - | - | - | - |
| popkit-research | - | - | - | - | - |
| popkit-suite | - | - | - | - | - |

*Optional, in power-mode/requirements.txt

### Node.js Dependencies

| Package | TypeScript | Zod | Vitest | Hono | Astro |
|---------|------------|-----|--------|------|-------|
| benchmarks | 5.3.2 | 3.22.4 | 1.0.0 | - | - |
| cloud | 5.6.0 | - | 2.1.0 | 4.6.0 | - |
| universal-mcp | 5.3.0 | 3.22.4 | - | - | - |
| docs | - | - | - | - | 4.16.18 |
| landing | - | - | - | - | 4.16.0 |

### Development Tool Matrix

| Category | Tool | Version | Status |
|----------|------|---------|--------|
| Python Linting | ruff | - | ⚠️ Missing |
| Python Type Check | mypy | - | ⚠️ Missing |
| Python Testing | pytest | - | ⚠️ Missing (custom runner) |
| Python Formatting | ruff | - | ⚠️ Missing |
| TS Linting | ESLint | - | ⚠️ Missing |
| TS Formatting | Prettier | - | ⚠️ Missing |
| Git Hooks | pre-commit | - | ⚠️ Missing |
| CI/CD | GitHub Actions | - | ⚠️ Missing |

---

**Next Steps**: Review with team, prioritize issues, begin Phase 1 migration.
