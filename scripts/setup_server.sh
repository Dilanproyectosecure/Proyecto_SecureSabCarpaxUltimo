#!/bin/bash
# Setup inicial del servidor (ejecutar solo la primera vez)
set -e

echo "=== Setup inicial del servidor ==="

mkdir -p /home/azureuser/securesab_project/logs

sudo tee /etc/systemd/system/gunicorn.service > /dev/null <<'SERVICEEOF'
[Unit]
Description=Gunicorn daemon for SecureSAB
After=network.target mysql.service

[Service]
Type=simple
User=azureuser
Group=azureuser
WorkingDirectory=/home/azureuser/securesab_project
ExecStart=/home/azureuser/securesab_project/venv/bin/gunicorn config.wsgi:application -c config/gunicorn.conf.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

# --- Instalar Certbot si no está presente ---
if ! command -v certbot &>/dev/null; then
    echo "Instalando Certbot..."
    sudo apt-get update -qq && sudo apt-get install -y -qq certbot python3-certbot-nginx
fi

# --- Obtener certificado SSL si no existe ---
if [ ! -d "/etc/letsencrypt/live/securesab.app" ]; then
    echo "Obteniendo certificado SSL para securesab.app..."
    sudo certbot --nginx -d securesab.app -d www.securesab.app --non-interactive --agree-tos -m securesabsena@gmail.com || true
fi

# --- Configuración de Nginx ---
sudo tee /etc/nginx/sites-available/securesab > /dev/null <<'NGINXEOF'
server {
    listen 80;
    server_name securesab.app www.securesab.app 158.23.17.242;

    # Redirección permanente a HTTPS (solo para dominios)
    if ($host != "158.23.17.242") {
        return 301 https://$host$request_uri;
    }

    location /static/ {
        alias /var/www/securesab-static/;
    }

    location /media/ {
        alias /home/azureuser/securesab_project/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl;
    server_name securesab.app www.securesab.app;

    ssl_certificate /etc/letsencrypt/live/securesab.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/securesab.app/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location /static/ {
        alias /var/www/securesab-static/;
    }

    location /media/ {
        alias /home/azureuser/securesab_project/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINXEOF

sudo ln -sf /etc/nginx/sites-available/securesab /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# --- Programar renovación automática de Certbot ---
echo "0 0,12 * * * root certbot renew --quiet --no-self-upgrade" | sudo tee /etc/cron.d/certbot-renew

sudo systemctl daemon-reload
sudo systemctl enable gunicorn

echo "=== Setup completado ==="
