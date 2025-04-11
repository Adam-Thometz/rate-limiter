import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import time
from unittest.mock import patch
from app.middleware.rate_limiter.unified_limiter import unified_rate_limit_middleware
from app.middleware.rate_limiter.rate_limit_config import rate_limit_config, RateLimitType

# Reset the rate limit configuration for each test
@pytest.fixture(autouse=True)
def reset_rate_limit_config():
    rate_limit_config.route_configs = {}
    rate_limit_config.default_limit_type = RateLimitType.NONE
    rate_limit_config.exempt_paths = {"/health", "/docs", "/redoc", "/openapi.json"}

# Create a test FastAPI app with our middleware
@pytest.fixture
def app():
    app = FastAPI()
    app.middleware("http")(unified_rate_limit_middleware)
    
    @app.get("/")
    async def root():
        return {"message": "Welcome to the rate limiter test"}
    
    @app.get("/token-bucket")
    async def token_bucket():
        return {"message": "Token bucket endpoint"}
    
    @app.get("/fixed-window")
    async def fixed_window():
        return {"message": "Fixed window endpoint"}
    
    @app.get("/unlimited")
    async def unlimited():
        return {"message": "Unlimited endpoint"}
    
    @app.get("/dynamic")
    async def dynamic():
        return {"message": "Dynamic endpoint"}
    
    # Configure rate limiting for routes
    rate_limit_config.set_limit_for_route("/token-bucket", RateLimitType.TOKEN_BUCKET)
    rate_limit_config.set_limit_for_route("/fixed-window", RateLimitType.FIXED_WINDOW)
    rate_limit_config.set_limit_for_route("/unlimited", RateLimitType.NONE)
    
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

class TestRateLimiterMiddleware:
    
    def test_unlimited_endpoint(self, client):
        """Test that unlimited endpoints have no rate limiting."""
        # Make multiple requests to the unlimited endpoint
        for _ in range(20):
            response = client.get("/unlimited")
            assert response.status_code == 200
            assert response.json() == {"message": "Unlimited endpoint"}
    
    def test_token_bucket_rate_limiting(self, client, monkeypatch):
        """Test token bucket rate limiting."""
        # Patch time.time to return a fixed value for consistency
        monkeypatch.setattr(time, "time", lambda: 1000.0)
        
        # Make requests up to the limit (10)
        for i in range(10):
            response = client.get("/token-bucket", headers={"X-Forwarded-For": "192.168.1.1"})
            assert response.status_code == 200, f"Request {i+1} should be allowed"
        
        # The next request should be rate limited
        response = client.get("/token-bucket", headers={"X-Forwarded-For": "192.168.1.1"})
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
        
        # Reset the client IP tracking for the token bucket
        from app.middleware.rate_limiter.token_bucket import token_bucket
        token_bucket.buckets = {}
        
        # A different client IP should not be rate limited
        response = client.get("/token-bucket", headers={"X-Forwarded-For": "192.168.1.2"})
        assert response.status_code == 200
    
    def test_fixed_window_rate_limiting(self, client, monkeypatch):
        """Test fixed window rate limiting."""
        # Patch time.time to return a fixed value for consistency
        monkeypatch.setattr(time, "time", lambda: 3600.0)
        
        # Make requests up to the limit (10)
        for i in range(10):
            response = client.get("/fixed-window", headers={"X-Forwarded-For": "192.168.1.1"})
            assert response.status_code == 200, f"Request {i+1} should be allowed"
        
        # The next request should be rate limited
        response = client.get("/fixed-window", headers={"X-Forwarded-For": "192.168.1.1"})
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
        
        # Move to the next window
        monkeypatch.setattr(time, "time", lambda: 3660.0)
        
        # Should be allowed again in the new window
        response = client.get("/fixed-window", headers={"X-Forwarded-For": "192.168.1.1"})
        assert response.status_code == 200
    
    def test_runtime_config_change(self, client, monkeypatch):
        """Test changing rate limit configuration at runtime."""
        # Initially unlimited
        rate_limit_config.set_limit_for_route("/dynamic", RateLimitType.NONE)
        
        response = client.get("/dynamic")
        assert response.status_code == 200
        
        # Change to token bucket
        rate_limit_config.set_limit_for_route("/dynamic", RateLimitType.TOKEN_BUCKET)
        
        # Reset any existing buckets
        from app.middleware.rate_limiter.token_bucket import token_bucket
        token_bucket.buckets = {}
        
        # Fix the time for consistent testing
        monkeypatch.setattr(time, "time", lambda: 1000.0)
        
        # Make requests up to the limit (10)
        for i in range(10):
            response = client.get("/dynamic", headers={"X-Forwarded-For": "192.168.1.1"})
            assert response.status_code == 200, f"Request {i+1} should be allowed"
        
        # The next request should be rate limited
        response = client.get("/dynamic", headers={"X-Forwarded-For": "192.168.1.1"})
        assert response.status_code == 429
        
        # Change back to unlimited
        rate_limit_config.set_limit_for_route("/dynamic", RateLimitType.NONE)
        
        # Should be allowed again
        response = client.get("/dynamic", headers={"X-Forwarded-For": "192.168.1.1"})
        assert response.status_code == 200 