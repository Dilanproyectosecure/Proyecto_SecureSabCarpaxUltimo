import time
from .hikvision_service import obtener_eventos
from apps.login.models import Usuarios as Usuario
from .models import Huella

def worker_huellas():
    while True:
        data = obtener_eventos()

        eventos = data.get("AcsEvent", {}).get("InfoList", [])

        for e in eventos:
            employee_no = e.get("employeeNoString") or e.get("employeeNo")
            huella = e.get("fingerPrintData")

            if not employee_no:
                continue

            try:
                usuario = Usuario.objects.filter(id_usuario=employee_no).first()
                if not usuario:
                    usuario = Usuario.objects.filter(cedula=employee_no).first()

                if not usuario:
                    print("Usuario no existe:", employee_no)
                    continue

                Huella.objects.update_or_create(
                    usuario=usuario,
                    defaults={
                        "template": huella,
                        "dedo": 1
                    }
                )

                print("✔ Huella guardada:", usuario.nombre)

            except Exception as e:
                print("[ERROR] Error guardando huella en worker:", e)

        time.sleep(2)