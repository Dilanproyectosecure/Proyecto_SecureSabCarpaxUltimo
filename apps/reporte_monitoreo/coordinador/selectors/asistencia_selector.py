from django.db.models import Q
from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente, AsistenciaSede, Ficha, Jornada
from apps.login.models import Usuarios, RoleUser

def obtener_asistencias_ambiente_con_filtros(request):
    """Construye queryset de asistencia ambiente con filtros"""
    asistencias = AsistenciaAmbiente.objects.select_related(
        'id_usuario__id_ficha__id_jornada', 'id_competencia', 'id_instructor'
    ).all()

    # Excluir roles que no son aprendices ni instructores
    roles_excluir = ['gestor', 'coordinador', 'vigilante']
    
    # Obtener IDs de usuarios con roles no deseados
    usuarios_excluir = RoleUser.objects.filter(
        role__name__in=roles_excluir
    ).values_list('id_usuario', flat=True)
    
    asistencias = asistencias.exclude(id_usuario__id_usuario__in=usuarios_excluir)
    
    ficha_id = request.GET.get('ficha')
    documento = request.GET.get('documento')
    fecha = request.GET.get('fecha')
    estado = request.GET.get('estado')
    jornada_id = request.GET.get('jornada')
    instructor_id = request.GET.get('instructor')
    
    if ficha_id and ficha_id != 'all':
        asistencias = asistencias.filter(id_usuario__id_ficha_id=ficha_id)
    
    if documento:
        asistencias = asistencias.filter(
            Q(id_usuario__cedula__icontains=documento) |
            Q(id_usuario__nombre__icontains=documento) |
            Q(id_usuario__apellido__icontains=documento)
        )
    
    if fecha:
        asistencias = asistencias.filter(fecha=fecha)
    
    if estado and estado != 'all':
        if estado.lower() in ['justificado', 'justificada']:
            asistencias = asistencias.filter(
                Q(estado_asistencia__iexact='justificado') | 
                Q(estado_asistencia__iexact='justificada')
            )
        else:
            asistencias = asistencias.filter(estado_asistencia__iexact=estado)
    
    if jornada_id and jornada_id != 'all':
        asistencias = asistencias.filter(id_usuario__id_ficha__id_jornada_id=jornada_id)
    
    if instructor_id and instructor_id != 'all':
        asistencias = asistencias.filter(id_instructor_id=instructor_id)
    
    return asistencias.order_by('-fecha')


def obtener_asistencias_sede_con_filtros(request):
    """Construye queryset de asistencia sede con filtros (solo aprendices e instructores)"""
    asistencias = AsistenciaSede.objects.select_related('id_usuario__id_ficha__id_jornada').all()
    
    # Excluir roles que no son aprendices ni instructores
    roles_excluir = ['gestor', 'coordinador', 'vigilante']
    
    usuarios_excluir = RoleUser.objects.filter(
        role__name__in=roles_excluir
    ).values_list('id_usuario', flat=True)
    
    asistencias = asistencias.exclude(id_usuario__id_usuario__in=usuarios_excluir)
    
    ficha_id = request.GET.get('ficha')
    documento = request.GET.get('documento')
    fecha = request.GET.get('fecha')
    jornada_id = request.GET.get('jornada')
    rol_filtro = request.GET.get('rol')
    
    if ficha_id and ficha_id != 'all':
        asistencias = asistencias.filter(id_usuario__id_ficha_id=ficha_id)
    
    if documento:
        asistencias = asistencias.filter(
            Q(id_usuario__cedula__icontains=documento) |
            Q(id_usuario__nombre__icontains=documento) |
            Q(id_usuario__apellido__icontains=documento)
        )
    
    if fecha:
        asistencias = asistencias.filter(fecha=fecha)
    
    if jornada_id and jornada_id != 'all':
        asistencias = asistencias.filter(id_usuario__id_ficha__id_jornada_id=jornada_id)
    
    if rol_filtro and rol_filtro != 'all':
        usuarios_con_rol = RoleUser.objects.filter(role__name__iexact=rol_filtro).values_list('id_usuario', flat=True)
        asistencias = asistencias.filter(id_usuario__id_usuario__in=usuarios_con_rol)
    
    return asistencias.order_by('-id_asistencia')


def obtener_fichas_activas():
    return Ficha.objects.filter(estado__icontains='activa').order_by('numero_ficha')


def obtener_jornadas():
    return Jornada.objects.all().order_by('nombre_jornada')


def obtener_instructores():
    return Usuarios.objects.filter(roleuser__role__name__icontains='instructor').order_by('nombre', 'apellido').distinct()


def obtener_roles():
    from apps.login.models import Roles
    return Roles.objects.all().order_by('name')