#!/usr/bin/env bash

# PopKit Issue Migration Script
# Migrates issues from jrc1883/elshaddai to jrc1883/popkit-claude
#
# Usage:
#   ./scripts/migrate-issues.sh --dry-run          # Preview only
#   ./scripts/migrate-issues.sh --phase 1          # Migrate Phase 1 (critical)
#   ./scripts/migrate-issues.sh --issue 691        # Migrate specific issue
#   ./scripts/migrate-issues.sh --all              # Migrate all recommended
#   ./scripts/migrate-issues.sh --help             # Show help

set -euo pipefail

# Configuration
SOURCE_REPO="jrc1883/elshaddai"
TARGET_REPO="jrc1883/popkit-claude"
DRY_RUN=false
PHASE=""
SPECIFIC_ISSUE=""
MIGRATE_ALL=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --phase)
            PHASE="$2"
            shift 2
            ;;
        --issue)
            SPECIFIC_ISSUE="$2"
            shift 2
            ;;
        --all)
            MIGRATE_ALL=true
            shift
            ;;
        --help)
            cat <<EOF
PopKit Issue Migration Script

Migrates issues from elshaddai (private) to popkit-claude (public)

Usage:
  $0 [OPTIONS]

Options:
  --dry-run           Preview migrations without creating issues
  --phase N           Migrate issues from Phase N (1-4)
  --issue NUM         Migrate specific issue number
  --all               Migrate all recommended issues
  --help              Show this help message

Phases:
  Phase 1: Critical issues (P0/P1-high, release blockers)
  Phase 2: Features & enhancements
  Phase 3: Documentation & low priority
  Phase 4: Review & cleanup

Examples:
  $0 --dry-run --phase 1
  $0 --issue 691
  $0 --all

EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check for gh CLI
if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI (gh) is not installed. Please install it first."
    exit 1
fi

# Verify authentication
if ! gh auth status &> /dev/null; then
    log_error "Not authenticated with GitHub. Run 'gh auth login' first."
    exit 1
fi

# Phase 1 issues (critical)
PHASE1_ISSUES=(
    691 690 689 688 676 675 674 673 679 677
    580 589 588 587 586 585 584 583
    519 522 520 518
    650 613
)

# Phase 2 issues (features & enhancements)
PHASE2_ISSUES=(
    666 511 512 513 514 515 516 517
    483 484 485 486 487 499 496
    498 488 629 628
    625 626 627 671 672
    603 687
)

# Phase 3 issues (documentation & low priority)
PHASE3_ISSUES=(
    685 618 617 602 579 569 540 523
    527 526
    220 215 216 217 218 219 221
    471 472 500 501
    201 202 203 204 205 206 207 208 209 210
    211 212 213 214 222 223 224 225 226 227
)

# Function to get issue data from source repo
get_issue_data() {
    local issue_number=$1

    log_info "Fetching issue #$issue_number from $SOURCE_REPO..."

    # Get issue data as JSON
    gh issue view "$issue_number" \
        --repo "$SOURCE_REPO" \
        --json number,title,body,state,labels,assignees,milestone \
        2>/dev/null || {
            log_error "Failed to fetch issue #$issue_number"
            return 1
        }
}

# Function to sanitize issue body (remove private info)
sanitize_body() {
    local body="$1"

    # Remove any mentions of private repos
    body=$(echo "$body" | sed 's/elshaddai/popkit-claude/g')

    # Remove Stripe/billing references (just in case)
    if echo "$body" | grep -qi "stripe\|billing\|payment"; then
        log_warning "Issue body contains billing-related keywords. Please review manually."
    fi

    echo "$body"
}

