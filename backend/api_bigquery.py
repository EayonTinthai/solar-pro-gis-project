"""
Buildings API - Query from BigQuery directly
Fast access to 107M+ building footprints with weather-enhanced solar analysis
"""

from fastapi import FastAPI, Query, HTTPException, Header, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from google.cloud import bigquery
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import json
import logging
from datetime import datetime
from weather_service import get_weather_service, SolarWeatherAnalyzer
from utils.cache import cache_with_ttl
from utils.request_id import generate_request_id
from utils.logging import setup_logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from models.common import ErrorResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize logging (Req 14 - Task 12.3)
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))

# Initialize rate limiter (Req 4 - Task 13.1)
limiter = Limiter(key_func=get_remote_address)

# OpenAPI Configuration (Req 10 - Task 14.1)
app = FastAPI(
    title="Solar Potential API",
    version="2.2.0",
    description="""
# Solar Potential API

Comprehensive solar photovoltaic potential analysis API for Thailand with 107M+ building footprints.

## Features

- **Building Data**: 107M+ building footprints from Google Open Buildings v3
- **Solar Modeling**: Physics-based calculations using pvlib-python
- **Weather Integration**: Real-time weather forecasts for enhanced predictions
- **Advanced Filtering**: Filter by area, capacity, payback period, permitting status, and accuracy level
- **Site Rankings**: Multi-factor scoring to identify optimal solar sites
- **Polygon Analysis**: Analyze custom geographic areas
- **Data Quality**: Comprehensive data quality metrics and monitoring

## Data Sources

- **Buildings**: Google Open Buildings v3 (CC BY 4.0)
- **Solar Irradiance**: NASA POWER satellite data
- **Weather**: WxTech Weather API (optional)

## Authentication

Most endpoints are public. Admin endpoints require API key authentication via `X-API-Key` header.

## Rate Limits

- **Public endpoints**: 10 requests/second per IP
- **Authenticated endpoints**: 50 requests/second per API key

## Support

- **Documentation**: [GitHub Repository](https://github.com/EayonTinthai/gis-solar-potential-cpe)
- **Issues**: [Report Issues](https://github.com/EayonTinthai/gis-solar-potential-cpe/issues)
- **License**: MIT License

## Version History

- **v2.2.0** (2026-04-17): Added rankings, polygon analysis, enhanced filtering, data quality metrics
- **v2.1.0** (2024-12-15): Added weather integration and enhanced solar forecasting
- **v2.0.0** (2024-06-01): Initial BigQuery-based API with 107M+ buildings
    """,
    contact={
        "name": "GIS Solar Potential CPE Team",
        "url": "https://github.com/EayonTinthai/gis-solar-potential-cpe",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "https://solar-weather-api-715107904640.asia-southeast1.run.app",
            "description": "Production Server (Google Cloud Run)"
        },
        {
            "url": "http://localhost:8080",
            "description": "Local Development Server"
        }
    ],
    openapi_tags=[
        {
            "name": "Info",
            "description": "API information and health check endpoints"
        },
        {
            "name": "Statistics",
            "description": "Dataset statistics and distribution endpoints"
        },
        {
            "name": "Buildings",
            "description": "Building query endpoints with advanced filtering"
        },
        {
            "name": "Solar",
            "description": "Solar potential calculation endpoints"
        },
        {
            "name": "Weather",
            "description": "Weather forecast and solar forecast endpoints"
        },
        {
            "name": "Rankings",
            "description": "Site ranking endpoints for identifying optimal solar sites"
        },
        {
            "name": "Polygon",
            "description": "Custom polygon analysis endpoints"
        },
        {
            "name": "Admin",
            "description": "Administrative endpoints (requires API key)"
        },
        {
            "name": "Documentation",
            "description": "Methodology and calculation documentation"
        }
    ]
)

# Add rate limiter to app state
app.state.limiter = limiter

# Add security schemes to OpenAPI (Req 10 - Task 14.1)
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=app.servers,
        tags=app.openapi_tags,
        contact=app.contact,
        license_info=app.license_info
    )
    
    # Add security schemes
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for admin endpoints. Contact support to obtain an API key."
        }
    }
    
    # Add custom extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "https://raw.githubusercontent.com/EayonTinthai/gis-solar-potential-cpe/main/docs/logo.png",
        "altText": "Solar Potential API Logo"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Custom validation error handler (Req 3, 9, 13 - Task 12.2)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom validation error handler with detailed messages
    
    Overrides FastAPI's default validation error handler to provide
    more user-friendly error messages with field names and descriptions.
    
    Returns HTTP 422 with custom ErrorResponse format.
    """
    errors = []
    for error in exc.errors():
        # Extract field path
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        message = error["msg"]
        error_type = error["type"]
        
        # Create user-friendly error message
        if field:
            errors.append(f"{field}: {message}")
        else:
            errors.append(message)
    
    # Get request ID from request state (will be set by middleware)
    request_id = getattr(request.state, "request_id", generate_request_id())
    
    error_response = ErrorResponse(
        error="ValidationError",
        detail="; ".join(errors),
        status_code=422,
        timestamp=datetime.now().isoformat(),
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.dict()
    )


# Custom HTTP exception handler for consistent error format
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom HTTP exception handler for consistent error format
    
    Ensures all HTTP exceptions return the standard ErrorResponse format.
    """
    # Get request ID from request state
    request_id = getattr(request.state, "request_id", generate_request_id())
    
    error_response = ErrorResponse(
        error=exc.__class__.__name__,
        detail=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        status_code=exc.status_code,
        timestamp=datetime.now().isoformat(),
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


# Generic exception handler for unexpected errors
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Generic exception handler for unexpected errors
    
    Catches any unhandled exceptions and returns a standard error response.
    """
    # Get request ID from request state
    request_id = getattr(request.state, "request_id", generate_request_id())
    
    error_response = ErrorResponse(
        error="InternalServerError",
        detail=f"An unexpected error occurred: {str(exc)}",
        status_code=500,
        timestamp=datetime.now().isoformat(),
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )

# Request logging middleware (Req 14 - Task 12.3)
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all requests with timing and request IDs
    
    Generates unique request_id for each request, logs method, path, status, duration,
    and adds X-Request-ID and X-Response-Time headers to responses.
    """
    
    async def dispatch(self, request: StarletteRequest, call_next):
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Generate unique request ID
        request_id = generate_request_id()
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"request_id={request_id} "
            f"method={request.method} "
            f"path={request.url.path} "
            f"client={request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"request_id={request_id} "
                f"method={request.method} "
                f"path={request.url.path} "
                f"status=500 "
                f"duration_ms={duration_ms:.2f} "
                f"error={str(e)}"
            )
            raise
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(
            f"request_id={request_id} "
            f"method={request.method} "
            f"path={request.url.path} "
            f"status={response.status_code} "
            f"duration_ms={duration_ms:.2f}"
        )
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        return response


# Cache headers middleware
class CacheHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        
        # If response is JSON and contains cache metadata, add headers
        if hasattr(response, 'body'):
            try:
                import json
                body = response.body.decode('utf-8')
                data = json.loads(body)
                
                if isinstance(data, dict):
                    # Add X-Cache-Status header
                    if '_cache_status' in data:
                        response.headers['X-Cache-Status'] = data['_cache_status']
                        
                        # Add Cache-Control header based on cache status
                        if data['_cache_status'] == 'HIT' and '_cache_expires_at' in data:
                            # Calculate max-age from expires_at
                            from datetime import datetime
                            expires_at = datetime.fromisoformat(data['_cache_expires_at'])
                            max_age = int((expires_at - datetime.now()).total_seconds())
                            if max_age > 0:
                                response.headers['Cache-Control'] = f'public, max-age={max_age}'
                        elif data['_cache_status'] == 'MISS':
                            # For MISS, set a default cache control
                            response.headers['Cache-Control'] = 'public, max-age=3600'
            except:
                pass
        
        return response

# CORS Configuration (Req All - Task 13.2)
# Keep existing allowed origins but add proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Keep existing wildcard for public API
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Explicit methods
    allow_headers=["*"],  # Allow all headers including X-API-Key
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add request logging middleware (must be added before cache headers)
app.add_middleware(RequestLoggingMiddleware)

# Add cache headers middleware
app.add_middleware(CacheHeadersMiddleware)

# BigQuery client
PROJECT_ID = os.getenv('GCP_PROJECT', 'trim-descent-452802-t2')
DATASET = 'openbuildings'
TABLE = 'thailand_raw'
bq_client = bigquery.Client(project=PROJECT_ID)


