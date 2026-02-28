FROM python:3.12-slim

# Install FFmpeg and other system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p /tmp/video-fx-uploads /tmp/video-fx-outputs

# Expose port
EXPOSE 8080

# Run the application
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
