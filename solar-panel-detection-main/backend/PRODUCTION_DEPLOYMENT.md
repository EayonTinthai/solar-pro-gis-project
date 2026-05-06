# Production Deployment Guide - Solar Potential API v2.2.0

This guide provides step-by-step instructions for safely deploying the Solar Potential API v2.2.0 to production using gradual traffic rollout.

## Overview

The production deployment process uses **traffic splitting** to gradually route traffic to the new version, allowing you to monitor for issues and rollback if needed.

### Deployment Stages

1. **Deploy with 0% traffic** - Deploy new version without routing any traffic
2. **Route 10% traffic** - Send 10% of requests to new version
3. **Monitor for 5-10 minutes** - Check logs, metrics, and error rates
4. **Route 50% traffic** - Increase to 50% if no issues detected
5. **Monitor for 1 hour** - Extended monitoring period
6. **Route 100% traffic** - Complete rollout if stable
7. **Post-deployment verification** - Verify all endpoints working

## Prerequisites

Before deploying to production:

- [ ] All staging tests passed successfully
- [ ] Load tests completed with acceptable performance
- [ ] Security review completed
- [ ] Database migrations applied (if any)
- [ ] Environment variables configured in Secret Manager
- [ ] Rollback plan documented
- [ ] Stakeholders notified of deployment window
- [ ] Monitoring dashboards ready

## Required Tools

- Google Cloud SDK (`gcloud`) installed and configured
- PowerShell 5.1 or later
- Access to GCP project: `trim-descent-452802-t2`
- Permissions: Cloud Run Admin, Logs Viewer, Monitoring Viewer

## Environment Variables

Ensure these are configured in Cloud Run or Secret Manager:

### Required
```bash
GCP_PROJECT=trim-descent-452802-t2
BIGQUERY_DATASET=openbuildings
BIGQUERY_TABLE=thailand_raw
WXTECH_API_KEY=<from Secret Manager>
ADMIN_API_KEYS=<from Secret Manager>
```

### Optional (with defaults)
```bash
API_VERSION=2.2.0
LOG_LEVEL=INFO
CACHE_TTL_STATS=86400
CACHE_TTL_BUILDINGS=3600
CACHE_TTL_WEATHER=3600
CACHE_TTL_RANKINGS=86400
CACHE_MAX_SIZE=1000
RATE_LIMIT_PUBLIC=10
RATE_LIMIT_AUTHENTICATED=50
MAX_WORKERS=4
BIGQUERY_TIMEOUT_SECONDS=30
REQUEST_TIMEOUT_SECONDS=30
```

## Deployment Process

### Step 1: Pre-Deployment Checks

Run pre-deployment verification:

```powershell
# Verify staging is working
.\verify-production.ps1 -ServiceUrl "https://solar-weather-api-staging-<hash>.run.app"

# Check current production status
gcloud run services describe solar-weather-api --region asia-southeast1

# Review recent production logs
gcloud run services logs read solar-weather-api --region asia-southeast1 --limit 50
```

### Step 2: Deploy New Version (10% Traffic)

Deploy the new version with initial 10% traffic split:

```powershell
.\deploy-production.ps1 -InitialTrafficPercent 10
```

**What this does:**
1. Builds Docker image using Cloud Build
2. Deploys new revision to Cloud Run with 0% traffic
3. Splits traffic: 10% to new revision, 90% to old revision
4. Saves deployment info to `production-deployment-info.json`
5. Creates monitoring script `monitor-production.ps1`

**Expected output:**
```
========================================
Initial Deployment Complete!
========================================

Current Status:
  New revision: solar-weather-api-00042-abc (10% traffic)
  Old revision: solar-weather-api-00041-xyz (90% traffic)

Next Steps:
  1. Monitor logs and metrics for 5 minutes
  2. If no issues, run: .\rollout-production.ps1 -Stage 50
  ...
```

### Step 3: Monitor Initial Rollout (5-10 minutes)

Monitor the deployment for issues:

```powershell
# Stream logs
gcloud run services logs tail solar-weather-api --region asia-southeast1

# Or use monitoring script
.\monitor-production.ps1

# Check health endpoint
curl https://solar-weather-api-<hash>.run.app/health

# Run verification
.\verify-production.ps1
```