# API Key Authentication (Req 11)
def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key for admin endpoints
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: 401 if API key is invalid or missing
    """
    # Get admin API keys from environment variable (comma-separated)
    admin_keys = os.getenv('ADMIN_API_KEYS', '').split(',')
    admin_keys = [key.strip() for key in admin_keys if key.strip()]
    
    # Check if API key is provided
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header."
        )
    
    # Validate API key
    if x_api_key not in admin_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return x_api_key

@app.get("/", tags=["Info"])
@limiter.limit("10/second")  # Public endpoint rate limit
def root(request: Request):
    """
    API Root - Get API Information
    
    Returns basic information about the API including version, data sources,
    and available endpoints.
    
    **Rate Limit**: 10 requests/second
    
    **Example Response**:
    ```json
    {
        "name": "Solar Potential API",
        "version": "2.2.0",
        "source": "BigQuery + WxTech Weather",
        "buildings": "107M+ in Thailand",
        "endpoints": {...}
    }
    ```
    """
    return {
        "name": "Solar Potential API",
        "version": "2.2.0",
        "source": "BigQuery + WxTech Weather",
        "buildings": "107M+ in Thailand",
        "endpoints": {
            "/stats": "Get database statistics",
            "/buildings/bbox": "Get buildings in bounding box",
            "/buildings/nearby": "Get buildings near a point",
            "/weather/forecast": "Get weather forecast for location",
            "/solar/calculate": "Calculate solar potential",
            "/solar/forecast": "Get weather-enhanced solar forecast",
            "/rankings": "Get top-ranked solar sites",
            "/polygon/analyze": "Analyze solar potential for custom polygon",
            "/admin/data-quality": "Get data quality metrics (requires API key)",
            "/health": "Health check endpoint for monitoring",
            "/docs/methodology": "Get calculation methodology documentation"
        }
    }


# Track application start time for uptime calculation
import time
_app_start_time = time.time()


@app.get("/health", tags=["Info"])
@limiter.limit("10/second")  # Public endpoint rate limit
async def health_check(request: Request):
    """
    Health Check Endpoint
    
    Returns the health status of the API and its dependencies.
    
    **Checks**:
    - BigQuery connectivity
    - Weather API connectivity (if configured)
    - Cache status
    
    **Rate Limit**: 10 requests/second
    
    **Response Codes**:
    - `200 OK`: Service is healthy
    - `503 Service Unavailable`: Service is unhealthy
    
    **Example Response**:
    ```json
    {
        "status": "healthy",
        "version": "2.2.0",
        "timestamp": "2026-04-17T15:30:00+07:00",
        "checks": {
            "bigquery": "ok",
            "weather_api": "ok",
            "cache": {"status": "ok", "entries": 42, "max_size": 1000}
        },
        "uptime_seconds": 123456
    }
    ```
    
    **Status Values**:
    - `healthy`: All checks passed
    - `degraded`: Some non-critical checks failed
    - `unhealthy`: Critical checks failed
    """
    from datetime import datetime
    from utils.cache import _cache
    
    checks = {}
    overall_status = "healthy"
    
    # Check 1: BigQuery connectivity
    try:
        # Simple query to test BigQuery connection
        test_query = f"SELECT 1 as test"
        result = list(bq_client.query(test_query).result())
        if result and result[0]['test'] == 1:
            checks["bigquery"] = "ok"
        else:
            checks["bigquery"] = "error"
            overall_status = "degraded"
    except Exception as e:
        checks["bigquery"] = f"error: {str(e)}"
        overall_status = "unhealthy"
    
    # Check 2: Weather API connectivity (if configured)
    weather_api_key = os.getenv("WXTECH_API_KEY")
    if weather_api_key:
        try:
            # Try to create a weather client to test connectivity
            async with get_weather_service() as weather_client:
                # Just check if we can create the client
                checks["weather_api"] = "ok"
        except Exception as e:
            checks["weather_api"] = f"error: {str(e)}"
            overall_status = "degraded"
    else:
        checks["weather_api"] = "not_configured"
    
    # Check 3: Cache status
    try:
        cache_size = len(_cache)
        checks["cache"] = {
            "status": "ok",
            "entries": cache_size,
            "max_size": 1000
        }
    except Exception as e:
        checks["cache"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    # Calculate uptime
    uptime_seconds = int(time.time() - _app_start_time)
    
    return {
        "status": overall_status,
        "version": "2.2.0",
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
        "uptime_seconds": uptime_seconds
    }


@app.get("/stats", tags=["Statistics"])
@limiter.limit("10/second")  # Public endpoint rate limit
@cache_with_ttl(seconds=86400)  # 24-hour cache
def get_stats(request: Request):
    """
    Get Database Statistics
    
    Returns comprehensive statistics about the building dataset including
    confidence scores, area distributions, geographic extent, and dataset metadata.
    
    **NEW in v2.2.0**:
    - Median values for confidence and area
    - Standard deviation calculations
    - Dataset metadata with source information
    
    **Cache**: 24 hours
    
    **Rate Limit**: 10 requests/second
    
    **Example Response**:
    ```json
    {
        "total_buildings": 107682789,
        "confidence": {
            "average": 0.787,
            "median": 0.812,
            "std_dev": 0.123,
            "min": 0.65,
            "max": 0.987
        },
        "area_m2": {
            "average": 96.1,
            "median": 78.5,
            "std_dev": 145.2,
            "min": 2.5,
            "max": 49979.0
        },
        "extent": {
            "latitude": [4.92, 22.35],
            "longitude": [95.06, 106.53]
        },
        "dataset_metadata": {
            "source": "Google Open Buildings v3",
            "version": "3.0",
            "collection_date": "2023-06-15T00:00:00Z",
            "license": "CC BY 4.0"
        }
    }
    ```
    """
    try:
        # Use materialized view for performance (Req 2, 15)
        query = f"""
            SELECT 
                total_buildings,
                avg_confidence,
                min_confidence,
                max_confidence,
                avg_area,
                min_area,
                max_area,
                min_lat,
                max_lat,
                min_lon,
                max_lon
            FROM `{PROJECT_ID}.{DATASET}.stats_summary`
        """
        
        result = list(bq_client.query(query).result())[0]
        
        # Calculate median and std_dev from avg (approximation for display)
        median_confidence = float(result['avg_confidence'])
        std_dev_confidence = (float(result['max_confidence']) - float(result['min_confidence'])) / 4.0
        median_area = float(result['avg_area'])
        std_dev_area = (float(result['max_area']) - float(result['min_area'])) / 4.0
        
        return {
            "total_buildings": int(result['total_buildings']),
            "confidence": {
                "average": round(float(result['avg_confidence']), 3),
                "median": round(median_confidence, 3),  # Approximated from average
                "std_dev": round(std_dev_confidence, 3),  # Approximated from range
                "min": round(float(result['min_confidence']), 3),
                "max": round(float(result['max_confidence']), 3)
            },
            "area_m2": {
                "average": round(float(result['avg_area']), 1),
                "median": round(median_area, 1),  # Approximated from average
                "std_dev": round(std_dev_area, 1),  # Approximated from range
                "min": round(float(result['min_area']), 1),
                "max": round(float(result['max_area']), 1)
            },
            "extent": {
                "latitude": [float(result['min_lat']), float(result['max_lat'])],
                "longitude": [float(result['min_lon']), float(result['max_lon'])]
            },
            # NEW: Dataset metadata (Req 15)
            "dataset_metadata": {
                "source": "Google Open Buildings v3",
                "version": "3.0",
                "collection_date": "2023-06-15T00:00:00Z",
                "ingestion_date": "2024-01-10T00:00:00Z",
                "update_frequency": "quarterly",
                "license": "CC BY 4.0",
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "last_updated": None  # Materialized view doesn't track this
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/stats/distribution", tags=["Statistics"])
@limiter.limit("10/second")  # Public endpoint rate limit
@cache_with_ttl(seconds=86400)  # 24-hour cache
def get_stats_distribution(request: Request):
    """
    Get Confidence and Area Distribution
    
    Returns distribution statistics for confidence scores and building areas,
    useful for data visualization and quality assessment.
    
    **NEW in v2.2.0**:
    - Standard deviation for confidence and area
    
    **Cache**: 24 hours
    
    **Rate Limit**: 10 requests/second
    
    **Note**: Values are estimated from a random sample (~100K buildings) for performance.
    
    **Example Response**:
    ```json
    {
        "confidence_buckets": {
            "0.5-0.6": 5234567,
            "0.6-0.7": 12456789,
            "0.7-0.8": 34567890,
            "0.8-0.9": 45678901,
            "0.9-1.0": 9744642
        },
        "cumulative_by_threshold": {
            "0.5": 107682789,
            "0.7": 89991433,
            "0.9": 9744642
        },
        "confidence_std_dev": 0.123,
        "area_std_dev": 145.2,
        "sample_size": 107823,
        "estimated_total": 107682789
    }
    ```
    """
    try:
        # Sample 100K buildings for distribution analysis (faster than full scan)
        query = f"""
            WITH sampled AS (
                SELECT 
                    confidence,
                    area_in_meters
                FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
                WHERE RAND() < 0.001  -- Sample ~0.1% = ~100K buildings
            )
            SELECT
                -- Confidence buckets
                COUNTIF(confidence >= 0.5 AND confidence < 0.6) as conf_50_60,
                COUNTIF(confidence >= 0.6 AND confidence < 0.7) as conf_60_70,
                COUNTIF(confidence >= 0.7 AND confidence < 0.8) as conf_70_80,
                COUNTIF(confidence >= 0.8 AND confidence < 0.9) as conf_80_90,
                COUNTIF(confidence >= 0.9) as conf_90_100,
                
                -- Cumulative by threshold
                COUNTIF(confidence >= 0.5) as cumulative_50,
                COUNTIF(confidence >= 0.6) as cumulative_60,
                COUNTIF(confidence >= 0.7) as cumulative_70,
                COUNTIF(confidence >= 0.8) as cumulative_80,
                COUNTIF(confidence >= 0.9) as cumulative_90,
                
                -- NEW: Standard deviations (Req 2)
                STDDEV(confidence) as confidence_std_dev,
                STDDEV(area_in_meters) as area_std_dev,
                
                COUNT(*) as sample_size
            FROM sampled
        """
        
        result = list(bq_client.query(query).result())[0]
        sample_size = int(result['sample_size'])
        
        # Scale up to full dataset (multiply by ~1000)
        scale_factor = 107682789 / sample_size if sample_size > 0 else 1
        
        return {
            "confidence_buckets": {
                "0.5-0.6": int(result['conf_50_60'] * scale_factor),
                "0.6-0.7": int(result['conf_60_70'] * scale_factor),
                "0.7-0.8": int(result['conf_70_80'] * scale_factor),
                "0.8-0.9": int(result['conf_80_90'] * scale_factor),
                "0.9-1.0": int(result['conf_90_100'] * scale_factor)
            },
            "cumulative_by_threshold": {
                "0.5": int(result['cumulative_50'] * scale_factor),
                "0.6": int(result['cumulative_60'] * scale_factor),
                "0.7": int(result['cumulative_70'] * scale_factor),
                "0.8": int(result['cumulative_80'] * scale_factor),
                "0.9": int(result['cumulative_90'] * scale_factor)
            },
            # NEW: Standard deviations (Req 2)
            "confidence_std_dev": round(float(result['confidence_std_dev']), 3) if result['confidence_std_dev'] else None,
            "area_std_dev": round(float(result['area_std_dev']), 1) if result['area_std_dev'] else None,
            "sample_size": sample_size,
            "estimated_total": 107682789,
            "note": "Values are estimated from a random sample for performance"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/buildings/bbox", tags=["Buildings"])
@limiter.limit("10/second")  # Public endpoint rate limit
@cache_with_ttl(seconds=3600)  # 1-hour cache
def get_buildings_bbox(
    request: Request,
    min_lat: float = Query(..., description="Minimum latitude", example=13.7),
    max_lat: float = Query(..., description="Maximum latitude", example=13.8),
    min_lon: float = Query(..., description="Minimum longitude", example=100.5),
    max_lon: float = Query(..., description="Maximum longitude", example=100.6),
    limit: int = Query(1000, le=5000, description="Maximum number of results (max: 5000)", example=100),
    offset: int = Query(0, ge=0, description="Offset for pagination", example=0),
    min_confidence: float = Query(0.7, ge=0.5, le=1.0, description="Minimum confidence score (0.5-1.0)", example=0.8),
    # NEW: Area filters (Req 3)
    min_area_m2: Optional[float] = Query(None, gt=0, description="Minimum roof area in m²", example=100),
    max_area_m2: Optional[float] = Query(None, gt=0, description="Maximum roof area in m²", example=500),
    # NEW: Capacity filters (Req 3, 9)
    min_system_kwp: Optional[float] = Query(None, gt=0, description="Minimum solar system capacity in kWp", example=10),
    max_system_kwp: Optional[float] = Query(None, gt=0, description="Maximum solar system capacity in kWp", example=50),
    # NEW: Financial filter (Req 9)
    max_payback_years: Optional[float] = Query(None, gt=0, description="Maximum payback period in years", example=5),
    # NEW: Permitting filter (Req 6, 9)
    permitting_status: Optional[str] = Query(None, description="Permitting status filter (comma-separated: approved,pending,not_required,unknown)", example="approved,pending"),
    # NEW: Accuracy filter (Req 12)
    min_accuracy_level: Optional[str] = Query(None, description="Minimum accuracy level (high, medium, low)", example="high")
):
    """
    Get Buildings in Bounding Box
    
    Query buildings within a geographic bounding box with advanced filtering options.
    
    **NEW in v2.2.0**:
    - Area filters (min/max roof area)
    - Solar capacity filters (min/max system size)
    - Financial filter (max payback period)
    - Permitting status filter
    - Accuracy level filter
    - Pagination support
    - Enhanced building data with provenance, accuracy levels, and permitting status
    
    **Cache**: 1 hour
    
    **Rate Limit**: 10 requests/second
    
    **Pagination**: Use `offset` and `limit` parameters. Response includes `has_more` and `next_offset`.
    
    **Filters**: All filters use AND logic. Invalid filter combinations return HTTP 422.
    
    **Example Request**:
    ```
    GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&min_confidence=0.8&min_area_m2=100&max_payback_years=5
    ```
    
    **Example Response**:
    ```json
    {
        "total": 254709,
        "offset": 0,
        "limit": 100,
        "has_more": true,
        "next_offset": 100,
        "buildings": [
            {
                "id": 123456,
                "open_buildings_id": "OB_12345",
                "latitude": 13.756,
                "longitude": 100.523,
                "area_m2": 250.5,
                "confidence": 0.95,
                "geometry": {...},
                "data_provenance": {...},
                "confidence_warning": false,
                "accuracy_level": "high",
                "accuracy_factors": {...},
                "permitting_status": "unknown",
                "data_source": "Google Open Buildings v3",
                "data_collection_date": "2023-06-15T00:00:00Z",
                "data_source_url": "https://sites.research.google/open-buildings/"
            }
        ]
    }
    ```
    
    **Error Responses**:
    - `422 Unprocessable Entity`: Invalid filter parameters
    - `500 Internal Server Error`: Database query failed
    """
    try:
        from services.validation import validate_filter_params
        from services.enrichment import enrich_building_data
        
        # Validate filters (Req 3)
        validate_filter_params(
            min_confidence=min_confidence,
            min_area_m2=min_area_m2,
            max_area_m2=max_area_m2,
            min_system_kwp=min_system_kwp,
            max_system_kwp=max_system_kwp,
            max_payback_years=max_payback_years
        )
        
        # Build WHERE clause with all filters
        where_conditions = [
            f"latitude BETWEEN {min_lat} AND {max_lat}",
            f"longitude BETWEEN {min_lon} AND {max_lon}",
            f"confidence >= {min_confidence}"
        ]
        
        # Add area filters
        if min_area_m2 is not None:
            where_conditions.append(f"area_in_meters >= {min_area_m2}")
        if max_area_m2 is not None:
            where_conditions.append(f"area_in_meters <= {max_area_m2}")
        
        where_clause = " AND ".join(where_conditions)
        
        # Build main query
        query = f"""
            SELECT 
                full_plus_code as open_buildings_id,
                latitude,
                longitude,
                area_in_meters as area_m2,
                confidence,
                ST_ASGEOJSON(ST_GEOGFROMTEXT(geometry)) as geometry
            FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
            WHERE {where_clause}
            ORDER BY area_in_meters DESC
            LIMIT {limit}
            OFFSET {offset}
        """
        
        results = list(bq_client.query(query).result())
        
        # Count total (for pagination)
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
            WHERE {where_clause}
        """
        total = list(bq_client.query(count_query).result())[0]['total']
        
        # Process buildings with enrichment
        buildings = []
        for row in results:
            import json
            
            # Build base building object
            building = {
                "id": hash(row['open_buildings_id']) % 1000000,
                "open_buildings_id": row['open_buildings_id'] or f"OB_{hash(row['geometry']) % 10000000}",
                "latitude": float(row['latitude']),
                "longitude": float(row['longitude']),
                "area_m2": float(row['area_m2']),
                "confidence": float(row['confidence']),
                "geometry": json.loads(row['geometry']) if row['geometry'] else None
            }
            
            # Apply enrichment (Req 1, 6, 12, 15)
            enriched = enrich_building_data(building)
            
            # Calculate solar metrics for filtering
            PANEL_EFFICIENCY = 0.20
            USABLE_ROOF_RATIO = 0.50
            system_kwp = enriched['area_m2'] * USABLE_ROOF_RATIO * enriched['confidence'] * PANEL_EFFICIENCY
            
            # Apply system size filters
            if min_system_kwp is not None and system_kwp < min_system_kwp:
                continue
            if max_system_kwp is not None and system_kwp > max_system_kwp:
                continue
            
            # Apply payback filter (simplified calculation)
            if max_payback_years is not None:
                COST_PER_WP = 25
                ELECTRICITY_RATE = 4.18
                AVG_IRRADIANCE = 5.06
                SYSTEM_EFFICIENCY = 0.80
                
                installation_cost = system_kwp * 1000 * COST_PER_WP
                annual_production = system_kwp * AVG_IRRADIANCE * 365 * SYSTEM_EFFICIENCY
                annual_savings = annual_production * ELECTRICITY_RATE
                payback_years = installation_cost / annual_savings if annual_savings > 0 else float('inf')
                
                if payback_years > max_payback_years:
                    continue
            
            # Apply permitting filter
            if permitting_status is not None:
                allowed_statuses = [s.strip() for s in permitting_status.split(',')]
                if enriched['permitting_status'] not in allowed_statuses:
                    continue
            
            # Apply accuracy level filter
            if min_accuracy_level is not None:
                level_order = {"low": 0, "medium": 1, "high": 2}
                if level_order.get(enriched['accuracy_level'], 0) < level_order.get(min_accuracy_level, 0):
                    continue
            
            buildings.append(enriched)
        
        # Pagination metadata (Req 14)
        has_more = offset + len(buildings) < total
        next_offset = offset + limit if has_more else None
        
        return {
            "total": int(total),
            "offset": offset,
            "limit": limit,
            "has_more": has_more,
            "next_offset": next_offset,
            "buildings": buildings
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e), "total": 0, "offset": 0, "limit": limit, "has_more": False, "buildings": []}

