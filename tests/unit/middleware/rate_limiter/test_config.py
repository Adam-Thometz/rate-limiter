import pytest
from app.middleware.rate_limiter.config import RateLimitConfig, RateLimitType

class TestRateLimitConfig:

    def test_init(self):
        """Test initialization of RateLimitConfig."""
        config = RateLimitConfig()
        
        # Default values
        assert config.default_limit_type == RateLimitType.NONE
        assert config.route_configs == {}
        assert config.exempt_paths == {"/health", "/docs", "/redoc", "/openapi.json"}
    
    def test_set_limit_for_route(self):
        """Test setting rate limit for a single route."""
        config = RateLimitConfig()
        
        # Set a limit for a route
        config.set_limit_for_route("/api/users", RateLimitType.TOKEN_BUCKET)
        
        assert "/api/users" in config.route_configs
        assert config.route_configs["/api/users"] == RateLimitType.TOKEN_BUCKET
        
        # Update an existing route
        config.set_limit_for_route("/api/users", RateLimitType.FIXED_WINDOW)
        
        assert config.route_configs["/api/users"] == RateLimitType.FIXED_WINDOW
    
    def test_set_limit_for_routes(self):
        """Test setting rate limit for multiple routes."""
        config = RateLimitConfig()
        
        # Set a limit for multiple routes
        config.set_limit_for_routes(["/api/users", "/api/posts"], RateLimitType.TOKEN_BUCKET)
        
        assert "/api/users" in config.route_configs
        assert "/api/posts" in config.route_configs
        assert config.route_configs["/api/users"] == RateLimitType.TOKEN_BUCKET
        assert config.route_configs["/api/posts"] == RateLimitType.TOKEN_BUCKET
    
    def test_exempt_route(self):
        """Test exempting a route from rate limiting."""
        config = RateLimitConfig()
        
        # Exempt a route
        config.exempt_route("/api/public")
        
        assert "/api/public" in config.exempt_paths
    
    def test_get_limit_type_for_path_exempt(self):
        """Test getting limit type for an exempt path."""
        config = RateLimitConfig()
        
        # Default exempt path
        assert config.get_limit_type_for_path("/health") == RateLimitType.NONE
        
        # Custom exempt path
        config.exempt_route("/api/public")
        assert config.get_limit_type_for_path("/api/public") == RateLimitType.NONE
    
    def test_get_limit_type_for_path_configured(self):
        """Test getting limit type for a configured path."""
        config = RateLimitConfig()
        
        # Configure some paths
        config.set_limit_for_route("/api/users", RateLimitType.TOKEN_BUCKET)
        config.set_limit_for_route("/api/posts", RateLimitType.FIXED_WINDOW)
        
        # Exact path match
        assert config.get_limit_type_for_path("/api/users") == RateLimitType.TOKEN_BUCKET
        assert config.get_limit_type_for_path("/api/posts") == RateLimitType.FIXED_WINDOW
        
        # Prefix match
        assert config.get_limit_type_for_path("/api/users/123") == RateLimitType.TOKEN_BUCKET
        assert config.get_limit_type_for_path("/api/posts/trending") == RateLimitType.FIXED_WINDOW
    
    def test_get_limit_type_for_path_default(self):
        """Test getting limit type for an unconfigured path."""
        config = RateLimitConfig()
        
        # Default is NONE
        assert config.get_limit_type_for_path("/unknown/path") == RateLimitType.NONE
        
        # Change default and test again
        config.default_limit_type = RateLimitType.TOKEN_BUCKET
        assert config.get_limit_type_for_path("/unknown/path") == RateLimitType.TOKEN_BUCKET
    
    def test_path_prefix_priority(self):
        """Test that longer path prefixes take priority over shorter ones."""
        config = RateLimitConfig()
        
        # Configure paths with different lengths
        config.set_limit_for_route("/api", RateLimitType.TOKEN_BUCKET)
        config.set_limit_for_route("/api/users", RateLimitType.FIXED_WINDOW)
        
        # The more specific path should take priority
        assert config.get_limit_type_for_path("/api/users/123") == RateLimitType.FIXED_WINDOW
        assert config.get_limit_type_for_path("/api/posts") == RateLimitType.TOKEN_BUCKET 