"""
Manual test for health endpoint
Run this to verify the health endpoint works
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from fastapi.testclient import TestClient
    from api_bigquery import app
    
    client = TestClient(app)
    
    print("Testing /health endpoint...")
    response = client.get("/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Verify structure
        required_fields = ["status", "version", "timestamp", "checks", "uptime_seconds"]
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
        else:
            print("✅ All required fields present")
            
        # Verify checks
        if "checks" in data:
            checks = data["checks"]
            print(f"\nChecks:")
            print(f"  - BigQuery: {checks.get('bigquery', 'missing')}")
            print(f"  - Weather API: {checks.get('weather_api', 'missing')}")
            print(f"  - Cache: {checks.get('cache', 'missing')}")
            
        print(f"\nStatus: {data.get('status', 'unknown')}")
        print(f"Version: {data.get('version', 'unknown')}")
        print(f"Uptime: {data.get('uptime_seconds', 0)} seconds")
        
        print("\n✅ Health endpoint test PASSED")
    else:
        print(f"❌ Health endpoint test FAILED - Expected 200, got {response.status_code}")
        
except Exception as e:
    print(f"❌ Error running test: {e}")
    import traceback
    traceback.print_exc()
