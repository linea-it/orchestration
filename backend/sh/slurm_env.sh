#!/bin/bash --login

export APP_DIR=         # e.g.: /data/apps/app.orch/dev
export BASE_DIR=        # e.g.: ${APP_DIR}/orchestration
export MAMBA_ROOT_PREFIX=   # e.g.: ${APP_DIR}/micromamba
export MICROMAMBA_BIN=      # e.g.: /usr/local/bin/micromamba
export RABBITMQ_ENV=    # e.g.: /home/app.orch/rabbitmq/.env
export WORKER_NAME="slurm"
export ORCHESTRATION_ENV_NAME="orchestration"

set -a
. "$RABBITMQ_ENV"
. "$BASE_DIR/.env"
set +a

MICROMAMBA_BIN="${MICROMAMBA_BIN:-micromamba}"
MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-${APP_DIR}/micromamba}"
ENV_PREFIX="${MAMBA_ROOT_PREFIX}/envs/${ORCHESTRATION_ENV_NAME}"

if ! command -v "$MICROMAMBA_BIN" >/dev/null 2>&1; then
    echo "Failed to find micromamba in PATH. Set MICROMAMBA_BIN or update PATH."
    exit 1
fi

if [ ! -d "$PIPELINES_DIR" ]; then
    echo "Error: PIPELINES_DIR not defined."
    exit 1
fi

if [ ! -d "$ENV_PREFIX" ]; then
    echo "Create virtual environment..."
    "$MICROMAMBA_BIN" create --root-prefix "$MAMBA_ROOT_PREFIX" -y -f "$BASE_DIR/backend/environment.yml"
    echo "Virtual environment created and packages installed."
fi

export PATH="$ENV_PREFIX/bin:$BASE_DIR/backend/sh/:$PATH"

umask g+w
