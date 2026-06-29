from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente, Justificacion
from django.db.models import Prefetch

def obtener_inasistencias_usuario(usuario):
    return AsistenciaAmbiente.objects.filter(
        id_usuario=usuario,
        estado_asistencia__in=['Inasistio', 'Justificado', 'Justificada']
    ).select_related(
        'id_competencia',
        'id_instructor'
    ).prefetch_related(
        Prefetch(
            'justificacion_set',
            queryset=Justificacion.objects.order_by('-id_justificacion'),
            to_attr='justificaciones'
        )
    )