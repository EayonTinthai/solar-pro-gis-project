"""
Test script for ranking algorithm

This script tests the ranking algorithm with sample data to verify it works correctly.
"""

from services.ranking import calculate_ranking_score


def test_ranking_algorithm():
    """Test the ranking algorithm with sample buildings"""
    
    print("=" * 60)
    print("Testing Ranking Algorithm")
    print("=" * 60)
    print()
    
    # Test case 1: High-quality building
    print("Test Case 1: High-quality building")
    print("-" * 40)
    result1 = calculate_ranking_score(
        annual_production_kwh=50000,  # Good production
        area_m2=500,  # Large roof
        confidence=0.95,  # High confidence
        payback_years=3.0,  # Short payback
        permitting_status="approved"  # Approved
    )
    print(f"Annual Production: 50,000 kWh")
    print(f"Area: 500 m²")
    print(f"Confidence: 0.95")
    print(f"Payback: 3.0 years")
    print(f"Permitting: approved")
    print()
    print(f"Results:")
    print(f"  Overall Score: {result1['ranking_score']}/100")
    print(f"  Solar Potential: {result1['solar_potential_score']}/40")
    print(f"  Roof Area: {result1['roof_area_score']}/20")
    print(f"  Confidence: {result1['confidence_score']}/20")
    print(f"  Payback: {result1['payback_score']}/15")
    print(f"  Permitting: {result1['permitting_score']}/5")
    print()
    
    # Test case 2: Medium-quality building
    print("Test Case 2: Medium-quality building")
    print("-" * 40)
    result2 = calculate_ranking_score(
        annual_production_kwh=25000,  # Medium production
        area_m2=250,  # Medium roof
        confidence=0.75,  # Medium confidence
        payback_years=5.0,  # Medium payback
        permitting_status="pending"  # Pending
    )
    print(f"Annual Production: 25,000 kWh")
    print(f"Area: 250 m²")
    print(f"Confidence: 0.75")
    print(f"Payback: 5.0 years")
    print(f"Permitting: pending")
    print()
    print(f"Results:")
    print(f"  Overall Score: {result2['ranking_score']}/100")
    print(f"  Solar Potential: {result2['solar_potential_score']}/40")
    print(f"  Roof Area: {result2['roof_area_score']}/20")
    print(f"  Confidence: {result2['confidence_score']}/20")
    print(f"  Payback: {result2['payback_score']}/15")
    print(f"  Permitting: {result2['permitting_score']}/5")
    print()
    
    # Test case 3: Low-quality building
    print("Test Case 3: Low-quality building")
    print("-" * 40)
    result3 = calculate_ranking_score(
        annual_production_kwh=10000,  # Low production
        area_m2=100,  # Small roof
        confidence=0.65,  # Low confidence
        payback_years=8.0,  # Long payback
        permitting_status="unknown"  # Unknown
    )
    print(f"Annual Production: 10,000 kWh")
    print(f"Area: 100 m²")
    print(f"Confidence: 0.65")
    print(f"Payback: 8.0 years")
    print(f"Permitting: unknown")
    print()
    print(f"Results:")
    print(f"  Overall Score: {result3['ranking_score']}/100")
    print(f"  Solar Potential: {result3['solar_potential_score']}/40")
    print(f"  Roof Area: {result3['roof_area_score']}/20")
    print(f"  Confidence: {result3['confidence_score']}/20")
    print(f"  Payback: {result3['payback_score']}/15")
    print(f"  Permitting: {result3['permitting_score']}/5")
    print()
    
    # Verify ranking order
    print("=" * 60)
    print("Verification: Ranking Order")
    print("=" * 60)
    scores = [
        ("High-quality", result1['ranking_score']),
        ("Medium-quality", result2['ranking_score']),
        ("Low-quality", result3['ranking_score'])
    ]
    scores.sort(key=lambda x: x[1], reverse=True)
    
    print("Expected order: High > Medium > Low")
    print(f"Actual order: {' > '.join([s[0] for s in scores])}")
    
    if scores[0][0] == "High-quality" and scores[1][0] == "Medium-quality" and scores[2][0] == "Low-quality":
        print("✓ Ranking order is correct!")
    else:
        print("✗ Ranking order is incorrect!")
    
    print()
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    test_ranking_algorithm()
