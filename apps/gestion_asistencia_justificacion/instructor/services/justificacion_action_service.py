from datetime import date
from apps.reporte_monitoreo.coordinador.models import Justificacion, AsistenciaAmbiente


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


def habilitar_carga_evidencia(asistencia_id, instructor, observaciones=None):
    """
    Habilita la carga de evidencia para una inasistencia vencida.
    Crea un registro Justificacion con estado='Habilitado' para que el
    aprendiz pueda subir su evidencia.
    """
    try:
        asistencia = AsistenciaAmbiente.objects.get(
            id_asistencia_ambiente=asistencia_id
        )
    except AsistenciaAmbiente.DoesNotExist:
        return False, "Inasistencia no encontrada"

    if asistencia.estado_asistencia != 'Inasistio':
        return False, "Solo se pueden habilitar inasistencias"

    habilitacion_existente = Justificacion.objects.filter(
        id_asistencia_ambiente=asistencia,
        estado='Habilitado'
    ).exists()

    if habilitacion_existente:
        return False, "Esta inasistencia ya fue habilitada anteriormente"

    Justificacion.objects.create(
        id_asistencia_ambiente=asistencia,
        motivo='Habilitación por urgencia justificada',
        soporte='',
        fecha=date.today(),
        estado='Habilitado',
        observaciones=observaciones or f'Habilitado por el instructor {instructor.nombre} {instructor.apellido}'
    )

    return True, "Carga de evidencia habilitada correctamente"