FROM debian:12.5 AS base
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    apt-get update && apt-get install --no-install-recommends -yq python3 python3-pip git python3-dev gettext curl

# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV PYTHONPATH=/app/.venv/lib
ENV PATH=/app/.venv/bin:$PATH
COPY ./pyproject.toml uv.lock ./
COPY src/manage.py src/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-dev

FROM base AS base-node
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get update && \
    apt-get install -y --fix-missing nodejs


FROM scratch AS source
WORKDIR /app
COPY src src


FROM node:22-slim AS frontend-base
WORKDIR /app
COPY src/frontend/package.json src/frontend/package-lock.json ./
RUN npm install


FROM frontend-base AS frontend
COPY src/frontend/src src
COPY src/frontend/vite.config.js src/frontend/.eslintrc.cjs ./

FROM frontend AS frontend-prod
RUN npm run build


FROM base AS production

# Compile the translations for multilanguage
FROM base AS translation
COPY --from=source /app .
RUN DATABASE_URL="" \
  DJANGO_SETTINGS_MODULE="config.settings.test" \
  ./src/manage.py compilemessages -l no

FROM base-node AS tailwind
COPY --from=source /app .
RUN DATABASE_URL="" \
  DJANGO_SETTINGS_MODULE="config.settings.test" \
  ./src/manage.py tailwind install
RUN DATABASE_URL="" \
  DJANGO_SETTINGS_MODULE="config.settings.test" \
  ./src/manage.py tailwind build


FROM base AS django
COPY --from=production /app .
COPY --from=translation /app/src/locale /app/src/locale
COPY --from=source /app .
COPY --from=tailwind /app/src/theme/static /app/src/theme/static
COPY --from=frontend-prod /app/static /app/src/frontend/static
RUN mkdir media
COPY entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]

FROM base-node AS dev
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=cache,target=/root/.cache/ms-playwright \
  uv sync --locked && \
  uv run playwright install && uv run playwright install-deps

COPY --from=django /app/src src
COPY --from=translation /app/src/locale /app/src/locale
COPY --from=django /app/entrypoint.sh .
COPY entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
