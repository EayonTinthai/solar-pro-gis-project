"""
Load tests for Solar Potential API using Locust
Requirements: 4, 14

Run with: locust -f tests/locustfile.py --host=http://localhost:8080

Test scenarios:
- 100 concurrent users
- Verify response times < 600ms (p95)
- Verify cache effectiveness
"""

from locust import HttpUser, task, between, events
import random
import json
from datetime import datetime


class SolarPotentialUser(HttpUser):
    """
    Simulates a user interacting with the Solar Potential API
    
    This user performs various API operations with realistic patterns:
    - Queries building data
    - Calculates solar potential
    - Checks statistics
    - Analyzes polygons
    """
    
    # Wait between 1-3 seconds between tasks (realistic user behavior)
    wait_time = between(1, 3)
    
    # Bangkok area coordinates for testing
    BANGKOK_BOUNDS = {
        "min_lat": 13.6,
        "max_lat": 13.9,
        "min_lon": 100.4,
        "max_lon": 100.7
    }
    
    def on_start(self):
        """Called when a user starts"""
        self.stats_cache_hits = 0
        self.stats_cache_misses = 0
    
    @task(10)
    def get_buildings_bbox(self):
        """
        Query buildings by bounding box (most common operation)
        Weight: 10 (high frequency)
        """
        # Generate random bbox within Bangkok
        lat_range = self.BANGKOK_BOUNDS["max_lat"] - self.BANGKOK_BOUNDS["min_lat"]
        lon_range = self.BANGKOK_BOUNDS["max_lon"] - self.BANGKOK_BOUNDS["min_lon"]
        
        min_lat = self.BANGKOK_BOUNDS["min_lat"] + random.random() * lat_range * 0.8
        min_lon = self.BANGKOK_BOUNDS["min_lon"] + random.random() * lon_range * 0.8
        
        params = {
            "min_lat": min_lat,
            "max_lat": min_lat + 0.05,
            "min_lon": min_lon,
            "max_lon": min_lon + 0.05,
            "limit": 100,
            "min_confidence": 0.7
        }
        
        with self.client.get(
            "/buildings/bbox",
            params=params,
            catch_response=True,
            name="/buildings/bbox"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "buildings" in data:
                    response.success()
                else:
                    response.failure("Missing buildings field")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(5)
    def get_buildings_with_filters(self):
        """
        Query buildings with advanced filters
        Weight: 5 (medium frequency)
        """
        lat_range = self.BANGKOK_BOUNDS["max_lat"] - self.BANGKOK_BOUNDS["min_lat"]
        lon_range = self.BANGKOK_BOUNDS["max_lon"] - self.BANGKOK_BOUNDS["min_lon"]
        
        min_lat = self.BANGKOK_BOUNDS["min_lat"] + random.random() * lat_range * 0.8
        min_lon = self.BANGKOK_BOUNDS["min_lon"] + random.random() * lon_range * 0.8
        
        params = {
            "min_lat": min_lat,
            "max_lat": min_lat + 0.05,
            "min_lon": min_lon,
            "max_lon": min_lon + 0.05,
            "limit": 50,
            "min_confidence": 0.8,
            "min_area_m2": 100,
            "max_area_m2": 500
        }
        
        with self.client.get(
            "/buildings/bbox",
            params=params,
            catch_response=True,
            name="/buildings/bbox (filtered)"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(3)
    def calculate_solar_potential(self):
        """
        Calculate solar potential for a building
        Weight: 3 (medium-low frequency)
        """
        # Random location in Bangkok
        lat = self.BANGKOK_BOUNDS["min_lat"] + random.random() * (
            self.BANGKOK_BOUNDS["max_lat"] - self.BANGKOK_BOUNDS["min_lat"]
        )
        lon = self.BANGKOK_BOUNDS["min_lon"] + random.random() * (
            self.BANGKOK_BOUNDS["max_lon"] - self.BANGKOK_BOUNDS["min_lon"]
        )
        
        payload = {
            "latitude": lat,
            "longitude": lon,
            "area_m2": random.uniform(100, 500),
            "confidence": random.uniform(0.7, 0.95),
            "tilt": None,
            "azimuth": 180
        }
        
        with self.client.post(
            "/solar/calculate",
            json=payload,
            catch_response=True,
            name="/solar/calculate"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "system_size_kwp" in data and "annual_production_kwh" in data:
                    response.success()
                else:
                    response.failure("Missing required fields")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def calculate_solar_with_custom_params(self):
        """
        Calculate solar potential with custom parameters
        Weight: 2 (low frequency)
        """
        lat = self.BANGKOK_BOUNDS["min_lat"] + random.random() * (
            self.BANGKOK_BOUNDS["max_lat"] - self.BANGKOK_BOUNDS["min_lat"]
        )
        lon = self.BANGKOK_BOUNDS["min_lon"] + random.random() * (
            self.BANGKOK_BOUNDS["max_lon"] - self.BANGKOK_BOUNDS["min_lon"]
        )
        
        payload = {
            "latitude": lat,
            "longitude": lon,
            "area_m2": random.uniform(100, 500),
            "confidence": random.uniform(0.7, 0.95),
            "tilt": None,
            "azimuth": 180,
            "custom_params": {
                "panel_efficiency": random.uniform(0.18, 0.23),
                "system_efficiency": random.uniform(0.75, 0.88),
                "cost_per_wp": random.uniform(22, 28)
            }
        }
        
        with self.client.post(
            "/solar/calculate",
            json=payload,
            catch_response=True,
            name="/solar/calculate (custom)"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(8)
    def get_stats(self):
        """
        Get dataset statistics (should be heavily cached)
        Weight: 8 (high frequency, tests caching)
        """
        with self.client.get(
            "/stats",
            catch_response=True,
            name="/stats"
        ) as response:
            if response.status_code == 200:
                # Track cache hits/misses if header is present
                cache_status = response.headers.get("X-Cache-Status", "UNKNOWN")
                if cache_status == "HIT":
                    self.stats_cache_hits += 1
                elif cache_status == "MISS":
                    self.stats_cache_misses += 1
                
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(4)
    def get_stats_distribution(self):
        """
        Get statistics distribution (should be cached)
        Weight: 4 (medium frequency)
        """
        with self.client.get(
            "/stats/distribution",
            catch_response=True,
            name="/stats/distribution"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def analyze_polygon(self):
        """
        Analyze a custom polygon
        Weight: 1 (low frequency, expensive operation)
        """
        # Small polygon in Bangkok
        lat = self.BANGKOK_BOUNDS["min_lat"] + random.random() * (
            self.BANGKOK_BOUNDS["max_lat"] - self.BANGKOK_BOUNDS["min_lat"]
        ) * 0.8
        lon = self.BANGKOK_BOUNDS["min_lon"] + random.random() * (
            self.BANGKOK_BOUNDS["max_lon"] - self.BANGKOK_BOUNDS["min_lon"]
        ) * 0.8
        
        # Create a small square polygon (~1km x 1km)
        polygon = {
            "type": "Polygon",
            "coordinates": [[
                [lon, lat],
                [lon + 0.01, lat],
                [lon + 0.01, lat + 0.01],
                [lon, lat + 0.01],
                [lon, lat]
            ]]
        }
        
        payload = {
            "geometry": polygon,
            "min_confidence": 0.7,
            "include_buildings": False
        }
        
        with self.client.post(
            "/polygon/analyze",
            json=payload,
            catch_response=True,
            name="/polygon/analyze"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "aggregated_stats" in data:
                    response.success()
                else:
                    response.failure("Missing aggregated_stats")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def get_health(self):
        """
        Health check endpoint
        Weight: 2 (monitoring/health checks)
        """
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Called when the load test stops
    Print cache effectiveness statistics
    """
    print("\n" + "="*80)
    print("LOAD TEST SUMMARY")
    print("="*80)
    
    # Get statistics
    stats = environment.stats
    
    # Print overall statistics
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    
    # Print response time statistics
    print(f"\nResponse Times:")
    print(f"  Average: {stats.total.avg_response_time:.2f}ms")
    print(f"  Median: {stats.total.median_response_time:.2f}ms")
    print(f"  95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"  99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"  Max: {stats.total.max_response_time:.2f}ms")
    
    # Check performance targets
    p95 = stats.total.get_response_time_percentile(0.95)
    print(f"\nPerformance Target Check:")
    print(f"  Target: p95 < 600ms")
    print(f"  Actual: p95 = {p95:.2f}ms")
    if p95 < 600:
        print(f"  Status: ✓ PASS")
    else:
        print(f"  Status: ✗ FAIL")
    
    # Print per-endpoint statistics
    print(f"\nPer-Endpoint Statistics:")
    print(f"{'Endpoint':<40} {'Requests':<10} {'Failures':<10} {'Avg (ms)':<10} {'p95 (ms)':<10}")
    print("-" * 80)
    
    for name, entry in stats.entries.items():
        if entry.num_requests > 0:
            print(f"{name:<40} {entry.num_requests:<10} {entry.num_failures:<10} "
                  f"{entry.avg_response_time:<10.2f} {entry.get_response_time_percentile(0.95):<10.2f}")
    
    print("="*80)


# Additional test scenarios for specific use cases

class HighLoadUser(HttpUser):
    """
    Simulates high-load scenario with rapid requests
    Used for stress testing
    """
    wait_time = between(0.1, 0.5)  # Very short wait time
    
    @task
    def rapid_stats_requests(self):
        """Rapid stats requests to test caching under load"""
        self.client.get("/stats", name="/stats (high-load)")
    
    @task
    def rapid_bbox_requests(self):
        """Rapid bbox requests"""
        params = {
            "min_lat": 13.7,
            "max_lat": 13.8,
            "min_lon": 100.5,
            "max_lon": 100.6,
            "limit": 10
        }
        self.client.get("/buildings/bbox", params=params, name="/buildings/bbox (high-load)")


class CacheTestUser(HttpUser):
    """
    Specifically tests cache effectiveness
    Makes repeated identical requests to measure cache hit rate
    """
    wait_time = between(0.5, 1.5)
    
    # Fixed parameters for cache testing
    FIXED_BBOX = {
        "min_lat": 13.7,
        "max_lat": 13.8,
        "min_lon": 100.5,
        "max_lon": 100.6,
        "limit": 100
    }
    
    @task(5)
    def cached_stats_request(self):
        """Repeated stats requests (should hit cache)"""
        self.client.get("/stats", name="/stats (cache-test)")
    
    @task(3)
    def cached_bbox_request(self):
        """Repeated bbox requests with same parameters"""
        self.client.get(
            "/buildings/bbox",
            params=self.FIXED_BBOX,
            name="/buildings/bbox (cache-test)"
        )
    
    @task(2)
    def cached_distribution_request(self):
        """Repeated distribution requests"""
        self.client.get("/stats/distribution", name="/stats/distribution (cache-test)")
