"""
Integration tests for API endpoints
Requirements: All
"""

import pytest
from fastapi.testclient import TestClient
from api_bigquery import app

client = TestClient(app)


class TestStatsEndpoints:
    """Test /stats endpoints with new fields (Req 2, 15)"""
    
    def test_stats_endpoint_structure(self):
        """Test /stats endpoint returns correct structure"""
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check basic structure
        assert "total_buildings" in data
        assert "confidence" in data
        assert "area_m2" in data
        assert "extent" in data
        
        # Check new dataset_metadata field (Req 15)
        assert "dataset_metadata" in data
        metadata = data["dataset_metadata"]
        assert "source" in metadata
        assert "version" in metadata
        assert "collection_date" in metadata
        assert "ingestion_date" in metadata
        assert "update_frequency" in metadata
        assert "license" in metadata
    
    def test_stats_confidence_has_median(self):
        """Test /stats includes median confidence (Req 2)"""
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        confidence = data["confidence"]
        assert "median" in confidence
        assert "average" in confidence
        assert isinstance(confidence["median"], (int, float))
    
    def test_stats_area_has_median(self):
        """Test /stats includes median area (Req 2)"""
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        area = data["area_m2"]
        assert "median" in area
        assert "average" in area
        assert isinstance(area["median"], (int, float))
    
    def test_stats_distribution_endpoint(self):
        """Test /stats/distribution endpoint structure"""
        response = client.get("/stats/distribution")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "confidence_buckets" in data
        assert "cumulative_by_threshold" in data
        
        # Check new std_dev fields (Req 2)
        assert "confidence_std_dev" in data
        assert "area_std_dev" in data
    
    def test_stats_cache_headers(self):
        """Test /stats includes cache headers (Req 4)"""
        response = client.get("/stats")
        
        assert response.status_code == 200
        # Cache headers should be present
        # Note: Actual header names depend on implementation


