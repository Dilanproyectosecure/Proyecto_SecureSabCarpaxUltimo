# Documento de Instalacion - Servidor Azure (SecureSab)

## 1. Configuracion de la Maquina Virtual en Azure

| Campo | Valor |
|---|---|
| **Nombre** | securesab-server |
| **Sistema Operativo** | Ubuntu 24.04.4 LTS (Noble Numbat) |
| **Tamano** | Standard B2s v2 (2 vCPU, 8 GB RAM) |
| **Arquitectura** | x64 |
| **Ubicacion** | Mexico Central |
| **IP Publica** | 158.23.17.242 |
| **IP Privada** | 172.16.0.4 |
| **Grupo de Recursos** | SecureSAB-RG |
| **Subscripcion** | Azure for Students |
| **Virtual Network** | vnet-mexicocentral-1 / subnet-mexicocentral-1 |
| **Fecha de Creacion** | 26/05/2026 |

---

## 2. Servicios Instalados en el Servidor

| Servicio | Version | Puerto | Estado |
|---|---|---|---|
| **SSH** | OpenSSH | 22 | Activo |
| **Nginx** | 1.24.0 | 80, 443 | Activo |
| **MySQL** | Community Server | 3306 (solo local) | Activo |
| **Python** | 3.12.3 | - | Instalado |
| **Django** | 6.0.6 | - | Instalado (venv) |
| **Gunicorn** | 23.0.0 | - | Instalado |

---

## 3. Arquitectura del Servidor

```
Internet (securesab.app)
  |
  v
[puerto 80/443] --> Nginx (reverse proxy + SSL Let's Encrypt)
  |
  v
[puerto 127.0.0.1:8000] --> Django (manage.py runserver)
  |
  v
[puerto 127.0.0.1:3306] --> MySQL (solo accesible desde localhost)
```

---

## 4. Estructura de Archivos

```
/home/azureuser/securesab_project/
|-- apps/                  # Aplicaciones Django
|-- config/                # Configuracion del proyecto
|-- core/                  # Modulos core
|-- scripts/               # Scripts de deploy y setup
|-- staticfiles/           # Archivos estaticos recolectados
|-- media/                 # Archivos subidos por usuarios
|-- venv/                  # Entorno virtual Python
|-- manage.py              # Script de gestion de Django
|-- requirements.txt       # Dependencias Python
|-- deploy.sh              # Script de despliegue automatico
|-- .env                   # Variables de entorno
```

---

## 5. Base de Datos MySQL

| Campo | Valor |
|---|---|
| **Host** | localhost (127.0.0.1) |
| **Puerto** | 3306 |
| **Usuario** | root |
| **Contrasena** | root |
| **Base de datos** | secure11 |
| **Charset** | utf8mb4 |
| **Total de tablas** | 47 |

### Tablas principales:
- `usuarios` - Usuarios del sistema
- `ficha` - Fichas de formacion
- `asistencia_sede` - Asistencia por sede
- `asistencia_ambiente` - Asistencia por ambiente
- `justificacion` - Justificaciones
- `huella` - Huellas digitales
- `reportes` - Reportes generados
- `roles` / `permissions` - Sistema de permisos

---

## 6. Configuracion Nginx

**Archivo:** `/etc/nginx/sites-available/securesab`

```nginx
server {
    server_name securesab.app www.securesab.app;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/securesab-static/;
    }

    location /media/ {
        alias /home/azureuser/securesab_project/media/;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/securesab.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/securesab.app/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if ($host = www.securesab.app) {
        return 301 https://$host$request_uri;
    }
    if ($host = securesab.app) {
        return 301 https://$host$request_uri;
    }
    listen 80;
    server_name securesab.app www.securesab.app;
    return 404;
}
```

---

## 7. Certificados SSL (Let's Encrypt)

| Campo | Valor |
|---|---|
| **Dominio** | securesab.app, www.securesab.app |
| **Tipo de llave** | ECDSA |
| **Vencimiento** | 12/09/2026 |
| **Certificado** | /etc/letsencrypt/live/securesab.app/fullchain.pem |
| **Llave privada** | /etc/letsencrypt/live/securesab.app/privkey.pem |

---

## 8. Firewall (UFW)

| Puerto | Protocolo | Acceso |
|---|---|---|
| 22 | TCP | Abierto (SSH) |
| 80 | TCP | Abierto (HTTP) |
| 443 | TCP | Abierto (HTTPS) |
| 8000 | TCP | Abierto (Django) |

---

## 9. Comandos Utiles

```bash
# Conectarse al servidor
ssh -i "C:\Users\migue\Downloads\clave-securesab-pc2.pem" azureuser@158.23.17.242

# Entrar al entorno virtual
cd ~/securesab_project && source venv/bin/activate

# Iniciar Django
python manage.py runserver 0.0.0.0:8000

# Ver bases de datos
mysql -u root -proot -e "SHOW DATABASES;"

# Ver tablas de secure11
mysql -u root -proot -e "USE secure11; SHOW TABLES;"

# Verificar Nginx
sudo nginx -t && sudo systemctl reload nginx

# Renovar SSL
sudo certbot renew --dry-run

# Deploy
cd ~/securesab_project && bash deploy.sh
```

---

## 10. Variables de Entorno (.env)

```
DATABASE_PASSWORD=root
GMAIL_APP_PASSWORD=unkjhiyrivblzlem
```

---

## 11. Dependencias Principales

| Paquete | Version | Uso |
|---|---|---|
| Django | 6.0.6 | Framework web |
| PyMySQL | 1.1.2 | Conexion MySQL |
| gunicorn | 23.0.0 | Servidor WSGI |
| reportlab | 4.4.10 | Generacion PDF |
| openpyxl | 3.1.5 | Archivos Excel |
| selenium | 4.33.0 | Automatizacion web |
| pyTelegramBotAPI | 4.27.0 | Bot Telegram |
| twilio | 9.6.2 | Mensajeria SMS |
| pillow | 12.1.1 | Manejo de imagenes |
| xhtml2pdf | 0.2.17 | HTML a PDF |
| cryptography | 46.0.5 | Encriptacion |

---

*Documento generado el 16/06/2026*
