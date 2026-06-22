FROM python:3.11-slim

WORKDIR /app/warmth

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md __init__.py ./
COPY apps ./apps
COPY packages ./packages
COPY infra ./infra
COPY services ./services

RUN uv pip install --system -e .

COPY data ./data

ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

CMD uvicorn warmth.apps.api.main:app --host 0.0.0.0 --port ${PORT}
