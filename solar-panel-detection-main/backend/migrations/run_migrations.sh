#!/bin/bash
# BigQuery Migration Runner Script
# Run this script to execute all migrations

set -e  # Exit on error

PROJECT_ID="trim-descent-452802-t2"
DATASET_ID="openbuildings"

echo "============================================================"
echo "BigQuery Migration Runner"
echo "Project: $PROJECT_ID"
echo "Dataset: $DATASET_ID"
echo "============================================================"

# Function to run a migration
run_migration() {
    local migration_file=$1
    echo ""
    echo "============================================================"
    echo "Running migration: $migration_file"
    echo "============================================================"
    
    if [ ! -f "$migration_file" ]; then
        echo "❌ Migration file not found: $migration_file"
        exit 1
    fi
    
    if bq query --use_legacy_sql=false < "$migration_file"; then
        echo "✓ Migration $migration_file completed successfully"
    else
        echo "❌ Migration $migration_file failed"
        exit 1
    fi
}

# Run migrations in order
run_migration "001_create_rankings_cache.sql"
run_migration "002_create_stats_summary_view.sql"
run_migration "003_create_permitting_data.sql"

echo ""
echo "============================================================"
echo "✓ All migrations completed successfully"
echo "============================================================"

# Verify tables exist
echo ""
echo "============================================================"
echo "Verifying migrations..."
echo "============================================================"

echo ""
echo "Checking rankings_cache table..."
bq show "$PROJECT_ID:$DATASET_ID.rankings_cache" && echo "✓ Table exists" || echo "❌ Table not found"

echo ""
echo "Checking stats_summary view..."
bq show "$PROJECT_ID:$DATASET_ID.stats_summary" && echo "✓ View exists" || echo "❌ View not found"

echo ""
echo "Checking permitting_data table..."
bq show "$PROJECT_ID:$DATASET_ID.permitting_data" && echo "✓ Table exists" || echo "❌ Table not found"

echo ""
echo "============================================================"
echo "✓ Migration verification completed"
echo "============================================================"
