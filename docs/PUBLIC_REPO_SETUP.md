# Public Repository Setup Guide

**Date:** 2026-01-06
**Repository:** https://github.com/jrc1883/popkit-claude
**Status:** Ready for Public Launch (Beta)

---

## ✅ Completed

### 1. Repository State
- **Latest Commits Pushed:** All fixes from today are live
  - `e432599` - Marketplace publication fixes (v1.0.0-beta.3)
  - `6feac30` - IP scanner fixes (34 false positives → 0)
  - `0e8e7ea` - CI workflow modernization
- **CI/CD:** All checks should pass on next run
- **Plugins:** 5 modular plugins ready for installation

### 2. Billing Protection
- **Added "Coming Soon" Guard:** Billing checkout now returns 503 with message
- **Message:** "PopKit Pro and Team plans are not yet available. Join the waitlist at https://popkit.dev"
- **Easy to Remove:** Just uncomment the code when ready to launch

---

## 📋 Recommended Next Steps

### Priority 1: Repository Security & Quality

#### A. Branch Protection (GitHub Web UI Required)

Navigate to: **Settings → Branches → Add rule** for `main`

**Required Settings:**
```
✅ Require a pull request before merging
   └─ Require approvals: 1
   └─ Dismiss stale PR approvals when new commits are pushed
   └─ Require review from Code Owners (optional, if using CODEOWNERS)

✅ Require status checks to pass before merging
   └─ Require branches to be up to date before merging
   └─ Status checks that are required:
       - Validate Plugins
       - Validate Agents
       - Validate Hooks
       - IP Leak Scanner
       - CI Complete

✅ Require conversation resolution before merging

✅ Require signed commits (optional, recommended)

✅ Do not allow bypassing the above settings
   └─ Include administrators (recommended for safety)

❌ Allow force pushes: Disabled
❌ Allow deletions: Disabled
```

#### B. Repository Settings (GitHub Web UI)

**Settings → General:**
```
✅ Disable: Wiki (not using)
✅ Disable: Projects (using GitHub Projects separately)
✅ Disable: Allow merge commits (prefer squash or rebase)
✅ Enable: Automatically delete head branches
✅ Enable: Allow squash merging
✅ Suggested: Default to squash merging
```

**Settings → Security:**
```
✅ Enable: Dependabot alerts
✅ Enable: Dependabot security updates
✅ Enable: Code scanning (GitHub Advanced Security if available)
✅ Enable: Secret scanning
```

#### C. Issue Templates (Can Automate)

Create `.github/ISSUE_TEMPLATE/`:
- `bug_report.md` - Bug reports
- `feature_request.md` - Feature requests
- `config.yml` - Issue template configuration

#### D. Pull Request Template

Create `.github/PULL_REQUEST_TEMPLATE.md`:
```markdown
## Description
<!-- Brief description of changes -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
<!-- How has this been tested? -->

## Checklist
- [ ] CI passes
- [ ] No IP leaks detected
- [ ] Tests added/updated (if applicable)
- [ ] Documentation updated (if applicable)
```

---

## 🔢 Version Bump Strategy

### Current State
- **Version:** 1.0.0-beta.3
- **Status:** Beta, marketplace published
- **Stability:** CI fixed, IP scanner fixed, plugins validated

### Options

#### Option A: Stay at Beta 3 (Recommended for Now)
**Pros:**
- Already published
- Users can start testing
- Signals "not production ready"
- Can iterate quickly

**Cons:**
- Beta tag may reduce trust

**When to use:** If you expect to find issues and need flexibility

#### Option B: Bump to Beta 4
**Pros:**
- Shows progress since beta.3
- Includes today's fixes (IP scanner, CI, billing guard)
- Clean version for public launch

**Cons:**
- Requires republishing marketplace
- Small incremental change

**When to use:** If you want to mark today's fixes as a release

#### Option C: Bump to 1.0.0 (Full Release)
**Pros:**
- Signals production-ready
- More professional
- Users trust it more

**Cons:**
- Sets expectations for stability
- Harder to make breaking changes
- Need confidence in quality

**When to use:** After 1-2 weeks of beta testing with no critical issues

### Recommendation

**Stay at 1.0.0-beta.3** for now:
1. Let users test for 1-2 weeks
2. Collect feedback via GitHub Issues
3. Fix any critical bugs → beta.4
4. After 2-3 stable weeks → 1.0.0

---

## 🚀 Launch Checklist

### Pre-Launch (Do These First)
- [x] Fix all CI failures
- [x] Fix IP scanner false positives
- [x] Add billing "coming soon" guard
- [ ] Set up branch protection
- [ ] Test plugin installation from marketplace
- [ ] Create issue templates
- [ ] Create PR template
- [ ] Add CONTRIBUTING.md

### Launch Day
- [ ] Announce on social media / blog
- [ ] Monitor GitHub Issues
- [ ] Monitor CI runs
- [ ] Check installation metrics

### Post-Launch (First Week)
- [ ] Respond to issues within 24h
- [ ] Fix any critical bugs immediately (beta.4)
- [ ] Update documentation based on feedback
- [ ] Collect feature requests

### Stable Release Criteria (1.0.0)
- [ ] 2+ weeks with no critical bugs
- [ ] 10+ successful installations
- [ ] Positive user feedback
- [ ] All planned features implemented
- [ ] Documentation complete

---

## 🎯 Immediate Action Items (Next 30 Minutes)

### You Can Do (GitHub Web UI)
1. **Set up branch protection:** Settings → Branches → Add rule
   - Require PR approvals
   - Require status checks
   - Prevent force push/deletion

2. **Configure repository settings:** Settings → General
   - Disable Wiki/Projects
   - Set default merge strategy to squash
   - Enable auto-delete head branches

3. **Enable security features:** Settings → Security
   - Dependabot alerts
   - Secret scanning

### I Can Do (Command Line)
1. **Commit billing guard:** Already done, ready to push
2. **Create issue templates:** Can generate these
3. **Create PR template:** Can generate this
4. **Create CONTRIBUTING.md:** Can generate this

---

## 📝 Notes

- **Branch Protection:** Most effective safety measure - prevents accidental force pushes and ensures CI passes
- **Issue Templates:** Help users file better bug reports
- **Version Strategy:** Beta allows quick iteration, 1.0.0 requires stability
- **Billing Guard:** Protects against premature payments while you test

---

## 🔗 Quick Links

- **Repository:** https://github.com/jrc1883/popkit-claude
- **Marketplace:** Install via `/plugin install popkit-core@popkit-claude`
- **CI Status:** https://github.com/jrc1883/popkit-claude/actions
- **Issues:** https://github.com/jrc1883/popkit-claude/issues
