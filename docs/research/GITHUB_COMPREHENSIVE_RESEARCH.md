# GitHub Comprehensive Research - December 2025

Part of Epic #128 (GitHub Workflow Refinement)

## Executive Summary

This research covers GitHub's full feature set to inform PopKit's GitHub integration strategy. Key finding: **GitHub Pro at $4/month is absolutely worth it** for private repository branch protection and code review features.

---

## 1. GitHub Plans Comparison

### Pricing Tiers (2025)

| Plan | Price | Key Features |
|------|-------|--------------|
| **Free** | $0 | Public repos unlimited, private repos limited, basic features |
| **Pro** | $4/month | Protected branches for private repos, code owners, required reviews |
| **Team** | $4/user/month | Team management, org-level features |
| **Enterprise** | $21/user/month | Advanced security, compliance, SSO |

### GitHub Pro Benefits Over Free

1. **Protected Branches in Private Repos** - The #1 reason to upgrade
   - Require pull request reviews before merging
   - Require status checks to pass
   - Require linear history
   - Restrict who can push to matching branches

2. **Code Owners** - Automatic review assignment
   - CODEOWNERS file in `.github/`, root, or `docs/`
   - Auto-assign reviewers based on file paths
   - Require approval from code owners before merge

3. **Required Reviews**
   - Require specific number of approvals
   - Dismiss stale reviews on new commits
   - Require review from most recent pusher

4. **Draft Pull Requests** - Work in progress indicator

5. **Repository Insights** - Traffic and contributor graphs

### Recommendation

**Upgrade to GitHub Pro ($4/month)** for PopKit development. The branch protection and code owners features are essential for maintaining code quality in private repositories.

---

## 2. Issue & Project Management

### GitHub Projects (New System)

GitHub Projects v2 replaces classic project boards with powerful features:

**Views:**
- **Table** - Spreadsheet-like view with custom fields
- **Board** - Kanban-style columns
- **Roadmap** - Timeline/Gantt view for planning

**Custom Fields:**
- Status (single select)
- Priority (single select)
- Iteration (time-boxed sprints)
- Date fields
- Number fields
- Text fields

**Automation:**
- Built-in workflows (auto-move items)
- GitHub Actions integration
- GraphQL API access

### Milestones Best Practices

1. **Associate with releases** - v1.0.0, v1.1.0, etc.
2. **Set due dates** - Creates accountability
3. **Track progress** - Visual burndown
4. **Prioritize within** - Drag to reorder issues

### Labels Taxonomy

Recommended label structure:
```
Priority:     P0-critical, P1-high, P2-medium, P3-low
Type:         bug, feature, enhancement, docs, chore
Phase:        phase:now, phase:next, phase:future
Status:       blocked, needs-review, help-wanted
Area:         frontend, backend, cloud, plugin
```

### Sub-Issues (Hierarchies)

GitHub now supports sub-issues:
- Break large issues into smaller tasks
- Track progress on parent issue
- Parallel team work

---

## 3. CI/CD & GitHub Actions

### Best Practices

**1. Workflow Structure**
```yaml
name: CI
on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - uses: actions/cache@v4  # Cache dependencies
```

**2. Performance Optimization**
- Cache dependencies (save 60-80% build time)
- Parallel jobs with `strategy.matrix`
- Conditional execution with `if:`

**3. Security**
- NEVER hardcode secrets
- Use `secrets.GITHUB_TOKEN` for repo access
- Self-hosted runners for private needs
- Pin action versions (e.g., `@v4`)

**4. Marketplace Actions**
- Use certified/verified actions
- Check for security advisories
- Keep actions updated

### Recommended Workflows for PopKit

```yaml
# 1. CI Pipeline
- Lint + Type Check
- Unit Tests
- Build Verification

# 2. Release Pipeline
- Version Bump
- Changelog Generation
- GitHub Release Creation
- Public Repo Sync

# 3. Issue Automation
- Auto-label based on content
- Stale issue management
- PR-Issue linking
```

