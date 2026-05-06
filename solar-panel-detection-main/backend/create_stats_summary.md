# Create stats_summary Materialized View

## Purpose
Pre-aggregate statistics for fast `/stats` endpoint response (< 400ms target)

## Instructions

1. Go to BigQuery Console: https://console.cloud.google.com/bigquery?project=trim-descent-452802-t2

2. Select location: **asia-southeast1**

3. Run this SQL:

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS `trim-descent-452802-t2.openbuildings.stats_summary`
OPTIONS(
    enable_refresh=true,
    refresh_interval_minutes=1440,
    description="Materialized view for fast statistics queries",
    labels=[("purpose", "stats"), ("version", "v1")]
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
FROM `trim-descent-452802-t2.openbuildings.thailand_raw`;
```

4. Wait for initial materialization (~2-5 minutes for 107M records)

5. View will auto-refresh daily

## Benefits
- `/stats` endpoint: ~5000ms → ~200ms (25x faster)
- Reduced BigQuery costs (cached aggregations)
- Automatic daily updates

## Status
- ⏳ Not created yet
- API currently queries raw table directly (slower but functional)
