# Enhanced Buildings Endpoints - Usage Examples

## Overview

This document provides examples of using the enhanced `/buildings/bbox` and `/buildings/nearby` endpoints with the new filtering, pagination, and enrichment features.

## Basic Usage

### Get buildings in bounding box (unchanged)

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6
```

Response:
```json
{
  "total": 15234,
  "offset": 0,
  "limit": 1000,
  "has_more": true,
  "next_offset": 1000,
  "buildings": [...]
}
```

## Advanced Filtering

### Filter by area

Get buildings between 100-500 m²:

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&min_area_m2=100&max_area_m2=500
```

### Filter by solar capacity

Get buildings with 10-50 kWp potential:

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&min_system_kwp=10&max_system_kwp=50
```

### Filter by payback period

Get buildings with payback <= 5 years:

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&max_payback_years=5
```

### Filter by confidence

Get only high-confidence buildings (>= 0.8):

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&min_confidence=0.8
```

### Filter by accuracy level

Get only high-accuracy buildings:

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&min_accuracy_level=high
```

### Filter by permitting status

Get approved or pending buildings:

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&permitting_status=approved,pending
```

## Combined Filters

Get large, high-confidence buildings with good payback:

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&min_area_m2=200&min_confidence=0.8&max_payback_years=5
```

## Pagination

### First page (default)

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6
```

Response:
```json
{
  "total": 15234,
  "offset": 0,
  "limit": 1000,
  "has_more": true,
  "next_offset": 1000,
  "buildings": [...]
}
```

### Second page

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&offset=1000
```

### Custom page size

Get 500 results per page:

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=500
```

### Large page size

Get up to 5000 results (maximum):

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=5000
```

## Nearby Endpoint

All the same filters work with `/buildings/nearby`:

### Basic nearby search

```bash
GET /buildings/nearby?lat=13.7563&lon=100.5018&radius_m=1000
```

### Nearby with filters

```bash
GET /buildings/nearby?lat=13.7563&lon=100.5018&radius_m=1000&min_area_m2=200&min_confidence=0.8
```

### Nearby with pagination

```bash
GET /buildings/nearby?lat=13.7563&lon=100.5018&radius_m=1000&limit=50&offset=0
```

## Enriched Response Fields

Every building now includes these additional fields:

```json
{
  "id": 123456,
  "open_buildings_id": "OB_123456",
  "latitude": 13.7563,
  "longitude": 100.5018,
  "area_m2": 250.0,
  "confidence": 0.85,
  "geometry": {...},
  
  // Data provenance
  "data_provenance": {
    "data_source": "Google Open Buildings v3",
    "collection_method": "ML detection from satellite imagery",
    "last_updated": "2023-06-15T00:00:00Z"
  },
  
  // Confidence warning
  "confidence_warning": false,
  
  // Accuracy assessment
  "accuracy_level": "medium",
  "accuracy_factors": {
    "confidence_score": 0.85,
    "data_age_days": 1037,
    "validation_status": "unvalidated"
  },
  
  // Permitting information
  "permitting_status": "unknown",
  
  // Data traceability
  "data_source": "Google Open Buildings v3",
  "data_collection_date": "2023-06-15T00:00:00Z",
  "data_source_url": "https://sites.research.google/open-buildings/",
  
  // Quality flag
  "data_quality_flag": "high"
}
```

## Error Handling

### Invalid confidence range

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&min_confidence=1.5
```

Response (HTTP 422):
```json
{
  "error": "ValidationError",
  "detail": "min_confidence must be between 0.5 and 1.0, got 1.5",
  "status_code": 422,
  "timestamp": "2026-04-17T15:30:00+07:00",
  "request_id": "req_abc123"
}
```

### Invalid area range

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&min_area_m2=500&max_area_m2=100
```

Response (HTTP 422):
```json
{
  "error": "ValidationError",
  "detail": "min_area_m2 (500.0) must be <= max_area_m2 (100.0)",
  "status_code": 422,
  "timestamp": "2026-04-17T15:30:00+07:00",
  "request_id": "req_abc123"
}
```

### Negative values

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&min_area_m2=-10
```

Response (HTTP 422):
```json
{
  "error": "ValidationError",
  "detail": "min_area_m2 must be positive, got -10.0",
  "status_code": 422,
  "timestamp": "2026-04-17T15:30:00+07:00",
  "request_id": "req_abc123"
}
```

## Use Cases

### Energy Developer: Find optimal sites

Find large buildings with high confidence and good payback:

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&min_area_m2=300&min_confidence=0.85&max_payback_years=4&min_accuracy_level=high
```

### Researcher: Get high-quality data

Get only validated, high-accuracy buildings:

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&min_accuracy_level=high&min_confidence=0.9
```

### Installer: Find medium-sized projects

Get buildings suitable for residential/small commercial:

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&min_area_m2=100&max_area_m2=500&min_system_kwp=5&max_system_kwp=50
```

### Policy Maker: Analyze permitted sites

Get buildings with approved permits:

```bash
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&permitting_status=approved
```

## Performance Notes

- Caching: Responses are cached for 1 hour
- Pagination: Use smaller page sizes for faster responses
- Filters: More filters = fewer results = faster response
- Area filters: Applied in SQL (fast)
- System size/payback filters: Applied post-query (slower)

## Backward Compatibility

All new parameters are optional. Existing API calls continue to work unchanged:

```bash
# Old API call - still works
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=100&min_confidence=0.7
```

The response now includes additional enrichment fields, but all original fields remain in the same format.

