FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Expose port
EXPOSE 8000

# Wait for database and run migrations, then start server
CMD ["sh", "-c", "until pg_isready -h postgres -p 5432 -U lineuplab; do sleep 2; done && alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]

