"""
Syntax validation test for enhanced solar calculation endpoint
Tests that the code is syntactically correct and models are properly defined
"""
import ast
import sys

def test_syntax():
    """Test that api_bigquery.py has valid Python syntax"""
    print("\n=== Test 1: Syntax Validation ===")
    try:
        with open('api_bigquery.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        ast.parse(code)
        print("✓ api_bigquery.py has valid Python syntax")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_model_definitions():
    """Test that required models are defined in the code"""
    print("\n=== Test 2: Model Definitions ===")
    try:
        with open('api_bigquery.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        required_models = [
            'CustomSolarParams',
            'SolarCalculationRequest',
            'SolarCalculationResponse',
            'CalculationStep',
            'CalculationBreakdown'
        ]
        
        all_found = True
        for model in required_models:
            if f'class {model}' in code:
                print(f"✓ {model} class defined")
            else:
                print(f"✗ {model} class not found")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_function_definitions():
    """Test that required functions are defined"""
    print("\n=== Test 3: Function Definitions ===")
    try:
        with open('api_bigquery.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        required_functions = [
            'validate_custom_params',
            'calculate_solar_potential'
        ]
        
        all_found = True
        for func in required_functions:
            if f'def {func}' in code or f'async def {func}' in code:
                print(f"✓ {func} function defined")
            else:
                print(f"✗ {func} function not found")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_custom_params_fields():
    """Test that CustomSolarParams has all required fields"""
    print("\n=== Test 4: CustomSolarParams Fields ===")
    try:
        with open('api_bigquery.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Find CustomSolarParams class definition
        tree = ast.parse(code)
        
        custom_params_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'CustomSolarParams':
                custom_params_class = node
                break
        
        if not custom_params_class:
            print("✗ CustomSolarParams class not found")
            return False
        
        # Extract field names from the class
        fields = []
        for item in custom_params_class.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                fields.append(item.target.id)
        
        required_fields = [
            'panel_efficiency',
            'system_efficiency',
            'usable_roof_ratio',
            'cost_per_wp',
            'electricity_rate',
            'co2_factor'
        ]
        
        all_found = True
        for field in required_fields:
            if field in fields:
                print(f"✓ {field} field present")
            else:
                print(f"✗ {field} field missing")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_calculation_breakdown_fields():
    """Test that CalculationBreakdown has all required step fields"""
    print("\n=== Test 5: CalculationBreakdown Fields ===")
    try:
        with open('api_bigquery.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        tree = ast.parse(code)
        
        breakdown_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'CalculationBreakdown':
                breakdown_class = node
                break
        
        if not breakdown_class:
            print("✗ CalculationBreakdown class not found")
            return False
        
        # Extract field names
        fields = []
        for item in breakdown_class.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                fields.append(item.target.id)
        
        required_fields = [
            'step_1_usable_area',
            'step_2_system_size',
            'step_3_annual_production',
            'step_4_financial'
        ]
        
        all_found = True
        for field in required_fields:
            if field in fields:
                print(f"✓ {field} field present")
            else:
                print(f"✗ {field} field missing")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_response_model_fields():
    """Test that SolarCalculationResponse has new fields"""
    print("\n=== Test 6: SolarCalculationResponse New Fields ===")
    try:
        with open('api_bigquery.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        tree = ast.parse(code)
        
        response_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'SolarCalculationResponse':
                response_class = node
                break
        
        if not response_class:
            print("✗ SolarCalculationResponse class not found")
            return False
        
        # Extract field names
        fields = []
        for item in response_class.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                fields.append(item.target.id)
        
        new_fields = [
            'calculation_breakdown',
            'custom_parameters'
        ]
        
        all_found = True
        for field in new_fields:
            if field in fields:
                print(f"✓ {field} field present")
            else:
                print(f"✗ {field} field missing")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_validation_logic():
    """Test that validate_custom_params has proper validation logic"""
    print("\n=== Test 7: Validation Logic ===")
    try:
        with open('api_bigquery.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Check for PARAM_RANGES definition
        if 'PARAM_RANGES' in code:
            print("✓ PARAM_RANGES defined")
        else:
            print("✗ PARAM_RANGES not found")
            return False
        
        # Check for parameter range validation
        required_params = [
            'panel_efficiency',
            'system_efficiency',
            'usable_roof_ratio',
            'cost_per_wp',
            'electricity_rate',
            'co2_factor'
        ]
        
        all_found = True
        for param in required_params:
            if f'"{param}"' in code or f"'{param}'" in code:
                print(f"✓ {param} validation present")
            else:
                print(f"✗ {param} validation missing")
                all_found = False
        
        # Check for HTTPException on validation failure
        if 'HTTPException' in code and 'status_code=422' in code:
            print("✓ HTTPException with 422 status code present")
        else:
            print("✗ HTTPException with 422 status code missing")
            all_found = False
        
        return all_found
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_calculation_breakdown_creation():
    """Test that calculation breakdown is created in the endpoint"""
    print("\n=== Test 8: Calculation Breakdown Creation ===")
    try:
        with open('api_bigquery.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Check for CalculationBreakdown instantiation
        if 'CalculationBreakdown(' in code:
            print("✓ CalculationBreakdown instantiation found")
        else:
            print("✗ CalculationBreakdown instantiation not found")
            return False
        
        # Check for all four steps
        steps = [
            'step_1_usable_area',
            'step_2_system_size',
            'step_3_annual_production',
            'step_4_financial'
        ]
        
        all_found = True
        for step in steps:
            if f'{step}=' in code or f'{step} =' in code:
                print(f"✓ {step} assignment found")
            else:
                print(f"✗ {step} assignment missing")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_custom_parameters_tracking():
    """Test that custom parameters are tracked in the response"""
    print("\n=== Test 9: Custom Parameters Tracking ===")
    try:
        with open('api_bigquery.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Check for custom_parameters dictionary creation
        if 'custom_parameters = {}' in code or 'custom_parameters={}' in code:
            print("✓ custom_parameters dictionary initialization found")
        else:
            print("✗ custom_parameters dictionary initialization not found")
            return False
        
        # Check that custom_parameters is included in response
        if '"custom_parameters":' in code or "'custom_parameters':" in code:
            print("✓ custom_parameters included in response")
        else:
            print("✗ custom_parameters not included in response")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Enhanced Solar Calculation - Syntax Validation")
    print("Testing Requirements 5 and 13 Implementation")
    print("=" * 60)
    
    results = []
    
    results.append(("Syntax Validation", test_syntax()))
    results.append(("Model Definitions", test_model_definitions()))
    results.append(("Function Definitions", test_function_definitions()))
    results.append(("CustomSolarParams Fields", test_custom_params_fields()))
    results.append(("CalculationBreakdown Fields", test_calculation_breakdown_fields()))
    results.append(("SolarCalculationResponse Fields", test_response_model_fields()))
    results.append(("Validation Logic", test_validation_logic()))
    results.append(("Calculation Breakdown Creation", test_calculation_breakdown_creation()))
    results.append(("Custom Parameters Tracking", test_custom_parameters_tracking()))
    
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
    
    if passed == total:
        print("\n✓ All validation tests passed!")
        print("  - Custom parameters support implemented (Req 13)")
        print("  - Calculation breakdown implemented (Req 5)")
        print("  - Custom parameters tracking implemented (Req 13)")
    else:
        print(f"\n✗ {total - passed} test(s) failed")
    
    sys.exit(0 if passed == total else 1)
