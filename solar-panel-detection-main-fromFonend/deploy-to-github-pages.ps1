#!/usr/bin/env pwsh
# Deploy to GitHub Pages

Write-Host "🚀 Deploying to GitHub Pages..." -ForegroundColor Green

# Navigate to frontend directory
Set-Location frontend

try {
    # Build the project
    Write-Host "🔨 Building project..." -ForegroundColor Yellow
    npm run build

    # Install gh-pages if not exists
    Write-Host "📦 Installing gh-pages..." -ForegroundColor Yellow
    npm install --save-dev gh-pages

    # Deploy to GitHub Pages
    Write-Host "🌐 Deploying to GitHub Pages..." -ForegroundColor Yellow
    npx gh-pages -d dist

    Write-Host "✅ Deployed successfully!" -ForegroundColor Green
    Write-Host "🌐 URL: https://teera235.github.io/solar-panel-detection/" -ForegroundColor Cyan

} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    Set-Location ..
}

Write-Host "🎉 GitHub Pages deployment complete!" -ForegroundColor Green