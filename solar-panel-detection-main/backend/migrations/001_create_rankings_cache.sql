-- Migration 001: Create rankings_cache table
-- Purpose: Store pre-calculated building rankings for fast retrieval
-- Requirements: 7, 11, 14

CREATE TABLE IF NOT EXISTS `trim-descent-452802-t2.openbuildings.rankings_cache` (
    building_id STRING NOT NULL,
    open_buildings_id STRING,
    latitude FLOAT64 NOT NULL,
    longitude FLOAT64 NOT NULL,
    area_m2 FLOAT64 NOT NULL,
    confidence FLOAT64 NOT NULL,
    ranking_score FLOAT64 NOT NULL,
    ranking_position INT64 NOT NULL,
    solar_potential_score FLOAT64,
    roof_area_score FLOAT64,
    confidence_score FLOAT64,
    payback_score FLOAT64,
    permitting_score FLOAT64,
    scope_type STRING NOT NULL,  -- "global", "country", "region", "province"
    scope_value STRING NOT NULL,  -- "TH", "Bangkok", etc.
    calculated_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(calculated_at)
CLUSTER BY scope_type, scope_value, ranking_position
OPTIONS(
    description="Pre-calculated building rankings for solar potential",
    labels=[("purpose", "rankings"), ("version", "v1")]
);

-- Create index on expires_at for cache cleanup
CREATE INDEX IF NOT EXISTS idx_rankings_expires 
ON `trim-descent-452802-t2.openbuildings.rankings_cache`(expires_at);