# Function to transform labels
transform_labels() {
    local labels="$1"

    # Remove private/monorepo labels
    labels=$(echo "$labels" | jq -r '
        map(select(
            .name != "app:elshaddai" and
            .name != "scope:monorepo" and
            .name != "app:genesis" and
            .name != "app:reseller" and
            .name != "app:runtheworld"
        )) |
        map(.name) |
        join(",")
    ')

    # Add migration label
    if [ -n "$labels" ]; then
        labels="$labels,migration"
    else
        labels="migration"
    fi

    echo "$labels"
}

# Function to create migration footer
create_footer() {
    local issue_number=$1

    cat <<EOF


---

**Migrated from:** $SOURCE_REPO#$issue_number
**Migration Date:** $(date +%Y-%m-%d)
**Migration Reason:** Repository split - moving PopKit issues to public repository

This issue was automatically migrated from the private elshaddai repository as part of the PopKit public release.
EOF
}

# Function to migrate a single issue
migrate_issue() {
    local issue_number=$1

    log_info "Migrating issue #$issue_number..."

    # Get issue data
    local issue_data
    issue_data=$(get_issue_data "$issue_number") || return 1

    # Extract fields
    local title=$(echo "$issue_data" | jq -r '.title')
    local body=$(echo "$issue_data" | jq -r '.body // ""')
    local state=$(echo "$issue_data" | jq -r '.state')
    local labels=$(echo "$issue_data" | jq -r '.labels')

    # Sanitize and transform
    body=$(sanitize_body "$body")
    labels=$(transform_labels "$labels")

    # Add migration footer
    body="$body$(create_footer "$issue_number")"

    log_info "  Title: $title"
    log_info "  State: $state"
    log_info "  Labels: $labels"

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would create issue in $TARGET_REPO"
        echo ""
        echo "Title: $title"
        echo "Labels: $labels"
        echo "State: $state"
        echo ""
        echo "Body:"
        echo "$body" | head -20
        echo "..."
        echo ""
        return 0
    fi

    # Create issue in target repo
    local new_issue_url
    new_issue_url=$(gh issue create \
        --repo "$TARGET_REPO" \
        --title "$title" \
        --body "$body" \
        --label "$labels" \
        2>&1) || {
            log_error "Failed to create issue: $new_issue_url"
            return 1
        }

    log_success "Created: $new_issue_url"

    # If original was closed, close the new one
    if [ "$state" = "CLOSED" ]; then
        local new_issue_number=$(echo "$new_issue_url" | grep -o '[0-9]*$')
        gh issue close "$new_issue_number" \
            --repo "$TARGET_REPO" \
            --comment "Migrated as closed from $SOURCE_REPO#$issue_number" \
            2>/dev/null || log_warning "Failed to close issue"
        log_info "  Closed (original was closed)"
    fi

    # Add comment to original issue
    gh issue comment "$issue_number" \
        --repo "$SOURCE_REPO" \
        --body "Migrated to $TARGET_REPO: $new_issue_url" \
        2>/dev/null || log_warning "Failed to add comment to source issue"

    echo ""
    sleep 2  # Rate limiting
}

# Function to migrate multiple issues
migrate_issues() {
    local issues=("$@")
    local total=${#issues[@]}
    local count=0
    local failed=0

    log_info "Migrating $total issues..."
    echo ""

    for issue in "${issues[@]}"; do
        ((count++))
        log_info "[$count/$total] Processing issue #$issue"

        if ! migrate_issue "$issue"; then
            ((failed++))
        fi
    done

    echo ""
    log_success "Migration complete!"
    log_info "Total: $total, Success: $((total - failed)), Failed: $failed"
}

# Main execution
main() {
    log_info "PopKit Issue Migration Script"
    log_info "Source: $SOURCE_REPO"
    log_info "Target: $TARGET_REPO"

    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN MODE - No issues will be created"
    fi

    echo ""

    # Migrate based on arguments
    if [ -n "$SPECIFIC_ISSUE" ]; then
        migrate_issue "$SPECIFIC_ISSUE"
    elif [ -n "$PHASE" ]; then
        case $PHASE in
            1)
                log_info "Migrating Phase 1 issues (critical)"
                migrate_issues "${PHASE1_ISSUES[@]}"
                ;;
            2)
                log_info "Migrating Phase 2 issues (features)"
                migrate_issues "${PHASE2_ISSUES[@]}"
                ;;
            3)
                log_info "Migrating Phase 3 issues (documentation)"
                migrate_issues "${PHASE3_ISSUES[@]}"
                ;;
            *)
                log_error "Invalid phase: $PHASE (valid: 1-3)"
                exit 1
                ;;
        esac
    elif [ "$MIGRATE_ALL" = true ]; then
        log_info "Migrating all recommended issues"
        migrate_issues "${PHASE1_ISSUES[@]}" "${PHASE2_ISSUES[@]}" "${PHASE3_ISSUES[@]}"
    else
        log_error "No migration target specified. Use --phase, --issue, or --all"
        echo ""
        echo "Run '$0 --help' for usage information"
        exit 1
    fi
}

# Run main
main
