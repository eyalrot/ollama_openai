# Build stage
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 proxyuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/proxyuser/.local

# Copy application code
COPY --chown=proxyuser:proxyuser src/ ./src/

# Set environment variables
ENV PATH=/home/proxyuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Switch to non-root user
USER proxyuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; import sys; sys.exit(0 if httpx.get('http://localhost:${PROXY_PORT:-11434}/health').status_code == 200 else 1)"

# Expose port
EXPOSE 11434

# Run the application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "11434"]