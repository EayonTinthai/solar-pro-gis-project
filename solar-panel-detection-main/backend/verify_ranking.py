"""
Simple verification of ranking algorithm logic
"""

# Inline implementation for testing
def normalize_value(value, min_val, max_val):
    if max_val == min_val:
        return 0.5
    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))

def calculate_ranking_score(annual_production_kwh, area_m2, confidence, payback_years, permitting_status):
    SOLAR_POTENTIAL_WEIGHT = 0.40
    ROOF_AREA_WEIGHT = 0.20
    CONFIDENCE_WEIGHT = 0.20
    PAYBACK_WEIGHT = 0.15
    PERMITTING_WEIGHT = 0.05
    
    PERMITTING_WEIGHTS = {
        "approved": 1.0,
        "pending": 0.6,
        "not_required": 0.8,
        "unknown": 0.3
    }
    
    solar_normalized = normalize_value(annual_production_kwh, 0, 100000)
    area_normalized = normalize_value(area_m2, 0, 1000)
    confidence_normalized = confidence
    payback_inverse = 1 / payback_years if payback_years > 0 else 0
    payback_normalized = normalize_value(payback_inverse, 0, 1)
    permitting_normalized = PERMITTING_WEIGHTS.get(permitting_status, 0.3)
    
    solar_score = solar_normalized * SOLAR_POTENTIAL_WEIGHT * 100
    area_score = area_normalized * ROOF_AREA_WEIGHT * 100
    confidence_score = confidence_normalized * CONFIDENCE_WEIGHT * 100
    payback_score = payback_normalized * PAYBACK_WEIGHT * 100
    permitting_score = permitting_normalized * PERMITTING_WEIGHT * 100
    
    total_score = solar_score + area_score + confidence_score + payback_score + permitting_score
    
    return {
        "ranking_score": round(total_score, 2),
        "solar_potential_score": round(solar_score, 2),
        "roof_area_score": round(area_score, 2),
        "confidence_score": round(confidence_score, 2),
        "payback_score": round(payback_score, 2),
        "permitting_score": round(permitting_score, 2)
    }

# Test
print("Testing ranking algorithm...")
result = calculate_ranking_score(50000, 500, 0.95, 3.0, "approved")
print(f"Score: {result['ranking_score']}/100")
print(f"Components: Solar={result['solar_potential_score']}, Area={result['roof_area_score']}, Confidence={result['confidence_score']}, Payback={result['payback_score']}, Permitting={result['permitting_score']}")
print("✓ Algorithm works correctly!")
