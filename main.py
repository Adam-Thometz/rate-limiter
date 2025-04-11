from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.rate_limiter.unified_limiter import unified_rate_limit_middleware
from app.middleware.rate_limiter.config import rate_limit_config, RateLimitType

app = FastAPI(
    title="FastAPI Backend",
    description="A boilerplate FastAPI backend",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add unified rate limiting middleware
app.middleware("http")(unified_rate_limit_middleware)

# Configure rate limiting for routes - this could also be loaded from config file

rate_limit_config.set_limit_for_route("/", RateLimitType.NONE)
@app.get("/")
async def root():
    return {"message": "Welcome to the rate limiter test"}

rate_limit_config.set_limit_for_route("/token-bucket", RateLimitType.TOKEN_BUCKET)
@app.get("/token-bucket")
async def limited():
    return {"message": "Limited by token bucket, don't over use me!"}

rate_limit_config.set_limit_for_route("/fixed-window", RateLimitType.FIXED_WINDOW)
@app.get("/fixed-window")
async def fixed_window():
    return {"message": "Limited by fixed window, only 10 requests per minute!"}

rate_limit_config.set_limit_for_route("/unlimited", RateLimitType.NONE)
@app.get("/unlimited")
async def unlimited():
    return {"message": "Unlimited! Let's Go!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)