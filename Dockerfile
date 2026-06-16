FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create directories for data and logs
RUN mkdir -p /app/data /app/logs /app/evidence

# Expose port
EXPOSE 8080

# Run Flask web UI
CMD ["python3", "web/app.py"]
