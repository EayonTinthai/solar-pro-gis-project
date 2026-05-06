# Manual Migration Guide

This guide provides step-by-step instructions for running BigQuery migrations manually through the Google Cloud Console.

## Prerequisites

- Access to Google Cloud Console
- Permissions to create tables and views in BigQuery
- Project: `trim-descent-452802-t2`
- Dataset: `openbuildings`

## Step-by-Step Instructions

### Migration 001: Create rankings_cache Table

1. Open [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **BigQuery** from the menu
3. Select project: `trim-descent-452802-t2`
4. Click **"Compose New Query"**
5. Copy and paste the contents of `001_create_rankings_cache.sql`
6. Click **"Run"**
7. Verify success: You should see "Query complete" message
8. Verify table exists:
   - In the Explorer panel, expand `trim-descent-452802-t2` > `openbuildings`
   - You should see `rankings_cache` table

**Expected Result:**
```
Table created: rankings_cache
- Partitioned by: calculated_at (daily)
- Clustered by: scope_type, scope_value, ranking_position
- Rows: 0 (empty table, ready for data)
```

### Migration 002: Create stats_summary Materialized View

1. In BigQuery console, click **"Compose New Query"**
2. Copy and paste the contents of `002_create_stats_summary_view.sql`
3. Click **"Run"**
4. Wait for the view to be created (may take 1-2 minutes)
5. Verify success: You should see "Query complete" message
6. Verify view exists:
   - In the Explorer panel, expand `trim-descent-452802-t2` > `openbuildings`
   - You should see `stats_summary` with a view icon

**Expected Result:**
```
Materialized view created: stats_summary
- Type: MATERIALIZED_VIEW
- Refresh interval: 1440 minutes (daily)
- Rows: 1 (aggregated statistics)
```

**Test the view:**
```sql
SELECT * FROM `trim-descent-452802-t2.openbuildings.stats_summary`;
```

You should see aggregated statistics including:
- total_buildings
- avg_confidence, median_confidence, std_dev_confidence
- avg_area, median_area, std_dev_area
- Geographic extent (min/max lat/lon)

### Migration 003: Create permitting_data Table

1. In BigQuery console, click **"Compose New Query"**
2. Copy and paste the contents of `003_create_permitting_data.sql`
3. Click **"Run"**
4. Verify success: You should see "Query complete" message
5. Verify table exists:
   - In the Explorer panel, expand `trim-descent-452802-t2` > `openbuildings`
   - You should see `permitting_data` table

**Expected Result:**
```
Table created: permitting_data
- Clustered by: latitude, longitude
- Rows: 0 (empty table, placeholder for future data)
```

### Migration 004: Verify Clustering (Documentation Only)

This migration is documentation only. It describes the clustering strategy for the main table.

**Optional: Apply clustering to main table**

If the main table (`thailand_raw`) doesn't have clustering applied, you can apply it with:

```sql
ALTER TABLE `trim-descent-452802-t2.openbuildings.thailand_raw`
CLUSTER BY confidence, area_in_meters, latitude, longitude;
```

**Note:** This operation may take several minutes for large tables.

## Verification Steps

### 1. Verify All Tables Exist

Run this query to list all tables:

```sql
SELECT 
  table_name,
  table_type,
  ROUND(size_bytes / 1024 / 1024, 2) as size_mb,
  row_count
FROM `trim-descent-452802-t2.openbuildings.__TABLES__`
WHERE table_name IN ('rankings_cache', 'stats_summary', 'permitting_data', 'thailand_raw')
ORDER BY table_name;
```

**Expected output:**
- rankings_cache (TABLE)
- stats_summary (MATERIALIZED_VIEW)
- permitting_data (TABLE)
- thailand_raw (TABLE)

### 2. Verify Clustering

Check clustering on rankings_cache:

```sql
SELECT 
  table_name,
  clustering_fields
FROM `trim-descent-452802-t2.openbuildings.INFORMATION_SCHEMA.TABLES`
WHERE table_name = 'rankings_cache';
```

**Expected:** `["scope_type", "scope_value", "ranking_position"]`

### 3. Test Query Performance

Test stats query performance:

```sql
SELECT * FROM `trim-descent-452802-t2.openbuildings.stats_summary`;
```

**Expected:** Query completes in < 600ms

Test filtered bbox query:

```sql
SELECT COUNT(*) as count
FROM `trim-descent-452802-t2.openbuildings.thailand_raw`
WHERE latitude BETWEEN 13.0 AND 14.0
  AND longitude BETWEEN 100.0 AND 101.0
  AND confidence >= 0.7
  AND area_in_meters >= 50;
```

**Expected:** Query completes in < 600ms

## Troubleshooting

### Error: "Table already exists"

If you see this error, the migration has already been run. You can:
1. Skip this migration (it's already complete)
2. Or drop the table first: `DROP TABLE IF EXISTS <table_name>`

### Error: "Permission denied"

You need the following IAM roles:
- `roles/bigquery.dataEditor` - To create tables
- `roles/bigquery.jobUser` - To run queries

Contact your GCP administrator to grant these permissions.

### Error: "Dataset not found"

Verify the dataset exists:
```sql
SELECT * FROM `trim-descent-452802-t2.openbuildings.__TABLES__` LIMIT 1;
```

If the dataset doesn't exist, create it first:
```sql
CREATE SCHEMA IF NOT EXISTS `trim-descent-452802-t2.openbuildings`;
```

### Materialized View Not Refreshing

Check the view's refresh status:

```sql
SELECT 
  table_name,
  option_name,
  option_value
FROM `trim-descent-452802-t2.openbuildings.INFORMATION_SCHEMA.TABLE_OPTIONS`
WHERE table_name = 'stats_summary'
  AND option_name IN ('enable_refresh', 'refresh_interval_minutes');
```

To manually refresh:
```sql
CALL BQ.REFRESH_MATERIALIZED_VIEW('trim-descent-452802-t2.openbuildings.stats_summary');
```

## Rollback Instructions

If you need to rollback the migrations:

### Drop rankings_cache table:
```sql
DROP TABLE IF EXISTS `trim-descent-452802-t2.openbuildings.rankings_cache`;
```

### Drop stats_summary view:
```sql
DROP MATERIALIZED VIEW IF EXISTS `trim-descent-452802-t2.openbuildings.stats_summary`;
```

### Drop permitting_data table:
```sql
DROP TABLE IF EXISTS `trim-descent-452802-t2.openbuildings.permitting_data`;
```

## Post-Migration Checklist

- [ ] All 3 migrations executed successfully
- [ ] All tables/views visible in BigQuery Explorer
- [ ] stats_summary view returns data
- [ ] Query performance meets targets (< 600ms)
- [ ] Clustering is applied to rankings_cache
- [ ] No errors in BigQuery logs

## Next Steps

After successful migration:

1. Update the migration status in `README.md`
2. Run the verification script: `python verify_migrations.py`
3. Test the API endpoints that use these tables
4. Monitor query performance in production

## Support

For issues or questions:
- Check BigQuery logs in Cloud Console
- Review the main README.md for additional documentation
- Contact the development team
