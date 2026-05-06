# Deployment Checklist - v2.2.0

This checklist ensures all requirements are met before deploying the Solar Potential API v2.2.0 to production.

## Pre-Deployment Checklist

### 1. Environment Variables

Verify all required environment variables are set in Cloud Run:

- [ ] `GCP_PROJECT` - Google Cloud Project ID (e.g., `trim-descent-452802-t2`)
- [ ] `BIGQUERY_DATASET` - BigQuery dataset name (default: `openbuildings`)
- [ ] `BIGQUERY_TABLE` - BigQuery table name (default: `thailand_raw`)
- [ ] `WXTECH_API_KEY` - WxTech Weather API key (optional, stored in Secret Manager)
- [ ] `ADMIN_API_KEYS` - Comma-separated admin API keys (stored in Secret Manager)
- [ ] `LOG_LEVEL` - Logging level (default: `INFO`)
- [ ] `API_VERSION` - API version (should be `2.2.0`)

**Optional Performance Tuning Variables:**
- [ ] `CACHE_TTL_STATS` - Cache TTL for stats endpoint (default: 86400 seconds)
- [ ] `CACHE_TTL_BUILDINGS` - Cache TTL for buildings endpoint (default: 3600 seconds)
- [ ] `CACHE_TTL_WEATHER` - Cache TTL for weather endpoint (default: 3600 seconds)
- [ ] `CACHE_TTL_RANKINGS` - Cache TTL for rankings endpoint (default: 86400 seconds)
- [ ] `CACHE_MAX_SIZE` - Maximum cache entries (default: 1000)
- [ ] `RATE_LIMIT_PUBLIC` - Rate limit for public endpoints (default: 10 req/s)
- [ ] `RATE_LIMIT_AUTHENTICATED` - Rate limit for authenticated endpoints (default: 50 req/s)
- [ ] `MAX_WORKERS` - Number of worker processes (default: 4)
- [ ] `BIGQUERY_TIMEOUT_SECONDS` - BigQuery query timeout (default: 30)
- [ ] `REQUEST_TIMEOUT_SECONDS` - HTTP request timeout (default: 30)

### 2. BigQuery Tables and Views

Verify all required BigQuery objects exist:

- [ ] **Main table**: `{PROJECT}.openbuildings.thailand_raw`
  - Contains 107M+ building footprints
  - Has columns: `open_buildings_id`, `latitude`, `longitude`, `area_in_meters`, `confidence`, `geometry_wkt`

- [ ] **Materialized view**: `{PROJECT}.openbuildings.stats_summary`
  - Created by migration `002_create_stats_summary_view.sql`
  - Provides fast statistics queries
  - Verify it's refreshed and up-to-date

- [ ] **Rankings cache table**: `{PROJECT}.openbuildings.rankings_cache`
  - Created by migration `001_create_rankings_cache.sql`
  - Partitioned by `calculated_at` date
  - Clustered by `scope_type`, `scope_value`, `ranking_position`

- [ ] **Permitting data table**: `{PROJECT}.openbuildings.permitting_data` (optional)
  - Created by migration `003_create_permitting_data.sql`
  - May be empty initially (placeholder for future integration)

- [ ] **Indexes**: Verify indexes exist
  - Created by migration `004_create_indexes.sql`
  - Check indexes on: `confidence`, `area_in_meters`, spatial columns

**Verification Command:**
```bash
# List all tables in dataset
bq ls --project_id=trim-descent-452802-t2 openbuildings

# Check stats_summary view
bq query --project_id=trim-descent-452802-t2 "SELECT * FROM openbuildings.stats_summary LIMIT 1"

# Check rankings_cache table
bq query --project_id=trim-descent-452802-t2 "SELECT COUNT(*) FROM openbuildings.rankings_cache"
```

### 3. Database Migrations

Verify all migrations have been executed:

- [ ] Migration 001: `001_create_rankings_cache.sql` - Rankings cache table
- [ ] Migration 002: `002_create_stats_summary_view.sql` - Stats summary materialized view
- [ ] Migration 003: `003_create_permitting_data.sql` - Permitting data table
- [ ] Migration 004: `004_create_indexes.sql` - Performance indexes

**Verification:**
```bash
cd solar-panel-detection-main/backend/migrations
python ../verify_migrations.py
```

### 4. Rankings Pre-calculation

Rankings must be pre-calculated before deployment:

- [ ] Run rankings calculation script:
  ```bash
  cd solar-panel-detection-main/backend
  python calculate_rankings.py
  ```

- [ ] Verify rankings were created:
  ```bash
  bq query --project_id=trim-descent-452802-t2 \
    "SELECT COUNT(*) as total, 
     MIN(calculated_at) as oldest, 
     MAX(calculated_at) as newest 
     FROM openbuildings.rankings_cache"
  ```

- [ ] Set up Cloud Scheduler job for daily rankings refresh (optional):
  ```bash
  gcloud scheduler jobs create http rankings-refresh \
    --schedule="0 2 * * *" \
    --uri="https://YOUR-CLOUD-RUN-URL/admin/rankings/refresh" \
    --http-method=POST \
    --headers="X-API-Key=YOUR-ADMIN-KEY"
  ```

### 5. Tests

Verify all tests pass:

- [ ] **Unit tests**: Run all unit tests
  ```bash
  cd solar-panel-detection-main/backend
  pytest tests/test_enrichment.py -v
  pytest tests/test_validation.py -v
  ```

- [ ] **Integration tests**: Run endpoint tests
  ```bash
  pytest tests/test_endpoints.py -v
  ```

- [ ] **Load tests**: Verify performance targets
  ```bash
  pytest tests/test_cache.py -v
  # Optional: Run Locust load tests
  python run_load_tests.py
  ```

- [ ] **Security tests**: Verify authentication and rate limiting
  ```bash
  pytest tests/test_security.py -v
  ```

**Expected Results:**
- All tests should pass
- No critical errors or warnings
- Performance targets met (p95 < 600ms)

### 6. Documentation

Verify all documentation is up-to-date:

- [ ] `BACKEND.md` - Complete API reference with v2.2.0 features
- [ ] `README.md` - Updated with v2.2.0 features and version number
- [ ] `.env.example` - Contains all required environment variables
- [ ] `DEPLOYMENT_GUIDE.md` - Deployment instructions are current
- [ ] OpenAPI documentation - Auto-generated at `/docs` endpoint
- [ ] Version numbers updated to `2.2.0` in:
  - [ ] `api_bigquery.py` (FastAPI app version)
  - [ ] `BACKEND.md` (API Version)
  - [ ] `README.md` (Version footer)
  - [ ] All test files expecting version `2.2.0`

### 7. Code Quality

- [ ] No syntax errors (run `python -m py_compile api_bigquery.py`)
- [ ] All imports resolve correctly
- [ ] No hardcoded credentials or API keys
- [ ] Logging configured appropriately (no debug logs in production)
- [ ] Error handling implemented for all endpoints
- [ ] Rate limiting configured and tested

### 8. Security

- [ ] Admin API keys stored in Secret Manager (not in code or env files)
- [ ] CORS configured appropriately (currently allows all origins for public API)
- [ ] Rate limiting enabled and tested
- [ ] Input validation implemented for all endpoints
- [ ] SQL injection prevention (using parameterized queries)
- [ ] No sensitive data in logs

### 9. Performance

- [ ] Caching implemented and tested
- [ ] Cache hit rate > 60% (verify after deployment)
- [ ] Response times meet targets:
  - [ ] Building queries: p95 < 600ms
  - [ ] Solar calculations: p95 < 600ms
  - [ ] Weather forecasts: p95 < 500ms
- [ ] BigQuery queries optimized (use EXPLAIN to verify)
- [ ] Materialized views refreshed

