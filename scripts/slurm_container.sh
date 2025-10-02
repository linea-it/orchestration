#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Building SLURM Container..."

# Build do backend base primeiro (se necessário)
if ! docker image inspect orchestration-backend:latest >/dev/null 2>&1; then
    echo "Building base backend image first..."
    docker build -t orchestration-backend:latest ./backend/
fi

# Build do container SLURM
echo "Building SLURM worker image..."
docker build -f ./backend/Dockerfile.slurm -t orchestration-slurm-worker:latest ./backend/

echo "Build completed!"

# Verificar se existem as configurações SLURM necessárias
echo "Checking SLURM configuration..."

if [ ! -d "/etc/slurm" ]; then
    echo "WARNING: /etc/slurm directory not found on host."
    echo "Make sure SLURM is properly configured on the host system."
fi

if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found. Please create it with necessary environment variables."
fi

echo "To run the SLURM worker container, use:"
echo "docker-compose -f docker-compose-development.yml up celery_slurm_worker"
echo ""
echo "Or to run all services:"
echo "docker-compose -f docker-compose-development.yml up"