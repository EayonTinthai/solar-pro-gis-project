"""
Test script for the /docs/methodology endpoint

This script verifies that the methodology endpoint returns the expected
structure and content as specified in Requirement 10.
"""

import json


def test_methodology_endpoint():
    """Test the methodology endpoint structure"""
    # Import the app
    from api_bigquery import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Make request to methodology endpoint
    response = client.get("/docs/methodology")
    
    # Check status code
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # Parse JSON response
    data = response.json()
    
    # Verify top-level structure
    assert "version" in data, "Missing 'version' field"
    assert "formulas" in data, "Missing 'formulas' field"
    assert "parameters" in data, "Missing 'parameters' field"
    assert "references" in data, "Missing 'references' field"
    
    # Verify version
    assert data["version"] == "2.2.0", f"Expected version 2.2.0, got {data['version']}"
    
    # Verify formulas section
    expected_formulas = [
        "usable_roof_area",
        "system_size_kwp",
        "annual_production_kwh",
        "installation_cost_thb",
        "annual_savings_thb",
        "payback_period_years",
        "co2_reduction_kg"
    ]
    
    for formula_name in expected_formulas:
        assert formula_name in data["formulas"], f"Missing formula: {formula_name}"
        formula = data["formulas"][formula_name]
        assert "formula" in formula, f"Missing 'formula' field in {formula_name}"
        assert "description" in formula, f"Missing 'description' field in {formula_name}"
        assert "parameters" in formula, f"Missing 'parameters' field in {formula_name}"
    
    # Verify parameters section
    expected_parameters = [
        "panel_efficiency",
        "system_efficiency",
        "usable_roof_ratio",
        "cost_per_wp",
        "electricity_rate",
        "co2_factor"
    ]
    
    for param_name in expected_parameters:
        assert param_name in data["parameters"], f"Missing parameter: {param_name}"
        param = data["parameters"][param_name]
        assert "default" in param, f"Missing 'default' field in {param_name}"
        assert "range" in param, f"Missing 'range' field in {param_name}"
        assert "unit" in param, f"Missing 'unit' field in {param_name}"
        assert "description" in param, f"Missing 'description' field in {param_name}"
    
    # Verify calculation methods
    assert "calculation_methods" in data, "Missing 'calculation_methods' field"
    assert "pvlib" in data["calculation_methods"], "Missing 'pvlib' calculation method"
    assert "simplified" in data["calculation_methods"], "Missing 'simplified' calculation method"
    
    # Verify data sources
    assert "data_sources" in data, "Missing 'data_sources' field"
    assert "building_footprints" in data["data_sources"], "Missing 'building_footprints' data source"
    assert "solar_irradiance" in data["data_sources"], "Missing 'solar_irradiance' data source"
    
    # Verify references is a list
    assert isinstance(data["references"], list), "References should be a list"
    assert len(data["references"]) > 0, "References list should not be empty"
    
    # Verify assumptions
    assert "assumptions" in data, "Missing 'assumptions' field"
    
    # Verify limitations
    assert "limitations" in data, "Missing 'limitations' field"
    
    # Verify validation
    assert "validation" in data, "Missing 'validation' field"
    
    print("✅ All tests passed!")
    print(f"\n📊 Methodology endpoint structure:")
    print(f"  - Version: {data['version']}")
    print(f"  - Formulas: {len(data['formulas'])} formulas documented")
    print(f"  - Parameters: {len(data['parameters'])} parameters documented")
    print(f"  - References: {len(data['references'])} academic references")
    print(f"  - Calculation methods: {len(data['calculation_methods'])} methods")
    print(f"  - Data sources: {len(data['data_sources'])} sources")
    
    # Print a sample formula for verification
    print(f"\n📝 Sample formula (usable_roof_area):")
    print(f"  Formula: {data['formulas']['usable_roof_area']['formula']}")
    print(f"  Description: {data['formulas']['usable_roof_area']['description']}")
    print(f"  Example: {data['formulas']['usable_roof_area']['example']}")
    
    return True


if __name__ == "__main__":
    try:
        test_methodology_endpoint()
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Error running test: {e}")
        exit(1)
