# Deploy to Staging Environment
# This script builds and deploys the Solar Potential API to Cloud Run staging

param(
    [string]$ProjectId = "trim-descent-452802-t2",
    [string]$Region = "asia-southeast1",
    [string]$ServiceName = "solar-weather-api-staging",
    [switch]$SkipBuild = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Solar Potential API - Staging Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

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
    Write-Host "Step 1: Building Docker image..." -ForegroundColor Green
    Write-Host "Using Cloud Build with cloudbuild-bigquery.yaml" -ForegroundColor Yellow
    
    # Submit build to Cloud Build
    $BuildCommand = "gcloud builds submit --config=cloudbuild-bigquery.yaml --project=$ProjectId"
    Write-Host "Running: $BuildCommand" -ForegroundColor Gray
    
    Invoke-Expression $BuildCommand
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "Step 1: Skipping build (using existing image)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 2: Deploy to Cloud Run Staging
Write-Host "Step 2: Deploying to Cloud Run staging..." -ForegroundColor Green
Write-Host "Service: $ServiceName" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host ""

# Deploy command
$DeployCommand = @"
gcloud run deploy $ServiceName ``
  --image gcr.io/$ProjectId/solar-bigquery-api:latest ``
  --platform managed ``
  --region $Region ``
  --allow-unauthenticated ``
  --memory 2Gi ``
  --cpu 2 ``
  --min-instances 0 ``
  --max-instances 5 ``
  --timeout 60s ``
  --set-env-vars "GCP_PROJECT=$ProjectId,BIGQUERY_DATASET=openbuildings,BIGQUERY_TABLE=thailand_raw,API_VERSION=2.2.0,LOG_LEVEL=INFO,CACHE_TTL_STATS=86400,CACHE_TTL_BUILDINGS=3600,CACHE_TTL_WEATHER=3600,CACHE_TTL_RANKINGS=86400,CACHE_MAX_SIZE=1000,RATE_LIMIT_PUBLIC=10,RATE_LIMIT_AUTHENTICATED=50,MAX_WORKERS=4,BIGQUERY_TIMEOUT_SECONDS=30,REQUEST_TIMEOUT_SECONDS=30" ``
  --project=$ProjectId
"@

Write-Host "Running deployment command..." -ForegroundColor Gray
Invoke-Expression $DeployCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Deployment failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host ""

# Step 3: Get service URL
Write-Host "Step 3: Getting service URL..." -ForegroundColor Green
$ServiceUrl = gcloud run services describe $ServiceName --region $Region --format "value(status.url)" --project=$ProjectId

if ($ServiceUrl) {
    Write-Host "Service URL: $ServiceUrl" -ForegroundColor Cyan
    Write-Host ""
    
    # Save URL to file for smoke tests
    $ServiceUrl | Out-File -FilePath "staging-url.txt" -Encoding UTF8
    Write-Host "Service URL saved to: staging-url.txt" -ForegroundColor Yellow
} else {
    Write-Host "WARNING: Could not retrieve service URL" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Staging Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run smoke tests: .\run-smoke-tests.ps1" -ForegroundColor White
Write-Host "2. Run full test suite: .\run-staging-tests.ps1" -ForegroundColor White
Write-Host "3. Monitor logs: gcloud run services logs tail $ServiceName --region $Region" -ForegroundColor White
Write-Host ""
