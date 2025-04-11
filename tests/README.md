# Rate Limiter Tests

This directory contains tests for the rate limiter implementation.

## Test Structure

- **Unit Tests**: Tests for individual components
  - `tests/unit/middleware/rate_limiter/token_bucket/`: Tests for the token bucket algorithm
  - `tests/unit/middleware/rate_limiter/fixed_window/`: Tests for the fixed window counter algorithm
  - `tests/unit/middleware/rate_limiter/`: Tests for the config and unified limiter

- **Integration Tests**: Tests for the integration of components
  - `tests/integration/`: Integration tests for the middleware with FastAPI

## Running Tests

### Prerequisites

Make sure you have the required dependencies:

```bash
pip install -r requirements.txt
```

### Running All Tests

```bash
pytest
```

### Running Unit Tests Only

```bash
pytest tests/unit/
```

### Running Integration Tests Only

```bash
pytest tests/integration/
```

### Running Tests for a Specific Module

```bash
# Token bucket tests
pytest tests/unit/middleware/rate_limiter/token_bucket/test_token_bucket.py

# Fixed window tests
pytest tests/unit/middleware/rate_limiter/fixed_window/test_fixed_window.py

# Config tests
pytest tests/unit/middleware/rate_limiter/test_config.py
```

### Running Tests with Coverage

```bash
pytest --cov=app tests/
```

### Troubleshooting

If you encounter module import errors such as `import file mismatch`, try clearing the cache:

```bash
# Remove Python cache files
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

# Then run the tests again
pytest
```

## Test Coverage

The tests cover:

1. **Token Bucket Algorithm**:
   - Initialization with default and custom parameters
   - Token refill mechanism based on elapsed time
   - Consumption of tokens with success and failure cases
   - Thread safety

2. **Fixed Window Counter Algorithm**:
   - Initialization with default and custom parameters
   - Window key calculation and transitions
   - Request counting and rate limiting
   - Thread safety

3. **Configuration System**:
   - Route configuration
   - Path matching and priority
   - Default settings and exemptions

4. **Integration**:
   - End-to-end tests with FastAPI
   - Different rate limiting strategies
   - Runtime configuration changes 