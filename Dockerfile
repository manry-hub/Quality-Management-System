# ==============================================================================
# Multi-Stage Dockerfile for QMS Automotive (Django 5.x + uv + Python 3.12)
# ==============================================================================

# Stage 1: Build & Dependency Resolution Stage
FROM ghcr.io/astral-sh/uv:0.5.26-python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install minimal build tools if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for optimal layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into virtualenv without project code
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ==============================================================================
# Stage 2: Runtime Production Image
# ==============================================================================
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Install runtime shared libraries for WeasyPrint (PDF rendering), PostgreSQL, and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and directories
RUN groupadd -r -g 1000 appgroup && \
    useradd -r -u 1000 -g appgroup -d /app -s /sbin/nologin appuser && \
    mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R appuser:appgroup /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Set environment PATH to use virtualenv directly
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE="config.settings.production"

# Copy application source code
COPY --chown=appuser:appgroup . /app/

# Switch to non-root user
USER appuser

EXPOSE 8000

# Default entrypoint runs Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
