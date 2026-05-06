-- Migration 003: Create permitting_data table (placeholder for future)
-- Purpose: Store permitting status for buildings
-- Requirements: 6, 11

CREATE TABLE IF NOT EXISTS `trim-descent-452802-t2.openbuildings.permitting_data` (
    building_id STRING NOT NULL,
    latitude FLOAT64 NOT NULL,
    longitude FLOAT64 NOT NULL,
    permitting_status STRING NOT NULL,  -- "approved", "pending", "not_required", "unknown"
    permit_number STRING,
    approval_date DATE,
    expiry_date DATE,
    authority STRING,
    notes STRING,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY latitude, longitude
OPTIONS(
    description="Permitting status data for solar installations (placeholder for future integration)",
    labels=[("purpose", "permitting"), ("version", "v1"), ("status", "placeholder")]
);

-- Create index on permitting_status for filtering
CREATE INDEX IF NOT EXISTS idx_permitting_status 
ON `trim-descent-452802-t2.openbuildings.permitting_data`(permitting_status);

-- Create index on building_id for lookups
CREATE INDEX IF NOT EXISTS idx_permitting_building 
ON `trim-descent-452802-t2.openbuildings.permitting_data`(building_id);
