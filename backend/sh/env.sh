#!/bin/bash --login

export MICROMAMBA_BIN="${MICROMAMBA_BIN:-micromamba}"
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-/opt/micromamba}"
export ORCHESTRATION_ENV_NAME="${ORCHESTRATION_ENV_NAME:-orchestration}"
export PATH="${MAMBA_ROOT_PREFIX}/envs/${ORCHESTRATION_ENV_NAME}/bin:${PATH}"
