#!/bin/bash --login

envfile="${BASE_DIR}/sh/env.sh"

# shellcheck disable=SC1090
source "${envfile}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

# Para produção é necessário usar o uWSGI!
# uWSGI para servir o app e ter compatibilidade com Shibboleth
# https://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html
uwsgi \
    --socket 0.0.0.0:8000 \
    --wsgi-file ${BASE_DIR}/orchestration/wsgi.py \
    --module orchestration.wsgi:application \
    --buffer-size=32768 \
    --processes=1 \
    --threads=1 \
    --static-map /django_static=${BASE_DIR}/django_static \
    --py-autoreload=${AUTORELOAD:-0}