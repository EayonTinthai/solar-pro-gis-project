"""
Building data models
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class DataProvenance(BaseModel):
    """Data source and collection metadata"""
    data_source: str = Field(..., description="Data source name")
    collection_method: str = Field(..., description="How data was collected")
    last_updated: str = Field(..., description="ISO 8601 timestamp of last update")


class AccuracyFactors(BaseModel):
    """Factors contributing to accuracy level"""
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="ML confidence score")
    data_age_days: int = Field(..., ge=0, description="Days since data collection")
    validation_status: str = Field(..., description="Validation status: validated or unvalidated")


class BuildingResponse(BaseModel):
    """Enhanced building response with all new fields"""
    # Existing fields
    id: int
    open_buildings_id: str
    latitude: float
    longitude: float
    area_m2: float
    confidence: float
    geometry: Optional[Dict[str, Any]] = None
    
    # NEW: Data provenance (Req 1)
    data_provenance: DataProvenance
    confidence_warning: bool = Field(..., description="True if confidence < 0.7")
    
    # NEW: Accuracy level (Req 12)
    accuracy_level: str = Field(..., description="high, medium, or low")
    accuracy_factors: AccuracyFactors
    
    # NEW: Permitting status (Req 6)
    permitting_status: str = Field(
        default="unknown",
        description="approved, pending, not_required, or unknown"
    )
    
    # NEW: Data traceability (Req 15)
    data_source: str
    data_collection_date: str = Field(..., description="ISO 8601 timestamp")
    data_source_url: str
    
    # NEW: Data quality flag (Req 11)
    data_quality_flag: str = Field(..., description="high, medium, or low")


class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses"""
    total: int = Field(..., description="Total matching records")
    offset: int = Field(..., ge=0, description="Current offset")
    limit: int = Field(..., ge=1, description="Current limit")
    has_more: bool = Field(..., description="More results available")
    next_offset: Optional[int] = Field(None, description="Suggested offset for next page")
