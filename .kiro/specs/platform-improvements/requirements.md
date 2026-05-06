# Requirements Document - Backend Improvements

## Introduction

This document outlines backend API requirements for improvements to the Solar Potential Platform based on stakeholder review feedback. The improvements address critical backend bugs, enhance data transparency through API responses, improve calculation handling, and add new backend features for energy developers.

**Scope**: Backend API only (Frontend improvements handled separately)

## Glossary

- **API**: Backend RESTful service providing building and solar data
- **Building_Data**: Google Open Buildings dataset with 107M+ footprints
- **Confidence_Score**: Detection confidence value (0-1 scale) from ML model
- **Energy_Developer**: Primary user persona - professionals evaluating solar sites
- **Permitting_Status**: Regulatory approval state for solar installations
- **Ranking_System**: Backend algorithm for identifying optimal solar sites
- **Data_Provenance**: Metadata about data source, collection method, and timestamp
- **Accuracy_Level**: Calculated quality indicator (High/Medium/Low) based on confidence and validation

## Requirements

### Requirement 1: Data Confidence and Transparency

**User Story:** As an energy developer, I want to see confidence scores and data sources for each building via API, so that I can assess data reliability for investment decisions.

#### Acceptance Criteria

1. THE API SHALL include `confidence_score` field in all building responses (already implemented)
2. THE API SHALL add `data_provenance` object to building responses containing:
   - `data_source`: String (e.g., "Google Open Buildings v3")
   - `collection_method`: String (e.g., "ML detection from satellite imagery")
   - `last_updated`: ISO 8601 timestamp
3. THE API SHALL add `confidence_warning` boolean field when confidence < 0.7
4. THE API documentation SHALL include confidence calculation methodology

### Requirement 2: Statistical Clarity

**User Story:** As an energy developer, I want statistical measures via API, so that I can evaluate dataset reliability.

#### Acceptance Criteria

1. THE `/stats/distribution` endpoint SHALL add `standard_deviation` fields:
   - `confidence_std_dev`: Standard deviation of confidence scores
   - `area_std_dev`: Standard deviation of building areas
2. THE `/stats` endpoint SHALL add `median` values alongside existing `average` values
3. THE API documentation SHALL explain statistical metrics in accessible language

### Requirement 3: Filter System Improvements

**User Story:** As an energy developer, I want validated API filters with clear bounds, so that I can efficiently query suitable buildings.

#### Acceptance Criteria

1. THE API SHALL validate `min_confidence` parameter is between 0.5 and 1.0
2. THE API SHALL validate `area_m2` filters are positive numbers
3. THE API SHALL return HTTP 422 with descriptive error for invalid filter values
4. THE `/buildings/bbox` endpoint SHALL add optional filters:
   - `min_area_m2`: Minimum roof area (default: none)
   - `max_area_m2`: Maximum roof area (default: none)
   - `min_system_kwp`: Minimum solar capacity (default: none)
   - `max_system_kwp`: Maximum solar capacity (default: none)
5. THE API SHALL document valid ranges for all filter parameters in OpenAPI schema
6. THE API SHALL respond to filtered queries within 600ms (95th percentile)

### Requirement 4: Performance and Caching

**User Story:** As an energy developer, I want fast API responses, so that I can explore scenarios interactively.

#### Acceptance Criteria

1. THE API SHALL support 100 concurrent requests without performance degradation
2. THE API SHALL implement caching for:
   - `/stats`: 24-hour TTL
   - `/stats/distribution`: 24-hour TTL
   - `/weather/forecast`: 1-hour TTL
   - `/buildings/bbox`: 1-hour TTL (keyed by bbox parameters)
3. THE API SHALL add `Cache-Control` headers to responses
4. THE API SHALL add `X-Cache-Status` header (HIT/MISS) for debugging
5. THE API SHALL respond to building queries within 600ms (95th percentile)

### Requirement 5: Calculation Transparency

**User Story:** As an energy developer, I want detailed calculation breakdowns via API, so that I can trust and audit the results.

#### Acceptance Criteria

1. THE `/solar/calculate` endpoint SHALL add `calculation_breakdown` object containing:
   - `step_1_usable_area`: Calculation with formula
   - `step_2_system_size`: Calculation with formula
   - `step_3_annual_production`: Calculation with formula
   - `step_4_financial`: Calculation with formula
2. THE API SHALL include `calculation_method` field (already implemented: "pvlib" or "simplified")
3. THE API SHALL return all intermediate values (already implemented: usable_roof_area, system_size_kwp, etc.)
4. THE API documentation SHALL document all formulas (already in BACKEND.md)

### Requirement 6: Permitting Data Integration

**User Story:** As an energy developer, I want permitting status via API, so that I can prioritize sites with regulatory approval.

#### Acceptance Criteria

1. THE API SHALL add `permitting_status` field to building data model with values:
   - `"approved"`: Regulatory approval granted
   - `"pending"`: Application submitted
   - `"not_required"`: No permit needed
   - `"unknown"`: No data available (default)
