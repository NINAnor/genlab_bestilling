#!/bin/bash

set -o errexit
set -o pipefail

# Run commands to setup

manage.py wait_for_database

if [[ -z "${WAIT_FOR_HTTP}" ]]
then
  echo "No HTTP service to wait for"
else
  manage.py wait_for_http "$WAIT_FOR_HTTP"
fi

if [[ -z "${DJANGO_MIGRATE}" ]]
then
  echo "Skip migration and setup"
else
  manage.py makemigrations
  manage.py migrate
  manage.py setup
fi

if [[ -z "${DJANGO_COLLECTSTATIC}" ]]
then
  echo "Skip collectstatic"
else
  manage.py collectstatic --noinput
fi


exec "$@"
