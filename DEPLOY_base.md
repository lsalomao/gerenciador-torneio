# Guia de Deploy - Gerenciador de Times de Vôlei

## Pré-requisitos no VPS
- Docker e Docker Compose instalados
- Nginx instalado no sistema
- Domínio apontando para o IP do VPS
- Portas 80 e 443 abertas no firewall

## Passo 1: Preparar o VPS

### 1.1 Conectar ao VPS
```bash
ssh usuario@seu-vps-ip
```

### 1.2 Criar diretório do projeto
```bash
sudo mkdir -p /opt/gerenciador-times
sudo chown $USER:$USER /opt/gerenciador-times
cd /opt/gerenciador-times
```

## Passo 2: Enviar arquivos para o VPS

### Opção A: Usando Git (Recomendado)
```bash
# No VPS
cd /opt/gerenciador-times
git clone <url-do-repositorio> .
```

### Opção B: Usando SCP (da sua máquina local)
```bash
# Na sua máquina local, no diretório do projeto
scp -r * usuario@seu-vps-ip:/opt/gerenciador-times/
```

### Opção C: Usando rsync (da sua máquina local)
```bash
# Na sua máquina local, no diretório do projeto
rsync -avz --exclude 'db.sqlite3' --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' . usuario@seu-vps-ip:/opt/gerenciador-times/
```

## Passo 3: Configurar variáveis de ambiente

```bash
# No VPS
cd /opt/gerenciador-times
cp .env.example .env
nano .env
```

Edite o arquivo `.env` com suas configurações:
```env
DEBUG=False
SECRET_KEY=gere-uma-chave-secreta-forte-aqui
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=volei_db
DB_USER=volei_user
DB_PASSWORD=senha-forte-do-banco
DB_HOST=db
DB_PORT=5432

POSTGRES_DB=volei_db
POSTGRES_USER=volei_user
POSTGRES_PASSWORD=senha-forte-do-banco

CSRF_TRUSTED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
```

**Importante:** Gere uma SECRET_KEY forte:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Passo 4: Configurar Nginx

### 4.1 Copiar configuração do Nginx
```bash
sudo cp /opt/gerenciador-times/sites-available/volei /etc/nginx/sites-available/volei
```

### 4.2 Editar configuração com seu domínio
```bash
sudo nano /etc/nginx/sites-available/volei.ledtech.app
```

Substitua `volei.ledtech.app` pelo seu domínio em todas as ocorrências.

### 4.3 Criar link simbólico
```bash
sudo ln -s /etc/nginx/sites-available/volei.ledtech.app /etc/nginx/sites-enabled/
```

### 4.4 Remover configuração padrão (se existir)
```bash
sudo rm /etc/nginx/sites-enabled/default
```

### 4.5 Testar configuração
```bash
sudo nginx -t
```

### 4.6 Recarregar Nginx
```bash
sudo systemctl reload nginx
```

## Passo 5: Configurar SSL com Let's Encrypt (Opcional mas Recomendado)

### 5.1 Instalar Certbot
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx -y
```

### 5.2 Obter certificado SSL
```bash
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

Siga as instruções do Certbot. Ele configurará automaticamente o SSL no Nginx.

## Passo 6: Iniciar aplicação com Docker

### 6.1 Build e iniciar containers
```bash
cd /opt/gerenciador-times
docker-compose up -d --build
```

### 6.2 Verificar se containers estão rodando
```bash
docker-compose ps
```

### 6.3 Executar migrações do banco de dados
```bash
docker-compose exec web python manage.py migrate
```

### 6.4 Criar superusuário
```bash
docker-compose exec web python manage.py createsuperuser
```

### 6.5 Coletar arquivos estáticos
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### 6.6 Copiar arquivos estáticos para o Nginx
```bash
sudo mkdir -p /opt/gerenciador-times/staticfiles
sudo mkdir -p /opt/gerenciador-times/media
docker cp volei_web:/app/staticfiles/. /opt/gerenciador-times/staticfiles/
docker cp volei_web:/app/media/. /opt/gerenciador-times/media/
sudo chown -R www-data:www-data /opt/gerenciador-times/staticfiles
sudo chown -R www-data:www-data /opt/gerenciador-times/media
```

## Passo 7: Verificar aplicação

### 7.1 Ver logs
```bash
docker-compose logs -f web
```

### 7.2 Acessar no navegador
```
http://seu-dominio.com
```
ou
```
https://seu-dominio.com (se configurou SSL)
```

## Comandos Úteis

### Parar aplicação
```bash
docker-compose down
```

### Reiniciar aplicação
```bash
docker-compose restart
```

### Ver logs
```bash
docker-compose logs -f
```

### Atualizar aplicação (após mudanças no código)
```bash
cd /opt/gerenciador-times
git pull  # se usando git
docker-compose down
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
docker cp volei_web:/app/staticfiles/. /opt/gerenciador-times/staticfiles/
```

### Backup do banco de dados
```bash
docker-compose exec db pg_dump -U volei_user volei_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restaurar banco de dados
```bash
docker-compose exec -T db psql -U volei_user volei_db < backup.sql
```

### Acessar shell do Django
```bash
docker-compose exec web python manage.py shell
```

### Acessar bash do container
```bash
docker-compose exec web bash
```

## Troubleshooting

### Erro 502 Bad Gateway
- Verifique se o container está rodando: `docker-compose ps`
- Verifique os logs: `docker-compose logs web`
- Verifique se a porta 8000 está acessível: `curl http://localhost:8000`

### Arquivos estáticos não carregam
- Verifique permissões: `ls -la /opt/gerenciador-times/staticfiles`
- Execute collectstatic novamente
- Verifique configuração do Nginx

### Erro de conexão com banco de dados
- Verifique se o container do banco está rodando: `docker-compose ps`
- Verifique as variáveis de ambiente no `.env`
- Verifique logs do banco: `docker-compose logs db`

### Reiniciar tudo do zero
```bash
docker-compose down -v  # Remove volumes também
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput
```

## Segurança

1. **Firewall**: Configure UFW para permitir apenas portas necessárias
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **Atualizações**: Mantenha o sistema atualizado
```bash
sudo apt update && sudo apt upgrade -y
```

3. **Backups**: Configure backups automáticos do banco de dados

4. **Monitoramento**: Configure logs e monitoramento de recursos

## Estrutura de Diretórios no VPS

```
/opt/gerenciador-times/
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── requirements.txt
├── .env
├── gerenciador_volei/
├── volei/
├── static/
├── staticfiles/
├── media/
└── sites-available/
```

## Portas Utilizadas

- **80**: HTTP (Nginx)
- **443**: HTTPS (Nginx)
- **8000**: Aplicação Django (apenas localhost)
- **5432**: PostgreSQL (apenas localhost)
