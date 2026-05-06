# Deploy BigQuery Buildings API to Cloud Run
# This API includes building footprints + weather integration

Write-Host "`n=== Deploying BigQuery Buildings API to Cloud Run ===" -ForegroundColor Cyan
Write-Host ""

# Set project
Write-Host "Setting GCP project..." -ForegroundColor Yellow
gcloud config set project trim-descent-452802-t2

Write-Host ""

# Build and deploy
Write-Host "Building and deploying BigQuery API..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Gray

Set-Location backend

# Build Docker image
Write-Host "Building Docker image with Cloud Build..." -ForegroundColor Yellow
gcloud builds submit --config cloudbuild-bigquery.yaml --timeout=20m .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy solar-weather-api `
    --image gcr.io/trim-descent-452802-t2/solar-bigquery-api `
    --region asia-southeast1 `
    --platform managed `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 2 `
    --min-instances 0 `
    --max-instances 10 `
    --port 8080 `
    --timeout 300 `
    --set-env-vars "GCP_PROJECT=trim-descent-452802-t2"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Deployment Successful! ===" -ForegroundColor Green
    Write-Host ""
    
    $url = gcloud run services describe solar-weather-api --region=asia-southeast1 --format="value(status.url)"
    Write-Host "API URL: $url" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available endpoints:" -ForegroundColor White
    Write-Host "  GET  /stats - Database statistics" -ForegroundColor Gray
    Write-Host "  GET  /buildings/bbox - Buildings in bounding box" -ForegroundColor Gray
    Write-Host "  GET  /buildings/nearby - Buildings near point" -ForegroundColor Gray
    Write-Host "  GET  /weather/forecast - Weather forecast" -ForegroundColor Gray
    Write-Host "  POST /solar/calculate - Solar potential calculation" -ForegroundColor Gray
    Write-Host "  GET  /solar/forecast - Solar generation forecast" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Test it:" -ForegroundColor Yellow
    Write-Host "  curl `"$url/stats`"" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Deployment failed!" -ForegroundColor Red
    Write-Host "Check the error messages above" -ForegroundColor Yellow
    exit 1
}

Set-Location ..
