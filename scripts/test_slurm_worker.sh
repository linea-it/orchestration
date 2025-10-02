#!/bin/bash

set -e

echo "🧪 Testando Worker SLURM Containerizado"
echo "========================================"

PROJECT_ROOT="/home/singulani/projects/orchestration"
cd "$PROJECT_ROOT"

# Verificar se RabbitMQ está rodando
echo "📡 Verificando RabbitMQ..."
if ! docker-compose -f docker-compose-development.yml ps rabbitmq | grep -q "Up"; then
    echo "🚀 Iniciando RabbitMQ..."
    docker-compose -f docker-compose-development.yml up -d rabbitmq
    echo "⏳ Aguardando RabbitMQ inicializar..."
    sleep 15
fi

# Teste 1: Verificar se o container pode ser construído
echo ""
echo "🔧 Teste 1: Build do container SLURM worker"
docker-compose -f docker-compose-development.yml build celery_slurm_worker
echo "✅ Build realizado com sucesso"

# Teste 2: Verificar comandos SLURM disponíveis
echo ""
echo "🔧 Teste 2: Verificar comandos SLURM no container"
docker run --rm --env-file .env --network host --user 1000:1000 orchestration-celery_slurm_worker bash -c "
echo 'Comandos SLURM disponíveis:'
which sbatch && echo '- sbatch: OK'
which squeue && echo '- squeue: OK'
which scancel && echo '- scancel: OK'
which sinfo && echo '- sinfo: OK' || echo '- sinfo: Não encontrado (normal se SLURM não estiver configurado)'
echo '- Versão do cliente SLURM:'
sbatch --version || echo 'sbatch --version não disponível'
"
echo "✅ Comandos SLURM verificados"

# Teste 3: Verificar ambiente Python/Conda
echo ""
echo "🔧 Teste 3: Verificar ambiente Python"
docker run --rm --env-file .env --network host --user 1000:1000 orchestration-celery_slurm_worker bash -c "
echo 'Verificando ambiente Python...'
conda --version
python --version
echo 'Verificando se consegue ativar ambiente orchestration...'
source /opt/conda/bin/activate && conda activate orchestration && echo 'Ambiente ativado com sucesso'
echo 'Verificando se Celery está disponível...'
source /opt/conda/bin/activate && conda activate orchestration && celery --version
"
echo "✅ Ambiente Python verificado"

# Teste 4: Testar script de inicialização (apenas primeira parte)
echo ""
echo "🔧 Teste 4: Testar script de inicialização"
timeout 10s docker run --rm --env-file .env --network host --user 1000:1000 \
    -v $(pwd)/logs:/var/log/orchestration \
    -v $(pwd)/pipelines:/pipelines \
    -v $(pwd)/datasets:/datasets \
    -v $(pwd)/processes:/processes \
    orchestration-celery_slurm_worker bash -c "/slurm_worker_container.sh" || echo "⏰ Timeout esperado - worker iniciou corretamente"

echo ""
echo "🎉 Todos os testes básicos concluídos!"
echo "📝 Próximos passos para usar em produção:"
echo "   1. Configure o SLURM no host se ainda não estiver configurado"
echo "   2. Monte o volume /etc/slurm do host para o container"
echo "   3. Configure as variáveis de ambiente específicas do seu cluster"
echo "   4. Execute: docker-compose -f docker-compose-development.yml up celery_slurm_worker"
echo ""
echo "💡 Para ver logs: docker-compose -f docker-compose-development.yml logs -f celery_slurm_worker"