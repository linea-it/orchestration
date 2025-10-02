# Estende o backend base para adicionar funcionalidades do SLURM
FROM orchestration-backend:latest AS base

# Switch to root para instalar pacotes do sistema
USER root

# Instalar SLURM client tools para submissão de jobs
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    slurm-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Criar diretórios necessários para SLURM
RUN mkdir -p /etc/slurm /var/log/slurm /var/spool/slurm \
    && chown -R 1000:1000 /var/log/slurm /var/spool/slurm

# Copiar script específico do worker SLURM
COPY --chmod=0775 ./sh/slurm_worker_container.sh /slurm_worker_container.sh

# Switch back to non-privileged user
USER orch

# Default command para o worker SLURM
CMD ["/slurm_worker_container.sh"]
