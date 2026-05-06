"""
Input validation services
"""

from typing import Dict, Any, Optional, Tuple
from fastapi import HTTPException


# Parameter ranges for custom solar calculations
PARAM_RANGES = {
    "panel_efficiency": (0.15, 0.25),
    "system_efficiency": (0.70, 0.90),
    "usable_roof_ratio": (0.30, 0.70),
    "cost_per_wp": (20, 50),
    "electricity_rate": (3.0, 6.0),
    "co2_factor": (0.30, 0.50)
}


def validate_filter_params(
    min_confidence: Optional[float] = None,
    min_area_m2: Optional[float] = None,
    max_area_m2: Optional[float] = None,
    min_system_kwp: Optional[float] = None,
    max_system_kwp: Optional[float] = None,
    max_payback_years: Optional[float] = None
) -> None:
    """
    Validate filter parameters
    
    Args:
        min_confidence: Minimum confidence threshold
        min_area_m2: Minimum area filter
        max_area_m2: Maximum area filter
        min_system_kwp: Minimum system size filter
        max_system_kwp: Maximum system size filter
        max_payback_years: Maximum payback period filter
        
    Raises:
        HTTPException: If validation fails
    """
    # Validate confidence range
    if min_confidence is not None:
        if not (0.5 <= min_confidence <= 1.0):
            raise HTTPException(
                status_code=422,
                detail=f"min_confidence must be between 0.5 and 1.0, got {min_confidence}"
            )
    
    # Validate area filters
    if min_area_m2 is not None and min_area_m2 <= 0:
        raise HTTPException(
            status_code=422,
            detail=f"min_area_m2 must be positive, got {min_area_m2}"
        )
    
    if max_area_m2 is not None and max_area_m2 <= 0:
        raise HTTPException(
            status_code=422,
            detail=f"max_area_m2 must be positive, got {max_area_m2}"
        )
    
    if min_area_m2 is not None and max_area_m2 is not None:
        if min_area_m2 > max_area_m2:
            raise HTTPException(
                status_code=422,
                detail=f"min_area_m2 ({min_area_m2}) must be <= max_area_m2 ({max_area_m2})"
            )
    
    # Validate system size filters
    if min_system_kwp is not None and min_system_kwp <= 0:
        raise HTTPException(
            status_code=422,
            detail=f"min_system_kwp must be positive, got {min_system_kwp}"
        )
    
    if max_system_kwp is not None and max_system_kwp <= 0:
        raise HTTPException(
            status_code=422,
            detail=f"max_system_kwp must be positive, got {max_system_kwp}"
        )
    
    if min_system_kwp is not None and max_system_kwp is not None:
        if min_system_kwp > max_system_kwp:
            raise HTTPException(
                status_code=422,
                detail=f"min_system_kwp ({min_system_kwp}) must be <= max_system_kwp ({max_system_kwp})"
            )
    
    # Validate payback filter
    if max_payback_years is not None and max_payback_years <= 0:
        raise HTTPException(
            status_code=422,
            detail=f"max_payback_years must be positive, got {max_payback_years}"
        )


def validate_custom_solar_params(params: Dict[str, float]) -> None:
    """
    Validate custom solar calculation parameters
    
    Args:
        params: Dictionary of custom parameters
        
    Raises:
        HTTPException: If validation fails
    """
    for key, value in params.items():
        if key not in PARAM_RANGES:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown parameter: {key}"
            )
        
        min_val, max_val = PARAM_RANGES[key]
        if not (min_val <= value <= max_val):
            raise HTTPException(
                status_code=422,
                detail=f"{key} must be between {min_val} and {max_val}, got {value}"
            )


def calculate_polygon_area_km2(geometry: Dict[str, Any]) -> float:
    """
    Calculate polygon area in square kilometers using spherical geometry
    
    Args:
        geometry: GeoJSON geometry object (Polygon or MultiPolygon)
        
    Returns:
        Area in square kilometers
    """
    from math import radians, sin, cos, sqrt, atan2
    
    def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth radius in meters
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    def polygon_area(coordinates: list) -> float:
        """Calculate area of a single polygon ring using shoelace formula (approximate)"""
        if len(coordinates) < 3:
            return 0.0
        
        # Use shoelace formula with approximate conversion to meters
        area = 0.0
        n = len(coordinates)
        
        for i in range(n):
            j = (i + 1) % n
            lon1, lat1 = coordinates[i][0], coordinates[i][1]
            lon2, lat2 = coordinates[j][0], coordinates[j][1]
            
            # Convert to approximate meters (at the average latitude)
            avg_lat = (lat1 + lat2) / 2
            x1 = lon1 * 111320 * cos(radians(avg_lat))
            y1 = lat1 * 110540
            x2 = lon2 * 111320 * cos(radians(avg_lat))
            y2 = lat2 * 110540
            
            area += x1 * y2 - x2 * y1
        
        return abs(area) / 2.0  # Return in square meters
    
    geom_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    
    total_area_m2 = 0.0
    
    if geom_type == "Polygon":
        # First ring is exterior, rest are holes
        if coordinates:
            total_area_m2 = polygon_area(coordinates[0])
            # Subtract holes
            for hole in coordinates[1:]:
                total_area_m2 -= polygon_area(hole)
    
    elif geom_type == "MultiPolygon":
        for polygon in coordinates:
            if polygon:
                total_area_m2 += polygon_area(polygon[0])
                # Subtract holes
                for hole in polygon[1:]:
                    total_area_m2 -= polygon_area(hole)
    
    # Convert to km²
    return total_area_m2 / 1_000_000


def validate_polygon(geometry: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate polygon geometry
    
    Args:
        geometry: GeoJSON geometry object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check geometry type
    geom_type = geometry.get("type")
    if geom_type not in ["Polygon", "MultiPolygon"]:
        return False, f"Geometry type must be Polygon or MultiPolygon, got {geom_type}"
    
    # Check coordinates exist
    if "coordinates" not in geometry:
        return False, "Geometry must have coordinates"
    
    coordinates = geometry["coordinates"]
    
    # Count vertices
    vertex_count = 0
    if geom_type == "Polygon":
        for ring in coordinates:
            vertex_count += len(ring)
    else:  # MultiPolygon
        for polygon in coordinates:
            for ring in polygon:
                vertex_count += len(ring)
    
    # Validate vertex count
    if vertex_count > 1000:
        return False, f"Polygon has too many vertices ({vertex_count}), maximum is 1000"
    
    # Calculate and validate area
    try:
        area_km2 = calculate_polygon_area_km2(geometry)
        if area_km2 > 1000:
            return False, f"Polygon area ({area_km2:.2f} km²) exceeds maximum of 1000 km²"
    except Exception as e:
        return False, f"Error calculating polygon area: {str(e)}"
    
    return True, None
