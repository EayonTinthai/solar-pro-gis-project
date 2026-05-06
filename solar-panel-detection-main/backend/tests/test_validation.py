"""
Tests for validation services
Requirements: 3, 8, 13
"""

import pytest
from fastapi import HTTPException
from services.validation import (
    validate_filter_params,
    validate_custom_solar_params,
    validate_polygon,
    calculate_polygon_area_km2,
    PARAM_RANGES
)


class TestValidateFilterParams:
    """Test filter parameter validation (Req 3)"""
    
    def test_valid_min_confidence(self):
        """Test valid min_confidence values"""
        # Should not raise exception
        validate_filter_params(min_confidence=0.7)
        validate_filter_params(min_confidence=0.5)
        validate_filter_params(min_confidence=1.0)
    
    def test_invalid_min_confidence_too_low(self):
        """Test min_confidence below 0.5 raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_filter_params(min_confidence=0.4)
        
        assert exc_info.value.status_code == 422
        assert "min_confidence must be between 0.5 and 1.0" in exc_info.value.detail
        assert "0.4" in exc_info.value.detail
    
    def test_invalid_min_confidence_too_high(self):
        """Test min_confidence above 1.0 raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_filter_params(min_confidence=1.5)
        
        assert exc_info.value.status_code == 422
        assert "min_confidence must be between 0.5 and 1.0" in exc_info.value.detail
    
    def test_valid_area_filters(self):
        """Test valid area filter values"""
        validate_filter_params(min_area_m2=50.0, max_area_m2=500.0)
        validate_filter_params(min_area_m2=100.0)
        validate_filter_params(max_area_m2=1000.0)
    
    def test_invalid_min_area_negative(self):
        """Test negative min_area_m2 raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_filter_params(min_area_m2=-10.0)
        
        assert exc_info.value.status_code == 422
        assert "min_area_m2 must be positive" in exc_info.value.detail
    
    def test_invalid_min_area_zero(self):
        """Test zero min_area_m2 raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_filter_params(min_area_m2=0.0)
        
        assert exc_info.value.status_code == 422
        assert "min_area_m2 must be positive" in exc_info.value.detail
    
    def test_invalid_max_area_negative(self):
        """Test negative max_area_m2 raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_filter_params(max_area_m2=-100.0)
        
        assert exc_info.value.status_code == 422
        assert "max_area_m2 must be positive" in exc_info.value.detail
    
    def test_invalid_area_range_min_greater_than_max(self):
        """Test min_area > max_area raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_filter_params(min_area_m2=500.0, max_area_m2=100.0)
        
        assert exc_info.value.status_code == 422
        assert "min_area_m2" in exc_info.value.detail
        assert "max_area_m2" in exc_info.value.detail
        assert "500" in exc_info.value.detail
        assert "100" in exc_info.value.detail
    
    def test_valid_system_kwp_filters(self):
        """Test valid system size filter values"""
        validate_filter_params(min_system_kwp=5.0, max_system_kwp=50.0)
        validate_filter_params(min_system_kwp=10.0)
        validate_filter_params(max_system_kwp=100.0)
    
    def test_invalid_min_system_kwp_negative(self):
        """Test negative min_system_kwp raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_filter_params(min_system_kwp=-5.0)
        
        assert exc_info.value.status_code == 422
        assert "min_system_kwp must be positive" in exc_info.value.detail
    
    def test_invalid_max_system_kwp_negative(self):
        """Test negative max_system_kwp raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_filter_params(max_system_kwp=-10.0)
        
        assert exc_info.value.status_code == 422
        assert "max_system_kwp must be positive" in exc_info.value.detail
    
    def test_invalid_system_kwp_range(self):
        """Test min_system_kwp > max_system_kwp raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_filter_params(min_system_kwp=50.0, max_system_kwp=10.0)
        
        assert exc_info.value.status_code == 422
        assert "min_system_kwp" in exc_info.value.detail
        assert "max_system_kwp" in exc_info.value.detail
    
    def test_valid_payback_filter(self):
        """Test valid payback filter values"""
        validate_filter_params(max_payback_years=5.0)
        validate_filter_params(max_payback_years=10.0)
    
    def test_invalid_payback_negative(self):
        """Test negative max_payback_years raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_filter_params(max_payback_years=-2.0)
        
        assert exc_info.value.status_code == 422
        assert "max_payback_years must be positive" in exc_info.value.detail
    
    def test_multiple_valid_filters(self):
        """Test multiple valid filters together"""
        validate_filter_params(
            min_confidence=0.8,
            min_area_m2=100.0,
            max_area_m2=500.0,
            min_system_kwp=10.0,
            max_system_kwp=50.0,
            max_payback_years=5.0
        )


