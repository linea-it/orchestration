#!/bin/bash --login

export MICROMAMBA_BIN="${MICROMAMBA_BIN:-micromamba}"
export ORCHESTRATION_ENV_PREFIX="${ORCHESTRATION_ENV_PREFIX:-/opt/micromamba/envs/orchestration}"
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-${BASE_DIR}/.micromamba}"
export ORCHESTRATION_ENV_NAME="${ORCHESTRATION_ENV_NAME:-orchestration}"
export PATH="${ORCHESTRATION_ENV_PREFIX}/bin:${PATH}"
