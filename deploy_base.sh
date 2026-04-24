#!/bin/bash

set -e

echo "==================================="
echo "Deploy - Gerenciador de Times"
echo "Porta: 5006 | HTTPS: Sim"
echo ""

DOMAIN="volei.ledtech.app"
read -p "Digite o email para SSL (ex: seu@email.com): " EMAIL
read -sp "Digite a senha do banco de dados: " DB_PASSWORD
echo ""

PROJECT_DIR="/opt/gerenciador-times"

echo ""
echo "1. Verificando diretório do projeto..."
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Criando diretório $PROJECT_DIR..."
    mkdir -p $PROJECT_DIR
fi

echo ""
echo "2. Verificando se já estamos no diretório correto..."
if [ "$PWD" != "$PROJECT_DIR" ]; then
    echo "Copiando arquivos para $PROJECT_DIR..."
    cp -r . $PROJECT_DIR/
    cd $PROJECT_DIR
else
    echo "Já estamos em $PROJECT_DIR"
fi

echo ""
echo "3. Configurando variáveis de ambiente..."
if [ ! -f .env ]; then
    cp .env.example .env

    SECRET_KEY=$(openssl rand -base64 50 | tr -d '\n')

    sed -i "s|DEBUG=.*|DEBUG=False|g" .env
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env
    sed -i "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=$DOMAIN,localhost,127.0.0.1|g" .env
    sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASSWORD|g" .env
    sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$DB_PASSWORD|g" .env
    sed -i "s|CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=https://$DOMAIN|g" .env

    echo "Arquivo .env configurado!"
else
    echo "Arquivo .env já existe, pulando..."
fi

echo ""
echo "4. Configurando Nginx (temporariamente sem SSL)..."
cat > /etc/nginx/sites-available/$DOMAIN << 'EOF'
server {
    listen 80;
    server_name volei.ledtech.app;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    client_max_body_size 20M;

    location /static/ {
        alias /opt/gerenciador-times/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/gerenciador-times/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:5006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

if [ ! -f /etc/nginx/sites-enabled/$DOMAIN ]; then
    ln -s /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
fi

if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

echo ""
echo "5. Testando configuração do Nginx..."
nginx -t

echo ""
echo "6. Recarregando Nginx..."
systemctl reload nginx

echo ""
echo "7. Iniciando containers Docker (porta 5006)..."
docker-compose down 2>/dev/null || true
docker-compose up -d --build

echo ""
echo "8. Aguardando containers iniciarem..."
sleep 10

echo ""
echo "9. Executando migrações..."
docker-compose exec -T web python manage.py migrate

echo ""
echo "10. Coletando arquivos estáticos..."
docker-compose exec -T web python manage.py collectstatic --noinput

echo ""
echo "11. Copiando arquivos estáticos para Nginx..."
mkdir -p $PROJECT_DIR/staticfiles
mkdir -p $PROJECT_DIR/media
mkdir -p /var/www/certbot
docker cp volei_web:/app/staticfiles/. $PROJECT_DIR/staticfiles/ 2>/dev/null || true
docker cp volei_web:/app/media/. $PROJECT_DIR/media/ 2>/dev/null || true
chown -R www-data:www-data $PROJECT_DIR/staticfiles
chown -R www-data:www-data $PROJECT_DIR/media

echo ""
echo "12. Configurando SSL com Let's Encrypt..."
read -p "Deseja configurar SSL agora? (s/n): " SETUP_SSL

if [ "$SETUP_SSL" = "s" ] || [ "$SETUP_SSL" = "S" ]; then
    if ! command -v certbot &> /dev/null; then
        echo "Instalando Certbot..."
        apt update
        apt install certbot python3-certbot-nginx -y
    fi

    certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive
    echo "SSL configurado com sucesso!"
else
    echo "Pulando configuração SSL. Você pode configurar depois com:"
    echo "certbot --nginx -d $DOMAIN"
fi

echo ""
echo "==================================="
echo "Deploy concluído com sucesso!"
echo "==================================="
echo ""
echo "Aplicação rodando em:"
echo "- HTTP: http://$DOMAIN (redireciona para HTTPS)"
echo "- HTTPS: https://$DOMAIN"
echo "- Porta interna: 5006"
echo ""
echo "Próximos passos:"
echo "1. Criar superusuário: docker-compose exec web python manage.py createsuperuser"
echo "2. Acessar: https://$DOMAIN"
echo ""
echo "Comandos úteis:"
echo "- Ver logs: docker-compose logs -f"
echo "- Reiniciar: docker-compose restart"
echo "- Parar: docker-compose down"
echo "- Status: docker-compose ps"
echo ""