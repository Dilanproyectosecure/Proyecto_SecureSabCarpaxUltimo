from django.db.models import Q
from apps.reporte_monitoreo.coordinador.models import Justificacion


def obtener_justificaciones():
    return Justificacion.objects.filter(
        id_asistencia_ambiente__isnull=False
    ).select_related(
        'id_asistencia_ambiente',
        'id_asistencia_ambiente__id_usuario',
        'id_asistencia_ambiente__id_usuario__id_ficha',
        'id_asistencia_ambiente__id_usuario__id_ficha__id_jornada'
    ).order_by('-fecha', '-id_justificacion')


def filtrar_justificaciones(queryset, ficha_id=None, jornada_id=None,
                            estado=None, fecha_desde=None,
                            fecha_hasta=None, aprendiz=None):

    if ficha_id:
        queryset = queryset.filter(
            id_asistencia_ambiente__id_usuario__id_ficha_id=ficha_id
        )

    if jornada_id:
        queryset = queryset.filter(
            id_asistencia_ambiente__id_usuario__id_ficha__id_jornada_id=jornada_id
        )

    if estado:
        queryset = queryset.filter(estado=estado)

    if fecha_desde:
        queryset = queryset.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        queryset = queryset.filter(fecha__lte=fecha_hasta)

    if aprendiz:
        queryset = queryset.filter(
            Q(id_asistencia_ambiente__id_usuario__nombre__icontains=aprendiz) |
            Q(id_asistencia_ambiente__id_usuario__apellido__icontains=aprendiz) |
            Q(id_asistencia_ambiente__id_usuario__cedula__icontains=aprendiz)
        )

    return queryset