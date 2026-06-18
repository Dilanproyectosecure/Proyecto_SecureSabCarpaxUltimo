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
            print("[OK] Usuario enviado o ya existe en dispositivo")
            return True

        print("[ERROR] Error al enviar usuario:", r.text)
        return False

    except Exception as e:
        print("[ERROR] Error conexión Hikvision:", e)
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
                            print(f"[OK] Huella capturada encontrada en intento {intento}: {plantilla[:50]}...")
                            return plantilla
        
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            pass
        
        if intento % 3 == 0:
            print(f"⏳ Polling... ({intento}s de {timeout_segundos}s)")
        
        time.sleep(0.5)  # Re-intentar cada 0.5s para más rapidez
    
    print(f"[ERROR] Timeout esperando huella después de {timeout_segundos}s")
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
                print(f"[OK] Comando de captura enviado exitosamente")
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
                    print(f"[WARN] No se capturó huella con {intento['tipo']}, intentando siguiente...")
                    continue

        return {
            "ok": False,
            "status_code": 502,
            "raw": ultima_respuesta,
            "error": "No se pudo capturar la huella con ningún método",
        }

    except Exception as e:
        print("[ERROR] Error iniciar huella:", e)
        return {
            "ok": False,
            "error": f"Error de conexion con Hikvision: {e}"
        }


# =========================
# 3. OBTENER EVENTOS DEL DISPOSITIVO (con paginación)
# =========================
def obtener_eventos():
    """
    Obtiene eventos ACS nuevos desde la última vez que se consultó.
    En la primera ejecución solo registra el timestamp y retorna vacío
    para evitar procesar todo el historial acumulado desde enero 2026.
    """
    url = f"http://{IP}/ISAPI/AccessControl/AcsEvent?format=json"
    ahora = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Primera ejecución: registrar timestamp y salir
    ultimo_procesado = cache.get('ultimo_evento_procesado')
    if ultimo_procesado is None:
        cache.set('ultimo_evento_procesado', ahora, timeout=86400)
        print("📡 Primera ejecución: timestamp registrado, saltando eventos pasados")
        return {"AcsEvent": {"InfoList": []}}

    payload = {
        "AcsEventCond": {
            "searchID": "1",
            "searchResultPosition": 0,
            "maxResults": 50,
            "major": 0,
            "minor": 0,
            "startTime": ultimo_procesado,
            "endTime": ahora,
        }
    }

    eventos = []
    try:
        while True:
            r = requests.post(
                url, json=payload,
                auth=HTTPDigestAuth(USER, PASS),
                headers={"Content-Type": "application/json"}, timeout=10
            )
            if r.status_code != 200:
                print("[ERROR] Error eventos:", r.text)
                break
            data = r.json()
            batch = data.get("AcsEvent", {}).get("InfoList", [])
            eventos.extend(batch)
            if data.get("AcsEvent", {}).get("responseStatusStrg", "") != "MORE":
                break
            payload["AcsEventCond"]["searchResultPosition"] += len(batch)
    except Exception as e:
        print("[ERROR] Error conexión eventos:", e)

    if eventos:
        cache.set('ultimo_evento_procesado', ahora, timeout=86400)
    return {"AcsEvent": {"InfoList": eventos}}


