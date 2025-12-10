#!/bin/bash
# =============================================================================
# Setup Labels for PopKit Repository
# =============================================================================
#
# Creates all the labels needed for issue/PR automation.
# Run this once to set up the label taxonomy.
#
# Usage: bash .github/scripts/setup-labels.sh
#
# =============================================================================

set -e

REPO="jrc1883/popkit"

echo "=== Setting up labels for $REPO ==="
echo ""

# Function to create or update a label
create_label() {
    local name="$1"
    local color="$2"
    local description="$3"

    echo "Creating label: $name"

    # Try to create, if it exists, update it
    gh label create "$name" --color "$color" --description "$description" --repo "$REPO" 2>/dev/null || \
    gh label edit "$name" --color "$color" --description "$description" --repo "$REPO" 2>/dev/null || \
    echo "  (label may already exist with same settings)"
}

echo "=== Type Labels ==="
create_label "bug" "d73a4a" "Something isn't working"
create_label "enhancement" "a2eeef" "New feature or request"
create_label "documentation" "0075ca" "Improvements or additions to documentation"
create_label "question" "d876e3" "Further information is requested"
create_label "chore" "fef2c0" "Maintenance tasks"

echo ""
echo "=== Area Labels ==="
create_label "plugin" "1d76db" "Plugin code (commands, skills, agents)"
create_label "cloud" "5319e7" "Cloud API code"
create_label "hooks" "c5def5" "Python hooks and utilities"
create_label "agents" "fbca04" "Agent definitions and routing"
create_label "skills" "bfd4f2" "Skill definitions"
create_label "commands" "d4c5f9" "Slash command definitions"
create_label "power-mode" "f9d0c4" "Multi-agent orchestration"
create_label "landing" "e99695" "Landing page and marketing"

echo ""
echo "=== Status Labels ==="
create_label "stale" "ffffff" "No activity for 30+ days"
create_label "blocked" "b60205" "Blocked by external dependency"
create_label "in-progress" "0e8a16" "Currently being worked on"
create_label "needs-triage" "e4e669" "Needs priority assignment"
create_label "keep-open" "006b75" "Exempt from stale bot"
create_label "help-wanted" "008672" "Extra attention is needed"
create_label "good-first-issue" "7057ff" "Good for newcomers"

echo ""
echo "=== Size Labels (for PRs) ==="
create_label "size/S" "009900" "Small PR (<50 lines)"
create_label "size/M" "00ff00" "Medium PR (50-200 lines)"
create_label "size/L" "ffff00" "Large PR (200-500 lines)"
create_label "size/XL" "ff9900" "Extra large PR (500+ lines)"

echo ""
echo "=== Special Labels ==="
create_label "security" "ee0701" "Security-related issue"
create_label "performance" "ff7619" "Performance optimization"
create_label "breaking-change" "b60205" "Introduces breaking changes"
create_label "ci" "ededed" "CI/CD related"
create_label "config" "d4c5f9" "Configuration changes"
create_label "tests" "bfdadc" "Test-related changes"

echo ""
echo "=== Done! ==="
echo ""
echo "Labels created/updated for $REPO"
echo "Run 'gh label list --repo $REPO' to see all labels"
