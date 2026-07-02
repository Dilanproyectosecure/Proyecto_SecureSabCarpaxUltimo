from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente, Justificacion, PeticionJustificacion
from django.db.models import Prefetch

def obtener_inasistencias_usuario(usuario):
    return AsistenciaAmbiente.objects.filter(
        id_usuario=usuario
    ).select_related(
        'id_competencia',
        'id_instructor'
    ).prefetch_related(
        Prefetch(
            'justificacion_set',
            queryset=Justificacion.objects.order_by('-id_justificacion'),
            to_attr='justificaciones'
        ),
        Prefetch(
            'peticionjustificacion_set',
            queryset=PeticionJustificacion.objects.order_by('-id_peticion'),
            to_attr='peticiones'
        )
    )