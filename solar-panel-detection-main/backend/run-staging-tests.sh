#!/bin/bash
# Run Full Test Suite on Staging Environment
# This script runs integration tests and load tests against the staging API

set -e

# Configuration
SERVICE_URL="${1:-}"
SKIP_LOAD_TESTS="${SKIP_LOAD_TESTS:-false}"

echo "========================================"
echo "Solar Potential API - Full Test Suite"
echo "========================================"
echo ""

# Get service URL from file if not provided
if [ -z "$SERVICE_URL" ]; then
    if [ -f "staging-url.txt" ]; then
        SERVICE_URL=$(cat staging-url.txt | tr -d '\n\r')
        echo "Using service URL from staging-url.txt"
    else
        echo "ERROR: No service URL provided and staging-url.txt not found"
        echo "Usage: ./run-staging-tests.sh <service-url>"
        exit 1
    fi
fi

echo "Testing API at: $SERVICE_URL"
echo ""

# Set environment variable for tests
export TEST_API_URL="$SERVICE_URL"
echo "Set TEST_API_URL environment variable"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "ERROR: pytest not found. Installing test dependencies..."
    pip install -r requirements.txt
fi

# Navigate to backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Current directory: $(pwd)"
echo ""

# Track test results
INTEGRATION_TEST_RESULT=0
CACHE_TEST_RESULT=0
SECURITY_TEST_RESULT=0
VALIDATION_TEST_RESULT=0
LOAD_TEST_RESULT=0

# Step 1: Run Integration Tests
echo "========================================"
echo "Step 1: Running Integration Tests"
echo "========================================"
echo ""

pytest tests/test_endpoints.py -v --tb=short --color=yes || INTEGRATION_TEST_RESULT=$?

if [ $INTEGRATION_TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✓ Integration tests PASSED"
else
    echo ""
    echo "✗ Integration tests FAILED"
fi

echo ""

# Step 2: Run Cache Tests
echo "========================================"
echo "Step 2: Running Cache Tests"
echo "========================================"
echo ""

pytest tests/test_cache.py -v --tb=short --color=yes || CACHE_TEST_RESULT=$?

if [ $CACHE_TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✓ Cache tests PASSED"
else
    echo ""
    echo "✗ Cache tests FAILED"
fi

echo ""

# Step 3: Run Security Tests
echo "========================================"
echo "Step 3: Running Security Tests"
echo "========================================"
echo ""

pytest tests/test_security.py -v --tb=short --color=yes || SECURITY_TEST_RESULT=$?

if [ $SECURITY_TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✓ Security tests PASSED"
else
    echo ""
    echo "✗ Security tests FAILED"
fi

echo ""

# Step 4: Run Validation Tests
echo "========================================"
echo "Step 4: Running Validation Tests"
echo "========================================"
echo ""

pytest tests/test_validation.py -v --tb=short --color=yes || VALIDATION_TEST_RESULT=$?

if [ $VALIDATION_TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✓ Validation tests PASSED"
else
    echo ""
    echo "✗ Validation tests FAILED"
fi

echo ""

# Step 5: Run Load Tests (optional)
if [ "$SKIP_LOAD_TESTS" != "true" ]; then
    echo "========================================"
    echo "Step 5: Running Load Tests"
    echo "========================================"
    echo ""
    
    # Check if locust is installed
    if ! command -v locust &> /dev/null; then
        echo "WARNING: locust not found. Skipping load tests."
        echo "To install: pip install locust"
        LOAD_TEST_RESULT=0
    else
        echo "Running Locust load tests..."
        echo "This will run for 60 seconds with 10 concurrent users"
        echo ""
        
        # Run locust in headless mode
        locust -f tests/locustfile.py --host="$SERVICE_URL" --users 10 --spawn-rate 2 --run-time 60s --headless --only-summary || LOAD_TEST_RESULT=$?
        
        if [ $LOAD_TEST_RESULT -eq 0 ]; then
            echo ""
            echo "✓ Load tests PASSED"
        else
            echo ""
            echo "✗ Load tests FAILED"
        fi
    fi
    echo ""
else
    echo "Skipping load tests (set SKIP_LOAD_TESTS=false to run)"
    echo ""
fi

# Summary
echo "========================================"
echo "Test Suite Summary"
echo "========================================"
echo ""

TOTAL_TESTS=4
PASSED_TESTS=0

echo -n "Integration Tests: "
if [ $INTEGRATION_TEST_RESULT -eq 0 ]; then
    echo "PASSED ✓"
    ((PASSED_TESTS++))
else
    echo "FAILED ✗"
fi

echo -n "Cache Tests: "
if [ $CACHE_TEST_RESULT -eq 0 ]; then
    echo "PASSED ✓"
    ((PASSED_TESTS++))
else
    echo "FAILED ✗"
fi

echo -n "Security Tests: "
if [ $SECURITY_TEST_RESULT -eq 0 ]; then
    echo "PASSED ✓"
    ((PASSED_TESTS++))
else
    echo "FAILED ✗"
fi

echo -n "Validation Tests: "
if [ $VALIDATION_TEST_RESULT -eq 0 ]; then
    echo "PASSED ✓"
    ((PASSED_TESTS++))
else
    echo "FAILED ✗"
fi

if [ "$SKIP_LOAD_TESTS" != "true" ]; then
    echo -n "Load Tests: "
    if [ $LOAD_TEST_RESULT -eq 0 ]; then
        echo "PASSED ✓"
        ((PASSED_TESTS++))
    else
        echo "FAILED ✗"
    fi
    ((TOTAL_TESTS++))
fi

echo ""
echo "Total: $PASSED_TESTS/$TOTAL_TESTS tests passed"
echo ""

# Overall result
if [ $INTEGRATION_TEST_RESULT -eq 0 ] && \
   [ $CACHE_TEST_RESULT -eq 0 ] && \
   [ $SECURITY_TEST_RESULT -eq 0 ] && \
   [ $VALIDATION_TEST_RESULT -eq 0 ] && \
   ([ "$SKIP_LOAD_TESTS" = "true" ] || [ $LOAD_TEST_RESULT -eq 0 ]); then
    echo "========================================"
    echo "ALL TESTS PASSED ✓"
    echo "========================================"
    echo ""
    echo "Staging environment is ready for production deployment!"
    exit 0
else
    echo "========================================"
    echo "SOME TESTS FAILED ✗"
    echo "========================================"
    echo ""
    echo "Please fix failing tests before deploying to production."
    exit 1
fi
