# ── Stage: base Python image ──────────────────────────────────────────────────
# python:3.12-slim is a minimal Debian image with Python pre-installed.
# We use slim (not alpine) because psycopg2 needs glibc which alpine lacks.
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# ── Install system dependencies ───────────────────────────────────────────────
# libpq-dev: required to compile psycopg2 (PostgreSQL adapter)
# gcc: C compiler needed for some Python packages
# We clean up apt cache afterwards to keep the image small
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Install Python dependencies ───────────────────────────────────────────────
# Copy requirements first (before app code) so Docker can cache this layer.
# If you change app code but not requirements.txt, Docker reuses this cached
# layer and skips the slow pip install step.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application code ─────────────────────────────────────────────────────
COPY . .

# ── Runtime config ────────────────────────────────────────────────────────────
# Tell Python not to buffer stdout/stderr so logs appear immediately in Docker
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# The port Flask/Gunicorn will listen on inside the container
EXPOSE 5000

# Default command: start Gunicorn with 2 worker processes
# This is overridden per-service in docker-compose.yml
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "wsgi:app"]
