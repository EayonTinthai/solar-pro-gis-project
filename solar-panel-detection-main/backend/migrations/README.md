# BigQuery Migrations

This directory contains SQL migration files for the Solar Potential Platform backend.

## Migration Files

| File | Purpose | Requirements |
|------|---------|--------------|
| `001_create_rankings_cache.sql` | Create rankings cache table with partitioning | 7, 11, 14 |
| `002_create_stats_summary_view.sql` | Create materialized view for statistics | 2, 14, 15 |
| `003_create_permitting_data.sql` | Create permitting data table (placeholder) | 6, 11 |
| `004_create_indexes.sql` | Documentation for clustering strategy | 3, 14 |

## How to Run Migrations

### Option 1: Using bq command-line tool

```bash
# Set your project
export PROJECT_ID="trim-descent-452802-t2"

# Run each migration
bq query --use_legacy_sql=false < migrations/001_create_rankings_cache.sql
bq query --use_legacy_sql=false < migrations/002_create_stats_summary_view.sql
bq query --use_legacy_sql=false < migrations/003_create_permitting_data.sql
```

### Option 2: Using Google Cloud Console

1. Go to BigQuery in Google Cloud Console
2. Open the SQL workspace
3. Copy and paste each migration file
4. Click "Run"

### Option 3: Using Python script

```python
from google.cloud import bigquery
import os

client = bigquery.Client(project="trim-descent-452802-t2")

migrations = [
    "001_create_rankings_cache.sql",
    "002_create_stats_summary_view.sql",
    "003_create_permitting_data.sql"
]

for migration_file in migrations:
    with open(f"migrations/{migration_file}", "r") as f:
        query = f.read()
        print(f"Running {migration_file}...")
        query_job = client.query(query)
        query_job.result()
        print(f"✓ {migration_file} completed")
```

## Quick Start

### Automated Migration (Recommended)

**Using PowerShell (Windows):**
```powershell
cd migrations
.\run_migrations.ps1
```

**Using Bash (Linux/Mac):**
```bash
cd migrations
chmod +x run_migrations.sh
./run_migrations.sh
```

**Using Python:**
```bash
cd ..
python run_migrations.py
```

### Verification

After running migrations, verify they were successful:

```bash
python verify_migrations.py
```

This will check:
- All tables and views exist
- Clustering is applied
- Query performance meets targets

## Migration Status

- [ ] 001_create_rankings_cache.sql
- [ ] 002_create_stats_summary_view.sql
- [ ] 003_create_permitting_data.sql
- [ ] 004_create_indexes.sql (documentation only)

## Notes

- BigQuery uses clustering instead of traditional indexes
- Materialized views refresh automatically based on configured interval
- Partitioning helps with query performance and cost optimization
- All migrations are idempotent (safe to run multiple times)

## Rollback

To rollback migrations:

```bash
# Drop tables/views
bq rm -f -t trim-descent-452802-t2.openbuildings.rankings_cache
bq rm -f -m trim-descent-452802-t2.openbuildings.stats_summary
bq rm -f -t trim-descent-452802-t2.openbuildings.permitting_data
```
