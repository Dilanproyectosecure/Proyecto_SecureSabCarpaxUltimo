import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime
from django.core.cache import cache
from django.utils import timezone

from apps.login.models import Usuarios
from .models import Huella
from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente
from .services import registrar_asistencia_sede_por_huella


# =========================
# CONFIGURACIÓN DISPOSITIVO
# =========================
IP = "192.168.1.13"
USER = "admin"
PASS = "Dilan1105"


# =========================
# 1. ENVIAR USUARIO A HIKVISION
# =========================
def enviar_usuario_hikvision(usuario):
    url = f"http://{IP}/ISAPI/AccessControl/UserInfo/Record?format=json"

    data = {
        "UserInfo": {
            "employeeNo": str(usuario.id_usuario),
            "name": f"{usuario.nombre}",
            "userType": "normal",
            "Valid": {
                "enable": True,
                "beginTime": "2026-01-01T00:00:00",
                "endTime": "2030-12-31T23:59:59"
            }
        }
    }

    try:
        r = requests.post(
            url,
            json=data,
            auth=HTTPDigestAuth(USER, PASS),
            timeout=10
        )

        if r.status_code in [200, 201] or "deviceUserAlreadyExist" in r.text:
            print("✅ Usuario enviado o ya existe en dispositivo")
            return True

        print("❌ Error al enviar usuario:", r.text)
        return False

    except Exception as e:
        print("❌ Error conexión Hikvision:", e)
        return False


# =========================
# 2. ACTIVAR CAPTURA DE HUELLA
# =========================
def _respuesta_hikvision_ok(status_code, body):
    if status_code not in [200, 201]:
        return False

    texto = (body or "").lower()
    errores = [
        "badauthorization",
        "invalid operation",
        "messageparameterslack",
        "invalid xml content",
        "parameter error",
    ]
    if any(err in texto for err in errores):
        return False

    # Algunos equipos responden con statusCode=1 cuando la operacion es exitosa.
    if "<statuscode>1</statuscode>" in texto:
        return True

    return True


def obtener_ultima_huella_capturada(employee_no, timeout_segundos=30):
    """
    Intenta obtener la huella capturada RE-ENVIANDO el comando CaptureFingerPrint.
    El dispositivo almacena la huella y la devuelve en la siguiente llamada.
    """
    import time
    import re
    
    inicio = time.time()
    intento = 0
    
    print(f"🔄 Polling: Re-enviando comando CaptureFingerPrint para obtener huella...")
    
    # Payload xml-2 que devuelve la huella si está disponible
    url_xml = f"http://{IP}/ISAPI/AccessControl/CaptureFingerPrint"
    payload_xml2 = f"""
<CaptureFingerPrintCond version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <employeeNo>{employee_no}</employeeNo>
    <fingerNo>1</fingerNo>
    <fingerPrintID>1</fingerPrintID>
</CaptureFingerPrintCond>
"""
    
    while (time.time() - inicio) < timeout_segundos:
        intento += 1
        
        try:
            # Re-enviar xml-2, que es el que devuelve CaptureFingerPrint con fingerData
            r = requests.post(
                url_xml,
                data=payload_xml2,
                auth=HTTPDigestAuth(USER, PASS),
                headers={"Content-Type": "application/xml"},
                timeout=5
            )
            
            respuesta = r.text or ""
            
            # Buscar fingerData en la respuesta
            if respuesta and len(respuesta) > 100:
                # Primero buscar <CaptureFingerPrint> que indica huella capturada
                if "<CaptureFingerPrint" in respuesta or "<fingerData>" in respuesta:
                    match = re.search(r'<fingerData>(.*?)</fingerData>', respuesta, re.DOTALL)
                    if match:
                        plantilla = match.group(1).strip()
                        if plantilla and len(plantilla) > 100:
                            print(f"✅ Huella capturada encontrada en intento {intento}: {plantilla[:50]}...")
                            return plantilla
        
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            pass
        
        if intento % 3 == 0:
            print(f"⏳ Polling... ({intento}s de {timeout_segundos}s)")
        
        time.sleep(0.5)  # Re-intentar cada 0.5s para más rapidez
    
    print(f"❌ Timeout esperando huella después de {timeout_segundos}s")
    return None


