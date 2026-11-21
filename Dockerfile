# CapSense production image: builds the React frontend, then serves it and the API with gunicorn.

# ---- 1. Build the React frontend ----
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- 2. Python app ----
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app/ app/
COPY data/ data/
COPY scripts/ scripts/
COPY run.py ./
COPY --from=frontend /frontend/dist frontend/dist

# Run as a non-root user.
RUN useradd --create-home capsense && mkdir -p instance && chown capsense instance
USER capsense

# One worker process on purpose: students' session-only API keys live in this process's
# memory, so every request must reach the same process. Threads handle concurrency.
# The long timeout leaves room for AI requests made with a student's own key.
CMD gunicorn run:app --workers 1 --threads 8 --timeout 180 --bind 0.0.0.0:${PORT:-10000} --access-logfile -
