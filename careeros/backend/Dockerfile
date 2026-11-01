# CareerOS AI Backend Dockerfile
# Multi-stage build: build stage + runtime stage

FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim AS runtime

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r careeros && useradd -r -g careeros careeros

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create data directory for SQLite (dev) / uploads
RUN mkdir -p /app/data /app/uploads && \
    chown -R careeros:careeros /app

USER careeros

# Environment variables with defaults
ENV DATABASE_URL=sqlite:///./data/careeros.db
ENV SECRET_KEY=change-me-in-production
ENV JWT_ALGORITHM=HS256
ENV ACCESS_TOKEN_EXPIRE_MINUTES=30
ENV FRONTEND_URL=http://localhost:5173
ENV LLM_PROVIDER=auto
ENV GEMINI_MODEL=gemini-1.5-flash
ENV GEMINI_TEMPERATURE=0.3
ENV GEMINI_MAX_TOKENS=4096
ENV VECTOR_STORE_BACKEND=pgvector
ENV LOG_LEVEL=INFO

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
