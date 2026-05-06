# Backend Tests

This directory contains tests for the Solar Potential Platform backend API.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_enrichment.py       # Unit tests for enrichment functions
├── test_validation.py       # Unit tests for validation logic
├── test_endpoints.py        # Integration tests for API endpoints
└── locustfile.py           # Load tests (to be added in task 15.4)
```

## Running Tests

### Run all tests
```bash
cd solar-panel-detection-main/backend
pytest
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_enrichment.py
```

### Run with verbose output
```bash
pytest -v
```

## Test Categories

### Unit Tests
- `test_enrichment.py`: Tests for data enrichment functions
- `test_validation.py`: Tests for input validation logic

### Integration Tests
- `test_endpoints.py`: Tests for API endpoints with real requests

### Load Tests
- `locustfile.py`: Performance and load testing scenarios

## Writing Tests

### Unit Test Example
```python
def test_calculate_accuracy_level():
    from services.enrichment import calculate_accuracy_level
    
    level, factors = calculate_accuracy_level(0.85, 200)
    assert level == "high"
    assert factors["confidence_score"] == 0.85
```

### Integration Test Example
```python
def test_stats_endpoint(test_client):
    response = test_client.get("/stats")
    assert response.status_code == 200
    assert "total_buildings" in response.json()
```

## Test Coverage Goals

- Unit tests: >80% coverage
- Integration tests: All endpoints covered
- Load tests: 100 concurrent users, <600ms p95 response time

## CI/CD Integration

Tests are automatically run on:
- Pull requests
- Commits to main branch
- Before deployment

## Notes

- Tests use pytest fixtures for common setup
- Integration tests may require BigQuery access
- Load tests should be run against staging environment
- Mock external services (weather API) in unit tests
