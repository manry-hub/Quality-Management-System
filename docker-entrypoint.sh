#!/bin/sh
set -e

# Automatically run database migrations and collect static assets on web service startup
if [ "$1" = "gunicorn" ]; then
    echo "==> Running database migrations..."
    python manage.py migrate --noinput || {
        echo "WARNING: Migration check failed; continuing to start server..."
    }
    echo "==> Collecting static assets..."
    python manage.py collectstatic --noinput || {
        echo "WARNING: Static collection failed; continuing..."
    }
    echo "==> Starting Gunicorn application server..."
fi

exec "$@"