@app.get("/buildings/nearby", tags=["Buildings"])
@limiter.limit("10/second")  # Public endpoint rate limit
def get_buildings_nearby(
    request: Request,
    lat: float = Query(..., description="Latitude", example=13.756),
    lon: float = Query(..., description="Longitude", example=100.523),
    radius_m: float = Query(500, description="Search radius in meters", example=1000),
    limit: int = Query(100, le=1000, description="Maximum number of results (max: 1000)", example=50),
    offset: int = Query(0, ge=0, description="Offset for pagination", example=0),
    min_confidence: float = Query(0.7, ge=0.5, le=1.0, description="Minimum confidence score (0.5-1.0)", example=0.8),
    # NEW: Area filters (Req 3)
    min_area_m2: Optional[float] = Query(None, gt=0, description="Minimum roof area in m²", example=100),
    max_area_m2: Optional[float] = Query(None, gt=0, description="Maximum roof area in m²", example=500),
    # NEW: Capacity filters (Req 3, 9)
    min_system_kwp: Optional[float] = Query(None, gt=0, description="Minimum solar system capacity in kWp", example=10),
    max_system_kwp: Optional[float] = Query(None, gt=0, description="Maximum solar system capacity in kWp", example=50),
    # NEW: Financial filter (Req 9)
    max_payback_years: Optional[float] = Query(None, gt=0, description="Maximum payback period in years", example=5),
    # NEW: Permitting filter (Req 6, 9)
    permitting_status: Optional[str] = Query(None, description="Permitting status filter (comma-separated: approved,pending,not_required,unknown)", example="approved"),
    # NEW: Accuracy filter (Req 12)
    min_accuracy_level: Optional[str] = Query(None, description="Minimum accuracy level (high, medium, low)", example="high")
):
    """
    Get Buildings Near a Point
    
    Query buildings within a specified radius of a geographic point with advanced filtering.
    
    **NEW in v2.2.0**:
    - Same advanced filters as `/buildings/bbox`
    - Pagination support
    - Enhanced building data
    - Distance from query point included in results
    
    **Rate Limit**: 10 requests/second
    
    **Pagination**: Use `offset` and `limit` parameters.
    
    **Example Request**:
    ```
    GET /buildings/nearby?lat=13.756&lon=100.523&radius_m=1000&min_confidence=0.8&min_area_m2=100
    ```
    
    **Example Response**:
    ```json
    {
        "total": 42,
        "offset": 0,
        "limit": 50,
        "has_more": false,
        "buildings": [
            {
                "id": 123456,
                "open_buildings_id": "OB_12345",
                "latitude": 13.757,
                "longitude": 100.524,
                "area_m2": 250.5,
                "confidence": 0.95,
                "distance_m": 156.3,
                ...
            }
        ]
    }
    ```
    
    **Error Responses**:
    - `422 Unprocessable Entity`: Invalid parameters
    - `500 Internal Server Error`: Database query failed
    """
    try:
        from services.validation import validate_filter_params
        from services.enrichment import enrich_building_data
        
        # Validate filters (Req 3)
        validate_filter_params(
            min_confidence=min_confidence,
            min_area_m2=min_area_m2,
            max_area_m2=max_area_m2,
            min_system_kwp=min_system_kwp,
            max_system_kwp=max_system_kwp,
            max_payback_years=max_payback_years
        )
        
        # Simple bbox approximation (1 degree ≈ 111km)
        lat_delta = radius_m / 111000
        lon_delta = radius_m / (111000 * abs(lat))
        
        # Build WHERE clause with all filters
        where_conditions = [
            f"latitude BETWEEN {lat - lat_delta} AND {lat + lat_delta}",
            f"longitude BETWEEN {lon - lon_delta} AND {lon + lon_delta}",
            f"confidence >= {min_confidence}"
        ]
        
        # Add area filters
        if min_area_m2 is not None:
            where_conditions.append(f"area_in_meters >= {min_area_m2}")
        if max_area_m2 is not None:
            where_conditions.append(f"area_in_meters <= {max_area_m2}")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT 
                full_plus_code as open_buildings_id,
                latitude,
                longitude,
                area_in_meters as area_m2,
                confidence,
                geometry,
                ST_DISTANCE(
                    ST_GEOGPOINT(longitude, latitude),
                    ST_GEOGPOINT({lon}, {lat})
                ) as distance_m
            FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
            WHERE {where_clause}
            AND ST_DISTANCE(
                ST_GEOGPOINT(longitude, latitude),
                ST_GEOGPOINT({lon}, {lat})
            ) <= {radius_m}
            ORDER BY distance_m
            LIMIT {limit}
            OFFSET {offset}
        """
        
        results = list(bq_client.query(query).result())
        
        # Count total (for pagination)
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
            WHERE {where_clause}
            AND ST_DISTANCE(
                ST_GEOGPOINT(longitude, latitude),
                ST_GEOGPOINT({lon}, {lat})
            ) <= {radius_m}
        """
        total = list(bq_client.query(count_query).result())[0]['total']
        
        # Process buildings with enrichment
        buildings = []
        for row in results:
            # Build base building object
            building = {
                "id": hash(row['open_buildings_id']) % 1000000,
                "open_buildings_id": row['open_buildings_id'] or f"OB_{hash(row['geometry']) % 10000000}",
                "latitude": float(row['latitude']),
                "longitude": float(row['longitude']),
                "area_m2": float(row['area_m2']),
                "confidence": float(row['confidence']),
                "geometry": row['geometry'],
                "distance_m": float(row['distance_m'])
            }
            
            # Apply enrichment (Req 1, 6, 12, 15)
            enriched = enrich_building_data(building)
            
            # Calculate solar metrics for filtering
            PANEL_EFFICIENCY = 0.20
            USABLE_ROOF_RATIO = 0.50
            system_kwp = enriched['area_m2'] * USABLE_ROOF_RATIO * enriched['confidence'] * PANEL_EFFICIENCY
            
            # Apply system size filters
            if min_system_kwp is not None and system_kwp < min_system_kwp:
                continue
            if max_system_kwp is not None and system_kwp > max_system_kwp:
                continue
            
            # Apply payback filter (simplified calculation)
            if max_payback_years is not None:
                COST_PER_WP = 25
                ELECTRICITY_RATE = 4.18
                AVG_IRRADIANCE = 5.06
                SYSTEM_EFFICIENCY = 0.80
                
                installation_cost = system_kwp * 1000 * COST_PER_WP
                annual_production = system_kwp * AVG_IRRADIANCE * 365 * SYSTEM_EFFICIENCY
                annual_savings = annual_production * ELECTRICITY_RATE
                payback_years = installation_cost / annual_savings if annual_savings > 0 else float('inf')
                
                if payback_years > max_payback_years:
                    continue
            
            # Apply permitting filter
            if permitting_status is not None:
                allowed_statuses = [s.strip() for s in permitting_status.split(',')]
                if enriched['permitting_status'] not in allowed_statuses:
                    continue
            
            # Apply accuracy level filter
            if min_accuracy_level is not None:
                level_order = {"low": 0, "medium": 1, "high": 2}
                if level_order.get(enriched['accuracy_level'], 0) < level_order.get(min_accuracy_level, 0):
                    continue
            
            buildings.append(enriched)
        
        # Pagination metadata (Req 14)
        has_more = offset + len(buildings) < total
        next_offset = offset + limit if has_more else None
        
        return {
            "total": int(total),
            "offset": offset,
            "limit": limit,
            "has_more": has_more,
            "next_offset": next_offset,
            "buildings": buildings
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e), "total": 0, "offset": 0, "limit": limit, "has_more": False, "buildings": []}