def iniciar_registro_huella(employee_no):
    url_xml = f"http://{IP}/ISAPI/AccessControl/CaptureFingerPrint"
    url_json = f"http://{IP}/ISAPI/AccessControl/CaptureFingerPrint?format=json"

    payloads = [
        {
            "tipo": "xml-1",
            "url": url_xml,
            "headers": {"Content-Type": "application/xml"},
            "data": f"""
<CaptureFingerPrint version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <employeeNo>{employee_no}</employeeNo>
    <fingerNo>1</fingerNo>
</CaptureFingerPrint>
""",
        },
        {
            "tipo": "xml-2",
            "url": url_xml,
            "headers": {"Content-Type": "application/xml"},
            "data": f"""
<CaptureFingerPrintCond version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <employeeNo>{employee_no}</employeeNo>
    <fingerNo>1</fingerNo>
    <fingerPrintID>1</fingerPrintID>
</CaptureFingerPrintCond>
""",
        },
    ]

    ultima_respuesta = ""

    try:
        for intento in payloads:
            r = requests.post(
                intento["url"],
                data=intento["data"],
                auth=HTTPDigestAuth(USER, PASS),
                headers=intento["headers"],
                timeout=10,
            )

            ultima_respuesta = r.text or ""
            print(f"📡 Respuesta dispositivo ({intento['tipo']}): {ultima_respuesta[:150]}...")

            if _respuesta_hikvision_ok(r.status_code, ultima_respuesta):
                print(f"✅ Comando de captura enviado exitosamente")
                # Ahora ESPERAR Y HACER POLLING RE-ENVIANDO el comando para obtener la huella
                print(f"⏳ Esperando huella... (máx. 20s)")
                finger_data = obtener_ultima_huella_capturada(employee_no, timeout_segundos=20)
                
                if finger_data:
                    return {
                        "ok": True,
                        "status_code": r.status_code,
                        "raw": ultima_respuesta,
                        "payload_usado": intento["tipo"],
                        "huella": finger_data,
                    }
                else:
                    # Continuar intentando con otro payload si no se capturó
                    print(f"⚠️ No se capturó huella con {intento['tipo']}, intentando siguiente...")
                    continue

        return {
            "ok": False,
            "status_code": 502,
            "raw": ultima_respuesta,
            "error": "No se pudo capturar la huella con ningún método",
        }

    except Exception as e:
        print("❌ Error iniciar huella:", e)
        return {
            "ok": False,
            "error": f"Error de conexion con Hikvision: {e}"
        }


