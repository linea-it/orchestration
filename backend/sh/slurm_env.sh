#!/bin/bash --login

export APP_DIR=         # e.g.: /data/apps/app.orch/dev
export BASE_DIR=        # e.g.: ${APP_DIR}/orchestration
export CONDA_PATH=      # e.g.: ${APP_DIR}/miniconda3/bin/activate
export RABBITMQ_ENV=    # e.g.: /home/app.orch/rabbitmq/.env
export WORKER_NAME="slurm"

set -a
. $RABBITMQ_ENV         # environment variables related to rabbitmq running on srvorch-dev server
. $BASE_DIR/.env
set +a

echo "Activating environment"

# shellcheck source=/data/apps/app.orch/dev/miniconda3/bin/activate
source $CONDA_PATH || { echo "Failed to activate Conda environment"; exit 1; }

if [ ! -d "$PIPELINES_DIR" ]; then
    echo "Error: PIPELINES_DIR not defined."
    exit 1
fi

HASENV=$(conda env list | grep 'orchestration ')

if [ -z "$HASENV" ]; then
    echo "Create virtual environment..."
    conda env create -f $BASE_DIR/backend/environment.yml
    echo "Virtual environment created and packages installed."
fi

conda activate orchestration

export PATH=$PATH:$BASE_DIR/backend/sh/

umask g+w
