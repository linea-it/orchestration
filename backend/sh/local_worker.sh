#!/bin/bash --login

set -o errexit
set -o pipefail
set -o nounset

envfile="${BASE_DIR}/sh/env.sh"

# shellcheck disable=SC1090
source "${envfile}"

host=$(hostname)

sleep 5

echo "Starting Celery Worker"

rm -rf /tmp/local-*.pid

celery -A orchestration worker -Q local,"local.${host}" \
    -l "${LOGGING_LEVEL}" \
    --pidfile="/tmp/local-%n.pid" \
    --logfile="${LOG_DIR}/local.${host}%I.log" \
    --pool="processes" \
    --concurrency=2
