# Deployment Scripts Reference

Quick reference guide for all deployment scripts in the Solar Potential API project.

## Scripts Overview

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `deploy-staging.ps1` | Deploy to staging environment | Testing before production |
| `deploy-production.ps1` | Deploy to production with traffic splitting | Production deployments |
| `rollout-production.ps1` | Increase traffic to new version | After monitoring shows stability |
| `rollback-production.ps1` | Revert to previous version | When issues are detected |
| `verify-production.ps1` | Verify all endpoints working | After any deployment |
| `monitor-production.ps1` | Monitor logs and metrics | Continuous monitoring (auto-generated) |

## Quick Start

### Staging Deployment

```powershell
# Deploy to staging
.\deploy-staging.ps1

# Run smoke tests
.\run-smoke-tests.ps1

# Run full test suite
.\run-staging-tests.ps1
```

### Production Deployment (Safe Rollout)

```powershell
# Step 1: Deploy with 10% traffic
.\deploy-production.ps1 -InitialTrafficPercent 10

# Step 2: Monitor for 5-10 minutes
.\verify-production.ps1

# Step 3: Increase to 50% if stable
.\rollout-production.ps1 -Stage 50

# Step 4: Monitor for 1 hour
.\verify-production.ps1

# Step 5: Complete rollout to 100%
.\rollout-production.ps1 -Stage 100

# Step 6: Final verification
.\verify-production.ps1
```

### Emergency Rollback

```powershell
# Rollback to previous version immediately
.\rollback-production.ps1

# Verify rollback successful
.\verify-production.ps1
```

## Script Details

### deploy-staging.ps1

Deploys to staging environment for testing.

**Parameters:**
- `-ProjectId` - GCP project ID (default: trim-descent-452802-t2)
- `-Region` - Cloud Run region (default: asia-southeast1)
- `-ServiceName` - Service name (default: solar-weather-api-staging)
- `-SkipBuild` - Skip Docker build, use existing image

**Example:**
```powershell
# Standard deployment
.\deploy-staging.ps1

# Skip build (use existing image)
.\deploy-staging.ps1 -SkipBuild

# Custom service name
.\deploy-staging.ps1 -ServiceName "my-staging-service"
```

**Output:**
- Builds and deploys to Cloud Run
- Saves service URL to `staging-url.txt`
- Provides next steps for testing

---

### deploy-production.ps1

Deploys new version to production with traffic splitting.

**Parameters:**
- `-ProjectId` - GCP project ID (default: trim-descent-452802-t2)
- `-Region` - Cloud Run region (default: asia-southeast1)
- `-ServiceName` - Service name (default: solar-weather-api)
- `-ImageTag` - Docker image tag (default: latest)
- `-SkipBuild` - Skip Docker build
- `-AutoRollout` - Skip confirmation prompt
- `-InitialTrafficPercent` - Initial traffic % (default: 10)
- `-MonitoringDelayMinutes` - Monitoring period (default: 5)

**Example:**
```powershell
# Standard deployment (10% traffic)
.\deploy-production.ps1

# Deploy with 20% initial traffic
.\deploy-production.ps1 -InitialTrafficPercent 20

# Skip build, use existing image
.\deploy-production.ps1 -SkipBuild -ImageTag "v2.2.0"

# Automated deployment (no prompts)
.\deploy-production.ps1 -AutoRollout
```

**Output:**
- Deploys new revision with 0% traffic
- Splits traffic to initial percentage
- Saves deployment info to `production-deployment-info.json`
- Creates `monitor-production.ps1` script

---

### rollout-production.ps1

Increases traffic to new version in stages.

**Parameters:**
- `-Stage` - Traffic percentage (50 or 100) **[Required]**
- `-ProjectId` - GCP project ID (default: trim-descent-452802-t2)
- `-Region` - Cloud Run region (default: asia-southeast1)
- `-ServiceName` - Service name (default: solar-weather-api)
- `-Force` - Skip confirmation prompt

**Example:**
```powershell
# Increase to 50%
.\rollout-production.ps1 -Stage 50

# Complete rollout to 100%
.\rollout-production.ps1 -Stage 100

# Force rollout without confirmation
.\rollout-production.ps1 -Stage 100 -Force
```

**Output:**
- Updates traffic split
- Updates `production-deployment-info.json`
- Provides monitoring instructions

---

### rollback-production.ps1

Reverts traffic to previous revision.

**Parameters:**
- `-ProjectId` - GCP project ID (default: trim-descent-452802-t2)
- `-Region` - Cloud Run region (default: asia-southeast1)
- `-ServiceName` - Service name (default: solar-weather-api)
- `-Force` - Skip confirmation prompt

**Example:**
```powershell
# Standard rollback (with confirmation)
.\rollback-production.ps1

# Force rollback without confirmation
.\rollback-production.ps1 -Force
```

**Output:**
- Routes 100% traffic to previous revision
- Saves rollback info to `production-rollback-info.json`
- Provides next steps for investigation

---

### verify-production.ps1

Runs comprehensive verification tests on production.

**Parameters:**
- `-ProjectId` - GCP project ID (default: trim-descent-452802-t2)
- `-Region` - Cloud Run region (default: asia-southeast1)
- `-ServiceName` - Service name (default: solar-weather-api)
- `-ServiceUrl` - Service URL (auto-detected if not provided)

