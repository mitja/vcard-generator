# Multi-stage image using uv (Astral) as the package manager
# See: https://github.com/astral-sh/uv
FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS base

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime deps with uv (no optional vcard package)
# (Using a requirements.txt inline keeps Docker layer caching effective.)
RUN printf "python-fasthtml\nMonsterUI\nuvicorn\n" > requirements.txt \
 && uv pip install --system -r requirements.txt

# Copy the app
COPY app.py /app/app.py

# Non-root user (optional but recommended)
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 80

# Healthcheck: Try the root path
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python - <<'PY'\nimport urllib.request, sys\ntry:\n    with urllib.request.urlopen('http://127.0.0.1:8000', timeout=3) as r:\n        sys.exit(0 if r.status==200 else 1)\nexcept Exception:\n    sys.exit(1)\nPY

# Run with uvicorn directly (FastHTML supplies 'app' ASGI)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
