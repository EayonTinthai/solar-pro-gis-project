"""
Pydantic models for API request/response schemas
"""

from .building import (
    BuildingResponse,
    DataProvenance,
    AccuracyFactors,
    PaginationMetadata
)
from .solar import (
    SolarCalculationRequest,
    SolarCalculationResponse,
    CalculationBreakdown,
    CalculationStep,
    CustomSolarParameters
)
from .ranking import (
    RankingResponse,
    RankingFactors,
    RankingScope
)
from .polygon import (
    PolygonAnalysisRequest,
    PolygonAnalysisResponse,
    AggregatedStats
)
from .admin import (
    DataQualityResponse,
    QualityByRegion
)
from .common import (
    ErrorResponse,
    HealthCheckResponse
)

__all__ = [
    # Building models
    "BuildingResponse",
    "DataProvenance",
    "AccuracyFactors",
    "PaginationMetadata",
    
    # Solar models
    "SolarCalculationRequest",
    "SolarCalculationResponse",
    "CalculationBreakdown",
    "CalculationStep",
    "CustomSolarParameters",
    
    # Ranking models
    "RankingResponse",
    "RankingFactors",
    "RankingScope",
    
    # Polygon models
    "PolygonAnalysisRequest",
    "PolygonAnalysisResponse",
    "AggregatedStats",
    
    # Admin models
    "DataQualityResponse",
    "QualityByRegion",
    
    # Common models
    "ErrorResponse",
    "HealthCheckResponse",
]
