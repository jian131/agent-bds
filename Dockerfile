# Backend Dockerfile - Python 3.12 + Playwright
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
  gcc \
  libpq-dev \
  curl \
  wget \
  gnupg \
  # Playwright dependencies
  libnss3 \
  libnspr4 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libcups2 \
  libdrm2 \
  libdbus-1-3 \
  libxkbcommon0 \
  libatspi2.0-0 \
  libxcomposite1 \
  libxdamage1 \
  libxfixes3 \
  libxrandr2 \
  libgbm1 \
  libasound2 \
  libpango-1.0-0 \
  libcairo2 \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/chroma /app/logs /app/credentials

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
