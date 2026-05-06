"""
Verify Cache Effectiveness
Task 19.2 - Verify caching effectiveness

This script tests the caching system to ensure:
1. Cache hit rates are acceptable (> 60%)
2. TTL values are appropriate
3. Cache headers are correct
4. Cache eviction works properly

Usage:
    python verify_cache_effectiveness.py [--api-url http://localhost:8080]
"""

import requests
import time
import argparse
from datetime import datetime
from typing import Dict, List, Tuple
import statistics


class CacheEffectivenessTest:
    """
    Test suite for cache effectiveness
    
    Tests:
    1. Cache hit/miss tracking
    2. Cache header verification
    3. TTL verification
    4. Cache eviction
    5. Performance improvement from caching
    """
    
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/')
        self.results = []
    
    def test_cache_headers(self) -> bool:
        """
        Test 1: Verify cache headers are present and correct
        
        Expected headers:
        - X-Cache-Status: HIT or MISS
        - Cache-Control: public, max-age=<seconds>
        - X-Request-ID: <uuid>
        - X-Response-Time: <ms>ms
        """
        print(f"\n{'='*80}")
        print(f"TEST 1: CACHE HEADERS")
        print(f"{'='*80}")
        
        # Test endpoints that should have caching
        cached_endpoints = [
            ("/stats", 86400),  # 24 hours
            ("/stats/distribution", 86400),  # 24 hours
            ("/buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=10", 3600),  # 1 hour
        ]
        
        all_passed = True
        
        for endpoint, expected_ttl in cached_endpoints:
            print(f"\nTesting: {endpoint}")
            
            try:
                # First request (should be MISS)
                response1 = requests.get(f"{self.api_url}{endpoint}")
                
                # Check status code
                if response1.status_code != 200:
                    print(f"  ✗ Status code: {response1.status_code} (expected 200)")
                    all_passed = False
                    continue
                
                # Check X-Cache-Status header
                cache_status1 = response1.headers.get('X-Cache-Status')
                if not cache_status1:
                    print(f"  ✗ Missing X-Cache-Status header")
                    all_passed = False
                else:
                    print(f"  ✓ X-Cache-Status: {cache_status1}")
                
                # Check Cache-Control header
                cache_control = response1.headers.get('Cache-Control')
                if not cache_control:
                    print(f"  ⚠ Missing Cache-Control header")
                else:
                    print(f"  ✓ Cache-Control: {cache_control}")
                    
                    # Verify max-age is reasonable
                    if 'max-age=' in cache_control:
                        max_age = int(cache_control.split('max-age=')[1].split(',')[0])
                        if max_age > 0:
                            print(f"  ✓ max-age: {max_age}s (expected ~{expected_ttl}s)")
                        else:
                            print(f"  ⚠ max-age is 0")
                
                # Check X-Request-ID header
                request_id = response1.headers.get('X-Request-ID')
                if not request_id:
                    print(f"  ⚠ Missing X-Request-ID header")
                else:
                    print(f"  ✓ X-Request-ID: {request_id}")
                
                # Check X-Response-Time header
                response_time = response1.headers.get('X-Response-Time')
                if not response_time:
                    print(f"  ⚠ Missing X-Response-Time header")
                else:
                    print(f"  ✓ X-Response-Time: {response_time}")
                
                # Second request (should be HIT)
                time.sleep(0.1)  # Small delay
                response2 = requests.get(f"{self.api_url}{endpoint}")
                cache_status2 = response2.headers.get('X-Cache-Status')
                
                if cache_status2 == 'HIT':
                    print(f"  ✓ Second request: Cache HIT (caching working)")
                elif cache_status2 == 'MISS':
                    print(f"  ⚠ Second request: Cache MISS (caching may not be working)")
                else:
                    print(f"  ⚠ Second request: No cache status")
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_cache_hit_rate(self, num_requests: int = 100) -> Tuple[float, Dict]:
        """
        Test 2: Measure cache hit rate
        
        Makes repeated requests to cached endpoints and measures hit rate.
        Target: > 60% hit rate
        """
        print(f"\n{'='*80}")
        print(f"TEST 2: CACHE HIT RATE")
        print(f"{'='*80}")
        print(f"Making {num_requests} requests to /stats endpoint...")
        
        hits = 0
        misses = 0
        errors = 0
        response_times = []
        
        for i in range(num_requests):
            try:
                start_time = time.time()
                response = requests.get(f"{self.api_url}/stats")
                duration = (time.time() - start_time) * 1000  # ms
                
                if response.status_code == 200:
                    cache_status = response.headers.get('X-Cache-Status', 'UNKNOWN')
                    
                    if cache_status == 'HIT':
                        hits += 1
                    elif cache_status == 'MISS':
                        misses += 1
                    
                    response_times.append(duration)
                else:
                    errors += 1
                
                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i + 1}/{num_requests} requests")
                
            except Exception as e:
                errors += 1
        
        # Calculate statistics
        total_requests = hits + misses + errors
        hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            "total_requests": total_requests,
            "hits": hits,
            "misses": misses,
            "errors": errors,
            "hit_rate_percent": hit_rate,
            "avg_response_time_ms": statistics.mean(response_times) if response_times else 0,
            "median_response_time_ms": statistics.median(response_times) if response_times else 0,
            "p95_response_time_ms": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0
        }
        
        # Print results
        print(f"\n{'='*80}")
        print(f"CACHE HIT RATE RESULTS")
        print(f"{'='*80}")
        print(f"Total requests: {stats['total_requests']}")
        print(f"Cache hits: {stats['hits']}")
        print(f"Cache misses: {stats['misses']}")
        print(f"Errors: {stats['errors']}")
        print(f"Hit rate: {stats['hit_rate_percent']:.1f}%")
        print(f"\nResponse times:")
        print(f"  Average: {stats['avg_response_time_ms']:.2f}ms")
        print(f"  Median: {stats['median_response_time_ms']:.2f}ms")
        print(f"  p95: {stats['p95_response_time_ms']:.2f}ms")
        
        # Check if hit rate meets target
        target_hit_rate = 60.0
        if stats['hit_rate_percent'] >= target_hit_rate:
            print(f"\n✓ Hit rate {stats['hit_rate_percent']:.1f}% meets target (>= {target_hit_rate}%)")
        else:
            print(f"\n⚠ Hit rate {stats['hit_rate_percent']:.1f}% below target (>= {target_hit_rate}%)")
        
        return hit_rate, stats
    
    def test_cache_performance_improvement(self) -> Dict:
        """
        Test 3: Measure performance improvement from caching
        
        Compares response times for cache hits vs misses
        """
        print(f"\n{'='*80}")
        print(f"TEST 3: CACHE PERFORMANCE IMPROVEMENT")
        print(f"{'='*80}")
        
        # Clear cache by making a unique request
        print(f"Making initial request to populate cache...")
        
        # First request (MISS)
        start_time = time.time()
        response1 = requests.get(f"{self.api_url}/stats")
        miss_time = (time.time() - start_time) * 1000
        cache_status1 = response1.headers.get('X-Cache-Status', 'UNKNOWN')
        
        print(f"  First request: {miss_time:.2f}ms (Status: {cache_status1})")
        
        # Wait a bit
        time.sleep(0.1)
        
        # Second request (should be HIT)
        start_time = time.time()
        response2 = requests.get(f"{self.api_url}/stats")
        hit_time = (time.time() - start_time) * 1000
        cache_status2 = response2.headers.get('X-Cache-Status', 'UNKNOWN')
        
        print(f"  Second request: {hit_time:.2f}ms (Status: {cache_status2})")
        
        # Calculate improvement
        if cache_status2 == 'HIT' and miss_time > 0:
            improvement_percent = ((miss_time - hit_time) / miss_time) * 100
            speedup = miss_time / hit_time if hit_time > 0 else 0
            
            print(f"\n{'='*80}")
            print(f"PERFORMANCE IMPROVEMENT")
            print(f"{'='*80}")
            print(f"Cache MISS time: {miss_time:.2f}ms")
            print(f"Cache HIT time: {hit_time:.2f}ms")
            print(f"Improvement: {improvement_percent:.1f}%")
            print(f"Speedup: {speedup:.1f}x faster")
            
            if improvement_percent > 50:
                print(f"\n✓ Significant performance improvement from caching")
            else:
                print(f"\n⚠ Limited performance improvement from caching")
            
            return {
                "miss_time_ms": miss_time,
                "hit_time_ms": hit_time,
                "improvement_percent": improvement_percent,
                "speedup": speedup
            }
        else:
            print(f"\n⚠ Could not measure improvement (cache status: {cache_status2})")
            return {}
    
    def test_ttl_values(self) -> bool:
        """
        Test 4: Verify TTL values are appropriate
        
        Checks that cached responses have reasonable TTL values
        """
        print(f"\n{'='*80}")
        print(f"TEST 4: TTL VALUES")
        print(f"{'='*80}")
        
        # Expected TTL values for each endpoint
        expected_ttls = {
            "/stats": 86400,  # 24 hours
            "/stats/distribution": 86400,  # 24 hours
            "/buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=10": 3600,  # 1 hour
        }
        
        all_passed = True
        
        for endpoint, expected_ttl in expected_ttls.items():
            print(f"\nTesting: {endpoint}")
            print(f"  Expected TTL: {expected_ttl}s ({expected_ttl/3600:.1f} hours)")
            
            try:
                response = requests.get(f"{self.api_url}{endpoint}")
                
                # Check if response contains cache metadata
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for _cache_expires_at in response body
                    if '_cache_expires_at' in data:
                        expires_at = data['_cache_expires_at']
                        print(f"  ✓ Cache expires at: {expires_at}")
                        
                        # Parse and calculate remaining TTL
                        from datetime import datetime
                        try:
                            expires_dt = datetime.fromisoformat(expires_at)
                            now = datetime.now()
                            remaining_seconds = (expires_dt - now).total_seconds()
                            
                            print(f"  ✓ Remaining TTL: {remaining_seconds:.0f}s ({remaining_seconds/3600:.1f} hours)")
                            
                            # Check if TTL is reasonable (within 10% of expected)
                            if abs(remaining_seconds - expected_ttl) / expected_ttl < 0.1:
                                print(f"  ✓ TTL is appropriate")
                            else:
                                print(f"  ⚠ TTL differs from expected")
                        except:
                            print(f"  ⚠ Could not parse expiration time")
                    else:
                        print(f"  ⚠ No cache expiration metadata in response")
                        all_passed = False
                else:
                    print(f"  ✗ Request failed with status {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_cache_size_and_eviction(self) -> bool:
        """
        Test 5: Verify cache size limits and eviction
        
        Tests that cache doesn't grow unbounded and eviction works
        """
        print(f"\n{'='*80}")
        print(f"TEST 5: CACHE SIZE AND EVICTION")
        print(f"{'='*80}")
        
        # Check health endpoint for cache status
        try:
            response = requests.get(f"{self.api_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'checks' in data and 'cache' in data['checks']:
                    cache_info = data['checks']['cache']
                    
                    if isinstance(cache_info, dict):
                        entries = cache_info.get('entries', 0)
                        max_size = cache_info.get('max_size', 0)
                        
                        print(f"Cache entries: {entries}")
                        print(f"Max cache size: {max_size}")
                        
                        if entries <= max_size:
                            print(f"✓ Cache size is within limits")
                            return True
                        else:
                            print(f"⚠ Cache size exceeds max size")
                            return False
                    else:
                        print(f"✓ Cache status: {cache_info}")
                        return True
                else:
                    print(f"⚠ No cache information in health endpoint")
                    return False
            else:
                print(f"✗ Health endpoint returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error checking cache size: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict:
        """
        Run all cache effectiveness tests
        
        Returns summary of all test results
        """
        print(f"\n{'='*80}")
        print(f"CACHE EFFECTIVENESS TEST SUITE")
        print(f"{'='*80}")
        print(f"API URL: {self.api_url}")
        print(f"Date: {datetime.now().isoformat()}")
        print(f"{'='*80}")
        
        results = {
            "api_url": self.api_url,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test 1: Cache headers
        results["tests"]["cache_headers"] = {
            "passed": self.test_cache_headers()
        }
        
        # Test 2: Cache hit rate
        hit_rate, hit_stats = self.test_cache_hit_rate(num_requests=50)
        results["tests"]["cache_hit_rate"] = {
            "passed": hit_rate >= 60.0,
            "hit_rate_percent": hit_rate,
            "stats": hit_stats
        }
        
        # Test 3: Performance improvement
        perf_improvement = self.test_cache_performance_improvement()
        results["tests"]["performance_improvement"] = {
            "passed": perf_improvement.get('improvement_percent', 0) > 50,
            "stats": perf_improvement
        }
        
        # Test 4: TTL values
        results["tests"]["ttl_values"] = {
            "passed": self.test_ttl_values()
        }
        
        # Test 5: Cache size and eviction
        results["tests"]["cache_size_eviction"] = {
            "passed": self.test_cache_size_and_eviction()
        }
        
        # Print final summary
        print(f"\n{'='*80}")
        print(f"FINAL SUMMARY")
        print(f"{'='*80}")
        
        total_tests = len(results["tests"])
        passed_tests = sum(1 for test in results["tests"].values() if test["passed"])
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        
        for test_name, test_result in results["tests"].items():
            status = "✓ PASS" if test_result["passed"] else "✗ FAIL"
            print(f"  {test_name}: {status}")
        
        if passed_tests == total_tests:
            print(f"\n✓ All cache effectiveness tests passed!")
        else:
            print(f"\n⚠ Some cache effectiveness tests failed")
        
        print(f"{'='*80}\n")
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Verify cache effectiveness for Solar Potential API"
    )
    parser.add_argument(
        '--api-url',
        default='http://localhost:8080',
        help="API base URL (default: http://localhost:8080)"
    )
    parser.add_argument(
        '--num-requests',
        type=int,
        default=50,
        help="Number of requests for hit rate test (default: 50)"
    )
    
    args = parser.parse_args()
    
    # Run tests
    tester = CacheEffectivenessTest(args.api_url)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    all_passed = all(test["passed"] for test in results["tests"].values())
    exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
