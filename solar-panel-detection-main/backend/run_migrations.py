#!/usr/bin/env python3
"""
BigQuery Migration Runner
Executes database migrations for the Solar Potential Platform
"""

import os
import sys
from pathlib import Path
from google.cloud import bigquery
from google.api_core import exceptions
import time

# Project configuration
PROJECT_ID = "trim-descent-452802-t2"
DATASET_ID = "openbuildings"

# Migration files in order
MIGRATIONS = [
    "001_create_rankings_cache.sql",
    "002_create_stats_summary_view.sql",
    "003_create_permitting_data.sql",
]

def get_bigquery_client():
    """Initialize BigQuery client"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        return client
    except Exception as e:
        print(f"❌ Failed to initialize BigQuery client: {e}")
        sys.exit(1)

def run_migration(client: bigquery.Client, migration_file: str) -> bool:
    """Run a single migration file"""
    migrations_dir = Path(__file__).parent / "migrations"
    migration_path = migrations_dir / migration_file
    
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Running migration: {migration_file}")
    print(f"{'='*60}")
    
    try:
        # Read migration SQL
        with open(migration_path, 'r') as f:
            query = f.read()
        
        # Execute query
        print(f"Executing SQL...")
        query_job = client.query(query)
        
        # Wait for completion
        result = query_job.result()
        
        print(f"✓ Migration {migration_file} completed successfully")
        return True
        
    except exceptions.GoogleAPIError as e:
        print(f"❌ BigQuery API error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_table_exists(client: bigquery.Client, table_id: str) -> bool:
    """Verify that a table exists"""
    try:
        client.get_table(table_id)
        return True
    except exceptions.NotFound:
        return False
    except Exception as e:
        print(f"❌ Error checking table {table_id}: {e}")
        return False

def verify_view_exists(client: bigquery.Client, view_id: str) -> bool:
    """Verify that a materialized view exists"""
    try:
        view = client.get_table(view_id)
        return view.table_type == "MATERIALIZED_VIEW"
    except exceptions.NotFound:
        return False
    except Exception as e:
        print(f"❌ Error checking view {view_id}: {e}")
        return False

def verify_migrations(client: bigquery.Client) -> bool:
    """Verify all migrations were successful"""
    print(f"\n{'='*60}")
    print("Verifying migrations...")
    print(f"{'='*60}")
    
    all_verified = True
    
    # Check rankings_cache table
    rankings_table = f"{PROJECT_ID}.{DATASET_ID}.rankings_cache"
    print(f"\nChecking table: {rankings_table}")
    if verify_table_exists(client, rankings_table):
        print(f"✓ Table exists: rankings_cache")
        
        # Check table schema
        table = client.get_table(rankings_table)
        print(f"  - Partitioning: {table.time_partitioning}")
        print(f"  - Clustering: {table.clustering_fields}")
        print(f"  - Rows: {table.num_rows}")
    else:
        print(f"❌ Table not found: rankings_cache")
        all_verified = False
    
    # Check stats_summary view
    stats_view = f"{PROJECT_ID}.{DATASET_ID}.stats_summary"
    print(f"\nChecking materialized view: {stats_view}")
    if verify_view_exists(client, stats_view):
        print(f"✓ Materialized view exists: stats_summary")
        
        # Check view details
        view = client.get_table(stats_view)
        print(f"  - Type: {view.table_type}")
        print(f"  - Rows: {view.num_rows}")
        
        # Query the view to verify it works
        try:
            query = f"SELECT * FROM `{stats_view}` LIMIT 1"
            result = client.query(query).result()
            print(f"✓ View is queryable")
        except Exception as e:
            print(f"❌ View query failed: {e}")
            all_verified = False
    else:
        print(f"❌ Materialized view not found: stats_summary")
        all_verified = False
    
    # Check permitting_data table
    permitting_table = f"{PROJECT_ID}.{DATASET_ID}.permitting_data"
    print(f"\nChecking table: {permitting_table}")
    if verify_table_exists(client, permitting_table):
        print(f"✓ Table exists: permitting_data")
        
        # Check table schema
        table = client.get_table(permitting_table)
        print(f"  - Clustering: {table.clustering_fields}")
        print(f"  - Rows: {table.num_rows}")
    else:
        print(f"❌ Table not found: permitting_data")
        all_verified = False
    
    return all_verified

def verify_clustering(client: bigquery.Client) -> bool:
    """Verify clustering is applied to main table"""
    print(f"\n{'='*60}")
    print("Verifying table clustering...")
    print(f"{'='*60}")
    
    main_table = f"{PROJECT_ID}.{DATASET_ID}.thailand_raw"
    print(f"\nChecking main table: {main_table}")
    
    try:
        table = client.get_table(main_table)
        
        if table.clustering_fields:
            print(f"✓ Clustering is applied")
            print(f"  - Clustering fields: {table.clustering_fields}")
        else:
            print(f"⚠ No clustering applied to main table")
            print(f"  - Consider running: ALTER TABLE `{main_table}` CLUSTER BY confidence, area_in_meters, latitude, longitude")
        
        return True
        
    except exceptions.NotFound:
        print(f"❌ Main table not found: {main_table}")
        return False
    except Exception as e:
        print(f"❌ Error checking clustering: {e}")
        return False

def test_query_performance(client: bigquery.Client) -> bool:
    """Test query performance on key endpoints"""
    print(f"\n{'='*60}")
    print("Testing query performance...")
    print(f"{'='*60}")
    
    # Test stats query
    print(f"\nTest 1: Stats query (using materialized view)")
    stats_view = f"{PROJECT_ID}.{DATASET_ID}.stats_summary"
    query = f"SELECT * FROM `{stats_view}`"
    
    try:
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
        return False
    
    # Test bbox query with filters
    print(f"\nTest 2: Bbox query with filters")
    main_table = f"{PROJECT_ID}.{DATASET_ID}.thailand_raw"
    query = f"""
    SELECT COUNT(*) as count
    FROM `{main_table}`
    WHERE latitude BETWEEN 13.0 AND 14.0
      AND longitude BETWEEN 100.0 AND 101.0
      AND confidence >= 0.7
      AND area_in_meters >= 50
    """
    
    try:
        start_time = time.time()
        result = client.query(query).result()
        duration_ms = (time.time() - start_time) * 1000
        
        for row in result:
            print(f"  - Matching buildings: {row.count}")
        
        print(f"✓ Query completed in {duration_ms:.2f}ms")
        
        if duration_ms < 600:
            print(f"✓ Performance target met (< 600ms)")
        else:
            print(f"⚠ Performance target not met (> 600ms)")
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False
    
    return True

def main():
    """Main migration runner"""
    print(f"\n{'='*60}")
    print("BigQuery Migration Runner")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    print(f"{'='*60}")
    
    # Initialize client
    client = get_bigquery_client()
    
    # Run migrations
    success_count = 0
    for migration_file in MIGRATIONS:
        if run_migration(client, migration_file):
            success_count += 1
        else:
            print(f"\n❌ Migration failed: {migration_file}")
            print("Stopping migration process.")
            sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"✓ All {success_count}/{len(MIGRATIONS)} migrations completed successfully")
    print(f"{'='*60}")
    
    # Verify migrations
    if verify_migrations(client):
        print(f"\n✓ All migrations verified successfully")
    else:
        print(f"\n❌ Some migrations failed verification")
        sys.exit(1)
    
    # Verify clustering
    verify_clustering(client)
    
    # Test query performance
    test_query_performance(client)
    
    print(f"\n{'='*60}")
    print("✓ Migration process completed successfully")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
