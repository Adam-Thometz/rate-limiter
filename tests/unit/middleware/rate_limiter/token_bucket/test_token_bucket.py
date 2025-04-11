import time
import threading
import pytest
from unittest.mock import patch
from app.middleware.rate_limiter.token_bucket.limiter import TokenBucket

class TestTokenBucket:
    
    def test_init(self):
        """Test initialization of TokenBucket with default and custom values."""
        # Test with default values
        bucket = TokenBucket()
        assert bucket.capacity == 10
        assert bucket.refill_rate == 1.0
        assert bucket.buckets == {}
        
        # Test with custom values
        bucket = TokenBucket(capacity=20, refill_rate=0.5)
        assert bucket.capacity == 20
        assert bucket.refill_rate == 0.5
        assert bucket.buckets == {}
    
    def test_get_tokens_new_ip(self):
        """Test that new IPs start with a full bucket."""
        bucket = TokenBucket(capacity=15)
        
        with patch('time.time', return_value=1000.0):
            tokens = bucket._get_tokens("192.168.1.1")
            
            # New IP should have a full bucket
            assert tokens == 15
            assert "192.168.1.1" in bucket.buckets
            assert bucket.buckets["192.168.1.1"][0] == 15  # Tokens
            assert bucket.buckets["192.168.1.1"][1] == 1000.0  # Last refill time
    
    def test_get_tokens_refill(self):
        """Test that tokens are refilled based on elapsed time."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)
        
        # Setup initial state - 5 tokens at time 1000.0
        with patch('time.time', return_value=1000.0):
            bucket.buckets["192.168.1.1"] = (5.0, 1000.0)
            
            # Get tokens without time passing
            tokens = bucket._get_tokens("192.168.1.1")
            
            # No time passed, so no refill
            assert tokens == 5.0
            assert bucket.buckets["192.168.1.1"][0] == 5.0
            assert bucket.buckets["192.168.1.1"][1] == 1000.0
        
        # 2.5 seconds pass, refill rate is 2.0 tokens/sec
        with patch('time.time', return_value=1002.5):
            tokens = bucket._get_tokens("192.168.1.1")
            
            # 2.5 seconds * 2.0 tokens/sec = 5.0 tokens added
            # 5.0 (initial) + 5.0 (added) = 10.0 tokens (full bucket)
            assert tokens == 10.0
            assert bucket.buckets["192.168.1.1"][0] == 10.0
            assert bucket.buckets["192.168.1.1"][1] == 1002.5
    
    def test_get_tokens_cap_at_capacity(self):
        """Test that tokens are capped at the bucket capacity."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)
        
        # Setup initial state - 8 tokens at time 1000.0
        with patch('time.time', return_value=1000.0):
            bucket.buckets["192.168.1.1"] = (8.0, 1000.0)
        
        # 5 seconds pass, refill rate is 2.0 tokens/sec
        with patch('time.time', return_value=1005.0):
            tokens = bucket._get_tokens("192.168.1.1")
            
            # 5 seconds * 2.0 tokens/sec = 10.0 tokens added
            # 8.0 (initial) + 10.0 (added) = 18.0 tokens, but capped at 10.0
            assert tokens == 10.0
            assert bucket.buckets["192.168.1.1"][0] == 10.0
            assert bucket.buckets["192.168.1.1"][1] == 1005.0
    
    def test_consume_success(self):
        """Test that tokens can be consumed successfully."""
        bucket = TokenBucket(capacity=10)
        
        # Setup initial state - full bucket
        with patch('time.time', return_value=1000.0):
            bucket.buckets["192.168.1.1"] = (10.0, 1000.0)
            
            # Consume 1 token (default)
            result = bucket.consume("192.168.1.1")
            
            # Success
            assert result is True
            assert bucket.buckets["192.168.1.1"][0] == 9.0
            assert bucket.buckets["192.168.1.1"][1] == 1000.0
            
            # Consume 5 tokens
            result = bucket.consume("192.168.1.1", 5)
            
            # Success
            assert result is True
            assert bucket.buckets["192.168.1.1"][0] == 4.0
            assert bucket.buckets["192.168.1.1"][1] == 1000.0
    
    def test_consume_failure(self):
        """Test that consumption fails when not enough tokens."""
        bucket = TokenBucket(capacity=10)
        
        # Setup initial state - 3 tokens
        with patch('time.time', return_value=1000.0):
            bucket.buckets["192.168.1.1"] = (3.0, 1000.0)
            
            # Try to consume 5 tokens
            result = bucket.consume("192.168.1.1", 5)
            
            # Failure
            assert result is False
            # Bucket remains unchanged
            assert bucket.buckets["192.168.1.1"][0] == 3.0
            assert bucket.buckets["192.168.1.1"][1] == 1000.0
    
    def test_consume_new_ip(self):
        """Test consuming tokens for a new IP."""
        bucket = TokenBucket(capacity=10)
        
        with patch('time.time', return_value=1000.0):
            # Consume for a new IP
            result = bucket.consume("192.168.1.1", 4)
            
            # Success - new IP gets a full bucket first
            assert result is True
            assert bucket.buckets["192.168.1.1"][0] == 6.0  # 10 - 4 = 6
            assert bucket.buckets["192.168.1.1"][1] == 1000.0
    
    def test_thread_safety(self):
        """Test that the token bucket is thread-safe."""
        bucket = TokenBucket(capacity=100, refill_rate=0)  # No refill
        
        # Initialize the bucket for our test IP
        with patch('time.time', return_value=1000.0):
            bucket.buckets["192.168.1.1"] = (100.0, 1000.0)
        
        # Function to consume tokens in parallel
        def consume_tokens():
            with patch('time.time', return_value=1000.0):
                for _ in range(10):  # Each thread consumes 10 tokens
                    bucket.consume("192.168.1.1")
        
        # Create and start 10 threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=consume_tokens)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # 10 threads * 10 tokens = 100 tokens consumed
        with patch('time.time', return_value=1000.0):
            tokens = bucket._get_tokens("192.168.1.1")
            assert tokens == 0.0  # All tokens consumed 