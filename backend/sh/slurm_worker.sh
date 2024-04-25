#!/bin/bash --login

set -o errexit
set -o pipefail
set -o nounset

host=$(hostname)

sleep 5

echo "Starting Celery SLURM Worker"

rm -rf /tmp/slurm-*.pid

celery -A orchestration worker -Q slurm,slurm.${host} \
    -l "${LOGGING_LEVEL}" \
    --pidfile="/tmp/slurm-%n.pid" \
    --logfile="${LOG_DIR}/slurm.${host}.log" \
    --pool="solo"

