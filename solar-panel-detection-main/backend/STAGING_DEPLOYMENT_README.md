# Staging Deployment Guide

This guide covers deploying and testing the Solar Potential API v2.2.0 in a staging environment before production deployment.

## Overview

The staging deployment process consists of three main steps:

1. **Deploy to Staging** - Build and deploy the API to Cloud Run staging
2. **Run Smoke Tests** - Quick validation of all endpoints
3. **Run Full Test Suite** - Comprehensive integration and load tests

## Prerequisites

### Required Tools

- **Google Cloud SDK** (`gcloud` CLI)
- **Docker** (for local testing, optional)
- **Python 3.11+** with pip
- **PowerShell** (Windows) or **Bash** (Linux/Mac)

### Required Access

- Access to GCP project: `trim-descent-452802-t2`
- Permissions to deploy to Cloud Run
- Permissions to access BigQuery dataset

### Environment Setup

1. Install Google Cloud SDK:
   ```bash
   # Follow instructions at: https://cloud.google.com/sdk/docs/install
   ```

2. Authenticate with GCP:
   ```bash
   gcloud auth login
   gcloud config set project trim-descent-452802-t2
   ```

3. Install Python dependencies (for tests):
   ```bash
   cd solar-panel-detection-main/backend
   pip install -r requirements.txt
   ```

## Deployment Scripts

### Available Scripts

| Script | Platform | Purpose |
|--------|----------|---------|
| `deploy-staging.ps1` | Windows | Deploy to staging environment |
| `deploy-staging.sh` | Linux/Mac | Deploy to staging environment |
| `run-smoke-tests.ps1` | Windows | Run quick smoke tests |
| `run-smoke-tests.sh` | Linux/Mac | Run quick smoke tests |
| `run-staging-tests.ps1` | Windows | Run full test suite |
| `run-staging-tests.sh` | Linux/Mac | Run full test suite |

## Step-by-Step Deployment

### Step 1: Deploy to Staging

#### Windows (PowerShell)

```powershell
cd solar-panel-detection-main\backend
.\deploy-staging.ps1
```

#### Linux/Mac (Bash)

```bash
cd solar-panel-detection-main/backend
./deploy-staging.sh
```

#### What This Does

1. Sets GCP project to `trim-descent-452802-t2`
2. Builds Docker image using Cloud Build
3. Pushes image to Container Registry
4. Deploys to Cloud Run staging service
5. Retrieves and saves service URL to `staging-url.txt`

#### Configuration

The staging deployment uses these settings:

- **Service Name**: `solar-weather-api-staging`
- **Region**: `asia-southeast1`
- **Memory**: 2Gi
- **CPU**: 2 cores
- **Min Instances**: 0 (scales to zero)
- **Max Instances**: 5
- **Timeout**: 60 seconds

#### Skip Build Option

To deploy without rebuilding (uses existing image):

**Windows:**
```powershell
.\deploy-staging.ps1 -SkipBuild
```

**Linux/Mac:**
```bash
SKIP_BUILD=true ./deploy-staging.sh
```

### Step 2: Run Smoke Tests

After deployment completes, run smoke tests to verify basic functionality.

#### Windows (PowerShell)

```powershell
.\run-smoke-tests.ps1
```

#### Linux/Mac (Bash)

```bash
./run-smoke-tests.sh
```

#### What This Tests

The smoke tests verify these endpoints:

