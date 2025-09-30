#docker run --name dev-postgres -e POSTGRES_DB=loads_db -e POSTGRES_USER=fastoads_user -e POSTGRES_PASSWORD=msVWXPmsVWXP -p 127.0.0.1:5432:5432 -d postgres:17
#docker run -it ceasione/fastloads:latest /bin/bash
#docker run -it ceasione/fastloads:latest pytest

FROM python:3.10-slim
LABEL authors="oliver"

# Install system dependencies for Poetry and your app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set work directory
WORKDIR /fastloads

# Copy only dependency files first (for better caching)
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no dev deps, install into system site-packages instead of virtualenv)
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main --no-interaction

# Copy app code
COPY . .

RUN groupadd -g 1500 fastloads && \
    useradd -u 1500 -g fastloads -s /bin/bash fastloads && \
    chown -R fastloads:fastloads /fastloads

USER fastloads

ENV SOCKET_LOC=/tmp/docker_fastloads.sock

# Run the app with poetry (or python directly if installed system-wide)
CMD python -m uvicorn app.api:app --uds $SOCKET_LOC
