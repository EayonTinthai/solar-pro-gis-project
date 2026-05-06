"""
Tests for error handling and validation (Task 12)

Tests the custom error response format, validation error handler,
and request logging middleware.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json


def test_validation_error_format(test_client):
    """
    Test that validation errors return custom ErrorResponse format
    
    Validates: Task 12.2 - Validation error handler
    """
    # Test with invalid min_confidence (out of range)
    response = test_client.get("/buildings/bbox", params={
        "min_lat": 13.0,
        "max_lat": 14.0,
        "min_lon": 100.0,
        "max_lon": 101.0,
        "min_confidence": 1.5  # Invalid: > 1.0
    })
    
    assert response.status_code == 422
    data = response.json()
    
    # Check ErrorResponse format
    assert "error" in data
    assert "detail" in data
    assert "status_code" in data
    assert "timestamp" in data
    assert "request_id" in data
    
    assert data["error"] == "ValidationError"
    assert data["status_code"] == 422
    assert "min_confidence" in data["detail"]
    
    # Verify timestamp is valid ISO 8601
    datetime.fromisoformat(data["timestamp"])
    
    # Verify request_id format
    assert data["request_id"].startswith("req_")


def test_validation_error_multiple_fields(test_client):
    """
    Test validation errors with multiple invalid fields
    
    Validates: Task 12.2 - Multiple field validation
    """
    response = test_client.get("/buildings/bbox", params={
        "min_lat": 13.0,
        "max_lat": 14.0,
        "min_lon": 100.0,
        "max_lon": 101.0,
        "min_confidence": 1.5,  # Invalid
        "min_area_m2": -100  # Invalid: negative
    })
    
    assert response.status_code == 422
    data = response.json()
    
    # Should contain errors for both fields
    assert "min_confidence" in data["detail"] or "min_area_m2" in data["detail"]


def test_http_exception_format(test_client):
    """
    Test that HTTP exceptions return custom ErrorResponse format
    
    Validates: Task 12.2 - HTTP exception handler
    """
    # Test 404 error
    response = test_client.get("/nonexistent-endpoint")
    
    assert response.status_code == 404
    data = response.json()
    
    # Check ErrorResponse format
    assert "error" in data
    assert "detail" in data
    assert "status_code" in data
    assert "timestamp" in data
    assert "request_id" in data
    
    assert data["status_code"] == 404


def test_request_id_header(test_client):
    """
    Test that X-Request-ID header is added to responses
    
    Validates: Task 12.3 - Request logging middleware
    """
    response = test_client.get("/")
    
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")


def test_response_time_header(test_client):
    """
    Test that X-Response-Time header is added to responses
    
    Validates: Task 12.3 - Request logging middleware
    """
    response = test_client.get("/")
    
    assert "X-Response-Time" in response.headers
    assert response.headers["X-Response-Time"].endswith("ms")
    
    # Verify it's a valid number
    time_str = response.headers["X-Response-Time"].replace("ms", "")
    time_ms = float(time_str)
    assert time_ms >= 0


def test_request_id_consistency_in_error(test_client):
    """
    Test that request_id in error response matches X-Request-ID header
    
    Validates: Task 12.3 - Request ID consistency
    """
    response = test_client.get("/buildings/bbox", params={
        "min_lat": 13.0,
        "max_lat": 14.0,
        "min_lon": 100.0,
        "max_lon": 101.0,
        "min_confidence": 1.5  # Invalid
    })
    
    assert response.status_code == 422
    data = response.json()
    
    # Request ID in body should match header
    assert "X-Request-ID" in response.headers
    assert data["request_id"] == response.headers["X-Request-ID"]


def test_validation_error_descriptive_messages(test_client):
    """
    Test that validation errors have descriptive messages
    
    Validates: Task 12.2 - Descriptive error messages
    """
    # Test with missing required parameter
    response = test_client.get("/buildings/bbox", params={
        "min_lat": 13.0,
        "max_lat": 14.0,
        "min_lon": 100.0
        # Missing max_lon
    })
    
    assert response.status_code == 422
    data = response.json()
    
    # Should mention the missing field
    assert "max_lon" in data["detail"].lower() or "required" in data["detail"].lower()


def test_custom_params_validation_error(test_client):
    """
    Test validation errors for custom solar parameters
    
    Validates: Task 12.2 - Custom parameter validation (Req 13)
    """
    response = test_client.post("/solar/calculate", json={
        "latitude": 13.7563,
        "longitude": 100.5018,
        "area_m2": 250.0,
        "confidence": 0.95,
        "custom_params": {
            "panel_efficiency": 0.30  # Invalid: > 0.25
        }
    })
    
    assert response.status_code == 422
    data = response.json()
    
    assert "panel_efficiency" in data["detail"]
    assert "0.15" in data["detail"] and "0.25" in data["detail"]  # Should mention valid range


def test_error_response_timestamp_format(test_client):
    """
    Test that error response timestamps are in ISO 8601 format
    
    Validates: Task 12.1 - ErrorResponse model
    """
    response = test_client.get("/buildings/bbox", params={
        "min_lat": 13.0,
        "max_lat": 14.0,
        "min_lon": 100.0,
        "max_lon": 101.0,
        "min_confidence": 1.5
    })
    
    assert response.status_code == 422
    data = response.json()
    
    # Should be valid ISO 8601 timestamp
    timestamp = datetime.fromisoformat(data["timestamp"])
    assert timestamp is not None
    
    # Should be recent (within last minute)
    now = datetime.now()
    time_diff = abs((now - timestamp.replace(tzinfo=None)).total_seconds())
    assert time_diff < 60  # Within 1 minute


def test_polygon_validation_error(test_client):
    """
    Test validation error for invalid polygon
    
    Validates: Task 12.2 - Polygon validation errors (Req 8)
    """
    response = test_client.post("/polygon/analyze", json={
        "geometry": {
            "type": "Polygon",
            "coordinates": []  # Invalid: empty coordinates
        },
        "min_confidence": 0.7
    })
    
    assert response.status_code == 422
    data = response.json()
    
    assert "error" in data
    assert "detail" in data


def test_admin_endpoint_auth_error(test_client):
    """
    Test authentication error for admin endpoints
    
    Validates: Task 12.2 - Authentication errors (Req 11)
    """
    # Try to access admin endpoint without API key
    response = test_client.get("/admin/data-quality")
    
    assert response.status_code == 401
    data = response.json()
    
    # Check ErrorResponse format
    assert "error" in data
    assert "detail" in data
    assert "status_code" in data
    assert data["status_code"] == 401
    assert "API key" in data["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
