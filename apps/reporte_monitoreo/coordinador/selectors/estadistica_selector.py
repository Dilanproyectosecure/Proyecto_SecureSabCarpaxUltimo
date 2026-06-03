from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from apps.reporte_monitoreo.coordinador.models import Ficha, AsistenciaSede, AsistenciaAmbiente, Justificacion, Novedad
from apps.login.models import Usuarios

def obtener_total_fichas_activas():
    total = Ficha.objects.filter(Q(estado__icontains='activa') | Q(estado__icontains='activo')).count()
    return total if total > 0 else Ficha.objects.count()

def obtener_total_aprendices():
    return Usuarios.objects.filter(id_ficha__isnull=False).exclude(
        Q(nombre__icontains='instructor') | Q(nombre__icontains='coordinador') |
        Q(apellido__icontains='instructor') | Q(apellido__icontains='coordinador')
    ).count()

def obtener_asistencia_sede_hoy():
    hoy = timezone.localdate()
    presentes = AsistenciaSede.objects.filter(fecha=hoy, estado_asistencia__icontains='presente').count()
    total = AsistenciaSede.objects.filter(fecha=hoy).count()
    porcentaje = round((presentes / total) * 100, 1) if total > 0 else 0
    return presentes, total, porcentaje

def obtener_justificaciones_pendientes():
    return Justificacion.objects.filter(estado__icontains='pendiente').count()

def obtener_datos_asistencias_semanales():
    hoy = timezone.localdate()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    labels = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie']
    presentes = []
    ausentes = []
    
    for offset in range(5):
        fecha = inicio_semana + timedelta(days=offset)
        presentes.append(AsistenciaAmbiente.objects.filter(fecha=fecha, estado_asistencia__icontains='asistio').count())
        ausentes.append(AsistenciaAmbiente.objects.filter(fecha=fecha, estado_asistencia__icontains='inasistio').count())
    
    return labels, presentes, ausentes

def obtener_alertas_por_ficha(asistencias):
    """Calcula alertas por ficha para el PDF"""
    alertas_ficha = []
    fichas = asistencias.values_list('id_usuario__id_ficha__numero_ficha', flat=True).distinct()
    
    for ficha_num in fichas:
        if not ficha_num:
            continue
            
        asistencias_ficha = asistencias.filter(id_usuario__id_ficha__numero_ficha=ficha_num)
        total_ficha = asistencias_ficha.count()
        inasistio_ficha = asistencias_ficha.filter(estado_asistencia__icontains='inasistio').count()
        justificada_ficha = asistencias_ficha.filter(
            Q(estado_asistencia__icontains='justificad') |
            Q(estado_asistencia__icontains='justificado')
        ).count()
        sin_instructor = asistencias_ficha.filter(id_instructor__isnull=True).count()
        
        pct_inas = round((inasistio_ficha / total_ficha) * 100, 2) if total_ficha else 0
        
        if inasistio_ficha >= 3 or pct_inas >= 30:
            nivel = 'Alta'
        elif inasistio_ficha >= 1 or pct_inas >= 15:
            nivel = 'Media'
        else:
            nivel = 'Baja'
        
        alertas_ficha.append({
            'ficha': ficha_num,
            'total': total_ficha,
            'inasistio': inasistio_ficha,
            'justificada': justificada_ficha,
            'sin_instructor': sin_instructor,
            'pct_inasistencia': pct_inas,
            'nivel': nivel,
        })
    
    return sorted(alertas_ficha, key=lambda a: (a['nivel'] == 'Alta', a['inasistio'], a['sin_instructor']), reverse=True)[:8]