---

## 4. GitHub Pages

### Features

- **Free hosting** for static sites
- **Custom domains** with automatic SSL
- **Jekyll integration** built-in
- **GitHub Actions** for custom builds

### Limitations

- Static content only (no server-side code)
- 1 GB storage per repository
- 100 GB/month bandwidth
- 10 builds per hour

### Use Cases for PopKit

1. **Documentation site** - popkit.dev
2. **Landing page** - Already built with Astro
3. **Demo/showcase** - Interactive examples

---

## 5. GitHub Advanced Security (GHAS)

### New 2025 Structure

Starting April 2025, GHAS split into two products:

**GitHub Secret Protection** ($19/user/month)
- Secret scanning
- Push protection
- AI-powered credential detection
- Custom patterns

**GitHub Code Security** ($30/user/month)
- CodeQL code scanning
- Copilot Autofix
- Dependency review
- Security campaigns

### Free Features (All Repos)

- **Public repos** get all scanning features free
- **Dependabot alerts** - Vulnerability notifications
- **Dependabot security updates** - Auto-PR for fixes
- **Secret scanning (basic)** - Detect known patterns

### Recommendation

For PopKit, the **free security features are sufficient** for now. Consider Secret Protection ($19/mo) when handling customer API keys at scale.

---

## 6. GitHub CLI (gh)

### Key Commands for Automation

```bash
# Issue Management
gh issue list --state open --label bug
gh issue create --title "..." --body "..." --label enhancement
gh issue close 42 --comment "Fixed in PR #43"

# Pull Requests
gh pr create --title "..." --body "..." --base main
gh pr merge 43 --auto --squash
gh pr review 43 --approve

# Actions/Workflows
gh run list --workflow ci.yml
gh run watch 12345678
gh run rerun 12345678 --failed
gh workflow run release.yml

# Releases
gh release create v1.0.0 --generate-notes
gh release download v1.0.0 --pattern "*.zip"

# API Access
gh api repos/{owner}/{repo}/issues
gh api graphql -f query='...'
```

### Custom Aliases

```bash
# Add alias
gh alias set prc 'pr create --fill'
gh alias set issues 'issue list --assignee @me'

# Use alias
gh prc  # Creates PR with auto-filled title/body
gh issues  # Lists your assigned issues
```

### JSON Output for Scripting

```bash
# Get issue data as JSON
gh issue list --json number,title,state | jq '.[] | select(.state == "OPEN")'

# Use in scripts
ISSUE_COUNT=$(gh issue list --state open --json number | jq length)
```

---

## 7. GitHub API

### REST vs GraphQL

| Aspect | REST | GraphQL |
|--------|------|---------|
| Requests | Multiple for related data | Single query |
| Response | Fixed structure | Custom structure |
| Learning | Easier | Steeper |
| Best for | Simple operations | Complex queries |

### GraphQL Example

```graphql
query {
  repository(owner: "jrc1883", name: "popkit") {
    issues(first: 10, states: OPEN) {
      nodes {
        number
        title
        labels(first: 5) {
          nodes { name }
        }
      }
    }
  }
}
```

### Webhooks

Real-time notifications for:
- Push events
- Pull request events
- Issue events
- Release events
- etc.

Delivery: Immediate (within seconds), no retries on failure.

---

## 8. GitHub Discussions

### Features

- **Categories** - Q&A, Ideas, Show and Tell, etc.
- **Pinned discussions** - Announcements
- **Labels** - Organization
- **Analytics** - Community health

### Use Cases for PopKit

1. **User Q&A** - Support questions
2. **Feature requests** - Ideas collection
3. **Announcements** - Release notes
4. **Community showcase** - User projects

---

## 9. GitHub Codespaces

### Features

- **Instant dev environments** in the cloud
- **Configurable** via devcontainer.json
- **VS Code integration** (browser or local)
- **Scalable** (2-32 cores)