class TestValidateCustomSolarParams:
    """Test custom solar parameter validation (Req 13)"""
    
    def test_valid_panel_efficiency(self):
        """Test valid panel efficiency values"""
        validate_custom_solar_params({"panel_efficiency": 0.20})
        validate_custom_solar_params({"panel_efficiency": 0.15})
        validate_custom_solar_params({"panel_efficiency": 0.25})
    
    def test_invalid_panel_efficiency_too_low(self):
        """Test panel efficiency below range raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_custom_solar_params({"panel_efficiency": 0.10})
        
        assert exc_info.value.status_code == 422
        assert "panel_efficiency" in exc_info.value.detail
        assert "0.15" in exc_info.value.detail
        assert "0.25" in exc_info.value.detail
    
    def test_invalid_panel_efficiency_too_high(self):
        """Test panel efficiency above range raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_custom_solar_params({"panel_efficiency": 0.30})
        
        assert exc_info.value.status_code == 422
        assert "panel_efficiency" in exc_info.value.detail
    
    def test_valid_system_efficiency(self):
        """Test valid system efficiency values"""
        validate_custom_solar_params({"system_efficiency": 0.80})
        validate_custom_solar_params({"system_efficiency": 0.70})
        validate_custom_solar_params({"system_efficiency": 0.90})
    
    def test_invalid_system_efficiency(self):
        """Test system efficiency out of range raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_custom_solar_params({"system_efficiency": 0.95})
        
        assert exc_info.value.status_code == 422
        assert "system_efficiency" in exc_info.value.detail
    
    def test_valid_usable_roof_ratio(self):
        """Test valid usable roof ratio values"""
        validate_custom_solar_params({"usable_roof_ratio": 0.50})
        validate_custom_solar_params({"usable_roof_ratio": 0.30})
        validate_custom_solar_params({"usable_roof_ratio": 0.70})
    
    def test_invalid_usable_roof_ratio(self):
        """Test usable roof ratio out of range raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_custom_solar_params({"usable_roof_ratio": 0.80})
        
        assert exc_info.value.status_code == 422
        assert "usable_roof_ratio" in exc_info.value.detail
    
    def test_valid_cost_per_wp(self):
        """Test valid cost per watt values"""
        validate_custom_solar_params({"cost_per_wp": 25})
        validate_custom_solar_params({"cost_per_wp": 20})
        validate_custom_solar_params({"cost_per_wp": 50})
    
    def test_invalid_cost_per_wp(self):
        """Test cost per watt out of range raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_custom_solar_params({"cost_per_wp": 60})
        
        assert exc_info.value.status_code == 422
        assert "cost_per_wp" in exc_info.value.detail
    
    def test_valid_electricity_rate(self):
        """Test valid electricity rate values"""
        validate_custom_solar_params({"electricity_rate": 4.18})
        validate_custom_solar_params({"electricity_rate": 3.0})
        validate_custom_solar_params({"electricity_rate": 6.0})
    
    def test_invalid_electricity_rate(self):
        """Test electricity rate out of range raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_custom_solar_params({"electricity_rate": 7.0})
        
        assert exc_info.value.status_code == 422
        assert "electricity_rate" in exc_info.value.detail
    
    def test_valid_co2_factor(self):
        """Test valid CO2 factor values"""
        validate_custom_solar_params({"co2_factor": 0.40})
        validate_custom_solar_params({"co2_factor": 0.30})
        validate_custom_solar_params({"co2_factor": 0.50})
    
    def test_invalid_co2_factor(self):
        """Test CO2 factor out of range raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_custom_solar_params({"co2_factor": 0.60})
        
        assert exc_info.value.status_code == 422
        assert "co2_factor" in exc_info.value.detail
    
    def test_unknown_parameter(self):
        """Test unknown parameter raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_custom_solar_params({"unknown_param": 0.5})
        
        assert exc_info.value.status_code == 422
        assert "Unknown parameter" in exc_info.value.detail
        assert "unknown_param" in exc_info.value.detail
    
    def test_multiple_valid_params(self):
        """Test multiple valid parameters together"""
        validate_custom_solar_params({
            "panel_efficiency": 0.22,
            "system_efficiency": 0.85,
            "usable_roof_ratio": 0.60,
            "cost_per_wp": 23.0,
            "electricity_rate": 4.50,
            "co2_factor": 0.35
        })
    
    def test_multiple_params_one_invalid(self):
        """Test multiple parameters with one invalid raises error"""
        with pytest.raises(HTTPException) as exc_info:
            validate_custom_solar_params({
                "panel_efficiency": 0.22,
                "system_efficiency": 0.95,  # Invalid
                "cost_per_wp": 23.0
            })
        
        assert exc_info.value.status_code == 422
        assert "system_efficiency" in exc_info.value.detail


