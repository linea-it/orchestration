#!/bin/bash --login

set -o errexit
set -o pipefail
set -o nounset

envfile="${BASE_DIR}/sh/env.sh"

# shellcheck disable=SC1090
source "${envfile}"

host=$(hostname)

sleep 10

echo "Starting Celery Worker"

rm -f '/tmp/local-celery*.pid'
rm -f '/tmp/local-celery.pid'
celery -A orchestration worker -Q local,"local.${host}" \
    -l INFO \
    --pidfile="/tmp/local-%n.pid" \
    --logfile="${LOG_DIR}/local.${host}%I.log" \
    --pool="processes" \
    --concurrency=2
