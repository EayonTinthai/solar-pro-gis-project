# Rankings Feature Documentation

## Overview

The Rankings feature provides a multi-factor scoring system to identify and prioritize the best solar installation opportunities. Buildings are ranked based on solar potential, roof area, confidence score, payback period, and permitting status.

**Requirements**: Requirement 7

## Architecture

### Components

1. **Ranking Algorithm** (`services/ranking.py`)
   - Calculates weighted scores for buildings
   - Normalizes factors to 0-1 scale
   - Returns 0-100 overall score with component breakdown

2. **Rankings Calculation Job** (`calculate_rankings.py`)
   - Batch processes buildings to calculate rankings
   - Stores results in BigQuery `rankings_cache` table
   - Should be run daily via Cloud Scheduler

3. **Rankings API Endpoint** (`/rankings` in `api_bigquery.py`)
   - Queries pre-calculated rankings from cache
   - Supports filtering by scope and confidence
   - Returns enriched building data with ranking scores

### Database Schema

**Table**: `rankings_cache`

```sql
CREATE TABLE rankings_cache (
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
    scope_type STRING NOT NULL,
    scope_value STRING NOT NULL,
    calculated_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(calculated_at)
CLUSTER BY scope_type, scope_value, ranking_position;
```

## Ranking Algorithm

### Weights

The ranking score is calculated using the following weights:

| Factor | Weight | Description |
|--------|--------|-------------|
| Solar Potential | 40% | Annual production in kWh |
| Roof Area | 20% | Building area in m² |
| Confidence Score | 20% | ML detection confidence (0-1) |
| Payback Period | 15% | Investment payback time (shorter is better) |
| Permitting Status | 5% | Regulatory approval status |

### Permitting Status Weights

| Status | Weight | Description |
|--------|--------|-------------|
| approved | 1.0 | Full regulatory approval |
| not_required | 0.8 | No permit needed |
| pending | 0.6 | Application submitted |
| unknown | 0.3 | No data available |

### Calculation Formula

```python
# Normalize each factor to 0-1 scale
solar_normalized = normalize(annual_production_kwh, 0, 100000)
area_normalized = normalize(area_m2, 0, 1000)
confidence_normalized = confidence  # Already 0-1
payback_normalized = normalize(1/payback_years, 0, 1)
permitting_normalized = PERMITTING_WEIGHTS[status]

# Calculate weighted scores
solar_score = solar_normalized * 0.40 * 100
area_score = area_normalized * 0.20 * 100
confidence_score = confidence_normalized * 0.20 * 100
payback_score = payback_normalized * 0.15 * 100
permitting_score = permitting_normalized * 0.05 * 100

# Total score (0-100)
ranking_score = solar_score + area_score + confidence_score + payback_score + permitting_score
```

## Usage

### 1. Calculate Rankings

Run the rankings calculation job to populate the cache:

```bash
cd solar-panel-detection-main/backend
python calculate_rankings.py
```

This will:
- Query buildings from BigQuery
- Calculate solar metrics for each building
- Calculate ranking scores
- Store results in `rankings_cache` table
- Set expiration to 24 hours from calculation time

**Recommended Schedule**: Daily via Cloud Scheduler

### 2. Query Rankings via API

**Endpoint**: `GET /rankings`

**Query Parameters**:
- `scope` (string): Geographic scope - "global", "country", "region", or "province" (default: "country")
- `scope_value` (string): Scope identifier, e.g., "TH" for Thailand (default: "TH")
- `limit` (integer): Number of results to return (default: 100, max: 1000)
- `min_confidence` (float): Minimum confidence threshold (default: 0.7, range: 0.5-1.0)

**Example Request**:
```bash
curl "https://your-api.com/rankings?scope=country&scope_value=TH&limit=100&min_confidence=0.7"
```

