#!/bin/bash
# Smoke Tests for Staging Environment
# This script runs basic smoke tests against the staging API

set -e

# Configuration
SERVICE_URL="${1:-}"

echo "========================================"
echo "Solar Potential API - Smoke Tests"
echo "========================================"
echo ""

# Get service URL from file if not provided
if [ -z "$SERVICE_URL" ]; then
    if [ -f "staging-url.txt" ]; then
        SERVICE_URL=$(cat staging-url.txt | tr -d '\n\r')
        echo "Using service URL from staging-url.txt"
    else
        echo "ERROR: No service URL provided and staging-url.txt not found"
        echo "Usage: ./run-smoke-tests.sh <service-url>"
        echo "   or: Run deploy-staging.sh first to create staging-url.txt"
        exit 1
    fi
fi

echo "Testing API at: $SERVICE_URL"
echo ""

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run a test
test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local body="${4:-}"
    local expected_status="${5:-200}"
    
    echo "Testing: $name"
    echo "  URL: $url"
    
    if [ -n "$body" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
            -H "Content-Type: application/json" \
            -d "$body" \
            --max-time 30 2>&1) || true
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
            --max-time 30 2>&1) || true
    fi
    
    # Extract status code (last line)
    status_code=$(echo "$response" | tail -n 1)
    # Extract body (all but last line)
    body_response=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "$expected_status" ]; then
        echo "  ✓ PASS - Status: $status_code"
        # Show preview of response
        echo "  Response preview: $(echo "$body_response" | head -c 200)..."
        ((TESTS_PASSED++))
    else
        echo "  ✗ FAIL - Expected status $expected_status, got $status_code"
        ((TESTS_FAILED++))
    fi
    
    echo ""
}

# Test 1: Health Check
echo "Test 1: Health Check Endpoint"
test_endpoint "GET /health" "$SERVICE_URL/health"

# Test 2: Root Endpoint
echo "Test 2: Root Endpoint"
test_endpoint "GET /" "$SERVICE_URL/"

# Test 3: Stats Endpoint
echo "Test 3: Statistics Endpoint"
test_endpoint "GET /stats" "$SERVICE_URL/stats"

# Test 4: Stats Distribution Endpoint
echo "Test 4: Stats Distribution Endpoint"
test_endpoint "GET /stats/distribution" "$SERVICE_URL/stats/distribution"

# Test 5: Buildings BBox Endpoint
echo "Test 5: Buildings BBox Endpoint"
test_endpoint "GET /buildings/bbox" "$SERVICE_URL/buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=5"

# Test 6: Buildings Nearby Endpoint
echo "Test 6: Buildings Nearby Endpoint"
test_endpoint "GET /buildings/nearby" "$SERVICE_URL/buildings/nearby?latitude=13.7563&longitude=100.5018&radius_km=1&limit=5"

# Test 7: Solar Calculate Endpoint
echo "Test 7: Solar Calculate Endpoint"
solar_body='{"latitude":13.7563,"longitude":100.5018,"area_m2":250.0,"confidence":0.95,"tilt":null,"azimuth":180}'
test_endpoint "POST /solar/calculate" "$SERVICE_URL/solar/calculate" "POST" "$solar_body"

# Test 8: Rankings Endpoint
echo "Test 8: Rankings Endpoint"
test_endpoint "GET /rankings" "$SERVICE_URL/rankings?limit=10&scope=country&scope_value=TH"

# Test 9: Polygon Analyze Endpoint
echo "Test 9: Polygon Analyze Endpoint"
polygon_body='{"geometry":{"type":"Polygon","coordinates":[[[100.5,13.7],[100.6,13.7],[100.6,13.8],[100.5,13.8],[100.5,13.7]]]},"min_confidence":0.7,"include_buildings":false}'
test_endpoint "POST /polygon/analyze" "$SERVICE_URL/polygon/analyze" "POST" "$polygon_body"

# Test 10: Methodology Documentation Endpoint
echo "Test 10: Methodology Documentation Endpoint"
test_endpoint "GET /docs/methodology" "$SERVICE_URL/docs/methodology"

# Test 11: OpenAPI Documentation
echo "Test 11: OpenAPI Documentation"
test_endpoint "GET /docs" "$SERVICE_URL/docs"

# Test 12: Weather Forecast Endpoint (may fail if no API key)
echo "Test 12: Weather Forecast Endpoint"
test_endpoint "GET /weather/forecast" "$SERVICE_URL/weather/forecast?latitude=13.7563&longitude=100.5018"

# Summary
echo "========================================"
echo "Smoke Test Results"
echo "========================================"
echo ""
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"
echo ""

# Exit with appropriate code
if [ $TESTS_FAILED -gt 0 ]; then
    echo "Smoke tests FAILED"
    exit 1
else
    echo "All smoke tests PASSED ✓"
    exit 0
fi
