"""
Puente Hikvision → Azure SecureSab
Corre en el PC local para reenviar eventos del lector biométrico al servidor en Azure.
"""
import requests
from requests.auth import HTTPDigestAuth
import json
import time
import os
from datetime import datetime, timezone

# =========================
# CONFIGURACIÓN
# =========================
HIK_IP = "192.168.1.13"
HIK_USER = "admin"
HIK_PASS = "Dilan1105"
AZURE_URL = "http://158.23.17.242:8000/gestor_sistema/webhook/huella/"
POLL_INTERVAL = 5
COOLDOWN_HIK = 60
COOLDOWN_AZURE = 30

# =========================
# ESTADO (con persistencia a archivo)
# =========================
TIMESTAMP_FILE = os.path.join(os.path.dirname(__file__), ".puente_timestamp")

def _cargar_timestamp():
    if os.path.exists(TIMESTAMP_FILE):
        with open(TIMESTAMP_FILE) as f:
            return f.read().strip()
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _guardar_timestamp(ts):
    with open(TIMESTAMP_FILE, "w") as f:
        f.write(ts)

ultimo_timestamp = _cargar_timestamp()
eventos_vistos = set()
cooldown_hik = 0
cooldown_azure = 0


def obtener_eventos():
    url = f"http://{HIK_IP}/ISAPI/AccessControl/AcsEvent?format=json"
    global ultimo_timestamp
    payload = {
        "AcsEventCond": {
            "searchID": "1",
            "searchResultPosition": 0,
            "maxResults": 50,
            "major": 0,
            "minor": 0,
            "startTime": ultimo_timestamp,
            "endTime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    }
    try:
        r = requests.post(
            url, json=payload,
            auth=HTTPDigestAuth(HIK_USER, HIK_PASS),
            headers={"Content-Type": "application/json"}, timeout=10
        )
        if r.status_code != 200:
            print(f"[HIK] Error {r.status_code}: {r.text[:100]}")
            return None
        data = r.json()
        eventos = data.get("AcsEvent", {}).get("InfoList", [])
        if eventos:
            ultimo_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            _guardar_timestamp(ultimo_timestamp)
        return eventos
    except requests.exceptions.ConnectTimeout:
        return None
    except requests.exceptions.ConnectionError:
        return None
    except Exception as e:
        print(f"[HIK] Error: {e}")
        return None


def enviar_webhook(employee_no):
    global cooldown_azure
    now = time.time()
    if now < cooldown_azure:
        return False
    key = f"evt:{employee_no}"
    if key in eventos_vistos:
        return True
    try:
        r = requests.post(AZURE_URL, json={"employeeNoString": str(employee_no)},
                          timeout=5)
        if r.status_code == 200:
            print(f"  → Azure OK: employeeNo={employee_no}")
            eventos_vistos.add(key)
            if len(eventos_vistos) > 500:
                eventos_vistos.clear()
            return True
        print(f"  → Azure Error {r.status_code}: {r.text[:80]}")
        return False
    except requests.exceptions.ConnectTimeout:
        cooldown_azure = now + COOLDOWN_AZURE
        print(f"  → Azure timeout, esperando {COOLDOWN_AZURE}s...")
        return False
    except requests.exceptions.ConnectionError:
        cooldown_azure = now + COOLDOWN_AZURE
        print(f"  → Azure sin conexión, esperando {COOLDOWN_AZURE}s...")
        return False
    except Exception as e:
        print(f"  → Azure error: {e}")
        return False


def main():
    global cooldown_hik
    print("=" * 55)
    print(" PUENTE HIKVISION → AZURE SECURESAB")
    print(f" Hikvision: {HIK_IP}")
    print(f" Azure:     {AZURE_URL}")
    print(f" Poll cada: {POLL_INTERVAL}s")
    print("=" * 55)

    while True:
        try:
            now = time.time()

            if now < cooldown_hik:
                time.sleep(1)
                continue

            eventos = obtener_eventos()

            if eventos is None:
                if cooldown_hik == 0:
                    print(f"[HIK] Sin respuesta, esperando {COOLDOWN_HIK}s...")
                cooldown_hik = now + COOLDOWN_HIK
                time.sleep(1)
                continue

            cooldown_hik = 0

            if not eventos:
                time.sleep(POLL_INTERVAL)
                continue

            for evento in eventos:
                emp = evento.get("employeeNoString") or evento.get("employeeNo")
                if emp:
                    enviar_webhook(emp)

        except KeyboardInterrupt:
            print("\nPuente detenido")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
