# Quick Start - Staging Deployment

This is a quick reference guide for deploying and testing the Solar Potential API v2.2.0 in staging.

## Prerequisites

- Google Cloud SDK installed and authenticated
- Python 3.11+ with pip
- Access to GCP project: `trim-descent-452802-t2`

## Quick Deploy (3 Steps)

### 1. Deploy to Staging

**Windows:**
```powershell
cd solar-panel-detection-main\backend
.\deploy-staging.ps1
```

**Linux/Mac:**
```bash
cd solar-panel-detection-main/backend
./deploy-staging.sh
```

⏱️ Takes ~5-10 minutes (includes Docker build)

### 2. Run Smoke Tests

**Windows:**
```powershell
.\run-smoke-tests.ps1
```

**Linux/Mac:**
```bash
./run-smoke-tests.sh
```

⏱️ Takes ~2-3 minutes

### 3. Run Full Test Suite

**Windows:**
```powershell
.\run-staging-tests.ps1
```

**Linux/Mac:**
```bash
./run-staging-tests.sh
```

⏱️ Takes ~5-10 minutes

## Expected Results

✅ All tests should pass  
✅ Response times < 600ms (p95)  
✅ No errors in logs  
✅ Cache working correctly  

## If Tests Fail

1. Check logs:
   ```bash
   gcloud run services logs read solar-weather-api-staging --region asia-southeast1 --limit 50
   ```

2. Test manually:
   ```bash
   curl $(cat staging-url.txt)/health
   ```

3. Review troubleshooting guide in `STAGING_DEPLOYMENT_README.md`

## Skip Build (Faster Redeployment)

If you've already built the image and just want to redeploy:

**Windows:**
```powershell
.\deploy-staging.ps1 -SkipBuild
```

**Linux/Mac:**
```bash
SKIP_BUILD=true ./deploy-staging.sh
```

## Skip Load Tests (Faster Testing)

If you want to skip the load tests:

**Windows:**
```powershell
.\run-staging-tests.ps1 -SkipLoadTests
```

**Linux/Mac:**
```bash
SKIP_LOAD_TESTS=true ./run-staging-tests.sh
```

## Monitor Staging

```bash
# Stream logs
gcloud run services logs tail solar-weather-api-staging --region asia-southeast1

# Get service URL
cat staging-url.txt

# Test health
curl $(cat staging-url.txt)/health
```

## Next Steps

After successful staging deployment:

1. ✅ Monitor for 24 hours
2. ✅ Review performance metrics
3. ✅ Prepare for production deployment
4. ✅ Follow `DEPLOYMENT_GUIDE.md` for production

## Full Documentation

- **Detailed Guide**: `STAGING_DEPLOYMENT_README.md`
- **Production Deployment**: `DEPLOYMENT_GUIDE.md`
- **Deployment Checklist**: `DEPLOYMENT_CHECKLIST.md`

---

**Quick Reference** | **API Version**: 2.2.0 | **Last Updated**: April 19, 2026
