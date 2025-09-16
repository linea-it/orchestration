#!/bin/bash --login

set -o errexit
set -o pipefail
set -o nounset

host=$(hostname)

sleep 5

slurmname="${WORKER_NAME}"

echo "Starting Celery SLURM Worker: ${slurmname} on host ${host}"

rm -rf /tmp/${slurmname}-*.pid

cd $BASE_DIR/backend

celery -A orchestration worker -Q "${slurmname}","${slurmname}"."${host}" \
    -l "${LOGGING_LEVEL}" \
    --pidfile="/tmp/${slurmname}-%n.pid" \
    --logfile="${LOG_DIR}/${slurmname}.${host}.log" \
    --pool="processes" \
    --concurrency=2

