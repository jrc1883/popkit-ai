---
name: deploy-github-releases
description: "Configure GitHub Releases for CLI tools - cross-platform builds, checksums, changelog. Supports Go, Rust, Node.js, Python. Use for binary artifact releases."
---

# GitHub Releases Deployment

Configure GitHub Releases for CLI tools and binaries. Cross-platform builds, checksums, automated changelogs.

**Core principle:** Every release is reproducible and verifiable.

**Trigger:** `/popkit:deploy setup github-releases`

## Critical Rules

1. **ALWAYS include checksums** - SHA256 for all artifacts
2. **Build all major platforms** - linux, macos, windows × amd64, arm64
3. **Use conventional commits** - For changelog generation
4. **Sign releases** - GPG or Sigstore
5. **Include source tarball** - Reproducibility

## Process

### Step 1: Detect Type

```python
def detect_release_type():
    if Path("go.mod").exists(): return "go"
    if Path("Cargo.toml").exists(): return "rust"
    if Path("pyproject.toml").exists() and has_scripts(): return "python-cli"
    if Path("package.json").exists() and has_bin(): return "node-cli"
    return "generic"
```

### Step 2-3: Configure (via AskUserQuestion)

**Release Type:** CLI Binary | Library/Package | Pre-built Assets
**Platforms:** All (recommended) | Linux+macOS | Linux only

## Workflows by Stack

See `examples/workflows/` for complete implementations:

| Stack | Tool | File |
|-------|------|------|
| **Go** | GoReleaser | `go-release.yml`, `.goreleaser.yaml` |
| **Rust** | cargo-dist | `rust-release.yml` |
| **Node.js** | pkg | `node-release.yml` |
| **Python** | PyInstaller | `python-release.yml` |
| **Generic** | Custom | `generic-release.yml` |

### Workflow Structure (All Stacks)

```yaml
name: Release
on:
  push:
    tags: ['v*']
permissions:
  contents: write

jobs:
  build:      # Multi-platform matrix
  release:    # Create GitHub Release with changelog
```

### Changelog (git-cliff)

```toml
# cliff.toml
[git]
conventional_commits = true
commit_parsers = [
  { message = "^feat", group = "Features" },
  { message = "^fix", group = "Bug Fixes" },
  { message = "^perf", group = "Performance" }
]
```

See `examples/cliff.toml` for full config.

## Output

```
GitHub Releases Setup
═════════════════════
[1/4] Detecting type... ✓ Go CLI
[2/4] Release config... ✓ CLI Binary, 6 platforms, SHA256
[3/4] Generating workflows... 
      → .goreleaser.yaml
      → .github/workflows/release.yml
[4/4] Changelog config... → cliff.toml

Files Created:
├── .goreleaser.yaml
├── .github/workflows/release.yml
└── cliff.toml

Release Process:
  git tag v1.0.0 && git push --tags
  → GitHub Actions builds + creates release

Artifacts (per release):
  - Binary archives (6 platforms)
  - checksums.txt (SHA256)
  - Source tarball
```

## Integration

**Command:** `/popkit:deploy setup github-releases`
**Agent:** devops-automator
**Related:** `/popkit:git release`, `/popkit:git release changelog`

## Verification

| Check | Command |
|-------|---------|
| Workflow syntax | `gh workflow view release.yml` |
| GoReleaser | `goreleaser check` |
| Test build | `goreleaser build --snapshot --clean` |
| Dry-run | `goreleaser release --snapshot --clean` |

## Related

| Skill | Relationship |
|-------|--------------|
| `pop-deploy-init` | Run first |
| `pop-deploy-npm` | For npm packages |
| `pop-deploy-pypi` | For PyPI packages |

## Examples

See `examples/workflows/` for:
- `go-release.yml` - GoReleaser workflow
- `rust-release.yml` - Rust cargo-dist workflow
- `node-release.yml` - Node.js pkg workflow
- `python-release.yml` - Python PyInstaller workflow
- `generic-release.yml` - Custom build workflow
- `.goreleaser.yaml` - Full GoReleaser config
- `cliff.toml` - git-cliff changelog config