1. **GET /health** - Health check
2. **GET /** - Root endpoint
3. **GET /stats** - Statistics
4. **GET /stats/distribution** - Distribution stats
5. **GET /buildings/bbox** - Building queries
6. **GET /buildings/nearby** - Nearby buildings
7. **POST /solar/calculate** - Solar calculations
8. **GET /rankings** - Site rankings
9. **POST /polygon/analyze** - Polygon analysis
10. **GET /docs/methodology** - Methodology docs
11. **GET /docs** - OpenAPI docs
12. **GET /weather/forecast** - Weather forecast

#### Expected Results

- All tests should return HTTP 200
- Average response time should be < 600ms
- No errors in responses

#### Manual URL Testing

You can also test manually using the saved URL:

```bash
# Get the staging URL
cat staging-url.txt

# Test health endpoint
curl $(cat staging-url.txt)/health

# Test stats endpoint
curl $(cat staging-url.txt)/stats
```

### Step 3: Run Full Test Suite

After smoke tests pass, run the comprehensive test suite.

#### Windows (PowerShell)

```powershell
.\run-staging-tests.ps1
```

#### Linux/Mac (Bash)

```bash
./run-staging-tests.sh
```

#### What This Tests

The full test suite includes:

1. **Integration Tests** (`test_endpoints.py`)
   - All API endpoints
   - Request/response validation
   - Error handling

2. **Cache Tests** (`test_cache.py`)
   - Cache functionality
   - TTL behavior
   - Cache headers

3. **Security Tests** (`test_security.py`)
   - API key authentication
   - Rate limiting
   - CORS configuration

4. **Validation Tests** (`test_validation.py`)
   - Input validation
   - Parameter ranges
   - Error responses

5. **Load Tests** (`locustfile.py`) - Optional
   - 10 concurrent users
   - 60 second duration
   - Performance metrics

#### Skip Load Tests

Load tests can be skipped for faster testing:

**Windows:**
```powershell
.\run-staging-tests.ps1 -SkipLoadTests
```

**Linux/Mac:**
```bash
SKIP_LOAD_TESTS=true ./run-staging-tests.sh
```

#### Expected Results

- All test suites should pass
- No critical errors
- Performance targets met:
  - p95 response time < 600ms
  - p99 response time < 1000ms
  - Cache hit rate > 60%

## Monitoring Staging Deployment

### View Logs

```bash
# Stream logs in real-time
gcloud run services logs tail solar-weather-api-staging --region asia-southeast1

# View recent logs
gcloud run services logs read solar-weather-api-staging --region asia-southeast1 --limit 100
```

### View Metrics

```bash
# Get service details
gcloud run services describe solar-weather-api-staging --region asia-southeast1

# Open in Cloud Console
gcloud run services describe solar-weather-api-staging --region asia-southeast1 --format="value(status.url)"
```

Then navigate to: Cloud Console → Cloud Run → solar-weather-api-staging → Metrics

### Check Service Status

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe solar-weather-api-staging --region asia-southeast1 --format="value(status.url)")

# Test health endpoint
curl $SERVICE_URL/health

# Check response headers
curl -I $SERVICE_URL/stats
```

## Troubleshooting

### Build Fails

**Issue**: Cloud Build fails with error

**Solutions**:
1. Check Docker syntax in `Dockerfile.bigquery`
2. Verify all files exist (api_bigquery.py, models/, services/, utils/)
3. Check Cloud Build logs:
   ```bash
   gcloud builds list --limit 5
   gcloud builds log <BUILD_ID>
   ```

### Deployment Fails

**Issue**: Cloud Run deployment fails

**Solutions**:
1. Check environment variables are set correctly
2. Verify service account has required permissions
3. Check Cloud Run logs for startup errors
4. Verify BigQuery dataset and tables exist

### Smoke Tests Fail

**Issue**: Some endpoints return errors

**Common Causes**:
1. **Missing environment variables** - Check Cloud Run configuration
2. **BigQuery connection issues** - Verify GCP_PROJECT, BIGQUERY_DATASET, BIGQUERY_TABLE
3. **Weather API not configured** - WXTECH_API_KEY may be missing (optional)
4. **Rankings not calculated** - Run `calculate_rankings.py` first

**Debug Steps**:
```bash
# Check service logs
gcloud run services logs read solar-weather-api-staging --region asia-southeast1 --limit 50

# Test specific endpoint
curl -v $(cat staging-url.txt)/health

# Check environment variables
gcloud run services describe solar-weather-api-staging --region asia-southeast1 --format="value(spec.template.spec.containers[0].env)"
```

### Integration Tests Fail

**Issue**: pytest tests fail

**Solutions**:
1. Verify TEST_API_URL environment variable is set
2. Check API is accessible from test machine
3. Review test output for specific failures
4. Check if BigQuery tables exist and have data

### Load Tests Fail

**Issue**: Locust load tests show high error rates or slow responses

**Solutions**:
1. Increase Cloud Run instances:
   ```bash
   gcloud run services update solar-weather-api-staging --min-instances 1 --max-instances 10
   ```
2. Check BigQuery query performance
3. Verify cache is working (check X-Cache-Status headers)
4. Review Cloud Run metrics for bottlenecks

### Service Won't Start

**Issue**: Service deploys but won't start (503 errors)

**Solutions**:
1. Check startup logs:
   ```bash
   gcloud run services logs read solar-weather-api-staging --region asia-southeast1 --limit 50
   ```
2. Verify Python dependencies are installed correctly
3. Check for import errors or missing modules
4. Verify BigQuery connection works

## Performance Validation

### Response Time Targets

| Endpoint | Target (p95) | Target (p99) |
|----------|--------------|--------------|
| /health | < 100ms | < 200ms |
| /stats | < 400ms | < 600ms |
| /buildings/bbox | < 600ms | < 1000ms |
| /solar/calculate | < 600ms | < 1000ms |
| /rankings | < 500ms | < 800ms |

### Cache Effectiveness

Check cache headers in responses:

```bash
# Test cache hit
curl -I $(cat staging-url.txt)/stats

# Look for these headers:
# X-Cache-Status: HIT or MISS
# Cache-Control: public, max-age=86400
```

Expected cache hit rate: > 60% after warm-up

### Load Test Metrics

When running load tests, monitor:

- **Request rate**: Should handle 10+ req/s
- **Error rate**: Should be < 1%
- **Response time**: p95 < 600ms, p99 < 1000ms
- **Concurrent users**: Should handle 10+ concurrent users

## Rollback Procedure

If issues are found in staging, rollback to previous version:

```bash
# List revisions
gcloud run revisions list --service solar-weather-api-staging --region asia-southeast1

# Rollback to previous revision
gcloud run services update-traffic solar-weather-api-staging \
  --region asia-southeast1 \
  --to-revisions=PREVIOUS_REVISION=100
```

## Next Steps

After successful staging deployment and testing:

1. **Review Test Results** - Ensure all tests passed
2. **Check Performance Metrics** - Verify targets met
3. **Monitor for 24 Hours** - Watch for any issues
4. **Prepare Production Deployment** - Follow production deployment guide
5. **Update Documentation** - Document any issues or changes

## Production Deployment

Once staging is validated, proceed to production deployment:

1. Review `DEPLOYMENT_CHECKLIST.md`
2. Follow `DEPLOYMENT_GUIDE.md` for production
3. Use traffic splitting for gradual rollout
4. Monitor production metrics closely

## Support

For issues or questions:

- **Documentation**: `DEPLOYMENT_GUIDE.md`, `DEPLOYMENT_CHECKLIST.md`
- **Logs**: `gcloud run services logs read solar-weather-api-staging`
- **GitHub Issues**: https://github.com/EayonTinthai/gis-solar-potential-cpe/issues

---

**Document Version**: 1.0  
**Created**: April 19, 2026  
**API Version**: 2.2.0  
**Status**: Ready for Use
