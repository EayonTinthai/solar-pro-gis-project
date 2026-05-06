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
