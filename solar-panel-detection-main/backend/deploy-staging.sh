#!/bin/bash
# Deploy to Staging Environment
# This script builds and deploys the Solar Potential API to Cloud Run staging

set -e  # Exit on error

# Configuration
PROJECT_ID="${1:-trim-descent-452802-t2}"
REGION="${2:-asia-southeast1}"
SERVICE_NAME="${3:-solar-weather-api-staging}"
SKIP_BUILD="${SKIP_BUILD:-false}"

echo "========================================"
echo "Solar Potential API - Staging Deployment"
echo "========================================"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Set project
echo "Setting GCP project to: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# Navigate to backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "Current directory: $(pwd)"
echo ""

# Step 1: Build Docker image (unless skipped)
if [ "$SKIP_BUILD" != "true" ]; then
    echo "Step 1: Building Docker image..."
    echo "Using Cloud Build with cloudbuild-bigquery.yaml"
    
    # Submit build to Cloud Build
    gcloud builds submit --config=cloudbuild-bigquery.yaml --project="$PROJECT_ID"
    
    echo "Build completed successfully!"
    echo ""
else
    echo "Step 1: Skipping build (using existing image)"
    echo ""
fi

# Step 2: Deploy to Cloud Run Staging
echo "Step 2: Deploying to Cloud Run staging..."
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Deploy command
gcloud run deploy "$SERVICE_NAME" \
  --image "gcr.io/$PROJECT_ID/solar-bigquery-api:latest" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 60s \
  --set-env-vars "GCP_PROJECT=$PROJECT_ID,BIGQUERY_DATASET=openbuildings,BIGQUERY_TABLE=thailand_raw,API_VERSION=2.2.0,LOG_LEVEL=INFO,CACHE_TTL_STATS=86400,CACHE_TTL_BUILDINGS=3600,CACHE_TTL_WEATHER=3600,CACHE_TTL_RANKINGS=86400,CACHE_MAX_SIZE=1000,RATE_LIMIT_PUBLIC=10,RATE_LIMIT_AUTHENTICATED=50,MAX_WORKERS=4,BIGQUERY_TIMEOUT_SECONDS=30,REQUEST_TIMEOUT_SECONDS=30" \
  --project="$PROJECT_ID"

echo ""
echo "Deployment completed successfully!"
echo ""

# Step 3: Get service URL
echo "Step 3: Getting service URL..."
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format "value(status.url)" --project="$PROJECT_ID")

if [ -n "$SERVICE_URL" ]; then
    echo "Service URL: $SERVICE_URL"
    echo ""
    
    # Save URL to file for smoke tests
    echo "$SERVICE_URL" > staging-url.txt
    echo "Service URL saved to: staging-url.txt"
else
    echo "WARNING: Could not retrieve service URL"
fi

echo ""
echo "========================================"
echo "Staging Deployment Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Run smoke tests: ./run-smoke-tests.sh"
echo "2. Run full test suite: ./run-staging-tests.sh"
echo "3. Monitor logs: gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo ""
