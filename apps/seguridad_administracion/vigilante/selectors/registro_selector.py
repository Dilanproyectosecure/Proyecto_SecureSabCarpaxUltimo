from django.db.models import Q
from apps.seguridad_administracion.vigilante.models import RegistroManual
from datetime import date

def obtener_registros_manuales_con_filtros(request):
    """Obtiene registros manuales con filtros"""
    registros = RegistroManual.objects.select_related('id_usuario', 'id_asistencia_sede').all().order_by('-fecha_registro')
    
    filtro_nombre = request.GET.get('nombre', '').strip()
    filtro_cedula = request.GET.get('cedula', '').strip()
    filtro_fecha_desde = request.GET.get('fechaDesde', '')
    filtro_fecha_hasta = request.GET.get('fechaHasta', '')
    
    if filtro_nombre:
        registros = registros.filter(
            Q(nombres__icontains=filtro_nombre) |
            Q(id_usuario__nombre__icontains=filtro_nombre) |
            Q(id_usuario__apellido__icontains=filtro_nombre)
        )
    
    if filtro_cedula:
        registros = registros.filter(
            Q(cedula__icontains=filtro_cedula) |
            Q(documento__icontains=filtro_cedula)
        )
    
    if filtro_fecha_desde:
        registros = registros.filter(fecha__gte=filtro_fecha_desde)
    
    if filtro_fecha_hasta:
        registros = registros.filter(fecha__lte=filtro_fecha_hasta)
    
    return registros


def obtener_todos_registros_manuales():
    """Obtiene todos los registros manuales ordenados"""
    from apps.seguridad_administracion.vigilante.models import RegistroManual
    return RegistroManual.objects.select_related('id_usuario', 'id_asistencia_sede').all().order_by('-fecha_registro')

def obtener_registros_recientes(limite=30):
    """Obtiene los últimos registros manuales"""
    return RegistroManual.objects.select_related('id_usuario', 'id_asistencia_sede').all().order_by('-fecha_registro')[:limite]


def obtener_movimientos_hoy():
    """Obtiene la cantidad de movimientos registrados hoy"""
    hoy = date.today()
    return RegistroManual.objects.filter(fecha=hoy).count()