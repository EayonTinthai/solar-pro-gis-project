"""
Common models used across the API
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Detailed error message")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    request_id: str = Field(..., description="Unique request identifier")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="healthy or unhealthy")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    checks: Dict[str, str] = Field(..., description="Individual service checks")
    uptime_seconds: int = Field(..., description="Server uptime in seconds")


class DatasetMetadata(BaseModel):
    """Dataset metadata for stats endpoint"""
    source: str
    version: str
    collection_date: str
    ingestion_date: str
    update_frequency: str
    license: str
    license_url: Optional[str] = None
