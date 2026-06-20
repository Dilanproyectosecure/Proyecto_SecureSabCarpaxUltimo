from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from apps.reporte_monitoreo.coordinador.models import Ficha, AsistenciaSede, AsistenciaAmbiente, Justificacion
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
    entradas = []
    salidas = []
    
    for offset in range(5):
        fecha = inicio_semana + timedelta(days=offset)
        dia = AsistenciaSede.objects.filter(fecha=fecha)
        entradas.append(dia.filter(hora_entrada__isnull=False).count())
        salidas.append(dia.filter(hora_salida__isnull=False).count())
    
    return labels, entradas, salidas

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


def obtener_distribucion_asistencia_hoy():
    hoy = timezone.localdate()
    total_aprendices = Usuarios.objects.filter(id_ficha__isnull=False).exclude(
        Q(nombre__icontains='instructor') | Q(nombre__icontains='coordinador') |
        Q(apellido__icontains='instructor') | Q(apellido__icontains='coordinador')
    ).count()

    presentes = AsistenciaSede.objects.filter(
        fecha=hoy, estado_asistencia__icontains='presente'
    ).count()

    justificados = Justificacion.objects.filter(
        fecha=hoy,
        estado__icontains='aprobado'
    ).count()

    ausentes = total_aprendices - presentes - justificados
    if ausentes < 0:
        ausentes = 0

    pct_presentes = round((presentes / total_aprendices) * 100, 1) if total_aprendices > 0 else 0
    pct_ausentes = round((ausentes / total_aprendices) * 100, 1) if total_aprendices > 0 else 0
    pct_justificados = round((justificados / total_aprendices) * 100, 1) if total_aprendices > 0 else 0

    return {
        'total': total_aprendices,
        'presentes': presentes,
        'ausentes': ausentes,
        'justificados': justificados,
        'pct_presentes': pct_presentes,
        'pct_ausentes': pct_ausentes,
        'pct_justificados': pct_justificados,
    }


def obtener_asistencia_por_ambiente_hoy():
    hoy = timezone.localdate()
    asistencias = AsistenciaAmbiente.objects.filter(
        fecha=hoy,
        estado_asistencia__icontains='presente'
    ).values('id_usuario__id_ficha__numero_ficha').annotate(
        total=Count('id_asistencia_ambiente')
    ).order_by('-total')

    resultado = []
    for item in asistencias:
        ficha_num = item['id_usuario__id_ficha__numero_ficha']
        if ficha_num:
            resultado.append({
                'ambiente': str(ficha_num),
                'presentes': item['total']
            })

    return resultado


def obtener_tendencia_asistencia_7_dias():
    hoy = timezone.localdate()
    labels = []
    valores = []

    dias_nombre = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']

    for i in range(6, -1, -1):
        fecha = hoy - timedelta(days=i)
        labels.append(f"{dias_nombre[fecha.weekday()]} {fecha.day}")

        count = AsistenciaSede.objects.filter(
            fecha=fecha,
            estado_asistencia__icontains='presente'
        ).count()
        valores.append(count)

    return {
        'labels': labels,
        'valores': valores,
    }


def obtener_fichas_con_estadisticas_coordinador(fecha=None, instructor_id=None, jornada_id=None):
    fichas = Ficha.objects.filter(
        Q(estado__icontains='activa') | Q(estado__icontains='activo')
    ).select_related('id_programa', 'id_jornada').order_by('numero_ficha')

    if not fichas.exists():
        fichas = Ficha.objects.select_related('id_programa', 'id_jornada').order_by('numero_ficha')

    if fecha is None:
        fecha = timezone.localdate()

    fichas_data = []

    for ficha in fichas:
        total_aprendices = Usuarios.objects.filter(
            id_ficha=ficha
        ).exclude(
            Q(nombre__icontains='instructor') | Q(nombre__icontains='coordinador') |
            Q(apellido__icontains='instructor') | Q(apellido__icontains='coordinador')
        ).count()

        asistencias = AsistenciaAmbiente.objects.filter(
            id_usuario__id_ficha=ficha,
            fecha=fecha
        )

        if instructor_id:
            asistencias = asistencias.filter(id_instructor_id=instructor_id)

        asistio = asistencias.filter(estado_asistencia__iexact='Asistio').count()
        inasistio = asistencias.filter(estado_asistencia__iexact='Inasistio').count()
        retardo = asistencias.filter(estado_asistencia__iexact='Retardo').count()
        justificada = asistencias.filter(
            Q(estado_asistencia__iexact='Justificado') | Q(estado_asistencia__iexact='Justificada')
        ).count()

        total_registros = asistencias.count()

        if total_aprendices > 0:
            pct_inasistencia = round((inasistio / total_aprendices) * 100, 1)
        else:
            pct_inasistencia = 0

        if inasistio >= 5 or pct_inasistencia >= 40:
            nivel = 'Alta'
        elif inasistio >= 2 or pct_inasistencia >= 20:
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
            'asistio': asistio,
            'inasistio': inasistio,
            'retardo': retardo,
            'justificada': justificada,
            'total_registros': total_registros,
            'pct_inasistencia': pct_inasistencia,
            'nivel': nivel,
        })

    return fichas_data
