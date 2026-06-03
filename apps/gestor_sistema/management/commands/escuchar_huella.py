from django.core.management.base import BaseCommand
import time
# Cambiamos guardar_eventos por procesar_eventos
from apps.gestor_sistema.hikvision_service import procesar_eventos 

class Command(BaseCommand):
    help = 'Escucha eventos del Hikvision'

    def handle(self, *args, **kwargs):
        self.stdout.write("Escuchando huellas...")

        while True:
            try:
                # Usamos el nombre correcto aquí también
                procesar_eventos() 
            except Exception as e:
                self.stdout.write(f"Error: {e}")

            time.sleep(10)