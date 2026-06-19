# SecureSab - Sistema de Asistencia Biometrica

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-4.2-green)
![MySQL](https://img.shields.io/badge/MySQL-MariaDB%2010.4-orange)
![License](https://img.shields.io/badge/License-Propietario-red)

## Descripcion

**SecureSab** es un sistema web de gestion de asistencia biometrica desarrollado para el **SENA (Servicio Nacional de Aprendizaje)** de Colombia. Utiliza lectores biometricos **Hikvision** para registrar la entrada y salida de aprendices, instructores y personal mediante huellas dactilares, complementado con gestion de asistencia en ambientes de formacion, control de visitantes y reportes para coordinacion.

El sistema resuelve el problema del control de asistencia en centros de formacion, reemplazando procesos manuales con un sistema automatizado que integra hardware biometrico, gestion por roles y exportacion de reportes.

---

## Caracteristicas Principales

- **Asistencia biometrica automatizada** mediante lector de huellas dactilares Hikvision
- **5 roles diferenciados** con funcionalidades especificas por rol
- **Gestion de asistencia en ambiente de formacion** (aula) por parte de instructores
- **Gestion de visitantes** con registro de entrada/salida por vigilancia
- **Registro manual de asistencia** como respaldo cuando falla el biometrico
- **Sistema de justificacion** de inasistencias con soporte documental
- **Dashboard y reportes** con exportacion a CSV, Excel y PDF
- **Monitoreo en tiempo real** de eventos de huella dactilar
- **Historial de auditoria completo** de todas las acciones del sistema
- **Recuperacion de contrasena** por codigo de verificacion por correo
- **Sincronizacion con dispositivo Hikvision** para usuarios, huellas y eventos
- **Despliegue en la nube** con Azure + Nginx + SSL

---

## Arquitectura del Sistema

```
+---------------------+       +-------------------+       +------------------+
|   Dispositivo       |       |                   |       |                  |
|   Hikvision         |<----->|   SecureSab       |<----->|   MySQL /        |
|   (192.168.1.13)    | HTTP  |   (Django 4.2)    |       |   MariaDB 10.4   |
|   - Huellas         | ISAPI |                   |       |                  |
|   - Reconocimiento  |       |   - Auth/Roles    |       |   Base: secure11 |
+---------------------+       |   - Asistencia    |       +------------------+
                              |   - Reportes      |
+---------------------+       |   - Monitoreo     |       +------------------+
|   Correo SMTP       |<----- |   - Auditoria     |<----->|   Azure VM       |
|   (Gmail)           |       |                   |       |   Ubuntu 24.04   |
+---------------------+       +-------------------+       |   Nginx + SSL    |
                                                          |   Gunicorn       |
+---------------------+       +-------------------+       +------------------+
|   Usuarios          |       |   Frontend        |
|   - Aprendices      |<----->|   HTML/CSS/JS     |
|   - Instructores    |       |   Bootstrap       |
|   - Coordinadores   |       |   Chart.js        |
|   - Vigilantes      |       +-------------------+
|   - Gestores        |
+---------------------+
```

### Flujo de Asistencia Biometrica

```
Aprendiz coloca huella -> Hikvision reconocimiento -> Webhook HTTP POST
    -> Django valida usuario -> Registra asistencia_sede -> Responde al dispositivo
```

---

## Roles del Sistema

| Rol | Modulo | Funciones principales |
|-----|--------|----------------------|
| **Aprendiz** | `/aprendiz/` | Consultar asistencia propia, radicar justificaciones de inasistencia |
| **Instructor** | `/instructor/` | Ver fichas asignadas, gestionar asistencia en ambiente, revisar justificaciones |
| **Coordinador** | `/coordinador/` | Dashboard con KPIs, reportes de asistencia (sede/ambiente), exportar CSV/PDF |
| **Vigilante** | `/vigilante/` | Registrar visitantes, control de entrada/salida, registro manual de asistencia |
| **Gestor** | `/gestor_sistema/` | Administracion completa: CRUD usuarios, gestion de huellas, monitoreo biometrico, reportes, auditoria |

---

## Modelos de Datos

### Autenticacion y Usuarios

| Modelo | Tabla | Descripcion |
|--------|-------|-------------|
| `Usuarios` | `usuarios` | Usuarios del sistema (cedula, nombre, correo, ficha, estado) |
| `Roles` | `roles` | Roles del sistema (aprendiz, instructor, coordinador, vigilante, gestor) |
| `RoleUser` | `role_user` | Relacion usuario-rol |
| `Permissions` | `permissions` | Permisos del sistema |

### Estructura de Formacion

| Modelo | Tabla | Descripcion |
|--------|-------|-------------|
| `Jornada` | `jornada` | Jornadas de formacion (manana, tarde, etc.) |
| `Coordinacion` | `coordinacion` | Unidades de coordinacion |
| `Programa` | `programa` | Programas de formacion |
| `Ficha` | `ficha` | Grupos de formacion (fichas SENA) |
| `Competencia` | `competencia` | Competencias de formacion |
| `FichaInstructor` | `ficha_instructor` | Asignacion ficha-instructor-competencia |
| `ResultadoAprendizaje` | `resultado_aprendizaje` | Resultados de aprendizaje por competencia |

### Asistencia

| Modelo | Tabla | Descripcion |
|--------|-------|-------------|
| `AsistenciaSede` | `asistencia_sede` | Registro de entrada/salida a la sede (biometrico) |
| `AsistenciaAmbiente` | `asistencia_ambiente` | Asistencia en ambiente de formacion (marca instructor) |
| `Justificacion` | `justificacion` | Justificaciones de inasistencia con soporte documental |
| `Novedad` | `novedad` | Novedades e incidentes |

### Biometrico y Seguridad

| Modelo | Tabla | Descripcion |
|--------|-------|-------------|
| `Huella` | `huella` | Plantillas de huellas dactilares |
| `RegistroActividad` | `registro_actividad` | Log completo de auditoria del sistema |
| `HistorialFallos` | `historial_fallos` | Historial de fallos de reconocimiento biometrico |
| `Area` | `areas` | Areas/zonas fisicas de la sede |
| `Visitante` | `visitante` | Registros de visitantes |
| `RegistroManual` | `registro_manual` | Registros manuales de asistencia (respaldo biometrico) |

---

## Tecnologias

| Componente | Tecnologia | Version |
|------------|------------|---------|
| **Backend** | Django | 4.2.16 |
| **Lenguaje** | Python | 3.12 |
| **Base de datos** | MySQL / MariaDB | 10.4.32 (XAMPP) |
| **Servidor local** | XAMPP | Apache + MariaDB |
| **Servidor produccion** | Gunicorn | 23.0.0 |
| **Reverse proxy** | Nginx | - |
| **SO produccion** | Ubuntu Server | 24.04 LTS |
| **Plataforma cloud** | Microsoft Azure | VM B2s v2 (2 vCPU, 8GB RAM) |
| **SSL** | Lets Encrypt | Certificado gratuito |
| **Dispositivo biometrico** | Hikvision | ISAPI (HTTP REST) |
| **Correo** | Gmail SMTP | TLS Puerto 587 |
| **Generacion PDF** | xhtml2pdf / reportlab | 0.2.17 / 4.4.10 |
| **Exportacion Excel** | openpyxl / pandas | 3.1.5 / 3.0.1 |
| **Graficas** | Chart.js | Frontend |

---

## Requisitos Previos

- **Python 3.12** o superior
- **XAMPP** con MySQL/MariaDB activo (puerto 3306)
- **pip** (gestor de paquetes de Python)
- **Git** (para clonar el repositorio)
- **Dispositivo Hikvision** conectado a la red local (opcional, para funcionalidad biometrica)

---

## Instalacion Local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/SecureSab.git
cd Proyecto_SecureSabCarpaxUltimo
```

### 2. Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea el archivo `.env` en la raiz del proyecto:

```env
DATABASE_USER=root
DATABASE_PASSWORD=root
HIKVISION_IP=192.168.1.13
HIKVISION_USER=admin
HIKVISION_PASS=tu_password_hikvision
```

### 5. Configurar base de datos

Asegurate de que XAMPP este corriendo con MySQL activo. La base de datos `secure11` debe existir:

```sql
CREATE DATABASE secure11 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

> **Nota:** Las tablas se gestionan externamente (`managed = False`). El esquema fue disenado originalmente con Laravel y las tablas ya existen en la base de datos de produccion.

### 6. Ejecutar el servidor

```bash
python manage.py runserver
```

El sistema estara disponible en: **http://127.0.0.1:8000**

---

## Variables de Entorno

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| `DATABASE_USER` | Usuario de MySQL | `root` |
| `DATABASE_PASSWORD` | Contrasena de MySQL | `root` |
| `HIKVISION_IP` | Direccion IP del lector biometrico | `192.168.1.13` |
| `HIKVISION_USER` | Usuario del dispositivo Hikvision | `admin` |
| `HIKVISION_PASS` | Contrasena del dispositivo Hikvision | `admin123` |

---

## Estructura del Proyecto

```
Proyecto_SecureSabCarpaxUltimo/
|
|-- config/                         # Configuracion del proyecto Django
|   |-- settings.py                 # Configuracion principal
|   |-- settings_test.py            # Configuracion de pruebas
|   |-- urls.py                     # URLs raiz
|   |-- wsgi.py                     # Punto de entrada WSGI
|
|-- apps/                           # Aplicaciones Django
|   |-- login/                      # Autenticacion y gestion de usuarios
|   |   |-- models.py              # Modelos: Usuarios, Roles, RoleUser, Permissions
|   |   |-- views.py               # Login, logout, perfil, recuperacion contrasena
|   |   |-- selectors/             # Consultas de base de datos
|   |   |-- services/              # Logica de negocio (auth, registro)
|   |   |-- templates/             # login.html, recuperar.html, etc.
|   |   |-- urls.py                # Rutas de autenticacion
|   |
|   |-- gestor_sistema/            # Administracion del sistema (rol: Gestor)
|   |   |-- views.py               # CRUD usuarios, huellas, reportes, monitoreo
|   |   |-- selectors/             # Consultas optimizadas
|   |   |-- services/              # Logica: Hikvision, huellas, auditoria
|   |   |-- templates/             # Panel admin, dashboard, monitoreo, etc.
|   |   |-- urls.py                # Rutas de administracion
|   |
|   |-- gestion_asistencia_justificacion/
|   |   |-- instructor/            # Gestion de asistencia (rol: Instructor)
|   |   |   |-- views.py           # Fichas, asistencia ambiente, justificaciones
|   |   |   |-- templates/         # Fichas, gestion asistencia, reportes PDF
|   |   |
|   |   |-- aprendiz/              # Consulta de asistencia (rol: Aprendiz)
|   |       |-- views.py           # Consultar asistencia, radicar justificacion
|   |       |-- templates/         # consultar_asistencia.html, etc.
|   |
|   |-- reporte_monitoreo/
|   |   |-- coordinador/           # Reportes y monitoreo (rol: Coordinador)
|   |       |-- views.py           # Dashboard, reportes, exportaciones
|   |       |-- templates/         # Dashboard, asistencia, justificaciones
|   |
|   |-- seguridad_administracion/
|   |   |-- vigilante/             # Control de visitantes (rol: Vigilante)
|   |       |-- views.py           # Visitantes, registro manual, historial
|   |       |-- templates/         # Registro, consulta, historial
|   |
|   |-- core/                      # App base (placeholder)
|
|-- media/                          # Archivos subidos
|   |-- justificaciones/           # Soportes de justificacion
|
|-- static/                         # Archivos estaticos (CSS, JS, imagenes)
|-- templates/                      # Templates globales (base.html, menu.html)
|-- requirements.txt                # Dependencias de Python
|-- manage.py                       # Script de gestion de Django
|-- .env                            # Variables de entorno (no incluir en Git)
|-- deploy.sh                       # Script de despliegue en Azure
```

---

## Despliegue en Azure

### Configuracion de la VM

| Parametro | Valor |
|-----------|-------|
| **Proveedor** | Microsoft Azure |
| **Servicio** | Maquina Virtual |
| **SO** | Ubuntu Server 24.04 LTS |
| **Tamano** | Standard B2s v2 (2 vCPU, 8 GB RAM) |
| **IP Publica** | 158.23.17.242 |
| **Dominio** | securesab.app |

### Stack de produccion

```
Internet -> Nginx (Puerto 443/SSL) -> Gunicorn (Puerto 8000) -> Django -> MySQL (Puerto 3306)
```

### Pasos de despliegue

#### 1. Configurar la VM

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install python3.12 python3.12-venv python3-pip nginx certbot python3-certbot-nginx mysql-server -y

# Crear usuario de despliegue
sudo adduser deploy
sudo usermod -aG sudo deploy
```

#### 2. Configurar MySQL

```bash
sudo mysql_secure_installation

# Crear base de datos
sudo mysql -u root -p
```

```sql
CREATE DATABASE secure11 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE USER 'secure_user'@'localhost' IDENTIFIED BY 'tu_password_seguro';
GRANT ALL PRIVILEGES ON secure11.* TO 'secure_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 3. Desplegar la aplicacion

```bash
# Clonar repositorio
cd /home/deploy
git clone https://github.com/tu-usuario/SecureSab.git
cd Proyecto_SecureSabCarpaxUltimo

# Crear entorno virtual
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
nano .env    # Editar variables de entorno

# Recolectar archivos estaticos
python manage.py collectstatic --noinput
```

#### 4. Configurar Gunicorn como servicio systemd

Crear `/etc/systemd/system/secureSab.service`:

```ini
[Unit]
Description=SecureSab Django Application
After=network.target mysql.service

[Service]
User=deploy
Group=www-data
WorkingDirectory=/home/deploy/Proyecto_SecureSabCarpaxUltimo
ExecStart=/home/deploy/Proyecto_SecureSabCarpaxUltimo/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/secureSab.sock \
    config.wsgi:application

Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable secureSab
sudo systemctl start secureSab
```

#### 5. Configurar Nginx

Crear `/etc/nginx/sites-available/secureSab`:

```nginx
server {
    listen 80;
    server_name securesab.app www.securesab.app;

    location /static/ {
        alias /home/deploy/Proyecto_SecureSabCarpaxUltimo/staticfiles/;
    }

    location /media/ {
        alias /home/deploy/Proyecto_SecureSabCarpaxUltimo/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/secureSab.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/secureSab /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Configurar SSL con Lets Encrypt

```bash
sudo certbot --nginx -d securesab.app -d www.securesab.app
sudo certbot renew --dry-run    # Verificar renovacion automatica
```

### Script de despliegue automatico

El archivo `deploy.sh` ejecuta:

```bash
#!/bin/bash
cd /home/deploy/Proyecto_SecureSabCarpaxUltimo
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl restart secureSab
sudo systemctl restart nginx
```

---

## Integracion con Hikvision

### Dispositivo compatible

- **Modelo:** Lectores biometricos Hikvision con soporte ISAPI
- **IP configurable:** `192.168.1.13` (en `.env`)

### Funcionalidades implementadas

| Funcion | Endpoint ISAPI | Metodo |
|---------|---------------|--------|
| Sincronizar usuarios | `/ISAPI/AccessControl/UserInfo/Record` | PUT |
| Capturar huella | `/ISAPI/AccessControl/CaptureFingerPrint` | POST |
| Subir huella al dispositivo | `/ISAPI/AccessControl/UserInfo/Modify` | PUT |
| Obtener eventos de reconocimiento | `/ISAPI/AccessControl/AcsEvent` | GET |
| Eliminar usuario del dispositivo | `/ISAPI/AccessControl/UserInfo/Delete` | PUT |
| Webhook en tiempo real | `/gestor_sistema/webhook/huella/` | POST |

### Flujo de reconocimiento

1. El dispositivo Hikvision detecta una huella y la compara con las almacenadas
2. Si hay coincidencia, envia un evento HTTP POST al webhook de Django
3. Django valida el usuario, registra la asistencia en `asistencia_sede`
4. Se almacena en cache para monitoreo en tiempo real
5. El gestor puede ver los eventos en el modulo de monitoreo

---

## Endpoints Principales

### Autenticacion

| Ruta | Descripcion |
|------|-------------|
| `/login/` | Inicio de sesion |
| `/login/logout/` | Cerrar sesion |
| `/login/perfil/` | Mi perfil |
| `/login/recuperar/` | Recuperar contrasena |

### Aprendiz

| Ruta | Descripcion |
|------|-------------|
| `/aprendiz/consultar-asistencia/` | Consultar mi asistencia |
| `/aprendiz/radicar-justificacion/` | Radicar justificacion |

### Instructor

| Ruta | Descripcion |
|------|-------------|
| `/instructor/fichas/` | Mis fichas asignadas |
| `/instructor/fichas/gestionar-asistencia/` | Registrar asistencia en ambiente |
| `/instructor/gestionar-justificaciones/` | Revisar justificaciones |

### Coordinador

| Ruta | Descripcion |
|------|-------------|
| `/coordinador/` | Dashboard principal |
| `/coordinador/asistencia-ambiente/` | Asistencia en ambiente |
| `/coordinador/asistencia-sede/` | Asistencia en sede |
| `/coordinador/justificaciones/` | Justificaciones |

### Vigilante

| Ruta | Descripcion |
|------|-------------|
| `/vigilante/iniciov/` | Panel de vigilancia |
| `/vigilante/registrar-invitado/` | Registrar visitante |
| `/vigilante/registro-manual/` | Registro manual |
| `/vigilante/historial/` | Historial de movimientos |

### Gestor del Sistema

| Ruta | Descripcion |
|------|-------------|
| `/gestor_sistema/` | Panel de administracion |
| `/gestor_sistema/crear-usuario/` | Crear usuario |
| `/gestor_sistema/huellas/` | Gestion de huellas |
| `/gestor_sistema/webhook/huella/` | Webhook biometrico |
| `/gestor_sistema/monitoreo/` | Monitoreo en tiempo real |
| `/gestor_sistema/reportes/` | Reportes |
| `/gestor_sistema/registro-actividad/` | Auditoria del sistema |

---

## Troubleshooting

### MySQL no inicia en XAMPP

**Causa mas comun:** Puerto 3306 ocupado por otra instancia.

```bash
# Verificar que usa el puerto
netstat -ano | findstr :3306

# Matar proceso problematico (ejecutar como Administrador)
taskkill /PID <numero_pid> /F

# Reiniciar MySQL desde XAMPP
```

**Tabla corrupta:** Si el error dice "Table is marked as crashed":

```bash
# Detener MySQL en XAMPP, luego ejecutar:
C:\xampp\mysql\bin\aria_chk.exe --safe-recover --force C:\xampp\mysql\data\<base>\<tabla>.MAI
```

**Servicio Windows MySQL80 compitiendo:**

```bash
# Deshabilitar (ejecutar como Administrador)
sc config MySQL80 start= disabled
net stop MySQL80
```

### El dispositivo Hikvision no responde

1. Verificar que el dispositivo este encendido y en la misma red
2. Hacer ping a la IP configurada (`192.168.1.13`)
3. Verificar credenciales en el archivo `.env`
4. Asegurarse de que no hay un firewall bloqueando el puerto 80

### Errores de CORS o conexiones rechazadas

Verificar que la IP del servidor Django este autorizada en la configuracion del dispositivo Hikvision.

---

## Creditos

Desarrollado como proyecto de formacion para el SENA - Servicio Nacional de Aprendizaje (Colombia).

---

> **Nota:** Este sistema utiliza una base de datos con esquema gestionado externamente (originalmente disenado con Laravel). Los modelos Django utilizan `managed = False` para trabajar sobre las tablas existentes.
