FROM debian:12.5 as base
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    apt-get update && apt-get install --no-install-recommends -yq python3 python3-pip git python3-venv python3-dev gettext







WORKDIR /app
RUN python3 -m venv .venv
ENV PYTHONPATH=/app/.venv/lib
ENV PATH=/app/.venv/bin:$PATH
COPY ./pyproject.toml .
COPY src/manage.py src/
RUN pip install -e .


FROM scratch as source
WORKDIR /app
COPY src src

# SCSS build - bootstrap customization
FROM node:14 AS theme
WORKDIR /app
COPY theme/package.json .
RUN npm i -g gulp
RUN npm install
COPY theme/src src
COPY theme/gulpfile.js .
COPY src/static static
RUN gulp build


FROM base as production
RUN pip install -e .[prod]


# Compile the translations for multilanguage
FROM base as translation
COPY --from=source /app .
RUN DATABASE_URL="" DJANGO_BASE_SCHEMA_URL="" \
  DJANGO_SETTINGS_MODULE="config.settings.test" \
  manage.py compilemessages

FROM base as django
COPY --from=production /app .
COPY --from=translation /app/src/locale /app/src/locale
COPY --from=source /app .
COPY --from=theme /app/static src/static
RUN mkdir media
COPY entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]

FROM base as dev
RUN pip install -e .[dev]

COPY --from=django /app/src src
COPY --from=translation /app/src/locale /app/src/locale
COPY --from=django /app/entrypoint.sh .
COPY entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
