#!/bin/bash --login

set -o errexit
set -o pipefail
set -o nounset

host=$(hostname)
slurmname="${WORKER_NAME:-slurm}"

echo "Starting Containerized Celery SLURM Worker: ${slurmname} on host ${host}"

# Aguardar um pouco para garantir que os serviços estejam prontos
sleep 5

# Remover arquivos PID antigos
rm -rf /tmp/${slurmname}-*.pid

# Navegar para o diretório do backend
# BASE_DIR deve estar definido no ambiente do container
if [ -z "${BASE_DIR:-}" ]; then
    export BASE_DIR=/app
fi
# O backend já está em /app (BASE_DIR)
if [ ! -f "$BASE_DIR/manage.py" ]; then
    echo "ERROR: Django manage.py not found in: $BASE_DIR"
    echo "Available files:"
    ls -la $BASE_DIR/
    exit 1
fi

# Já estamos no diretório correto
cd $BASE_DIR

# Ativar ambiente conda
if [ -f "$BASE_DIR/sh/env.sh" ]; then
    source $BASE_DIR/sh/env.sh
elif [ -f "/app/sh/env.sh" ]; then
    source /app/sh/env.sh
else
    echo "ERROR: env.sh not found"
    exit 1
fi

echo "SLURM Worker ready - container configured as submission node"

# Verificar se conseguimos nos comunicar com o SLURM
if command -v sinfo >/dev/null 2>&1; then
    echo "Testing SLURM connectivity..."
    sinfo -h >/dev/null 2>&1 && echo "SLURM cluster accessible" || echo "Warning: SLURM cluster not accessible yet"
fi

echo "Starting Celery SLURM Worker..."

# Iniciar o worker Celery
celery -A orchestration worker -Q "${slurmname}","${slurmname}".\"${host}\" \
    -l ${LOGGING_LEVEL:-INFO} \
    --pidfile="/tmp/${slurmname}-%n.pid" \
    --logfile="${LOG_DIR}/${slurmname}.${host}.log" \
    --pool="processes" \
    --concurrency="${SLURM_WORKER_CONCURRENCY:-2}"
