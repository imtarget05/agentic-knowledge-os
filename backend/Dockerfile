# --- Stage 1: Builder stage ---
FROM python:3.11-slim AS builder

WORKDIR /build

# Install dependencies needed for compiling python libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create a virtual environment but install directly, or keep them structured
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# --- Stage 2: Runtime stage ---
FROM python:3.11-slim AS runtime

WORKDIR /workspace

# Copy installed python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY app ./app

EXPOSE 8000

ENV PORT=8000
ENV HOST="0.0.0.0"

CMD ["python", "-m", "app.main"]
