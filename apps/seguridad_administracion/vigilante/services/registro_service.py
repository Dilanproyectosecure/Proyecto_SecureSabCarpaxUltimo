from django.utils import timezone
from datetime import date, datetime
from apps.seguridad_administracion.vigilante.models import RegistroManual
from apps.reporte_monitoreo.coordinador.models import AsistenciaSede
from apps.login.models import Usuarios
from apps.gestor_sistema.services import registrar_actividad

def procesar_registro_manual(request, documento, tipo_movimiento, motivo):
    """Procesa un registro manual de ingreso/salida"""
    if not motivo:
        motivo = 'Fallo Lectura Huella'
    
    # Buscar usuario
    try:
        usuario = Usuarios.objects.get(cedula=documento)
    except Usuarios.DoesNotExist:
        return False, f'El documento {documento} no está registrado en el sistema'
    
    if usuario.estado != 'Activo':
        return False, f'El usuario {usuario.nombre} {usuario.apellido} no está activo'
    
    # Validar salida
    if tipo_movimiento == 'Salida':
        ultima_asistencia = AsistenciaSede.objects.filter(
            id_usuario=usuario,
            fecha=date.today(),
            hora_salida__isnull=True
        ).first()
        
        if not ultima_asistencia:
            return False, f'No se puede registrar salida. {usuario.nombre} {usuario.apellido} no tiene un ingreso registrado hoy'
    
    # Procesar ingreso o salida
    mensaje_extra = ''
    if tipo_movimiento == 'Ingreso':
        ingreso_pendiente = AsistenciaSede.objects.filter(
            id_usuario=usuario,
            fecha=date.today(),
            hora_salida__isnull=True
        ).first()
        
        if ingreso_pendiente:
            return False, f'{usuario.nombre} {usuario.apellido} ya tiene un ingreso registrado hoy. Registre una salida primero.'
        
        asistencia = AsistenciaSede.objects.create(
            id_usuario=usuario,
            fecha=date.today(),
            hora_entrada=datetime.now().time(),
            estado_asistencia='Ingreso'
        )
        
        registrar_actividad(
            usuario=request.user,
            tipo_accion='REGISTRO_MANUAL',
            actividad='Registro manual de ingreso',
            descripcion=f'Registro manual de ingreso para {usuario.nombre} {usuario.apellido} (cédula: {documento}) - Motivo: {motivo}',
            request=request
        )
        
    else:  # Salida
        asistencia = ultima_asistencia
        asistencia.hora_salida = datetime.now().time()
        asistencia.estado_asistencia = 'Salida'
        asistencia.save()
        
        registrar_actividad(
            usuario=request.user,
            tipo_accion='REGISTRO_MANUAL',
            actividad='Registro manual de salida',
            descripcion=f'Registro manual de salida para {usuario.nombre} {usuario.apellido} (cédula: {documento}) - Motivo: {motivo}',
            request=request
        )
    
    # Crear registro manual
    RegistroManual.objects.create(
        id_usuario=usuario,
        id_asistencia_sede=asistencia,
        documento=documento,
        tipo_movimiento=tipo_movimiento,
        fecha=date.today(),
        hora=datetime.now().time(),
        motivo=motivo,
        cedula=documento,
        fecha_registro=datetime.now(),
        nombres=f"{usuario.nombre} {usuario.apellido}",
        observaciones=motivo,
        tipo_registro='Manual'
    )
    
    return True, f'{tipo_movimiento} registrado exitosamente para {usuario.nombre} {usuario.apellido}{mensaje_extra}'