#!/bin/bash
set -e

echo "=== Deploy iniciado ==="
cd /home/azureuser/securesab_project

# Ejecutar setup del servidor (nginx, SSL, systemd)
bash scripts/setup_server.sh

echo "1. Guardando configuracion local..."
mkdir -p /tmp/deploy_backup
cp config/settings.py /tmp/deploy_backup/settings.py
cp .env /tmp/deploy_backup/.env 2>/dev/null || true

echo "2. Stashing local changes..."
git stash --include-untracked 2>/dev/null || true

echo "3. Pulling latest code..."
git pull origin main

echo "4. Restaurando configuracion del servidor..."
cp /tmp/deploy_backup/settings.py config/settings.py
cp /tmp/deploy_backup/.env .env 2>/dev/null || true

echo "5. Instalando/actualizando dependencias..."
source venv/bin/activate
pip install -r requirements.txt

echo "6. Ejecutando migraciones..."
python manage.py migrate --noinput

echo "7. Running collectstatic..."
python manage.py collectstatic --noinput 2>&1

echo "8. Sincronizando archivos estaticos..."
sudo mkdir -p /var/www/securesab-static
sudo cp -r staticfiles/* /var/www/securesab-static/

echo "9. Renovando certificado SSL (si aplica)..."
sudo certbot renew --quiet --no-self-upgrade 2>/dev/null || true

echo "10. Reiniciando Gunicorn..."
sudo systemctl restart gunicorn

echo "11. Verificando deploy..."
for i in $(seq 1 10); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
  if [ "$STATUS" = "200" ]; then
    echo "=== Deploy exitoso! HTTP $STATUS ==="
    git stash drop 2>/dev/null || true
    exit 0
  fi
  echo "Intento $i/10 - HTTP $STATUS, esperando..."
  sleep 2
done

echo "=== Deploy fallido después de 10 intentos ==="
exit 1
