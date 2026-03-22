FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY data/ ./data/
COPY logs/ ./logs/
COPY portfolio/ ./portfolio/

# Create necessary directories
RUN mkdir -p logs data portfolio reports

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "app/api_server.py"]