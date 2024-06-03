#!/bin/bash --login

set -o errexit
set -o nounset
set -o pipefail

envfile="${BASE_DIR}/sh/env.sh"

# shellcheck disable=SC1090
source "${envfile}"

worker_ready() {
    celery --app orchestration inspect ping
}

until worker_ready; do
    >&2 echo 'Celery workers not available'
    sleep 5
done
>&2 echo 'Celery workers is available'

celery -A orchestration flower --url-prefix=flower