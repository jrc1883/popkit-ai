# PopKit Plugin Cleanup Script
# Removes runtime state pollution from plugin packages

Write-Host "PopKit Plugin Cleanup" -ForegroundColor Cyan
Write-Host "=" * 50

# 1. Remove .claude runtime state from plugin packages
Write-Host "`nRemoving .claude runtime state from plugin packages..." -ForegroundColor Yellow
$claudeFolders = @(
    "packages\popkit-core\.claude",
    "packages\popkit-dev\.claude",
    "packages\popkit-ops\.claude",
    "packages\popkit-research\.claude"
)

foreach ($folder in $claudeFolders) {
    if (Test-Path $folder) {
        Write-Host "  Deleting: $folder" -ForegroundColor Red
        Remove-Item -Recurse -Force $folder
    }
}

# 2. Verify .gitignore has proper patterns
Write-Host "`nVerifying .gitignore patterns..." -ForegroundColor Yellow
$gitignoreContent = Get-Content .gitignore -Raw
if ($gitignoreContent -match "\.claude/") {
    Write-Host "  ✓ .claude/ is gitignored" -ForegroundColor Green
} else {
    Write-Host "  ✗ WARNING: .claude/ not in .gitignore" -ForegroundColor Red
}

# 3. Show plugin package structure (should only have .claude-plugin/)
Write-Host "`nPlugin Package Structure:" -ForegroundColor Yellow
$plugins = @("popkit-core", "popkit-dev", "popkit-ops", "popkit-research")
foreach ($plugin in $plugins) {
    Write-Host "  $plugin/" -ForegroundColor Cyan
    $dotFolders = Get-ChildItem "packages\$plugin" -Directory -Hidden -ErrorAction SilentlyContinue |
                  Where-Object { $_.Name -match "^\." }
    foreach ($folder in $dotFolders) {
        $status = if ($folder.Name -eq ".claude-plugin") { "✓" } else { "✗" }
        $color = if ($folder.Name -eq ".claude-plugin") { "Green" } else { "Red" }
        Write-Host "    $status $($folder.Name)/" -ForegroundColor $color
    }
}

# 4. Summary
Write-Host "`n" + ("=" * 50) -ForegroundColor Cyan
Write-Host "Cleanup Complete!" -ForegroundColor Green
Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Run: git status" -ForegroundColor White
Write-Host "  2. Verify no .claude folders exist in packages/*/" -ForegroundColor White
Write-Host "  3. Test plugin installation: /plugin install ./packages/popkit-core" -ForegroundColor White
