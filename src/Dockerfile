# syntax=docker/dockerfile:1.4

# ===============
# Step 1: Builder
# ===============
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /usr/src

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        pkg-config

COPY pyproject.toml ./
RUN mkdir -p apps core && touch README.md apps/__init__.py core/__init__.py

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-build-isolation .

# ===============
# Step 2: Runtime
# ===============
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /usr/src

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        curl

COPY --from=builder /usr/local /usr/local

COPY . /usr/src

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "60"]
