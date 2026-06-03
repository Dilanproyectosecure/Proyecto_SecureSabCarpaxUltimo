from django.db.models import Q
from apps.reporte_monitoreo.coordinador.models import Justificacion

def obtener_justificaciones_con_filtros(request):
    """Obtiene justificaciones con filtros aplicados"""
    justificaciones = Justificacion.objects.select_related(
        'id_asistencia_ambiente',
        'id_asistencia_ambiente__id_usuario',
        'id_asistencia_ambiente__id_usuario__id_ficha'
    ).all().order_by('-fecha', '-id_justificacion')
    
    search = request.GET.get('search', '').strip()
    estado = request.GET.get('estado', 'all')
    
    if search:
        justificaciones = justificaciones.filter(
            Q(id_asistencia_ambiente__id_usuario__nombre__icontains=search) |
            Q(id_asistencia_ambiente__id_usuario__apellido__icontains=search) |
            Q(id_asistencia_ambiente__id_usuario__cedula__icontains=search) |
            Q(motivo__icontains=search)
        )
    
    if estado != 'all':
        justificaciones = justificaciones.filter(estado=estado)
    
    return justificaciones


def obtener_estadisticas_justificaciones(justificaciones):
    """Calcula estadísticas de justificaciones"""
    total = justificaciones.count()
    pendientes = justificaciones.filter(estado='Pendiente').count()
    aprobadas = justificaciones.filter(estado='Aprobado').count()
    rechazadas = justificaciones.filter(estado='Rechazado').count()
    return total, pendientes, aprobadas, rechazadas