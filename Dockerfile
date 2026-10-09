# syntax=docker/dockerfile:1
# Production image: gunicorn behind a proxy that terminates TLS. Static files are collected at build
# time and served by WhiteNoise; uploaded photos live in the /data volume.

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Dependencies first: this layer only changes with the lock file.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project
COPY pyproject.toml uv.lock README.md manage.py ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-editable
# A throwaway key: collectstatic needs settings to load, not a real secret.
RUN DJANGO_SECRET_KEY=build-only DJANGO_STATIC_ROOT=/app/staticfiles .venv/bin/python manage.py collectstatic --noinput

FROM python:3.14-slim-bookworm
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=adote.config.settings \
    DJANGO_STATIC_ROOT=/app/staticfiles \
    DJANGO_MEDIA_ROOT=/data/media \
    DATABASE_URL=sqlite:////data/db.sqlite3
RUN useradd --system --uid 10001 --no-create-home adote && mkdir -p /data/media && chown -R adote /data
WORKDIR /app
COPY --from=build /app/.venv ./.venv
COPY --from=build /app/staticfiles ./staticfiles
COPY manage.py scripts/docker-entrypoint.sh scripts/healthcheck.py ./
USER adote
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 CMD ["python", "healthcheck.py"]
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "adote.config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", \
     "--access-logfile", "-", "--forwarded-allow-ips", "*"]
