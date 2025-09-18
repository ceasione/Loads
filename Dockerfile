
FROM python:3.10-slim
LABEL authors="oliver"

# Install system dependencies for Poetry and your app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (for better caching)
COPY pyproject.toml poetry.lock* ./

# Install Poetry
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /fastloads

# Install dependencies (no dev deps, install into system site-packages instead of virtualenv)
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main --no-interaction

# Copy app code
COPY . .

# Run the app with poetry (or python directly if installed system-wide)
CMD ["poetry", "run", "python", "-m", "uvicorn", "app.api:app"]
