# 🚀 Deployment do Worker SLURM Containerizado

Este documento descreve como fazer o deployment do worker SLURM containerizado em produção.

## ✅ Status da Implementação

### ✅ Implementado e Testado
- Container SLURM com cliente SLURM instalado
- Script de inicialização funcional
- Integração com docker-compose
- Carregamento correto das tarefas SLURM
- Conectividade com RabbitMQ
- Ambiente Python/Conda funcionando

### 🔄 Para Configuração em Produção
- Configuração SLURM do cluster de produção
- Volumes e permissões específicos do ambiente
- Variáveis de ambiente do cluster

## 📋 Pré-requisitos para Produção

1. **Host com acesso ao cluster SLURM**
   - Configuração SLURM em `/etc/slurm/`
   - Conectividade de rede com controladores SLURM
   - Usuário com permissões para submeter jobs

2. **Volumes necessários**
   ```bash
   /etc/slurm        # Configurações SLURM (read-only)
   /var/spool/slurm  # Spool directory (read-write)
   ```

## 🚀 Deployment Passo a Passo

### 1. Preparar Ambiente

```bash
# Clone do repositório
git clone <repository-url>
cd orchestration

# Configurar variáveis de ambiente
cp .env.slurm.example .env.slurm
# Editar .env.slurm conforme seu ambiente
```

### 2. Build dos Containers

```bash
# Usar script auxiliar
./scripts/slurm_container.sh

# Ou manualmente
docker build -t orchestration-backend:latest ./backend/
docker build -f ./backend/Dockerfile.slurm -t orchestration-slurm-worker:latest ./backend/
```

### 3. Configurar Docker Compose

Ajustar `docker-compose-development.yml` ou criar `docker-compose-production.yml`:

```yaml
  celery_slurm_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.slurm
    command: /slurm_worker_container.sh
    network_mode: "host"  # IMPORTANTE: Para acesso direto ao cluster
    env_file:
      - .env
      - .env.slurm  # Configurações específicas SLURM
    volumes:
      # Volumes do projeto
      - ./pipelines:/pipelines
      - ./datasets:/datasets
      - ./processes:/processes
      - ./logs:/var/log/orchestration
      
      # Volumes SLURM (CRÍTICO)
      - /etc/slurm:/etc/slurm:ro
      - /var/spool/slurm:/var/spool/slurm
      
      # Se usar autenticação MUNGE
      - /etc/munge:/etc/munge:ro
      - /var/run/munge:/var/run/munge:ro
    
    depends_on:
      - rabbitmq
      - backend
```

### 4. Executar

```bash
# Apenas o worker SLURM
docker-compose -f docker-compose-development.yml up celery_slurm_worker

# Ou todo o stack
docker-compose -f docker-compose-development.yml up
```

## 🔧 Configurações de Produção

### Variáveis de Ambiente (.env.slurm)

```bash
# Worker Configuration
WORKER_NAME=slurm
SLURM_WORKER_CONCURRENCY=4  # Ajustar conforme capacidade

# Logging
LOGGING_LEVEL=INFO
LOG_DIR=/var/log/orchestration

# SLURM específico (se necessário)
SLURM_CONF=/etc/slurm/slurm.conf
SLURM_CLUSTER_NAME=production-cluster

# Autenticação (se usar MUNGE)
# MUNGE_SOCKET=/var/run/munge/munge.socket.2
```

### Volumes e Permissões

```bash
# No host, verificar permissões
ls -la /etc/slurm/
ls -la /var/spool/slurm/

# Ajustar se necessário (cuidado em produção!)
sudo chown -R slurm:slurm /var/spool/slurm
sudo chmod 755 /var/spool/slurm
```

## 🔍 Verificação e Monitoramento

### Logs
```bash
# Logs do worker
docker-compose logs -f celery_slurm_worker

# Verificar conectividade SLURM
docker exec -it orchestration-celery_slurm_worker-1 sinfo
docker exec -it orchestration-celery_slurm_worker-1 squeue
```

### Testes de Conectividade
```bash
# Testar comandos SLURM
docker exec orchestration-celery_slurm_worker-1 bash -c "
  echo 'Testing SLURM connectivity...'
  sinfo -h && echo 'sinfo: OK' || echo 'sinfo: FAILED'
  squeue -h && echo 'squeue: OK' || echo 'squeue: FAILED'
"
```

### Health Check
```bash
# Verificar se worker está processando
docker exec orchestration-celery_slurm_worker-1 celery -A orchestration inspect active
```

## 🐛 Troubleshooting

### Problemas Comuns

1. **"SLURM cluster not accessible"**
   - Verificar conectividade de rede
   - Verificar configuração em `/etc/slurm/`
   - Verificar serviços SLURM no cluster

2. **Problemas de autenticação**
   - Verificar MUNGE se usado
   - Verificar permissões de usuário
   - Verificar volumes montados

3. **Worker não conecta no RabbitMQ**
   - Verificar se RabbitMQ está rodando
   - Verificar variáveis RABBITMQ_* no .env

### Debug Avançado

```bash
# Entrar no container para debug
docker exec -it orchestration-celery_slurm_worker-1 bash

# Dentro do container
conda activate orchestration
cd /app

# Testar manualmente
python manage.py shell
# >>> from core.executors.slurm.commands import *
# >>> sinfo()
```

## 📈 Otimizações de Produção

1. **Concorrência**
   - Ajustar `SLURM_WORKER_CONCURRENCY` conforme carga esperada
   - Monitorar uso de CPU/memória

2. **Logs**
   - Rotação de logs
   - Centralização (ELK, etc.)

3. **Monitoring**
   - Prometheus + Grafana para métricas Celery
   - Alertas para falhas de conectividade SLURM

4. **Alta Disponibilidade**
   - Múltiplos workers SLURM
   - Load balancer se necessário

## 🔄 Atualizações

Para atualizar o worker SLURM:

```bash
# Rebuild
docker-compose build celery_slurm_worker

# Restart
docker-compose restart celery_slurm_worker
```

## 📞 Suporte

Para problemas específicos:
1. Verificar logs detalhados
2. Testar conectividade SLURM manualmente
3. Validar configurações de rede
4. Verificar permissões de usuário/volumes