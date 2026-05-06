"""
Verification script for enhanced buildings endpoints
Tests the new filters, pagination, and enrichment features
"""

import sys
import json


def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from services.validation import validate_filter_params
        print("✓ validation service imported")
    except ImportError as e:
        print(f"✗ Failed to import validation service: {e}")
        return False
    
    try:
        from services.enrichment import enrich_building_data
        print("✓ enrichment service imported")
    except ImportError as e:
        print(f"✗ Failed to import enrichment service: {e}")
        return False
    
    return True


def test_validation():
    """Test filter validation logic"""
    print("\nTesting filter validation...")
    
    from services.validation import validate_filter_params
    from fastapi import HTTPException
    
    # Test valid parameters
    try:
        validate_filter_params(
            min_confidence=0.7,
            min_area_m2=50.0,
            max_area_m2=500.0,
            min_system_kwp=5.0,
            max_system_kwp=50.0,
            max_payback_years=10.0
        )
        print("✓ Valid parameters accepted")
    except HTTPException as e:
        print(f"✗ Valid parameters rejected: {e.detail}")
        return False
    
    # Test invalid confidence
    try:
        validate_filter_params(min_confidence=1.5)
        print("✗ Invalid confidence not rejected")
        return False
    except HTTPException:
        print("✓ Invalid confidence rejected")
    
    # Test invalid area range
    try:
        validate_filter_params(min_area_m2=500.0, max_area_m2=50.0)
        print("✗ Invalid area range not rejected")
        return False
    except HTTPException:
        print("✓ Invalid area range rejected")
    
    # Test negative values
    try:
        validate_filter_params(min_area_m2=-10.0)
        print("✗ Negative area not rejected")
        return False
    except HTTPException:
        print("✓ Negative area rejected")
    
    return True


def test_enrichment():
    """Test building data enrichment"""
    print("\nTesting data enrichment...")
    
    from services.enrichment import enrich_building_data
    
    # Test building data
    test_building = {
        "id": 123456,
        "open_buildings_id": "TEST123",
        "latitude": 13.7563,
        "longitude": 100.5018,
        "area_m2": 250.0,
        "confidence": 0.85,
        "geometry": None
    }
    
    try:
        enriched = enrich_building_data(test_building)
        
        # Check all required fields are present
        required_fields = [
            "data_provenance",
            "confidence_warning",
            "accuracy_level",
            "accuracy_factors",
            "permitting_status",
            "data_source",
            "data_collection_date",
            "data_source_url",
            "data_quality_flag"
        ]
        
        missing_fields = [f for f in required_fields if f not in enriched]
        if missing_fields:
            print(f"✗ Missing fields: {missing_fields}")
            return False
        
        print("✓ All enrichment fields present")
        
        # Verify data provenance structure
        if not isinstance(enriched['data_provenance'], dict):
            print("✗ data_provenance is not a dict")
            return False
        
        if 'data_source' not in enriched['data_provenance']:
            print("✗ data_provenance missing data_source")
            return False
        
        print("✓ Data provenance structure correct")
        
        # Verify accuracy level
        if enriched['accuracy_level'] not in ['high', 'medium', 'low']:
            print(f"✗ Invalid accuracy level: {enriched['accuracy_level']}")
            return False
        
        print(f"✓ Accuracy level: {enriched['accuracy_level']}")
        
        # Verify confidence warning
        if enriched['confidence'] < 0.7 and not enriched['confidence_warning']:
            print("✗ Confidence warning not set for low confidence")
            return False
        
        if enriched['confidence'] >= 0.7 and enriched['confidence_warning']:
            print("✗ Confidence warning set for high confidence")
            return False
        
        print("✓ Confidence warning logic correct")
        
        # Print sample enriched data
        print("\nSample enriched building:")
        print(json.dumps(enriched, indent=2, default=str))
        
        return True
        
    except Exception as e:
        print(f"✗ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_structure():
    """Test that API endpoints are properly defined"""
    print("\nTesting API structure...")
    
    try:
        from api_bigquery import app
        
        # Get all routes
        routes = [route.path for route in app.routes]
        
        # Check required endpoints exist
        required_endpoints = [
            "/buildings/bbox",
            "/buildings/nearby"
        ]
        
        for endpoint in required_endpoints:
            if endpoint in routes:
                print(f"✓ Endpoint {endpoint} exists")
            else:
                print(f"✗ Endpoint {endpoint} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ API structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("Enhanced Buildings Endpoints Verification")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Validation", test_validation),
        ("Enrichment", test_enrichment),
        ("API Structure", test_api_structure)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

