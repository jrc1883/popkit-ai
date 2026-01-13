# Branch Protection Setup Guide

This guide explains how to set up branch protection for PopKit.

## Prerequisites

1. **GitHub Pro subscription** ($4/month) - Required for branch protection on private repos
2. **CODEOWNERS file** - Already created at `.github/CODEOWNERS`

## Option 1: Manual Setup (Recommended)

### Step 1: Go to Repository Settings

1. Navigate to https://github.com/jrc1883/popkit
2. Click **Settings** tab
3. Click **Branches** in the left sidebar

### Step 2: Add Branch Protection Rule

1. Click **Add branch protection rule**
2. Enter branch name pattern: `master` (or `main`)

### Step 3: Configure Protection Settings

Enable the following options:

#### Pull Request Reviews

- [x] **Require a pull request before merging**
  - [x] Require approvals: **1**
  - [x] Dismiss stale pull request approvals when new commits are pushed
  - [x] Require review from Code Owners
  - [ ] Require approval of the most recent reviewable push

#### Status Checks

- [x] **Require status checks to pass before merging**
  - [x] Require branches to be up to date before merging
  - Add required status checks:
    - `CI` (once you create the GitHub Actions workflow)
    - `typecheck` (optional)
    - `lint` (optional)

#### Other Settings

- [ ] Require signed commits (optional - more secure but adds friction)
- [ ] Require linear history (optional - enforces rebase workflow)
- [x] **Do not allow bypassing the above settings** (recommended)
- [ ] Restrict who can push to matching branches (optional)
- [x] **Allow force pushes** - DISABLED
- [x] **Allow deletions** - DISABLED

### Step 4: Save Changes

Click **Create** or **Save changes**

## Option 2: Script Setup

If you prefer using the command line:

```bash
bash .github/scripts/setup-branch-protection.sh
```

Note: This requires GitHub Pro and authenticated `gh` CLI.

## Option 3: GitHub CLI Commands

```bash
# View current protection rules
gh api repos/jrc1883/popkit/branches/master/protection

# Update protection (requires proper JSON body)
gh api \
  --method PUT \
  repos/jrc1883/popkit/branches/master/protection \
  --input protection-config.json
```

## Verifying Setup

After configuration, verify that:

1. **CODEOWNERS works**: Create a test PR modifying `packages/plugin/` - you should be auto-requested for review
2. **Reviews required**: PRs cannot be merged without approval
3. **Status checks**: Once CI is set up, PRs cannot be merged without passing checks

## Troubleshooting

### "Branch protection rule not available"

- Ensure you have GitHub Pro subscription
- Private repos require Pro/Team/Enterprise for branch protection

### "CODEOWNERS not working"

- Verify file is at `.github/CODEOWNERS` (or root, or `docs/`)
- Check file syntax (no trailing spaces, proper format)
- Ensure usernames exist on GitHub

### "Status checks not appearing"

- Run the CI workflow at least once to create the status check
- Status checks are only available after first workflow run

## Related Files

- `.github/CODEOWNERS` - Code ownership definitions
- `.github/scripts/setup-branch-protection.sh` - Automation script
- `.github/workflows/ci.yml` - CI workflow (to be created)
