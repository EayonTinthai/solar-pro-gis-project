"""
Unit tests for enhanced solar calculation models
Tests Requirements 5 and 13 - model structure and validation
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all required models can be imported"""
    print("\n=== Test 1: Import Models ===")
    try:
        from api_bigquery import (
            CustomSolarParams,
            SolarCalculationRequest,
            SolarCalculationResponse,
            CalculationStep,
            CalculationBreakdown,
            validate_custom_params
        )
        print("✓ All models imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_custom_params_model():
    """Test CustomSolarParams model structure (Req 13)"""
    print("\n=== Test 2: CustomSolarParams Model ===")
    try:
        from api_bigquery import CustomSolarParams
        
        # Test with valid parameters
        params = CustomSolarParams(
            panel_efficiency=0.22,
            system_efficiency=0.85,
            usable_roof_ratio=0.60,
            cost_per_wp=23.0,
            electricity_rate=4.5,
            co2_factor=0.35
        )
        
        print(f"✓ Created CustomSolarParams with all fields")
        print(f"  - panel_efficiency: {params.panel_efficiency}")
        print(f"  - system_efficiency: {params.system_efficiency}")
        print(f"  - usable_roof_ratio: {params.usable_roof_ratio}")
        print(f"  - cost_per_wp: {params.cost_per_wp}")
        print(f"  - electricity_rate: {params.electricity_rate}")
        print(f"  - co2_factor: {params.co2_factor}")
        
        # Test with partial parameters (all should be optional)
        partial_params = CustomSolarParams(panel_efficiency=0.22)
        print(f"✓ Created CustomSolarParams with partial fields")
        print(f"  - panel_efficiency: {partial_params.panel_efficiency}")
        print(f"  - system_efficiency: {partial_params.system_efficiency} (None)")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_calculation_step_model():
    """Test CalculationStep model structure (Req 5)"""
    print("\n=== Test 3: CalculationStep Model ===")
    try:
        from api_bigquery import CalculationStep
        
        step = CalculationStep(
            formula="area_m2 × usable_roof_ratio × confidence_adjustment",
            inputs={
                "area_m2": 250.0,
                "usable_roof_ratio": 0.50,
                "confidence_adjustment": 0.95
            },
            result=118.75,
            unit="m²"
        )
        
        print(f"✓ Created CalculationStep")
        print(f"  - formula: {step.formula}")
        print(f"  - inputs: {step.inputs}")
        print(f"  - result: {step.result}")
        print(f"  - unit: {step.unit}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_calculation_breakdown_model():
    """Test CalculationBreakdown model structure (Req 5)"""
    print("\n=== Test 4: CalculationBreakdown Model ===")
    try:
        from api_bigquery import CalculationStep, CalculationBreakdown
        
        breakdown = CalculationBreakdown(
            step_1_usable_area=CalculationStep(
                formula="area_m2 × usable_roof_ratio × confidence_adjustment",
                inputs={"area_m2": 250.0, "usable_roof_ratio": 0.50, "confidence_adjustment": 0.95},
                result=118.75,
                unit="m²"
            ),
            step_2_system_size=CalculationStep(
                formula="usable_roof_area × panel_efficiency",
                inputs={"usable_roof_area": 118.75, "panel_efficiency": 0.20},
                result=23.75,
                unit="kWp"
            ),
            step_3_annual_production=CalculationStep(
                formula="system_size_kwp × avg_irradiance × 365 × system_efficiency",
                inputs={"system_size_kwp": 23.75, "avg_irradiance": 5.06, "days_per_year": 365, "system_efficiency": 0.80},
                result=35000.0,
                unit="kWh/year"
            ),
            step_4_financial=CalculationStep(
                formula="installation_cost / annual_savings",
                inputs={"installation_cost_thb": 593750.0, "annual_savings_thb": 146300.0},
                result=4.06,
                unit="years"
            )
        )
        
        print(f"✓ Created CalculationBreakdown with all 4 steps")
        print(f"  - step_1_usable_area: {breakdown.step_1_usable_area.result} {breakdown.step_1_usable_area.unit}")
        print(f"  - step_2_system_size: {breakdown.step_2_system_size.result} {breakdown.step_2_system_size.unit}")
        print(f"  - step_3_annual_production: {breakdown.step_3_annual_production.result} {breakdown.step_3_annual_production.unit}")
        print(f"  - step_4_financial: {breakdown.step_4_financial.result} {breakdown.step_4_financial.unit}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_solar_request_model():
    """Test SolarCalculationRequest with custom_params (Req 13)"""
    print("\n=== Test 5: SolarCalculationRequest Model ===")
    try:
        from api_bigquery import SolarCalculationRequest, CustomSolarParams
        
        # Test without custom params
        request1 = SolarCalculationRequest(
            latitude=13.7563,
            longitude=100.5018,
            area_m2=250.0,
            confidence=0.95
        )
        print(f"✓ Created request without custom_params")
        print(f"  - custom_params: {request1.custom_params}")
        
        # Test with custom params
        request2 = SolarCalculationRequest(
            latitude=13.7563,
            longitude=100.5018,
            area_m2=250.0,
            confidence=0.95,
            custom_params=CustomSolarParams(
                panel_efficiency=0.22,
                cost_per_wp=23.0
            )
        )
        print(f"✓ Created request with custom_params")
        print(f"  - panel_efficiency: {request2.custom_params.panel_efficiency}")
        print(f"  - cost_per_wp: {request2.custom_params.cost_per_wp}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_solar_response_model():
    """Test SolarCalculationResponse with new fields (Req 5, 13)"""
    print("\n=== Test 6: SolarCalculationResponse Model ===")
    try:
        from api_bigquery import (
            SolarCalculationResponse,
            CalculationBreakdown,
            CalculationStep
        )
        
        breakdown = CalculationBreakdown(
            step_1_usable_area=CalculationStep(
                formula="test", inputs={}, result=100.0, unit="m²"
            ),
            step_2_system_size=CalculationStep(
                formula="test", inputs={}, result=20.0, unit="kWp"
            ),
            step_3_annual_production=CalculationStep(
                formula="test", inputs={}, result=30000.0, unit="kWh/year"
            ),
            step_4_financial=CalculationStep(
                formula="test", inputs={}, result=4.0, unit="years"
            )
        )
        
        response = SolarCalculationResponse(
            usable_roof_area=118.75,
            system_size_kwp=23.75,
            annual_production_kwh=35000.0,
            installation_cost_thb=593750.0,
            annual_savings_thb=146300.0,
            payback_period_years=4.06,
            co2_reduction_kg=14000.0,
            co2_reduction_ton=14.0,
            irradiance_source="NASA POWER",
            irradiance_kwh_m2_day=5.06,
            assumptions={
                "panel_efficiency": 0.20,
                "usable_roof_ratio": 0.50,
                "cost_per_wp": 25,
                "electricity_rate": 4.18,
                "co2_factor": 0.40,
                "system_efficiency": 0.80
            },
            calculation_breakdown=breakdown,
            custom_parameters={"panel_efficiency": 0.22}
        )
        
        print(f"✓ Created SolarCalculationResponse with new fields")
        print(f"  - calculation_breakdown: Present")
        print(f"  - custom_parameters: {response.custom_parameters}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_validate_custom_params():
    """Test validate_custom_params function (Req 13)"""
    print("\n=== Test 7: validate_custom_params Function ===")
    try:
        from api_bigquery import validate_custom_params, CustomSolarParams
        from fastapi import HTTPException
        
        # Test valid parameters
        valid_params = CustomSolarParams(
            panel_efficiency=0.22,
            system_efficiency=0.85,
            usable_roof_ratio=0.60,
            cost_per_wp=23.0,
            electricity_rate=4.5,
            co2_factor=0.35
        )
        
        try:
            validate_custom_params(valid_params)
            print("✓ Valid parameters passed validation")
        except HTTPException:
            print("✗ Valid parameters failed validation")
            return False
        
        # Test None (should pass)
        try:
            validate_custom_params(None)
            print("✓ None passed validation")
        except HTTPException:
            print("✗ None failed validation")
            return False
        
        # Test invalid panel_efficiency (too high)
        invalid_params = CustomSolarParams(panel_efficiency=0.30)
        try:
            validate_custom_params(invalid_params)
            print("✗ Invalid panel_efficiency should have failed")
            return False
        except HTTPException as e:
            print(f"✓ Invalid panel_efficiency correctly rejected: {e.detail}")
        
        # Test invalid cost_per_wp (too low)
        invalid_params = CustomSolarParams(cost_per_wp=15.0)
        try:
            validate_custom_params(invalid_params)
            print("✗ Invalid cost_per_wp should have failed")
            return False
        except HTTPException as e:
            print(f"✓ Invalid cost_per_wp correctly rejected: {e.detail}")
        
        # Test invalid electricity_rate (too high)
        invalid_params = CustomSolarParams(electricity_rate=7.0)
        try:
            validate_custom_params(invalid_params)
            print("✗ Invalid electricity_rate should have failed")
            return False
        except HTTPException as e:
            print(f"✓ Invalid electricity_rate correctly rejected: {e.detail}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Enhanced Solar Calculation Models - Unit Tests")
    print("Testing Requirements 5 and 13")
    print("=" * 60)
    
    results = []
    
    results.append(("Import Models", test_imports()))
    results.append(("CustomSolarParams Model", test_custom_params_model()))
    results.append(("CalculationStep Model", test_calculation_step_model()))
    results.append(("CalculationBreakdown Model", test_calculation_breakdown_model()))
    results.append(("SolarCalculationRequest Model", test_solar_request_model()))
    results.append(("SolarCalculationResponse Model", test_solar_response_model()))
    results.append(("validate_custom_params Function", test_validate_custom_params()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    sys.exit(0 if passed == total else 1)
