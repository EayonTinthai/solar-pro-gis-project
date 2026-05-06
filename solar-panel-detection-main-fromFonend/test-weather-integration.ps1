#!/usr/bin/env pwsh
# Test Weather Integration for Solar Panel Detection System

Write-Host "🧪 Testing Weather Integration..." -ForegroundColor Green

# Configuration
$WEATHER_API_URL = "https://solar-weather-api-715107904640.asia-southeast1.run.app"
$TEST_LAT = 13.7563
$TEST_LON = 100.5018  # Bangkok coordinates
$TEST_SYSTEM_KWP = 5.0

# Function to test API endpoint
function Test-ApiEndpoint {
    param($Url, $Description)
    
    Write-Host "Testing $Description..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec 15
        Write-Host "✅ ${Description}: SUCCESS" -ForegroundColor Green
        return $response
    } catch {
        Write-Host "❌ ${Description}: FAILED - $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

Write-Host "🌐 Weather API Base URL: $WEATHER_API_URL" -ForegroundColor Cyan
Write-Host "📍 Test Location: Bangkok ($TEST_LAT, $TEST_LON)" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "🔍 Test 1: API Health Check" -ForegroundColor Yellow
$healthUrl = "$WEATHER_API_URL/health"
$health = Test-ApiEndpoint $healthUrl "Health Check"

if ($health) {
    Write-Host "   Status: $($health.status)" -ForegroundColor White
    Write-Host "   Timestamp: $($health.timestamp)" -ForegroundColor White
    Write-Host ""
}

# Test 2: Weather Forecast
Write-Host "🌤️ Test 2: Weather Forecast" -ForegroundColor Yellow
$weatherUrl = "$WEATHER_API_URL/weather/forecast?lat=$TEST_LAT&lon=$TEST_LON&timezone=Asia/Bangkok"
$weather = Test-ApiEndpoint $weatherUrl "Weather Forecast"

if ($weather) {
    $impact = $weather.impact_summary
    Write-Host "   Impact Level: $($impact.impact_level)" -ForegroundColor White
    Write-Host "   Temperature: $($impact.avg_temperature)°C" -ForegroundColor White
    Write-Host "   Solar Radiation: $($impact.avg_solar_radiation) W/m²" -ForegroundColor White
    Write-Host "   Rain (24h): $($impact.total_rain_24h) mm" -ForegroundColor White
    Write-Host ""
}

# Test 3: Solar Forecast
Write-Host "☀️ Test 3: Solar Generation Forecast" -ForegroundColor Yellow
$solarUrl = "$WEATHER_API_URL/solar/forecast?lat=$TEST_LAT&lon=$TEST_LON&system_kwp=$TEST_SYSTEM_KWP&timezone=Asia/Bangkok"
$solar = Test-ApiEndpoint $solarUrl "Solar Forecast"

if ($solar) {
    Write-Host "   Next 24h Generation: $($solar.next_24h_generation_kwh) kWh" -ForegroundColor White
    Write-Host "   Weather Quality Score: $($solar.weather_quality_score)/100" -ForegroundColor White
    Write-Host "   Hourly Forecasts: $($solar.hourly_forecast.Count) entries" -ForegroundColor White
    Write-Host "   Weekly Outlook: $($solar.weekly_outlook.Count) days" -ForegroundColor White
    Write-Host ""
}

# Test 4: Enhanced Solar Calculation
Write-Host "🔧 Test 4: Enhanced Solar Calculation" -ForegroundColor Yellow
$calcUrl = "$WEATHER_API_URL/solar/calculate"
$calcBody = @{
    latitude = $TEST_LAT
    longitude = $TEST_LON
    area_m2 = 120
    confidence = 0.85
    tilt = $null
    azimuth = 180
} | ConvertTo-Json

try {
    Write-Host "Testing Enhanced Solar Calculation..." -ForegroundColor Cyan
    $calc = Invoke-RestMethod -Uri $calcUrl -Method POST -Body $calcBody -ContentType "application/json" -TimeoutSec 15
    Write-Host "✅ Enhanced Solar Calculation: SUCCESS" -ForegroundColor Green
    Write-Host "   System Size: $($calc.system_size_kwp) kWp" -ForegroundColor White
    Write-Host "   Annual Production: $($calc.annual_production_kwh) kWh" -ForegroundColor White
    Write-Host "   Calculation Method: $($calc.assumptions.calculation_method)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "❌ Enhanced Solar Calculation: FAILED - $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 5: Frontend Integration Check
Write-Host "🎨 Test 5: Frontend Integration" -ForegroundColor Yellow
$frontendUrl = "https://solar-panel-detection-440806.web.app"

try {
    Write-Host "Testing Frontend Accessibility..." -ForegroundColor Cyan
    $frontendResponse = Invoke-WebRequest -Uri $frontendUrl -Method GET -TimeoutSec 10
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "✅ Frontend: ACCESSIBLE" -ForegroundColor Green
        Write-Host "   URL: $frontendUrl" -ForegroundColor White
        
        # Check if weather integration assets are present
        $content = $frontendResponse.Content
        if ($content -match "weather" -or $content -match "WeatherPanel") {
            Write-Host "   Weather Integration: ✅ DETECTED" -ForegroundColor Green
        } else {
            Write-Host "   Weather Integration: ⚠️ NOT DETECTED" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "❌ Frontend: NOT ACCESSIBLE - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Summary
Write-Host "📊 Test Summary" -ForegroundColor Green
Write-Host "===============" -ForegroundColor Green

$testResults = @()
$testResults += if ($health) { "✅ API Health Check" } else { "❌ API Health Check" }
$testResults += if ($weather) { "✅ Weather Forecast" } else { "❌ Weather Forecast" }
$testResults += if ($solar) { "✅ Solar Forecast" } else { "❌ Solar Forecast" }

foreach ($result in $testResults) {
    Write-Host $result -ForegroundColor White
}

Write-Host ""

if ($health -and $weather -and $solar) {
    Write-Host "🎉 All weather integration tests PASSED!" -ForegroundColor Green
    Write-Host "The weather-enhanced solar panel detection system is ready for use." -ForegroundColor White
} else {
    Write-Host "⚠️ Some tests FAILED. Please check the API deployment and configuration." -ForegroundColor Yellow
    Write-Host "Refer to WEATHER_INTEGRATION.md for troubleshooting guidance." -ForegroundColor White
}

Write-Host ""
Write-Host "🔗 Useful URLs:" -ForegroundColor Cyan
Write-Host "   Weather API: $WEATHER_API_URL" -ForegroundColor White
Write-Host "   Frontend: $frontendUrl" -ForegroundColor White
Write-Host "   API Docs: ${WEATHER_API_URL}/docs" -ForegroundColor White