**What to look for:**
- ✅ No increase in error rate
- ✅ Response times within acceptable range (<600ms p95)
- ✅ Health check returns "healthy"
- ✅ No critical errors in logs
- ✅ Cache working correctly (X-Cache-Status headers)

**If issues detected:**
```powershell
# Rollback immediately
.\rollback-production.ps1
```

### Step 4: Increase to 50% Traffic

If monitoring looks good after 5-10 minutes:

```powershell
.\rollout-production.ps1 -Stage 50
```

**What this does:**
1. Updates traffic split to 50% new, 50% old
2. Updates deployment info
3. Provides monitoring instructions

**Expected output:**
```
========================================
Rollout Stage 50% Complete!
========================================

Current Status:
  New revision: solar-weather-api-00042-abc (50% traffic)
  Old revision: solar-weather-api-00041-xyz (50% traffic)

Next Steps:
  1. Monitor for 1 hour
  2. Check error rates and performance metrics
  3. If stable, run: .\rollout-production.ps1 -Stage 100
  ...
```

### Step 5: Extended Monitoring (1 hour)

Monitor for 1 hour at 50% traffic:

```powershell
# Continuous monitoring
.\monitor-production.ps1

# Check metrics dashboard
# https://console.cloud.google.com/run/detail/asia-southeast1/solar-weather-api/metrics

# Run verification every 15 minutes
.\verify-production.ps1
```

**Monitoring checklist:**
- [ ] Error rate remains stable
- [ ] Response times acceptable
- [ ] No memory/CPU issues
- [ ] Cache hit rate >60%
- [ ] No user complaints
- [ ] All endpoints responding correctly

**If issues detected:**
```powershell
# Rollback to previous version
.\rollback-production.ps1
```

### Step 6: Complete Rollout (100% Traffic)

If monitoring is stable after 1 hour:

```powershell
.\rollout-production.ps1 -Stage 100
```

**What this does:**
1. Routes 100% traffic to new revision
2. Updates deployment info
3. Marks deployment as complete

**Expected output:**
```
========================================
Rollout Stage 100% Complete!
========================================

Deployment Complete!
  All traffic is now routed to the new revision.

Post-Deployment Tasks:
  1. Continue monitoring for 24 hours
  2. Run post-deployment verification: .\verify-production.ps1
  ...
```

### Step 7: Post-Deployment Verification

Run comprehensive verification:

```powershell
.\verify-production.ps1
```

**What this tests:**
1. Health check endpoint
2. Statistics endpoints (/stats, /stats/distribution)
3. Buildings endpoints (/buildings/bbox, /buildings/nearby)
4. Solar calculation endpoint
5. Rankings endpoint
6. Polygon analysis endpoint
7. Documentation endpoint
8. Cache headers
9. Performance (p95 < 600ms)
10. Error logs

**Expected output:**
```
========================================
Verification Summary
========================================

Total Tests: 11
Passed: 11
Failed: 0
Success Rate: 100%

========================================
✓ All Verifications Passed!
========================================

Production deployment is healthy and working correctly.
```

### Step 8: Post-Deployment Tasks

After successful deployment:

1. **Continue monitoring for 24 hours**
   ```powershell
   # Check logs periodically
   gcloud run services logs read solar-weather-api --region asia-southeast1 --limit 100
   ```

2. **Update documentation**
   - Update CHANGELOG.md with v2.2.0 changes
   - Update API documentation if needed
   - Update README.md with new features

3. **Notify stakeholders**
   - Send deployment success notification
   - Share new features and improvements
   - Provide updated API documentation links

4. **Clean up old revisions** (after 7 days)
   ```powershell
   # List revisions
   gcloud run revisions list --service solar-weather-api --region asia-southeast1
   
   # Delete old revisions (keep last 3)
   gcloud run revisions delete <old-revision-name> --region asia-southeast1
   ```

## Rollback Procedure

If issues are detected at any stage:

### Immediate Rollback

```powershell
.\rollback-production.ps1
```

This will:
1. Route 100% traffic back to previous revision
2. Save rollback info to `production-rollback-info.json`
3. Provide next steps for investigation

### Post-Rollback Actions

1. **Verify rollback successful**
   ```powershell
   .\verify-production.ps1
   ```

2. **Investigate issues**
   - Review error logs
   - Check metrics for anomalies
   - Reproduce issues in staging

3. **Document rollback reason**
   - Update `production-rollback-info.json`
   - Create incident report
   - Plan fixes for next deployment

