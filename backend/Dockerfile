# Multi-stage build for QuantCAI backend
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Copy dependencies from builder
COPY --from=builder /home/app/.local /home/app/.local

# Copy application code
COPY --chown=app:app . .

# Ensure PATH includes user binaries
ENV PATH=/home/app/.local/bin:$PATH

# Environment
ENV ENV=production
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]