#!/bin/bash --login

source /app/sh/env.sh

set -o errexit
set -o pipefail
set -o nounset

host=$(hostname)

sleep 10 

echo "Starting Celery Worker"

rm -f '/tmp/local-celery*.pid'
rm -f '/tmp/local-celery.pid'
celery -A orchestration worker -Q local,"local.${host}" \
    -l INFO \
    --pidfile="/tmp/local-%n.pid" \
    --logfile="/logs/local.${host}%I.log" \
    --pool="processes" \
    --concurrency=2
