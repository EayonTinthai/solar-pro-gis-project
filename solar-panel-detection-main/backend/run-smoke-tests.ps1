# Smoke Tests for Staging Environment
# This script runs basic smoke tests against the staging API

param(
    [string]$ServiceUrl = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Solar Potential API - Smoke Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get service URL from file if not provided
if ([string]::IsNullOrEmpty($ServiceUrl)) {
    if (Test-Path "staging-url.txt") {
        $ServiceUrl = Get-Content "staging-url.txt" -Raw
        $ServiceUrl = $ServiceUrl.Trim()
        Write-Host "Using service URL from staging-url.txt" -ForegroundColor Yellow
    } else {
        Write-Host "ERROR: No service URL provided and staging-url.txt not found" -ForegroundColor Red
        Write-Host "Usage: .\run-smoke-tests.ps1 -ServiceUrl <url>" -ForegroundColor Yellow
        Write-Host "   or: Run deploy-staging.ps1 first to create staging-url.txt" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Testing API at: $ServiceUrl" -ForegroundColor Cyan
Write-Host ""

# Track test results
$TestsPassed = 0
$TestsFailed = 0
$TestResults = @()

# Helper function to run a test
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [string]$Body = $null,
        [hashtable]$Headers = @{},
        [int]$ExpectedStatus = 200
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            UseBasicParsing = $true
            TimeoutSec = 30
        }
        
        if ($Body) {
            $params.Body = $Body
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-WebRequest @params
        
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "  ✓ PASS - Status: $($response.StatusCode)" -ForegroundColor Green
            
            # Try to parse JSON response
            try {
                $json = $response.Content | ConvertFrom-Json
                Write-Host "  Response preview: $($json | ConvertTo-Json -Depth 2 -Compress | Select-Object -First 200)..." -ForegroundColor Gray
            } catch {
                Write-Host "  Response length: $($response.Content.Length) bytes" -ForegroundColor Gray
            }
            
            $script:TestsPassed++
            $script:TestResults += @{
                Name = $Name
                Status = "PASS"
                StatusCode = $response.StatusCode
                ResponseTime = $response.Headers["X-Response-Time"]
            }
            return $true
        } else {
            Write-Host "  ✗ FAIL - Expected status $ExpectedStatus, got $($response.StatusCode)" -ForegroundColor Red
            $script:TestsFailed++
            $script:TestResults += @{
                Name = $Name
                Status = "FAIL"
                StatusCode = $response.StatusCode
                Error = "Unexpected status code"
            }
            return $false
        }
    } catch {
        Write-Host "  ✗ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:TestsFailed++
        $script:TestResults += @{
            Name = $Name
            Status = "FAIL"
            Error = $_.Exception.Message
        }
        return $false
    }
    
    Write-Host ""
}

# Test 1: Health Check
Write-Host "Test 1: Health Check Endpoint" -ForegroundColor Cyan
Test-Endpoint -Name "GET /health" -Url "$ServiceUrl/health"
Write-Host ""

# Test 2: Root Endpoint
Write-Host "Test 2: Root Endpoint" -ForegroundColor Cyan
Test-Endpoint -Name "GET /" -Url "$ServiceUrl/"
Write-Host ""

# Test 3: Stats Endpoint
Write-Host "Test 3: Statistics Endpoint" -ForegroundColor Cyan
Test-Endpoint -Name "GET /stats" -Url "$ServiceUrl/stats"
Write-Host ""

# Test 4: Stats Distribution Endpoint
Write-Host "Test 4: Stats Distribution Endpoint" -ForegroundColor Cyan
Test-Endpoint -Name "GET /stats/distribution" -Url "$ServiceUrl/stats/distribution"
Write-Host ""

# Test 5: Buildings BBox Endpoint
Write-Host "Test 5: Buildings BBox Endpoint" -ForegroundColor Cyan
$bboxUrl = "$ServiceUrl/buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=5"
Test-Endpoint -Name "GET /buildings/bbox" -Url $bboxUrl
Write-Host ""

# Test 6: Buildings Nearby Endpoint
Write-Host "Test 6: Buildings Nearby Endpoint" -ForegroundColor Cyan
$nearbyUrl = "$ServiceUrl/buildings/nearby?latitude=13.7563&longitude=100.5018&radius_km=1&limit=5"
Test-Endpoint -Name "GET /buildings/nearby" -Url $nearbyUrl
Write-Host ""

