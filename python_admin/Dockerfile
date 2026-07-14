FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for Prisma and async DB drivers
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Download the latest installer for uv (fast Python package manager)
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the PATH
ENV PATH="/root/.local/bin/:$PATH"

# Copy the requirements file first (for Docker layer caching)
COPY requirements.txt .

# Install dependencies using uv (significantly faster than pip)
RUN uv pip install --system -r requirements.txt

# Copy the rest of the application
COPY . .

# Generate Prisma client from the Python-specific schema
RUN python generate_prisma.py && prisma generate --schema=schema_py.prisma

# Expose the application port
EXPOSE 8000

# Set production environment
ENV ENVIRONMENT=production

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Health check — Render uses this to verify the service is healthy
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with Gunicorn + Uvicorn workers
# IMPORTANT: -w 1 (single worker) is REQUIRED because APScheduler runs
# the bi-hourly marketing loop. Multiple workers would cause duplicate
# social posts and email blasts.
CMD ["gunicorn", "main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