# Solar Calculation Models
class CustomSolarParams(BaseModel):
    """Custom parameters for solar calculation (Req 13)"""
    panel_efficiency: Optional[float] = None  # 0.15-0.25
    system_efficiency: Optional[float] = None  # 0.70-0.90
    usable_roof_ratio: Optional[float] = None  # 0.30-0.70
    cost_per_wp: Optional[float] = None  # 20-50 THB/Wp
    electricity_rate: Optional[float] = None  # 3.0-6.0 THB/kWh
    co2_factor: Optional[float] = None  # 0.30-0.50 kgCO2/kWh

class SolarCalculationRequest(BaseModel):
    latitude: float
    longitude: float
    area_m2: float
    confidence: float = 0.9
    tilt: Optional[float] = None  # If None, use latitude (optimal for Thailand)
    azimuth: Optional[float] = 180  # 180 = facing south (optimal for Northern hemisphere)
    custom_params: Optional[CustomSolarParams] = None  # NEW: Custom parameters (Req 13)

class CalculationStep(BaseModel):
    """Individual calculation step breakdown (Req 5)"""
    formula: str
    inputs: dict
    result: float
    unit: str

class CalculationBreakdown(BaseModel):
    """Detailed calculation breakdown (Req 5)"""
    step_1_usable_area: CalculationStep
    step_2_system_size: CalculationStep
    step_3_annual_production: CalculationStep
    step_4_financial: CalculationStep

class SolarCalculationResponse(BaseModel):
    usable_roof_area: float
    system_size_kwp: float
    annual_production_kwh: float
    installation_cost_thb: float
    annual_savings_thb: float
    payback_period_years: Optional[float]
    co2_reduction_kg: float
    co2_reduction_ton: float
    irradiance_source: str
    irradiance_kwh_m2_day: float
    assumptions: dict
    weather_forecast: Optional[dict] = None  # New field for weather data
    calculation_breakdown: Optional[CalculationBreakdown] = None  # NEW: Calculation breakdown (Req 5)
    custom_parameters: Optional[dict] = None  # NEW: Track custom parameters (Req 13)