# Test 7: Solar Calculate Endpoint
Write-Host "Test 7: Solar Calculate Endpoint" -ForegroundColor Cyan
$solarBody = @{
    latitude = 13.7563
    longitude = 100.5018
    area_m2 = 250.0
    confidence = 0.95
    tilt = $null
    azimuth = 180
} | ConvertTo-Json

Test-Endpoint -Name "POST /solar/calculate" -Url "$ServiceUrl/solar/calculate" -Method "POST" -Body $solarBody
Write-Host ""

# Test 8: Rankings Endpoint
Write-Host "Test 8: Rankings Endpoint" -ForegroundColor Cyan
$rankingsUrl = "$ServiceUrl/rankings?limit=10&scope=country&scope_value=TH"
Test-Endpoint -Name "GET /rankings" -Url $rankingsUrl
Write-Host ""

# Test 9: Polygon Analyze Endpoint
Write-Host "Test 9: Polygon Analyze Endpoint" -ForegroundColor Cyan
$polygonBody = @{
    geometry = @{
        type = "Polygon"
        coordinates = @(@(
            @(100.5, 13.7),
            @(100.6, 13.7),
            @(100.6, 13.8),
            @(100.5, 13.8),
            @(100.5, 13.7)
        ))
    }
    min_confidence = 0.7
    include_buildings = $false
} | ConvertTo-Json -Depth 10

Test-Endpoint -Name "POST /polygon/analyze" -Url "$ServiceUrl/polygon/analyze" -Method "POST" -Body $polygonBody
Write-Host ""

# Test 10: Methodology Documentation Endpoint
Write-Host "Test 10: Methodology Documentation Endpoint" -ForegroundColor Cyan
Test-Endpoint -Name "GET /docs/methodology" -Url "$ServiceUrl/docs/methodology"
Write-Host ""

# Test 11: OpenAPI Documentation
Write-Host "Test 11: OpenAPI Documentation" -ForegroundColor Cyan
Test-Endpoint -Name "GET /docs" -Url "$ServiceUrl/docs"
Write-Host ""

# Test 12: Weather Forecast Endpoint (may fail if no API key)
Write-Host "Test 12: Weather Forecast Endpoint" -ForegroundColor Cyan
$weatherUrl = "$ServiceUrl/weather/forecast?latitude=13.7563&longitude=100.5018"
Test-Endpoint -Name "GET /weather/forecast" -Url $weatherUrl
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Smoke Test Results" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total Tests: $($TestsPassed + $TestsFailed)" -ForegroundColor White
Write-Host "Passed: $TestsPassed" -ForegroundColor Green
Write-Host "Failed: $TestsFailed" -ForegroundColor $(if ($TestsFailed -gt 0) { "Red" } else { "Green" })
Write-Host ""

# Show failed tests
if ($TestsFailed -gt 0) {
    Write-Host "Failed Tests:" -ForegroundColor Red
    foreach ($result in $TestResults) {
        if ($result.Status -eq "FAIL") {
            Write-Host "  - $($result.Name): $($result.Error)" -ForegroundColor Red
        }
    }
    Write-Host ""
}

# Performance check
Write-Host "Performance Check:" -ForegroundColor Yellow
$responseTimes = $TestResults | Where-Object { $_.ResponseTime } | ForEach-Object { 
    [double]($_.ResponseTime -replace 'ms', '')
}

if ($responseTimes.Count -gt 0) {
    $avgResponseTime = ($responseTimes | Measure-Object -Average).Average
    Write-Host "  Average Response Time: $([math]::Round($avgResponseTime, 2))ms" -ForegroundColor White
    
    if ($avgResponseTime -lt 600) {
        Write-Host "  ✓ Performance target met (< 600ms)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Performance target not met (>= 600ms)" -ForegroundColor Yellow
    }
}
Write-Host ""

# Exit with appropriate code
if ($TestsFailed -gt 0) {
    Write-Host "Smoke tests FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "All smoke tests PASSED ✓" -ForegroundColor Green
    exit 0
}
