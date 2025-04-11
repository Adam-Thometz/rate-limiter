from enum import Enum
from typing import Dict, List, Optional, Set, Union

class RateLimitType(str, Enum):
    TOKEN_BUCKET = "token_bucket"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    NONE = "none"  # No rate limiting

class RateLimitConfig:
    """Centralized configuration for rate limiting."""
    
    def __init__(self):
        # Default rate limit type for routes not explicitly configured
        self.default_limit_type: RateLimitType = RateLimitType.NONE
        
        # Map of path prefixes to rate limit types
        self.route_configs: Dict[str, RateLimitType] = {}
        
        # Paths that are completely exempt from rate limiting
        self.exempt_paths: Set[str] = {"/health", "/docs", "/redoc", "/openapi.json"}
    
    def set_limit_for_route(self, path_prefix: str, limit_type: RateLimitType):
        """
        Configure rate limiting for a specific path prefix.
        
        Args:
            path_prefix: The route path prefix to apply rate limiting to
            limit_type: The type of rate limiting to apply
        """
        self.route_configs[path_prefix] = limit_type
    
    def set_limit_for_routes(self, path_prefixes: List[str], limit_type: RateLimitType):
        """
        Configure rate limiting for multiple path prefixes.
        
        Args:
            path_prefixes: List of route path prefixes to apply rate limiting to
            limit_type: The type of rate limiting to apply
        """
        for path in path_prefixes:
            self.set_limit_for_route(path, limit_type)
    
    def exempt_route(self, path: str):
        """
        Mark a route as exempt from all rate limiting.
        
        Args:
            path: The route path to exempt
        """
        self.exempt_paths.add(path)
    
    def get_limit_type_for_path(self, path: str) -> RateLimitType:
        """
        Determine which rate limiting type to apply to a given path.
        
        Args:
            path: The request path
            
        Returns:
            RateLimitType: The type of rate limiting to apply
        """
        # First check if path is exempt
        if path in self.exempt_paths:
            return RateLimitType.NONE
        
        # Sort route configs by path length in descending order (longest first)
        # This ensures more specific paths take priority
        matched_prefix = ""
        matched_type = self.default_limit_type
        
        for prefix, limit_type in sorted(self.route_configs.items(), key=lambda x: len(x[0]), reverse=True):
            if path.startswith(prefix) and len(prefix) > len(matched_prefix):
                matched_prefix = prefix
                matched_type = limit_type
        
        return matched_type

# Create a global config instance
rate_limit_config = RateLimitConfig() 