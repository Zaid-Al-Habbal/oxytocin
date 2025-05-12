#!/usr/bin/env sh

# entrypoint.sh - waits for the database, runs migrations, then starts Django server

if [ "$(id -u)" -eq 0 ]; then
  mkdir -p /app/media
  chown -R appuser:appuser /app/media
  exec gosu appuser "$0" "$@"
fi

set -e

FLAG=/tmp/.migrations_applied

if [ ! -f "$FLAG" ]; then
  echo "==> Applying migrations…"
  until python manage.py migrate --noinput; do
    echo "   Database not ready, retrying…"
    sleep 1
  done
  touch "$FLAG"
else
  echo "==> Migrations already applied, skipping."
fi

# Use exec so SIGTERM/SIGINT are forwarded properly
exec python manage.py runserver 0.0.0.0:8000

