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

sudo tee /etc/nginx/sites-available/securesab > /dev/null <<'NGINXEOF'
server {
    listen 80;
    server_name 158.23.17.242;

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

sudo systemctl daemon-reload
sudo systemctl enable gunicorn

echo "=== Setup completado ==="
