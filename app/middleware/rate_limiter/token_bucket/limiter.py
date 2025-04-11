import time
from typing import Dict, Tuple
import threading

class TokenBucket:
    def __init__(self, capacity: int = 10, refill_rate: float = 1.0):
        """
        Initialize token bucket rate limiter.
        
        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Number of tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: Dict[str, Tuple[float, float]] = {}  # {ip: (tokens, last_refill_time)}
        self.lock = threading.Lock()
    
    def _get_tokens(self, ip: str) -> float:
        """Get current number of tokens for an IP address."""
        if ip not in self.buckets:
            # New IP, initialize with full bucket
            self.buckets[ip] = (self.capacity, time.time())
            return self.capacity
        
        tokens, last_refill = self.buckets[ip]
        now = time.time()
        
        # Calculate time passed since last refill
        time_passed = now - last_refill
        
        # Calculate new tokens to add based on time passed and refill rate
        new_tokens = time_passed * self.refill_rate
        
        # Update tokens and last refill time
        current_tokens = min(self.capacity, tokens + new_tokens)
        self.buckets[ip] = (current_tokens, now)
        
        return current_tokens
    
    def consume(self, ip: str, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket for a given IP.
        
        Args:
            ip: The IP address identifier
            tokens: Number of tokens to consume (default 1)
            
        Returns:
            bool: True if tokens were consumed, False if not enough tokens
        """
        with self.lock:
            current_tokens = self._get_tokens(ip)
            
            # Check if we have enough tokens
            if current_tokens < tokens:
                return False
            
            # Consume tokens
            self.buckets[ip] = (current_tokens - tokens, self.buckets[ip][1])
            return True

# Create a global token bucket rate limiter instance
token_bucket = TokenBucket(capacity=10, refill_rate=1.0) 