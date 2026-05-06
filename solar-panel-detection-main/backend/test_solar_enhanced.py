"""
Test script for enhanced solar calculation endpoint
Tests Requirements 5 and 13
"""
import requests
import json

BASE_URL = "http://localhost:8080"

def test_solar_calculate_basic():
    """Test basic solar calculation without custom params"""
    print("\n=== Test 1: Basic Solar Calculation ===")
    
    payload = {
        "latitude": 13.7563,
        "longitude": 100.5018,
        "area_m2": 250.0,
        "confidence": 0.95
    }
    
    response = requests.post(f"{BASE_URL}/solar/calculate", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Usable roof area: {data['usable_roof_area']} m²")
        print(f"✓ System size: {data['system_size_kwp']} kWp")
        print(f"✓ Annual production: {data['annual_production_kwh']} kWh")
        
        # Check for calculation breakdown (Req 5)
        if 'calculation_breakdown' in data:
            print("\n✓ Calculation breakdown present:")
            breakdown = data['calculation_breakdown']
            print(f"  - Step 1 (Usable Area): {breakdown['step_1_usable_area']['result']} {breakdown['step_1_usable_area']['unit']}")
            print(f"    Formula: {breakdown['step_1_usable_area']['formula']}")
            print(f"  - Step 2 (System Size): {breakdown['step_2_system_size']['result']} {breakdown['step_2_system_size']['unit']}")
            print(f"    Formula: {breakdown['step_2_system_size']['formula']}")
            print(f"  - Step 3 (Annual Production): {breakdown['step_3_annual_production']['result']} {breakdown['step_3_annual_production']['unit']}")
            print(f"    Formula: {breakdown['step_3_annual_production']['formula']}")
            print(f"  - Step 4 (Financial): {breakdown['step_4_financial']['result']} {breakdown['step_4_financial']['unit']}")
            print(f"    Formula: {breakdown['step_4_financial']['formula']}")
        else:
            print("✗ Calculation breakdown missing!")
        
        # Check custom_parameters is None for basic request
        if data.get('custom_parameters') is None:
            print("✓ custom_parameters is None (as expected for basic request)")
        else:
            print(f"✗ custom_parameters should be None but got: {data.get('custom_parameters')}")
    else:
        print(f"✗ Error: {response.text}")

def test_solar_calculate_with_custom_params():
    """Test solar calculation with custom parameters (Req 13)"""
    print("\n=== Test 2: Solar Calculation with Custom Parameters ===")
    
    payload = {
        "latitude": 13.7563,
        "longitude": 100.5018,
        "area_m2": 250.0,
        "confidence": 0.95,
        "custom_params": {
            "panel_efficiency": 0.22,
            "cost_per_wp": 23.0,
            "electricity_rate": 4.5
        }
    }
    
    response = requests.post(f"{BASE_URL}/solar/calculate", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Usable roof area: {data['usable_roof_area']} m²")
        print(f"✓ System size: {data['system_size_kwp']} kWp")
        print(f"✓ Annual production: {data['annual_production_kwh']} kWh")
        
        # Check custom_parameters tracking (Req 13)
        if 'custom_parameters' in data and data['custom_parameters']:
            print("\n✓ Custom parameters tracked:")
            for key, value in data['custom_parameters'].items():
                print(f"  - {key}: {value}")
            
            # Verify only customized params are included
            expected_params = {"panel_efficiency", "cost_per_wp", "electricity_rate"}
            actual_params = set(data['custom_parameters'].keys())
            if actual_params == expected_params:
                print("✓ Only customized parameters included")
            else:
                print(f"✗ Expected {expected_params}, got {actual_params}")
        else:
            print("✗ Custom parameters not tracked!")
        
        # Verify assumptions reflect custom values
        assumptions = data['assumptions']
        if assumptions['panel_efficiency'] == 0.22:
            print("✓ Custom panel_efficiency used in calculation")
        else:
            print(f"✗ Expected panel_efficiency 0.22, got {assumptions['panel_efficiency']}")
    else:
        print(f"✗ Error: {response.text}")

def test_solar_calculate_invalid_params():
    """Test validation of out-of-range parameters (Req 13)"""
    print("\n=== Test 3: Invalid Parameter Validation ===")
    
    # Test panel_efficiency out of range
    payload = {
        "latitude": 13.7563,
        "longitude": 100.5018,
        "area_m2": 250.0,
        "confidence": 0.95,
        "custom_params": {
            "panel_efficiency": 0.30  # Out of range (max 0.25)
        }
    }
    
    response = requests.post(f"{BASE_URL}/solar/calculate", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 422:
        print("✓ Correctly rejected out-of-range panel_efficiency")
        print(f"  Error: {response.json()['detail']}")
    else:
        print(f"✗ Should have returned 422, got {response.status_code}")
    
    # Test cost_per_wp out of range
    payload['custom_params'] = {"cost_per_wp": 60}  # Out of range (max 50)
    response = requests.post(f"{BASE_URL}/solar/calculate", json=payload)
    
    if response.status_code == 422:
        print("✓ Correctly rejected out-of-range cost_per_wp")
        print(f"  Error: {response.json()['detail']}")
    else:
        print(f"✗ Should have returned 422, got {response.status_code}")

def test_calculation_breakdown_structure():
    """Test calculation breakdown structure (Req 5)"""
    print("\n=== Test 4: Calculation Breakdown Structure ===")
    
    payload = {
        "latitude": 13.7563,
        "longitude": 100.5018,
        "area_m2": 250.0,
        "confidence": 0.95
    }
    
    response = requests.post(f"{BASE_URL}/solar/calculate", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        breakdown = data.get('calculation_breakdown')
        
        if breakdown:
            required_steps = ['step_1_usable_area', 'step_2_system_size', 
                            'step_3_annual_production', 'step_4_financial']
            
            all_present = all(step in breakdown for step in required_steps)
            if all_present:
                print("✓ All required calculation steps present")
            else:
                print(f"✗ Missing steps: {[s for s in required_steps if s not in breakdown]}")
            
            # Check structure of each step
            for step_name in required_steps:
                step = breakdown[step_name]
                required_fields = ['formula', 'inputs', 'result', 'unit']
                has_all_fields = all(field in step for field in required_fields)
                
                if has_all_fields:
                    print(f"✓ {step_name} has all required fields")
                else:
                    missing = [f for f in required_fields if f not in step]
                    print(f"✗ {step_name} missing fields: {missing}")
        else:
            print("✗ calculation_breakdown not present in response")
    else:
        print(f"✗ Request failed: {response.status_code}")

if __name__ == "__main__":
    print("=" * 60)
    print("Enhanced Solar Calculation Endpoint Tests")
    print("Testing Requirements 5 and 13")
    print("=" * 60)
    
    try:
        test_solar_calculate_basic()
        test_solar_calculate_with_custom_params()
        test_solar_calculate_invalid_params()
        test_calculation_breakdown_structure()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API server")
        print("  Make sure the API is running on http://localhost:8080")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
