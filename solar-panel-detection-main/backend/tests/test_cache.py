"""
Tests for caching functionality
"""

import pytest
from datetime import datetime, timedelta
from utils.cache import (
    cache_with_ttl,
    generate_cache_key,
    clear_cache,
    evict_expired,
    _cache
)


def test_generate_cache_key():
    """Test cache key generation"""
    key1 = generate_cache_key("test_func", (1, 2), {"a": 3})
    key2 = generate_cache_key("test_func", (1, 2), {"a": 3})
    key3 = generate_cache_key("test_func", (1, 3), {"a": 3})
    
    # Same inputs should generate same key
    assert key1 == key2
    
    # Different inputs should generate different key
    assert key1 != key3


def test_cache_with_ttl_sync():
    """Test caching decorator with synchronous function"""
    clear_cache()
    
    call_count = 0
    
    @cache_with_ttl(seconds=60)
    def test_func(x):
        nonlocal call_count
        call_count += 1
        return {"result": x * 2}
    
    # First call - should execute function
    result1 = test_func(5)
    assert result1["result"] == 10
    assert result1["_cache_status"] == "MISS"
    assert call_count == 1
    
    # Second call with same args - should use cache
    result2 = test_func(5)
    assert result2["result"] == 10
    assert result2["_cache_status"] == "HIT"
    assert call_count == 1  # Function not called again
    
    # Call with different args - should execute function
    result3 = test_func(10)
    assert result3["result"] == 20
    assert result3["_cache_status"] == "MISS"
    assert call_count == 2


@pytest.mark.asyncio
async def test_cache_with_ttl_async():
    """Test caching decorator with async function"""
    clear_cache()
    
    call_count = 0
    
    @cache_with_ttl(seconds=60)
    async def test_func(x):
        nonlocal call_count
        call_count += 1
        return {"result": x * 2}
    
    # First call - should execute function
    result1 = await test_func(5)
    assert result1["result"] == 10
    assert result1["_cache_status"] == "MISS"
    assert call_count == 1
    
    # Second call with same args - should use cache
    result2 = await test_func(5)
    assert result2["result"] == 10
    assert result2["_cache_status"] == "HIT"
    assert call_count == 1  # Function not called again


def test_cache_expiration():
    """Test that cache entries expire after TTL"""
    clear_cache()
    
    @cache_with_ttl(seconds=1)
    def test_func(x):
        return {"result": x}
    
    # First call
    result1 = test_func(5)
    assert result1["_cache_status"] == "MISS"
    
    # Immediate second call - should hit cache
    result2 = test_func(5)
    assert result2["_cache_status"] == "HIT"
    
    # Wait for expiration
    import time
    time.sleep(1.1)
    
    # After expiration - should miss cache
    result3 = test_func(5)
    assert result3["_cache_status"] == "MISS"


def test_clear_cache():
    """Test cache clearing"""
    clear_cache()
    
    @cache_with_ttl(seconds=60)
    def test_func(x):
        return {"result": x}
    
    # Add some entries
    test_func(1)
    test_func(2)
    test_func(3)
    
    # Cache should have entries
    assert len(_cache) > 0
    
    # Clear cache
    count = clear_cache()
    assert count > 0
    assert len(_cache) == 0


def test_evict_expired():
    """Test expired entry eviction"""
    clear_cache()
    
    # Manually add expired entry
    from datetime import datetime, timedelta
    _cache["expired_key"] = ({"data": "old"}, datetime.now() - timedelta(seconds=10))
    _cache["valid_key"] = ({"data": "new"}, datetime.now() + timedelta(seconds=60))
    
    # Evict expired
    count = evict_expired()
    
    assert count == 1
    assert "expired_key" not in _cache
    assert "valid_key" in _cache


def test_cache_metadata():
    """Test that cache metadata is added to responses"""
    clear_cache()
    
    @cache_with_ttl(seconds=60)
    def test_func(x):
        return {"result": x}
    
    result = test_func(5)
    
    # Check metadata fields
    assert "_cache_status" in result
    assert "_cache_expires_at" in result
    assert result["_cache_status"] in ["HIT", "MISS"]
    
    # Verify expires_at is a valid ISO timestamp
    expires_at = result["_cache_expires_at"]
    datetime.fromisoformat(expires_at)  # Should not raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
