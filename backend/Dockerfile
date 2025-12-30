FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directories
RUN mkdir -p storage/products storage/references storage/temp

# Expose port
EXPOSE 8000

# Run migrations, fix missing columns, and start the application
CMD ["sh", "-c", "echo 'Current migration state:' && alembic current && echo 'Running migrations...' && alembic upgrade head && echo 'Fixing missing columns...' && python fix_missing_columns.py && echo 'Startup complete!' && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
