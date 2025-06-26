#!/bin/bash

set -o errexit
set -o pipefail

# Run commands to setup

if [[ -z "${DJANGO_WAIT_FOR_DATABASE}" ]]
then
  echo "Skipping database wait"
else
  ./src/manage.py wait_for_database
fi

if [[ -z "${WAIT_FOR_HTTP}" ]]
then
  echo "No HTTP service to wait for"
else
  ./src/manage.py wait_for_http "$WAIT_FOR_HTTP"
fi

if [[ -z "${DJANGO_MIGRATE}" ]]
then
  echo "Skip migration and setup"
else
  ./src/manage.py makemigrations
  ./src/manage.py migrate
  ./src/manage.py setup
fi

if [[ -z "${DJANGO_TAILWIND}" ]]
then
  echo "Skip tailwind"
else
  ./src/manage.py tailwind install --no-input
fi

if [[ -z "${DJANGO_COLLECTSTATIC}" ]]
then
  echo "Skip collectstatic"
else
  ./src/manage.py collectstatic --noinput
fi


exec "$@"
