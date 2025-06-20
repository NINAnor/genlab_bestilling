#!/bin/bash

alias dpcli_dev="docker compose --profile dev"
alias dpcli_prod="docker compose --profile prod"

alias djcli_dev="docker compose exec -it django-dev ./src/manage.py"
alias djcli_prod="docker compose exec -it django ./src/manage.py"

alias deps-sync="uv sync"
alias deps-sync-prod="uv sync --profile prod --no-dev"
alias deps-outdated="uv tree --outdated --depth 1"
alias deps-lock="uv lock"
alias deps-check="uv lock --check && uv sync --check"
alias deps-up="uv lock --upgrade"

alias lint="uv run pre-commit run --all-files"
alias django="uv run ./src/manage.py"

echo "Aliases loaded successfully."

[ -f aliases-private.sh ] && . aliases-private.sh
