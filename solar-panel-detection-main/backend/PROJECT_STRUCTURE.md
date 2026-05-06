# Backend Project Structure

This document describes the organization of the Solar Potential Platform backend codebase.

## Directory Structure

```
backend/
├── api_bigquery.py          # Main FastAPI application (entry point)
├── weather_service.py       # Weather integration service
├── requirements.txt         # Python dependencies
├── pytest.ini              # Pytest configuration
├── .env.example            # Environment variables template
├── Dockerfile.bigquery     # Docker configuration
│
├── models/                 # Pydantic data models
│   ├── __init__.py
│   ├── building.py         # Building response models
│   ├── solar.py           # Solar calculation models
│   ├── ranking.py         # Ranking system models
│   ├── polygon.py         # Polygon analysis models
│   ├── admin.py           # Admin/data quality models
│   └── common.py          # Common models (errors, health)
│
├── services/              # Business logic layer
│   ├── __init__.py
│   ├── enrichment.py      # Data enrichment functions
│   ├── ranking.py         # Ranking algorithm
│   └── validation.py      # Input validation
│
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── cache.py          # Caching with TTL
│   ├── logging.py        # Logging setup
│   └── request_id.py     # Request ID generation
│
├── migrations/            # BigQuery SQL migrations
│   ├── README.md
│   ├── 001_create_rankings_cache.sql
│   ├── 002_create_stats_summary_view.sql
│   ├── 003_create_permitting_data.sql
│   └── 004_create_indexes.sql
│
└── tests/                # Test suite
    ├── __init__.py
    ├── conftest.py       # Pytest fixtures
    ├── test_enrichment.py
    ├── test_validation.py
    ├── test_endpoints.py
    └── README.md

```

## Module Responsibilities

### Main Application (`api_bigquery.py`)
- FastAPI application setup
- Endpoint definitions
- CORS configuration
- Request/response handling
- Middleware integration

### Models (`models/`)
Pydantic models for request/response validation and serialization:
- **building.py**: Building data, provenance, accuracy
- **solar.py**: Solar calculations, custom parameters
- **ranking.py**: Ranking scores and factors
- **polygon.py**: Polygon analysis requests/responses
- **admin.py**: Data quality metrics
- **common.py**: Error responses, health checks

### Services (`services/`)
Business logic separated from API layer:
- **enrichment.py**: Add computed fields to building data
- **ranking.py**: Calculate ranking scores
- **validation.py**: Validate user inputs

### Utils (`utils/`)
Reusable utility functions:
- **cache.py**: In-memory caching with TTL
- **logging.py**: Logging configuration
- **request_id.py**: Unique request ID generation

### Migrations (`migrations/`)
BigQuery schema changes:
- SQL files for creating tables, views, indexes
- README with execution instructions
- Idempotent migrations (safe to run multiple times)

### Tests (`tests/`)
Comprehensive test suite:
- Unit tests for services and utilities
- Integration tests for API endpoints
- Load tests for performance validation
- Fixtures for common test data

## Design Principles

### 1. Separation of Concerns
- API layer (FastAPI) handles HTTP
- Services layer handles business logic
- Models layer handles data validation
- Utils layer provides shared functionality

### 2. Testability
- Business logic in services (easy to unit test)
- Dependency injection for external services
- Fixtures for common test scenarios

### 3. Maintainability
- Clear module boundaries
- Comprehensive documentation
- Type hints throughout
- Consistent naming conventions

### 4. Performance
- Caching at multiple levels
- Query optimization in services
- Async/await for I/O operations
- Connection pooling for BigQuery

## Adding New Features

### 1. Add a new endpoint
1. Define request/response models in `models/`
2. Add business logic in `services/`
3. Create endpoint in `api_bigquery.py`
4. Add tests in `tests/`

### 2. Add a new service
1. Create service file in `services/`
2. Export from `services/__init__.py`
3. Add unit tests in `tests/`
4. Use in endpoints as needed

### 3. Add a new model
1. Create model in appropriate `models/` file
2. Export from `models/__init__.py`
3. Use in endpoints and services

## Code Style

- Follow PEP 8 style guide
- Use type hints for all functions
- Document all public functions with docstrings
- Keep functions focused and small
- Use meaningful variable names

## Dependencies

See `requirements.txt` for full list. Key dependencies:
- **FastAPI**: Web framework
- **Pydantic**: Data validation
- **BigQuery**: Database client
- **pytest**: Testing framework
- **cachetools**: Caching utilities
- **slowapi**: Rate limiting

## Environment Variables

See `.env.example` for required environment variables:
- `GCP_PROJECT`: Google Cloud project ID
- `WXTECH_API_KEY`: Weather API key (optional)
- `ADMIN_API_KEYS`: Admin authentication keys
- `PORT`: Server port (default: 8080)

## Running the Application

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python api_bigquery.py
```

### Production
```bash
# Build Docker image
docker build -f Dockerfile.bigquery -t solar-api .

# Run container
docker run -p 8080:8080 --env-file .env solar-api
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test category
pytest -m unit
```

## Documentation

- API documentation: `/docs` (Swagger UI)
- Alternative docs: `/redoc` (ReDoc)
- OpenAPI spec: `/openapi.json`
- Backend guide: `BACKEND.md`
- Migration guide: `migrations/README.md`
- Test guide: `tests/README.md`

## Version History

- **v2.2.0**: Platform improvements (current)
  - Enhanced data transparency
  - New ranking system
  - Polygon analysis
  - Advanced filtering
  - Performance optimizations

- **v2.1.0**: Weather integration
  - Real-time weather data
  - Solar forecasting
  - Weather-enhanced calculations

- **v2.0.0**: BigQuery migration
  - 107M+ buildings
  - Improved performance
  - Spatial queries

## Support

- GitHub: https://github.com/EayonTinthai/gis-solar-potential-cpe
- Issues: https://github.com/EayonTinthai/gis-solar-potential-cpe/issues
- Documentation: See `BACKEND.md`
