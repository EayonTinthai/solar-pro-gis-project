#!/usr/bin/env pwsh
# Deploy Frontend with Weather Integration to Firebase

Write-Host "🚀 Deploying Frontend with Weather Integration..." -ForegroundColor Green

# Set project variables
$PROJECT_ID = "solar-panel-detection-440806"
$FRONTEND_DIR = "frontend"

# Check if we're in the right directory
if (-not (Test-Path $FRONTEND_DIR)) {
    Write-Host "❌ Frontend directory not found. Make sure you're in the project root." -ForegroundColor Red
    exit 1
}

# Navigate to frontend directory
Set-Location $FRONTEND_DIR

try {
    # Install dependencies
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install

    # Build the project
    Write-Host "🔨 Building frontend with weather integration..." -ForegroundColor Yellow
    npm run build

    # Check if build was successful
    if (-not (Test-Path "dist")) {
        Write-Host "❌ Build failed - dist directory not found" -ForegroundColor Red
        exit 1
    }

    # Deploy to Firebase
    Write-Host "🚀 Deploying to Firebase..." -ForegroundColor Yellow
    firebase deploy --project $PROJECT_ID

    Write-Host "✅ Frontend with weather integration deployed successfully!" -ForegroundColor Green
    Write-Host "🌐 URL: https://$PROJECT_ID.web.app" -ForegroundColor Cyan

} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # Return to original directory
    Set-Location ..
}

Write-Host "🎉 Weather-enhanced frontend deployment complete!" -ForegroundColor Green