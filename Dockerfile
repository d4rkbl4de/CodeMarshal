# Dockerfile - Production Build
# CodeMarshal Container Image
# Multi-stage build for smaller production image

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Install additional dependencies for search functionality
RUN pip install --no-cache-dir --prefix=/install \
    ripgrep-binary \
    pyyaml \
    psutil

# Copy application code
COPY . .

# Stage 2: Runtime
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    CODEMARSHAL_HOME=/data

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ripgrep \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application
COPY . /app

# Create storage directories
RUN mkdir -p /data/.codemarshal \
    /data/storage \
    /data/config \
    /data/projects

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r codemarshal && \
    useradd -r -g codemarshal -s /bin/bash codemarshal && \
    chown -R codemarshal:codemarshal /data /app

# Switch to non-root user
USER codemarshal

# Volume for persistent data
VOLUME ["/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from bridge.commands import execute_search; print('OK')" || exit 1

# Default entrypoint
ENTRYPOINT ["python", "-m", "bridge.entry.cli"]

# Default command shows help
CMD ["--help"]
