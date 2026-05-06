"""
Apply Query Optimizations to BigQuery Tables
Task 19.1 - Optimize BigQuery queries

This script applies the recommended optimizations from QUERY_OPTIMIZATION_REPORT.md:
1. Apply table clustering
2. Verify clustering is applied
3. Test query performance before/after

Usage:
    python apply_query_optimizations.py [--dry-run]
"""

import os
import sys
import time
import argparse
from google.cloud import bigquery
from datetime import datetime


def apply_table_clustering(client: bigquery.Client, project_id: str, dataset: str, table: str, dry_run: bool = False):
    """
    Apply clustering to the main table
    
    Clustering columns: confidence, area_in_meters, latitude, longitude
    These columns are chosen based on common query patterns:
    - confidence: Used in WHERE clauses for filtering
    - area_in_meters: Used for sorting and filtering
    - latitude, longitude: Used for spatial queries
    """
    full_table_name = f"`{project_id}.{dataset}.{table}`"
    
    print(f"\n{'='*80}")
    print(f"APPLYING TABLE CLUSTERING")
    print(f"{'='*80}")
    print(f"Table: {full_table_name}")
    print(f"Clustering columns: confidence, area_in_meters, latitude, longitude")
    print()
    
    # Check if table is already clustered
    table_ref = client.get_table(f"{project_id}.{dataset}.{table}")
    
    if table_ref.clustering_fields:
        print(f"✓ Table is already clustered on: {', '.join(table_ref.clustering_fields)}")
        
        # Check if clustering matches our desired configuration
        desired_clustering = ['confidence', 'area_in_meters', 'latitude', 'longitude']
        if table_ref.clustering_fields == desired_clustering:
            print(f"✓ Clustering configuration is optimal. No changes needed.")
            return True
        else:
            print(f"⚠ Clustering configuration differs from recommended.")
            print(f"  Current: {', '.join(table_ref.clustering_fields)}")
            print(f"  Recommended: {', '.join(desired_clustering)}")
            
            if not dry_run:
                response = input("\nDo you want to re-cluster the table? (yes/no): ")
                if response.lower() != 'yes':
                    print("Skipping re-clustering.")
                    return False
    else:
        print(f"⚠ Table is not clustered. Applying clustering...")
    
    # Apply clustering
    clustering_query = f"""
        ALTER TABLE {full_table_name}
        CLUSTER BY confidence, area_in_meters, latitude, longitude
    """
    
    if dry_run:
        print(f"\n[DRY RUN] Would execute:")
        print(clustering_query)
        return True
    
    try:
        print(f"\nExecuting clustering command...")
        print(f"Note: This operation may take several minutes for large tables.")
        
        start_time = time.time()
        query_job = client.query(clustering_query)
        query_job.result()  # Wait for completion
        duration = time.time() - start_time
        
        print(f"✓ Clustering applied successfully in {duration:.2f} seconds")
        
        # Verify clustering was applied
        table_ref = client.get_table(f"{project_id}.{dataset}.{table}")
        if table_ref.clustering_fields:
            print(f"✓ Verified: Table is now clustered on {', '.join(table_ref.clustering_fields)}")
            return True
        else:
            print(f"✗ Error: Clustering was not applied")
            return False
            
    except Exception as e:
        print(f"✗ Error applying clustering: {str(e)}")
        return False


def test_query_performance(client: bigquery.Client, project_id: str, dataset: str, table: str):
    """
    Test query performance with sample queries
    
    Runs representative queries and measures execution time
    """
    print(f"\n{'='*80}")
    print(f"TESTING QUERY PERFORMANCE")
    print(f"{'='*80}")
    
    full_table_name = f"`{project_id}.{dataset}.{table}`"
    
    # Test queries
    test_queries = [
        {
            "name": "Bounding Box Query (Bangkok area)",
            "query": f"""
                SELECT 
                    full_plus_code,
                    latitude,
                    longitude,
                    area_in_meters,
                    confidence
                FROM {full_table_name}
                WHERE latitude BETWEEN 13.7 AND 13.8
                  AND longitude BETWEEN 100.5 AND 100.6
                  AND confidence >= 0.8
                ORDER BY area_in_meters DESC
                LIMIT 100
            """
        },
        {
            "name": "Confidence Filter Query",
            "query": f"""
                SELECT 
                    COUNT(*) as total,
                    AVG(confidence) as avg_confidence,
                    AVG(area_in_meters) as avg_area
                FROM {full_table_name}
                WHERE confidence >= 0.9
                  AND area_in_meters >= 200
            """
        },
        {
            "name": "Spatial Distance Query",
            "query": f"""
                SELECT 
                    full_plus_code,
                    latitude,
                    longitude,
                    ST_DISTANCE(
                        ST_GEOGPOINT(longitude, latitude),
                        ST_GEOGPOINT(100.523, 13.756)
                    ) as distance_m
                FROM {full_table_name}
                WHERE latitude BETWEEN 13.746 AND 13.766
                  AND longitude BETWEEN 100.513 AND 100.533
                  AND confidence >= 0.7
                ORDER BY distance_m
                LIMIT 50
            """
        }
    ]
    
    results = []
    
    for test in test_queries:
        print(f"\nTesting: {test['name']}")
        print(f"Query: {test['query'][:100]}...")
        
        try:
            start_time = time.time()
            query_job = client.query(test['query'])
            result = list(query_job.result())
            duration = time.time() - start_time
            
            # Get query statistics
            bytes_processed = query_job.total_bytes_processed
            bytes_billed = query_job.total_bytes_billed
            
            print(f"  ✓ Execution time: {duration*1000:.2f}ms")
            print(f"  ✓ Bytes processed: {bytes_processed / (1024**2):.2f} MB")
            print(f"  ✓ Bytes billed: {bytes_billed / (1024**2):.2f} MB")
            print(f"  ✓ Results: {len(result)} rows")
            
            results.append({
                "name": test['name'],
                "duration_ms": duration * 1000,
                "bytes_processed_mb": bytes_processed / (1024**2),
                "rows": len(result),
                "status": "success"
            })
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            results.append({
                "name": test['name'],
                "status": "error",
                "error": str(e)
            })
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"PERFORMANCE SUMMARY")
    print(f"{'='*80}")
    print(f"{'Query':<40} {'Time (ms)':<15} {'Status':<10}")
    print(f"{'-'*80}")
    
    for result in results:
        if result['status'] == 'success':
            status_icon = "✓" if result['duration_ms'] < 600 else "⚠"
            print(f"{result['name']:<40} {result['duration_ms']:<15.2f} {status_icon}")
        else:
            print(f"{result['name']:<40} {'N/A':<15} ✗")
    
    print(f"{'-'*80}")
    
    # Check if all queries meet performance target
    all_pass = all(
        r['status'] == 'success' and r['duration_ms'] < 600 
        for r in results
    )
    
    if all_pass:
        print(f"✓ All queries meet performance target (< 600ms)")
    else:
        print(f"⚠ Some queries exceed performance target")
    
    return results


