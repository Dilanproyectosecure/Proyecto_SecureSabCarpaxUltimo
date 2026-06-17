from django.core.management.base import BaseCommand
import time
from apps.gestor_sistema.hikvision_service import procesar_eventos

class Command(BaseCommand):
    help = 'Escucha eventos del Hikvision cada 10 segundos'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("📡 Escuchando huellas del dispositivo Hikvision..."))
        self.stdout.write(self.style.WARNING("Presiona Ctrl+C para detener"))

        try:
            while True:
                procesar_eventos()
                time.sleep(10)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("\n✅ Escucha de huellas detenida"))