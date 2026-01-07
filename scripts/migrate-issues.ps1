# PopKit Issue Migration Script (PowerShell)
# Migrates issues from jrc1883/elshaddai to jrc1883/popkit-claude
#
# Usage:
#   .\scripts\migrate-issues.ps1 -DryRun                # Preview only
#   .\scripts\migrate-issues.ps1 -Phase 1               # Migrate Phase 1 (critical)
#   .\scripts\migrate-issues.ps1 -Issue 691             # Migrate specific issue
#   .\scripts\migrate-issues.ps1 -All                   # Migrate all recommended
#   .\scripts\migrate-issues.ps1 -Help                  # Show help

param(
    [switch]$DryRun,
    [int]$Phase = 0,
    [int]$Issue = 0,
    [switch]$All,
    [switch]$Help
)

# Configuration
$SourceRepo = "jrc1883/elshaddai"
$TargetRepo = "jrc1883/popkit-claude"

# Color functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Show help
if ($Help) {
    Write-Host @"
PopKit Issue Migration Script

Migrates issues from elshaddai (private) to popkit-claude (public)

Usage:
  .\scripts\migrate-issues.ps1 [OPTIONS]

Options:
  -DryRun             Preview migrations without creating issues
  -Phase N            Migrate issues from Phase N (1-3)
  -Issue NUM          Migrate specific issue number
  -All                Migrate all recommended issues
  -Help               Show this help message

Phases:
  Phase 1: Critical issues (P0/P1-high, release blockers)
  Phase 2: Features & enhancements
  Phase 3: Documentation & low priority

Examples:
  .\scripts\migrate-issues.ps1 -DryRun -Phase 1
  .\scripts\migrate-issues.ps1 -Issue 691
  .\scripts\migrate-issues.ps1 -All

"@
    exit 0
}

# Check for gh CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) is not installed. Please install it first."
    exit 1
}

# Verify authentication
try {
    gh auth status 2>&1 | Out-Null
} catch {
    Write-Error "Not authenticated with GitHub. Run 'gh auth login' first."
    exit 1
}

# Phase definitions
$Phase1Issues = @(
    691, 690, 689, 688, 676, 675, 674, 673, 679, 677,
    580, 589, 588, 587, 586, 585, 584, 583,
    519, 522, 520, 518,
    650, 613
)

$Phase2Issues = @(
    666, 511, 512, 513, 514, 515, 516, 517,
    483, 484, 485, 486, 487, 499, 496,
    498, 488, 629, 628,
    625, 626, 627, 671, 672,
    603, 687
)

$Phase3Issues = @(
    685, 618, 617, 602, 579, 569, 540, 523,
    527, 526,
    220, 215, 216, 217, 218, 219, 221,
    471, 472, 500, 501,
    201, 202, 203, 204, 205, 206, 207, 208, 209, 210,
    211, 212, 213, 214, 222, 223, 224, 225, 226, 227
)

