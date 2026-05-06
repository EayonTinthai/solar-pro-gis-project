"""
Pytest configuration and fixtures
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """
    Create a test client for the API
    
    Note: Import app here to avoid circular imports
    """
    from api_bigquery import app
    return TestClient(app)


@pytest.fixture
def sample_building_data():
    """Sample building data for testing"""
    return {
        "id": 123456,
        "open_buildings_id": "OB_12345",
        "latitude": 13.7563,
        "longitude": 100.5018,
        "area_m2": 250.0,
        "confidence": 0.85,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[100.5, 13.75], [100.51, 13.75], [100.51, 13.76], [100.5, 13.76], [100.5, 13.75]]]
        }
    }


@pytest.fixture
def sample_solar_request():
    """Sample solar calculation request"""
    return {
        "latitude": 13.7563,
        "longitude": 100.5018,
        "area_m2": 250.0,
        "confidence": 0.9,
        "tilt": None,
        "azimuth": 180
    }
