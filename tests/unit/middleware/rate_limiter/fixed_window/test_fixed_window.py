import time
import threading
import pytest
from unittest.mock import patch
from app.middleware.rate_limiter.fixed_window.limiter import FixedWindowCounter

class TestFixedWindowCounter:
    
    def test_init(self):
        """Test initialization of FixedWindowCounter with default and custom values."""
        # Test with default values
        counter = FixedWindowCounter()
        assert counter.window_size == 60
        assert counter.max_requests == 10
        assert counter.counters == {}
        
        # Test with custom values
        counter = FixedWindowCounter(window_size=30, max_requests=20)
        assert counter.window_size == 30
        assert counter.max_requests == 20
        assert counter.counters == {}
    
    def test_get_window_key(self):
        """Test window key calculation based on timestamps."""
        counter = FixedWindowCounter(window_size=60)
        
        # Test exact minute boundary
        assert counter._get_window_key(3600.0) == 3600
        
        # Test middle of a minute
        assert counter._get_window_key(3630.5) == 3600
        
        # Test just before minute boundary
        assert counter._get_window_key(3659.999) == 3600
        
        # Test at next minute boundary
        assert counter._get_window_key(3660.0) == 3660
        
        # Test with a different window size (30 seconds)
        counter = FixedWindowCounter(window_size=30)
        assert counter._get_window_key(3615.0) == 3600
        assert counter._get_window_key(3629.999) == 3600
        assert counter._get_window_key(3630.0) == 3630
        assert counter._get_window_key(3645.0) == 3630
        assert counter._get_window_key(3660.0) == 3660
    
    def test_cleanup_old_windows(self):
        """Test cleanup of old windows."""
        counter = FixedWindowCounter(window_size=60)
        
        # Setup counters with multiple windows
        counter.counters = {
            "192.168.1.1": {
                3480: 5,  # Old window
                3540: 7,  # Previous window
                3600: 3   # Current window
            }
        }
        
        # Cleanup with current time at 3600 (keep 3540 and 3600)
        with patch('time.time', return_value=3600.0):
            counter._cleanup_old_windows("192.168.1.1", 3600.0)
            assert "192.168.1.1" in counter.counters
            assert len(counter.counters["192.168.1.1"]) == 2
            assert 3480 not in counter.counters["192.168.1.1"]
            assert 3540 in counter.counters["192.168.1.1"]
            assert 3600 in counter.counters["192.168.1.1"]
        
        # Cleanup with current time at 3660 (keep only 3660)
        counter.counters = {
            "192.168.1.1": {
                3540: 7,  # Old window
                3600: 3,  # Previous window
                3660: 1   # Current window
            }
        }
        
        with patch('time.time', return_value=3660.0):
            counter._cleanup_old_windows("192.168.1.1", 3660.0)
            assert "192.168.1.1" in counter.counters
            assert len(counter.counters["192.168.1.1"]) == 2
            assert 3540 not in counter.counters["192.168.1.1"]
            assert 3600 in counter.counters["192.168.1.1"]
            assert 3660 in counter.counters["192.168.1.1"]
    
    def test_is_allowed_new_ip(self):
        """Test that new IPs are allowed and initialized correctly."""
        counter = FixedWindowCounter(max_requests=5)
        
        with patch('time.time', return_value=3600.0):
            # New IP should be allowed
            result = counter.is_allowed("192.168.1.1")
            
            assert result is True
            assert "192.168.1.1" in counter.counters
            assert 3600 in counter.counters["192.168.1.1"]
            assert counter.counters["192.168.1.1"][3600] == 1  # First request counted
    
    def test_is_allowed_under_limit(self):
        """Test that requests under the limit are allowed."""
        counter = FixedWindowCounter(max_requests=5)
        
        # Setup counters with existing requests
        counter.counters = {
            "192.168.1.1": {
                3600: 3  # 3 requests already in current window
            }
        }
        
        with patch('time.time', return_value=3600.0):
            # Should be allowed (4th request)
            result = counter.is_allowed("192.168.1.1")
            
            assert result is True
            assert counter.counters["192.168.1.1"][3600] == 4
            
            # Should be allowed (5th request, reaches limit)
            result = counter.is_allowed("192.168.1.1")
            
            assert result is True
            assert counter.counters["192.168.1.1"][3600] == 5
    
    def test_is_allowed_over_limit(self):
        """Test that requests over the limit are denied."""
        counter = FixedWindowCounter(max_requests=5)
        
        # Setup counters with max requests
        counter.counters = {
            "192.168.1.1": {
                3600: 5  # Already at limit
            }
        }
        
        with patch('time.time', return_value=3600.0):
            # Should be denied (6th request)
            result = counter.is_allowed("192.168.1.1")
            
            assert result is False
            assert counter.counters["192.168.1.1"][3600] == 5  # Count unchanged
    
    def test_is_allowed_window_transition(self):
        """Test that window transitions reset the count."""
        counter = FixedWindowCounter(max_requests=5)
        
        # Setup counters with max requests in previous window
        counter.counters = {
            "192.168.1.1": {
                3600: 5  # Max requests in previous window
            }
        }
        
        with patch('time.time', return_value=3660.0):
            # Should be allowed in new window
            result = counter.is_allowed("192.168.1.1")
            
            assert result is True
            assert 3600 in counter.counters["192.168.1.1"]  # Previous window still tracked
            assert 3660 in counter.counters["192.168.1.1"]  # New window added
            assert counter.counters["192.168.1.1"][3660] == 1  # First request in new window
    
    def test_thread_safety(self):
        """Test that the counter is thread-safe."""
        counter = FixedWindowCounter(max_requests=100)
        
        # Function to make requests in parallel
        def make_requests():
            with patch('time.time', return_value=3600.0):
                for _ in range(10):  # Each thread makes 10 requests
                    counter.is_allowed("192.168.1.1")
        
        # Create and start 10 threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # 10 threads * 10 requests = 100 requests
        assert "192.168.1.1" in counter.counters
        assert 3600 in counter.counters["192.168.1.1"]
        assert counter.counters["192.168.1.1"][3600] == 100 