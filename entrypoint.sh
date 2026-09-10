#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py createcachetable || true
python manage.py collectstatic --noinput

exec gunicorn desafio_eqs.wsgi:application --bind 0.0.0.0:8000 --workers 3
