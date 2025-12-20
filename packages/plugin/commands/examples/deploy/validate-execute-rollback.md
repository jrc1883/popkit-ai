# Deploy Validate, Execute & Rollback Examples

## Validate

### Basic Usage

```bash
/popkit:deploy validate                 # Run all checks
/popkit:deploy validate --target docker # Validate for Docker specifically
/popkit:deploy validate --quick         # Fast checks only
/popkit:deploy validate --fix           # Auto-fix what's possible
```

### Checks Performed

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

### Sample Output

```
/popkit:deploy validate

Validation Report
═════════════════

Pre-flight checks for: docker, vercel

├─ Build:      ✅ Pass (12s)
├─ Tests:      ✅ 47/47 passing (45s)
├─ Lint:       ⚠️ 2 warnings (auto-fixed)
├─ TypeCheck:  ✅ No errors
├─ Security:   ✅ No vulnerabilities
├─ Secrets:    ✅ No exposure detected
├─ Config:     ✅ Valid for docker, vercel
└─ Deps:       ✅ All available

───────────────────────────────
Ready to deploy: Yes

Warnings (2):
  - src/utils.ts:45 - Unused variable 'temp' (auto-fixed)
  - src/api.ts:12 - Missing return type (auto-fixed)

Run /popkit:deploy execute to proceed.
```

---

## Execute

### Basic Usage

```bash
/popkit:deploy execute                  # Deploy to default target
/popkit:deploy execute docker           # Deploy Docker image
/popkit:deploy execute vercel           # Deploy to Vercel
/popkit:deploy execute npm              # Publish to npm
/popkit:deploy execute --all            # Deploy to all targets
/popkit:deploy execute --dry-run        # Show what would happen
```

### Process

1. **Pre-flight** (automatic validate)
2. **Confirm** (unless `--yes`)
3. **Execute** per target
4. **Post-deploy Validation**
5. **Record History**

### Sample Output

```
/popkit:deploy execute docker

Deploying to Docker...

[1/4] Running pre-flight checks...
      ✓ All validation checks passed

[2/4] Building Docker image...
      → Building ghcr.io/owner/repo:1.2.0
      → Stage 1/3: deps (cached)
      → Stage 2/3: builder (47s)
      → Stage 3/3: runner (3s)
      ✓ Build complete (52s)

[3/4] Pushing to registry...
      → Pushing to ghcr.io/owner/repo
      ✓ 1.2.0 pushed
      ✓ latest tag updated

[4/4] Recording deployment...
      ✓ History updated
      ✓ Rollback point saved

Deployment Complete!
═══════════════════

Target: docker
Image: ghcr.io/owner/repo:1.2.0
Duration: 1m 23s
Status: Success

Rollback available: /popkit:deploy rollback docker --to 1.1.0
```

---

## Rollback

### Basic Usage

```bash
/popkit:deploy rollback                 # Rollback last deployment
/popkit:deploy rollback docker          # Rollback Docker specifically
/popkit:deploy rollback --to v1.1.0     # Rollback to specific version
/popkit:deploy rollback --list          # Show rollback history
```

### Process

1. **Load History**
2. **Present Options**
3. **Execute Rollback**
4. **Verify**

### Sample Output

```
/popkit:deploy rollback docker

Rollback Docker Deployment
══════════════════════════

Current version: 1.2.0 (deployed 30m ago)

Available rollback points:
  1. v1.1.0 - Deployed 2 hours ago (success)
  2. v1.0.5 - Deployed 3 days ago (success)
  3. v1.0.4 - Deployed 5 days ago (success)

Which version would you like to rollback to?

[User selects v1.1.0]

Rolling back to v1.1.0...

[1/3] Re-tagging image...
      ✓ ghcr.io/owner/repo:1.1.0 → latest

[2/3] Updating deployment...
      ✓ Kubernetes deployment updated
      ✓ Pods rolling update started

[3/3] Verifying rollback...
      ✓ Health check passed
      ✓ Smoke tests passed

Rollback Complete!
══════════════════

Rolled back: 1.2.0 → 1.1.0
Duration: 45s
Status: Success

Note: v1.2.0 is still available in registry for future deployment.
```
