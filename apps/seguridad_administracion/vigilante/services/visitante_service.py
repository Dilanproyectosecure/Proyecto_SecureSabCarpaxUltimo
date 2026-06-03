from django.utils import timezone
from datetime import date, datetime
from apps.seguridad_administracion.vigilante.models import Visitante
from apps.reporte_monitoreo.coordinador.models import AsistenciaSede
from apps.gestor_sistema.services import registrar_actividad

def registrar_entrada_visitante(request, visitante):
    """Registra la entrada de un visitante"""
    if visitante.id_asistencia_sede and not visitante.id_asistencia_sede.hora_salida:
        return False, "Este invitado ya está dentro de las instalaciones"
    
    nueva_asistencia = AsistenciaSede.objects.create(
        id_usuario=request.user,
        fecha=date.today(),
        hora_entrada=datetime.now().time(),
        estado_asistencia='Ingreso'
    )
    
    visitante.id_asistencia_sede = nueva_asistencia
    visitante.save()
    
    registrar_actividad(
        usuario=request.user,
        tipo_accion='INVITADO_ENTRADA',
        actividad='Entrada de invitado',
        descripcion=f'Registro de entrada para {visitante.nombre} {visitante.apellido} (cédula: {visitante.cedula})',
        request=request
    )
    
    return True, "Entrada registrada"


def registrar_salida_visitante(request, visitante):
    """Registra la salida de un visitante"""
    if visitante.id_asistencia_sede and visitante.id_asistencia_sede.hora_salida:
        return False, "Este invitado ya tiene registrada la salida"
    
    asistencia = visitante.id_asistencia_sede
    asistencia.hora_salida = datetime.now().time()
    asistencia.estado_asistencia = 'Fuera'
    asistencia.save()
    
    registrar_actividad(
        usuario=request.user,
        tipo_accion='INVITADO_SALIDA',
        actividad='Salida de invitado',
        descripcion=f'Registro de salida para {visitante.nombre} {visitante.apellido} (cédula: {visitante.cedula})',
        request=request
    )
    
    return True, "Salida registrada"


def crear_visitante(request, datos, es_edicion=False):
    """Crea o actualiza un visitante"""
    nombre = datos.get('nombre')
    apellido = datos.get('apellido')
    cedula = datos.get('cedula')
    motivo = datos.get('motivo')
    area_id = datos.get('area_id')
    observaciones = datos.get('observaciones', '')
    
    if es_edicion:
        visitante = datos.get('visitante')
        visitante.nombre = nombre
        visitante.apellido = apellido
        visitante.tipo_documento = datos.get('tipo_documento', 'CC')
        visitante.motivo = motivo
        visitante.id_area_id = area_id if area_id else None
        visitante.observaciones = observaciones
        visitante.save()
        
        registrar_actividad(
            usuario=request.user,
            tipo_accion='INVITADO_UPDATE',
            actividad='Edición de invitado',
            descripcion=f'Se editó al invitado {nombre} {apellido} con cédula {cedula}',
            request=request
        )
        return visitante
    
    # Crear nueva asistencia en sede
    asistencia = AsistenciaSede.objects.create(
        id_usuario=request.user,
        fecha=date.today(),
        hora_entrada=datetime.now().time(),
        estado_asistencia='Ingreso'
    )
    
    visitante = Visitante.objects.create(
        nombre=nombre,
        apellido=apellido,
        tipo_documento=datos.get('tipo_documento', 'CC'),
        cedula=cedula,
        motivo=motivo,
        id_area_id=area_id if area_id else None,
        id_asistencia_sede=asistencia,
        observaciones=observaciones
    )
    
    registrar_actividad(
        usuario=request.user,
        tipo_accion='INVITADO_CREATE',
        actividad='Registro de invitado',
        descripcion=f'Se registró al invitado {nombre} {apellido} con cédula {cedula} - Motivo: {motivo}',
        request=request
    )
    
    return visitante