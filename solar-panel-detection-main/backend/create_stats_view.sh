#!/bin/bash
# Create stats_summary materialized view in BigQuery

echo "Creating stats_summary materialized view..."
echo "This will take a few minutes to process 107M+ records..."

bq query \
  --use_legacy_sql=false \
  --location=asia-southeast1 \
  --project_id=trim-descent-452802-t2 \
  "CREATE MATERIALIZED VIEW IF NOT EXISTS \`trim-descent-452802-t2.openbuildings.stats_summary\`
OPTIONS(
    enable_refresh=true,
    refresh_interval_minutes=1440,
    description='Materialized view for fast statistics queries',
    labels=[('purpose', 'stats'), ('version', 'v1')]
)
AS
SELECT 
    COUNT(*) as total_buildings,
    AVG(confidence) as avg_confidence,
    STDDEV(confidence) as std_dev_confidence,
    APPROX_QUANTILES(confidence, 100)[OFFSET(50)] as median_confidence,
    MIN(confidence) as min_confidence,
    MAX(confidence) as max_confidence,
    AVG(area_in_meters) as avg_area,
    STDDEV(area_in_meters) as std_dev_area,
    APPROX_QUANTILES(area_in_meters, 100)[OFFSET(50)] as median_area,
    MIN(area_in_meters) as min_area,
    MAX(area_in_meters) as max_area,
    MIN(latitude) as min_lat,
    MAX(latitude) as max_lat,
    MIN(longitude) as min_lon,
    MAX(longitude) as max_lon,
    CURRENT_TIMESTAMP() as last_updated
FROM \`trim-descent-452802-t2.openbuildings.thailand_raw\`"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Materialized view created successfully!"
    echo "View: trim-descent-452802-t2.openbuildings.stats_summary"
    echo "Refresh interval: Daily (1440 minutes)"
    echo ""
    echo "Test it:"
    echo "  curl https://solar-weather-api-715107904640.asia-southeast1.run.app/stats"
else
    echo ""
    echo "❌ Failed to create view"
    echo "You can create it manually in BigQuery Console:"
    echo "https://console.cloud.google.com/bigquery?project=trim-descent-452802-t2"
fi
