#!/usr/bin/env python3
"""
BigQuery Index and Optimization Verification Script
Verifies clustering, partitioning, and query performance
"""

import os
import sys
import time
from google.cloud import bigquery
from google.api_core import exceptions

# Project configuration
PROJECT_ID = "trim-descent-452802-t2"
DATASET_ID = "openbuildings"

# Performance targets (in milliseconds)
PERFORMANCE_TARGET_MS = 600

def get_bigquery_client():
    """Initialize BigQuery client"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        print(f"✓ Connected to BigQuery project: {PROJECT_ID}")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize BigQuery client: {e}")
        sys.exit(1)

def verify_table_clustering(client: bigquery.Client, table_name: str, expected_fields: list) -> bool:
    """Verify clustering on a table"""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    try:
        table = client.get_table(table_id)
        
        if table.clustering_fields:
            actual_fields = table.clustering_fields
            if set(actual_fields) == set(expected_fields):
                print(f"✓ Clustering verified: {', '.join(actual_fields)}")
                return True
            else:
                print(f"⚠ Clustering mismatch:")
                print(f"  Expected: {', '.join(expected_fields)}")
                print(f"  Actual: {', '.join(actual_fields)}")
                return False
        else:
            print(f"❌ No clustering applied")
            print(f"  Expected: {', '.join(expected_fields)}")
            return False
            
    except exceptions.NotFound:
        print(f"❌ Table not found: {table_name}")
        return False
    except Exception as e:
        print(f"❌ Error checking clustering: {e}")
        return False

def verify_table_partitioning(client: bigquery.Client, table_name: str, expected_field: str) -> bool:
    """Verify partitioning on a table"""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    try:
        table = client.get_table(table_id)
        
        if table.time_partitioning:
            partition_type = table.time_partitioning.type_
            partition_field = table.time_partitioning.field
            
            if partition_field == expected_field:
                print(f"✓ Partitioning verified: {partition_type} on {partition_field}")
                return True
            else:
                print(f"⚠ Partitioning mismatch:")
                print(f"  Expected field: {expected_field}")
                print(f"  Actual field: {partition_field}")
                return False
        else:
            print(f"❌ No partitioning applied")
            print(f"  Expected: {expected_field}")
            return False
            
    except exceptions.NotFound:
        print(f"❌ Table not found: {table_name}")
        return False
    except Exception as e:
        print(f"❌ Error checking partitioning: {e}")
        return False

def test_query_performance(client: bigquery.Client, query: str, description: str, target_ms: int = PERFORMANCE_TARGET_MS) -> tuple:
    """Test query performance"""
    try:
        start_time = time.time()
        query_job = client.query(query)
        result = query_job.result()
        duration_ms = (time.time() - start_time) * 1000
        
        # Get result count
        row_count = 0
        for row in result:
            row_count += 1
        
        meets_target = duration_ms < target_ms
        
        return True, duration_ms, meets_target, row_count
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False, 0, False, 0

def get_query_execution_plan(client: bigquery.Client, query: str) -> dict:
    """Get query execution plan for analysis"""
    try:
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        query_job = client.query(query, job_config=job_config)
        
        return {
            "total_bytes_processed": query_job.total_bytes_processed,
            "total_bytes_billed": query_job.total_bytes_billed,
            "estimated_cost_usd": (query_job.total_bytes_billed / 1024**4) * 5  # $5 per TB
        }
    except Exception as e:
        print(f"⚠ Could not get execution plan: {e}")
        return None

def main():
    """Main verification function"""
    print(f"\n{'='*70}")
    print("BigQuery Index and Optimization Verification")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    print(f"Performance Target: < {PERFORMANCE_TARGET_MS}ms")
    print(f"{'='*70}\n")
    
    # Initialize client
    client = get_bigquery_client()
    
    all_verified = True
    
    # ========================================
    # 1. Verify rankings_cache clustering
    # ========================================
    print(f"\n{'='*70}")
    print("1. Verify rankings_cache Clustering")
    print(f"{'='*70}")
    
    expected_clustering = ["scope_type", "scope_value", "ranking_position"]
    if not verify_table_clustering(client, "rankings_cache", expected_clustering):
        all_verified = False
    
    # Verify partitioning
    if not verify_table_partitioning(client, "rankings_cache", "calculated_at"):
        all_verified = False
    
    # ========================================
    # 2. Verify permitting_data clustering
    # ========================================
    print(f"\n{'='*70}")
    print("2. Verify permitting_data Clustering")
    print(f"{'='*70}")
    
    expected_clustering = ["latitude", "longitude"]
    if not verify_table_clustering(client, "permitting_data", expected_clustering):
        all_verified = False
    
    # ========================================
    # 3. Verify main table optimization
    # ========================================
    print(f"\n{'='*70}")
    print("3. Verify thailand_raw Table Optimization")
    print(f"{'='*70}")
    
    table_id = f"{PROJECT_ID}.{DATASET_ID}.thailand_raw"
    try:
        table = client.get_table(table_id)
        
        print(f"Table: thailand_raw")
        print(f"  - Rows: {table.num_rows:,}")
        print(f"  - Size: {table.num_bytes / 1024 / 1024 / 1024:.2f} GB")
        
        if table.clustering_fields:
            print(f"✓ Clustering is applied")
            print(f"  - Fields: {', '.join(table.clustering_fields)}")
            
            # Check if recommended fields are present
            recommended = ["confidence", "area_in_meters", "latitude", "longitude"]
            actual = table.clustering_fields
            
            if set(actual) >= set(recommended):
                print(f"✓ All recommended clustering fields present")
            else:
                missing = set(recommended) - set(actual)
                print(f"⚠ Missing recommended fields: {', '.join(missing)}")
        else:
            print(f"⚠ No clustering applied to main table")
            print(f"  Recommendation: Apply clustering for better performance")
            print(f"  Command: ALTER TABLE `{table_id}`")
            print(f"           CLUSTER BY confidence, area_in_meters, latitude, longitude")
            all_verified = False
            
    except exceptions.NotFound:
        print(f"❌ Main table not found: thailand_raw")
        all_verified = False
    except Exception as e:
        print(f"❌ Error checking main table: {e}")
        all_verified = False
    
    # ========================================
    # 4. Test Query Performance
    # ========================================
    print(f"\n{'='*70}")
    print("4. Query Performance Testing")
    print(f"{'='*70}")
    
    # Test 1: Stats query using materialized view
    print(f"\nTest 1: Stats Query (Materialized View)")
    print("-" * 70)
    
    query1 = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.stats_summary`"
    
    # Get execution plan
    plan = get_query_execution_plan(client, query1)
    if plan:
        print(f"Execution Plan:")
        print(f"  - Bytes to process: {plan['total_bytes_processed'] / 1024 / 1024:.2f} MB")
        print(f"  - Estimated cost: ${plan['estimated_cost_usd']:.6f}")
    
    # Execute query
    success, duration_ms, meets_target, row_count = test_query_performance(
        client, query1, "Stats query"
    )
    
    if success:
        print(f"✓ Query executed successfully")
        print(f"  - Duration: {duration_ms:.2f}ms")
        print(f"  - Rows returned: {row_count}")
        
        if meets_target:
            print(f"✓ Performance target met (< {PERFORMANCE_TARGET_MS}ms)")
        else:
            print(f"❌ Performance target not met (> {PERFORMANCE_TARGET_MS}ms)")
            all_verified = False
    else:
        all_verified = False
    
    # Test 2: Filtered bbox query
    print(f"\nTest 2: Filtered Bbox Query")
    print("-" * 70)
    
    query2 = f"""
    SELECT 
        latitude,
        longitude,
        area_in_meters,
        confidence
    FROM `{PROJECT_ID}.{DATASET_ID}.thailand_raw`
    WHERE latitude BETWEEN 13.0 AND 14.0
      AND longitude BETWEEN 100.0 AND 101.0
      AND confidence >= 0.7
      AND area_in_meters >= 50
    LIMIT 1000
    """
    
    # Get execution plan
    plan = get_query_execution_plan(client, query2)
    if plan:
        print(f"Execution Plan:")
        print(f"  - Bytes to process: {plan['total_bytes_processed'] / 1024 / 1024:.2f} MB")
        print(f"  - Estimated cost: ${plan['estimated_cost_usd']:.6f}")
    
    # Execute query
    success, duration_ms, meets_target, row_count = test_query_performance(
        client, query2, "Filtered bbox query"
    )
    
    if success:
        print(f"✓ Query executed successfully")
        print(f"  - Duration: {duration_ms:.2f}ms")
        print(f"  - Rows returned: {row_count}")
        
        if meets_target:
            print(f"✓ Performance target met (< {PERFORMANCE_TARGET_MS}ms)")
        else:
            print(f"❌ Performance target not met (> {PERFORMANCE_TARGET_MS}ms)")
            all_verified = False
    else:
        all_verified = False
    
    # Test 3: Count query with filters
    print(f"\nTest 3: Count Query with Filters")
    print("-" * 70)
    
    query3 = f"""
    SELECT COUNT(*) as count
    FROM `{PROJECT_ID}.{DATASET_ID}.thailand_raw`
    WHERE confidence >= 0.8
      AND area_in_meters BETWEEN 100 AND 500
    """
    
    # Get execution plan
    plan = get_query_execution_plan(client, query3)
    if plan:
        print(f"Execution Plan:")
        print(f"  - Bytes to process: {plan['total_bytes_processed'] / 1024 / 1024:.2f} MB")
        print(f"  - Estimated cost: ${plan['estimated_cost_usd']:.6f}")
    
    # Execute query
    success, duration_ms, meets_target, row_count = test_query_performance(
        client, query3, "Count query"
    )
    
    if success:
        print(f"✓ Query executed successfully")
        print(f"  - Duration: {duration_ms:.2f}ms")
        
        if meets_target:
            print(f"✓ Performance target met (< {PERFORMANCE_TARGET_MS}ms)")
        else:
            print(f"❌ Performance target not met (> {PERFORMANCE_TARGET_MS}ms)")
            all_verified = False
    else:
        all_verified = False
    
    # Test 4: Spatial query
    print(f"\nTest 4: Spatial Query")
    print("-" * 70)
    
    query4 = f"""
    SELECT 
        latitude,
        longitude,
        area_in_meters,
        confidence
    FROM `{PROJECT_ID}.{DATASET_ID}.thailand_raw`
    WHERE ST_DISTANCE(
        ST_GEOGPOINT(longitude, latitude),
        ST_GEOGPOINT(100.5018, 13.7563)
    ) < 5000
    AND confidence >= 0.7
    LIMIT 100
    """
    
    # Get execution plan
    plan = get_query_execution_plan(client, query4)
    if plan:
        print(f"Execution Plan:")
        print(f"  - Bytes to process: {plan['total_bytes_processed'] / 1024 / 1024:.2f} MB")
        print(f"  - Estimated cost: ${plan['estimated_cost_usd']:.6f}")
    
    # Execute query
    success, duration_ms, meets_target, row_count = test_query_performance(
        client, query4, "Spatial query", target_ms=1000  # More lenient for spatial
    )
    
    if success:
        print(f"✓ Query executed successfully")
        print(f"  - Duration: {duration_ms:.2f}ms")
        print(f"  - Rows returned: {row_count}")
        
        if meets_target:
            print(f"✓ Performance target met (< 1000ms)")
        else:
            print(f"⚠ Performance could be improved (> 1000ms)")
    else:
        all_verified = False
    
    # ========================================
    # 5. Summary and Recommendations
    # ========================================
    print(f"\n{'='*70}")
    print("5. Summary and Recommendations")
    print(f"{'='*70}\n")
    
    if all_verified:
        print("✓ All optimizations verified successfully")
        print("\nAll tables have proper clustering and partitioning.")
        print("Query performance meets targets.")
    else:
        print("⚠ Some optimizations need attention")
        print("\nRecommendations:")
        print("1. Apply clustering to tables without it")
        print("2. Monitor query performance in production")
        print("3. Consider additional indexes if performance degrades")
        print("4. Review query execution plans for optimization opportunities")
    
    print(f"\n{'='*70}")
    print("Verification Complete")
    print(f"{'='*70}\n")
    
    return 0 if all_verified else 1

if __name__ == "__main__":
    sys.exit(main())
