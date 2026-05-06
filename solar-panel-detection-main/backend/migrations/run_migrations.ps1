# BigQuery Migration Runner Script (PowerShell)
# Run this script to execute all migrations

$ErrorActionPreference = "Stop"

$PROJECT_ID = "trim-descent-452802-t2"
$DATASET_ID = "openbuildings"

Write-Host "============================================================"
Write-Host "BigQuery Migration Runner"
Write-Host "Project: $PROJECT_ID"
Write-Host "Dataset: $DATASET_ID"
Write-Host "============================================================"

# Function to run a migration
function Run-Migration {
    param (
        [string]$MigrationFile
    )
    
    Write-Host ""
    Write-Host "============================================================"
    Write-Host "Running migration: $MigrationFile"
    Write-Host "============================================================"
    
    if (-not (Test-Path $MigrationFile)) {
        Write-Host "❌ Migration file not found: $MigrationFile" -ForegroundColor Red
        exit 1
    }
    
    try {
        Get-Content $MigrationFile | bq query --use_legacy_sql=false
        Write-Host "✓ Migration $MigrationFile completed successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Migration $MigrationFile failed" -ForegroundColor Red
        Write-Host $_.Exception.Message
        exit 1
    }
}

# Run migrations in order
Run-Migration "001_create_rankings_cache.sql"
Run-Migration "002_create_stats_summary_view.sql"
Run-Migration "003_create_permitting_data.sql"

Write-Host ""
Write-Host "============================================================"
Write-Host "✓ All migrations completed successfully" -ForegroundColor Green
Write-Host "============================================================"

# Verify tables exist
Write-Host ""
Write-Host "============================================================"
Write-Host "Verifying migrations..."
Write-Host "============================================================"

Write-Host ""
Write-Host "Checking rankings_cache table..."
try {
    bq show "$PROJECT_ID`:$DATASET_ID.rankings_cache" | Out-Null
    Write-Host "✓ Table exists" -ForegroundColor Green
}
catch {
    Write-Host "❌ Table not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "Checking stats_summary view..."
try {
    bq show "$PROJECT_ID`:$DATASET_ID.stats_summary" | Out-Null
    Write-Host "✓ View exists" -ForegroundColor Green
}
catch {
    Write-Host "❌ View not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "Checking permitting_data table..."
try {
    bq show "$PROJECT_ID`:$DATASET_ID.permitting_data" | Out-Null
    Write-Host "✓ Table exists" -ForegroundColor Green
}
catch {
    Write-Host "❌ Table not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================"
Write-Host "✓ Migration verification completed" -ForegroundColor Green
Write-Host "============================================================"
