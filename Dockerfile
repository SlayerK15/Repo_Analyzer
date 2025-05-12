FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    libmagic1 \
    gcc \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.0

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not use virtualenvs inside Docker
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the port the app will run on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.tech_extraction.api.main:app", "--host", "0.0.0.0", "--port", "8000"]