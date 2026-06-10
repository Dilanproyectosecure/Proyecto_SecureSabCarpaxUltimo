from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from datetime import date, datetime
import json

from apps.seguridad_administracion.vigilante.selectors import (
    obtener_visitantes_con_filtros,
    obtener_visitante_por_id,
    obtener_visitante_activo_por_cedula,
    obtener_visitante_reciente_por_cedula,
    obtener_estadisticas_dashboard,
    obtener_registros_manuales_con_filtros,
    obtener_registros_recientes,
    obtener_movimientos_hoy,
    obtener_areas_activas,
)
from apps.seguridad_administracion.vigilante.services import (
    registrar_entrada_visitante,
    registrar_salida_visitante,
    crear_visitante,
    procesar_registro_manual,
)
from apps.seguridad_administracion.vigilante.utils.validadores import validar_nombre_apellido, formatear_nombre
from apps.seguridad_administracion.vigilante.models import Area, Visitante, RegistroManual
from apps.gestor_sistema.services import registrar_actividad


TIPOS_DOCUMENTO = [
    ('CC', 'CC - Cédula de ciudadanía'),
    ('TI', 'TI - Tarjeta de identidad'),
    ('CE', 'CE - Cédula de extranjería'),
    ('PA', 'PA - Pasaporte'),
    ('PEP', 'PEP - Permiso Especial de Permanencia'),
    ('PPT', 'PPT - Permiso por Protección Temporal'),
    ('NIT', 'NIT'),
    ('RC', 'RC - Registro civil'),
]


def obtener_todos_visitantes():
    return Visitante.objects.all()


def obtener_todos_registros_manuales():
    return RegistroManual.objects.all()


# ==================== DASHBOARD ====================

@login_required
def iniciov(request):
    """Vista de inicio / dashboard del vigilante"""
    
    stats = obtener_estadisticas_dashboard()
    stats['movimientosHoy'] = obtener_movimientos_hoy()
    stats['totalMovimientos'] = RegistroManual.objects.count()
    
    context = {
        'stats': stats,
        'vigilante_nombre': request.user.nombre or 'Vigilante',
        'vigilante_primer_nombre': request.user.nombre or 'Vigilante',
    }
    
    return render(request, 'iniciov.html', context)


# ==================== CONSULTAR INVITADO ====================

@login_required
def consultar_invitado(request):
    """Vista para consultar invitados con filtros"""
    
    visitantes = obtener_visitantes_con_filtros(request)
    
    # Verificar si hay filtros para registrar actividad
    filtros_activos = any([
        request.GET.get('nombre'), request.GET.get('cedula'),
        request.GET.get('fechaDesde'), request.GET.get('fechaHasta'), request.GET.get('area')
    ])
    
    
    
    paginator = Paginator(visitantes, 15)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    page_numbers = range(max(0, page_obj.number - 3), min(paginator.num_pages, page_obj.number + 2))
    ahora = datetime.now()
    areas = obtener_areas_activas()
    
    context = {
        'visitantes': page_obj,
        'fechaHoy': ahora.strftime('%d/%m/%Y'),
        'horaAhora': ahora.strftime('%H:%M:%S'),
        'areas': areas,
        'tipos_documento': TIPOS_DOCUMENTO,
        'totalPages': paginator.num_pages,
        'currentPage': page_obj.number - 1,
        'pageNumbers': page_numbers,
    }
    
    return render(request, 'consultar_invitado.html', context)


# ==================== ENTRADA/SALIDA INVITADO ====================

@login_required
def entrada_invitado(request, visitante_id):
    """Registrar entrada de un invitado"""
    
    visitante = get_object_or_404(Visitante, id_visitante=visitante_id)
    success, mensaje = registrar_entrada_visitante(request, visitante)

    registrar_actividad(
    usuario=request.user,
    tipo_accion='INVITADO_ENTRADA',
    actividad='Entrada de invitado',
    descripcion=f'Registro de entrada para {visitante.nombre} {visitante.apellido} (cédula: {visitante.cedula})',
    request=request
)
    
    if success:
        messages.success(request, mensaje)
    else:
        messages.warning(request, mensaje)
    
    return redirect('vigilante:consultar_invitado')


@login_required
def salida_invitado(request, visitante_id):
    """Registrar salida de un invitado"""
    
    visitante = get_object_or_404(Visitante, id_visitante=visitante_id)
    success, mensaje = registrar_salida_visitante(request, visitante)
    
    if success:
        messages.success(request, mensaje)
    else:
        messages.warning(request, mensaje)
    
    return redirect('vigilante:consultar_invitado')


# ==================== REGISTRAR INVITADO ====================