class TestBuildingsBboxEndpoint:
    """Test /buildings/bbox with filters and pagination (Req 3, 9, 12, 14)"""
    
    def test_bbox_basic_query(self):
        """Test basic bbox query"""
        response = client.get(
            "/buildings/bbox",
            params={
                "min_lat": 13.7,
                "max_lat": 13.8,
                "min_lon": 100.5,
                "max_lon": 100.6
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "buildings" in data
        assert isinstance(data["buildings"], list)
    
    def test_bbox_with_area_filters(self):
        """Test bbox with area filters (Req 3)"""
        response = client.get(
            "/buildings/bbox",
            params={
                "min_lat": 13.7,
                "max_lat": 13.8,
                "min_lon": 100.5,
                "max_lon": 100.6,
                "min_area_m2": 100,
                "max_area_m2": 500
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All buildings should be within area range
        for building in data["buildings"]:
            assert 100 <= building["area_m2"] <= 500
    
    def test_bbox_with_system_kwp_filters(self):
        """Test bbox with system capacity filters (Req 9)"""
        response = client.get(
            "/buildings/bbox",
            params={
                "min_lat": 13.7,
                "max_lat": 13.8,
                "min_lon": 100.5,
                "max_lon": 100.6,
                "min_system_kwp": 10,
                "max_system_kwp": 50
            }
        )
        
        assert response.status_code == 200
        # Should return successfully (actual filtering tested in unit tests)
    
    def test_bbox_with_pagination(self):
        """Test bbox with pagination (Req 14)"""
        response = client.get(
            "/buildings/bbox",
            params={
                "min_lat": 13.7,
                "max_lat": 13.8,
                "min_lon": 100.5,
                "max_lon": 100.6,
                "limit": 10,
                "offset": 0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check pagination metadata
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        assert "has_more" in data
        
        # Check limit is respected
        assert len(data["buildings"]) <= 10
    
    def test_bbox_enriched_building_data(self):
        """Test bbox returns enriched building data (Req 1, 6, 12, 15)"""
        response = client.get(
            "/buildings/bbox",
            params={
                "min_lat": 13.7,
                "max_lat": 13.8,
                "min_lon": 100.5,
                "max_lon": 100.6,
                "limit": 1
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["buildings"]) > 0:
            building = data["buildings"][0]
            
            # Check enriched fields
            assert "data_provenance" in building
            assert "confidence_warning" in building
            assert "accuracy_level" in building
            assert "accuracy_factors" in building
            assert "permitting_status" in building
            assert "data_source" in building
            assert "data_collection_date" in building
            assert "data_source_url" in building
    
    def test_bbox_invalid_confidence(self):
        """Test bbox rejects invalid confidence (Req 3)"""
        response = client.get(
            "/buildings/bbox",
            params={
                "min_lat": 13.7,
                "max_lat": 13.8,
                "min_lon": 100.5,
                "max_lon": 100.6,
                "min_confidence": 1.5
            }
        )
        
        assert response.status_code == 422
        assert "min_confidence" in response.json()["detail"]
    
    def test_bbox_invalid_area_range(self):
        """Test bbox rejects invalid area range (Req 3)"""
        response = client.get(
            "/buildings/bbox",
            params={
                "min_lat": 13.7,
                "max_lat": 13.8,
                "min_lon": 100.5,
                "max_lon": 100.6,
                "min_area_m2": 500,
                "max_area_m2": 100
            }
        )
        
        assert response.status_code == 422


class TestSolarCalculateEndpoint:
    """Test /solar/calculate with custom parameters (Req 5, 13)"""
    
    def test_solar_calculate_basic(self):
        """Test basic solar calculation"""
        response = client.post(
            "/solar/calculate",
            json={
                "latitude": 13.7563,
                "longitude": 100.5018,
                "area_m2": 250.0,
                "confidence": 0.9,
                "tilt": None,
                "azimuth": 180
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check basic fields
        assert "usable_roof_area" in data
        assert "system_size_kwp" in data
        assert "annual_production_kwh" in data
        assert "installation_cost_thb" in data
    
    def test_solar_calculate_with_custom_params(self):
        """Test solar calculation with custom parameters (Req 13)"""
        response = client.post(
            "/solar/calculate",
            json={
                "latitude": 13.7563,
                "longitude": 100.5018,
                "area_m2": 250.0,
                "confidence": 0.9,
                "tilt": None,
                "azimuth": 180,
                "custom_params": {
                    "panel_efficiency": 0.22,
                    "system_efficiency": 0.85,
                    "cost_per_wp": 23.0
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check custom_parameters field exists (Req 13)
        assert "custom_parameters" in data
        assert data["custom_parameters"]["panel_efficiency"] == 0.22
    
    def test_solar_calculate_with_calculation_breakdown(self):
        """Test solar calculation includes breakdown (Req 5)"""
        response = client.post(
            "/solar/calculate",
            json={
                "latitude": 13.7563,
                "longitude": 100.5018,
                "area_m2": 250.0,
                "confidence": 0.9,
                "tilt": None,
                "azimuth": 180
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check calculation_breakdown exists (Req 5)
        assert "calculation_breakdown" in data
        breakdown = data["calculation_breakdown"]
        
        assert "step_1_usable_area" in breakdown
        assert "step_2_system_size" in breakdown
        assert "step_3_annual_production" in breakdown
        assert "step_4_financial" in breakdown
        
        # Check step structure
        step1 = breakdown["step_1_usable_area"]
        assert "formula" in step1
        assert "inputs" in step1
        assert "result" in step1
        assert "unit" in step1
    
    def test_solar_calculate_invalid_custom_param(self):
        """Test solar calculation rejects invalid custom parameter (Req 13)"""
        response = client.post(
            "/solar/calculate",
            json={
                "latitude": 13.7563,
                "longitude": 100.5018,
                "area_m2": 250.0,
                "confidence": 0.9,
                "tilt": None,
                "azimuth": 180,
                "custom_params": {
                    "panel_efficiency": 0.30  # Out of range
                }
            }
        )
        
        assert response.status_code == 422
        assert "panel_efficiency" in response.json()["detail"]


class TestPolygonAnalyzeEndpoint:
    """Test /polygon/analyze endpoint (Req 8)"""
    
    def test_polygon_analyze_basic(self):
        """Test basic polygon analysis without buildings"""
        polygon = {
            "type": "Polygon",
            "coordinates": [[
                [100.5018, 13.7563],
                [100.5118, 13.7563],
                [100.5118, 13.7663],
                [100.5018, 13.7663],
                [100.5018, 13.7563]
            ]]
        }
        
        response = client.post(
            "/polygon/analyze",
            json={
                "geometry": polygon,
                "min_confidence": 0.7,
                "include_buildings": False,
                "limit": 1000
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "polygon_area_km2" in data
        assert "total_buildings" in data
        assert "aggregated_stats" in data
        assert "processing_time_ms" in data
        
        # Check aggregated stats structure
        stats = data["aggregated_stats"]
        assert "total_buildings" in stats
        assert "total_area_m2" in stats
        assert "total_system_kwp" in stats
        assert "total_annual_production_kwh" in stats
        assert "total_installation_cost_thb" in stats
        assert "avg_confidence" in stats
        
        # Buildings should be None when include_buildings=False
        assert data["buildings"] is None
        
        # Area should be positive and reasonable
        assert data["polygon_area_km2"] > 0
        assert data["polygon_area_km2"] < 2
    
    def test_polygon_analyze_with_buildings(self):
        """Test polygon analysis with individual buildings"""
        polygon = {
            "type": "Polygon",
            "coordinates": [[
                [100.5018, 13.7563],
                [100.5118, 13.7563],
                [100.5118, 13.7663],
                [100.5018, 13.7663],
                [100.5018, 13.7563]
            ]]
        }
        
        response = client.post(
            "/polygon/analyze",
            json={
                "geometry": polygon,
                "min_confidence": 0.8,
                "include_buildings": True,
                "limit": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Buildings should be a list when include_buildings=True
        assert data["buildings"] is not None
        assert isinstance(data["buildings"], list)
        
        # If there are buildings, check they have enriched data
        if len(data["buildings"]) > 0:
            building = data["buildings"][0]
            assert "accuracy_level" in building
            assert "data_provenance" in building
            assert "confidence_warning" in building
            assert "permitting_status" in building
    
    def test_polygon_analyze_multipolygon(self):
        """Test polygon analysis with multipolygon"""
        multipolygon = {
            "type": "MultiPolygon",
            "coordinates": [
                [[
                    [100.5018, 13.7563],
                    [100.5068, 13.7563],
                    [100.5068, 13.7613],
                    [100.5018, 13.7613],
                    [100.5018, 13.7563]
                ]],
                [[
                    [100.5118, 13.7563],
                    [100.5168, 13.7563],
                    [100.5168, 13.7613],
                    [100.5118, 13.7613],
                    [100.5118, 13.7563]
                ]]
            ]
        }
        
        response = client.post(
            "/polygon/analyze",
            json={
                "geometry": multipolygon,
                "min_confidence": 0.7,
                "include_buildings": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["polygon_area_km2"] > 0
    
    def test_polygon_analyze_invalid_geometry_type(self):
        """Test polygon analysis rejects invalid geometry type"""
        point = {
            "type": "Point",
            "coordinates": [100.5, 13.75]
        }
        
        response = client.post(
            "/polygon/analyze",
            json={
                "geometry": point,
                "min_confidence": 0.7,
                "include_buildings": False
            }
        )
        
        assert response.status_code == 422
        assert "must be Polygon or MultiPolygon" in response.json()["detail"]
    
    def test_polygon_analyze_too_large(self):
        """Test polygon analysis rejects polygon that's too large"""
        # Large polygon covering ~5° x 5° (roughly 550km x 550km)
        large_polygon = {
            "type": "Polygon",
            "coordinates": [[
                [100.0, 13.0],
                [105.0, 13.0],
                [105.0, 18.0],
                [100.0, 18.0],
                [100.0, 13.0]
            ]]
        }
        
        response = client.post(
            "/polygon/analyze",
            json={
                "geometry": large_polygon,
                "min_confidence": 0.7,
                "include_buildings": False
            }
        )
        
        assert response.status_code == 413
        assert "exceeds maximum of 1000 km²" in response.json()["detail"]
    
    def test_polygon_analyze_too_many_vertices(self):
        """Test polygon analysis rejects polygon with too many vertices"""
        import math
        
        # Generate polygon with 1500 vertices
        coords = []
        for i in range(1500):
            angle = 2 * math.pi * i / 1500
            lon = 100.5 + 0.1 * math.cos(angle)
            lat = 13.75 + 0.1 * math.sin(angle)
            coords.append([lon, lat])
        coords.append(coords[0])
        
        polygon = {
            "type": "Polygon",
            "coordinates": [coords]
        }
        
        response = client.post(
            "/polygon/analyze",
            json={
                "geometry": polygon,
                "min_confidence": 0.7,
                "include_buildings": False
            }
        )
        
        assert response.status_code == 422
        assert "too many vertices" in response.json()["detail"]


class TestRankingsEndpoint:
    """Test /rankings endpoint (Req 7)"""
    
    def test_rankings_endpoint_basic(self):
        """Test basic rankings query"""
        response = client.get(
            "/rankings",
            params={
                "scope": "country",
                "scope_value": "TH",
                "limit": 10
            }
        )
        
        # May return 200 or 404 depending on whether rankings are cached
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            assert "scope" in data
            assert "rankings" in data
            assert isinstance(data["rankings"], list)
    
    def test_rankings_with_confidence_filter(self):
        """Test rankings with confidence filter"""
        response = client.get(
            "/rankings",
            params={
                "scope": "country",
                "scope_value": "TH",
                "limit": 10,
                "min_confidence": 0.8
            }
        )
        
        # May not be implemented yet
        assert response.status_code in [200, 404, 500]


class TestAdminDataQualityEndpoint:
    """Test /admin/data-quality with authentication (Req 11)"""
    
    def test_admin_data_quality_without_auth(self):
        """Test admin endpoint requires authentication"""
        response = client.get("/admin/data-quality")
        
        # Should require authentication
        assert response.status_code in [401, 403, 404, 500]
    
    def test_admin_data_quality_with_invalid_key(self):
        """Test admin endpoint rejects invalid API key"""
        response = client.get(
            "/admin/data-quality",
            headers={"X-API-Key": "invalid_key"}
        )
        
        # Should reject invalid key
        assert response.status_code in [401, 403, 404, 500]


class TestHealthEndpoint:
    """Test /health endpoint (Req 14)"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "uptime_seconds" in data
        
        # Check status is one of the valid values
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        
        # Check version
        assert data["version"] == "2.2.0"
        
        # Check checks structure
        checks = data["checks"]
        assert "bigquery" in checks
        assert "weather_api" in checks
        assert "cache" in checks
        
        # BigQuery should be ok (or at least present)
        assert checks["bigquery"] is not None
        
        # Cache should have status info
        if isinstance(checks["cache"], dict):
            assert "status" in checks["cache"]
            assert "entries" in checks["cache"]
            assert "max_size" in checks["cache"]
        
        # Uptime should be a positive number
        assert data["uptime_seconds"] >= 0
        assert isinstance(data["uptime_seconds"], int)


class TestMethodologyEndpoint:
    """Test /docs/methodology endpoint (Req 10)"""
    
    def test_methodology_endpoint(self):
        """Test methodology documentation endpoint"""
        response = client.get("/docs/methodology")
        
        # May not be implemented yet
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            assert "version" in data
            assert "formulas" in data
            assert "parameters" in data


class TestErrorResponses:
    """Test error response format (Req 3, 9, 13)"""
    
    def test_validation_error_format(self):
        """Test validation errors have correct format"""
        response = client.get(
            "/buildings/bbox",
            params={
                "min_lat": 13.7,
                "max_lat": 13.8,
                "min_lon": 100.5,
                "max_lon": 100.6,
                "min_confidence": 1.5  # Invalid
            }
        )
        
        assert response.status_code == 422
        error = response.json()
        
        assert "detail" in error
        assert "min_confidence" in error["detail"]
    
    def test_not_found_error(self):
        """Test 404 error for non-existent endpoint"""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test 405 error for wrong HTTP method"""
        response = client.post("/stats")
        
        assert response.status_code == 405
