# Deployment Status Check Script

Write-Host "`n=== Solar Panel Detection System - Deployment Status ===" -ForegroundColor Cyan
Write-Host ""

# Check GCP Project
Write-Host "Checking GCP Project..." -ForegroundColor Yellow
$project = gcloud config get-value project 2>$null
Write-Host "Current Project: $project" -ForegroundColor White

Write-Host ""

# Check Backend API
Write-Host "Checking Backend API..." -ForegroundColor Yellow
$backendUrl = "https://solar-weather-api-715107904640.asia-southeast1.run.app"
try {
    $health = Invoke-RestMethod -Uri "$backendUrl/health" -Method Get -TimeoutSec 10
    Write-Host "Backend Status: $($health.status)" -ForegroundColor Green
    Write-Host "Weather API: $($health.weather_api)" -ForegroundColor Green
} catch {
    Write-Host "Backend API Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Check Frontend Deployment
Write-Host "Checking Frontend Deployment..." -ForegroundColor Yellow
$frontendUrl = "https://storage.googleapis.com/solar-weather-frontend/index.html"
try {
    $response = Invoke-WebRequest -Uri $frontendUrl -Method Head -TimeoutSec 10
    Write-Host "Frontend Status: $($response.StatusCode) $($response.StatusDescription)" -ForegroundColor Green
} catch {
    Write-Host "Frontend Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Check Environment File
Write-Host "Checking Environment Configuration..." -ForegroundColor Yellow
$envFile = "frontend/.env"
if (Test-Path $envFile) {
    Write-Host "Environment file found: $envFile" -ForegroundColor Green
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match "VITE_CLERK_PUBLISHABLE_KEY=pk_") {
        Write-Host "Clerk key is configured" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Clerk key may be missing or invalid" -ForegroundColor Yellow
    }
} else {
    Write-Host "Environment file not found" -ForegroundColor Red
}

Write-Host ""

# Summary
Write-Host "=== Deployment URLs ===" -ForegroundColor Cyan
Write-Host "Frontend: $frontendUrl" -ForegroundColor White
Write-Host "Backend:  $backendUrl" -ForegroundColor White
Write-Host "API Docs: $backendUrl/docs" -ForegroundColor White
Write-Host ""

Write-Host "If you see a blank page, update the Clerk key in frontend/.env" -ForegroundColor Yellow
Write-Host "Get your key from: https://dashboard.clerk.com/" -ForegroundColor Yellow
Write-Host ""
Write-Host "Then rebuild and redeploy:" -ForegroundColor Yellow
Write-Host "  cd frontend" -ForegroundColor White
Write-Host "  npm run build" -ForegroundColor White
Write-Host "  gcloud storage cp -r dist/* gs://solar-weather-frontend/" -ForegroundColor White
Write-Host ""
