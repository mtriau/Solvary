FROM python:3.13-slim

# Non-root from the start
RUN groupadd -r solvary && useradd -r -g solvary solvary

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts

USER solvary

EXPOSE 8010

# Liveness only — orchestrators should gate traffic on /api/ready
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8010/api/health', timeout=4)"]

# Migrations run before the server starts: production is migrations-only
# (lifespan create_all is disabled when ENVIRONMENT=production).
# Single worker by design — the job queue, SSE broker, and collab rooms are
# in-process until the Redis backplane lands (design phase 2).
CMD ["sh", "-c", "python -m alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8010"]