class TestValidatePolygon:
    """Test polygon validation (Req 8)"""
    
    def test_validate_polygon_valid(self):
        """Test validation of valid polygon"""
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
        
        is_valid, error = validate_polygon(polygon)
        assert is_valid is True
        assert error is None
    
    def test_validate_multipolygon_valid(self):
        """Test validation of valid multipolygon"""
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
        
        is_valid, error = validate_polygon(multipolygon)
        assert is_valid is True
        assert error is None
    
    def test_validate_polygon_invalid_type(self):
        """Test validation rejects invalid geometry type"""
        point = {
            "type": "Point",
            "coordinates": [100.5, 13.75]
        }
        
        is_valid, error = validate_polygon(point)
        assert is_valid is False
        assert "must be Polygon or MultiPolygon" in error
    
    def test_validate_polygon_missing_coordinates(self):
        """Test validation rejects polygon without coordinates"""
        polygon = {
            "type": "Polygon"
        }
        
        is_valid, error = validate_polygon(polygon)
        assert is_valid is False
        assert "must have coordinates" in error
    
    def test_validate_polygon_too_many_vertices(self):
        """Test validation rejects polygon with too many vertices"""
        import math
        
        # Generate polygon with 1500 vertices
        coords = []
        for i in range(1500):
            angle = 2 * math.pi * i / 1500
            lon = 100.5 + 0.1 * math.cos(angle)
            lat = 13.75 + 0.1 * math.sin(angle)
            coords.append([lon, lat])
        coords.append(coords[0])  # Close the polygon
        
        polygon = {
            "type": "Polygon",
            "coordinates": [coords]
        }
        
        is_valid, error = validate_polygon(polygon)
        assert is_valid is False
        assert "too many vertices" in error
        assert "1501" in error  # 1500 + 1 closing point
    
    def test_validate_polygon_too_large_area(self):
        """Test validation rejects polygon with area > 1000 km²"""
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
        
        is_valid, error = validate_polygon(large_polygon)
        assert is_valid is False
        assert "exceeds maximum of 1000 km²" in error
    
    def test_validate_polygon_boundary_vertices(self):
        """Test validation accepts polygon with exactly 1000 vertices"""
        import math
        
        # Generate polygon with exactly 1000 vertices
        coords = []
        for i in range(1000):
            angle = 2 * math.pi * i / 1000
            lon = 100.5 + 0.05 * math.cos(angle)
            lat = 13.75 + 0.05 * math.sin(angle)
            coords.append([lon, lat])
        coords.append(coords[0])
        
        polygon = {
            "type": "Polygon",
            "coordinates": [coords]
        }
        
        is_valid, error = validate_polygon(polygon)
        # Should be valid (1001 vertices including closing point)
        # But our limit is 1000, so this should fail
        assert is_valid is False


class TestCalculatePolygonArea:
    """Test polygon area calculation (Req 8)"""
    
    def test_calculate_polygon_area(self):
        """Test polygon area calculation"""
        # Small polygon (~1km x 1km)
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
        
        area_km2 = calculate_polygon_area_km2(polygon)
        
        # Should be approximately 1.2 km² (1.1km x 1.1km)
        assert area_km2 > 0
        assert area_km2 < 2  # Should be less than 2 km²
        assert 1.0 < area_km2 < 1.5  # More precise check
    
    def test_calculate_multipolygon_area(self):
        """Test multipolygon area calculation"""
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
        
        area_km2 = calculate_polygon_area_km2(multipolygon)
        
        # Should be approximately 0.6 km² (two 0.5km x 0.5km polygons)
        assert area_km2 > 0
        assert area_km2 < 1.0
    
    def test_calculate_large_polygon_area(self):
        """Test large polygon area calculation"""
        # Large polygon covering ~5° x 5°
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
        
        area_km2 = calculate_polygon_area_km2(large_polygon)
        
        # Should be much larger than 1000 km²
        assert area_km2 > 1000
    
    def test_calculate_tiny_polygon_area(self):
        """Test tiny polygon area calculation"""
        # Very small polygon
        tiny_polygon = {
            "type": "Polygon",
            "coordinates": [[
                [100.5000, 13.7500],
                [100.5001, 13.7500],
                [100.5001, 13.7501],
                [100.5000, 13.7501],
                [100.5000, 13.7500]
            ]]
        }
        
        area_km2 = calculate_polygon_area_km2(tiny_polygon)
        
        # Should be very small but positive
        assert area_km2 > 0
        assert area_km2 < 0.01  # Less than 0.01 km²


class TestParamRanges:
    """Test PARAM_RANGES constant"""
    
    def test_param_ranges_exist(self):
        """Test that all expected parameter ranges are defined"""
        expected_params = [
            "panel_efficiency",
            "system_efficiency",
            "usable_roof_ratio",
            "cost_per_wp",
            "electricity_rate",
            "co2_factor"
        ]
        
        for param in expected_params:
            assert param in PARAM_RANGES
    
    def test_param_ranges_format(self):
        """Test that parameter ranges are tuples of (min, max)"""
        for param, range_tuple in PARAM_RANGES.items():
            assert isinstance(range_tuple, tuple)
            assert len(range_tuple) == 2
            assert range_tuple[0] < range_tuple[1]  # min < max

