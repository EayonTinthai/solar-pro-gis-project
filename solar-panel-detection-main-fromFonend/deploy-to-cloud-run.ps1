# Deploy Weather-Enhanced Frontend to Cloud Run
# Updates the existing toothless-solar-frontend service

Write-Host "`n=== Deploying Weather-Enhanced Frontend to Cloud Run ===" -ForegroundColor Cyan
Write-Host ""

# Set project
Write-Host "Setting GCP project..." -ForegroundColor Yellow
gcloud config set project trim-descent-452802-t2

Write-Host ""

# Build frontend
Write-Host "Building frontend with weather integration..." -ForegroundColor Yellow
Set-Location frontend
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Build completed successfully!" -ForegroundColor Green
Set-Location ..

Write-Host ""

# Create Dockerfile for Cloud Run if not exists
Write-Host "Preparing Docker configuration..." -ForegroundColor Yellow

$dockerfileContent = @"
FROM nginx:alpine

# Copy built files
COPY frontend/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 8080 (Cloud Run requirement)
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
"@

$nginxConfig = @"
server {
    listen 8080;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # SPA routing - serve index.html for all routes
    location / {
        try_files `$uri `$uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
"@

Set-Content -Path "Dockerfile" -Value $dockerfileContent
Set-Content -Path "nginx.conf" -Value $nginxConfig

Write-Host "Docker configuration created!" -ForegroundColor Green

Write-Host ""

# Build and deploy to Cloud Run
Write-Host "Building and deploying to Cloud Run..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray

gcloud run deploy toothless-solar-frontend `
    --source . `
    --region asia-southeast1 `
    --platform managed `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 10 `
    --port 8080

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Deployment Successful! ===" -ForegroundColor Green
    Write-Host ""
    
    $url = gcloud run services describe toothless-solar-frontend --region=asia-southeast1 --format="value(status.url)"
    Write-Host "Frontend URL: $url" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Weather features now available:" -ForegroundColor White
    Write-Host "  - Weather Panel (cloud icon)" -ForegroundColor Gray
    Write-Host "  - Building weather info" -ForegroundColor Gray
    Write-Host "  - Solar forecast with weather" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Deployment failed!" -ForegroundColor Red
    Write-Host "Check the error messages above" -ForegroundColor Yellow
    exit 1
}
