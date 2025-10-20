FROM python:3.11-slim

# Faster, calmer Python & pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=180

WORKDIR /app
COPY requirements.txt .

# Optional build deps (leave commented unless a wheel needs compiling)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#       build-essential curl \
#   && rm -rf /var/lib/apt/lists/*

# Prefer wheels, cache downloads, retry, and extend timeouts
# (the cache mount needs the modern frontend; keep it simple instead)
RUN python -m pip install --upgrade pip wheel setuptools && \
    pip install --prefer-binary --timeout=180 --retries=5 -r requirements.txt

COPY app ./app

EXPOSE 80
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]


