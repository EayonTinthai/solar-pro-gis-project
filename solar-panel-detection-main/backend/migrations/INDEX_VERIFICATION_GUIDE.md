# Index and Optimization Verification Guide

This guide provides step-by-step instructions for verifying that clustering, partitioning, and query optimization are properly configured.

## Overview

BigQuery uses clustering and partitioning instead of traditional indexes. This guide helps verify:
1. Clustering is applied to all relevant tables
2. Partitioning is configured correctly
3. Query performance meets targets (< 600ms for p95)

## Prerequisites

- Access to Google Cloud Console
- BigQuery permissions
- Migrations 001-003 completed

## Verification Steps

### 1. Verify rankings_cache Clustering and Partitioning

**Check Clustering:**

```sql
SELECT 
  table_name,
  clustering_fields
FROM `trim-descent-452802-t2.openbuildings.INFORMATION_SCHEMA.TABLES`
WHERE table_name = 'rankings_cache';
```

**Expected Result:**
```
clustering_fields: ["scope_type", "scope_value", "ranking_position"]
```

**Check Partitioning:**

```sql
SELECT 
  table_name,
  partition_expiration_days,
  time_partitioning_type,
  time_partitioning_field
FROM `trim-descent-452802-t2.openbuildings.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'rankings_cache'
LIMIT 1;
```

**Expected Result:**
```
time_partitioning_type: DAY
time_partitioning_field: calculated_at
```

**Verification:** ⬜ Pass | ⬜ Fail

---

### 2. Verify permitting_data Clustering

**Check Clustering:**

```sql
SELECT 
  table_name,
  clustering_fields
FROM `trim-descent-452802-t2.openbuildings.INFORMATION_SCHEMA.TABLES`
WHERE table_name = 'permitting_data';
```

**Expected Result:**
```
clustering_fields: ["latitude", "longitude"]
```

**Verification:** ⬜ Pass | ⬜ Fail

---

### 3. Verify thailand_raw Table Optimization

**Check Current Clustering:**

```sql
SELECT 
  table_name,
  clustering_fields,
  row_count,
  ROUND(size_bytes / 1024 / 1024 / 1024, 2) as size_gb
FROM `trim-descent-452802-t2.openbuildings.INFORMATION_SCHEMA.TABLES`
WHERE table_name = 'thailand_raw';
```

**Recommended Clustering:**
```
["confidence", "area_in_meters", "latitude", "longitude"]
```

**If clustering is not applied or incomplete:**

```sql
-- Apply clustering (may take several minutes for large tables)
ALTER TABLE `trim-descent-452802-t2.openbuildings.thailand_raw`
CLUSTER BY confidence, area_in_meters, latitude, longitude;
```

**Verification:** ⬜ Pass | ⬜ Fail | ⬜ Applied Clustering

---

### 4. Test Query Performance

#### Test 1: Stats Query (Materialized View)

**Query:**
```sql
SELECT * FROM `trim-descent-452802-t2.openbuildings.stats_summary`;
```

**Performance Target:** < 600ms

**Steps:**
1. Open BigQuery console
2. Click "Compose New Query"
3. Paste the query above
4. Click "Run"
5. Note the execution time in the results panel

**Execution Time:** _______ ms

**Verification:** ⬜ Pass (< 600ms) | ⬜ Fail (> 600ms)

---

#### Test 2: Filtered Bbox Query

**Query:**
```sql
SELECT 
    latitude,
    longitude,
    area_in_meters,
    confidence
FROM `trim-descent-452802-t2.openbuildings.thailand_raw`
WHERE latitude BETWEEN 13.0 AND 14.0
  AND longitude BETWEEN 100.0 AND 101.0
  AND confidence >= 0.7
  AND area_in_meters >= 50
LIMIT 1000;
```

**Performance Target:** < 600ms

**Execution Time:** _______ ms

**Rows Returned:** _______

**Verification:** ⬜ Pass (< 600ms) | ⬜ Fail (> 600ms)

---

#### Test 3: Count Query with Filters

**Query:**
```sql
SELECT COUNT(*) as count
FROM `trim-descent-452802-t2.openbuildings.thailand_raw`
WHERE confidence >= 0.8
  AND area_in_meters BETWEEN 100 AND 500;
```

**Performance Target:** < 600ms

**Execution Time:** _______ ms

**Result Count:** _______

**Verification:** ⬜ Pass (< 600ms) | ⬜ Fail (> 600ms)

---

#### Test 4: Spatial Query

**Query:**
```sql
SELECT 
    latitude,
    longitude,
    area_in_meters,
    confidence