### Pricing

- Free tier: 120 core-hours/month (personal accounts)
- Paid: ~$0.18-$0.36/hour depending on machine size

### Use Case for PopKit

Enable contributors to start coding immediately without local setup. Particularly valuable for:
- New contributors
- Complex dependencies
- Cross-platform testing

---

## 10. GitHub Packages

### Supported Registries

- npm (Node.js)
- Container registry (Docker/OCI)
- RubyGems
- Maven/Gradle
- NuGet

### Features

- **Integrated** with GitHub permissions
- **Free** for public packages
- **Private packages** included with Pro/Team

### Use Case for PopKit

Consider publishing:
- PopKit CLI as npm package
- Docker images for MCP server
- Pre-built templates

---

## 11. Branch Protection & Code Review

### Protected Branch Settings

1. **Require pull request reviews**
   - Number of approvals required
   - Dismiss stale reviews on new commits
   - Require review from code owners

2. **Require status checks**
   - CI must pass before merge
   - Require branches to be up to date

3. **Require signed commits** (optional)

4. **Require linear history** (optional)
   - Forces rebase workflow

5. **Include administrators** (optional)
   - Rules apply to admins too

### CODEOWNERS File

```
# .github/CODEOWNERS

# Global owners
* @jrc1883

# Plugin code
packages/plugin/ @jrc1883

# Cloud API
packages/cloud/ @jrc1883

# Documentation
*.md @jrc1883
```

### Rulesets (New)

More flexible than classic branch protection:
- Bypass lists for specific users
- More granular controls
- Organization-wide application

---

## 12. Implementation Recommendations for PopKit

### Immediate Actions (After Pro Upgrade)

1. **Enable branch protection on main/master**
   - Require PR reviews (1 approval minimum)
   - Require status checks (CI passing)
   - Require up-to-date branches

2. **Create CODEOWNERS file**
   - Route reviews to appropriate owners
   - Auto-request reviews on relevant files

3. **Set up GitHub Actions workflows**
   - CI: lint, typecheck, test
   - Release: version bump, changelog, publish
   - Issue: auto-label, stale management

4. **Configure GitHub Pages**
   - Deploy landing page
   - Set up custom domain

### Future Enhancements

1. **GitHub Projects integration**
   - `/popkit:project` command for board management
   - Sprint planning views

2. **Webhook automations**
   - Real-time notifications to Discord/Slack
   - Issue-to-task sync

3. **GitHub Discussions**
   - Enable for community support
   - Integrate with /popkit:knowledge

---

## Sources

- [GitHub Pricing](https://github.com/pricing)
- [GitHub Docs - FAQ about plan changes](https://docs.github.com/en/get-started/learning-about-github/faq-about-changes-to-githubs-plans)
- [GitHub Docs - Best practices for Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects)
- [GitHub Docs - About milestones](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones)
- [GitHub Actions CI CD Best Practices 2025](https://thedevopstooling.com/github-actions-ci-cd-guide/)
- [GitHub Blog - Build CI/CD pipeline with GitHub Actions](https://github.blog/enterprise-software/ci-cd/build-ci-cd-pipeline-github-actions-four-steps/)
- [GitHub Docs - What is GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [GitHub Docs - About GitHub Advanced Security](https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security)
- [GitHub Docs - About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Docs - About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [GitHub Docs - About the GraphQL API](https://docs.github.com/en/graphql/overview/about-the-graphql-api)
- [GitHub Webhooks Guide 2025](https://inventivehq.com/blog/github-webhooks-guide)
- [GitHub Features - Discussions](https://github.com/features/discussions)
- [GitHub Docs - What are GitHub Codespaces](https://docs.github.com/codespaces/overview)
- [GitHub Docs - Introduction to GitHub Packages](https://docs.github.com/en/packages/learn-github-packages/introduction-to-github-packages)