# =========================
# 3. OBTENER EVENTOS DEL DISPOSITIVO
# =========================
def obtener_eventos():
    url = f"http://{IP}/ISAPI/AccessControl/AcsEvent?format=json"

    payload = {
        "AcsEventCond": {
            "searchID": "1",
            "searchResultPosition": 0,
            "maxResults": 50,
            "major": 0,
            "minor": 0,
            "startTime": "2026-01-01T00:00:00Z",
            "endTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    }

    try:
        r = requests.post(
            url,
            json=payload,
            auth=HTTPDigestAuth(USER, PASS),
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if r.status_code == 200:
            return r.json()

        print("❌ Error eventos:", r.text)
        return {}

    except Exception as e:
        print("❌ Error conexión eventos:", e)
        return {}


# =========================
# 4. PROCESAR HUELLA EN TIEMPO REAL
# =========================
def procesar_eventos():
    data = obtener_eventos()

    eventos = data.get("AcsEvent", {}).get("InfoList", [])

    for evento in eventos:
        employee_no = evento.get("employeeNoString") or evento.get("employeeNo")
        raw_time = evento.get("time")

        # Parsear timestamp ISO (ej: 2026-01-30T00:28:20+08:00) a fecha
        fecha = None
        if raw_time:
            try:
                # datetime.fromisoformat soporta offsets como +08:00
                dt = datetime.fromisoformat(raw_time)
                fecha = dt.date()
            except Exception:
                try:
                    # Intentar truncar la zona y parsear como fallback
                    dt = datetime.fromisoformat(raw_time.split("+")[0].rstrip("Z"))
                    fecha = dt.date()
                except Exception:
                    fecha = datetime.now().date()

        if not employee_no:
            continue


        try:
            # Buscar en el modelo de usuarios del app `login` (clase `Usuarios`),
            # que es el tipo esperado por las FK de AsistenciaSede.
            usuario = Usuarios.objects.filter(id_usuario=employee_no).first()
            if not usuario:
                usuario = Usuarios.objects.filter(cedula=employee_no).first()

            if not usuario:
                print("⚠ Usuario no existe:", employee_no)
                continue

            resultado = registrar_asistencia_sede_por_huella(usuario)

            if resultado["estado"] == "entrada":
                print(f"✔ Entrada registrada: {usuario.nombre}")
            elif resultado["estado"] == "salida":
                print(f"✔ Salida registrada: {usuario.nombre}")
            else:
                print(f"⚠ Ya tenía entrada y salida hoy: {usuario.nombre}")

            cache.set("ultima_huella", {
                "nombre": usuario.nombre,
                "hora": datetime.now().strftime("%H:%M:%S"),
                "estado": resultado["estado"],
            }, timeout=20)

        except Exception as e:
            print("❌ Error procesando evento de huella:", e)


# =========================
# 5. REGISTRO DIRECTO DE HUELLA (OPCIONAL)
# =========================
def enrollar_huella(employee_no, datos_huella, finger_no=1):
    """
    Enrolla la huella capturada en el dispositivo para que pueda usarla en reconocimiento.
    El dispositivo procesa internamente la plantilla para optimizarla.
    Retorna la plantilla después de ser enrolada (dispositivo la tiene lista para usar).
    """
    url = f"http://{IP}/ISAPI/AccessControl/FingerPrintManager/Enroll?format=json"
    
    payload = {
        "Enroll": {
            "employeeNo": str(employee_no),
            "fingerNo": finger_no,
            "fingerData": datos_huella
        }
    }
    
    try:
        r = requests.post(
            url,
            json=payload,
            auth=HTTPDigestAuth(USER, PASS),
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        respuesta = r.text or ""
        print(f"📝 Respuesta enrolamiento: {respuesta[:200]}...")
        
        if r.status_code in [200, 201, 204] and "error" not in respuesta.lower():
            # Enrolamiento exitoso - el dispositivo ya procesó la plantilla internamente
            print(f"✅ Huella enrolada exitosamente en el dispositivo")
            return {
                "ok": True,
                "status_code": r.status_code,
                "raw": respuesta,
                "plantilla_enrolada": datos_huella  # El dispositivo ya tiene la versión procesada
            }
        
        return {
            "ok": False,
            "status_code": r.status_code,
            "raw": respuesta,
            "error": "Dispositivo rechazó el enrolamiento"
        }
    
    except Exception as e:
        print(f"❌ Error enrolando huella: {e}")
        return {"ok": False, "error": str(e)}


def registrar_huella_hikvision(usuario):
    # Hikvision registra al usuario con employeeNo = id_usuario.
    return iniciar_registro_huella(usuario.id_usuario)


def obtener_huella_capturada(employee_no, esperar_segundos=45):
    """
    DEPRECADO: La huella ahora se obtiene directamente de la respuesta de CaptureFingerPrint.
    Esta función se mantiene por compatibilidad pero no hace nada.
    """
    # Ya no hacemos polling aquí - los datos vienen en la respuesta de captura
    print("⚠️ obtener_huella_capturada() es deprecated - usa registrar_huella_hikvision() directamente")
    return {"ok": False, "error": "Deprecated - use registrar_huella_hikvision()"}


# =========================
# 7. GUARDAR HUELLA A ARCHIVO TEMPORAL (JSON)
# =========================
def guardar_huella_a_archivo(usuario_id, datos_huella):
    """
    Guarda la huella en un archivo JSON temporal como paso intermedio.
    """
    import json
    import os
    
    # Ruta de carpeta temporal para huellas
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp_huellas')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Archivo JSON con nombre único por usuario
    archivo_json = os.path.join(temp_dir, f"huella_{usuario_id}_{datetime.now().timestamp()}.json")
    
    try:
        datos = {
            "id_usuario": usuario_id,
            "datos_huella_dactilar": datos_huella,
            "fecha_captura": datetime.now().isoformat(),
            "timestamp": datetime.now().timestamp()
        }
        
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Datos de huella guardados en: {archivo_json}")
        return {"ok": True, "archivo": archivo_json}
    
    except Exception as e:
        print(f"❌ Error guardando archivo JSON: {e}")
        return {"ok": False, "error": str(e)}


# =========================
# 8. GUARDAR HUELLA EN BD
# =========================
def guardar_huella_en_bd(usuario, datos_huella):
    """
    Guarda la huella capturada en la tabla 'huella'.
    """
    try:
        huella, created = Huella.objects.update_or_create(
            usuario=usuario,
            defaults={
                'datos_huella_dactilar': datos_huella,
                'fecha_registro': timezone.now(),
                'tiene_huella': True
            }
        )
        
        if created:
            print(f"✅ Huella guardada en BD para {usuario.nombre}")
        else:
            print(f"✅ Huella actualizada en BD para {usuario.nombre}")
        
        return {
            "ok": True,
            "id_huella": huella.id_huella,
            "mensaje": "Huella guardada correctamente"
        }
    
    except Exception as e:
        print(f"❌ Error guardando huella: {e}")
        return {
            "ok": False,
            "error": f"Error al guardar huella: {str(e)}"
        }


def subir_huella_a_dispositivo(employee_no, datos_huella, finger_no=1):
    """
    Sube la plantilla de huella al dispositivo Hikvision.
    Intenta múltiples variantes de payload y valida que la huella quede persistida.
    """
    import re
    import time

    employee_no = str(employee_no)

    ultima_respuesta = ""

    def _verificar_huella_persistida():
        url_verificacion = f"http://{IP}/ISAPI/AccessControl/FingerPrint/Search?format=json"
        payload_verificacion = {
            "FingerPrintCond": {
                "searchID": str(int(time.time())),
                "searchResultPosition": 0,
                "maxResults": 10,
                "employeeNo": employee_no,
            }
        }
        try:
            r_ver = requests.post(
                url_verificacion,
                json=payload_verificacion,
                auth=HTTPDigestAuth(USER, PASS),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            texto_ver = r_ver.text or ""
            print(f"🔎 Verificando huella en dispositivo: {r_ver.status_code}")
            print(f"🔎 Respuesta verificación: {texto_ver[:200]}...")

            if r_ver.status_code not in [200, 201]:
                return False, texto_ver

            patrones = [
                r'"fingerData"\s*:\s*"([^"]+)"',
                r'"fingerPrintData"\s*:\s*"([^"]+)"',
                r'<fingerData>(.*?)</fingerData>',
                r'<fingerPrintData>(.*?)</fingerPrintData>',
                r'"FingerPrint"\s*:\s*\[(.*?)\]',
            ]
            for patron in patrones:
                match = re.search(patron, texto_ver, re.DOTALL)
                if match:
                    plantilla = match.group(1).strip()
                    if plantilla and (employee_no in texto_ver or len(plantilla) > 100):
                        print(f"✅ Huella verificada en dispositivo: {plantilla[:50]}...")
                        return True, texto_ver

            if employee_no in texto_ver and ("fingerData" in texto_ver or "fingerPrintData" in texto_ver):
                print("✅ Huella verificada en dispositivo por coincidencia de employeeNo")
                return True, texto_ver

            return False, texto_ver
        except Exception as e:
            print(f"⚠️ Error verificando huella en dispositivo: {e}")
            return False, str(e)

    def _probar_payload(url, payload, method_name, content_type="application/json", http_method="post"):
        nonlocal ultima_respuesta
        try:
            request_kwargs = {
                "auth": HTTPDigestAuth(USER, PASS),
                "headers": {"Content-Type": content_type},
                "timeout": 15,
            }

            if content_type == "application/xml":
                request_kwargs["data"] = payload
            else:
                request_kwargs["json"] = payload

            response = requests.request(http_method.upper(), url, **request_kwargs)

            ultima_respuesta = response.text or ""
            print(f"📡 Respuesta subida huella ({method_name}): {ultima_respuesta[:200]}...")

            if response.status_code in [200, 201, 204]:
                texto = (ultima_respuesta or "").lower()
                if "notsupport" in texto or "invalid" in texto or "failed" in texto:
                    return False

                time.sleep(0.8)
                verificada, respuesta_ver = _verificar_huella_persistida()
                if verificada:
                    return True

                print(f"⚠️ El dispositivo aceptó la petición, pero no devolvió la huella al verificarla")
                print(f"⚠️ Verificación cruda: {respuesta_ver[:200]}...")

            return False
        except Exception as e:
            print(f"⚠️ Error en {method_name}: {e}")
            return False

    url_userinfo_json = f"http://{IP}/ISAPI/AccessControl/UserInfo/Record?format=json"
    url_userinfo_xml = f"http://{IP}/ISAPI/AccessControl/UserInfo/Record"
    url_fingerprint = f"http://{IP}/ISAPI/AccessControl/FingerPrint/Record"

    payload_json_1 = {
        "UserInfo": {
            "employeeNo": str(employee_no),
            "name": str(employee_no),
            "userType": "normal",
            "Valid": {
                "enable": True,
                "beginTime": "2026-01-01T00:00:00",
                "endTime": "2030-12-31T23:59:59",
            },
            "FingerPrintList": {
                "FingerPrint": [
                    {
                        "fingerNo": finger_no,
                        "fingerType": "normalFp",
                        "fingerData": datos_huella,
                    }
                ]
            },
        }
    }

    payload_json_2 = {
        "UserInfo": {
            "employeeNo": str(employee_no),
            "name": str(employee_no),
            "userType": "normal",
            "Valid": {
                "enable": True,
                "beginTime": "2026-01-01T00:00:00",
                "endTime": "2030-12-31T23:59:59",
            },
            "FingerPrintList": {
                "FingerPrint": [
                    {
                        "fingerNo": finger_no,
                        "fingerType": "normalFp",
                        "fingerPrintData": datos_huella,
                    }
                ]
            },
        }
    }

    payload_xml = f"""
<UserInfoList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <UserInfo>
        <employeeNo>{employee_no}</employeeNo>
        <name>{employee_no}</name>
        <userType>normal</userType>
        <Valid>
            <enable>true</enable>
            <beginTime>2026-01-01T00:00:00</beginTime>
            <endTime>2030-12-31T23:59:59</endTime>
        </Valid>
        <FingerPrintList>
            <FingerPrint>
                <fingerNo>{finger_no}</fingerNo>
                <fingerType>normalFp</fingerType>
                <fingerData>{datos_huella}</fingerData>
            </FingerPrint>
        </FingerPrintList>
    </UserInfo>
</UserInfoList>
"""

    if _probar_payload(url_userinfo_json, payload_json_1, "intento 1 - POST /UserInfo (fingerData)"):
        return {"ok": True, "status_code": 200, "raw": ultima_respuesta, "payload_usado": "userinfo-json-fingerData"}

    if _probar_payload(url_userinfo_json, payload_json_2, "intento 2 - POST /UserInfo (fingerPrintData)"):
        return {"ok": True, "status_code": 200, "raw": ultima_respuesta, "payload_usado": "userinfo-json-fingerPrintData"}

    if _probar_payload(url_userinfo_xml, payload_xml, "intento 3 - POST /UserInfo XML", content_type="application/xml"):
        return {"ok": True, "status_code": 200, "raw": ultima_respuesta, "payload_usado": "userinfo-xml"}

    url_userinfo_modify = f"http://{IP}/ISAPI/AccessControl/UserInfo/Modify"
    url_userinfo_setup = f"http://{IP}/ISAPI/AccessControl/UserInfo/SetUp"

    payload_modify_json = {
        "UserInfo": {
            "employeeNo": employee_no,
            "name": employee_no,
            "userType": "normal",
            "Valid": {
                "enable": True,
                "beginTime": "2026-01-01T00:00:00",
                "endTime": "2030-12-31T23:59:59",
            },
            "FingerPrintList": {
                "FingerPrint": [
                    {
                        "fingerNo": finger_no,
                        "fingerType": "normalFp",
                        "fingerPrintID": finger_no,
                        "fingerData": datos_huella,
                    }
                ]
            },
        }
    }

    payload_modify_xml = f"""
<UserInfo version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <employeeNo>{employee_no}</employeeNo>
    <name>{employee_no}</name>
    <userType>normal</userType>
    <Valid>
        <enable>true</enable>
        <beginTime>2026-01-01T00:00:00</beginTime>
        <endTime>2030-12-31T23:59:59</endTime>
    </Valid>
    <FingerPrintList>
        <FingerPrint>
            <fingerNo>{finger_no}</fingerNo>
            <fingerType>normalFp</fingerType>
            <fingerPrintID>{finger_no}</fingerPrintID>
            <fingerData>{datos_huella}</fingerData>
        </FingerPrint>
    </FingerPrintList>
</UserInfo>
"""

    if _probar_payload(url_userinfo_modify, payload_modify_json, "intento 4 - PUT /UserInfo/Modify"):
        return {"ok": True, "status_code": 200, "raw": ultima_respuesta, "payload_usado": "userinfo-modify-json"}

    if _probar_payload(url_userinfo_modify, payload_modify_xml, "intento 5 - PUT /UserInfo/Modify XML", content_type="application/xml", http_method="put"):
        return {"ok": True, "status_code": 200, "raw": ultima_respuesta, "payload_usado": "userinfo-modify-xml"}

    if _probar_payload(url_userinfo_setup, payload_modify_json, "intento 6 - PUT /UserInfo/SetUp"):
        return {"ok": True, "status_code": 200, "raw": ultima_respuesta, "payload_usado": "userinfo-setup-json"}

    if _probar_payload(url_userinfo_setup, payload_modify_xml, "intento 7 - PUT /UserInfo/SetUp XML", content_type="application/xml", http_method="put"):
        return {"ok": True, "status_code": 200, "raw": ultima_respuesta, "payload_usado": "userinfo-setup-xml"}

    payload_fingerprint = {
        "FingerPrint": {
            "employeeNo": employee_no,
            "fingerPrintID": finger_no,
            "fingerData": datos_huella,
        }
    }

    if _probar_payload(url_fingerprint, payload_fingerprint, "intento 8 - POST /FingerPrint/Record"):
        return {"ok": True, "status_code": 200, "raw": ultima_respuesta, "payload_usado": "fingerprint-record"}

    url_fingerprint_modify = f"http://{IP}/ISAPI/AccessControl/FingerPrint/Modify"
    if _probar_payload(url_fingerprint_modify, payload_fingerprint, "intento 9 - PUT /FingerPrint/Modify", http_method="put"):
        return {"ok": True, "status_code": 200, "raw": ultima_respuesta, "payload_usado": "fingerprint-modify"}

    return {
        "ok": False,
        "status_code": 502,
        "raw": ultima_respuesta,
        "error": "No se pudo verificar que la huella quedara persistida en el dispositivo",
    }


def definir_tipo(usuario):
    hoy = datetime.now().date()

    # Intentar contar registros según el modelo de AsistenciaAmbiente
    try:
        # El campo en la tabla de ambiente es `id_usuario` (FK a login.Usuarios)
        registros = AsistenciaAmbiente.objects.filter(
            id_usuario=usuario,
            fecha=hoy
        ).count()
    except Exception:
        # Fallback genérico si la estructura difiere
        registros = 0

    if registros == 0:
        return "Entrada"
    else:
        return "Salida"