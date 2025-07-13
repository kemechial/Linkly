#!/bin/sh
# wait-for-postgres.sh

set -e

host="db"
cmd="$@"

# This loop will continue until postgres is ready.
# pg_isready is a utility from the postgresql-client package.
# It checks if a connection can be established.
# We are using the POSTGRES_USER environment variable passed from the .env file.
until pg_isready -h "$host" -U "${POSTGRES_USER}" -q; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
# The `exec` command replaces the shell process with the command,
# so your application becomes the main process (PID 1) in the container.
exec $cmd