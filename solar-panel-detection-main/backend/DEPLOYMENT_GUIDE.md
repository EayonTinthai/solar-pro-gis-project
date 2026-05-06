# Deployment Guide - Solar Potential API v2.2.0

This guide covers deploying the enhanced Solar Potential API to Google Cloud Run.

## Prerequisites

- Google Cloud SDK installed and configured
- Docker installed (for local testing)
- Access to GCP project: `trim-descent-452802-t2`
- Required API keys (WxTech Weather API, Admin API keys)

## Environment Variables

### Required Variables

These MUST be set in Cloud Run for the application to function:

```bash
# Google Cloud Platform
GCP_PROJECT=trim-descent-452802-t2

# BigQuery Configuration
BIGQUERY_DATASET=openbuildings
BIGQUERY_TABLE=thailand_raw

# WxTech Weather API (Required for weather forecasting)
WXTECH_API_KEY=your_actual_wxtech_api_key

# Admin API Keys (Required for admin endpoints)
ADMIN_API_KEYS=key1,key2,key3
```

### Optional Variables (with defaults)

These have sensible defaults but can be customized:

```bash
# Cache Configuration (Requirement 4)
CACHE_TTL_STATS=86400              # 24 hours
CACHE_TTL_BUILDINGS=3600           # 1 hour
CACHE_TTL_WEATHER=3600             # 1 hour
CACHE_TTL_RANKINGS=86400           # 24 hours
CACHE_MAX_SIZE=1000                # Max cache entries

# Rate Limiting (Requirement 4)
RATE_LIMIT_PUBLIC=10               # Requests per second
RATE_LIMIT_AUTHENTICATED=50        # Requests per second for authenticated users
RATE_LIMIT_BURST=100               # Burst capacity

# Performance Tuning (Requirement 14)
MAX_WORKERS=4                      # Uvicorn worker processes
MAX_CONCURRENT_QUERIES=10          # Max concurrent BigQuery queries
BIGQUERY_TIMEOUT_SECONDS=30        # BigQuery query timeout
REQUEST_TIMEOUT_SECONDS=30         # HTTP request timeout

# Logging
LOG_LEVEL=INFO                     # DEBUG, INFO, WARNING, ERROR, CRITICAL

# API Configuration
API_VERSION=2.2.0
API_TITLE=Solar Potential API
API_DESCRIPTION=Comprehensive solar photovoltaic potential analysis API for Thailand

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

## Deployment Methods

### Method 1: Using Cloud Build (Recommended)

This method uses the `cloudbuild-bigquery.yaml` configuration:

```bash
# Navigate to backend directory
cd solar-panel-detection-main/backend

# Submit build to Cloud Build
gcloud builds submit --config=cloudbuild-bigquery.yaml

# Cloud Build will:
# 1. Build the Docker image
# 2. Push to Container Registry
# 3. Deploy to Cloud Run with environment variables
```

**Note**: The cloudbuild.yaml includes basic environment variables. You'll need to add secrets separately.

### Method 2: Manual Deployment

#### Step 1: Build Docker Image

```bash
cd solar-panel-detection-main/backend

# Build image
docker build -f Dockerfile.bigquery -t gcr.io/trim-descent-452802-t2/solar-bigquery-api:v2.2.0 .

# Push to Container Registry
docker push gcr.io/trim-descent-452802-t2/solar-bigquery-api:v2.2.0
```

#### Step 2: Deploy to Cloud Run

```bash
gcloud run deploy solar-weather-api \
  --image gcr.io/trim-descent-452802-t2/solar-bigquery-api:v2.2.0 \
  --region asia-southeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --min-instances 1 \
  --timeout 60s \
  --set-env-vars "GCP_PROJECT=trim-descent-452802-t2,BIGQUERY_DATASET=openbuildings,BIGQUERY_TABLE=thailand_raw,API_VERSION=2.2.0,LOG_LEVEL=INFO" \
  --set-secrets "WXTECH_API_KEY=wxtech-api-key:latest,ADMIN_API_KEYS=admin-api-keys:latest"
