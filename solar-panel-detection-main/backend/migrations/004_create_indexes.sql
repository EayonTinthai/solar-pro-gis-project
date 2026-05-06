-- Migration 004: Create indexes on main table for performance
-- Purpose: Optimize common query patterns
-- Requirements: 3, 14

-- Note: BigQuery doesn't support traditional indexes like PostgreSQL
-- Instead, we use clustering and partitioning for optimization
-- This file documents the optimization strategy

-- The thailand_raw table should be optimized with:
-- 1. Clustering on frequently filtered columns
-- 2. Partitioning if we add a date column in the future

-- For now, we document the recommended clustering columns:
-- - confidence (for min_confidence filters)
-- - area_in_meters (for area filters and sorting)
-- - latitude, longitude (for spatial queries)

-- To apply clustering to existing table (run manually if needed):
-- ALTER TABLE `trim-descent-452802-t2.openbuildings.thailand_raw`
-- CLUSTER BY confidence, area_in_meters, latitude, longitude;

-- Note: Clustering is automatically maintained by BigQuery
-- and improves query performance for filtered and sorted queries

-- For spatial queries, BigQuery uses built-in spatial indexing
-- when using ST_* functions, so no additional indexes needed
