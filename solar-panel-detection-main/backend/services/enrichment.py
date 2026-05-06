"""
Data enrichment services for building data
"""

from datetime import datetime
from typing import Dict, Tuple, Any


# Constants
DATA_COLLECTION_DATE = datetime(2023, 6, 15)
DATA_SOURCE = "Google Open Buildings v3"
DATA_SOURCE_URL = "https://sites.research.google/open-buildings/"
COLLECTION_METHOD = "ML detection from satellite imagery"


def get_data_age_days() -> int:
    """Calculate days since data collection"""
    return (datetime.now() - DATA_COLLECTION_DATE).days


def build_data_provenance() -> Dict[str, str]:
    """Build data provenance object"""
    return {
        "data_source": DATA_SOURCE,
        "collection_method": COLLECTION_METHOD,
        "last_updated": DATA_COLLECTION_DATE.isoformat() + "Z"
    }


def calculate_accuracy_level(confidence: float, data_age_days: int) -> Tuple[str, Dict[str, Any]]:
    """
    Calculate accuracy level based on confidence and data age
    
    Args:
        confidence: ML confidence score (0-1)
        data_age_days: Days since data collection
        
    Returns:
        Tuple of (level, factors) where:
        - level: "high", "medium", or "low"
        - factors: Dict with confidence_score, data_age_days, validation_status
    """
    # Determine level
    if confidence >= 0.8 and data_age_days < 365:
        level = "high"
    elif confidence >= 0.7 or data_age_days < 730:
        level = "medium"
    else:
        level = "low"
    
    # Build factors object
    factors = {
        "confidence_score": confidence,
        "data_age_days": data_age_days,
        "validation_status": "unvalidated"  # Default, can be updated with field validation
    }
    
    return level, factors


def get_permitting_status(lat: float, lon: float) -> str:
    """
    Get permitting status for location
    
    This is a placeholder for future integration with permitting database.
    Currently returns "unknown" for all locations.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        Permitting status: "approved", "pending", "not_required", or "unknown"
    """
    # TODO: Integrate with permitting database
    return "unknown"


def calculate_data_quality_flag(confidence: float) -> str:
    """
    Calculate data quality flag based on confidence
    
    Args:
        confidence: ML confidence score (0-1)
        
    Returns:
        Quality flag: "high", "medium", or "low"
    """
    if confidence >= 0.8:
        return "high"
    elif confidence >= 0.7:
        return "medium"
    else:
        return "low"


def enrich_building_data(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add computed fields to building data
    
    Args:
        row: Raw building data from BigQuery
        
    Returns:
        Enriched building data with all new fields
    """
    data_age_days = get_data_age_days()
    
    # Calculate accuracy level (Req 12)
    accuracy_level, accuracy_factors = calculate_accuracy_level(
        confidence=row['confidence'],
        data_age_days=data_age_days
    )
    
    # Data provenance (Req 1)
    data_provenance = build_data_provenance()
    
    # Confidence warning (Req 1)
    confidence_warning = row['confidence'] < 0.7
    
    # Permitting status (Req 6)
    permitting_status = get_permitting_status(row['latitude'], row['longitude'])
    
    # Data quality flag (Req 11)
    data_quality_flag = calculate_data_quality_flag(row['confidence'])
    
    return {
        **row,  # Original fields
        "data_provenance": data_provenance,
        "confidence_warning": confidence_warning,
        "accuracy_level": accuracy_level,
        "accuracy_factors": accuracy_factors,
        "permitting_status": permitting_status,
        "data_source": DATA_SOURCE,
        "data_collection_date": DATA_COLLECTION_DATE.isoformat() + "Z",
        "data_source_url": DATA_SOURCE_URL,
        "data_quality_flag": data_quality_flag
    }