### 10. Monitoring and Logging

- [ ] Cloud Logging configured
- [ ] Request logging middleware enabled
- [ ] Error tracking configured
- [ ] Performance metrics tracked
- [ ] Health check endpoint working (`/health`)
- [ ] Uptime monitoring configured (optional)

---

## Deployment Steps

### Step 1: Build Container Image

```bash
cd solar-panel-detection-main/backend

# Build using Cloud Build
gcloud builds submit --config=cloudbuild-bigquery.yaml \
  --project=trim-descent-452802-t2
```

**Verify:**
- [ ] Build completes successfully
- [ ] Container image pushed to Container Registry
- [ ] No build errors or warnings

### Step 2: Deploy to Cloud Run (Staging)

```bash
# Deploy to staging with 10% traffic
gcloud run deploy solar-weather-api-staging \
  --image gcr.io/trim-descent-452802-t2/solar-bigquery-api:latest \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300s \
  --set-env-vars "GCP_PROJECT=trim-descent-452802-t2,BIGQUERY_DATASET=openbuildings,BIGQUERY_TABLE=thailand_raw,API_VERSION=2.2.0,LOG_LEVEL=INFO" \
  --set-secrets "WXTECH_API_KEY=wxtech-api-key:latest,ADMIN_API_KEYS=admin-api-keys:latest"
```

**Verify:**
- [ ] Deployment completes successfully
- [ ] Service is accessible
- [ ] Health check passes

### Step 3: Smoke Tests on Staging

Run smoke tests against staging environment:

```bash
# Set staging URL
export STAGING_URL="https://solar-weather-api-staging-XXXXX.run.app"

# Test health endpoint
curl "$STAGING_URL/health"

# Test stats endpoint
curl "$STAGING_URL/stats"

# Test buildings endpoint
curl "$STAGING_URL/buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=5"

# Test solar calculation
curl -X POST "$STAGING_URL/solar/calculate" \
  -H "Content-Type: application/json" \
  -d '{"latitude":13.7563,"longitude":100.5018,"area_m2":250,"confidence":0.95}'

# Test rankings endpoint
curl "$STAGING_URL/rankings?limit=10"

# Test admin endpoint (with API key)
curl -H "X-API-Key: YOUR-ADMIN-KEY" "$STAGING_URL/admin/data-quality"
```

**Verify:**
- [ ] All endpoints return HTTP 200
- [ ] Responses contain expected data
- [ ] No errors in Cloud Logging
- [ ] Response times acceptable

### Step 4: Deploy to Production

```bash
# Deploy to production
gcloud run deploy solar-weather-api \
  --image gcr.io/trim-descent-452802-t2/solar-bigquery-api:latest \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --timeout 300s \
  --set-env-vars "GCP_PROJECT=trim-descent-452802-t2,BIGQUERY_DATASET=openbuildings,BIGQUERY_TABLE=thailand_raw,API_VERSION=2.2.0,LOG_LEVEL=INFO" \
  --set-secrets "WXTECH_API_KEY=wxtech-api-key:latest,ADMIN_API_KEYS=admin-api-keys:latest"
```

**Verify:**
- [ ] Deployment completes successfully
- [ ] Service is accessible at production URL
- [ ] Health check passes

### Step 5: Gradual Rollout (Optional)

If using traffic splitting:

```bash
# Start with 10% traffic to new version
gcloud run services update-traffic solar-weather-api \
  --to-revisions=LATEST=10

# Monitor for 30 minutes
# Check error rates, response times, cache hit rates

# Increase to 50% if stable
gcloud run services update-traffic solar-weather-api \
  --to-revisions=LATEST=50

# Monitor for 1 hour

# Increase to 100% if stable
gcloud run services update-traffic solar-weather-api \
  --to-revisions=LATEST=100
```

