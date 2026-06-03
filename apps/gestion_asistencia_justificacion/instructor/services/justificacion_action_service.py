from apps.reporte_monitoreo.coordinador.models import Justificacion


def procesar_accion_justificacion(
    justificacion_id,
    accion,
    observaciones=None
):
    """
    Aprueba o rechaza una justificación
    """

    try:
        justificacion = Justificacion.objects.get(
            id_justificacion=justificacion_id
        )

        if accion == 'aprobar':

            justificacion.estado = 'Aprobado'

            if justificacion.id_asistencia_ambiente:
                justificacion.id_asistencia_ambiente.estado_asistencia = 'Justificada'
                justificacion.id_asistencia_ambiente.save()

        elif accion == 'rechazar':
            justificacion.estado = 'Rechazado'

        if observaciones:
            justificacion.observaciones = observaciones

        justificacion.save()

        return True, "Procesado correctamente"

    except Justificacion.DoesNotExist:
        return False, "Justificación no encontrada"