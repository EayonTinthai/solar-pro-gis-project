#!/usr/bin/env python3
"""Create stats_summary materialized view in BigQuery"""

from google.cloud import bigquery

def create_stats_view():
    client = bigquery.Client(project="trim-descent-452802-t2", location="asia-southeast1")
    
    query = """
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
    FROM `trim-descent-452802-t2.openbuildings.thailand_raw`
    """
    
    print("Creating stats_summary materialized view...")
    print("This may take a few minutes...")
    
    job = client.query(query)
    job.result()  # Wait for completion
    
    print("✅ Materialized view created successfully!")
    print("View: trim-descent-452802-t2.openbuildings.stats_summary")
    print("Refresh interval: Daily (1440 minutes)")

if __name__ == "__main__":
    create_stats_view()
