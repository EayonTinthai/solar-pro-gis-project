# Migration Execution Checklist

Use this checklist to track migration execution and verification.

## Pre-Migration Checklist

- [ ] Access to Google Cloud Console confirmed
- [ ] BigQuery permissions verified (dataEditor, jobUser)
- [ ] Project ID confirmed: `trim-descent-452802-t2`
- [ ] Dataset confirmed: `openbuildings`
- [ ] Backup strategy reviewed (if needed)

## Migration Execution

### Migration 001: rankings_cache Table

**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Complete | ⬜ Failed

**Execution Method:** ⬜ Console | ⬜ bq CLI | ⬜ Python Script

**Steps:**
- [ ] Open `001_create_rankings_cache.sql`
- [ ] Execute SQL in BigQuery
- [ ] Verify table created
- [ ] Check partitioning: `DATE(calculated_at)`
- [ ] Check clustering: `scope_type, scope_value, ranking_position`
- [ ] Verify index created: `idx_rankings_expires`

**Verification Query:**
```sql
SELECT 
  table_name,
  table_type,
  row_count,
  ROUND(size_bytes / 1024 / 1024, 2) as size_mb
FROM `trim-descent-452802-t2.openbuildings.__TABLES__`
WHERE table_name = 'rankings_cache';
```

**Expected Result:** Table exists with 0 rows

**Notes:**
```
[Add any notes or issues encountered]
```

---

### Migration 002: stats_summary Materialized View

**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Complete | ⬜ Failed

**Execution Method:** ⬜ Console | ⬜ bq CLI | ⬜ Python Script

**Steps:**
- [ ] Open `002_create_stats_summary_view.sql`
- [ ] Execute SQL in BigQuery
- [ ] Wait for view creation (1-2 minutes)
- [ ] Verify view created
- [ ] Check refresh interval: 1440 minutes (daily)
- [ ] Test query: `SELECT * FROM stats_summary`

**Verification Query:**
```sql
SELECT * FROM `trim-descent-452802-t2.openbuildings.stats_summary`;
```

**Expected Result:** 1 row with aggregated statistics

**Sample Output:**
```
total_buildings: 107,682,789
avg_confidence: 0.787
median_confidence: 0.812
avg_area: 96.1
median_area: 78.5
```

**Notes:**
```
[Add any notes or issues encountered]
```

---

### Migration 003: permitting_data Table

**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Complete | ⬜ Failed

**Execution Method:** ⬜ Console | ⬜ bq CLI | ⬜ Python Script

**Steps:**
- [ ] Open `003_create_permitting_data.sql`
- [ ] Execute SQL in BigQuery
- [ ] Verify table created
- [ ] Check clustering: `latitude, longitude`
- [ ] Verify indexes created: `idx_permitting_status`, `idx_permitting_building`

**Verification Query:**
```sql
SELECT 
  table_name,
  table_type,
  row_count,
  ROUND(size_bytes / 1024 / 1024, 2) as size_mb
FROM `trim-descent-452802-t2.openbuildings.__TABLES__`
WHERE table_name = 'permitting_data';
```

**Expected Result:** Table exists with 0 rows (placeholder)

**Notes:**
```
[Add any notes or issues encountered]
```

---

### Migration 004: Clustering Documentation

**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Complete | ⬜ N/A

**Note:** This is documentation only, no SQL execution required.

**Optional: Apply clustering to main table**

- [ ] Check if `thailand_raw` has clustering
- [ ] If not, consider applying clustering (may take time)

**Check Clustering Query:**
```sql
SELECT 
  table_name,
  clustering_fields
FROM `trim-descent-452802-t2.openbuildings.INFORMATION_SCHEMA.TABLES`
WHERE table_name = 'thailand_raw';
```

**Apply Clustering (Optional):**
```sql
ALTER TABLE `trim-descent-452802-t2.openbuildings.thailand_raw`
CLUSTER BY confidence, area_in_meters, latitude, longitude;
```

**Notes:**
```
[Add any notes or issues encountered]
```

---

## Post-Migration Verification

### All Tables/Views Exist

- [ ] rankings_cache table exists
- [ ] stats_summary view exists
- [ ] permitting_data table exists

**Verification Query:**
```sql
SELECT 
  table_name,
  table_type,
  row_count,
  ROUND(size_bytes / 1024 / 1024, 2) as size_mb
FROM `trim-descent-452802-t2.openbuildings.__TABLES__`
WHERE table_name IN ('rankings_cache', 'stats_summary', 'permitting_data')
ORDER BY table_name;
```

### Clustering Verification

- [ ] rankings_cache has clustering
- [ ] permitting_data has clustering

**Verification Query:**
```sql
SELECT 
  table_name,
  clustering_fields
FROM `trim-descent-452802-t2.openbuildings.INFORMATION_SCHEMA.TABLES`
WHERE table_name IN ('rankings_cache', 'permitting_data')
ORDER BY table_name;
```

### Performance Testing

**Test 1: Stats Query**

- [ ] Query executes successfully
- [ ] Query completes in < 600ms
- [ ] Returns expected data

```sql
SELECT * FROM `trim-descent-452802-t2.openbuildings.stats_summary`;
```

**Execution Time:** _______ ms

**Test 2: Filtered Bbox Query**

- [ ] Query executes successfully
- [ ] Query completes in < 600ms
- [ ] Returns expected count

```sql
SELECT COUNT(*) as count
FROM `trim-descent-452802-t2.openbuildings.thailand_raw`
WHERE latitude BETWEEN 13.0 AND 14.0
  AND longitude BETWEEN 100.0 AND 101.0
  AND confidence >= 0.7
  AND area_in_meters >= 50;
```

**Execution Time:** _______ ms
**Result Count:** _______

### Index Verification

- [ ] idx_rankings_expires exists on rankings_cache
- [ ] idx_permitting_status exists on permitting_data
- [ ] idx_permitting_building exists on permitting_data

**Note:** BigQuery indexes may not be visible in INFORMATION_SCHEMA. Verify by checking query execution plans.

## Final Sign-Off

**Migration Completed By:** _______________________

**Date:** _______________________

**Time:** _______________________

**Overall Status:** ⬜ Success | ⬜ Partial Success | ⬜ Failed

**Issues Encountered:**
```
[List any issues or deviations from expected results]
```

**Next Steps:**
- [ ] Update migration status in README.md
- [ ] Notify team of completion
- [ ] Test API endpoints using new tables
- [ ] Monitor query performance in production
- [ ] Schedule ranking calculation job

## Rollback Plan (If Needed)

If rollback is required:

```sql
-- Drop tables/views in reverse order
DROP TABLE IF EXISTS `trim-descent-452802-t2.openbuildings.permitting_data`;
DROP MATERIALIZED VIEW IF EXISTS `trim-descent-452802-t2.openbuildings.stats_summary`;
DROP TABLE IF EXISTS `trim-descent-452802-t2.openbuildings.rankings_cache`;
```

**Rollback Executed:** ⬜ Yes | ⬜ No

**Rollback Reason:**
```
[If rollback was performed, explain why]
```
