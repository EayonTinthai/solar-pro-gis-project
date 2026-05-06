# Deploy to Production Environment with Traffic Splitting
# This script builds and deploys the Solar Potential API to Cloud Run production
# with gradual traffic rollout for safe deployments

param(
    [string]$ProjectId = "trim-descent-452802-t2",
    [string]$Region = "asia-southeast1",
    [string]$ServiceName = "solar-weather-api",
    [string]$ImageTag = "latest",
    [switch]$SkipBuild = $false,
    [switch]$AutoRollout = $false,
    [int]$InitialTrafficPercent = 10,
    [int]$MonitoringDelayMinutes = 5
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Solar Potential API - Production Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "WARNING: This will deploy to PRODUCTION!" -ForegroundColor Red
Write-Host ""

# Confirm deployment
if (-not $AutoRollout) {
    $Confirm = Read-Host "Are you sure you want to deploy to production? (yes/no)"
    if ($Confirm -ne "yes") {
        Write-Host "Deployment cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: gcloud CLI not found. Please install Google Cloud SDK." -ForegroundColor Red
    exit 1
}

# Set project
Write-Host "Setting GCP project to: $ProjectId" -ForegroundColor Yellow
gcloud config set project $ProjectId

# Navigate to backend directory
$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $BackendDir

Write-Host ""
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# Step 1: Build Docker image (unless skipped)
if (-not $SkipBuild) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Step 1: Building Docker image..." -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Get current git commit SHA for tagging
    $GitSha = git rev-parse --short HEAD 2>$null
    if (-not $GitSha) {
        $GitSha = Get-Date -Format "yyyyMMddHHmmss"
    }
    
    Write-Host "Building image with tag: v2.2.0-$GitSha" -ForegroundColor Yellow
    Write-Host ""
    
    # Build using Cloud Build
    $BuildCommand = "gcloud builds submit --config=cloudbuild-bigquery.yaml --project=$ProjectId"
    Write-Host "Running: $BuildCommand" -ForegroundColor Gray
    
    Invoke-Expression $BuildCommand
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
    Write-Host ""
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "Step 1: Skipping build (using existing image: $ImageTag)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 2: Deploy new version with 0% traffic
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Deploying new version (0% traffic)..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ImageUrl = "gcr.io/$ProjectId/solar-bigquery-api:$ImageTag"
Write-Host "Image: $ImageUrl" -ForegroundColor Yellow
Write-Host "Service: $ServiceName" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host ""

# Deploy with --no-traffic flag to create new revision without routing traffic
$DeployCommand = @"
gcloud run deploy $ServiceName ``
  --image $ImageUrl ``
  --platform managed ``
  --region $Region ``
  --allow-unauthenticated ``
  --memory 2Gi ``
  --cpu 2 ``
  --min-instances 1 ``
  --max-instances 10 ``
  --timeout 60s ``
  --no-traffic ``
  --set-env-vars "GCP_PROJECT=$ProjectId,BIGQUERY_DATASET=openbuildings,BIGQUERY_TABLE=thailand_raw,API_VERSION=2.2.0,LOG_LEVEL=INFO,CACHE_TTL_STATS=86400,CACHE_TTL_BUILDINGS=3600,CACHE_TTL_WEATHER=3600,CACHE_TTL_RANKINGS=86400,CACHE_MAX_SIZE=1000,RATE_LIMIT_PUBLIC=10,RATE_LIMIT_AUTHENTICATED=50,MAX_WORKERS=4,BIGQUERY_TIMEOUT_SECONDS=30,REQUEST_TIMEOUT_SECONDS=30" ``
  --project=$ProjectId
"@

Write-Host "Deploying new revision with 0% traffic..." -ForegroundColor Gray
Invoke-Expression $DeployCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Deployment failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "New revision deployed successfully (0% traffic)!" -ForegroundColor Green
Write-Host ""

# Get revision names
Write-Host "Getting revision information..." -ForegroundColor Yellow
$Revisions = gcloud run revisions list --service $ServiceName --region $Region --format="value(metadata.name)" --project=$ProjectId | Select-Object -First 2

if ($Revisions.Count -lt 2) {
    Write-Host "ERROR: Could not find revisions. Need at least 2 revisions for traffic splitting." -ForegroundColor Red
    exit 1
}

$NewRevision = $Revisions[0]
$OldRevision = $Revisions[1]

Write-Host "New revision: $NewRevision" -ForegroundColor Cyan
Write-Host "Old revision: $OldRevision" -ForegroundColor Cyan
Write-Host ""

# Step 3: Split traffic to new version (initial percentage)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 3: Routing $InitialTrafficPercent% traffic to new version..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$OldTrafficPercent = 100 - $InitialTrafficPercent

$TrafficSplitCommand = @"
gcloud run services update-traffic $ServiceName ``
  --region $Region ``
  --to-revisions=$NewRevision=$InitialTrafficPercent,$OldRevision=$OldTrafficPercent ``
  --project=$ProjectId
"@

Write-Host "Splitting traffic: $InitialTrafficPercent% new, $OldTrafficPercent% old" -ForegroundColor Yellow
Invoke-Expression $TrafficSplitCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Traffic split failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Traffic split completed: $InitialTrafficPercent% → new revision" -ForegroundColor Green
Write-Host ""

# Get service URL
$ServiceUrl = gcloud run services describe $ServiceName --region $Region --format "value(status.url)" --project=$ProjectId

Write-Host "Service URL: $ServiceUrl" -ForegroundColor Cyan
Write-Host ""

# Step 4: Monitor for issues
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 4: Monitoring deployment..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Monitoring for $MonitoringDelayMinutes minutes..." -ForegroundColor Yellow
Write-Host "Check for errors in logs and metrics dashboard." -ForegroundColor Yellow
Write-Host ""
Write-Host "Commands to monitor:" -ForegroundColor White
Write-Host "  Logs:    gcloud run services logs tail $ServiceName --region $Region" -ForegroundColor Gray
Write-Host "  Metrics: https://console.cloud.google.com/run/detail/$Region/$ServiceName/metrics" -ForegroundColor Gray
Write-Host ""

# Save deployment info
$DeploymentInfo = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    service = $ServiceName
    region = $Region
    new_revision = $NewRevision
    old_revision = $OldRevision
    initial_traffic = $InitialTrafficPercent
    service_url = $ServiceUrl
    image = $ImageUrl
}

$DeploymentInfo | ConvertTo-Json | Out-File -FilePath "production-deployment-info.json" -Encoding UTF8
Write-Host "Deployment info saved to: production-deployment-info.json" -ForegroundColor Yellow
Write-Host ""

# Create monitoring script
$MonitoringScript = @"
# Quick monitoring commands for production deployment
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# View logs
gcloud run services logs tail $ServiceName --region $Region --project=$ProjectId

# View metrics
# Open: https://console.cloud.google.com/run/detail/$Region/$ServiceName/metrics?project=$ProjectId

# Check health
curl $ServiceUrl/health

# Check error rate
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$ServiceName AND severity>=ERROR" --limit 50 --format json --project=$ProjectId

# Get current traffic split
gcloud run services describe $ServiceName --region $Region --format="value(status.traffic)" --project=$ProjectId
"@

$MonitoringScript | Out-File -FilePath "monitor-production.ps1" -Encoding UTF8
Write-Host "Monitoring script saved to: monitor-production.ps1" -ForegroundColor Yellow
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Initial Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Current Status:" -ForegroundColor Yellow
Write-Host "  New revision: $NewRevision ($InitialTrafficPercent% traffic)" -ForegroundColor White
Write-Host "  Old revision: $OldRevision ($OldTrafficPercent% traffic)" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Monitor logs and metrics for $MonitoringDelayMinutes minutes" -ForegroundColor White
Write-Host "  2. If no issues, run: .\rollout-production.ps1 -Stage 50" -ForegroundColor White
Write-Host "  3. Monitor for 1 hour" -ForegroundColor White
Write-Host "  4. If stable, run: .\rollout-production.ps1 -Stage 100" -ForegroundColor White
Write-Host "  5. If issues occur, run: .\rollback-production.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Monitoring Commands:" -ForegroundColor Yellow
Write-Host "  .\monitor-production.ps1" -ForegroundColor White
Write-Host "  .\verify-production.ps1" -ForegroundColor White
Write-Host ""