2. THE API SHALL return `permitting_status` in all building query responses
3. THE `/buildings/bbox` and `/buildings/nearby` endpoints SHALL add optional filter:
   - `permitting_status`: Filter by status (comma-separated for multiple)
4. THE API SHALL handle missing permitting data gracefully (default to "unknown")
5. THE API documentation SHALL explain permitting status values and data sources

### Requirement 7: Site Ranking System

**User Story:** As an energy developer, I want to query top-ranked solar sites via API, so that I can quickly identify best opportunities.

#### Acceptance Criteria

1. THE API SHALL provide new `GET /rankings` endpoint with parameters:
   - `scope`: Geographic scope ("global", "country", "region", "province")
   - `scope_value`: Scope identifier (e.g., "TH", "Bangkok")
   - `limit`: Number of results (default: 100, max: 1000)
   - `min_confidence`: Minimum confidence threshold (default: 0.7)
2. THE ranking algorithm SHALL calculate score based on:
   - Solar potential (40% weight): Annual production kWh
   - Roof area (20% weight): Larger roofs preferred
   - Confidence score (20% weight): Higher confidence preferred
   - Payback period (15% weight): Shorter payback preferred
   - Permitting status (5% weight): Approved > Pending > Unknown
3. THE API SHALL return ranked buildings with:
   - All standard building fields
   - `ranking_score`: Normalized 0-100 score
   - `ranking_position`: Position in results (1, 2, 3...)
   - `ranking_factors`: Breakdown of score components
4. THE API SHALL cache rankings for 24 hours
5. THE API documentation SHALL explain ranking algorithm and weights

### Requirement 8: Polygon Analysis Endpoint

**User Story:** As an energy developer, I want to analyze custom geographic areas via API, so that I can evaluate specific regions of interest.

#### Acceptance Criteria

1. THE API SHALL provide new `POST /polygon/analyze` endpoint accepting:
   - `geometry`: GeoJSON polygon or multipolygon
   - `min_confidence`: Minimum confidence threshold (default: 0.7)
   - `include_buildings`: Boolean to include individual buildings (default: false)
   - `limit`: Max buildings to return if include_buildings=true (default: 1000, max: 10000)
2. THE API SHALL return aggregated statistics:
   - `total_buildings`: Count of buildings in polygon
   - `total_area_m2`: Sum of building areas
   - `total_system_kwp`: Sum of potential solar capacity
   - `total_annual_production_kwh`: Sum of annual production
   - `total_installation_cost_thb`: Sum of installation costs
   - `avg_confidence`: Average confidence score
   - `avg_payback_years`: Average payback period
3. THE API SHALL optionally return individual buildings array when `include_buildings=true`
4. THE API SHALL validate polygon has max 1000 vertices
5. THE API SHALL return HTTP 413 if polygon area exceeds 1000 km²
6. THE API SHALL respond within 5 seconds for polygons with <10,000 buildings

### Requirement 9: Advanced Filtering for Energy Developers

**User Story:** As an energy developer, I want specialized API filters, so that I can find sites matching my project criteria.

#### Acceptance Criteria

1. THE `/buildings/bbox` and `/buildings/nearby` endpoints SHALL add filters:
   - `min_system_kwp`: Minimum solar capacity (already in Req 3)
   - `max_system_kwp`: Maximum solar capacity (already in Req 3)
   - `max_payback_years`: Maximum acceptable payback period
   - `permitting_status`: Filter by permitting status (already in Req 6)
2. THE API SHALL apply multiple filters with AND logic
3. THE API SHALL return `total_matching` count before limit is applied
4. THE API SHALL validate filter combinations and return HTTP 422 for invalid combinations
5. THE API documentation SHALL provide filter usage examples

### Requirement 10: API Documentation Enhancement

**User Story:** As an API consumer, I want comprehensive documentation, so that I can integrate the API effectively.

#### Acceptance Criteria

1. THE API SHALL provide OpenAPI 3.0 specification at `/openapi.json`
2. THE API SHALL provide interactive documentation at `/docs` (Swagger UI)
3. THE API SHALL provide alternative documentation at `/redoc` (ReDoc)
4. THE API documentation SHALL include:
   - Request/response examples for all endpoints
   - Parameter descriptions with valid ranges
   - Error response examples
   - Rate limiting information
   - Authentication requirements (if applicable)
5. THE BACKEND.md SHALL be kept up-to-date with all API changes
6. THE API SHALL add `/docs/methodology` endpoint returning calculation methodology as JSON

### Requirement 11: Data Quality Metadata

**User Story:** As a platform administrator, I want data quality metadata via API, so that I can monitor dataset health.

#### Acceptance Criteria

