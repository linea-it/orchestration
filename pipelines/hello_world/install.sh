#!/bin/bash

set -e

PIPE_BASE="$PIPELINES_DIR/hello_world"

if [ ! -d "$PIPE_BASE/.env" ]; then
    echo "Create virtual environment..."
    python3 -m venv "$PIPE_BASE/.env"
    . "$PIPE_BASE/.env/bin/activate"

    echo "Installing packages..."
    pip install -r "$PIPE_BASE/requirements.txt"

    echo "Virtual environment created and packages installed."
else
    echo "Virtual environment already exists. Using existing environment."
    . "$PIPE_BASE/.env/bin/activate"
fi

export PATH=$PATH:"$PIPE_BASE/scripts/"