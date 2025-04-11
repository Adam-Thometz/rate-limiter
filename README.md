# FastAPI Rate Limiter

A FastAPI backend with configurable rate limiting implementations.

## Rate Limiting Algorithms

### 1. Token Bucket Algorithm

- Each IP gets a bucket with capacity for 10 tokens
- Tokens are added at a rate of 1 token per second
- When a request arrives and the bucket contains tokens, the request is allowed and a token is removed
- When a request arrives and the bucket is empty, the request is rejected with 429 status

### 2. Fixed Window Counter Algorithm

- Uses a fixed time window (60 seconds by default)
- Counts requests in each window
- Window is determined by the floor of the current timestamp
- If more than 10 requests occur in a window, additional requests are rejected
- Windows reset automatically when a new time period starts

## Configuration System

The application includes a flexible rate limiting configuration system:

- Configure rate limiting per route or route prefix
- Select different rate limiting algorithms for different routes
- Exempt specific routes from rate limiting
- Change configuration at runtime via API

### Configuration Methods

```python
# In code configuration
from app.rate_limit_config import rate_limit_config, RateLimitType

# Apply token bucket rate limiting to a route
rate_limit_config.set_limit_for_route("/api/users", RateLimitType.TOKEN_BUCKET)

# Apply fixed window rate limiting to a route
rate_limit_config.set_limit_for_route("/api/posts", RateLimitType.FIXED_WINDOW)

# Exempt a route from rate limiting
rate_limit_config.exempt_route("/public")

# Apply rate limiting to multiple routes at once
rate_limit_config.set_limit_for_routes(["/api/v1/users", "/api/v1/accounts"], RateLimitType.TOKEN_BUCKET)
```

### Runtime Configuration

The API includes an admin endpoint to change rate limiting configuration at runtime:

```
POST /admin/rate-limit/{path}
```

With body:
```json
{
  "limit_type": "token_bucket" 
}
```

Possible values for `limit_type`:
- `token_bucket`
- `fixed_window`
- `none` (to disable rate limiting)

## Default Configuration

The rate limiters are configured with:

**Token Bucket:**
- Bucket capacity: 10 tokens
- Refill rate: 1 token per second

**Fixed Window Counter:**
- Window size: 60 seconds (1 minute)
- Maximum requests per window: 10

## Running the Application

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Run the server:
```
uvicorn main:app --reload
```

## Testing the Rate Limiters

### Pre-configured Routes

The following routes have rate limiting pre-configured:

- Token Bucket Rate Limiting:
  - `/limited`

- Fixed Window Rate Limiting:
  - `/fixed`

- No Rate Limiting:
  - `/unlimited`
  - `/health`

### API Documentation

FastAPI provides automatic documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 