1. THE API SHALL provide new `GET /admin/data-quality` endpoint returning:
   - `total_buildings`: Total count
   - `low_confidence_count`: Buildings with confidence < 0.7
   - `low_confidence_percentage`: Percentage of low confidence buildings
   - `data_freshness`: Days since last data update
   - `validation_status`: Overall data quality status
   - `quality_by_region`: Breakdown by province/region
2. THE API SHALL add `data_quality_flag` field to building responses:
   - `"high"`: Confidence >= 0.8
   - `"medium"`: Confidence 0.7-0.8
   - `"low"`: Confidence < 0.7
3. THE API SHALL require authentication for `/admin/*` endpoints
4. THE API SHALL log all data quality queries for audit trail

### Requirement 12: Accuracy Level Calculation

**User Story:** As an energy developer, I want accuracy levels via API, so that I can assess data quality programmatically.

#### Acceptance Criteria

1. THE API SHALL add `accuracy_level` field to all building responses with values:
   - `"high"`: Confidence >= 0.8 AND data_age < 365 days
   - `"medium"`: Confidence >= 0.7 OR data_age < 730 days
   - `"low"`: Confidence < 0.7 AND data_age >= 730 days
2. THE API SHALL add `accuracy_factors` object explaining the rating:
   - `confidence_score`: The building's confidence value
   - `data_age_days`: Days since data collection
   - `validation_status`: Whether building has been field-validated
3. THE `/buildings/bbox` and `/buildings/nearby` endpoints SHALL add filter:
   - `min_accuracy_level`: Filter by accuracy ("high", "medium", "low")
4. THE API documentation SHALL explain accuracy level calculation

### Requirement 13: Customizable Solar Parameters

**User Story:** As an energy developer, I want to customize calculation parameters via API, so that I can model different scenarios.

#### Acceptance Criteria

1. THE `/solar/calculate` endpoint SHALL accept optional parameters:
   - `panel_efficiency`: Panel efficiency (default: 0.20, range: 0.15-0.25)
   - `system_efficiency`: System performance ratio (default: 0.80, range: 0.70-0.90)
   - `usable_roof_ratio`: Usable roof percentage (default: 0.50, range: 0.30-0.70)
   - `cost_per_wp`: Installation cost THB/Wp (default: 25, range: 20-50)
   - `electricity_rate`: Electricity rate THB/kWh (default: 4.18, range: 3.0-6.0)
   - `co2_factor`: CO2 emission factor kg/kWh (default: 0.40, range: 0.30-0.50)
2. THE API SHALL validate all parameters are within specified ranges
3. THE API SHALL return HTTP 422 with descriptive error for out-of-range parameters
4. THE API SHALL include `custom_parameters` object in response showing which parameters were customized
5. THE API documentation SHALL explain parameter ranges and defaults

### Requirement 14: Pagination and Result Limits

**User Story:** As an API consumer, I want paginated results, so that I can handle large datasets efficiently.

#### Acceptance Criteria

1. THE `/buildings/bbox` and `/buildings/nearby` endpoints SHALL add pagination parameters:
   - `offset`: Number of records to skip (default: 0)
   - `limit`: Number of records to return (default: 1000, max: 5000)
2. THE API SHALL return pagination metadata in responses:
   - `total`: Total matching records
   - `offset`: Current offset
   - `limit`: Current limit
   - `has_more`: Boolean indicating more results available
   - `next_offset`: Suggested offset for next page
3. THE API SHALL use database indexes on:
   - `latitude`, `longitude` (spatial queries)
   - `confidence` (filtering)
   - `area_in_meters` (sorting)
4. THE API SHALL add `GET /health` endpoint for monitoring
5. THE API SHALL log query performance metrics to Cloud Logging

### Requirement 15: Data Source Traceability

**User Story:** As an energy developer, I want data source information via API, so that I can verify data authenticity.

#### Acceptance Criteria

1. THE API SHALL add `data_source` field to all building responses:
   - Value: "Google Open Buildings v3"
2. THE API SHALL add `data_collection_date` field (ISO 8601 timestamp)
3. THE API SHALL add `data_source_url` field with link to original dataset
4. THE `/stats` endpoint SHALL add `dataset_metadata` object:
   - `source`: Data source name
   - `version`: Dataset version
   - `collection_date`: When data was collected
   - `ingestion_date`: When data was loaded into system
   - `update_frequency`: How often data is refreshed
   - `license`: Data license information
5. THE API documentation SHALL include data provenance section

## Notes

- All requirements focus on backend API changes only
- Frontend team will handle UI/UX improvements separately
- System must maintain backward compatibility with existing API endpoints
- Performance requirements based on current 107M+ building dataset in BigQuery
- Permitting data integration requires external data source partnership (future phase)
- Ranking algorithm should be configurable for different markets
- New endpoints should follow RESTful conventions
- All responses should include proper HTTP status codes and error messages
- OpenAPI documentation should be auto-generated from FastAPI decorators

---

**Document Version**: 1.0  
**Created**: April 17, 2026  
**Status**: Draft for Review
