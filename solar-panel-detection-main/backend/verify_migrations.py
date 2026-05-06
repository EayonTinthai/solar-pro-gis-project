#!/usr/bin/env python3
"""
BigQuery Migration Verification Script
Verifies that all migrations have been applied successfully
"""

import os
import sys
from google.cloud import bigquery
from google.api_core import exceptions
import time

# Project configuration
PROJECT_ID = "trim-descent-452802-t2"
DATASET_ID = "openbuildings"

def get_bigquery_client():
    """Initialize BigQuery client"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        print(f"✓ Connected to BigQuery project: {PROJECT_ID}")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize BigQuery client: {e}")
        sys.exit(1)

def verify_table_exists(client: bigquery.Client, table_name: str) -> bool:
    """Verify that a table exists"""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    try:
        table = client.get_table(table_id)
        return True, table
    except exceptions.NotFound:
        return False, None
    except Exception as e:
        print(f"❌ Error checking table {table_name}: {e}")
        return False, None

def verify_view_exists(client: bigquery.Client, view_name: str) -> bool:
    """Verify that a materialized view exists"""
    view_id = f"{PROJECT_ID}.{DATASET_ID}.{view_name}"
    try:
        view = client.get_table(view_id)
        return view.table_type == "MATERIALIZED_VIEW", view
    except exceptions.NotFound:
        return False, None
    except Exception as e:
        print(f"❌ Error checking view {view_name}: {e}")
        return False, None

def main():
    """Main verification function"""
    print(f"\n{'='*60}")
    print("BigQuery Migration Verification")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    print(f"{'='*60}\n")
    
    # Initialize client
    client = get_bigquery_client()
    
    all_verified = True
    
    # Verify Migration 001: rankings_cache table
    print(f"\n{'='*60}")
    print("Migration 001: rankings_cache table")
    print(f"{'='*60}")
    
    exists, table = verify_table_exists(client, "rankings_cache")
    if exists:
        print(f"✓ Table exists: rankings_cache")
        print(f"  - Schema fields: {len(table.schema)}")
        print(f"  - Partitioning: {table.time_partitioning.type if table.time_partitioning else 'None'}")
        print(f"  - Clustering: {', '.join(table.clustering_fields) if table.clustering_fields else 'None'}")
        print(f"  - Rows: {table.num_rows}")
        print(f"  - Size: {table.num_bytes / 1024 / 1024:.2f} MB")
    else:
        print(f"❌ Table not found: rankings_cache")
        all_verified = False
    
    # Verify Migration 002: stats_summary view
    print(f"\n{'='*60}")
    print("Migration 002: stats_summary materialized view")
    print(f"{'='*60}")
    
    exists, view = verify_view_exists(client, "stats_summary")
    if exists:
        print(f"✓ Materialized view exists: stats_summary")
        print(f"  - Type: {view.table_type}")
        print(f"  - Schema fields: {len(view.schema)}")
        print(f"  - Rows: {view.num_rows}")
        print(f"  - Size: {view.num_bytes / 1024 / 1024:.2f} MB")
        
        # Test query the view
        try:
            query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.stats_summary` LIMIT 1"
            start_time = time.time()
            result = client.query(query).result()
            duration_ms = (time.time() - start_time) * 1000
            
            for row in result:
                print(f"  - Total buildings: {row.total_buildings:,}")
                print(f"  - Avg confidence: {row.avg_confidence:.3f}")
                print(f"  - Median confidence: {row.median_confidence:.3f}")
            
            print(f"✓ View is queryable (query time: {duration_ms:.2f}ms)")
        except Exception as e:
            print(f"❌ View query failed: {e}")
            all_verified = False
    else:
        print(f"❌ Materialized view not found: stats_summary")
        all_verified = False
    
    # Verify Migration 003: permitting_data table
    print(f"\n{'='*60}")
    print("Migration 003: permitting_data table")
    print(f"{'='*60}")
    
    exists, table = verify_table_exists(client, "permitting_data")
    if exists:
        print(f"✓ Table exists: permitting_data")
        print(f"  - Schema fields: {len(table.schema)}")
        print(f"  - Clustering: {', '.join(table.clustering_fields) if table.clustering_fields else 'None'}")
        print(f"  - Rows: {table.num_rows}")
        print(f"  - Size: {table.num_bytes / 1024 / 1024:.2f} MB")
        print(f"  - Status: Placeholder (ready for future data)")
    else:
        print(f"❌ Table not found: permitting_data")
        all_verified = False
    
    # Verify clustering on main table
    print(f"\n{'='*60}")
    print("Main Table Optimization")
    print(f"{'='*60}")
    
    exists, table = verify_table_exists(client, "thailand_raw")
    if exists:
        print(f"✓ Main table exists: thailand_raw")
        print(f"  - Rows: {table.num_rows:,}")
        print(f"  - Size: {table.num_bytes / 1024 / 1024 / 1024:.2f} GB")
        
        if table.clustering_fields:
            print(f"✓ Clustering is applied")
            print(f"  - Clustering fields: {', '.join(table.clustering_fields)}")
        else:
            print(f"⚠ No clustering applied")
            print(f"  - Recommendation: Apply clustering for better performance")
            print(f"  - Command: ALTER TABLE `{PROJECT_ID}.{DATASET_ID}.thailand_raw`")
            print(f"             CLUSTER BY confidence, area_in_meters, latitude, longitude")
    else:
        print(f"❌ Main table not found: thailand_raw")
        all_verified = False
    
    # Performance test
    print(f"\n{'='*60}")
    print("Performance Testing")
    print(f"{'='*60}")
    
    # Test 1: Stats query
    print(f"\nTest 1: Stats query (using materialized view)")
    try:
        query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.stats_summary`"
        start_time = time.time()
        result = client.query(query).result()
        duration_ms = (time.time() - start_time) * 1000
        
        print(f"✓ Query completed in {duration_ms:.2f}ms")
        
        if duration_ms < 600:
            print(f"✓ Performance target met (< 600ms)")
        else:
            print(f"⚠ Performance target not met (> 600ms)")
    except Exception as e:
        print(f"❌ Query failed: {e}")
        all_verified = False
    
    # Test 2: Filtered bbox query
    print(f"\nTest 2: Filtered bbox query")
    try:
        query = f"""
        SELECT COUNT(*) as count
        FROM `{PROJECT_ID}.{DATASET_ID}.thailand_raw`
        WHERE latitude BETWEEN 13.0 AND 14.0
          AND longitude BETWEEN 100.0 AND 101.0
          AND confidence >= 0.7
          AND area_in_meters >= 50
        """
        start_time = time.time()
        result = client.query(query).result()
        duration_ms = (time.time() - start_time) * 1000
        
        for row in result:
            print(f"  - Matching buildings: {row.count:,}")
        
        print(f"✓ Query completed in {duration_ms:.2f}ms")
        
        if duration_ms < 600:
            print(f"✓ Performance target met (< 600ms)")
        else:
            print(f"⚠ Performance target not met (> 600ms)")
    except Exception as e:
        print(f"❌ Query failed: {e}")
        all_verified = False
    
    # Final summary
    print(f"\n{'='*60}")
    if all_verified:
        print("✓ All migrations verified successfully")
        print(f"{'='*60}\n")
        return 0
    else:
        print("❌ Some migrations failed verification")
        print(f"{'='*60}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