# Function to get issue data
function Get-IssueData {
    param([int]$IssueNumber)

    Write-Info "Fetching issue #$IssueNumber from $SourceRepo..."

    try {
        $json = gh issue view $IssueNumber `
            --repo $SourceRepo `
            --json number,title,body,state,labels,assignees,milestone `
            2>&1 | ConvertFrom-Json

        return $json
    } catch {
        Write-Error "Failed to fetch issue #$IssueNumber"
        return $null
    }
}

# Function to sanitize body
function Sanitize-Body {
    param([string]$Body)

    # Replace repo references
    $Body = $Body -replace 'elshaddai', 'popkit-claude'

    # Check for private keywords
    if ($Body -match 'stripe|billing|payment') {
        Write-Warning "Issue body contains billing-related keywords. Please review manually."
    }

    return $Body
}

# Function to transform labels
function Transform-Labels {
    param([array]$Labels)

    # Filter out private labels
    $FilteredLabels = $Labels | Where-Object {
        $_.name -notin @('app:elshaddai', 'scope:monorepo', 'app:genesis', 'app:reseller', 'app:runtheworld')
    } | ForEach-Object { $_.name }

    # Add migration label
    $FilteredLabels += 'migration'

    return ($FilteredLabels -join ',')
}

# Function to create footer
function Create-Footer {
    param([int]$IssueNumber)

    $Date = Get-Date -Format "yyyy-MM-dd"

    return @"


---

**Migrated from:** $SourceRepo#$IssueNumber
**Migration Date:** $Date
**Migration Reason:** Repository split - moving PopKit issues to public repository

This issue was automatically migrated from the private elshaddai repository as part of the PopKit public release.
"@
}

# Function to migrate single issue
function Migrate-Issue {
    param([int]$IssueNumber)

    Write-Info "Migrating issue #$IssueNumber..."

    # Get issue data
    $IssueData = Get-IssueData -IssueNumber $IssueNumber
    if (-not $IssueData) {
        return $false
    }

    # Extract fields
    $Title = $IssueData.title
    $Body = if ($IssueData.body) { $IssueData.body } else { "" }
    $State = $IssueData.state
    $Labels = Transform-Labels -Labels $IssueData.labels

    # Sanitize
    $Body = Sanitize-Body -Body $Body
    $Body += Create-Footer -IssueNumber $IssueNumber

    Write-Info "  Title: $Title"
    Write-Info "  State: $State"
    Write-Info "  Labels: $Labels"

    if ($DryRun) {
        Write-Warning "[DRY RUN] Would create issue in $TargetRepo"
        Write-Host ""
        Write-Host "Title: $Title"
        Write-Host "Labels: $Labels"
        Write-Host "State: $State"
        Write-Host ""
        Write-Host "Body:"
        Write-Host ($Body -split "`n" | Select-Object -First 20)
        Write-Host "..."
        Write-Host ""
        return $true
    }

    # Create issue
    try {
        $NewIssueUrl = gh issue create `
            --repo $TargetRepo `
            --title $Title `
            --body $Body `
            --label $Labels `
            2>&1

        Write-Success "Created: $NewIssueUrl"

        # Close if original was closed
        if ($State -eq "CLOSED") {
            $NewIssueNumber = $NewIssueUrl -replace '.*/', ''
            gh issue close $NewIssueNumber `
                --repo $TargetRepo `
                --comment "Migrated as closed from $SourceRepo#$IssueNumber" `
                2>&1 | Out-Null
            Write-Info "  Closed (original was closed)"
        }

        # Comment on original
        gh issue comment $IssueNumber `
            --repo $SourceRepo `
            --body "Migrated to $TargetRepo: $NewIssueUrl" `
            2>&1 | Out-Null

        Write-Host ""
        Start-Sleep -Seconds 2  # Rate limiting
        return $true

    } catch {
        Write-Error "Failed to create issue: $_"
        return $false
    }
}

# Function to migrate multiple issues
function Migrate-Issues {
    param([array]$Issues)

    $Total = $Issues.Count
    $Count = 0
    $Failed = 0

    Write-Info "Migrating $Total issues..."
    Write-Host ""

    foreach ($IssueNum in $Issues) {
        $Count++
        Write-Info "[$Count/$Total] Processing issue #$IssueNum"

        if (-not (Migrate-Issue -IssueNumber $IssueNum)) {
            $Failed++
        }
    }

    Write-Host ""
    Write-Success "Migration complete!"
    Write-Info "Total: $Total, Success: $($Total - $Failed), Failed: $Failed"
}

# Main execution
Write-Info "PopKit Issue Migration Script"
Write-Info "Source: $SourceRepo"
Write-Info "Target: $TargetRepo"

if ($DryRun) {
    Write-Warning "DRY RUN MODE - No issues will be created"
}

Write-Host ""

# Migrate based on arguments
if ($Issue -ne 0) {
    Migrate-Issue -IssueNumber $Issue
} elseif ($Phase -ne 0) {
    switch ($Phase) {
        1 {
            Write-Info "Migrating Phase 1 issues (critical)"
            Migrate-Issues -Issues $Phase1Issues
        }
        2 {
            Write-Info "Migrating Phase 2 issues (features)"
            Migrate-Issues -Issues $Phase2Issues
        }
        3 {
            Write-Info "Migrating Phase 3 issues (documentation)"
            Migrate-Issues -Issues $Phase3Issues
        }
        default {
            Write-Error "Invalid phase: $Phase (valid: 1-3)"
            exit 1
        }
    }
} elseif ($All) {
    Write-Info "Migrating all recommended issues"
    $AllIssues = $Phase1Issues + $Phase2Issues + $Phase3Issues
    Migrate-Issues -Issues $AllIssues
} else {
    Write-Error "No migration target specified. Use -Phase, -Issue, or -All"
    Write-Host ""
    Write-Host "Run '.\scripts\migrate-issues.ps1 -Help' for usage information"
    exit 1
}
