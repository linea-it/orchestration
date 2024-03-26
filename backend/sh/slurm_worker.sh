#!/bin/bash --login

set -o errexit
set -o pipefail
set -o nounset

echo "Starting Celery Worker"
rm -f '/tmp/slurm-celery*.pid'
rm -f '/tmp/slurm-celery.pid'
celery -A orchestration worker \
    -l INFO \
    --pidfile="/tmp/slurm-%n.pid" \
    --logfile="${LOG_DIR}/slurm-%n%I.log" \
    --pool="solo" 
