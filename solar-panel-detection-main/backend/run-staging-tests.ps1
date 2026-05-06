# Run Full Test Suite on Staging Environment
# This script runs integration tests and load tests against the staging API

param(
    [string]$ServiceUrl = "",
    [switch]$SkipLoadTests = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Solar Potential API - Full Test Suite" -ForegroundColor Cyan
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
        Write-Host "Usage: .\run-staging-tests.ps1 -ServiceUrl <url>" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Testing API at: $ServiceUrl" -ForegroundColor Cyan
Write-Host ""

# Set environment variable for tests
$env:TEST_API_URL = $ServiceUrl
Write-Host "Set TEST_API_URL environment variable" -ForegroundColor Yellow
Write-Host ""

# Check if pytest is installed
$pytestInstalled = $null -ne (Get-Command pytest -ErrorAction SilentlyContinue)
if (-not $pytestInstalled) {
    Write-Host "ERROR: pytest not found. Installing test dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Navigate to backend directory
$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $BackendDir

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# Step 1: Run Integration Tests
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Running Integration Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Running pytest with integration tests..." -ForegroundColor Yellow
Write-Host ""

# Run pytest with verbose output
pytest tests/test_endpoints.py -v --tb=short --color=yes

$integrationTestResult = $LASTEXITCODE

if ($integrationTestResult -eq 0) {
    Write-Host ""
    Write-Host "✓ Integration tests PASSED" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Integration tests FAILED" -ForegroundColor Red
}

Write-Host ""

# Step 2: Run Cache Tests
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Running Cache Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

pytest tests/test_cache.py -v --tb=short --color=yes

$cacheTestResult = $LASTEXITCODE

if ($cacheTestResult -eq 0) {
    Write-Host ""
    Write-Host "✓ Cache tests PASSED" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Cache tests FAILED" -ForegroundColor Red
}

Write-Host ""

# Step 3: Run Security Tests
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 3: Running Security Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

pytest tests/test_security.py -v --tb=short --color=yes

$securityTestResult = $LASTEXITCODE

if ($securityTestResult -eq 0) {
    Write-Host ""
    Write-Host "✓ Security tests PASSED" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Security tests FAILED" -ForegroundColor Red
}

Write-Host ""

# Step 4: Run Validation Tests
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 4: Running Validation Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

pytest tests/test_validation.py -v --tb=short --color=yes

$validationTestResult = $LASTEXITCODE

if ($validationTestResult -eq 0) {
    Write-Host ""
    Write-Host "✓ Validation tests PASSED" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Validation tests FAILED" -ForegroundColor Red
}

Write-Host ""

# Step 5: Run Load Tests (optional)
$loadTestResult = 0
if (-not $SkipLoadTests) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Step 5: Running Load Tests" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Check if locust is installed
    $locustInstalled = $null -ne (Get-Command locust -ErrorAction SilentlyContinue)
    if (-not $locustInstalled) {
        Write-Host "WARNING: locust not found. Skipping load tests." -ForegroundColor Yellow
        Write-Host "To install: pip install locust" -ForegroundColor Yellow
        $loadTestResult = 0
    } else {
        Write-Host "Running Locust load tests..." -ForegroundColor Yellow
        Write-Host "This will run for 60 seconds with 10 concurrent users" -ForegroundColor Yellow
        Write-Host ""
        
        # Run locust in headless mode
        locust -f tests/locustfile.py --host=$ServiceUrl --users 10 --spawn-rate 2 --run-time 60s --headless --only-summary
        
        $loadTestResult = $LASTEXITCODE
        
        if ($loadTestResult -eq 0) {
            Write-Host ""
            Write-Host "✓ Load tests PASSED" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "✗ Load tests FAILED" -ForegroundColor Red
        }
    }
    Write-Host ""
} else {
    Write-Host "Skipping load tests (use -SkipLoadTests:$false to run)" -ForegroundColor Yellow
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Suite Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$totalTests = 4
$passedTests = 0

Write-Host "Integration Tests: " -NoNewline
if ($integrationTestResult -eq 0) {
    Write-Host "PASSED ✓" -ForegroundColor Green
    $passedTests++
} else {
    Write-Host "FAILED ✗" -ForegroundColor Red
}

Write-Host "Cache Tests: " -NoNewline
if ($cacheTestResult -eq 0) {
    Write-Host "PASSED ✓" -ForegroundColor Green
    $passedTests++
} else {
    Write-Host "FAILED ✗" -ForegroundColor Red
}

Write-Host "Security Tests: " -NoNewline
if ($securityTestResult -eq 0) {
    Write-Host "PASSED ✓" -ForegroundColor Green
    $passedTests++
} else {
    Write-Host "FAILED ✗" -ForegroundColor Red
}

Write-Host "Validation Tests: " -NoNewline
if ($validationTestResult -eq 0) {
    Write-Host "PASSED ✓" -ForegroundColor Green
    $passedTests++
} else {
    Write-Host "FAILED ✗" -ForegroundColor Red
}

if (-not $SkipLoadTests) {
    Write-Host "Load Tests: " -NoNewline
    if ($loadTestResult -eq 0) {
        Write-Host "PASSED ✓" -ForegroundColor Green
        $passedTests++
    } else {
        Write-Host "FAILED ✗" -ForegroundColor Red
    }
    $totalTests++
}

Write-Host ""
Write-Host "Total: $passedTests/$totalTests tests passed" -ForegroundColor White
Write-Host ""

# Overall result
$allTestsPassed = ($integrationTestResult -eq 0) -and 
                  ($cacheTestResult -eq 0) -and 
                  ($securityTestResult -eq 0) -and 
                  ($validationTestResult -eq 0) -and
                  (($SkipLoadTests) -or ($loadTestResult -eq 0))

if ($allTestsPassed) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "ALL TESTS PASSED ✓" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Staging environment is ready for production deployment!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "SOME TESTS FAILED ✗" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix failing tests before deploying to production." -ForegroundColor Red
    exit 1
}
