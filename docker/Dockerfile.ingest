# Start from Python base image
FROM python:3.11-slim

# Set environment vars for Poetry (no virtualenv inside Docker)
ENV POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

# Install curl and Poetry
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get remove -y curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Set working directory
WORKDIR /app

# Copy only relevant files for dependency install first
COPY ./pyproject.toml ./
COPY ./poetry.lock ./ 

# Install dependencies
RUN poetry install

# Copy actual service code and shared code
COPY ./api ./api
COPY ./shared ./shared
COPY ./realtimeresults_config.json ./realtimeresults_config.json

# Expose port
EXPOSE 8000

# Start the FastAPI app
CMD ["python",  "-m", "shared.helpers.cli", "--runservice", "api.ingest.main:app", "--config", "./realtimeresults_config.json"]
