#!/bin/sh
# wait-for-postgres.sh

set -e

host="$1"
shift
cmd="$@"

# We need the psql client to be installed in the app image for this to work.
# The 'until' loop will try to connect until it succeeds.
until PGPASSWORD=$POSTGRES_PASSWORD pg_isready -h "$host" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
# Once the DB is up, execute the command that was passed to the script.
exec $cmd