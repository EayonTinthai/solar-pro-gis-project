# Implementation Plan: Backend API Improvements

## Overview

This implementation plan breaks down the backend API improvements into discrete, manageable tasks. Each task builds on previous work and includes specific requirements references for traceability.

**Total Estimated Time**: 4 weeks (19 days)

## Tasks

- [x] 1. Setup and Infrastructure
- [x] 1.1 Create BigQuery tables and views
  - Create `rankings_cache` table with partitioning and clustering
  - Create `stats_summary` materialized view for performance
  - Create `permitting_data` table (placeholder for future)
  - Add indexes on `confidence`, `area_in_meters`, spatial columns
  - _Requirements: 7, 11, 14_

- [x] 1.2 Update project dependencies
  - Add `cachetools==5.3.2` for caching
  - Add `slowapi==0.1.9` for rate limiting
  - Add testing packages: `pytest`, `pytest-asyncio`, `httpx`, `locust`
  - Update `requirements.txt`
  - _Requirements: 4, 10_

- [x] 1.3 Create project structure
  - Create `models/` directory with Pydantic models
  - Create `services/` directory for business logic
  - Create `utils/` directory for helpers
  - Create `migrations/` directory with SQL files
  - Create `tests/` directory
  - _Requirements: All_

- [-] 2. Core Data Enrichment Functions
- [x] 2.1 Implement accuracy level calculation
  - Create `calculate_accuracy_level()` function
  - Logic: High (confidence >= 0.8 AND age < 365), Medium (confidence >= 0.7 OR age < 730), Low (otherwise)
  - Return accuracy level and factors object
  - _Requirements: 12_

- [x] 2.2 Implement data provenance builder
  - Create `build_data_provenance()` function
  - Return data_source, collection_method, last_updated
  - Use constants for Google Open Buildings v3 metadata
  - _Requirements: 1, 15_

- [x] 2.3 Implement building data enrichment
  - Create `enrich_building_data()` function
  - Add all new fields: data_provenance, confidence_warning, accuracy_level, accuracy_factors, permitting_status, data_source, data_collection_date, data_source_url
  - Calculate data_age_days from collection date
  - _Requirements: 1, 6, 12, 15_


- [x] 3. Caching System Implementation
- [x] 3.1 Create caching decorator
  - Implement `cache_with_ttl()` decorator
  - Generate cache keys from function name and arguments
  - Store cache with expiration timestamp
  - Add cache headers to responses (Cache-Control, X-Cache-Status)
  - _Requirements: 4_

- [x] 3.2 Implement cache management
  - Create in-memory cache dictionary with TTL
  - Implement LRU eviction when cache exceeds 1000 entries
  - Add cache invalidation function
  - _Requirements: 4_

- [x] 3.3 Apply caching to endpoints
  - Apply 24-hour cache to `/stats`
  - Apply 24-hour cache to `/stats/distribution`
  - Apply 1-hour cache to `/buildings/bbox`
  - Apply 1-hour cache to `/weather/forecast`
  - _Requirements: 4_

- [x] 4. Enhanced Statistics Endpoints
- [x] 4.1 Update `/stats` endpoint
  - Add median calculations using APPROX_QUANTILES
  - Add standard deviation using STDDEV
  - Add dataset_metadata object with source, version, dates, license
  - Use materialized view for performance
  - _Requirements: 2, 15_

- [x] 4.2 Update `/stats/distribution` endpoint
  - Add confidence_std_dev calculation
  - Add area_std_dev calculation
  - Keep existing bucket and cumulative calculations
  - _Requirements: 2_

- [x] 5. Enhanced Buildings Endpoints
- [x] 5.1 Add filter validation
  - Validate min_confidence between 0.5 and 1.0
  - Validate area_m2 filters are positive
  - Validate min <= max for range filters
  - Return HTTP 422 with descriptive errors
  - _Requirements: 3_

- [x] 5.2 Add new filters to `/buildings/bbox`
  - Add min_area_m2, max_area_m2 parameters
  - Add min_system_kwp, max_system_kwp parameters
  - Add max_payback_years parameter
  - Add permitting_status parameter (comma-separated)
  - Add min_accuracy_level parameter
  - Build dynamic SQL query with all filters
  - _Requirements: 3, 6, 9, 12_

- [x] 5.3 Add pagination to `/buildings/bbox`
  - Add offset parameter (default: 0)
  - Add limit parameter (default: 1000, max: 5000)
  - Return pagination metadata: total, offset, limit, has_more, next_offset
  - _Requirements: 14_

