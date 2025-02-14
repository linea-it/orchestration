#!/bin/bash

export APP_DIR=<app path>
export BASE_DIR=${APP_DIR}/orchestration
export CONDA_PATH=${APP_DIR}/miniconda3/bin/activate
source $CONDA_PATH

conda activate worker-slurm

set -a
. /home/app.orch/rabbitmq/.env  # environment variables related to rabbitmq running on orchestration server
. ./orchestration/.env
set +a

export PATH=$PATH:$BASE_DIR/backend/sh/

#export DEBUG="0"
#export LOGGING_LEVEL="INFO"
#export AUTORELOAD="0"

# AMQP
# export RABBITMQ_HOST="localhost"