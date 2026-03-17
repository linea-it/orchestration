#!/bin/bash

if [ ! -d "$PIPELINES_DIR" ]; then
    export PIPELINES_DIR=$APP_DIR
fi

echo "The directory containing the pipelines is: " "$PIPELINES_DIR"

MICROMAMBA_BIN="${MICROMAMBA_BIN:-micromamba}"
if ! command -v "$MICROMAMBA_BIN" >/dev/null 2>&1; then
    echo "Failed to find micromamba in PATH"
    exit 1
fi

for pipe in $( ls ${PIPELINES_DIR}/*/install.sh)
do
    echo "Installing: ${pipe}"
    bash "$pipe"
done