- [x] 5.4 Apply data enrichment to building responses
  - Call enrich_building_data() for each building
  - Return all new fields in response
  - _Requirements: 1, 6, 12, 15_

- [x] 5.5 Update `/buildings/nearby` endpoint
  - Apply same filters as bbox endpoint
  - Apply same pagination
  - Apply same data enrichment
  - _Requirements: 3, 6, 9, 12, 14_


- [x] 6. Enhanced Solar Calculation Endpoint
- [x] 6.1 Add custom parameters support
  - Accept custom_params object in request
  - Validate parameters within ranges (panel_efficiency: 0.15-0.25, system_efficiency: 0.70-0.90, etc.)
  - Return HTTP 422 for out-of-range values
  - Use custom values in calculations if provided
  - _Requirements: 13_

- [x] 6.2 Add calculation breakdown
  - Create calculation_breakdown object
  - Add step_1_usable_area with formula, inputs, result, unit
  - Add step_2_system_size with formula, inputs, result, unit
  - Add step_3_annual_production with formula, inputs, result, unit
  - Add step_4_financial with formula, inputs, result, unit
  - _Requirements: 5_

- [x] 6.3 Track custom parameters in response
  - Add custom_parameters object to response
  - Include only parameters that were customized
  - _Requirements: 13_

- [x] 7. New Endpoint: Rankings
- [x] 7.1 Implement ranking algorithm
  - Create calculate_ranking_score() function
  - Normalize solar potential (40% weight)
  - Normalize roof area (20% weight)
  - Use confidence directly (20% weight)
  - Normalize payback period inverse (15% weight)
  - Apply permitting status weights (5% weight)
  - Return 0-100 score
  - _Requirements: 7_

- [x] 7.2 Create rankings calculation job
  - Query all buildings from BigQuery
  - Calculate solar metrics for each building
  - Calculate ranking scores
  - Store in rankings_cache table
  - Set expires_at to 24 hours from now
  - _Requirements: 7_

- [x] 7.3 Implement `GET /rankings` endpoint
  - Accept scope, scope_value, limit, min_confidence parameters
  - Query from rankings_cache table
  - Filter by scope and confidence
  - Order by ranking_score DESC
  - Return buildings with ranking_score, ranking_position, ranking_factors
  - Apply 24-hour cache
  - _Requirements: 7_

- [x] 8. New Endpoint: Polygon Analysis
- [x] 8.1 Implement polygon validation
  - Validate geometry is Polygon or MultiPolygon
  - Validate max 1000 vertices
  - Calculate polygon area
  - Return HTTP 413 if area > 1000 km²
  - _Requirements: 8_

- [x] 8.2 Implement `POST /polygon/analyze` endpoint
  - Accept geometry, min_confidence, include_buildings, limit parameters
  - Use ST_CONTAINS for spatial query
  - Calculate aggregated statistics: total_buildings, total_area_m2, total_system_kwp, total_annual_production_kwh, total_installation_cost_thb, avg_confidence, avg_payback_years
  - Optionally return individual buildings array
  - Return processing_time_ms
  - _Requirements: 8_


- [x] 9. New Endpoint: Admin Data Quality
- [x] 9.1 Implement API key authentication
  - Create verify_api_key() dependency
  - Check X-API-Key header
  - Validate against ADMIN_API_KEYS environment variable
  - Return HTTP 401 for invalid/missing keys
  - _Requirements: 11_

- [x] 9.2 Implement `GET /admin/data-quality` endpoint
  - Require API key authentication
  - Query total_buildings count
  - Query low_confidence_count (confidence < 0.7)
  - Calculate low_confidence_percentage
  - Calculate data_freshness_days from collection date
  - Determine validation_status based on thresholds
  - Query quality_by_region with spatial joins
  - Apply 1-hour cache
  - Log all queries for audit trail
  - _Requirements: 11_

- [x] 9.3 Add data_quality_flag to building responses
  - Calculate flag based on confidence: high (>= 0.8), medium (0.7-0.8), low (< 0.7)
  - Add to enrich_building_data() function
  - _Requirements: 11_

- [x] 10. New Endpoint: Health Check
- [x] 10.1 Implement `GET /health` endpoint
  - Return status, version, timestamp
  - Check BigQuery connectivity
  - Check weather API connectivity (if configured)
  - Check cache status
  - Return uptime_seconds
  - _Requirements: 14_

