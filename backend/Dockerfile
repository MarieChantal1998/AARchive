FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/pyproject.toml /app/pyproject.toml
COPY backend/aarchive /app/aarchive
RUN pip install --no-cache-dir .
ENV PORT=8000
CMD ["sh", "-c", "uvicorn aarchive.main:app --host 0.0.0.0 --port ${PORT}"]

