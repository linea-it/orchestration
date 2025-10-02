#!/bin/bash

set -e

echo "🏢 Configuração para Produção com LDAP"
echo "======================================"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Função para detectar usuário SLURM
detect_slurm_user() {
    # Tentar diferentes usuários comuns
    for user in slurm slurmuser slurmd $USER; do
        if id "$user" >/dev/null 2>&1; then
            echo "$user"
            return 0
        fi
    done
    return 1
}

# 1. Detectar usuário e IDs
echo "🔍 Detectando configuração SLURM no host..."

if SLURM_USER=$(detect_slurm_user); then
    SLURM_UID=$(id -u "$SLURM_USER")
    SLURM_GID=$(id -g "$SLURM_USER")
    echo "✅ Usuário SLURM encontrado: $SLURM_USER (UID: $SLURM_UID, GID: $SLURM_GID)"
else
    echo "❌ Usuário SLURM não encontrado automaticamente."
    echo "Por favor, informe o usuário SLURM manualmente:"
    read -p "Nome do usuário SLURM: " SLURM_USER
    
    if ! id "$SLURM_USER" >/dev/null 2>&1; then
        echo "❌ Usuário '$SLURM_USER' não existe. Abortando."
        exit 1
    fi
    
    SLURM_UID=$(id -u "$SLURM_USER")
    SLURM_GID=$(id -g "$SLURM_USER")
    echo "✅ Usuário configurado: $SLURM_USER (UID: $SLURM_UID, GID: $SLURM_GID)"
fi

# 2. Verificar acesso SLURM
echo ""
echo "🔍 Verificando acesso ao SLURM..."

if command -v sinfo >/dev/null 2>&1; then
    echo "✅ Comando sinfo encontrado"
    if sinfo -h >/dev/null 2>&1; then
        echo "✅ SLURM cluster acessível"
    else
        echo "⚠️  SLURM cluster não acessível (normal se não estiver no nó de submissão)"
    fi
else
    echo "❌ Comando sinfo não encontrado. Certifique-se de que SLURM está instalado no host."
fi

# 3. Verificar diretórios SLURM
echo ""
echo "🔍 Verificando diretórios SLURM..."

if [ -d "/etc/slurm" ]; then
    echo "✅ /etc/slurm encontrado"
    ls -la /etc/slurm/ | head -3
else
    echo "❌ /etc/slurm não encontrado. Verifique a instalação SLURM."
fi

if [ -d "/var/spool/slurm" ]; then
    echo "✅ /var/spool/slurm encontrado"
else
    echo "⚠️  /var/spool/slurm não encontrado (pode estar em local diferente)"
fi

# 4. Configurar environment variables
echo ""
echo "🔧 Configurando variáveis de ambiente..."

ENV_FILE=".env.production"
if [ -f ".env" ]; then
    ENV_FILE=".env"
fi

# Backup do arquivo atual
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backup criado: $ENV_FILE.backup.*"
fi

# Adicionar ou atualizar variáveis SLURM
echo ""
echo "# SLURM LDAP Configuration - $(date)" >> "$ENV_FILE"
echo "USERID=$SLURM_UID" >> "$ENV_FILE"
echo "GROUPID=$SLURM_GID" >> "$ENV_FILE"
echo "USERNAME=$SLURM_USER" >> "$ENV_FILE"
echo "" >> "$ENV_FILE"

echo "✅ Variáveis adicionadas ao $ENV_FILE:"
echo "   USERID=$SLURM_UID"
echo "   GROUPID=$SLURM_GID"  
echo "   USERNAME=$SLURM_USER"

# 5. Ajustar permissões de diretórios locais
echo ""
echo "🔧 Ajustando permissões dos diretórios locais..."

for dir in logs processes; do
    if [ -d "$dir" ]; then
        echo "Ajustando permissões: $dir"
        sudo chown -R "$SLURM_UID:$SLURM_GID" "$dir" || {
            echo "⚠️  Não foi possível alterar permissões de $dir (pode precisar de sudo)"
        }
    else
        echo "Criando diretório: $dir"
        mkdir -p "$dir"
        sudo chown -R "$SLURM_UID:$SLURM_GID" "$dir" || {
            echo "⚠️  Não foi possível alterar permissões de $dir (pode precisar de sudo)"
        }
    fi
done

# 6. Gerar docker-compose de produção
echo ""
echo "🔧 Gerando configuração docker-compose para produção..."

cat > docker-compose.production.yml << EOF
# Docker Compose para Produção com LDAP
# Gerado automaticamente em $(date)

version: "3.9"

services:
  backend: &backend
    build:
      context: ./backend
      args:
        - "USERID=$SLURM_UID"
        - "GROUPID=$SLURM_GID"
        - "USERNAME=$SLURM_USER"
    command: /app/sh/start.sh
    user: "$SLURM_UID:$SLURM_GID"
    env_file:
      - $ENV_FILE
    volumes:
      - ./pipelines:/pipelines
      - ./datasets:/datasets
      - ./processes:/processes
      - ./logs:\${LOG_DIR}
      - ./db:/db
    depends_on:
      - rabbitmq

  celery_slurm_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.slurm
      args:
        - "USERID=$SLURM_UID"
        - "GROUPID=$SLURM_GID"
        - "USERNAME=$SLURM_USER"
    command: /slurm_worker_container.sh
    user: "$SLURM_UID:$SLURM_GID"
    network_mode: "host"  # CRÍTICO: Para acesso direto ao cluster SLURM
    env_file:
      - $ENV_FILE
    environment:
      - WORKER_NAME=slurm
      - SLURM_WORKER_CONCURRENCY=4
    volumes:
      - ./pipelines:/pipelines
      - ./datasets:/datasets
      - ./processes:/processes
      - ./logs:\${LOG_DIR}
      - ./db:/db
      # Volumes SLURM essenciais
      - /etc/slurm:/etc/slurm:ro
      - /var/spool/slurm:/var/spool/slurm
    depends_on:
      - rabbitmq

  rabbitmq:
    image: "rabbitmq:3.12.12-management"
    env_file:
      - $ENV_FILE
    ports:
      - "15672:15672"
      - "5672:5672"
    volumes:
      - "./rabbitmq/enabled_plugins:/etc/rabbitmq/enabled_plugins"
      - "./rabbitmq/data/:/var/lib/rabbitmq/"
      - "./rabbitmq/log/:/var/log/rabbitmq/"

EOF

echo "✅ Arquivo criado: docker-compose.production.yml"

# 7. Instruções finais
echo ""
echo "🎉 Configuração concluída!"
echo "========================"
echo ""
echo "📋 Próximos passos:"
echo "1. Revisar o arquivo $ENV_FILE"
echo "2. Testar: docker-compose -f docker-compose.production.yml build celery_slurm_worker"
echo "3. Executar: docker-compose -f docker-compose.production.yml up celery_slurm_worker"
echo "4. Verificar logs: docker-compose -f docker-compose.production.yml logs -f celery_slurm_worker"
echo ""
echo "🔍 Para testar se funcionou:"
echo "docker-compose -f docker-compose.production.yml exec celery_slurm_worker id"
echo "# Deve mostrar: uid=$SLURM_UID($SLURM_USER) gid=$SLURM_GID($SLURM_USER)"
echo ""
echo "📚 Documentação completa em: docs/LDAP_PRODUCTION.md"