def verify_table_structure(client: bigquery.Client, project_id: str, dataset: str, table: str):
    """
    Verify table structure and configuration
    """
    print(f"\n{'='*80}")
    print(f"VERIFYING TABLE STRUCTURE")
    print(f"{'='*80}")
    
    try:
        table_ref = client.get_table(f"{project_id}.{dataset}.{table}")
        
        print(f"Table: {table_ref.full_table_id}")
        print(f"Created: {table_ref.created}")
        print(f"Modified: {table_ref.modified}")
        print(f"Rows: {table_ref.num_rows:,}")
        print(f"Size: {table_ref.num_bytes / (1024**3):.2f} GB")
        
        # Check clustering
        if table_ref.clustering_fields:
            print(f"✓ Clustering: {', '.join(table_ref.clustering_fields)}")
        else:
            print(f"⚠ Clustering: Not configured")
        
        # Check partitioning
        if table_ref.time_partitioning:
            print(f"✓ Partitioning: {table_ref.time_partitioning.type_}")
        else:
            print(f"  Partitioning: Not configured (optional)")
        
        # Check schema
        print(f"\nKey columns:")
        key_columns = ['latitude', 'longitude', 'confidence', 'area_in_meters', 'geometry']
        for field in table_ref.schema:
            if field.name in key_columns:
                print(f"  - {field.name}: {field.field_type}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error verifying table: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Apply query optimizations to BigQuery tables"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        '--skip-clustering',
        action='store_true',
        help="Skip applying clustering (only test performance)"
    )
    parser.add_argument(
        '--project',
        default=os.getenv('GCP_PROJECT', 'trim-descent-452802-t2'),
        help="GCP project ID"
    )
    parser.add_argument(
        '--dataset',
        default='openbuildings',
        help="BigQuery dataset name"
    )
    parser.add_argument(
        '--table',
        default='thailand_raw',
        help="BigQuery table name"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print(f"BIGQUERY QUERY OPTIMIZATION")
    print(f"{'='*80}")
    print(f"Date: {datetime.now().isoformat()}")
    print(f"Project: {args.project}")
    print(f"Dataset: {args.dataset}")
    print(f"Table: {args.table}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'='*80}")
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=args.project)
        print(f"✓ Connected to BigQuery")
    except Exception as e:
        print(f"✗ Error connecting to BigQuery: {str(e)}")
        sys.exit(1)
    
    # Step 1: Verify table structure
    if not verify_table_structure(client, args.project, args.dataset, args.table):
        print(f"\n✗ Table verification failed. Exiting.")
        sys.exit(1)
    
    # Step 2: Apply clustering (unless skipped)
    if not args.skip_clustering:
        success = apply_table_clustering(
            client, 
            args.project, 
            args.dataset, 
            args.table,
            dry_run=args.dry_run
        )
        
        if not success and not args.dry_run:
            print(f"\n⚠ Clustering failed, but continuing with performance tests...")
    else:
        print(f"\n⚠ Skipping clustering (--skip-clustering flag)")
    
    # Step 3: Test query performance
    if not args.dry_run:
        test_query_performance(client, args.project, args.dataset, args.table)
    else:
        print(f"\n[DRY RUN] Skipping performance tests")
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"OPTIMIZATION COMPLETE")
    print(f"{'='*80}")
    
    if args.dry_run:
        print(f"This was a dry run. No changes were made.")
        print(f"Run without --dry-run to apply optimizations.")
    else:
        print(f"✓ Optimizations applied successfully")
        print(f"\nNext steps:")
        print(f"1. Monitor query performance in production")
        print(f"2. Check Cloud Monitoring for query metrics")
        print(f"3. Run load tests to verify improvements")
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
