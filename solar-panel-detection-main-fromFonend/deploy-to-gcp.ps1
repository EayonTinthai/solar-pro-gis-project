#!/usr/bin/env pwsh
# Deploy Frontend to Google Cloud Platform (Cloud Storage + CDN)

Write-Host "🚀 Deploying Frontend to Google Cloud Platform..." -ForegroundColor Green

# Configuration
$PROJECT_ID = "solar-panel-detection-440806"
$BUCKET_NAME = "solar-weather-frontend"
$REGION = "asia-southeast1"

Write-Host "📋 Deployment Configuration:" -ForegroundColor Cyan
Write-Host "  Project ID: $PROJECT_ID" -ForegroundColor White
Write-Host "  Bucket: $BUCKET_NAME" -ForegroundColor White
Write-Host "  Region: $REGION" -ForegroundColor White
Write-Host ""

# Navigate to frontend directory
Set-Location frontend

try {
    # Step 1: Build the project
    Write-Host "🔨 Step 1: Building frontend..." -ForegroundColor Yellow
    npm run build
    
    if (-not (Test-Path "dist")) {
        Write-Host "❌ Build failed - dist directory not found" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Build completed successfully" -ForegroundColor Green
    Write-Host ""

    # Step 2: Set GCP project
    Write-Host "🔧 Step 2: Setting GCP project..." -ForegroundColor Yellow
    gcloud config set project $PROJECT_ID
    Write-Host "✅ Project set to $PROJECT_ID" -ForegroundColor Green
    Write-Host ""

    # Step 3: Create storage bucket (if not exists)
    Write-Host "🪣 Step 3: Creating storage bucket..." -ForegroundColor Yellow
    $bucketCheck = gcloud storage buckets describe "gs://$BUCKET_NAME" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Creating new bucket: $BUCKET_NAME" -ForegroundColor Cyan
        gcloud storage buckets create "gs://$BUCKET_NAME" --location=$REGION
        
        # Make bucket public for web hosting
        gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" --member=allUsers --role=roles/storage.objectViewer
    } else {
        Write-Host "Bucket $BUCKET_NAME already exists" -ForegroundColor Cyan
    }
    Write-Host "✅ Storage bucket ready" -ForegroundColor Green
    Write-Host ""

    # Step 4: Upload files to bucket
    Write-Host "📤 Step 4: Uploading files to Cloud Storage..." -ForegroundColor Yellow
    
    # Upload all files from dist directory
    gcloud storage cp -r dist/* "gs://$BUCKET_NAME/"
    
    Write-Host "✅ Files uploaded successfully" -ForegroundColor Green
    Write-Host ""

    # Step 5: Configure bucket for web hosting
    Write-Host "🌐 Step 5: Configuring web hosting..." -ForegroundColor Yellow
    gcloud storage buckets update "gs://$BUCKET_NAME" --web-main-page-suffix=index.html --web-error-page=index.html
    Write-Host "✅ Web hosting configured" -ForegroundColor Green
    Write-Host ""

    # Success message
    $publicUrl = "https://storage.googleapis.com/$BUCKET_NAME/index.html"
    Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Access URLs:" -ForegroundColor Cyan
    Write-Host "  Public URL: $publicUrl" -ForegroundColor White
    Write-Host ""

}
catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    Set-Location ..
}

Write-Host ""
Write-Host "🚀 GCP deployment complete!" -ForegroundColor Green