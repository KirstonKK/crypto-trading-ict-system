# =============================================================================
# Multi-Stage Dockerfile for Kirston's Crypto Trading System
# =============================================================================
# Stage 1: Builder - Install dependencies and compile requirements
# Stage 2: Runtime - Minimal production image
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

LABEL maintainer="Kirston's Trading System"
LABEL description="ICT Enhanced Trading Monitor with Bybit Integration"

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime
# -----------------------------------------------------------------------------
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    TZ=UTC \
    # Application paths
    APP_HOME=/app \
    # Python path
    PYTHONPATH=/app:/app/src:/app/utils:/app/backtesting

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    sqlite3 \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r trading && \
    useradd -r -g trading -u 1000 -m -s /bin/bash trading && \
    mkdir -p /app /app/data /app/logs /app/config /app/results && \
    chown -R trading:trading /app

# Copy virtual environment from builder
COPY --from=builder --chown=trading:trading /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=trading:trading . /app/

# Create necessary directories with proper permissions
RUN mkdir -p \
    /app/data/cache \
    /app/data/persistence \
    /app/data/processed \
    /app/data/raw \
    /app/data/trading_sessions \
    /app/logs \
    /app/config/credentials \
    /app/results && \
    chown -R trading:trading /app/data /app/logs /app/config /app/results

# Copy and set up entrypoint script (from docker/ subdirectory since context is project root)
COPY --chown=trading:trading docker/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy diagnostic script for troubleshooting
COPY --chown=trading:trading docker/diagnose_blue_screen.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/diagnose_blue_screen.sh

# Expose ports
# 5001 - ICT Enhanced Monitor
# 5002 - Fundamental Analysis (if enabled)
EXPOSE 5001 5002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Switch to non-root user
USER trading

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command - start ICT Enhanced Monitor
CMD ["python3", "core/monitors/ict_enhanced_monitor.py", "--port", "5001"]
