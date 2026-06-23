from django.core.management.base import BaseCommand
import time
import traceback
from apps.gestor_sistema.hikvision_service import procesar_eventos

class Command(BaseCommand):
    help = 'Escucha eventos del Hikvision cada 30s'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("SecureSab - Escuchando huellas"))

        errores_seguidos = 0
        while True:
            try:
                procesar_eventos()
                errores_seguidos = 0
            except Exception:
                errores_seguidos += 1
                if errores_seguidos <= 3:
                    traceback.print_exc()
                else:
                    print(f"[ERROR] {errores_seguidos} errores seguidos, suprimiendo tracebacks...")
            time.sleep(30)