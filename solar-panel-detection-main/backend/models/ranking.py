"""
Ranking system models
"""

from pydantic import BaseModel, Field
from typing import List
from .building import BuildingResponse


class RankingScope(BaseModel):
    """Geographic scope for rankings"""
    type: str = Field(..., description="global, country, region, or province")
    value: str = Field(..., description="Scope identifier (e.g., TH, Bangkok)")


class RankingFactors(BaseModel):
    """Breakdown of ranking score components"""
    solar_potential_score: float = Field(..., description="Score from solar potential (out of 40)")
    roof_area_score: float = Field(..., description="Score from roof area (out of 20)")
    confidence_score: float = Field(..., description="Score from confidence (out of 20)")
    payback_score: float = Field(..., description="Score from payback period (out of 15)")
    permitting_score: float = Field(..., description="Score from permitting status (out of 5)")


class RankedBuilding(BuildingResponse):
    """Building with ranking information"""
    ranking_score: float = Field(..., ge=0, le=100, description="Overall ranking score 0-100")
    ranking_position: int = Field(..., ge=1, description="Position in rankings")
    ranking_factors: RankingFactors


class RankingResponse(BaseModel):
    """Response for rankings endpoint"""
    scope: RankingScope
    total_evaluated: int = Field(..., description="Total buildings evaluated")
    rankings: List[RankedBuilding]
    cache_expires_at: str = Field(..., description="ISO 8601 timestamp when cache expires")