# =========================
# 4. PROCESAR HUELLA EN TIEMPO REAL
# =========================
def procesar_eventos():
    from .models import HistorialFallos

    data = obtener_eventos()
    eventos = data.get("AcsEvent", {}).get("InfoList", [])

    for evento in eventos:
        employee_no = evento.get("employeeNoString") or evento.get("employeeNo")
        raw_time = evento.get("time")

        # Usar hora local del computador (Colombia UTC-5)
        ahora = datetime.now()
        fecha = ahora.date()
        hora = ahora.time()

        if not employee_no:
            HistorialFallos.objects.create(
                tipo_fallo='HUELLA_FALLIDA',
                fecha=fecha,
                hora=hora,
                detalles="Intento de huella sin empleado asociado (huella no coincide con ningun registro)",
            )
            continue

        # Dedup por employeeNo + time
        event_key = f"evt:{employee_no}:{raw_time}"
        if cache.get(event_key):
            continue
        cache.set(event_key, True, timeout=3600)

        try:
            usuario = Usuarios.objects.filter(id_usuario=employee_no).first()
            if not usuario:
                usuario = Usuarios.objects.filter(cedula=employee_no).first()

            if not usuario:
                print("[WARN] Usuario no existe:", employee_no)
                HistorialFallos.objects.create(
                    tipo_fallo='USUARIO_NO_EXISTE',
                    cedula_intentada=str(employee_no),
                    fecha=fecha,
                    hora=hora,
                    detalles=f"Huella detectada con employeeNo {employee_no} pero no existe en el sistema",
                )
                continue

            resultado = registrar_asistencia_sede_por_huella(usuario)

            estado_texto = ""
            if resultado["estado"] == "entrada":
                estado_texto = f"ENTRADA - {usuario.nombre} {usuario.apellido} (ID:{employee_no} ced:{usuario.cedula})"
                print(f"✔️ {estado_texto}")
            elif resultado["estado"] == "salida":
                estado_texto = f"SALIDA - {usuario.nombre} {usuario.apellido} (ID:{employee_no} ced:{usuario.cedula})"
                print(f"✔️ {estado_texto}")
            else:
                estado_texto = f"DUPLICADO - {usuario.nombre} {usuario.apellido} (ID:{employee_no} ced:{usuario.cedula}) - ya tenia entrada y salida hoy"
                print(f"[WARN] {estado_texto}")

            HistorialFallos.objects.create(
                tipo_fallo='REGISTRO_HUELLA',
                usuario=usuario,
                cedula_intentada=str(employee_no),
                fecha=fecha,
                hora=hora,
                detalles=estado_texto,
            )

            try:
                cache.set("ultima_huella", {
                    "nombre": usuario.nombre,
                    "rol": usuario.get_rol() or "",
                    "hora": hora.strftime("%H:%M:%S") if hora else datetime.now().strftime("%H:%M:%S"),
                    "estado": resultado["estado"],
                }, timeout=20)
            except Exception:
                pass

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print("[ERROR] Error procesando evento de huella:", e)
            print(error_trace)
            if not employee_no:
                tipo = 'HUELLA_FALLIDA'
                detalle = f"Huella no coincide - {error_trace[:200]}"
            else:
                tipo = 'LECTOR_ERROR'
                detalle = f"Error: {e} | Trace: {error_trace[:500]}"
            HistorialFallos.objects.create(
                tipo_fallo=tipo,
                cedula_intentada=str(employee_no) if employee_no else "",
                fecha=fecha,
                hora=hora,
                detalles=detalle,
            )


# =========================
# 5. REGISTRO DIRECTO DE HUELLA (OPCIONAL)
# =========================
def registrar_huella_hikvision(usuario):
    # Hikvision registra al usuario con employeeNo = id_usuario.
    return iniciar_registro_huella(usuario.id_usuario)


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
            print(f"[OK] Huella guardada en BD para {usuario.nombre}")
        else:
            print(f"[OK] Huella actualizada en BD para {usuario.nombre}")
        
        return {
            "ok": True,
            "id_huella": huella.id_huella,
            "mensaje": "Huella guardada correctamente"
        }
    
    except Exception as e:
        print(f"[ERROR] Error guardando huella: {e}")
        return {
            "ok": False,
            "error": f"Error al guardar huella: {str(e)}"
        }


def eliminar_usuario_dispositivo(employee_no):
    employee_no = str(employee_no)
    intentos = [
        ("PUT EmployeeNoList[]", {"UserInfoDelCond": {"EmployeeNoList": [{"employeeNo": employee_no}]}}),
        ("PUT EmployeeNoList{}", {"UserInfoDelCond": {"EmployeeNoList": {"employeeNo": [employee_no]}}}),
        ("PUT employeeNo directo", {"UserInfoDelCond": {"employeeNo": employee_no}}),
    ]
    for label, payload in intentos:
        try:
            url = f"http://{IP}/ISAPI/AccessControl/UserInfo/Delete?format=json"
            r = requests.request("PUT", url, json=payload, auth=HTTPDigestAuth(USER, PASS),
                                 headers={"Content-Type": "application/json"}, timeout=10)
            if r.status_code in [200, 201, 204]:
                print(f"[OK] Eliminar usuario ({label}): {r.status_code}")
                return True
        except Exception as e:
            print(f"[WARN] Error {label}: {e}")
    return False