**Example:**
```powershell
# Standard verification
.\verify-production.ps1

# Verify specific URL
.\verify-production.ps1 -ServiceUrl "https://solar-weather-api-abc123.run.app"

# Verify staging
.\verify-production.ps1 -ServiceName "solar-weather-api-staging"
```

**Tests Performed:**
1. Health check endpoint
2. Statistics endpoints
3. Buildings endpoints
4. Solar calculation
5. Rankings endpoint
6. Polygon analysis
7. Documentation endpoint
8. Cache headers
9. Performance check (p95 < 600ms)
10. Error logs check

**Output:**
- Test results for each endpoint
- Success/failure summary
- Saves report to `production-verification-report.json`
- Exit code 0 if all tests pass, 1 if any fail

---

## Common Workflows

### First-Time Production Deployment

```powershell
# 1. Test in staging first
.\deploy-staging.ps1
.\run-staging-tests.ps1

# 2. Deploy to production with 10% traffic
.\deploy-production.ps1

# 3. Monitor for 10 minutes
Start-Sleep -Seconds 600
.\verify-production.ps1

# 4. If stable, increase to 50%
.\rollout-production.ps1 -Stage 50

# 5. Monitor for 1 hour
Start-Sleep -Seconds 3600
.\verify-production.ps1

# 6. Complete rollout
.\rollout-production.ps1 -Stage 100

# 7. Final verification
.\verify-production.ps1
```

### Hotfix Deployment

```powershell
# 1. Deploy with higher initial traffic (already tested in staging)
.\deploy-production.ps1 -InitialTrafficPercent 50

# 2. Quick monitoring (5 minutes)
Start-Sleep -Seconds 300
.\verify-production.ps1

# 3. Complete rollout if stable
.\rollout-production.ps1 -Stage 100 -Force
```

### Rollback and Redeploy

```powershell
# 1. Rollback due to issues
.\rollback-production.ps1

# 2. Verify rollback successful
.\verify-production.ps1

# 3. Fix issues in code

# 4. Test in staging
.\deploy-staging.ps1
.\run-staging-tests.ps1

# 5. Redeploy to production
.\deploy-production.ps1
```

## Monitoring Commands

```powershell
# Stream logs
gcloud run services logs tail solar-weather-api --region asia-southeast1

# View error logs only
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=solar-weather-api AND severity>=ERROR" --limit 50

# Check current traffic split
gcloud run services describe solar-weather-api --region asia-southeast1 --format="value(status.traffic)"

# List all revisions
gcloud run revisions list --service solar-weather-api --region asia-southeast1

# View metrics dashboard
# https://console.cloud.google.com/run/detail/asia-southeast1/solar-weather-api/metrics
```

## Files Generated

| File | Description | When Created |
|------|-------------|--------------|
| `staging-url.txt` | Staging service URL | After staging deployment |
| `production-deployment-info.json` | Deployment metadata | After production deployment |
| `production-rollback-info.json` | Rollback metadata | After rollback |
| `production-verification-report.json` | Verification test results | After verification |
| `monitor-production.ps1` | Monitoring commands | After production deployment |

## Troubleshooting

### Script fails with "gcloud not found"

**Solution:** Install Google Cloud SDK
```powershell
# Download from: https://cloud.google.com/sdk/docs/install
# Or use chocolatey:
choco install gcloudsdk
```

### Script fails with "permission denied"

**Solution:** Check GCP permissions
```powershell
# Check current account
gcloud auth list

# Login if needed
gcloud auth login

# Set project
gcloud config set project trim-descent-452802-t2
```

### Cannot find deployment info file

**Solution:** Run deploy-production.ps1 first
```powershell
# The rollout and rollback scripts need deployment info
.\deploy-production.ps1
```

### Verification tests fail

**Solution:** Check specific failures
```powershell
# Review verification report
Get-Content production-verification-report.json | ConvertFrom-Json

# Check logs for errors
gcloud run services logs read solar-weather-api --region asia-southeast1 --limit 100

# Test specific endpoint manually
curl https://solar-weather-api-<hash>.run.app/health
```

## Best Practices

1. **Always test in staging first**
   - Run full test suite before production deployment
   - Verify all endpoints working

2. **Use gradual rollout**
   - Start with 10% traffic
   - Monitor for issues before increasing
   - Don't rush to 100%

3. **Monitor continuously**
   - Watch logs during rollout
   - Check error rates and performance
   - Use verification script frequently

4. **Have rollback plan ready**
   - Know how to rollback quickly
   - Test rollback procedure in staging
   - Document rollback reasons

5. **Document everything**
   - Save deployment info files
   - Keep verification reports
   - Document any issues encountered

6. **Communicate with team**
   - Notify team before deployment
   - Share deployment status
   - Report completion or issues

## Support

For issues or questions:
- Check logs: `gcloud run services logs read solar-weather-api --region asia-southeast1`
- Review documentation: `PRODUCTION_DEPLOYMENT.md`, `DEPLOYMENT_GUIDE.md`
- GitHub Issues: https://github.com/EayonTinthai/gis-solar-potential-cpe/issues

---

**Document Version**: 1.0  
**Last Updated**: April 19, 2026  
**API Version**: 2.2.0

