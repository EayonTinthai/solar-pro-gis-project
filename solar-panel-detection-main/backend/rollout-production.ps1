# Gradual Rollout Script for Production
# Increases traffic to new revision in stages

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet(50, 100)]
    [int]$Stage,
    
    [string]$ProjectId = "trim-descent-452802-t2",
    [string]$Region = "asia-southeast1",
    [string]$ServiceName = "solar-weather-api",
    [switch]$Force = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Production Rollout - Stage $Stage%" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Load deployment info
if (-not (Test-Path "production-deployment-info.json")) {
    Write-Host "ERROR: production-deployment-info.json not found." -ForegroundColor Red
    Write-Host "Please run deploy-production.ps1 first." -ForegroundColor Red
    exit 1
}

$DeploymentInfo = Get-Content "production-deployment-info.json" | ConvertFrom-Json

Write-Host "Deployment Info:" -ForegroundColor Yellow
Write-Host "  Timestamp: $($DeploymentInfo.timestamp)" -ForegroundColor White
Write-Host "  New Revision: $($DeploymentInfo.new_revision)" -ForegroundColor White
Write-Host "  Old Revision: $($DeploymentInfo.old_revision)" -ForegroundColor White
Write-Host "  Service URL: $($DeploymentInfo.service_url)" -ForegroundColor White
Write-Host ""

# Confirm rollout
if (-not $Force) {
    Write-Host "WARNING: This will route $Stage% of traffic to the new revision." -ForegroundColor Yellow
    $Confirm = Read-Host "Continue? (yes/no)"
    if ($Confirm -ne "yes") {
        Write-Host "Rollout cancelled." -ForegroundColor Yellow
        exit 0
    }
    Write-Host ""
}

# Set project
gcloud config set project $ProjectId | Out-Null

# Get current revisions
Write-Host "Getting current revision information..." -ForegroundColor Yellow
$Revisions = gcloud run revisions list --service $ServiceName --region $Region --format="value(metadata.name)" --project=$ProjectId | Select-Object -First 2

if ($Revisions.Count -lt 2) {
    Write-Host "ERROR: Could not find revisions." -ForegroundColor Red
    exit 1
}

$NewRevision = $Revisions[0]
$OldRevision = $Revisions[1]

Write-Host "New revision: $NewRevision" -ForegroundColor Cyan
Write-Host "Old revision: $OldRevision" -ForegroundColor Cyan
Write-Host ""

# Calculate traffic split
$NewTraffic = $Stage
$OldTraffic = 100 - $Stage

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Updating Traffic Split..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "New traffic split: $NewTraffic% new, $OldTraffic% old" -ForegroundColor Yellow
Write-Host ""

# Update traffic
$TrafficSplitCommand = @"
gcloud run services update-traffic $ServiceName ``
  --region $Region ``
  --to-revisions=$NewRevision=$NewTraffic,$OldRevision=$OldTraffic ``
  --project=$ProjectId
"@

Invoke-Expression $TrafficSplitCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Traffic split failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Traffic split updated successfully!" -ForegroundColor Green
Write-Host ""

# Update deployment info
$DeploymentInfo.current_traffic = $NewTraffic
$DeploymentInfo.last_update = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$DeploymentInfo | ConvertTo-Json | Out-File -FilePath "production-deployment-info.json" -Encoding UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Rollout Stage $Stage% Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Current Status:" -ForegroundColor Yellow
Write-Host "  New revision: $NewRevision ($NewTraffic% traffic)" -ForegroundColor White
Write-Host "  Old revision: $OldRevision ($OldTraffic% traffic)" -ForegroundColor White
Write-Host ""

if ($Stage -eq 50) {
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Monitor for 1 hour" -ForegroundColor White
    Write-Host "  2. Check error rates and performance metrics" -ForegroundColor White
    Write-Host "  3. If stable, run: .\rollout-production.ps1 -Stage 100" -ForegroundColor White
    Write-Host "  4. If issues occur, run: .\rollback-production.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Monitoring period: 1 hour" -ForegroundColor Yellow
    Write-Host "Monitor until: $((Get-Date).AddHours(1).ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
} elseif ($Stage -eq 100) {
    Write-Host "Deployment Complete!" -ForegroundColor Green
    Write-Host "  All traffic is now routed to the new revision." -ForegroundColor White
    Write-Host ""
    Write-Host "Post-Deployment Tasks:" -ForegroundColor Yellow
    Write-Host "  1. Continue monitoring for 24 hours" -ForegroundColor White
    Write-Host "  2. Run post-deployment verification: .\verify-production.ps1" -ForegroundColor White
    Write-Host "  3. Update documentation if needed" -ForegroundColor White
    Write-Host "  4. Notify stakeholders of successful deployment" -ForegroundColor White
}

Write-Host ""
Write-Host "Monitoring Commands:" -ForegroundColor Yellow
Write-Host "  .\monitor-production.ps1" -ForegroundColor White
Write-Host "  .\verify-production.ps1" -ForegroundColor White
Write-Host ""