**Example Response**:
```json
{
  "scope": {
    "type": "country",
    "value": "TH"
  },
  "total_evaluated": 10000,
  "rankings": [
    {
      "id": 123456,
      "open_buildings_id": "849VGJQH+2V",
      "latitude": 13.7563,
      "longitude": 100.5018,
      "area_m2": 850.5,
      "confidence": 0.95,
      "ranking_score": 87.5,
      "ranking_position": 1,
      "ranking_factors": {
        "solar_potential_score": 35.0,
        "roof_area_score": 18.0,
        "confidence_score": 19.0,
        "payback_score": 13.5,
        "permitting_score": 2.0
      },
      "data_provenance": { ... },
      "accuracy_level": "high",
      "permitting_status": "unknown",
      ...
    }
  ],
  "cache_expires_at": "2026-04-18T15:30:00+07:00"
}
```

### 3. Caching

- Rankings are cached for 24 hours
- Cache is automatically applied via `@cache_with_ttl(seconds=86400)` decorator
- Cache headers are added to responses:
  - `X-Cache-Status`: "HIT" or "MISS"
  - `Cache-Control`: Public cache with max-age

## Performance Considerations

### Query Optimization

1. **Pre-calculation**: Rankings are calculated in batch, not on-demand
2. **Partitioning**: Table is partitioned by `calculated_at` date
3. **Clustering**: Clustered by `scope_type`, `scope_value`, `ranking_position`
4. **Indexing**: Index on `expires_at` for cache cleanup
5. **Caching**: 24-hour API response cache

### Scalability

- Current implementation handles top 10,000 buildings per scope
- Can be extended to support more scopes (region, province)
- Calculation job can be parallelized for multiple scopes

## Monitoring

### Key Metrics

1. **Cache Hit Rate**: Should be >60% for rankings endpoint
2. **Calculation Time**: Job should complete in <10 minutes for 10K buildings
3. **API Response Time**: Should be <600ms (p95)
4. **Cache Freshness**: Monitor `expires_at` to ensure rankings are current

### Logging

The calculation job logs:
- Start/end timestamps
- Number of buildings processed
- Errors during calculation
- Storage success/failure

## Future Enhancements

1. **Regional Scopes**: Add support for province/region-level rankings
2. **Permitting Integration**: Connect to real permitting database
3. **Custom Weights**: Allow users to customize ranking weights
4. **Real-time Updates**: Trigger recalculation on data updates
5. **Historical Tracking**: Store ranking history for trend analysis

## Troubleshooting

### No Rankings Available

**Symptom**: API returns empty rankings array

**Solution**: Run `calculate_rankings.py` to generate rankings

### Expired Rankings

**Symptom**: API returns no results even though rankings exist

**Solution**: Rankings have expired (>24 hours old). Run calculation job again.

### Incorrect Scores

**Symptom**: Ranking scores don't match expectations

**Solution**: 
1. Verify normalization ranges in `calculate_ranking_score()`
2. Check solar metrics calculation in `calculate_solar_metrics()`
3. Review permitting status weights

### Performance Issues

**Symptom**: Calculation job takes too long

**Solution**:
1. Reduce `limit` parameter in `calculate_rankings_for_scope()`
2. Add more specific WHERE clauses to filter buildings
3. Consider parallelizing across multiple scopes

## Testing

### Unit Test

Test the ranking algorithm with sample data:

```bash
python test_ranking_algorithm.py
```

This will verify:
- Score calculation is correct
- Component scores sum to total
- Ranking order is logical (high > medium > low)

### Integration Test

Test the full workflow:

1. Run calculation job: `python calculate_rankings.py`
2. Query API: `curl http://localhost:8080/rankings`
3. Verify response contains rankings with correct structure

## References

- Requirements Document: `.kiro/specs/platform-improvements/requirements.md` (Requirement 7)
- Design Document: `.kiro/specs/platform-improvements/design.md` (Section: GET /rankings)
- Migration: `migrations/001_create_rankings_cache.sql`
