"""
Test script for polygon analysis endpoint
"""

import requests
import json

# Test polygon (small area in Bangkok)
test_polygon = {
    "type": "Polygon",
    "coordinates": [[
        [100.5018, 13.7563],  # Bangkok center
        [100.5118, 13.7563],
        [100.5118, 13.7663],
        [100.5018, 13.7663],
        [100.5018, 13.7563]
    ]]
}

# Test MultiPolygon
test_multipolygon = {
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

# Test invalid geometry (too many vertices)
def generate_large_polygon(num_vertices):
    """Generate a polygon with many vertices"""
    import math
    coords = []
    for i in range(num_vertices):
        angle = 2 * math.pi * i / num_vertices
        lon = 100.5 + 0.1 * math.cos(angle)
        lat = 13.75 + 0.1 * math.sin(angle)
        coords.append([lon, lat])
    coords.append(coords[0])  # Close the polygon
    return {
        "type": "Polygon",
        "coordinates": [coords]
    }

# Test validation functions
def test_validation():
    """Test polygon validation functions"""
    from services.validation import validate_polygon, calculate_polygon_area_km2
    
    print("Testing polygon validation...")
    
    # Test valid polygon
    is_valid, error = validate_polygon(test_polygon)
    print(f"✓ Valid polygon: {is_valid}, error: {error}")
    assert is_valid, "Valid polygon should pass validation"
    
    # Test valid multipolygon
    is_valid, error = validate_polygon(test_multipolygon)
    print(f"✓ Valid multipolygon: {is_valid}, error: {error}")
    assert is_valid, "Valid multipolygon should pass validation"
    
    # Test invalid geometry type
    invalid_geom = {"type": "Point", "coordinates": [100.5, 13.75]}
    is_valid, error = validate_polygon(invalid_geom)
    print(f"✓ Invalid geometry type: {is_valid}, error: {error}")
    assert not is_valid, "Invalid geometry type should fail"
    
    # Test too many vertices
    large_polygon = generate_large_polygon(1500)
    is_valid, error = validate_polygon(large_polygon)
    print(f"✓ Too many vertices: {is_valid}, error: {error}")
    assert not is_valid, "Polygon with too many vertices should fail"
    
    # Test area calculation
    area = calculate_polygon_area_km2(test_polygon)
    print(f"✓ Polygon area: {area:.2f} km²")
    assert area > 0, "Area should be positive"
    assert area < 1000, "Test polygon should be under 1000 km²"
    
    print("\n✅ All validation tests passed!")

def test_endpoint_local():
    """Test the polygon analysis endpoint (requires local server)"""
    base_url = "http://localhost:8080"
    
    print("\nTesting polygon analysis endpoint...")
    
    # Test 1: Basic polygon analysis without buildings
    print("\n1. Testing basic polygon analysis...")
    response = requests.post(
        f"{base_url}/polygon/analyze",
        json={
            "geometry": test_polygon,
            "min_confidence": 0.7,
            "include_buildings": False,
            "limit": 1000
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Polygon area: {data['polygon_area_km2']} km²")
        print(f"✓ Total buildings: {data['total_buildings']}")
        print(f"✓ Processing time: {data['processing_time_ms']} ms")
        print(f"✓ Aggregated stats:")
        print(f"  - Total area: {data['aggregated_stats']['total_area_m2']} m²")
        print(f"  - Total system: {data['aggregated_stats']['total_system_kwp']} kWp")
        print(f"  - Avg confidence: {data['aggregated_stats']['avg_confidence']}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
    
    # Test 2: Polygon analysis with buildings
    print("\n2. Testing polygon analysis with buildings...")
    response = requests.post(
        f"{base_url}/polygon/analyze",
        json={
            "geometry": test_polygon,
            "min_confidence": 0.8,
            "include_buildings": True,
            "limit": 10
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Buildings returned: {len(data['buildings']) if data['buildings'] else 0}")
        if data['buildings'] and len(data['buildings']) > 0:
            print(f"✓ First building has enriched data:")
            building = data['buildings'][0]
            print(f"  - Accuracy level: {building.get('accuracy_level')}")
            print(f"  - Data provenance: {building.get('data_provenance', {}).get('data_source')}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
    
    # Test 3: Invalid polygon (too large)
    print("\n3. Testing polygon that's too large...")
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
    
    response = requests.post(
        f"{base_url}/polygon/analyze",
        json={
            "geometry": large_polygon,
            "min_confidence": 0.7,
            "include_buildings": False
        }
    )
    
    if response.status_code == 413:
        print(f"✓ Correctly rejected large polygon: {response.status_code}")
        print(f"✓ Error message: {response.json()['detail']}")
    else:
        print(f"✗ Expected 413, got: {response.status_code}")
    
    # Test 4: Invalid geometry type
    print("\n4. Testing invalid geometry type...")
    response = requests.post(
        f"{base_url}/polygon/analyze",
        json={
            "geometry": {"type": "Point", "coordinates": [100.5, 13.75]},
            "min_confidence": 0.7,
            "include_buildings": False
        }
    )
    
    if response.status_code == 422:
        print(f"✓ Correctly rejected invalid geometry: {response.status_code}")
        print(f"✓ Error message: {response.json()['detail']}")
    else:
        print(f"✗ Expected 422, got: {response.status_code}")
    
    print("\n✅ Endpoint tests completed!")

if __name__ == "__main__":
    # Run validation tests (no server needed)
    test_validation()
    
    # Uncomment to test endpoint (requires server running)
    # test_endpoint_local()
    
    print("\n" + "="*50)
    print("To test the endpoint, start the server and run:")
    print("  python test_polygon_endpoint.py")
    print("Then uncomment the test_endpoint_local() call")
    print("="*50)
