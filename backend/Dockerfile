# ---------- builder stage ----------
FROM python:3.12-slim AS builder

WORKDIR /app

# Upgrade pip once, cache this layer separately from deps install
RUN pip install --upgrade pip --no-cache-dir

COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.12-slim AS runtime

# Create non-root user for least-privilege execution
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=appuser:appgroup . .

ENV FLASK_APP=app.main:create_app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Prevent Python from buffering stdout/stderr in threads
    PYTHONFAULTHANDLER=1

# Switch to non-root
USER appuser

EXPOSE 5000

# Lightweight liveness probe (used by docker-compose healthcheck)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO- http://localhost:5000/api/v1/health || exit 1

# Default command — overridden by docker-compose for migrations + gunicorn
CMD ["gunicorn", "app.main:create_app()", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--worker-class", "gthread", \
     "--worker-tmp-dir", "/dev/shm", \
     "--timeout", "30", \
     "--keep-alive", "5", \
     "--access-logfile", "-"]
