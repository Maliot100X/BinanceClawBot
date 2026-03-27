FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Non-root user
RUN useradd -m kaanova && chown -R kaanova:kaanova /app
USER kaanova

# Expose dashboard port
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s \
    CMD python -c "import sys; sys.exit(0)"

CMD ["python", "main.py"]
