"""
Polygon analysis models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from .building import BuildingResponse


class PolygonAnalysisRequest(BaseModel):
    """Request for polygon analysis"""
    geometry: Dict[str, Any] = Field(..., description="GeoJSON polygon or multipolygon")
    min_confidence: float = Field(default=0.7, ge=0.5, le=1.0)
    include_buildings: bool = Field(default=False, description="Include individual buildings in response")
    limit: int = Field(default=1000, ge=1, le=10000, description="Max buildings to return if include_buildings=true")


class AggregatedStats(BaseModel):
    """Aggregated statistics for polygon area"""
    total_buildings: int
    total_area_m2: float
    total_system_kwp: float
    total_annual_production_kwh: float
    total_installation_cost_thb: float
    avg_confidence: float
    avg_payback_years: Optional[float]


class PolygonAnalysisResponse(BaseModel):
    """Response for polygon analysis"""
    polygon_area_km2: float
    total_buildings: int
    aggregated_stats: AggregatedStats
    buildings: List[BuildingResponse] = Field(default_factory=list, description="Individual buildings if requested")
    processing_time_ms: float