@login_required
def registrar_invitado(request):
    """Vista para registrar un nuevo invitado"""
    
    areas = obtener_areas_activas()
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        cedula = request.POST.get('cedula', '').strip()
        motivo = request.POST.get('motivo', '').strip()
        id_visitante = request.POST.get('id_visitante', '').strip()
        
        # Validaciones
        if not nombre or not apellido or not cedula or not motivo:
            messages.error(request, 'Todos los campos obligatorios deben estar llenos')
            return render(request, 'registrar_invitado.html', {
                'areas': areas,
                'fechaHoy': date.today(),
                'horaAhora': datetime.now().strftime('%H:%M:%S'),
            })
        
        es_valido, error = validar_nombre_apellido(nombre, "El nombre")
        if not es_valido:
            messages.error(request, error)
            return render(request, 'registrar_invitado.html', {'areas': areas})
        
        es_valido, error = validar_nombre_apellido(apellido, "El apellido")
        if not es_valido:
            messages.error(request, error)
            return render(request, 'registrar_invitado.html', {'areas': areas})
        
        # Verificar invitado activo (sin salida registrada)
        invitado_activo = obtener_visitante_activo_por_cedula(cedula)
        if invitado_activo:
            messages.error(
                request,
                f'No se puede registrar la entrada de {invitado_activo.nombre} {invitado_activo.apellido} '
                f'porque ya está dentro de las instalaciones y no tiene salida registrada.'
            )
            return render(request, 'registrar_invitado.html', {
                'areas': areas,
                'fechaHoy': date.today(),
                'horaAhora': datetime.now().strftime('%H:%M:%S'),
            })
        
        # Formatear nombres
        nombre = formatear_nombre(nombre)
        apellido = formatear_nombre(apellido)
        
        datos = {
            'nombre': nombre,
            'apellido': apellido,
            'tipo_documento': request.POST.get('tipo_documento', 'CC'),
            'cedula': cedula,
            'motivo': motivo,
            'area_id': request.POST.get('area', ''),
            'observaciones': request.POST.get('observaciones', ''),
        }
        
        if id_visitante:
            datos['visitante'] = get_object_or_404(Visitante, id_visitante=id_visitante)
            crear_visitante(request, datos, es_edicion=True)
            messages.success(request, f'Invitado {nombre} {apellido} actualizado exitosamente')
        else:
            crear_visitante(request, datos, es_edicion=False)
            messages.success(request, f'Invitado {nombre} {apellido} registrado exitosamente')
        
        return redirect('vigilante:consultar_invitado')
    
    context = {
        'areas': areas,
        'fechaHoy': date.today(),
        'horaAhora': datetime.now().strftime('%H:%M:%S'),
    }
    return render(request, 'registrar_invitado.html', context)


# ==================== REGISTRO MANUAL ====================

@login_required
def registro_manual(request):
    """Registro manual de ingreso/salida por fallo de huella"""
    
    if request.method == 'POST':
        documento = request.POST.get('documento', '').strip()
        tipo_movimiento = request.POST.get('tipoMovimiento', '')
        motivo = request.POST.get('motivo', '').strip()
        
        success, mensaje = procesar_registro_manual(request, documento, tipo_movimiento, motivo)
        
        if success:
            messages.success(request, mensaje)
        else:
            messages.error(request, mensaje)
        
        return redirect('vigilante:registro_manual')
    
    registros_list = obtener_registros_recientes(30)
    
    context = {
        'fechaHoy': date.today().strftime('%d/%m/%Y'),
        'horaAhora': datetime.now().strftime('%H:%M:%S'),
        'registrosList': registros_list,
    }
    
    return render(request, 'registro_manual.html', context)


# ==================== HISTORIAL ====================
from apps.seguridad_administracion.vigilante.services.historial_service import (
    aplicar_filtros_historial,
    combinar_historial
)

@login_required
def historial(request):
    """Vista del historial de registros (visitantes + registros manuales)"""
    
    # Obtener parámetros de filtro
    filtro_nombre = request.GET.get('nombre', '').strip()
    filtro_cedula = request.GET.get('cedula', '').strip()
    filtro_tipo = request.GET.get('tipo', '')
    filtro_fecha_desde = request.GET.get('fechaDesde', '')
    filtro_fecha_hasta = request.GET.get('fechaHasta', '')
    page = request.GET.get('page', 1)
    
    # Obtener todos los datos
    visitantes = obtener_todos_visitantes()
    registros_manual = obtener_todos_registros_manuales()
    
    # Aplicar filtros
    visitantes, registros_manual = aplicar_filtros_historial(
        visitantes, registros_manual,
        filtro_nombre, filtro_cedula,
        filtro_fecha_desde, filtro_fecha_hasta
    )
    
    # Combinar historial
    registros_unificados = combinar_historial(visitantes, registros_manual, filtro_tipo)
    
    # Paginación
    paginator = Paginator(registros_unificados, 20)
    page_obj = paginator.get_page(page)
    page_numbers = range(max(0, page_obj.number - 3), min(paginator.num_pages, page_obj.number + 2))
    ahora = datetime.now()
    
    
    context = {
        'registros_unificados': page_obj,
        'fechaHoy': ahora.strftime('%d/%m/%Y'),
        'horaAhora': ahora.strftime('%H:%M:%S'),
        'filtroNombre': filtro_nombre,
        'filtroCedula': filtro_cedula,
        'filtroTipo': filtro_tipo,
        'filtroFechaDesde': filtro_fecha_desde,
        'filtroFechaHasta': filtro_fecha_hasta,
        'totalPages': paginator.num_pages,
        'currentPage': page_obj.number - 1,
        'pageNumbers': page_numbers,
    }
    
    return render(request, 'historial.html', context)


# ==================== AJAX ====================

@login_required
def buscar_visitante_por_cedula(request):
    """Vista AJAX para buscar un visitante por cédula"""
    
    cedula = request.GET.get('cedula', '').strip()
    
    if not cedula:
        return JsonResponse({'encontrado': False, 'error': 'Cédula requerida'}, status=400)
    
    visitante = obtener_visitante_reciente_por_cedula(cedula)
    
    if visitante:
        en_sede = bool(
            visitante.id_asistencia_sede and not visitante.id_asistencia_sede.hora_salida
        )
        return JsonResponse({
            'encontrado': True,
            'nombre': visitante.nombre,
            'apellido': visitante.apellido,
            'tipo_documento': visitante.tipo_documento,
            'id_visitante': visitante.id_visitante,
            'en_sede': en_sede,
        })
    
    return JsonResponse({'encontrado': False})