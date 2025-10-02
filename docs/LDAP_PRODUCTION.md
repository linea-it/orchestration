# 🏢 Worker SLURM em Ambiente com LDAP

## 💡 Abordagem Simplificada

Em ambientes com LDAP, **não precisamos** instalar suporte LDAP completo no container. A solução é muito mais simples:

### ✅ **O que funciona:**
- Container usa **mesmo UID/GID** do usuário SLURM do host
- Volumes montados mantêm permissões corretas
- `network_mode: host` permite comunicação direta
- SLURM vê jobs como vindos do usuário correto

### ❌ **O que NÃO precisamos:**
- ❌ Instalar `libnss-ldap` no container
- ❌ Configurar PAM/NSS no container  
- ❌ Montar configurações LDAP
- ❌ Resolver nomes de usuários no container

## 🔧 Configuração para Produção com LDAP

### 1. Descobrir UID/GID do usuário SLURM no host

```bash
# No host de produção
id slurm
# uid=1001(slurm) gid=1001(slurm) groups=1001(slurm)

# Ou descobrir o usuário que submete jobs
id $USER
# uid=1005(joao.silva) gid=1005(joao.silva) groups=1005(joao.silva),1001(slurm)
```

### 2. Ajustar docker-compose para usar UID correto

```yaml
  celery_slurm_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.slurm
      args:
        - "USERID=1005"        # UID do usuário LDAP
        - "GROUPID=1005"       # GID do usuário LDAP  
        - "USERNAME=joao.silva" # Nome do usuário LDAP
    command: /slurm_worker_container.sh
    user: "1005:1005"         # Executar com UID/GID corretos
    network_mode: "host"
    env_file:
      - .env
    volumes:
      - ./pipelines:/pipelines
      - ./datasets:/datasets
      - ./processes:/processes
      - ./logs:/var/log/orchestration
      # Volumes SLURM essenciais
      - /etc/slurm:/etc/slurm:ro
      - /var/spool/slurm:/var/spool/slurm
    depends_on:
      - rabbitmq
      - backend
```

### 3. Verificar permissões no host

```bash
# Verificar se o usuário tem acesso aos diretórios SLURM
ls -la /etc/slurm/
ls -la /var/spool/slurm/

# Verificar se consegue submeter jobs
sbatch --version
squeue
sinfo
```

### 4. Teste de funcionamento

```bash
# Build com UID correto
USERID=1005 GROUPID=1005 USERNAME=joao.silva docker-compose build celery_slurm_worker

# Executar
docker-compose up celery_slurm_worker

# Verificar se funciona
docker exec orchestration-celery_slurm_worker-1 id
# uid=1005(joao.silva) gid=1005(joao.silva)

docker exec orchestration-celery_slurm_worker-1 squeue
# Deve mostrar jobs normalmente
```

## 🔍 Vantagens desta Abordagem

### ✅ **Simplicidade**
- Não adiciona complexidade desnecessária
- Usa recursos nativos do Docker/Linux
- Facilita troubleshooting

### ✅ **Segurança**
- Container roda com usuário não-privilegiado
- Permissões consistentes com o host
- Audit trail correto nos logs SLURM

### ✅ **Performance**
- Sem overhead de resolução LDAP no container
- Comunicação direta host->cluster
- Menos pontos de falha

## 🚨 Pontos de Atenção

### 1. **UID/GID Consistency**
```bash
# SEMPRE verificar antes do deploy
echo "Host UID: $(id -u slurm)"
echo "Container UID: deve ser igual"
```

### 2. **Permissões de Arquivos**
```bash
# Volumes devem ter permissões corretas
sudo chown -R 1005:1005 ./logs
sudo chown -R 1005:1005 ./processes
```

### 3. **Jobs aparecem com usuário correto**
```bash
# No cluster SLURM, jobs devem aparecer como:
squeue -o "%i %j %u %T"
# JobID JobName User State
# 12345 my_job  joao.silva RUNNING
```

## 📋 Checklist de Deploy

- [ ] Descobrir UID/GID corretos no host
- [ ] Ajustar `USERID`/`GROUPID` no docker-compose  
- [ ] Verificar permissões dos volumes
- [ ] Testar conectividade SLURM no host
- [ ] Build do container com argumentos corretos
- [ ] Executar e verificar `id` no container
- [ ] Submeter job de teste
- [ ] Verificar logs de auditoria SLURM

## 🔄 Exemplo Completo

```bash
# 1. No host de produção
SLURM_USER_ID=$(id -u slurm)
SLURM_GROUP_ID=$(id -g slurm)

# 2. Configurar .env
echo "USERID=${SLURM_USER_ID}" >> .env
echo "GROUPID=${SLURM_GROUP_ID}" >> .env
echo "USERNAME=slurm" >> .env

# 3. Deploy
docker-compose build celery_slurm_worker
docker-compose up -d celery_slurm_worker

# 4. Verificar
docker-compose logs celery_slurm_worker
```

Esta abordagem é **muito mais robusta e simples** que tentar replicar todo o ambiente LDAP dentro do container!