"""
Manual test script for admin data quality endpoint
Run this to verify the implementation works correctly
"""

import os
import sys

# Test the authentication function
def test_verify_api_key():
    """Test API key verification"""
    from api_bigquery import verify_api_key
    
    # Set test API key
    os.environ['ADMIN_API_KEYS'] = 'test_key_1,test_key_2'
    
    print("Testing API key verification...")
    
    # Test valid key
    try:
        result = verify_api_key('test_key_1')
        print(f"✓ Valid key accepted: {result}")
    except Exception as e:
        print(f"✗ Valid key rejected: {e}")
        return False
    
    # Test invalid key
    try:
        result = verify_api_key('invalid_key')
        print(f"✗ Invalid key accepted (should have failed)")
        return False
    except Exception as e:
        print(f"✓ Invalid key rejected: {e}")
    
    # Test missing key
    try:
        result = verify_api_key(None)
        print(f"✗ Missing key accepted (should have failed)")
        return False
    except Exception as e:
        print(f"✓ Missing key rejected: {e}")
    
    return True


def test_data_quality_flag():
    """Test data quality flag calculation"""
    from services.enrichment import calculate_data_quality_flag
    
    print("\nTesting data quality flag calculation...")
    
    # Test high quality
    flag = calculate_data_quality_flag(0.85)
    assert flag == "high", f"Expected 'high', got '{flag}'"
    print(f"✓ High confidence (0.85) -> {flag}")
    
    # Test medium quality
    flag = calculate_data_quality_flag(0.75)
    assert flag == "medium", f"Expected 'medium', got '{flag}'"
    print(f"✓ Medium confidence (0.75) -> {flag}")
    
    # Test low quality
    flag = calculate_data_quality_flag(0.65)
    assert flag == "low", f"Expected 'low', got '{flag}'"
    print(f"✓ Low confidence (0.65) -> {flag}")
    
    # Test boundary cases
    flag = calculate_data_quality_flag(0.8)
    assert flag == "high", f"Expected 'high' for 0.8, got '{flag}'"
    print(f"✓ Boundary (0.8) -> {flag}")
    
    flag = calculate_data_quality_flag(0.7)
    assert flag == "medium", f"Expected 'medium' for 0.7, got '{flag}'"
    print(f"✓ Boundary (0.7) -> {flag}")
    
    return True


def test_enrichment_includes_quality_flag():
    """Test that enrichment includes data_quality_flag"""
    from services.enrichment import enrich_building_data
    
    print("\nTesting enrichment includes data_quality_flag...")
    
    # Test building data
    building = {
        "id": 1,
        "open_buildings_id": "TEST123",
        "latitude": 13.7563,
        "longitude": 100.5018,
        "area_m2": 250.0,
        "confidence": 0.85
    }
    
    enriched = enrich_building_data(building)
    
    # Check that data_quality_flag is present
    assert "data_quality_flag" in enriched, "data_quality_flag not in enriched data"
    print(f"✓ data_quality_flag present: {enriched['data_quality_flag']}")
    
    # Check that it's correct
    assert enriched['data_quality_flag'] == "high", f"Expected 'high', got '{enriched['data_quality_flag']}'"
    print(f"✓ data_quality_flag correct for confidence 0.85")
    
    # Test with low confidence
    building['confidence'] = 0.65
    enriched = enrich_building_data(building)
    assert enriched['data_quality_flag'] == "low", f"Expected 'low', got '{enriched['data_quality_flag']}'"
    print(f"✓ data_quality_flag correct for confidence 0.65")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Admin Data Quality Endpoint - Manual Tests")
    print("=" * 60)
    
    all_passed = True
    
    try:
        if not test_verify_api_key():
            all_passed = False
    except Exception as e:
        print(f"✗ API key verification test failed: {e}")
        all_passed = False
    
    try:
        if not test_data_quality_flag():
            all_passed = False
    except Exception as e:
        print(f"✗ Data quality flag test failed: {e}")
        all_passed = False
    
    try:
        if not test_enrichment_includes_quality_flag():
            all_passed = False
    except Exception as e:
        print(f"✗ Enrichment test failed: {e}")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
