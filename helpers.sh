#!/bin/bash

alias dpcli_dev="docker compose --profile dev"
alias dpcli_prod="docker compose --profile prod"

alias djcli_dev="docker compose --profile dev exec -it django-dev ./src/manage.py"
alias djcli_prod="docker compose --profile prod -it django ./src/manage.py"
