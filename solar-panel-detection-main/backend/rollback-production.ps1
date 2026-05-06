# Rollback Production Deployment
# Reverts traffic to previous revision in case of issues

param(
    [string]$ProjectId = "trim-descent-452802-t2",
    [string]$Region = "asia-southeast1",
    [string]$ServiceName = "solar-weather-api",
    [switch]$Force = $false
)

Write-Host "========================================" -ForegroundColor Red
Write-Host "Production Rollback" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "WARNING: This will rollback to the previous revision!" -ForegroundColor Yellow
Write-Host ""

# Load deployment info
if (-not (Test-Path "production-deployment-info.json")) {
    Write-Host "ERROR: production-deployment-info.json not found." -ForegroundColor Red
    Write-Host "Cannot determine which revision to rollback to." -ForegroundColor Red
    exit 1
}

$DeploymentInfo = Get-Content "production-deployment-info.json" | ConvertFrom-Json

Write-Host "Current Deployment Info:" -ForegroundColor Yellow
Write-Host "  New Revision: $($DeploymentInfo.new_revision)" -ForegroundColor White
Write-Host "  Old Revision: $($DeploymentInfo.old_revision)" -ForegroundColor White
Write-Host "  Deployed: $($DeploymentInfo.timestamp)" -ForegroundColor White
Write-Host ""

# Confirm rollback
if (-not $Force) {
    Write-Host "This will route 100% traffic back to: $($DeploymentInfo.old_revision)" -ForegroundColor Yellow
    $Confirm = Read-Host "Are you sure you want to rollback? (yes/no)"
    if ($Confirm -ne "yes") {
        Write-Host "Rollback cancelled." -ForegroundColor Yellow
        exit 0
    }
    Write-Host ""
}

# Set project
gcloud config set project $ProjectId | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Rolling back to previous revision..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Route 100% traffic to old revision
$RollbackCommand = @"
gcloud run services update-traffic $ServiceName ``
  --region $Region ``
  --to-revisions=$($DeploymentInfo.old_revision)=100 ``
  --project=$ProjectId
"@

Write-Host "Routing 100% traffic to: $($DeploymentInfo.old_revision)" -ForegroundColor Yellow
Invoke-Expression $RollbackCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Rollback failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Rollback completed successfully!" -ForegroundColor Green
Write-Host ""

# Save rollback info
$RollbackInfo = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    rolled_back_from = $DeploymentInfo.new_revision
    rolled_back_to = $DeploymentInfo.old_revision
    reason = "Manual rollback"
}

$RollbackInfo | ConvertTo-Json | Out-File -FilePath "production-rollback-info.json" -Encoding UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Rollback Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Current Status:" -ForegroundColor Yellow
Write-Host "  Active revision: $($DeploymentInfo.old_revision) (100% traffic)" -ForegroundColor White
Write-Host "  Rolled back from: $($DeploymentInfo.new_revision)" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Verify service is working: .\verify-production.ps1" -ForegroundColor White
Write-Host "  2. Investigate issues with new revision" -ForegroundColor White
Write-Host "  3. Fix issues and redeploy when ready" -ForegroundColor White
Write-Host "  4. Document rollback reason in production-rollback-info.json" -ForegroundColor White
Write-Host ""
Write-Host "Rollback info saved to: production-rollback-info.json" -ForegroundColor Yellow
Write-Host ""

