FROM debian:12.5 AS base
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    apt-get update && apt-get install --no-install-recommends -yq python3 python3-pip git python3-venv python3-dev gettext curl


WORKDIR /app
RUN python3 -m venv .venv
ENV PYTHONPATH=/app/.venv/lib
ENV PATH=/app/.venv/bin:$PATH
COPY ./pyproject.toml .
COPY src/manage.py src/
RUN pip install -e .

FROM base AS base-node
RUN curl -fsSL https://deb.nodesource.com/setup_20.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
  --mount=target=/var/cache/apt,type=cache,sharing=locked \
  apt-get update && apt-get install -y --fix-missing nodejs


FROM scratch AS source
WORKDIR /app
COPY src src


FROM node:20 AS frontend-base
WORKDIR /app
COPY src/frontend/package.json src/frontend/package-lock.json .
RUN npm install


FROM frontend-base AS frontend
COPY src/frontend/src src
COPY src/frontend/vite.config.js src/frontend/.eslintrc.cjs .

FROM frontend AS frontend-prod
RUN npm run build


FROM base AS production
RUN pip install -e .[prod]


# Compile the translations for multilanguage
FROM base AS translation
COPY --from=source /app .
RUN DATABASE_URL="" \
  DJANGO_SETTINGS_MODULE="config.settings.test" \
  manage.py compilemessages -l no

FROM base-node AS tailwind
COPY --from=source /app .
RUN DATABASE_URL="" \
  DJANGO_SETTINGS_MODULE="config.settings.test" \
  manage.py tailwind install
RUN DATABASE_URL="" \
  DJANGO_SETTINGS_MODULE="config.settings.test" \
  manage.py tailwind build


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
RUN pip install -e .[dev]
RUN python -m playwright install
RUN python -m playwright install-deps

COPY --from=django /app/src src
COPY --from=translation /app/src/locale /app/src/locale
COPY --from=django /app/entrypoint.sh .
COPY entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
