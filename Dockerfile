# Dockerfile - Production Build
# CodeMarshal container image with PDF export support.

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Build tools required for some Python wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy source and install package + PDF extras into a staging prefix.
COPY . /build
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install ".[export_pdf]"

# Stage 2: Runtime
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    CODEMARSHAL_HOME=/data

# Runtime dependencies include libraries required by WeasyPrint.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ripgrep \
    git \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder.
COPY --from=builder /install /usr/local

# Copy application source.
COPY . /app

# Create storage directories.
RUN mkdir -p /data/.codemarshal \
    /data/storage \
    /data/config \
    /data/projects

WORKDIR /app

# Create non-root user for security.
RUN groupadd -r codemarshal && \
    useradd -r -g codemarshal -s /bin/bash codemarshal && \
    chown -R codemarshal:codemarshal /data /app

USER codemarshal

VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from bridge.commands import execute_search; print('OK')" || exit 1

ENTRYPOINT ["python", "-m", "bridge.entry.cli"]
CMD ["--help"]
