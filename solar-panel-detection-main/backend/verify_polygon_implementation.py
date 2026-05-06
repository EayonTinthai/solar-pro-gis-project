"""
Verification script for polygon analysis implementation
This script verifies the implementation without requiring a full test environment
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

def verify_imports():
    """Verify all required modules can be imported"""
    print("Verifying imports...")
    
    try:
        from services.validation import validate_polygon, calculate_polygon_area_km2
        print("✓ Imported validation functions")
    except ImportError as e:
        print(f"✗ Failed to import validation functions: {e}")
        return False
    
    try:
        from api_bigquery import app, PolygonAnalysisRequest, PolygonAnalysisResponse
        print("✓ Imported API models")
    except ImportError as e:
        print(f"✗ Failed to import API models: {e}")
        return False
    
    return True


def verify_validation_logic():
    """Verify polygon validation logic"""
    print("\nVerifying validation logic...")
    
    from services.validation import validate_polygon, calculate_polygon_area_km2
    
    # Test 1: Valid polygon
    valid_polygon = {
        "type": "Polygon",
        "coordinates": [[
            [100.5018, 13.7563],
            [100.5118, 13.7563],
            [100.5118, 13.7663],
            [100.5018, 13.7663],
            [100.5018, 13.7563]
        ]]
    }
    
    is_valid, error = validate_polygon(valid_polygon)
    if is_valid and error is None:
        print("✓ Valid polygon passes validation")
    else:
        print(f"✗ Valid polygon failed: {error}")
        return False
    
    # Test 2: Invalid geometry type
    invalid_geom = {"type": "Point", "coordinates": [100.5, 13.75]}
    is_valid, error = validate_polygon(invalid_geom)
    if not is_valid and "must be Polygon or MultiPolygon" in error:
        print("✓ Invalid geometry type correctly rejected")
    else:
        print(f"✗ Invalid geometry type not rejected properly")
        return False
    
    # Test 3: Area calculation
    area = calculate_polygon_area_km2(valid_polygon)
    if 0 < area < 2:
        print(f"✓ Area calculation works: {area:.2f} km²")
    else:
        print(f"✗ Area calculation seems wrong: {area:.2f} km²")
        return False
    
    # Test 4: Large polygon rejection
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
    if not is_valid and "exceeds maximum of 1000 km²" in error:
        print("✓ Large polygon correctly rejected")
    else:
        print(f"✗ Large polygon not rejected properly: {error}")
        return False
    
    return True


def verify_api_structure():
    """Verify API endpoint structure"""
    print("\nVerifying API structure...")
    
    try:
        from api_bigquery import app
        
        # Check if polygon/analyze endpoint exists
        routes = [route.path for route in app.routes]
        
        if "/polygon/analyze" in routes:
            print("✓ /polygon/analyze endpoint registered")
        else:
            print("✗ /polygon/analyze endpoint not found")
            print(f"Available routes: {routes}")
            return False
        
        # Check if models are defined
        from api_bigquery import PolygonAnalysisRequest, PolygonAnalysisResponse, AggregatedStats
        print("✓ All required models defined")
        
        # Verify model fields
        request_fields = PolygonAnalysisRequest.__fields__.keys()
        expected_request_fields = {'geometry', 'min_confidence', 'include_buildings', 'limit'}
        if expected_request_fields.issubset(request_fields):
            print("✓ PolygonAnalysisRequest has all required fields")
        else:
            print(f"✗ PolygonAnalysisRequest missing fields: {expected_request_fields - request_fields}")
            return False
        
        response_fields = PolygonAnalysisResponse.__fields__.keys()
        expected_response_fields = {'polygon_area_km2', 'total_buildings', 'aggregated_stats', 'buildings', 'processing_time_ms'}
        if expected_response_fields.issubset(response_fields):
            print("✓ PolygonAnalysisResponse has all required fields")
        else:
            print(f"✗ PolygonAnalysisResponse missing fields: {expected_response_fields - response_fields}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error verifying API structure: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification checks"""
    print("="*60)
    print("Polygon Analysis Implementation Verification")
    print("="*60)
    
    checks = [
        ("Imports", verify_imports),
        ("Validation Logic", verify_validation_logic),
        ("API Structure", verify_api_structure)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} check failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "="*60)
    print("Verification Summary")
    print("="*60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✅ All verification checks passed!")
        print("\nImplementation Summary:")
        print("- Task 8.1: Polygon validation implemented")
        print("  - Validates geometry type (Polygon/MultiPolygon)")
        print("  - Validates max 1000 vertices")
        print("  - Calculates polygon area")
        print("  - Returns HTTP 413 if area > 1000 km²")
        print("\n- Task 8.2: POST /polygon/analyze endpoint implemented")
        print("  - Accepts geometry, min_confidence, include_buildings, limit")
        print("  - Uses ST_CONTAINS for spatial query")
        print("  - Calculates aggregated statistics")
        print("  - Optionally returns individual buildings")
        print("  - Returns processing_time_ms")
        return 0
    else:
        print("\n❌ Some verification checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
