# Nyx OSINT Docker Image

FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.0 \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root --only main

# Copy application code
COPY . .

# Install application
RUN poetry install --only main

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/exports /app/.cache

# Create non-root user
RUN useradd -m -u 1000 nyx && \
    chown -R nyx:nyx /app

# Switch to non-root user
USER nyx

# Expose ports (if needed for API in future)
EXPOSE 8000

# Default command (GUI)
CMD ["poetry", "run", "nyx"]
