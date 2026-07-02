from django.utils import timezone
from django.core.files.storage import default_storage
from datetime import date
import os

from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente, Justificacion, PeticionJustificacion


def crear_justificaciones(usuario, inasistencias_ids, motivo, soporte):
    
    hoy = date.today()
    creadas = 0

    for asistencia_id in inasistencias_ids:
        try:
            asistencia = AsistenciaAmbiente.objects.get(
                id_asistencia_ambiente=asistencia_id,
                id_usuario=usuario
            )

            dias_pasados = (hoy - asistencia.fecha).days

            if dias_pasados > 3:
                tiene_peticion = PeticionJustificacion.objects.filter(
                    id_asistencia_ambiente=asistencia,
                    id_aprendiz=usuario,
                    estado='Aprobado'
                ).exists()
                if not tiene_peticion:
                    continue

            extension = os.path.splitext(soporte.name)[1]

            nombre_archivo = f"justificacion_{usuario.id_usuario}_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{asistencia_id}{extension}"

            ruta = os.path.join('justificaciones', nombre_archivo)
            ruta_guardada = default_storage.save(ruta, soporte)

            Justificacion.objects.create(
                id_asistencia_ambiente=asistencia,
                motivo=motivo,
                soporte=ruta_guardada,
                fecha=hoy,
                estado='Pendiente',
                observaciones=''
            )

            creadas += 1

        except AsistenciaAmbiente.DoesNotExist:
            continue

    return creadas