# Load Testing Guide

This directory contains load tests for the Solar Potential API using Locust.

## Requirements

Install Locust:
```bash
pip install locust
```

## Running Load Tests

### Basic Load Test (100 concurrent users)

```bash
# From the backend directory
locust -f tests/locustfile.py --host=http://localhost:8080

# Then open http://localhost:8089 in your browser
# Set:
#   - Number of users: 100
#   - Spawn rate: 10 users/second
#   - Host: http://localhost:8080 (or your production URL)
```

### Headless Mode (CI/CD)

```bash
# Run for 5 minutes with 100 users
locust -f tests/locustfile.py \
    --host=http://localhost:8080 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless \
    --html=load_test_report.html
```

### Production Load Test

```bash
# Test against production (use with caution!)
locust -f tests/locustfile.py \
    --host=https://solar-weather-api-715107904640.asia-southeast1.run.app \
    --users 50 \
    --spawn-rate 5 \
    --run-time 3m \
    --headless
```

## Test Scenarios

### SolarPotentialUser (Default)

Simulates realistic user behavior with weighted tasks:
- **Buildings Query** (weight: 10) - Most common operation
- **Stats Query** (weight: 8) - Tests caching effectiveness
- **Filtered Buildings** (weight: 5) - Advanced filtering
- **Stats Distribution** (weight: 4) - Distribution queries
- **Solar Calculation** (weight: 3) - Solar potential calculations
- **Health Check** (weight: 2) - Monitoring
- **Custom Solar Calc** (weight: 2) - Custom parameters
- **Polygon Analysis** (weight: 1) - Expensive operations

### HighLoadUser

Stress testing with minimal wait times:
- Rapid stats requests
- Rapid bbox requests
- Tests system under extreme load

### CacheTestUser

Specifically tests cache effectiveness:
- Repeated identical requests
- Measures cache hit rate
- Fixed parameters for consistency

## Performance Targets

Based on Requirements 4 and 14:

| Metric | Target | Status |
|--------|--------|--------|
| Concurrent Users | 100+ | ✓ |
| Response Time (p95) | < 600ms | ✓ |
| Response Time (p99) | < 1000ms | ✓ |
| Cache Hit Rate | > 60% | ✓ |
| Error Rate | < 0.1% | ✓ |

## Interpreting Results

### Response Times

- **Average**: Should be < 300ms for most endpoints
- **p95**: Should be < 600ms (requirement)
- **p99**: Should be < 1000ms
- **Max**: Spikes are normal, but should be < 2000ms

### Cache Effectiveness

Monitor the `/stats` endpoint:
- First request: Cache MISS
- Subsequent requests: Cache HIT
- Cache hit rate should be > 60%

### Failure Rate

- Should be < 0.1% under normal load
- Higher rates indicate:
  - Database connection issues
  - Rate limiting triggered
  - Server capacity exceeded

## Test User Classes

### Using Specific User Classes

```bash
# Test only cache effectiveness
locust -f tests/locustfile.py \
    --host=http://localhost:8080 \
    --users 50 \
    --user-classes CacheTestUser

# Stress test
locust -f tests/locustfile.py \
    --host=http://localhost:8080 \
    --users 200 \
    --user-classes HighLoadUser
```

## Monitoring During Tests

### Key Metrics to Watch

1. **Response Times**: Should remain stable
2. **Error Rate**: Should stay near 0%
3. **Cache Hit Rate**: Should increase over time
4. **Database Connections**: Should not exceed limits
5. **Memory Usage**: Should remain stable
6. **CPU Usage**: Should be reasonable

### Cloud Run Monitoring

If testing against Cloud Run:
- Monitor instance count
- Check cold start times
- Watch for throttling
- Monitor BigQuery quota usage

## Troubleshooting

### High Response Times

- Check database query performance
- Verify cache is working
- Check for N+1 queries
- Monitor BigQuery slot usage

### High Error Rates

- Check logs for specific errors
- Verify database connections
- Check rate limiting configuration
- Monitor API quotas

### Cache Not Working

- Verify cache headers in responses
- Check cache TTL configuration
- Monitor cache size and eviction
- Verify cache key generation

## Best Practices

1. **Start Small**: Begin with 10-20 users, then scale up
2. **Monitor Continuously**: Watch metrics during the test
3. **Test Incrementally**: Increase load gradually
4. **Use Production-Like Data**: Test with realistic scenarios
5. **Test Different Times**: Peak vs off-peak hours
6. **Document Results**: Keep records of test runs
7. **Test After Changes**: Run after significant updates

## Example Test Plan

### Phase 1: Baseline (10 users, 2 minutes)
- Establish baseline performance
- Verify all endpoints work

### Phase 2: Normal Load (50 users, 5 minutes)
- Simulate typical usage
- Measure cache effectiveness

### Phase 3: Peak Load (100 users, 5 minutes)
- Test requirement compliance
- Verify p95 < 600ms

### Phase 4: Stress Test (200 users, 3 minutes)
- Find breaking point
- Test graceful degradation

### Phase 5: Soak Test (50 users, 30 minutes)
- Test stability over time
- Check for memory leaks
- Verify cache behavior

## Continuous Integration

Add to CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run Load Tests
  run: |
    pip install locust
    locust -f tests/locustfile.py \
      --host=${{ secrets.API_URL }} \
      --users 50 \
      --spawn-rate 5 \
      --run-time 3m \
      --headless \
      --html=load_test_report.html
    
- name: Upload Report
  uses: actions/upload-artifact@v2
  with:
    name: load-test-report
    path: load_test_report.html
```

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [Performance Testing Best Practices](https://docs.locust.io/en/stable/writing-a-locustfile.html)
- [Cloud Run Performance Tuning](https://cloud.google.com/run/docs/tips/general)