```

### Method 3: Using Secret Manager (Most Secure)

#### Step 1: Store Secrets

```bash
# Store WxTech API Key
echo -n "your_actual_wxtech_api_key" | gcloud secrets create wxtech-api-key \
  --data-file=- \
  --replication-policy="automatic"

# Store Admin API Keys
echo -n "key1,key2,key3" | gcloud secrets create admin-api-keys \
  --data-file=- \
  --replication-policy="automatic"

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding wxtech-api-key \
  --member="serviceAccount:715107904640-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding admin-api-keys \
  --member="serviceAccount:715107904640-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### Step 2: Deploy with Secrets

```bash
gcloud run deploy solar-weather-api \
  --image gcr.io/trim-descent-452802-t2/solar-bigquery-api:v2.2.0 \
  --region asia-southeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --min-instances 1 \
  --timeout 60s \
  --set-env-vars "GCP_PROJECT=trim-descent-452802-t2,BIGQUERY_DATASET=openbuildings,BIGQUERY_TABLE=thailand_raw,API_VERSION=2.2.0,LOG_LEVEL=INFO,CACHE_TTL_STATS=86400,CACHE_TTL_BUILDINGS=3600,CACHE_TTL_WEATHER=3600,CACHE_TTL_RANKINGS=86400,CACHE_MAX_SIZE=1000,RATE_LIMIT_PUBLIC=10,RATE_LIMIT_AUTHENTICATED=50,MAX_WORKERS=4,BIGQUERY_TIMEOUT_SECONDS=30,REQUEST_TIMEOUT_SECONDS=30" \
  --set-secrets "WXTECH_API_KEY=wxtech-api-key:latest,ADMIN_API_KEYS=admin-api-keys:latest"
```

## Updating Environment Variables

To update environment variables on an existing Cloud Run service:

```bash
# Update a single variable
gcloud run services update solar-weather-api \
  --region asia-southeast1 \
  --update-env-vars "CACHE_TTL_STATS=43200"

# Update multiple variables
gcloud run services update solar-weather-api \
  --region asia-southeast1 \
  --update-env-vars "CACHE_TTL_STATS=43200,CACHE_TTL_BUILDINGS=1800,LOG_LEVEL=DEBUG"

# Update secrets
gcloud run services update solar-weather-api \
  --region asia-southeast1 \
  --update-secrets "WXTECH_API_KEY=wxtech-api-key:latest"
```

## Traffic Splitting (Gradual Rollout)

For safer deployments, use traffic splitting:

```bash
# Deploy new version with 0% traffic
gcloud run deploy solar-weather-api \
  --image gcr.io/trim-descent-452802-t2/solar-bigquery-api:v2.2.0 \
  --region asia-southeast1 \
  --no-traffic

# Get revision names
gcloud run revisions list --service solar-weather-api --region asia-southeast1

# Split traffic: 90% old, 10% new
gcloud run services update-traffic solar-weather-api \
  --region asia-southeast1 \
  --to-revisions=OLD_REVISION=90,NEW_REVISION=10

# Monitor for issues, then increase to 50/50
gcloud run services update-traffic solar-weather-api \
  --region asia-southeast1 \
  --to-revisions=OLD_REVISION=50,NEW_REVISION=50

# If all good, route 100% to new version
gcloud run services update-traffic solar-weather-api \
  --region asia-southeast1 \
  --to-latest
```

## Rollback

If issues are detected, rollback to previous version:

```bash
# List revisions
gcloud run revisions list --service solar-weather-api --region asia-southeast1

# Rollback to specific revision
gcloud run services update-traffic solar-weather-api \
  --region asia-southeast1 \
  --to-revisions=PREVIOUS_REVISION=100
```

## Verification

After deployment, verify the service is working:

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe solar-weather-api \
  --region asia-southeast1 \
  --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test stats endpoint
curl $SERVICE_URL/stats

# Test documentation
curl $SERVICE_URL/docs
```

## Monitoring

### View Logs

```bash
# Stream logs
gcloud run services logs tail solar-weather-api --region asia-southeast1

# View recent logs
gcloud run services logs read solar-weather-api --region asia-southeast1 --limit 100
```

### View Metrics

```bash
# Open Cloud Console metrics
gcloud run services describe solar-weather-api \
  --region asia-southeast1 \
  --format 'value(status.url)'