4. **Fix and redeploy**
   - Fix identified issues
   - Test thoroughly in staging
   - Schedule new deployment

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Error Rate**
   - Target: <0.1%
   - Alert threshold: >1%

2. **Response Time**
   - Target: p95 <600ms
   - Alert threshold: p95 >1000ms

3. **Request Rate**
   - Monitor for unusual spikes or drops

4. **Cache Hit Rate**
   - Target: >60%
   - Alert threshold: <40%

5. **Memory Usage**
   - Target: <80% of allocated
   - Alert threshold: >90%

6. **CPU Usage**
   - Target: <70% average
   - Alert threshold: >85%

### Monitoring Commands

```powershell
# Stream logs
gcloud run services logs tail solar-weather-api --region asia-southeast1

# View error logs only
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=solar-weather-api AND severity>=ERROR" --limit 50 --format json

# Check current traffic split
gcloud run services describe solar-weather-api --region asia-southeast1 --format="value(status.traffic)"

# View metrics
# Open: https://console.cloud.google.com/run/detail/asia-southeast1/solar-weather-api/metrics
```

## Troubleshooting

### Issue: Deployment fails during build

**Symptoms:**
- Cloud Build fails
- Docker image not created

**Solutions:**
1. Check Cloud Build logs
2. Verify Dockerfile.bigquery is correct
3. Check for syntax errors in code
4. Ensure all dependencies in requirements.txt

### Issue: New revision won't start

**Symptoms:**
- Revision shows as "Failed"
- Container crashes on startup

**Solutions:**
1. Check container logs
2. Verify environment variables are set
3. Check for missing secrets
4. Verify BigQuery permissions

### Issue: High error rate on new revision

**Symptoms:**
- Error rate >1%
- 500 errors in logs

**Solutions:**
1. Rollback immediately
2. Check error logs for patterns
3. Verify database connectivity
4. Check for breaking changes

### Issue: Slow response times

**Symptoms:**
- p95 >1000ms
- Timeout errors

**Solutions:**
1. Check BigQuery query performance
2. Verify cache is working
3. Check memory/CPU allocation
4. Consider increasing resources

### Issue: Cache not working

**Symptoms:**
- All requests show X-Cache-Status: MISS
- High BigQuery query rate

**Solutions:**
1. Check cache configuration
2. Verify cache TTL settings
3. Check for cache key collisions
4. Review cache middleware

## Emergency Contacts

- **On-Call Engineer**: [Contact info]
- **Platform Team Lead**: [Contact info]
- **GCP Support**: [Support case link]

## Deployment Checklist

Use this checklist for each production deployment:

### Pre-Deployment
- [ ] All staging tests passed
- [ ] Load tests completed
- [ ] Security review completed
- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] Rollback plan documented
- [ ] Stakeholders notified
- [ ] Monitoring dashboards ready

### Deployment
- [ ] Deploy with 10% traffic
- [ ] Monitor for 5-10 minutes
- [ ] No errors detected
- [ ] Increase to 50% traffic
- [ ] Monitor for 1 hour
- [ ] No issues detected
- [ ] Increase to 100% traffic
- [ ] Run post-deployment verification

### Post-Deployment
- [ ] All verification tests passed
- [ ] Monitoring for 24 hours
- [ ] Documentation updated
- [ ] Stakeholders notified
- [ ] Deployment report created
- [ ] Old revisions cleaned up (after 7 days)

## Success Criteria

Deployment is considered successful when:

- ✅ All verification tests pass (100% success rate)
- ✅ Error rate <0.1%
- ✅ Response time p95 <600ms
- ✅ Cache hit rate >60%
- ✅ No critical errors in logs
- ✅ All endpoints responding correctly
- ✅ No user complaints
- ✅ Stable for 24 hours

## Related Documents

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - General deployment information
- [Backend Documentation](BACKEND.md) - API documentation
- [Requirements](../../.kiro/specs/platform-improvements/requirements.md) - Feature requirements
- [Design](../../.kiro/specs/platform-improvements/design.md) - Technical design
- [Tasks](../../.kiro/specs/platform-improvements/tasks.md) - Implementation tasks

---

**Document Version**: 1.0  
**Last Updated**: April 19, 2026  
**API Version**: 2.2.0  
**Author**: Platform Team

