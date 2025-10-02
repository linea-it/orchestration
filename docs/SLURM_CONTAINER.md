# SLURM Worker Containerizado

Este documento descreve como configurar e executar o worker SLURM dentro de um container Docker, permitindo que o container atue como um nó de submissão SLURM.

## Arquitetura

O container SLURM worker:
- Estende o backend base adicionando o cliente SLURM
- Usa `network_mode: host` para compartilhar a rede com o host
- Monta as configurações SLURM do host (`/etc/slurm`)
- Executa como um worker Celery dedicado para tarefas SLURM

## Pré-requisitos

1. **SLURM configurado no host**: O sistema host deve ter SLURM instalado e configurado
2. **Configurações acessíveis**: Os arquivos em `/etc/slurm` devem estar presentes
3. **Rede compartilhada**: O container precisa acessar os controladores SLURM

## Configuração

### 1. Verificar SLURM no Host

```bash
# Verificar se SLURM está funcionando
sinfo
squeue
```

### 2. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo:
```bash
cp .env.slurm.example .env.slurm
```

Edite `.env.slurm` conforme necessário e adicione as variáveis ao seu `.env` principal.

### 3. Build do Container

Use o script auxiliar:
```bash
./scripts/slurm_container.sh
```

Ou manualmente:
```bash
# Build do backend base
docker build -t orchestration-backend:latest ./backend/

# Build do worker SLURM
docker build -f ./backend/Dockerfile.slurm -t orchestration-slurm-worker:latest ./backend/
```

## Execução

### Usando Docker Compose (Recomendado)

Para executar apenas o worker SLURM:
```bash
docker-compose -f docker-compose-development.yml up celery_slurm_worker
```

Para executar todos os serviços incluindo SLURM:
```bash
docker-compose -f docker-compose-development.yml up
```

### Execução Manual

```bash
docker run --rm -it \
  --network host \
  --env-file .env \
  -v ./pipelines:/pipelines \
  -v ./datasets:/datasets \
  -v ./processes:/processes \
  -v ./logs:/var/log/orchestration \
  -v /etc/slurm:/etc/slurm:ro \
  -v /var/spool/slurm:/var/spool/slurm \
  orchestration-slurm-worker:latest
```

## Volumes Montados

| Volume Host | Volume Container | Descrição |
|-------------|------------------|-----------|
| `/etc/slurm` | `/etc/slurm` | Configurações SLURM (read-only) |
| `/var/spool/slurm` | `/var/spool/slurm` | Spool directory SLURM |
| `./pipelines` | `/pipelines` | Pipelines de processamento |
| `./datasets` | `/datasets` | Datasets |
| `./processes` | `/processes` | Diretório de processos |
| `./logs` | `${LOG_DIR}` | Logs |

## Troubleshooting

### Container não consegue se comunicar com SLURM

1. **Verificar configuração SLURM no host**:
   ```bash
   ls -la /etc/slurm/
   cat /etc/slurm/slurm.conf
   ```

2. **Verificar serviços SLURM**:
   ```bash
   systemctl status slurmd
   systemctl status slurmctld  # se for controller
   ```

3. **Verificar conectividade de rede**:
   O container usa `network_mode: host`, então deve ter acesso direto aos controladores SLURM.

### Logs do Container

```bash
# Ver logs do worker SLURM
docker-compose -f docker-compose-development.yml logs celery_slurm_worker

# Follow logs
docker-compose -f docker-compose-development.yml logs -f celery_slurm_worker
```

### Problemas de Permissão

Se houver problemas de permissão com `/var/spool/slurm`:

```bash
# No host, ajustar permissões se necessário
sudo chown -R 1000:1000 /var/spool/slurm
# ou
sudo chmod 777 /var/spool/slurm
```

## Comandos SLURM Disponíveis no Container

O container terá acesso aos seguintes comandos SLURM:
- `sbatch` - Submissão de jobs
- `squeue` - Verificar fila de jobs
- `scancel` - Cancelar jobs
- `sinfo` - Informações do cluster
- `scontrol` - Controle administrativo

## Desenvolvimento

Para modificar o worker SLURM:

1. Edite `backend/sh/slurm_worker_container.sh` para alterar o comportamento do worker
2. Edite `backend/Dockerfile.slurm` para adicionar dependências
3. Rebuild o container: `./scripts/slurm_container.sh`

## Integração com Código Existente

O worker SLURM containerizado usa a mesma lógica de submissão existente em:
- `backend/core/executors/slurm/tasks.py`
- `backend/core/executors/slurm/commands.py`

Não são necessárias alterações no código Python existente.