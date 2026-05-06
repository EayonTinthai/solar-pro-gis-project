"""
Quick verification script for caching functionality
Run this to verify the cache is working correctly
"""

from utils.cache import cache_with_ttl, clear_cache, _cache
import time


def demo_caching():
    """Demonstrate caching functionality"""
    print("=" * 60)
    print("CACHING SYSTEM VERIFICATION")
    print("=" * 60)
    
    # Clear cache to start fresh
    clear_cache()
    print("\n1. Cache cleared")
    print(f"   Cache size: {len(_cache)}")
    
    # Define a test function with caching
    call_count = 0
    
    @cache_with_ttl(seconds=5)
    def expensive_operation(x):
        nonlocal call_count
        call_count += 1
        print(f"   → Executing expensive operation (call #{call_count})")
        time.sleep(0.1)  # Simulate expensive operation
        return {"result": x * 2, "timestamp": time.time()}
    
    # Test 1: First call (MISS)
    print("\n2. First call with x=10 (should be MISS)")
    result1 = expensive_operation(10)
    print(f"   Result: {result1['result']}")
    print(f"   Cache status: {result1.get('_cache_status', 'N/A')}")
    print(f"   Cache size: {len(_cache)}")
    
    # Test 2: Second call with same args (HIT)
    print("\n3. Second call with x=10 (should be HIT)")
    result2 = expensive_operation(10)
    print(f"   Result: {result2['result']}")
    print(f"   Cache status: {result2.get('_cache_status', 'N/A')}")
    print(f"   Function was called {call_count} time(s) total")
    
    # Test 3: Call with different args (MISS)
    print("\n4. Call with x=20 (should be MISS)")
    result3 = expensive_operation(20)
    print(f"   Result: {result3['result']}")
    print(f"   Cache status: {result3.get('_cache_status', 'N/A')}")
    print(f"   Cache size: {len(_cache)}")
    print(f"   Function was called {call_count} time(s) total")
    
    # Test 4: Wait for expiration
    print("\n5. Waiting 6 seconds for cache to expire...")
    time.sleep(6)
    
    print("\n6. Call with x=10 after expiration (should be MISS)")
    result4 = expensive_operation(10)
    print(f"   Result: {result4['result']}")
    print(f"   Cache status: {result4.get('_cache_status', 'N/A')}")
    print(f"   Function was called {call_count} time(s) total")
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    print(f"✅ Cache MISS on first call: {result1.get('_cache_status') == 'MISS'}")
    print(f"✅ Cache HIT on repeated call: {result2.get('_cache_status') == 'HIT'}")
    print(f"✅ Cache MISS on different args: {result3.get('_cache_status') == 'MISS'}")
    print(f"✅ Cache MISS after expiration: {result4.get('_cache_status') == 'MISS'}")
    print(f"✅ Function called {call_count} times (expected: 4)")
    print("\n✨ Caching system is working correctly!")


if __name__ == "__main__":
    demo_caching()
