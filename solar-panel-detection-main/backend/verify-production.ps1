# Post-Deployment Verification Script
# Verifies all endpoints are working correctly in production

param(
    [string]$ProjectId = "trim-descent-452802-t2",
    [string]$Region = "asia-southeast1",
    [string]$ServiceName = "solar-weather-api",
    [string]$ServiceUrl = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Production Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get service URL if not provided
if (-not $ServiceUrl) {
    Write-Host "Getting service URL..." -ForegroundColor Yellow
    $ServiceUrl = gcloud run services describe $ServiceName --region $Region --format "value(status.url)" --project=$ProjectId 2>$null
    
    if (-not $ServiceUrl) {
        Write-Host "ERROR: Could not retrieve service URL" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Service URL: $ServiceUrl" -ForegroundColor Cyan
Write-Host ""

# Initialize results
$TestResults = @()
$PassedTests = 0
$FailedTests = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [string]$Body = $null,
        [scriptblock]$Validator
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor Gray
    
    try {
        $StartTime = Get-Date
        
        if ($Method -eq "GET") {
            $Response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 30 -ErrorAction Stop
        } elseif ($Method -eq "POST") {
            $Response = Invoke-RestMethod -Uri $Url -Method Post -Body $Body -ContentType "application/json" -TimeoutSec 30 -ErrorAction Stop
        }
        
        $Duration = ((Get-Date) - $StartTime).TotalMilliseconds
        
        # Run custom validator if provided
        $ValidationResult = $true
        $ValidationMessage = "OK"
        
        if ($Validator) {
            $ValidationResult = & $Validator $Response
            if (-not $ValidationResult) {
                $ValidationMessage = "Validation failed"
            }
        }
        
        if ($ValidationResult) {
            Write-Host "  ✓ PASSED ($([math]::Round($Duration, 0))ms)" -ForegroundColor Green
            $script:PassedTests++
            
            $script:TestResults += @{
                name = $Name
                status = "PASSED"
                duration_ms = [math]::Round($Duration, 0)
                message = $ValidationMessage
            }
        } else {
            Write-Host "  ✗ FAILED: $ValidationMessage" -ForegroundColor Red
            $script:FailedTests++
            
            $script:TestResults += @{
                name = $Name
                status = "FAILED"
                duration_ms = [math]::Round($Duration, 0)
                message = $ValidationMessage
            }
        }
    }
    catch {
        Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $script:FailedTests++
        
        $script:TestResults += @{
            name = $Name
            status = "FAILED"
            duration_ms = 0
            message = $_.Exception.Message
        }
    }
    
    Write-Host ""
}

# Test 1: Health Check
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Health Check Endpoint" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Test-Endpoint -Name "Health Check" -Url "$ServiceUrl/health" -Validator {
    param($Response)
    return $Response.status -eq "healthy" -and $Response.version -eq "2.2.0"
}

# Test 2: Statistics Endpoints
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "2. Statistics Endpoints" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Test-Endpoint -Name "Stats" -Url "$ServiceUrl/stats" -Validator {
    param($Response)
    return $Response.total_buildings -gt 0 -and $Response.dataset_metadata -ne $null
}

Test-Endpoint -Name "Stats Distribution" -Url "$ServiceUrl/stats/distribution" -Validator {
    param($Response)
    return $Response.confidence_buckets -ne $null -and $Response.confidence_std_dev -ne $null
}

# Test 3: Buildings Endpoints
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "3. Buildings Endpoints" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Test-Endpoint -Name "Buildings BBox" -Url "$ServiceUrl/buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=10" -Validator {
    param($Response)
    return $Response.buildings -ne $null -and $Response.total -gt 0
}

Test-Endpoint -Name "Buildings Nearby" -Url "$ServiceUrl/buildings/nearby?latitude=13.7563&longitude=100.5018&radius_km=1&limit=10" -Validator {
    param($Response)
    return $Response.buildings -ne $null
}

# Test 4: Solar Calculation
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "4. Solar Calculation Endpoint" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$SolarBody = @{
    latitude = 13.7563
    longitude = 100.5018
    area_m2 = 250.0
    confidence = 0.95
    azimuth = 180
} | ConvertTo-Json

Test-Endpoint -Name "Solar Calculate" -Url "$ServiceUrl/solar/calculate" -Method "POST" -Body $SolarBody -Validator {
    param($Response)
    return $Response.system_size_kwp -gt 0 -and $Response.calculation_breakdown -ne $null
}

# Test 5: Rankings Endpoint
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "5. Rankings Endpoint" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Test-Endpoint -Name "Rankings" -Url "$ServiceUrl/rankings?scope=country&scope_value=TH&limit=10" -Validator {
    param($Response)
    return $Response.rankings -ne $null -and $Response.rankings.Count -gt 0
}

# Test 6: Polygon Analysis
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "6. Polygon Analysis Endpoint" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$PolygonBody = @{
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

Test-Endpoint -Name "Polygon Analyze" -Url "$ServiceUrl/polygon/analyze" -Method "POST" -Body $PolygonBody -Validator {
    param($Response)
    return $Response.total_buildings -ge 0 -and $Response.aggregated_stats -ne $null
}

# Test 7: Documentation Endpoints
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "7. Documentation Endpoints" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Test-Endpoint -Name "Methodology" -Url "$ServiceUrl/docs/methodology" -Validator {
    param($Response)
    return $Response.version -eq "2.2.0" -and $Response.formulas -ne $null
}

# Test 8: Cache Headers
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "8. Cache Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Testing: Cache Headers" -ForegroundColor Yellow
try {
    $Response = Invoke-WebRequest -Uri "$ServiceUrl/stats" -Method Get -TimeoutSec 30
    
    $HasCacheControl = $Response.Headers.ContainsKey("Cache-Control")
    $HasCacheStatus = $Response.Headers.ContainsKey("X-Cache-Status")
    
    if ($HasCacheControl -and $HasCacheStatus) {
        Write-Host "  ✓ PASSED - Cache headers present" -ForegroundColor Green
        Write-Host "    Cache-Control: $($Response.Headers['Cache-Control'])" -ForegroundColor Gray
        Write-Host "    X-Cache-Status: $($Response.Headers['X-Cache-Status'])" -ForegroundColor Gray
        $script:PassedTests++
        
        $script:TestResults += @{
            name = "Cache Headers"
            status = "PASSED"
            duration_ms = 0
            message = "Cache headers present"
        }
    } else {
        Write-Host "  ✗ FAILED - Missing cache headers" -ForegroundColor Red
        $script:FailedTests++
        
        $script:TestResults += @{
            name = "Cache Headers"
            status = "FAILED"
            duration_ms = 0
            message = "Missing cache headers"
        }
    }
}
catch {
    Write-Host "  ✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $script:FailedTests++
    
    $script:TestResults += @{
        name = "Cache Headers"
        status = "FAILED"
        duration_ms = 0
        message = $_.Exception.Message
    }
}

Write-Host ""

# Test 9: Performance Check
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "9. Performance Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking response times (target: p95 < 600ms)..." -ForegroundColor Yellow
$ResponseTimes = @()

for ($i = 1; $i -le 10; $i++) {
    try {
        $StartTime = Get-Date
        Invoke-RestMethod -Uri "$ServiceUrl/stats" -Method Get -TimeoutSec 30 | Out-Null
        $Duration = ((Get-Date) - $StartTime).TotalMilliseconds
        $ResponseTimes += $Duration
        Write-Host "  Request $i : $([math]::Round($Duration, 0))ms" -ForegroundColor Gray
    }
    catch {
        Write-Host "  Request $i : FAILED" -ForegroundColor Red
    }
}

if ($ResponseTimes.Count -gt 0) {
    $ResponseTimes = $ResponseTimes | Sort-Object
    $P95Index = [math]::Floor($ResponseTimes.Count * 0.95)
    $P95 = $ResponseTimes[$P95Index]
    $Avg = ($ResponseTimes | Measure-Object -Average).Average
    
    Write-Host ""
    Write-Host "  Average: $([math]::Round($Avg, 0))ms" -ForegroundColor Cyan
    Write-Host "  P95: $([math]::Round($P95, 0))ms" -ForegroundColor Cyan
    
    if ($P95 -lt 600) {
        Write-Host "  ✓ PASSED - Performance target met" -ForegroundColor Green
        $script:PassedTests++
        
        $script:TestResults += @{
            name = "Performance Check"
            status = "PASSED"
            duration_ms = [math]::Round($P95, 0)
            message = "P95: $([math]::Round($P95, 0))ms (target: <600ms)"
        }
    } else {
        Write-Host "  ✗ FAILED - Performance target not met" -ForegroundColor Red
        $script:FailedTests++
        
        $script:TestResults += @{
            name = "Performance Check"
            status = "FAILED"
            duration_ms = [math]::Round($P95, 0)
            message = "P95: $([math]::Round($P95, 0))ms exceeds target of 600ms"
        }
    }
}

Write-Host ""

# Test 10: Error Logs Check
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "10. Error Logs Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking for errors in last 10 minutes..." -ForegroundColor Yellow
try {
    $ErrorLogs = gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$ServiceName AND severity>=ERROR AND timestamp>='$((Get-Date).AddMinutes(-10).ToString('yyyy-MM-ddTHH:mm:ssZ'))'" --limit 10 --format json --project=$ProjectId 2>$null | ConvertFrom-Json
    
    if ($ErrorLogs.Count -eq 0) {
        Write-Host "  ✓ PASSED - No errors in last 10 minutes" -ForegroundColor Green
        $script:PassedTests++
        
        $script:TestResults += @{
            name = "Error Logs"
            status = "PASSED"
            duration_ms = 0
            message = "No errors found"
        }
    } else {
        Write-Host "  ⚠ WARNING - Found $($ErrorLogs.Count) errors in last 10 minutes" -ForegroundColor Yellow
        Write-Host "  Review logs: gcloud run services logs tail $ServiceName --region $Region" -ForegroundColor Gray
        
        $script:TestResults += @{
            name = "Error Logs"
            status = "WARNING"
            duration_ms = 0
            message = "Found $($ErrorLogs.Count) errors"
        }
    }
}
catch {
    Write-Host "  ⚠ WARNING - Could not check error logs: $($_.Exception.Message)" -ForegroundColor Yellow
    
    $script:TestResults += @{
        name = "Error Logs"
        status = "WARNING"
        duration_ms = 0
        message = "Could not check logs"
    }
}

Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$TotalTests = $PassedTests + $FailedTests
$SuccessRate = if ($TotalTests -gt 0) { [math]::Round(($PassedTests / $TotalTests) * 100, 1) } else { 0 }

Write-Host "Total Tests: $TotalTests" -ForegroundColor White
Write-Host "Passed: $PassedTests" -ForegroundColor Green
Write-Host "Failed: $FailedTests" -ForegroundColor Red
Write-Host "Success Rate: $SuccessRate%" -ForegroundColor Cyan
Write-Host ""

# Save results
$VerificationReport = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    service_url = $ServiceUrl
    total_tests = $TotalTests
    passed = $PassedTests
    failed = $FailedTests
    success_rate = $SuccessRate
    results = $TestResults
}

$VerificationReport | ConvertTo-Json -Depth 10 | Out-File -FilePath "production-verification-report.json" -Encoding UTF8
Write-Host "Verification report saved to: production-verification-report.json" -ForegroundColor Yellow
Write-Host ""

# Final status
if ($FailedTests -eq 0) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ All Verifications Passed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Production deployment is healthy and working correctly." -ForegroundColor Green
    exit 0
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ Some Verifications Failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please review failed tests and consider rollback if critical." -ForegroundColor Yellow
    Write-Host "Rollback command: .\rollback-production.ps1" -ForegroundColor White
    exit 1
}

