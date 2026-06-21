from django.db.models import Q, Count
from django.utils import timezone
from apps.reporte_monitoreo.coordinador.models import Justificacion, Ficha
from apps.login.models import Usuarios


def obtener_justificaciones_con_filtros(request):
    """Obtiene justificaciones con filtros aplicados"""
    justificaciones = Justificacion.objects.select_related(
        'id_asistencia_ambiente',
        'id_asistencia_ambiente__id_usuario',
        'id_asistencia_ambiente__id_usuario__id_ficha',
        'id_asistencia_ambiente__id_competencia',
    ).all().order_by('-fecha', '-id_justificacion')
    
    ficha_id = request.GET.get('ficha', '')
    search = request.GET.get('search', '').strip()
    estado = request.GET.get('estado', 'all')
    
    if ficha_id and ficha_id.isdigit():
        justificaciones = justificaciones.filter(
            id_asistencia_ambiente__id_usuario__id_ficha_id=ficha_id
        )
    
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


def obtener_fichas_con_estadisticas_justificacion(jornada_id=None, programa_id=None, numero_ficha=None):
    fichas = Ficha.objects.filter(
        Q(estado__icontains='activa') | Q(estado__icontains='activo')
    ).select_related('id_programa', 'id_jornada').order_by('numero_ficha')

    if not fichas.exists():
        fichas = Ficha.objects.select_related('id_programa', 'id_jornada').order_by('numero_ficha')

    if jornada_id and str(jornada_id).isdigit():
        fichas = fichas.filter(id_jornada_id=jornada_id)

    if programa_id and str(programa_id).isdigit():
        fichas = fichas.filter(id_programa_id=programa_id)

    if numero_ficha:
        fichas = fichas.filter(numero_ficha__icontains=numero_ficha)

    fichas_data = []
    for ficha in fichas:
        justificaciones = Justificacion.objects.filter(
            id_asistencia_ambiente__id_usuario__id_ficha=ficha
        )
        total = justificaciones.count()
        pendientes = justificaciones.filter(estado__iexact='Pendiente').count()
        aprobadas = justificaciones.filter(estado__iexact='Aprobado').count()
        rechazadas = justificaciones.filter(estado__iexact='Rechazado').count()

        total_aprendices = Usuarios.objects.filter(id_ficha=ficha).exclude(
            Q(nombre__icontains='instructor') | Q(nombre__icontains='coordinador') |
            Q(apellido__icontains='instructor') | Q(apellido__icontains='coordinador')
        ).count()

        if total > 0:
            pct_pendientes = round((pendientes / total) * 100, 1)
        else:
            pct_pendientes = 0

        if pendientes >= 5 or pct_pendientes >= 50:
            nivel = 'Alta'
        elif pendientes >= 2 or pct_pendientes >= 20:
            nivel = 'Media'
        else:
            nivel = 'Baja'

        fichas_data.append({
            'id_ficha': ficha.id_ficha,
            'numero_ficha': ficha.numero_ficha,
            'estado': ficha.estado,
            'programa': ficha.id_programa.nombre_programa if ficha.id_programa else 'N/D',
            'jornada': ficha.id_jornada.nombre_jornada if ficha.id_jornada else 'N/D',
            'total_aprendices': total_aprendices,
            'total': total,
            'pendientes': pendientes,
            'aprobadas': aprobadas,
            'rechazadas': rechazadas,
            'pct_pendientes': pct_pendientes,
            'nivel': nivel,
        })

    return fichas_data