- [x] 11. New Endpoint: Methodology Documentation
- [x] 11.1 Implement `GET /docs/methodology` endpoint
  - Return JSON with version, formulas, parameters, references
  - Include all calculation formulas with descriptions
  - Include all parameter defaults and ranges
  - Include references to academic sources
  - _Requirements: 10_

- [x] 12. Error Handling and Validation 
- [x] 12.1 Create custom error response format
  - Implement ErrorResponse model
  - Include error, detail, status_code, timestamp, request_id
  - _Requirements: All_

- [x] 12.2 Implement validation error handler
  - Override FastAPI's default validation error handler
  - Format errors with field names and messages
  - Return HTTP 422 with custom format
  - _Requirements: 3, 9, 13_

- [x] 12.3 Add request logging middleware
  - Generate unique request_id for each request
  - Log method, path, status, duration
  - Add X-Request-ID and X-Response-Time headers
  - _Requirements: 14_


- [x] 13. Security Implementation
- [x] 13.1 Implement rate limiting
  - Add slowapi Limiter
  - Apply 10 req/second limit to public endpoints
  - Apply 50 req/second limit to authenticated endpoints
  - Return HTTP 429 when exceeded
  - _Requirements: 4_

- [x] 13.2 Update CORS configuration
  - Keep existing allowed origins
  - Add proper credentials and methods
  - Set max_age for preflight caching
  - _Requirements: All_

- [x] 14. API Documentation
- [x] 14.1 Update OpenAPI configuration
  - Set title, version, description
  - Add servers (production, local)
  - Add authentication schemes
  - Add tags for endpoint grouping
  - _Requirements: 10_

- [x] 14.2 Add endpoint documentation
  - Add detailed descriptions to all endpoints
  - Add parameter descriptions with examples
  - Add response examples
  - Add error response examples
  - _Requirements: 10_

- [x] 14.3 Update BACKEND.md
  - Document all new endpoints
  - Document all new parameters
  - Document all new response fields
  - Update examples
  - _Requirements: 10_

- [x] 15. Testing
- [x] 15.1 Write unit tests for enrichment functions
  - Test calculate_accuracy_level() with various inputs
  - Test build_data_provenance()
  - Test enrich_building_data()
  - _Requirements: 1, 12, 15_

- [x] 15.2 Write unit tests for validation
  - Test filter validation logic
  - Test parameter range validation
  - Test polygon validation
  - _Requirements: 3, 8, 13_

- [x] 15.3 Write integration tests for endpoints
  - Test `/stats` with new fields
  - Test `/buildings/bbox` with filters and pagination
  - Test `/solar/calculate` with custom parameters
  - Test `/rankings` endpoint
  - Test `/polygon/analyze` endpoint
  - Test `/admin/data-quality` with authentication
  - Test error responses
  - _Requirements: All_

- [x] 15.4 Write load tests
  - Create Locust test scenarios
  - Test 100 concurrent users
  - Verify response times < 600ms (p95)
  - Verify cache effectiveness
  - _Requirements: 4, 14_


- [x] 16. Environment Configuration
- [x] 16.1 Update .env.example
  - Add ADMIN_API_KEYS
  - Add cache configuration variables
  - Add rate limiting variables
  - Add performance tuning variables
  - _Requirements: 4, 11_

- [x] 16.2 Update deployment configuration
  - Update Dockerfile if needed
  - Update cloudbuild.yaml if needed
  - Ensure environment variables are set in Cloud Run
  - _Requirements: All_

- [x] 17. Database Migrations
- [x] 17.1 Run BigQuery migrations
  - Execute migration 001: Create rankings_cache table
  - Execute migration 002: Create stats_summary materialized view
  - Execute migration 003: Create permitting_data table
  - Verify all tables and views created successfully
  - _Requirements: 7, 11, 14_

- [x] 17.2 Verify indexes and optimization
  - Verify spatial indexes exist
  - Verify clustering is applied
  - Test query performance
  - _Requirements: 14_

- [x] 18. Checkpoint - Integration Testing
  - Run all integration tests
  - Verify all endpoints work correctly
  - Verify caching works
  - Verify authentication works
  - Verify error handling works
  - Fix any issues found
  - _Requirements: All_

- [x] 19. Performance Optimization
- [x] 19.1 Optimize BigQuery queries
  - Review query execution plans
  - Add missing indexes if needed
  - Optimize spatial queries
  - _Requirements: 14_

