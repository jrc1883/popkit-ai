#!/bin/bash
# =============================================================================
# Setup Branch Protection for PopKit
# =============================================================================
#
# This script configures branch protection rules for the main/master branch.
# Requires: GitHub Pro subscription and gh CLI authenticated.
#
# Usage: bash .github/scripts/setup-branch-protection.sh
#
# =============================================================================

set -e

REPO="jrc1883/popkit"
BRANCH="master"  # Change to "main" if that's your default branch

echo "=== Setting up branch protection for $REPO/$BRANCH ==="

# Check if gh is authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Please run 'gh auth login' first"
    exit 1
fi

# Create branch protection rule via GitHub API
# Note: This requires GitHub Pro for private repositories
echo "Creating branch protection rule..."

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  repos/$REPO/branches/$BRANCH/protection \
  -f "required_status_checks[strict]=true" \
  -f "required_status_checks[contexts][]=CI" \
  -f "enforce_admins=false" \
  -f "required_pull_request_reviews[dismiss_stale_reviews]=true" \
  -f "required_pull_request_reviews[require_code_owner_reviews]=true" \
  -f "required_pull_request_reviews[required_approving_review_count]=1" \
  -f "restrictions=null" \
  -f "required_linear_history=false" \
  -f "allow_force_pushes=false" \
  -f "allow_deletions=false"

echo ""
echo "=== Branch protection configured! ==="
echo ""
echo "Settings applied:"
echo "  ✓ Require pull request reviews (1 approval)"
echo "  ✓ Require review from code owners"
echo "  ✓ Dismiss stale reviews on new commits"
echo "  ✓ Require status checks to pass"
echo "  ✓ Require branches to be up to date"
echo "  ✗ Force pushes disabled"
echo "  ✗ Branch deletion disabled"
echo ""
echo "Note: Make sure you have a CI workflow that creates a 'CI' status check."
echo "      Otherwise, no PRs will be able to merge until CI is set up."