**Monitor:**
- [ ] Error rate < 0.1%
- [ ] Response times within targets
- [ ] No increase in 5xx errors
- [ ] Cache hit rate > 60%

### Step 6: Post-Deployment Verification

Run full test suite against production:

```bash
# Set production URL
export PROD_URL="https://solar-weather-api-715107904640.asia-southeast1.run.app"

# Run smoke tests (same as staging)
# Test all endpoints
# Verify responses

# Check Cloud Logging for errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=solar-weather-api" \
  --limit 50 \
  --format json

# Check performance metrics
# Visit Cloud Console > Cloud Run > solar-weather-api > Metrics
```

**Verify:**
- [ ] All endpoints working correctly
- [ ] No errors in logs
- [ ] Response times within targets
- [ ] Cache working correctly
- [ ] Rate limiting working
- [ ] Authentication working for admin endpoints

---

## Post-Deployment Monitoring

### First 24 Hours

Monitor these metrics closely:

- [ ] **Error Rate**: Should be < 0.1%
- [ ] **Response Time**: p95 < 600ms, p99 < 1000ms
- [ ] **Cache Hit Rate**: Should be > 60%
- [ ] **Request Volume**: Track baseline
- [ ] **BigQuery Costs**: Monitor query costs
- [ ] **Memory Usage**: Should be < 80% of allocated
- [ ] **CPU Usage**: Should be < 80% of allocated

### Alerts to Configure

Set up alerts for:

- [ ] Error rate > 1%
- [ ] Response time p95 > 1000ms
- [ ] Memory usage > 90%
- [ ] CPU usage > 90%
- [ ] BigQuery query failures
- [ ] Health check failures

---

## Rollback Plan

If issues are detected:

### Quick Rollback

```bash
# Rollback to previous revision
gcloud run services update-traffic solar-weather-api \
  --to-revisions=PREVIOUS_REVISION=100

# Or rollback to specific revision
gcloud run services update-traffic solar-weather-api \
  --to-revisions=solar-weather-api-00042-abc=100
```

### Verify Rollback

- [ ] Service is accessible
- [ ] Health check passes
- [ ] Error rate returns to normal
- [ ] Response times return to normal

---

## Success Criteria

Deployment is considered successful when:

- [ ] All pre-deployment checks passed
- [ ] All tests passed
- [ ] Deployment completed without errors
- [ ] All smoke tests passed
- [ ] Error rate < 0.1% for 24 hours
- [ ] Response times meet targets (p95 < 600ms)
- [ ] Cache hit rate > 60%
- [ ] No critical errors in logs
- [ ] All new v2.2.0 endpoints working correctly
- [ ] Documentation updated and accessible

---

## Troubleshooting

### Common Issues

**Issue: BigQuery connection fails**
- Check `GCP_PROJECT` environment variable
- Verify service account has BigQuery permissions
- Check BigQuery API is enabled

**Issue: Weather API fails**
- Check `WXTECH_API_KEY` is set correctly
- Verify API key is valid and not expired
- Check API quota limits

**Issue: Rankings endpoint returns empty results**
- Verify rankings have been pre-calculated
- Check `rankings_cache` table has data
- Run `calculate_rankings.py` script

**Issue: High response times**
- Check cache is working (look for `X-Cache-Status` header)
- Verify BigQuery queries are optimized
- Check materialized views are refreshed
- Consider increasing Cloud Run instances

**Issue: Rate limiting too aggressive**
- Adjust `RATE_LIMIT_PUBLIC` and `RATE_LIMIT_AUTHENTICATED` env vars
- Check rate limit headers in responses

---

## Contact

For deployment issues or questions:
- GitHub Issues: https://github.com/EayonTinthai/gis-solar-potential-cpe/issues
- Repository: https://github.com/EayonTinthai/gis-solar-potential-cpe

---

**Document Version**: 1.0  
**Created**: April 19, 2026  
**API Version**: 2.2.0  
**Status**: Ready for Production Deployment
