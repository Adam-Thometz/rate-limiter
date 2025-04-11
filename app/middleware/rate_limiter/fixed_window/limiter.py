import time
from typing import Dict
import threading
import math

class FixedWindowCounter:
    def __init__(self, window_size: int = 60, max_requests: int = 10):
        """
        Initialize fixed window counter rate limiter.
        
        Args:
            window_size: Size of the window in seconds
            max_requests: Maximum number of requests allowed in a window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        # {ip: {window_start_time: request_count}}
        self.counters: Dict[str, Dict[int, int]] = {}
        self.lock = threading.Lock()
    
    def _get_window_key(self, timestamp: float) -> int:
        """Calculate the window key based on the timestamp."""
        return math.floor(timestamp / self.window_size) * self.window_size
    
    def _cleanup_old_windows(self, ip: str, current_time: float):
        """Remove windows that are no longer relevant."""
        if ip in self.counters:
            current_window = self._get_window_key(current_time)
            # Keep only the current window
            self.counters[ip] = {k: v for k, v in self.counters[ip].items() 
                                 if k >= current_window - self.window_size}
    
    def is_allowed(self, ip: str) -> bool:
        """
        Check if a request from the given IP is allowed.
        
        Args:
            ip: The IP address identifier
            
        Returns:
            bool: True if the request is allowed, False if it exceeds the rate limit
        """
        with self.lock:
            current_time = time.time()
            current_window = self._get_window_key(current_time)
            
            # Initialize counter for this IP if it doesn't exist
            if ip not in self.counters:
                self.counters[ip] = {}
            
            # Cleanup old windows
            self._cleanup_old_windows(ip, current_time)
            
            # Initialize counter for this window if it doesn't exist
            if current_window not in self.counters[ip]:
                self.counters[ip][current_window] = 0
            
            # Check if the counter exceeds the limit
            if self.counters[ip][current_window] >= self.max_requests:
                return False
            
            # Increment the counter
            self.counters[ip][current_window] += 1
            return True

# Create a global fixed window counter instance
fixed_window_counter = FixedWindowCounter(window_size=60, max_requests=10) 