from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente, Justificacion
from django.db.models import Exists, OuterRef

def obtener_asistencias_usuario(usuario):
    """
    Retorna todas las asistencias del usuario con optimizaciones ORM
    """
    return AsistenciaAmbiente.objects.filter(
        id_usuario=usuario
    ).select_related(
        'id_competencia',
        'id_instructor'
    ).annotate(
        tiene_justificacion_aprobada=Exists(
            Justificacion.objects.filter(
                id_asistencia_ambiente=OuterRef('id_asistencia_ambiente'),
                estado='Aprobado'
            )
        )
    )