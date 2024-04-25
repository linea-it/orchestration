#!/bin/bash --login

set -o errexit
set -o pipefail
set -o nounset

envfile="${BASE_DIR}/sh/env.sh"

# shellcheck disable=SC1090
source "${envfile}"

echo "Starting Celery Worker"

rm -rf /tmp/celerybeat.pid

celery -A orchestration beat \
    -l "${LOGGING_LEVEL}" \
    -s /tmp/celerybeat-schedule \
    --pidfile="/tmp/celerybeat.pid" \
    --logfile="${LOG_DIR}/celerybeat.log" 
