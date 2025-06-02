#!/usr/bin/env sh
# entrypoint.sh - make media dir

if [ "$(id -u)" -eq 0 ]; then
  mkdir -p /app/media
  chown -R appuser:appuser /app/media
  exec gosu appuser "$0" "$@"
fi

# Execute the command passed into this script
exec "$@"