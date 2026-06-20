FROM python:3.10-slim

WORKDIR /app/warmth

RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml README.md __init__.py ./
COPY apps ./apps
COPY packages ./packages
COPY infra ./infra

RUN uv pip install --system -e .

COPY data ./data

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "warmth.apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
