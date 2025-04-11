from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.middleware.rate_limiter.config import RateLimitType, rate_limit_config
from app.middleware.rate_limiter.token_bucket import token_bucket
from app.middleware.rate_limiter.fixed_window import fixed_window_counter
from app.middleware.rate_limiter.sliding_window import sliding_window
async def unified_rate_limit_middleware(request: Request, call_next):
    """
    Unified middleware that handles multiple rate limiting strategies based on configuration.
    """
    path = request.url.path
    client_ip = request.client.host
    
    # Determine which rate limiting strategy to use based on the path
    limit_type = rate_limit_config.get_limit_type_for_path(path)
    
    # Apply rate limiting based on the determined strategy
    if limit_type == RateLimitType.TOKEN_BUCKET:
        if not token_bucket.consume(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again later."}
            )
    elif limit_type == RateLimitType.FIXED_WINDOW:
        if not fixed_window_counter.is_allowed(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again when the current window expires."}
            )
    # If NONE or any other type, no rate limiting is applied
    
    # Process the request if rate limit not exceeded or not applicable
    response = await call_next(request)
    return response 