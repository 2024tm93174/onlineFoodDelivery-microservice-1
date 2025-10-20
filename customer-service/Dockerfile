# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

# Faster, calmer Python & pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=180

WORKDIR /app
COPY requirements.txt .

# If any package ever falls back to source, uncomment the block below.
# Keeps image slightly larger but avoids obscure build failures.
# RUN apt-get update && apt-get install -y --no-install-recommends \
#       build-essential curl \
#   && rm -rf /var/lib/apt/lists/*

# Prefer wheels, cache downloads across builds, retry & extend timeouts
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip wheel setuptools && \
    pip install --prefer-binary --timeout=180 --retries=5 -r requirements.txt

COPY app ./app

EXPOSE 80
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]


