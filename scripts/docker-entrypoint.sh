#!/bin/sh
# Migrations run on every start: they are idempotent, and the schema must match the code being started.
set -e
python manage.py migrate --noinput
exec "$@"
