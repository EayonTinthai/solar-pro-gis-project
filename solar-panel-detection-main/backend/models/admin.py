"""
Admin and data quality models
"""

from pydantic import BaseModel, Field
from typing import List


class QualityByRegion(BaseModel):
    """Data quality metrics by region"""
    region: str
    total: int
    avg_confidence: float
    quality_flag: str = Field(..., description="high, medium, or low")


class DataQualityResponse(BaseModel):
    """Response for data quality endpoint"""
    total_buildings: int
    low_confidence_count: int
    low_confidence_percentage: float
    data_freshness_days: int
    validation_status: str = Field(..., description="Overall data quality status")
    quality_by_region: List[QualityByRegion]
    generated_at: str = Field(..., description="ISO 8601 timestamp")
