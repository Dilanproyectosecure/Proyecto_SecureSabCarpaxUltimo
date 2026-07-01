from datetime import date
from apps.reporte_monitoreo.coordinador.models import Justificacion, AsistenciaAmbiente, FichaInstructor


def procesar_accion_justificacion(
    justificacion_id,
    accion,
    observaciones=None,
    instructor_id=None
):
    """
    Aprueba o rechaza una justificación.
    Valida que la competencia de la justificación pertenezca al instructor.
    """

    try:
        justificacion = Justificacion.objects.select_related(
            'id_asistencia_ambiente',
            'id_asistencia_ambiente__id_competencia'
        ).get(
            id_justificacion=justificacion_id
        )
    except Justificacion.DoesNotExist:
        return False, "Justificación no encontrada"

    if instructor_id and justificacion.id_asistencia_ambiente:
        competencia_id = justificacion.id_asistencia_ambiente.id_competencia_id
        tiene_permiso = FichaInstructor.objects.filter(
            id_instructor=instructor_id,
            id_competencia=competencia_id
        ).exists()
        if not tiene_permiso:
            return False, "No tiene permiso para procesar justificaciones de esta competencia"

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