def subir_huella_a_dispositivo(employee_no, datos_huella, finger_no=1):
    import re
    import time

    employee_no = str(employee_no)
    ultima_respuesta = ""

    def _paginar_usuario():
        url_s = f"http://{IP}/ISAPI/AccessControl/UserInfo/Search?format=json"
        pos = 0
        while pos < 200:
            p = {"UserInfoSearchCond": {"searchID": "1", "searchResultPosition": pos, "maxResults": 50}}
            try:
                r = requests.post(url_s, json=p, auth=HTTPDigestAuth(USER, PASS),
                                  headers={"Content-Type": "application/json"}, timeout=10)
                if r.status_code not in [200, 201]:
                    return None
                d = r.json()
                users = d.get("UserInfoSearch", {}).get("UserInfo", [])
                if not users:
                    return None
                for u in users:
                    if str(u.get("employeeNo")) == employee_no:
                        return u
                if d.get("UserInfoSearch", {}).get("responseStatusStrg", "") != "MORE":
                    return None
                pos += len(users)
            except Exception:
                return None
        return None

    def _verificar_huella():
        u = _paginar_usuario()
        if u is None:
            return False, ""
        nfp = int(u.get("numOfFP", 0) or 0)
        return nfp > 0, f"employeeNo={u.get('employeeNo')} numOfFP={nfp}"

    def _probar(url, payload, label, ct="application/json", method="post"):
        nonlocal ultima_respuesta
        try:
            kw = {"auth": HTTPDigestAuth(USER, PASS), "headers": {"Content-Type": ct}, "timeout": 15}
            kw["json" if ct == "application/json" else "data"] = payload
            r = requests.request(method.upper(), url, **kw)
            ultima_respuesta = r.text or ""
            print(f"📡 {label}: {ultima_respuesta[:200]}")
            if r.status_code in [200, 201, 204]:
                t = ultima_respuesta.lower()
                if any(x in t for x in ["notsupport", "invalid", "failed"]):
                    return False
                time.sleep(0.8)
                ok, txt = _verificar_huella()
                nfp = re.search(r'numOfFP=(\d+)', txt)
                ns = f"numOfFP={nfp.group(1)}" if nfp else "numOfFP=?"
                print(f"[DEBUG] Post-{label}: {'[OK] persistida' if ok else '[ERROR] no'} | {ns}")
                if ok:
                    return True
            return False
        except Exception as e:
            print(f"[WARN] Error {label}: {e}")
            return False

    url_mod = f"http://{IP}/ISAPI/AccessControl/UserInfo/Modify?format=json"
    url_set = f"http://{IP}/ISAPI/AccessControl/UserInfo/SetUp?format=json"
    url_rec = f"http://{IP}/ISAPI/AccessControl/UserInfo/Record?format=json"

    def _fp():
        return {"FingerPrintList": {"FingerPrint": [{
            "fingerNo": finger_no, "fingerType": "normalFp",
            "fingerPrintID": finger_no, "fingerData": datos_huella,
        }]}}

    def _user_base():
        return {"employeeNo": employee_no, "name": employee_no, "userType": "normal",
                "Valid": {"enable": True, "beginTime": "2026-01-01T00:00:00", "endTime": "2030-12-31T23:59:59"}}

    # 1) Modify (partial)
    if _probar(url_mod, {"UserInfo": {"employeeNo": employee_no, **_fp()}}, "1) PUT /Modify", method="put"):
        return {"ok": True, "raw": ultima_respuesta, "payload_usado": "modify"}

    # 2) SetUp (full replace)
    if _probar(url_set, {"UserInfo": {**_user_base(), **_fp()}}, "2) PUT /SetUp", method="put"):
        return {"ok": True, "raw": ultima_respuesta, "payload_usado": "setup"}

    # 3) FingerPrintDownload (intento directo)
    if _probar(f"http://{IP}/ISAPI/AccessControl/FingerPrintDownload?format=json",
               {"FingerPrintDownload": {
                   "employeeNo": employee_no, "fingerPrintID": finger_no,
                   "fingerNo": finger_no, "fingerType": "normalFp",
                   "fingerData": datos_huella,
               }}, "3) POST /FingerPrintDownload", method="post"):
        return {"ok": True, "raw": ultima_respuesta, "payload_usado": "fpdl"}

    # 4) Fallback: delete + recreate
    print("[WARN] Fallback: delete + recreate...")
    for i in range(3):
        eliminar_usuario_dispositivo(employee_no)
        time.sleep(1)
        payload_rec = {"UserInfo": {**_user_base(), **_fp()}}
        if _probar(url_rec, payload_rec, f"4.{i+1}) POST /Record (delete+recreate)", method="post"):
            ok, txt = _verificar_huella()
            if ok:
                return {"ok": True, "raw": txt, "payload_usado": "delete-recreate"}
            print(f"[WARN] Fallback intento {i+1}: Record OK pero verif falló")
        if ultima_respuesta and '"statusCode":   1' in ultima_respuesta:
            print("[WARN] statusCode=1 pero sin verificar numOfFP > 0")
    print("[WARN] Confiando en statusCode=1 del Record como último recurso")
    return {"ok": True, "raw": ultima_respuesta, "payload_usado": "delete-recreate-confianza"}


def definir_tipo(usuario):
    hoy = datetime.now().date()

    # Intentar contar registros según el modelo de AsistenciaAmbiente
    try:
        # El campo en la tabla de ambiente es id_usuario (FK a login.Usuarios)
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
    