- [x] 19.2 Verify caching effectiveness
  - Check cache hit rates
  - Adjust TTL values if needed
  - Verify cache headers are correct
  - _Requirements: 4_

- [x] 19.3 Run load tests
  - Execute Locust load tests
  - Verify performance targets met
  - Identify bottlenecks
  - Optimize as needed
  - _Requirements: 4, 14_


- [x] 20. Deployment Preparation
- [x] 20.1 Update version number
  - Update API version to 2.2.0
  - Update version in all documentation
  - Update version in OpenAPI spec
  - _Requirements: All_

- [x] 20.2 Final documentation review
  - Review BACKEND.md for completeness
  - Review OpenAPI documentation
  - Review README.md
  - Ensure all examples work
  - _Requirements: 10_

- [x] 20.3 Create deployment checklist
  - Verify all environment variables set
  - Verify BigQuery tables exist
  - Verify tests pass
  - Verify documentation updated
  - _Requirements: All_

- [x] 21. Staging Deployment
- [x] 21.1 Deploy to staging environment
  - Build and push Docker image
  - Deploy to Cloud Run staging
  - Verify deployment successful
  - _Requirements: All_

- [x] 21.2 Run smoke tests on staging
  - Test all endpoints manually
  - Verify responses correct
  - Verify performance acceptable
  - _Requirements: All_

- [x] 21.3 Run full test suite on staging
  - Run integration tests against staging
  - Run load tests against staging
  - Verify all tests pass
  - _Requirements: All_

- [x] 22. Production Deployment
- [x] 22.1 Deploy to production with traffic splitting
  - Deploy new version to Cloud Run
  - Start with 10% traffic
  - Monitor error rates and performance
  - _Requirements: All_

- [x] 22.2 Gradual rollout
  - Increase to 50% traffic if no issues
  - Monitor for 1 hour
  - Increase to 100% traffic if stable
  - _Requirements: All_

- [x] 22.3 Post-deployment verification
  - Verify all endpoints working
  - Verify caching working
  - Verify performance targets met
  - Monitor error logs
  - _Requirements: All_

- [x] 23. Final Checkpoint
  - All tests passing
  - All endpoints documented
  - Performance targets met
  - No critical errors in logs
  - User acceptance complete


## Implementation Notes

### Task Dependencies

- Tasks 1-3 are foundational and should be completed first
- Tasks 4-11 can be worked on in parallel after core infrastructure is ready
- Tasks 12-14 should be completed before testing
- Tasks 15-17 are testing and deployment preparation
- Tasks 18-23 are deployment and verification

### Testing Strategy

- Write tests alongside implementation (not after)
- Run tests frequently during development
- Use pytest for unit and integration tests
- Use Locust for load testing
- Aim for >80% code coverage

### Code Organization

- Keep api_bigquery.py as main entry point
- Move business logic to services/
- Move data models to models/
- Keep utilities in utils/
- This improves maintainability and testability

### Performance Considerations

- Always test query performance on BigQuery
- Use EXPLAIN to understand query plans
- Cache aggressively but with appropriate TTLs
- Monitor cache hit rates in production

### Backward Compatibility

- All existing endpoints must continue to work
- New fields are additions, not modifications
- Existing clients should not break
- Consider versioning for future breaking changes

### Security Best Practices

- Never commit API keys or secrets
- Use environment variables for configuration
- Validate all user inputs
- Implement rate limiting
- Log security-relevant events

## Estimated Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| Setup & Infrastructure | 1-3 | 2 days |
| Core Enhancements | 4-6 | 5 days |
| New Endpoints | 7-11 | 5 days |
| Security & Docs | 12-14 | 2 days |
| Testing | 15 | 3 days |
| Deployment Prep | 16-20 | 2 days |
| Deployment | 21-23 | 2 days |
| **Total** | | **21 days (~4 weeks)** |

## Success Criteria

- [ ] All 15 requirements implemented
- [ ] All tests passing (unit, integration, load)
- [ ] API response time p95 < 600ms
- [ ] Cache hit rate > 60%
- [ ] Error rate < 0.1%
- [ ] Documentation complete and accurate
- [ ] Zero breaking changes to existing API
- [ ] Successfully deployed to production

---

**Document Version**: 1.0  
**Created**: April 17, 2026  
**Status**: Ready for Implementation  
**Related Documents**:
- Requirements: `.kiro/specs/platform-improvements/requirements.md`
- Design: `.kiro/specs/platform-improvements/design.md`
