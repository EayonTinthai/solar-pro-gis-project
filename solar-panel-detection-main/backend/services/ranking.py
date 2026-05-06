"""
Ranking algorithm services for solar site prioritization

This module implements the ranking algorithm that scores buildings based on:
- Solar potential (40% weight)
- Roof area (20% weight)
- Confidence score (20% weight)
- Payback period (15% weight)
- Permitting status (5% weight)

Requirements: 7
"""

from typing import Dict, Any


# Ranking weights (Req 7)
SOLAR_POTENTIAL_WEIGHT = 0.40  # 40%
ROOF_AREA_WEIGHT = 0.20        # 20%
CONFIDENCE_WEIGHT = 0.20       # 20%
PAYBACK_WEIGHT = 0.15          # 15%
PERMITTING_WEIGHT = 0.05       # 5%

# Permitting status weights (Req 7)
PERMITTING_WEIGHTS = {
    "approved": 1.0,
    "pending": 0.6,
    "not_required": 0.8,
    "unknown": 0.3
}


def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """
    Normalize a value to 0-1 scale
    
    Args:
        value: Value to normalize
        min_val: Minimum value in range
        max_val: Maximum value in range
        
    Returns:
        Normalized value between 0 and 1
    """
    if max_val == min_val:
        return 0.5  # Default to middle if no range
    
    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))  # Clamp to [0, 1]


def calculate_ranking_score(
    annual_production_kwh: float,
    area_m2: float,
    confidence: float,
    payback_years: float,
    permitting_status: str,
    max_production: float = 100000,
    max_area: float = 1000
) -> Dict[str, float]:
    """
    Calculate ranking score based on multiple factors (Req 7)
    
    The ranking algorithm uses weighted scoring:
    - Solar potential (40%): Normalized annual production
    - Roof area (20%): Normalized building area
    - Confidence (20%): ML confidence score (already 0-1)
    - Payback period (15%): Inverse normalized (shorter is better)
    - Permitting status (5%): Categorical weight
    
    Args:
        annual_production_kwh: Annual solar production in kWh
        area_m2: Roof area in square meters
        confidence: ML confidence score (0-1)
        payback_years: Payback period in years
        permitting_status: Permitting status string
        max_production: Maximum production for normalization (default: 100000)
        max_area: Maximum area for normalization (default: 1000)
        
    Returns:
        Dict with overall score (0-100) and component scores
    """
    # Normalize solar potential (40% weight)
    solar_normalized = normalize_value(annual_production_kwh, 0, max_production)
    
    # Normalize roof area (20% weight)
    area_normalized = normalize_value(area_m2, 0, max_area)
    
    # Confidence is already normalized (20% weight)
    confidence_normalized = confidence  # Already 0-1
    
    # Payback: shorter is better, so use inverse (15% weight)
    # Typical range: 2-10 years, so 1/10 to 1/2 = 0.1 to 0.5
    payback_inverse = 1 / payback_years if payback_years > 0 else 0
    payback_normalized = normalize_value(payback_inverse, 0, 1)
    
    # Permitting weight (5% weight)
    permitting_normalized = PERMITTING_WEIGHTS.get(permitting_status, 0.3)
    
    # Calculate weighted scores (out of their respective weights * 100)
    solar_score = solar_normalized * SOLAR_POTENTIAL_WEIGHT * 100
    area_score = area_normalized * ROOF_AREA_WEIGHT * 100
    confidence_score = confidence_normalized * CONFIDENCE_WEIGHT * 100
    payback_score = payback_normalized * PAYBACK_WEIGHT * 100
    permitting_score = permitting_normalized * PERMITTING_WEIGHT * 100
    
    # Total score (0-100)
    total_score = solar_score + area_score + confidence_score + payback_score + permitting_score
    
    return {
        "ranking_score": round(total_score, 2),
        "solar_potential_score": round(solar_score, 2),
        "roof_area_score": round(area_score, 2),
        "confidence_score": round(confidence_score, 2),
        "payback_score": round(payback_score, 2),
        "permitting_score": round(permitting_score, 2)
    }