```

Then navigate to Cloud Console → Cloud Run → solar-weather-api → Metrics

## Troubleshooting

### Issue: Service won't start

**Check logs:**
```bash
gcloud run services logs read solar-weather-api --region asia-southeast1 --limit 50
```

**Common causes:**
- Missing required environment variables (GCP_PROJECT, BIGQUERY_DATASET, BIGQUERY_TABLE)
- Invalid API keys
- BigQuery permissions issues

### Issue: Slow response times

**Check:**
- Cache hit rates in logs
- BigQuery query performance
- Memory/CPU allocation

**Solutions:**
- Increase memory/CPU: `--memory 4Gi --cpu 4`
- Increase min instances: `--min-instances 2`
- Adjust cache TTL values

### Issue: Rate limiting errors

**Adjust rate limits:**
```bash
gcloud run services update solar-weather-api \
  --region asia-southeast1 \
  --update-env-vars "RATE_LIMIT_PUBLIC=20,RATE_LIMIT_AUTHENTICATED=100"
```

### Issue: BigQuery quota exceeded

**Solutions:**
- Increase cache TTL to reduce queries
- Implement request throttling
- Request quota increase from Google

## Performance Tuning

### Recommended Settings for Production

```bash
# High traffic (1000+ req/min)
--memory 4Gi
--cpu 4
--max-instances 20
--min-instances 3
--set-env-vars "CACHE_MAX_SIZE=5000,MAX_WORKERS=8"

# Medium traffic (100-1000 req/min)
--memory 2Gi
--cpu 2
--max-instances 10
--min-instances 1
--set-env-vars "CACHE_MAX_SIZE=2000,MAX_WORKERS=4"

# Low traffic (<100 req/min)
--memory 1Gi
--cpu 1
--max-instances 5
--min-instances 0
--set-env-vars "CACHE_MAX_SIZE=1000,MAX_WORKERS=2"
```

## Cost Optimization

### Tips to reduce costs:

1. **Use min-instances wisely**: Set to 0 for dev/staging, 1+ for production
2. **Optimize cache TTL**: Longer TTL = fewer BigQuery queries = lower costs
3. **Set appropriate max-instances**: Prevent runaway costs from traffic spikes
4. **Use request timeout**: Prevent long-running queries from consuming resources
5. **Monitor BigQuery usage**: Set up billing alerts

### Example cost-optimized deployment:

```bash
gcloud run deploy solar-weather-api \
  --image gcr.io/trim-descent-452802-t2/solar-bigquery-api:v2.2.0 \
  --region asia-southeast1 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 5 \
  --min-instances 0 \
  --timeout 30s \
  --set-env-vars "CACHE_TTL_STATS=86400,CACHE_TTL_BUILDINGS=7200,BIGQUERY_TIMEOUT_SECONDS=20"
```

## Security Checklist

- [ ] Admin API keys stored in Secret Manager
- [ ] WxTech API key stored in Secret Manager
- [ ] Service account has minimal required permissions
- [ ] Rate limiting enabled
- [ ] Request timeout configured
- [ ] CORS configured for allowed origins only
- [ ] Logging enabled for audit trail
- [ ] No secrets in Docker image or source code

## Post-Deployment Checklist

- [ ] Service deployed successfully
- [ ] Health check endpoint returns 200
- [ ] All environment variables set correctly
- [ ] Secrets accessible from Secret Manager
- [ ] API documentation accessible at /docs
- [ ] Test all major endpoints
- [ ] Monitor logs for errors
- [ ] Check metrics dashboard
- [ ] Verify cache is working (X-Cache-Status headers)
- [ ] Test rate limiting
- [ ] Update DNS/load balancer if needed
- [ ] Notify stakeholders of deployment

## Support

For issues or questions:
- Check logs: `gcloud run services logs read solar-weather-api --region asia-southeast1`
- Review documentation: `BACKEND.md`, `README.md`
- GitHub Issues: https://github.com/EayonTinthai/gis-solar-potential-cpe/issues

---

**Document Version**: 1.0  
**Last Updated**: April 18, 2026  
**API Version**: 2.2.0
