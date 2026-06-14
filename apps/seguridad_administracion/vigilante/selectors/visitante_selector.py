from django.db.models import Q, CharField, Value
from django.db.models.functions import Concat, Coalesce
from apps.seguridad_administracion.vigilante.models import Visitante
from datetime import date

def obtener_visitantes_con_filtros(request):
    """Obtiene visitantes con filtros aplicados"""
    visitantes = Visitante.objects.select_related('id_asistencia_sede', 'id_area').all().order_by(
        '-id_asistencia_sede__fecha', '-id_asistencia_sede__hora_entrada'
    )
    
    nombre = request.GET.get('nombre', '').strip()
    cedula = request.GET.get('cedula', '').strip()
    tipo_documento = request.GET.get('tipo_documento', '').strip()
    fecha_desde = request.GET.get('fechaDesde', '')
    fecha_hasta = request.GET.get('fechaHasta', '')
    area_id = request.GET.get('area', '')
    
    if nombre:
        nombre = " ".join(nombre.split())
        visitantes = visitantes.annotate(
            nombre_completo=Concat(
                Coalesce('nombre', Value('')),
                Value(' '),
                Coalesce('apellido', Value('')),
                output_field=CharField(),
            )
        )
        partes_nombre = [parte for parte in nombre.split() if parte]
        condicion_nombre = Q(nombre_completo__icontains=nombre)
        for parte in partes_nombre:
            condicion_nombre &= Q(nombre_completo__icontains=parte)

        visitantes = visitantes.filter(condicion_nombre).distinct()
    
    if cedula:
        visitantes = visitantes.filter(cedula__icontains=cedula)

    if tipo_documento:
        visitantes = visitantes.filter(tipo_documento=tipo_documento)
    
    if fecha_desde:
        visitantes = visitantes.filter(id_asistencia_sede__fecha__gte=fecha_desde)
    
    if fecha_hasta:
        visitantes = visitantes.filter(id_asistencia_sede__fecha__lte=fecha_hasta)
    
    if area_id:
        visitantes = visitantes.filter(id_area_id=area_id)
    
    return visitantes


def obtener_visitante_por_id(visitante_id):
    """Obtiene un visitante por su ID"""
    return Visitante.objects.filter(id_visitante=visitante_id).first()


def obtener_visitante_activo_por_cedula(cedula):
    """Obtiene un visitante activo (sin salida) por cédula"""
    return Visitante.objects.filter(
        cedula=cedula,
        id_asistencia_sede__hora_salida__isnull=True
    ).select_related('id_asistencia_sede').first()


def obtener_visitante_reciente_por_cedula(cedula):
    """Obtiene el visitante más reciente por cédula"""
    return Visitante.objects.filter(cedula=cedula).order_by('-id_visitante').first()


def buscar_usuario_por_cedula(cedula):
    """Busca si la cédula pertenece a un usuario del sistema"""
    from apps.login.models import Usuarios
    return Usuarios.objects.filter(cedula=cedula).first()


def obtener_todos_visitantes():
    """Obtiene todos los visitantes ordenados por fecha"""
    from apps.seguridad_administracion.vigilante.models import Visitante
    return Visitante.objects.select_related('id_asistencia_sede').all().order_by(
        '-id_asistencia_sede__fecha', '-id_asistencia_sede__hora_entrada'
    )


def obtener_estadisticas_dashboard():
    """Obtiene estadísticas para el dashboard del vigilante"""
    hoy = date.today()
    
    visitantes_dentro = Visitante.objects.filter(
        id_asistencia_sede__fecha=hoy,
        id_asistencia_sede__hora_salida__isnull=True
    ).count()
    
    return {
        'totalVisitantes': Visitante.objects.count(),
        'visitantesDentro': visitantes_dentro,
    }