FROM `trim-descent-452802-t2.openbuildings.thailand_raw`
WHERE ST_DISTANCE(
    ST_GEOGPOINT(longitude, latitude),
    ST_GEOGPOINT(100.5018, 13.7563)
) < 5000
AND confidence >= 0.7
LIMIT 100;
```

**Performance Target:** < 1000ms (spatial queries are more expensive)

**Execution Time:** _______ ms

**Rows Returned:** _______

**Verification:** ⬜ Pass (< 1000ms) | ⬜ Fail (> 1000ms)

---

### 5. Analyze Query Execution Plans

For each query, check the execution plan to understand performance:

**Steps:**
1. In BigQuery console, click "Execution Details" after running a query
2. Review the "Query Plan" tab
3. Look for:
   - Bytes processed
   - Bytes billed
   - Slot time consumed
   - Stages and their durations

**Key Metrics to Check:**

| Query Type | Bytes Processed | Expected |
|------------|----------------|----------|
| Stats (materialized view) | < 1 MB | Very efficient |
| Filtered bbox | < 100 MB | Good with clustering |
| Count with filters | < 500 MB | Acceptable |
| Spatial query | < 1 GB | Expected for spatial ops |

**Notes:**
```
[Add observations about query execution plans]
```

---

### 6. Verify Index Creation (If Applicable)

BigQuery doesn't use traditional indexes, but some tables may have search indexes for specific use cases.

**Check for search indexes:**

```sql
SELECT 
  table_name,
  index_name,
  index_status
FROM `trim-descent-452802-t2.openbuildings.INFORMATION_SCHEMA.SEARCH_INDEXES`
WHERE table_name IN ('rankings_cache', 'permitting_data', 'thailand_raw');
```

**Expected Result:** No search indexes (not needed for this use case)

**Verification:** ⬜ Pass | ⬜ N/A

---

## Performance Optimization Recommendations

### If Query Performance is Below Target

1. **Check Clustering:**
   - Ensure clustering fields match common filter patterns
   - Verify clustering is applied to all relevant tables

2. **Review Query Patterns:**
   - Use clustering fields in WHERE clauses
   - Avoid SELECT * when possible
   - Use LIMIT for exploratory queries

3. **Consider Partitioning:**
   - For time-series data, partition by date
   - Helps with data lifecycle management

4. **Optimize Spatial Queries:**
   - Use bounding box pre-filter before ST_DISTANCE
   - Example:
     ```sql
     WHERE latitude BETWEEN @min_lat AND @max_lat
       AND longitude BETWEEN @min_lon AND @max_lon
       AND ST_DISTANCE(...) < @radius
     ```

5. **Use Materialized Views:**
   - For frequently accessed aggregations
   - Refresh interval should match data update frequency

### Cost Optimization

**Check query costs:**

```sql
-- Get query costs for the last 7 days
SELECT 
  user_email,
  query,
  total_bytes_processed,
  total_bytes_billed,
  ROUND(total_bytes_billed / 1024 / 1024 / 1024 / 1024, 4) as tb_billed,
  ROUND((total_bytes_billed / 1024 / 1024 / 1024 / 1024) * 5, 4) as estimated_cost_usd
FROM `trim-descent-452802-t2.region-asia-southeast1.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
ORDER BY total_bytes_billed DESC
LIMIT 20;
```

**Cost Optimization Tips:**
- Use clustering to reduce bytes scanned
- Partition tables by date for time-based queries
- Use materialized views for repeated aggregations
- Set up query result caching (enabled by default)

---

## Troubleshooting

### Clustering Not Applied

**Symptom:** Query performance is slow, clustering_fields is NULL

**Solution:**
```sql
ALTER TABLE `trim-descent-452802-t2.openbuildings.{table_name}`
CLUSTER BY {field1}, {field2}, ...;
```

**Note:** This operation may take time for large tables.

---

### Queries Scanning Too Many Bytes

**Symptom:** High costs, slow queries

**Solutions:**
1. Add clustering on frequently filtered columns
2. Use partitioning for time-based data
3. Avoid SELECT * - specify only needed columns
4. Use WHERE clauses that match clustering fields

---

### Materialized View Not Refreshing

**Symptom:** stats_summary shows stale data

**Check refresh status:**
```sql
SELECT 
  table_name,
  option_name,
  option_value
FROM `trim-descent-452802-t2.openbuildings.INFORMATION_SCHEMA.TABLE_OPTIONS`
WHERE table_name = 'stats_summary'
  AND option_name IN ('enable_refresh', 'refresh_interval_minutes');
```

**Manual refresh:**
```sql
CALL BQ.REFRESH_MATERIALIZED_VIEW('trim-descent-452802-t2.openbuildings.stats_summary');
```

---

## Final Checklist

- [ ] rankings_cache has clustering on scope_type, scope_value, ranking_position
- [ ] rankings_cache has partitioning on calculated_at
- [ ] permitting_data has clustering on latitude, longitude
- [ ] thailand_raw has clustering (recommended: confidence, area_in_meters, latitude, longitude)
- [ ] Stats query completes in < 600ms
- [ ] Filtered bbox query completes in < 600ms
- [ ] Count query completes in < 600ms
- [ ] Spatial query completes in < 1000ms
- [ ] Query execution plans show efficient byte scanning
- [ ] No unexpected costs or performance issues

## Sign-Off

**Verified By:** _______________________

**Date:** _______________________

**Overall Status:** ⬜ Pass | ⬜ Fail | ⬜ Needs Optimization

**Notes:**
```
[Add any additional notes or observations]
```

## Next Steps

After successful verification:
1. Update task status in tasks.md
2. Document any performance baselines
3. Set up monitoring for query performance
4. Schedule regular performance reviews
5. Proceed to task 18 (Integration Testing)