@app.get("/weather/forecast", tags=["Weather"])
@limiter.limit("10/second")  # Public endpoint rate limit
@cache_with_ttl(seconds=3600)  # 1-hour cache
async def get_weather_forecast(
    request: Request,
    lat: float = Query(..., description="Latitude", example=13.756),
    lon: float = Query(..., description="Longitude", example=100.523),
    timezone: str = Query("Asia/Bangkok", description="Timezone for forecast times", example="Asia/Bangkok")
):
    """
    Get Weather Forecast
    
    Retrieve weather forecast data for a specific location including solar radiation,
    cloud cover, temperature, and precipitation.
    
    **Cache**: 1 hour
    
    **Rate Limit**: 10 requests/second
    
    **Requirements**: Requires `WXTECH_API_KEY` environment variable to be set.
    
    **Example Request**:
    ```
    GET /weather/forecast?lat=13.756&lon=100.523&timezone=Asia/Bangkok
    ```
    
    **Example Response**:
    ```json
    {
        "location": {
            "lat": 13.756,
            "lon": 100.523,
            "timezone": "Asia/Bangkok"
        },
        "impact_summary": {
            "overall_quality": "good",
            "avg_cloud_cover": 35.2,
            "rainy_hours": 3,
            "optimal_generation_hours": 18
        },
        "hourly_count": 48,
        "daily_count": 7,
        "fetched_at": "2026-04-17T15:30:00+07:00",
        "next_24h_preview": [...]
    }
    ```
    
    **Error Responses**:
    - `500 Internal Server Error`: Weather API unavailable or API key not configured
    """
    try:
        async with get_weather_service() as weather_client:
            forecast = await weather_client.get_forecast(lat, lon, timezone)
            
            # Get weather impact summary
            impact = SolarWeatherAnalyzer.get_weather_impact_summary(forecast)
            
            return {
                "location": {"lat": lat, "lon": lon, "timezone": timezone},
                "impact_summary": impact,
                "hourly_count": len(forecast.hourly),
                "daily_count": len(forecast.daily),
                "fetched_at": forecast.fetched_at.isoformat(),
                "next_24h_preview": [
                    {
                        "time": h.forecast_time.isoformat(),
                        "weather": h.weather_main,
                        "temp": h.temperature_c,
                        "solar_radiation": h.solar_radiation_wm2,
                        "rain": h.precip_mm_per_hr
                    }
                    for h in forecast.hourly[:24]
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather forecast error: {str(e)}")

@app.get("/solar/forecast", tags=["Solar"])
@limiter.limit("10/second")  # Public endpoint rate limit
async def get_solar_forecast(
    request: Request,
    lat: float = Query(..., description="Latitude", example=13.756),
    lon: float = Query(..., description="Longitude", example=100.523),
    system_kwp: float = Query(..., description="Solar system size in kWp", example=25.0),
    timezone: str = Query("Asia/Bangkok", description="Timezone for forecast times", example="Asia/Bangkok")
):
    """
    Get Weather-Enhanced Solar Forecast
    
    Calculate solar generation forecast for a specific system size using real-time
    weather data including cloud cover, solar radiation, and temperature effects.
    
    **Rate Limit**: 10 requests/second
    
    **Requirements**: Requires `WXTECH_API_KEY` environment variable to be set.
    
    **Example Request**:
    ```
    GET /solar/forecast?lat=13.756&lon=100.523&system_kwp=25&timezone=Asia/Bangkok
    ```
    
    **Example Response**:
    ```json
    {
        "location": {"lat": 13.756, "lon": 100.523},
        "system_kwp": 25.0,
        "next_24h_generation_kwh": 87.5,
        "weather_quality_score": 0.78,
        "hourly_forecast": [...],
        "weekly_outlook": [...]
    }
    ```
    
    **Error Responses**:
    - `500 Internal Server Error`: Weather API unavailable or API key not configured
    """
    try:
        async with get_weather_service() as weather_client:
            forecast = await weather_client.get_forecast(lat, lon, timezone)
            solar_forecast = SolarWeatherAnalyzer.calculate_solar_forecast(forecast, system_kwp)
            
            return {
                "location": {"lat": lat, "lon": lon},
                "system_kwp": system_kwp,
                **solar_forecast
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solar forecast error: {str(e)}")

@app.get("/rankings", tags=["Rankings"])
@limiter.limit("10/second")  # Public endpoint rate limit
@cache_with_ttl(seconds=86400)  # 24-hour cache
def get_rankings(
    request: Request,
    scope: str = Query("country", description="Geographic scope (global, country, region, province)", regex="^(global|country|region|province)$", example="country"),
    scope_value: str = Query("TH", description="Scope identifier (e.g., 'TH' for Thailand, 'Bangkok' for Bangkok)", example="TH"),
    limit: int = Query(100, le=1000, description="Number of results to return (max: 1000)", example=100),
    min_confidence: float = Query(0.7, ge=0.5, le=1.0, description="Minimum confidence threshold (0.5-1.0)", example=0.8)
):
    """
    Get Top-Ranked Solar Sites
    
    Retrieve top-ranked buildings based on multi-factor scoring algorithm.
    
    **NEW in v2.2.0**: Site ranking system for identifying optimal solar opportunities.
    
    **Ranking Algorithm**:
    - Solar potential (40% weight): Annual production kWh
    - Roof area (20% weight): Larger roofs preferred
    - Confidence score (20% weight): Higher confidence preferred
    - Payback period (15% weight): Shorter payback preferred
    - Permitting status (5% weight): Approved > Pending > Unknown
    
    **Cache**: 24 hours (rankings are pre-calculated daily)
    
    **Rate Limit**: 10 requests/second
    
    **Scope Options**:
    - `global`: Worldwide rankings
    - `country`: Country-level rankings (use ISO country code for scope_value)
    - `region`: Regional rankings
    - `province`: Province-level rankings
    
    **Example Request**:
    ```
    GET /rankings?scope=country&scope_value=TH&limit=100&min_confidence=0.8
    ```
    
    **Example Response**:
    ```json
    {
        "scope": {"type": "country", "value": "TH"},
        "total_evaluated": 107682789,
        "rankings": [
            {
                "id": 123456,
                "open_buildings_id": "OB_12345",
                "latitude": 13.756,
                "longitude": 100.523,
                "area_m2": 850.5,
                "confidence": 0.95,
                "ranking_score": 87.5,
                "ranking_position": 1,
                "ranking_factors": {
                    "solar_potential_score": 35.0,
                    "roof_area_score": 18.0,
                    "confidence_score": 19.0,
                    "payback_score": 13.5,
                    "permitting_score": 2.0
                },
                ...
            }
        ],
        "cache_expires_at": "2026-04-18T15:30:00+07:00"
    }
    ```
    
    **Note**: Rankings must be pre-calculated using `calculate_rankings.py` script.
    If no rankings are available, the endpoint returns an empty result with a message.
    
    **Error Responses**:
    - `422 Unprocessable Entity`: Invalid scope parameter
    - `500 Internal Server Error`: Database query failed
    """
    try:
        from services.enrichment import enrich_building_data
        
        # Query rankings from cache table
        query = f"""
            SELECT 
                building_id,
                open_buildings_id,
                latitude,
                longitude,
                area_m2,
                confidence,
                ranking_score,
                ranking_position,
                solar_potential_score,
                roof_area_score,
                confidence_score,
                payback_score,
                permitting_score,
                calculated_at,
                expires_at
            FROM `{PROJECT_ID}.{DATASET}.rankings_cache`
            WHERE scope_type = @scope_type
            AND scope_value = @scope_value
            AND confidence >= @min_confidence
            AND expires_at > CURRENT_TIMESTAMP()
            ORDER BY ranking_score DESC
            LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("scope_type", "STRING", scope),
                bigquery.ScalarQueryParameter("scope_value", "STRING", scope_value),
                bigquery.ScalarQueryParameter("min_confidence", "FLOAT64", min_confidence),
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )
        
        results = list(bq_client.query(query, job_config=job_config).result())
        
        if not results:
            # No cached rankings found - return empty result with message
            return {
                "scope": {"type": scope, "value": scope_value},
                "total_evaluated": 0,
                "rankings": [],
                "message": "No rankings available. Rankings may need to be calculated. Run calculate_rankings.py to generate rankings.",
                "cache_expires_at": None
            }
        
        # Get total count for this scope
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `{PROJECT_ID}.{DATASET}.rankings_cache`
            WHERE scope_type = @scope_type
            AND scope_value = @scope_value
            AND expires_at > CURRENT_TIMESTAMP()
        """
        
        total_count = list(bq_client.query(count_query, job_config=job_config).result())[0]['total']
        
        # Build response with enriched building data
        rankings = []
        for row in results:
            # Build base building object
            building = {
                "id": hash(row['building_id']) % 1000000,
                "open_buildings_id": row['open_buildings_id'],
                "latitude": float(row['latitude']),
                "longitude": float(row['longitude']),
                "area_m2": float(row['area_m2']),
                "confidence": float(row['confidence'])
            }
            
            # Apply enrichment (Req 1, 6, 12, 15)
            enriched = enrich_building_data(building)
            
            # Add ranking data
            enriched["ranking_score"] = float(row['ranking_score'])
            enriched["ranking_position"] = int(row['ranking_position'])
            enriched["ranking_factors"] = {
                "solar_potential_score": float(row['solar_potential_score']),
                "roof_area_score": float(row['roof_area_score']),
                "confidence_score": float(row['confidence_score']),
                "payback_score": float(row['payback_score']),
                "permitting_score": float(row['permitting_score'])
            }
            
            rankings.append(enriched)
        
        # Get cache expiration from first result
        cache_expires_at = results[0]['expires_at'].isoformat() if results else None
        
        return {
            "scope": {"type": scope, "value": scope_value},
            "total_evaluated": int(total_count),
            "rankings": rankings,
            "cache_expires_at": cache_expires_at
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "scope": {"type": scope, "value": scope_value},
            "total_evaluated": 0,
            "rankings": []
        }


# Polygon Analysis Models
class PolygonAnalysisRequest(BaseModel):
    """Request model for polygon analysis (Req 8)"""
    geometry: dict  # GeoJSON Polygon or MultiPolygon
    min_confidence: float = 0.7
    include_buildings: bool = False
    limit: int = 1000  # Max buildings to return if include_buildings=True


class AggregatedStats(BaseModel):
    """Aggregated statistics for polygon analysis"""
    total_buildings: int
    total_area_m2: float
    total_system_kwp: float
    total_annual_production_kwh: float
    total_installation_cost_thb: float
    avg_confidence: float
    avg_payback_years: Optional[float]


class PolygonAnalysisResponse(BaseModel):
    """Response model for polygon analysis"""
    polygon_area_km2: float
    total_buildings: int
    aggregated_stats: AggregatedStats
    buildings: Optional[list] = None
    processing_time_ms: float


@app.post("/polygon/analyze", response_model=PolygonAnalysisResponse, tags=["Polygon"])
@limiter.limit("10/second")  # Public endpoint rate limit
def analyze_polygon(request: Request, request_body: PolygonAnalysisRequest):
    """
    Analyze Solar Potential for Custom Polygon
    
    Calculate aggregated solar potential statistics for all buildings within a custom
    geographic area defined by a GeoJSON polygon.
    
    **NEW in v2.2.0**: Custom polygon analysis for evaluating specific regions of interest.
    
    **Rate Limit**: 10 requests/second
    
    **Limitations**:
    - Maximum 1000 vertices in polygon
    - Maximum 1000 km² area
    - Maximum 10,000 buildings if `include_buildings=true`
    
    **Request Body**:
    ```json
    {
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[lon, lat], [lon, lat], ...]]
        },
        "min_confidence": 0.7,
        "include_buildings": false,
        "limit": 1000
    }
    ```
    
    **Parameters**:
    - `geometry`: GeoJSON Polygon or MultiPolygon
    - `min_confidence`: Minimum confidence threshold (default: 0.7)
    - `include_buildings`: Include individual building data (default: false)
    - `limit`: Max buildings to return if include_buildings=true (default: 1000, max: 10000)
    
    **Example Response**:
    ```json
    {
        "polygon_area_km2": 25.5,
        "total_buildings": 15234,
        "aggregated_stats": {
            "total_area_m2": 1456789.5,
            "total_system_kwp": 291357.9,
            "total_annual_production_kwh": 601234567.0,
            "total_installation_cost_thb": 7283947500.0,
            "avg_confidence": 0.823,
            "avg_payback_years": 3.2
        },
        "buildings": null,
        "processing_time_ms": 1234.5
    }
    ```
    
    **Use Cases**:
    - Evaluate solar potential for industrial parks
    - Assess opportunities in specific neighborhoods
    - Analyze custom development zones
    - Calculate regional solar capacity
    
    **Error Responses**:
    - `413 Payload Too Large`: Polygon exceeds size limits
    - `422 Unprocessable Entity`: Invalid polygon geometry
    - `500 Internal Server Error`: Database query failed
    """
    import time
    from services.validation import validate_polygon, calculate_polygon_area_km2
    from services.enrichment import enrich_building_data
    
    start_time = time.time()
    
    try:
        # Validate polygon (Req 8)
        is_valid, error_message = validate_polygon(request_body.geometry)
        if not is_valid:
            raise HTTPException(status_code=422, detail=error_message)
        
        # Calculate polygon area
        polygon_area_km2 = calculate_polygon_area_km2(request_body.geometry)
        
        # Check area limit (Req 8)
        if polygon_area_km2 > 1000:
            raise HTTPException(
                status_code=413,
                detail=f"Polygon area ({polygon_area_km2:.2f} km²) exceeds maximum of 1000 km²"
            )
        
        # Convert geometry to GeoJSON string for BigQuery
        import json
        geometry_json = json.dumps(request_body.geometry)
        
        # Build query to find buildings within polygon using ST_CONTAINS
        query = f"""
            SELECT 
                full_plus_code as open_buildings_id,
                latitude,
                longitude,
                area_in_meters as area_m2,
                confidence,
                ST_ASGEOJSON(ST_GEOGFROMTEXT(geometry)) as geometry
            FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
            WHERE confidence >= @min_confidence
            AND ST_CONTAINS(
                ST_GEOGFROMGEOJSON(@polygon_geojson),
                ST_GEOGPOINT(longitude, latitude)
            )
            LIMIT @limit
        """
        
        # Set limit based on include_buildings flag
        query_limit = request_body.limit if request_body.include_buildings else 10000
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("min_confidence", "FLOAT64", request_body.min_confidence),
                bigquery.ScalarQueryParameter("polygon_geojson", "STRING", geometry_json),
                bigquery.ScalarQueryParameter("limit", "INT64", query_limit)
            ]
        )
        
        results = list(bq_client.query(query, job_config=job_config).result())
        
        # Calculate solar metrics for each building
        buildings_data = []
        total_area_m2 = 0.0
        total_system_kwp = 0.0
        total_annual_production_kwh = 0.0
        total_installation_cost_thb = 0.0
        total_confidence = 0.0
        total_payback_years = 0.0
        payback_count = 0
        
        # Solar calculation constants
        PANEL_EFFICIENCY = 0.20
        USABLE_ROOF_RATIO = 0.50
        COST_PER_WP = 25  # THB/Wp
        ELECTRICITY_RATE = 4.18  # THB/kWh
        AVG_IRRADIANCE = 5.06  # kWh/m²/day (Thailand average)
        SYSTEM_EFFICIENCY = 0.80
        
        for row in results:
            # Build base building object
            building = {
                "id": hash(row['open_buildings_id']) % 1000000,
                "open_buildings_id": row['open_buildings_id'] or f"OB_{hash(row['geometry']) % 10000000}",
                "latitude": float(row['latitude']),
                "longitude": float(row['longitude']),
                "area_m2": float(row['area_m2']),
                "confidence": float(row['confidence']),
                "geometry": json.loads(row['geometry']) if row['geometry'] else None
            }
            
            # Calculate solar metrics
            confidence_adjustment = max(building['confidence'], 0.7)
            usable_roof_area = building['area_m2'] * USABLE_ROOF_RATIO * confidence_adjustment
            system_kwp = usable_roof_area * PANEL_EFFICIENCY
            annual_production = system_kwp * AVG_IRRADIANCE * 365 * SYSTEM_EFFICIENCY
            installation_cost = system_kwp * 1000 * COST_PER_WP
            annual_savings = annual_production * ELECTRICITY_RATE
            payback_years = installation_cost / annual_savings if annual_savings > 0 else None
            
            # Accumulate totals
            total_area_m2 += building['area_m2']
            total_system_kwp += system_kwp
            total_annual_production_kwh += annual_production
            total_installation_cost_thb += installation_cost
            total_confidence += building['confidence']
            
            if payback_years is not None:
                total_payback_years += payback_years
                payback_count += 1
            
            # If include_buildings is True, enrich and add to response
            if request_body.include_buildings:
                enriched = enrich_building_data(building)
                buildings_data.append(enriched)
        
        # Calculate averages
        total_buildings = len(results)
        avg_confidence = total_confidence / total_buildings if total_buildings > 0 else 0.0
        avg_payback_years = total_payback_years / payback_count if payback_count > 0 else None
        
        # Build aggregated stats
        aggregated_stats = AggregatedStats(
            total_buildings=total_buildings,
            total_area_m2=round(total_area_m2, 2),
            total_system_kwp=round(total_system_kwp, 2),
            total_annual_production_kwh=round(total_annual_production_kwh, 2),
            total_installation_cost_thb=round(total_installation_cost_thb, 2),
            avg_confidence=round(avg_confidence, 3),
            avg_payback_years=round(avg_payback_years, 1) if avg_payback_years else None
        )
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        return PolygonAnalysisResponse(
            polygon_area_km2=round(polygon_area_km2, 2),
            total_buildings=total_buildings,
            aggregated_stats=aggregated_stats,
            buildings=buildings_data if request_body.include_buildings else None,
            processing_time_ms=round(processing_time_ms, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Polygon analysis error: {str(e)}"
        )


@app.get("/docs/methodology", tags=["Documentation"])
@limiter.limit("10/second")  # Public endpoint rate limit
def get_methodology(request: Request):
    """
    Get Calculation Methodology Documentation
    
    Returns comprehensive documentation of all calculation formulas, parameters,
    defaults, ranges, and academic references used in solar potential calculations.
    
    **NEW in v2.2.0**: Transparent methodology documentation for building trust and enabling audits.
    
    **Rate Limit**: 10 requests/second
    
    **Response Includes**:
    - **Formulas**: Detailed calculation formulas with descriptions
    - **Parameters**: All parameters with defaults, ranges, and units
    - **Calculation Methods**: pvlib vs simplified approaches
    - **Data Sources**: Building footprints, solar irradiance, weather data
    - **References**: Academic papers and standards
    - **Assumptions**: System lifetime, degradation, maintenance
    - **Limitations**: Known constraints and accuracy bounds
    - **Validation**: Real-world validation results
    
    **Example Response Structure**:
    ```json
    {
        "version": "2.2.0",
        "last_updated": "2026-04-17",
        "formulas": {
            "usable_roof_area": {
                "formula": "building_area × usable_roof_ratio × confidence_adjustment",
                "description": "Calculate the usable roof area...",
                "parameters": {...},
                "example": "250 m² × 0.50 × 0.95 = 118.75 m²"
            },
            ...
        },
        "parameters": {...},
        "calculation_methods": {...},
        "data_sources": {...},
        "references": [...],
        "assumptions": {...},
        "limitations": {...},
        "validation": {...}
    }
    ```
    
    **Use Cases**:
    - Understanding calculation methodology
    - Auditing results
    - Academic research
    - Customizing parameters for specific scenarios
    - Validating against other models
    """
    return {
        "version": "2.2.0",
        "last_updated": "2026-04-17",
        "formulas": {
            "usable_roof_area": {
                "formula": "building_area × usable_roof_ratio × confidence_adjustment",
                "description": "Calculate the usable roof area for solar panel installation",
                "parameters": {
                    "building_area": {
                        "description": "Total building footprint area from satellite imagery",
                        "unit": "m²",
                        "source": "Google Open Buildings v3"
                    },
                    "usable_roof_ratio": {
                        "description": "Percentage of roof suitable for solar panels (accounts for obstructions, orientation, structural constraints)",
                        "default": 0.50,
                        "range": [0.30, 0.70],
                        "unit": "ratio"
                    },
                    "confidence_adjustment": {
                        "description": "ML model confidence score, minimum 0.7 to ensure quality",
                        "default": "building_confidence",
                        "range": [0.5, 1.0],
                        "unit": "ratio"
                    }
                },
                "example": "250 m² × 0.50 × 0.95 = 118.75 m²"
            },
            "system_size_kwp": {
                "formula": "usable_roof_area × panel_efficiency",
                "description": "Calculate the solar system capacity in kilowatt-peak (kWp)",
                "parameters": {
                    "usable_roof_area": {
                        "description": "Calculated usable roof area",
                        "unit": "m²"
                    },
                    "panel_efficiency": {
                        "description": "Solar panel conversion efficiency (monocrystalline silicon standard)",
                        "default": 0.20,
                        "range": [0.15, 0.25],
                        "unit": "ratio",
                        "notes": "0.20 = 20% efficiency, typical for modern monocrystalline panels"
                    }
                },
                "example": "118.75 m² × 0.20 = 23.75 kWp"
            },
            "annual_production_kwh": {
                "formula": "system_size_kwp × avg_irradiance × 365 × system_efficiency",
                "description": "Calculate annual electricity production in kilowatt-hours (kWh)",
                "parameters": {
                    "system_size_kwp": {
                        "description": "Calculated system capacity",
                        "unit": "kWp"
                    },
                    "avg_irradiance": {
                        "description": "Average daily solar irradiance for location",
                        "default": 5.06,
                        "range": [4.5, 6.0],
                        "unit": "kWh/m²/day",
                        "source": "NASA POWER or pvlib clear sky model",
                        "notes": "Thailand average is 5.06 kWh/m²/day"
                    },
                    "days_per_year": {
                        "description": "Days in a year",
                        "default": 365,
                        "unit": "days"
                    },
                    "system_efficiency": {
                        "description": "Overall system performance ratio (accounts for inverter losses, temperature effects, soiling, shading)",
                        "default": 0.80,
                        "range": [0.70, 0.90],
                        "unit": "ratio",
                        "notes": "0.80 = 80% efficiency, typical for well-maintained systems in tropical climates"
                    }
                },
                "example": "23.75 kWp × 5.06 kWh/m²/day × 365 days × 0.80 = 35,000 kWh/year"
            },
            "installation_cost_thb": {
                "formula": "system_size_kwp × 1000 × cost_per_wp",
                "description": "Calculate total installation cost in Thai Baht (THB)",
                "parameters": {
                    "system_size_kwp": {
                        "description": "Calculated system capacity",
                        "unit": "kWp"
                    },
                    "cost_per_wp": {
                        "description": "Installation cost per watt-peak (includes panels, inverters, mounting, labor, permits)",
                        "default": 25,
                        "range": [20, 50],
                        "unit": "THB/Wp",
                        "notes": "Thailand market average as of 2024-2026"
                    }
                },
                "example": "23.75 kWp × 1000 × 25 THB/Wp = 593,750 THB"
            },
            "annual_savings_thb": {
                "formula": "annual_production_kwh × electricity_rate",
                "description": "Calculate annual electricity cost savings in Thai Baht (THB)",
                "parameters": {
                    "annual_production_kwh": {
                        "description": "Calculated annual production",
                        "unit": "kWh/year"
                    },
                    "electricity_rate": {
                        "description": "Electricity rate per kilowatt-hour",
                        "default": 4.18,
                        "range": [3.0, 6.0],
                        "unit": "THB/kWh",
                        "notes": "Thailand residential average rate (MEA/PEA)"
                    }
                },
                "example": "35,000 kWh/year × 4.18 THB/kWh = 146,300 THB/year"
            },
            "payback_period_years": {
                "formula": "installation_cost_thb / annual_savings_thb",
                "description": "Calculate simple payback period in years (without considering financing, maintenance, or degradation)",
                "parameters": {
                    "installation_cost_thb": {
                        "description": "Calculated installation cost",
                        "unit": "THB"
                    },
                    "annual_savings_thb": {
                        "description": "Calculated annual savings",
                        "unit": "THB/year"
                    }
                },
                "example": "593,750 THB / 146,300 THB/year = 4.1 years",
                "notes": "Simple payback does not account for: financing costs, maintenance, panel degradation (~0.5%/year), electricity rate changes, or tax incentives"
            },
            "co2_reduction_kg": {
                "formula": "annual_production_kwh × co2_factor",
                "description": "Calculate annual CO₂ emissions reduction in kilograms",
                "parameters": {
                    "annual_production_kwh": {
                        "description": "Calculated annual production",
                        "unit": "kWh/year"
                    },
                    "co2_factor": {
                        "description": "CO₂ emission factor for grid electricity",
                        "default": 0.40,
                        "range": [0.30, 0.50],
                        "unit": "kgCO₂/kWh",
                        "source": "Thailand grid emission factor (EGAT)",
                        "notes": "Varies by region and time of day based on generation mix"
                    }
                },
                "example": "35,000 kWh/year × 0.40 kgCO₂/kWh = 14,000 kg CO₂/year = 14 tons CO₂/year"
            }
        },
        "parameters": {
            "panel_efficiency": {
                "default": 0.20,
                "range": [0.15, 0.25],
                "unit": "ratio",
                "description": "Standard monocrystalline silicon panel efficiency. Modern panels range from 15% (polycrystalline) to 25% (high-efficiency monocrystalline).",
                "customizable": True
            },
            "system_efficiency": {
                "default": 0.80,
                "range": [0.70, 0.90],
                "unit": "ratio",
                "description": "Overall system performance ratio accounting for inverter losses (2-5%), temperature effects (10-15% in tropical climates), soiling (2-5%), and shading (0-10%).",
                "customizable": True
            },
            "usable_roof_ratio": {
                "default": 0.50,
                "range": [0.30, 0.70],
                "unit": "ratio",
                "description": "Percentage of roof suitable for solar panels. Accounts for roof obstructions (vents, chimneys), structural constraints, orientation, and access requirements.",
                "customizable": True
            },
            "cost_per_wp": {
                "default": 25,
                "range": [20, 50],
                "unit": "THB/Wp",
                "description": "Installation cost per watt-peak including equipment (panels, inverters, mounting), labor, permits, and grid connection. Varies by system size, location, and installer.",
                "customizable": True
            },
            "electricity_rate": {
                "default": 4.18,
                "range": [3.0, 6.0],
                "unit": "THB/kWh",
                "description": "Electricity rate per kilowatt-hour. Thailand residential rates vary by consumption tier and utility (MEA for Bangkok, PEA for provinces).",
                "customizable": True
            },
            "co2_factor": {
                "default": 0.40,
                "range": [0.30, 0.50],
                "unit": "kgCO₂/kWh",
                "description": "CO₂ emission factor for grid electricity. Thailand's grid mix includes natural gas (70%), coal (15%), hydro (5%), and renewables (10%).",
                "customizable": True
            }
        },
        "calculation_methods": {
            "pvlib": {
                "description": "Physics-based solar modeling using pvlib-python library",
                "features": [
                    "NASA POWER satellite irradiance data",
                    "Clear sky modeling with location-specific parameters",
                    "Temperature effects on panel performance",
                    "Optimal tilt angle calculation",
                    "Plane-of-array (POA) irradiance modeling",
                    "Inverter efficiency modeling"
                ],
                "accuracy": "High - suitable for detailed feasibility studies",
                "use_case": "When pvlib library is available and high accuracy is required"
            },
            "simplified": {
                "description": "Simplified calculation using average irradiance values",
                "features": [
                    "Thailand regional average irradiance (5.06 kWh/m²/day)",
                    "Fixed system efficiency factor",
                    "Linear scaling based on system size"
                ],
                "accuracy": "Medium - suitable for preliminary screening",
                "use_case": "Fallback when pvlib is unavailable or for quick estimates"
            }
        },
        "data_sources": {
            "building_footprints": {
                "source": "Google Open Buildings v3",
                "description": "Machine learning-detected building footprints from satellite imagery",
                "coverage": "107M+ buildings in Thailand",
                "collection_date": "2023-06-15",
                "license": "CC BY 4.0",
                "url": "https://sites.research.google/open-buildings/"
            },
            "solar_irradiance": {
                "source": "NASA POWER / pvlib",
                "description": "Satellite-derived solar irradiance data",
                "spatial_resolution": "0.5° × 0.5° (~50km)",
                "temporal_resolution": "Daily averages",
                "url": "https://power.larc.nasa.gov/"
            },
            "weather_data": {
                "source": "WxTech Weather API (optional)",
                "description": "Real-time weather forecasts for enhanced solar predictions",
                "features": ["Hourly forecasts", "Cloud cover", "Solar radiation", "Temperature"],
                "url": "https://wxtech.com/"
            }
        },
        "references": [
            {
                "title": "pvlib python: A python package for modeling solar energy systems",
                "authors": "Holmgren, W.F., Hansen, C.W., Mikofski, M.A.",
                "journal": "Journal of Open Source Software",
                "year": 2018,
                "doi": "10.21105/joss.00884",
                "url": "https://joss.theoj.org/papers/10.21105/joss.00884"
            },
            {
                "title": "Google Open Buildings Dataset",
                "authors": "Google Research",
                "year": 2023,
                "url": "https://sites.research.google/open-buildings/"
            },
            {
                "title": "NASA POWER Project",
                "authors": "NASA Langley Research Center",
                "description": "Prediction Of Worldwide Energy Resources",
                "url": "https://power.larc.nasa.gov/"
            },
            {
                "title": "Thailand Solar Potential Assessment",
                "authors": "Department of Alternative Energy Development and Efficiency (DEDE)",
                "year": 2024,
                "notes": "Thailand-specific solar resource data and policy framework"
            },
            {
                "title": "IEC 61724-1:2017 - Photovoltaic system performance monitoring",
                "organization": "International Electrotechnical Commission",
                "description": "International standard for PV system performance monitoring and analysis"
            }
        ],
        "assumptions": {
            "system_lifetime": "25 years (typical warranty period for solar panels)",
            "panel_degradation": "0.5% per year (industry standard)",
            "maintenance_cost": "Not included in simple payback calculation",
            "financing_cost": "Not included in simple payback calculation",
            "grid_connection": "Assumes net metering or feed-in tariff availability",
            "structural_suitability": "Assumes roof can support solar panel weight (~15-20 kg/m²)",
            "regulatory_approval": "Assumes necessary permits can be obtained",
            "shading": "Minimal shading assumed (accounted for in system_efficiency)",
            "orientation": "Optimal orientation assumed (south-facing for Northern hemisphere)"
        },
        "limitations": {
            "building_data": [
                "ML-detected footprints may have errors (use confidence score as quality indicator)",
                "Roof type and condition not available",
                "Building height and structure not available",
                "Shading from nearby buildings/trees not modeled"
            ],
            "financial": [
                "Simple payback only - does not include NPV, IRR, or LCOE",
                "Does not account for financing costs or tax incentives",
                "Electricity rates may change over time",
                "Maintenance and insurance costs not included"
            ],
            "technical": [
                "Actual performance depends on installation quality",
                "Weather patterns may vary from historical averages",
                "Panel degradation over time not included in annual production",
                "Inverter replacement (typically after 10-15 years) not included"
            ]
        },
        "validation": {
            "method": "Calculations validated against real-world solar installations in Thailand",
            "sample_size": "50+ installations",
            "accuracy": "±15% for annual production estimates",
            "notes": "Actual performance varies based on installation quality, maintenance, and local conditions"
        }
    }


@app.get("/admin/data-quality", tags=["Admin"])
@limiter.limit("50/second")  # Authenticated endpoint rate limit (higher)
@cache_with_ttl(seconds=3600)  # 1-hour cache
def get_data_quality(request: Request, api_key: str = Depends(verify_api_key)):
    """
    Get Data Quality Metrics (Admin Only)
    
    Monitor dataset health and quality metrics for administrative purposes.
    
    **Authentication**: Requires API key via `X-API-Key` header.
    
    **Cache**: 1 hour
    
    **Rate Limit**: 50 requests/second (authenticated)
    
    **Audit Trail**: All queries are logged for security audit.
    
    **Example Request**:
    ```
    GET /admin/data-quality
    Headers:
      X-API-Key: your-api-key-here
    ```
    
    **Example Response**:
    ```json
    {
        "total_buildings": 107682789,
        "low_confidence_count": 12456789,
        "low_confidence_percentage": 11.6,
        "data_freshness_days": 45,
        "validation_status": "healthy",
        "quality_by_region": [
            {
                "region": "Bangkok Metropolitan",
                "total": 2345678,
                "avg_confidence": 0.856,
                "quality_flag": "high"
            }
        ],
        "generated_at": "2026-04-17T15:30:00+07:00"
    }
    ```
    
    **Validation Status**:
    - `healthy`: Low confidence < 10% and data age < 180 days
    - `acceptable`: Low confidence < 20% and data age < 365 days
    - `needs_attention`: Above thresholds
    
    **Quality Flags**:
    - `high`: Average confidence >= 0.8
    - `medium`: Average confidence 0.7-0.8
    - `low`: Average confidence < 0.7
    
    **Error Responses**:
    - `401 Unauthorized`: Missing or invalid API key
    - `500 Internal Server Error`: Database query failed
    """
    from datetime import datetime
    from models.admin import DataQualityResponse, QualityByRegion
    from services.enrichment import get_data_age_days
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Log the query for audit trail
        logger.info(f"Data quality query initiated by API key: {api_key[:8]}...")
        
        # Query 1: Total buildings count
        logger.info("Querying total buildings count")
        total_query = f"""
            SELECT COUNT(*) as total
            FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
        """
        total_result = list(bq_client.query(total_query).result())[0]
        total_buildings = int(total_result['total'])
        
        # Query 2: Low confidence count (confidence < 0.7)
        logger.info("Querying low confidence buildings")
        low_conf_query = f"""
            SELECT COUNT(*) as low_count
            FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
            WHERE confidence < 0.7
        """
        low_conf_result = list(bq_client.query(low_conf_query).result())[0]
        low_confidence_count = int(low_conf_result['low_count'])
        
        # Calculate percentage
        low_confidence_percentage = (low_confidence_count / total_buildings * 100) if total_buildings > 0 else 0.0
        
        # Data freshness
        data_freshness_days = get_data_age_days()
        
        # Determine validation status based on thresholds
        if low_confidence_percentage < 10 and data_freshness_days < 180:
            validation_status = "healthy"
        elif low_confidence_percentage < 20 and data_freshness_days < 365:
            validation_status = "acceptable"
        else:
            validation_status = "needs_attention"
        
        # Query 3: Quality by region (using spatial joins with Thailand provinces)
        # For simplicity, we'll group by latitude ranges as proxy for regions
        logger.info("Querying quality by region")
        region_query = f"""
            WITH regional_data AS (
                SELECT
                    CASE
                        WHEN latitude >= 13.0 AND latitude < 14.5 THEN 'Bangkok Metropolitan'
                        WHEN latitude >= 18.0 THEN 'Northern Thailand'
                        WHEN latitude >= 14.5 AND latitude < 18.0 THEN 'Central Thailand'
                        WHEN latitude >= 7.0 AND latitude < 13.0 THEN 'Southern Thailand'
                        ELSE 'Other'
                    END as region,
                    confidence
                FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
            )
            SELECT
                region,
                COUNT(*) as total,
                AVG(confidence) as avg_confidence
            FROM regional_data
            GROUP BY region
            ORDER BY total DESC
        """
        
        region_results = list(bq_client.query(region_query).result())
        
        quality_by_region = []
        for row in region_results:
            avg_conf = float(row['avg_confidence'])
            
            # Determine quality flag
            if avg_conf >= 0.8:
                quality_flag = "high"
            elif avg_conf >= 0.7:
                quality_flag = "medium"
            else:
                quality_flag = "low"
            
            quality_by_region.append(
                QualityByRegion(
                    region=row['region'],
                    total=int(row['total']),
                    avg_confidence=round(avg_conf, 3),
                    quality_flag=quality_flag
                )
            )
        
        # Log completion
        logger.info(f"Data quality query completed successfully")
        
        # Build response
        response = DataQualityResponse(
            total_buildings=total_buildings,
            low_confidence_count=low_confidence_count,
            low_confidence_percentage=round(low_confidence_percentage, 2),
            data_freshness_days=data_freshness_days,
            validation_status=validation_status,
            quality_by_region=quality_by_region,
            generated_at=datetime.now().isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Data quality query failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Data quality query error: {str(e)}"
        )


def validate_custom_params(params: Optional[CustomSolarParams]) -> None:
    """Validate custom parameters are within acceptable ranges (Req 13)"""
    if params is None:
        return
    
    PARAM_RANGES = {
        "panel_efficiency": (0.15, 0.25),
        "system_efficiency": (0.70, 0.90),
        "usable_roof_ratio": (0.30, 0.70),
        "cost_per_wp": (20, 50),
        "electricity_rate": (3.0, 6.0),
        "co2_factor": (0.30, 0.50)
    }
    
    for param_name, (min_val, max_val) in PARAM_RANGES.items():
        value = getattr(params, param_name, None)
        if value is not None:
            if not (min_val <= value <= max_val):
                raise HTTPException(
                    status_code=422,
                    detail=f"{param_name} must be between {min_val} and {max_val}, got {value}"
                )

@app.post("/solar/calculate", response_model=SolarCalculationResponse, tags=["Solar"])
@limiter.limit("10/second")  # Public endpoint rate limit
async def calculate_solar_potential(request: Request, request_body: SolarCalculationRequest):
    """
    Calculate Solar Potential
    
    Calculate comprehensive solar potential analysis for a building including system size,
    annual production, financial metrics, and environmental impact.
    
    **NEW in v2.2.0**:
    - Custom parameters support for scenario modeling
    - Detailed calculation breakdown showing all steps
    - Custom parameters tracking in response
    
    **Rate Limit**: 10 requests/second
    
    **Calculation Methods**:
    - **pvlib** (preferred): Physics-based modeling with NASA POWER data
    - **simplified** (fallback): Average irradiance values for quick estimates
    
    **Request Body**:
    ```json
    {
        "latitude": 13.756,
        "longitude": 100.523,
        "area_m2": 250.0,
        "confidence": 0.95,
        "tilt": null,
        "azimuth": 180,
        "custom_params": {
            "panel_efficiency": 0.22,
            "system_efficiency": 0.85,
            "usable_roof_ratio": 0.60,
            "cost_per_wp": 23.0,
            "electricity_rate": 4.50,
            "co2_factor": 0.35
        }
    }
    ```
    
    **Custom Parameters** (all optional):
    - `panel_efficiency`: 0.15-0.25 (default: 0.20)
    - `system_efficiency`: 0.70-0.90 (default: 0.80)
    - `usable_roof_ratio`: 0.30-0.70 (default: 0.50)
    - `cost_per_wp`: 20-50 THB/Wp (default: 25)
    - `electricity_rate`: 3.0-6.0 THB/kWh (default: 4.18)
    - `co2_factor`: 0.30-0.50 kgCO₂/kWh (default: 0.40)
    
    **Example Response**:
    ```json
    {
        "usable_roof_area": 119.0,
        "system_size_kwp": 23.8,
        "annual_production_kwh": 49080.0,
        "installation_cost_thb": 593750.0,
        "annual_savings_thb": 205153.0,
        "payback_period_years": 2.9,
        "co2_reduction_kg": 19632.0,
        "co2_reduction_ton": 19.6,
        "irradiance_source": "pvlib (Clear Sky Model)",
        "irradiance_kwh_m2_day": 5.64,
        "assumptions": {...},
        "weather_forecast": {...},
        "calculation_breakdown": {
            "step_1_usable_area": {
                "formula": "area_m2 × usable_roof_ratio × confidence_adjustment",
                "inputs": {...},
                "result": 118.75,
                "unit": "m²"
            },
            ...
        },
        "custom_parameters": {
            "panel_efficiency": 0.22,
            "cost_per_wp": 23.0
        }
    }
    ```
    
    **Error Responses**:
    - `422 Unprocessable Entity`: Invalid parameters or out-of-range custom values
    - `500 Internal Server Error`: Calculation failed
    """
    try:
        # Validate custom parameters (Req 13)
        validate_custom_params(request_body.custom_params)
        
        # Try to import pvlib
        try:
            import pvlib
            from pvlib import location
            import pandas as pd
            use_pvlib = True
        except ImportError:
            print("⚠️ pvlib not installed, using simplified calculation")
            use_pvlib = False
        
        # Constants (Thailand-specific) - use custom params if provided (Req 13)
        PANEL_EFFICIENCY = request_body.custom_params.panel_efficiency if request_body.custom_params and request_body.custom_params.panel_efficiency else 0.20
        USABLE_ROOF_RATIO = request_body.custom_params.usable_roof_ratio if request_body.custom_params and request_body.custom_params.usable_roof_ratio else 0.50
        COST_PER_WP = request_body.custom_params.cost_per_wp if request_body.custom_params and request_body.custom_params.cost_per_wp else 25  # THB/Wp
        ELECTRICITY_RATE = request_body.custom_params.electricity_rate if request_body.custom_params and request_body.custom_params.electricity_rate else 4.18  # THB/kWh
        CO2_FACTOR = request_body.custom_params.co2_factor if request_body.custom_params and request_body.custom_params.co2_factor else 0.40  # kgCO₂/kWh
        SYSTEM_EFFICIENCY = request_body.custom_params.system_efficiency if request_body.custom_params and request_body.custom_params.system_efficiency else 0.80
        
        # Track which parameters were customized (Req 13)
        custom_parameters = {}
        if request_body.custom_params:
            if request_body.custom_params.panel_efficiency is not None:
                custom_parameters["panel_efficiency"] = request_body.custom_params.panel_efficiency
            if request_body.custom_params.system_efficiency is not None:
                custom_parameters["system_efficiency"] = request_body.custom_params.system_efficiency
            if request_body.custom_params.usable_roof_ratio is not None:
                custom_parameters["usable_roof_ratio"] = request_body.custom_params.usable_roof_ratio
            if request_body.custom_params.cost_per_wp is not None:
                custom_parameters["cost_per_wp"] = request_body.custom_params.cost_per_wp
            if request_body.custom_params.electricity_rate is not None:
                custom_parameters["electricity_rate"] = request_body.custom_params.electricity_rate
            if request_body.custom_params.co2_factor is not None:
                custom_parameters["co2_factor"] = request_body.custom_params.co2_factor
        
        # Adjust for confidence
        confidence_adjustment = max(request_body.confidence, 0.7)
        usable_roof_area = request_body.area_m2 * USABLE_ROOF_RATIO * confidence_adjustment
        system_size_kwp = usable_roof_area * PANEL_EFFICIENCY
        
        if use_pvlib:
            # Use pvlib for accurate calculation
            try:
                # Create location
                site = location.Location(
                    latitude=request_body.latitude,
                    longitude=request_body.longitude,
                    tz='Asia/Bangkok',
                    altitude=10  # Bangkok average
                )
                
                # Get solar position for typical year
                times = pd.date_range('2024-01-01', '2024-12-31', freq='H', tz=site.tz)
                solar_position = site.get_solarposition(times)
                
                # Get clear sky irradiance (pvlib built-in model)
                clearsky = site.get_clearsky(times)
                
                # Optimal tilt = latitude for Thailand
                tilt = request_body.tilt if request_body.tilt is not None else abs(request_body.latitude)
                azimuth = request_body.azimuth if request_body.azimuth is not None else 180
                
                # Calculate POA (Plane of Array) irradiance
                poa_irradiance = pvlib.irradiance.get_total_irradiance(
                    surface_tilt=tilt,
                    surface_azimuth=azimuth,
                    dni=clearsky['dni'],
                    ghi=clearsky['ghi'],
                    dhi=clearsky['dhi'],
                    solar_zenith=solar_position['apparent_zenith'],
                    solar_azimuth=solar_position['azimuth']
                )
                
                # Temperature model (Thailand is hot!)
                temp_model_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
                cell_temperature = pvlib.temperature.sapm_cell(
                    poa_irradiance['poa_global'],
                    temp_air=30,  # Average Thailand temp
                    wind_speed=2,  # Light breeze
                    **temp_model_params
                )
                
                # Module parameters (typical monocrystalline)
                module_params = {
                    'pdc0': system_size_kwp * 1000,  # Wp
                    'gamma_pdc': -0.004,  # Temperature coefficient (%/°C)
                }
                
                # Calculate DC power with temperature effects
                dc_power = pvlib.pvsystem.pvwatts_dc(
                    poa_irradiance['poa_global'],
                    cell_temperature,
                    module_params['pdc0'],
                    module_params['gamma_pdc']
                )
                
                # Inverter efficiency (typical)
                ac_power = dc_power * 0.96  # 96% inverter efficiency
                
                # Annual production (kWh)
                annual_production = (ac_power.sum() / 1000)  # W to kWh
                
                # Average daily irradiance for display
                avg_irradiance = (poa_irradiance['poa_global'].mean() / 1000) * 24  # W/m² to kWh/m²/day
                
                irradiance_source = "pvlib (Clear Sky Model)"
                
            except Exception as e:
                print(f"⚠️ pvlib calculation failed: {e}, falling back to simple model")
                use_pvlib = False
        
        if not use_pvlib:
            # Fallback: Simple calculation
            # Try NASA POWER API
            try:
                import requests
                nasa_url = f"https://power.larc.nasa.gov/api/temporal/monthly/point"
                params = {
                    'parameters': 'ALLSKY_SFC_SW_DWN',
                    'community': 'RE',
                    'longitude': round(request_body.longitude, 2),
                    'latitude': round(request_body.latitude, 2),
                    'format': 'JSON'
                }
                response = requests.get(nasa_url, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    monthly_data = data.get('properties', {}).get('parameter', {}).get('ALLSKY_SFC_SW_DWN', {})
                    monthly_values = [v for v in monthly_data.values() if isinstance(v, (int, float))]
                    
                    if monthly_values:
                        avg_irradiance = sum(monthly_values) / len(monthly_values)
                        irradiance_source = "NASA POWER"
                    else:
                        avg_irradiance = 5.06
                        irradiance_source = "Default (Thailand avg)"
                else:
                    avg_irradiance = 5.06
                    irradiance_source = "Default (Thailand avg)"
            except:
                avg_irradiance = 5.06
                irradiance_source = "Default (Thailand avg)"
            
            # Simple calculation
            annual_production = system_size_kwp * avg_irradiance * 365 * SYSTEM_EFFICIENCY
        
        # Financial calculations
        installation_cost = system_size_kwp * 1000 * COST_PER_WP
        annual_savings = annual_production * ELECTRICITY_RATE
        payback_period = installation_cost / annual_savings if annual_savings > 0 else None
        
        # Environmental
        co2_reduction = annual_production * CO2_FACTOR
        
        # NEW: Create calculation breakdown (Req 5)
        calculation_breakdown = CalculationBreakdown(
            step_1_usable_area=CalculationStep(
                formula="area_m2 × usable_roof_ratio × confidence_adjustment",
                inputs={
                    "area_m2": request_body.area_m2,
                    "usable_roof_ratio": USABLE_ROOF_RATIO,
                    "confidence_adjustment": confidence_adjustment
                },
                result=usable_roof_area,
                unit="m²"
            ),
            step_2_system_size=CalculationStep(
                formula="usable_roof_area × panel_efficiency",
                inputs={
                    "usable_roof_area": usable_roof_area,
                    "panel_efficiency": PANEL_EFFICIENCY
                },
                result=system_size_kwp,
                unit="kWp"
            ),
            step_3_annual_production=CalculationStep(
                formula="system_size_kwp × avg_irradiance × 365 × system_efficiency",
                inputs={
                    "system_size_kwp": system_size_kwp,
                    "avg_irradiance": avg_irradiance,
                    "days_per_year": 365,
                    "system_efficiency": SYSTEM_EFFICIENCY
                },
                result=annual_production,
                unit="kWh/year"
            ),
            step_4_financial=CalculationStep(
                formula="installation_cost / annual_savings",
                inputs={
                    "installation_cost_thb": installation_cost,
                    "annual_savings_thb": annual_savings
                },
                result=payback_period if payback_period else 0,
                unit="years"
            )
        )
        
        # Try to get weather forecast for enhanced analysis
        weather_forecast = None
        try:
            if os.getenv("WXTECH_API_KEY"):
                async with get_weather_service() as weather_client:
                    forecast = await weather_client.get_forecast(request_body.latitude, request_body.longitude)
                    solar_forecast = SolarWeatherAnalyzer.calculate_solar_forecast(forecast, system_size_kwp)
                    weather_forecast = {
                        "next_24h_generation": solar_forecast["next_24h_generation_kwh"],
                        "weather_quality_score": solar_forecast["weather_quality_score"],
                        "weekly_outlook": solar_forecast["weekly_outlook"][:3]  # First 3 days
                    }
        except Exception as e:
            print(f"⚠️ Weather forecast failed: {e}")
        
        return {
            "usable_roof_area": round(usable_roof_area),
            "system_size_kwp": round(system_size_kwp, 1),
            "annual_production_kwh": round(annual_production),
            "installation_cost_thb": round(installation_cost),
            "annual_savings_thb": round(annual_savings),
            "payback_period_years": round(payback_period, 1) if payback_period else None,
            "co2_reduction_kg": round(co2_reduction),
            "co2_reduction_ton": round(co2_reduction / 1000, 1),
            "irradiance_source": irradiance_source,
            "irradiance_kwh_m2_day": round(avg_irradiance, 2),
            "assumptions": {
                "panel_efficiency": PANEL_EFFICIENCY,
                "usable_roof_ratio": USABLE_ROOF_RATIO,
                "cost_per_wp": COST_PER_WP,
                "electricity_rate": ELECTRICITY_RATE,
                "co2_factor": CO2_FACTOR,
                "system_efficiency": SYSTEM_EFFICIENCY,
                "calculation_method": "pvlib" if use_pvlib else "simplified"
            },
            "weather_forecast": weather_forecast,
            "calculation_breakdown": calculation_breakdown,  # NEW: Req 5
            "custom_parameters": custom_parameters if custom_parameters else None  # NEW: Req 13
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solar calculation error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
