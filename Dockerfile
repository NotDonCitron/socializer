# Multi-stage Dockerfile for Socializer

FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application code
COPY socializer/ ./socializer/
COPY socializer-api/ ./socializer-api/

# Install Python packages
RUN pip install --no-cache-dir -e ./socializer/ -e ./socializer-api/

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Development stage
FROM base as development
RUN pip install --no-cache-dir black ruff pytest pytest-asyncio pytest-cov pre-commit
CMD ["uvicorn", "socializer_api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "socializer_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
