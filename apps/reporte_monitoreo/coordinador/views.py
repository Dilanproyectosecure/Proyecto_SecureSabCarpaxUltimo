from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.http import HttpResponse
from io import BytesIO
import json
from django.db.models import Q

from apps.gestor_sistema.services import registrar_actividad

from .selectors.estadistica_selector import (
    obtener_total_fichas_activas, obtener_total_aprendices, obtener_asistencia_sede_hoy,
    obtener_justificaciones_pendientes, obtener_datos_asistencias_semanales, obtener_alertas_por_ficha
)
from .selectors.asistencia_selector import (
    obtener_asistencias_ambiente_con_filtros, obtener_asistencias_sede_con_filtros,
    obtener_fichas_activas, obtener_jornadas, obtener_instructores, obtener_roles
)
from .selectors.justificacion_selector import (
    obtener_justificaciones_con_filtros, obtener_estadisticas_justificaciones
)
from .services.export_service import obtener_logo_pdf, obtener_filtros_display, preparar_registros_pdf, exportar_csv
from .utils.pdf_utils import generar_pdf_asistencia_ambiente, generar_pdf_asistencia_sede
from apps.login.models import Usuarios
from datetime import datetime
from io import BytesIO
from xhtml2pdf import pisa

# ==================== DASHBOARD ====================

@login_required
def inicio(request):
    """Vista principal del dashboard del coordinador"""
    
    coordinador = request.user
    presentes, total_asistencia, porcentaje = obtener_asistencia_sede_hoy()
    labels_semana, entradas_semana, salidas_semana = obtener_datos_asistencias_semanales()
    
    dashboard_data = {
        'labels_semana': labels_semana,
        'entradas_semana': entradas_semana,
        'salidas_semana': salidas_semana,
    }
    
    context = {
        'coordinador_nombre': f"{coordinador.nombre or ''} {coordinador.apellido or ''}".strip() or 'Coordinador',
        'coordinador_primer_nombre': coordinador.nombre or 'Coordinador',
        'coordinador_correo': coordinador.correo or '',
        'total_fichas_activas': obtener_total_fichas_activas(),
        'total_aprendices': obtener_total_aprendices(),
        'presentes_sede_hoy': presentes,
        'justificaciones_pendientes': obtener_justificaciones_pendientes(),
        'porcentaje_asistencia_hoy': porcentaje,
        'dashboard_data_json': json.dumps(dashboard_data),
    }
    
    
    return render(request, 'inicio.html', context)


# ==================== ASISTENCIA AMBIENTE ====================

@login_required
def asistencia_ambiente(request):
    """Vista para mostrar asistencias en ambiente con filtros"""
    
    asistencias = obtener_asistencias_ambiente_con_filtros(request)
    
    paginator = Paginator(asistencias, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'asistencias': page_obj,
        'fichas': obtener_fichas_activas(),
        'jornadas': obtener_jornadas(),
        'instructores': obtener_instructores(),
        'filtros': {
            'ficha': request.GET.get('ficha', ''),
            'documento': request.GET.get('documento', ''),
            'fecha': request.GET.get('fecha', ''),
            'estado': request.GET.get('estado', ''),
            'jornada': request.GET.get('jornada', ''),
            'instructor': request.GET.get('instructor', ''),
        }
    }
    
    return render(request, 'asistencia_ambiente.html', context)


@login_required
def exportar_asistencia_ambiente_pdf(request):
    """Exporta asistencia ambiente a PDF"""
    
    asistencias = obtener_asistencias_ambiente_con_filtros(request)
    
    # KPIs
    total = asistencias.count()
    asistio = asistencias.filter(estado_asistencia__icontains='asistio').count()
    inasistio = asistencias.filter(estado_asistencia__icontains='inasistio').count()
    justificada = asistencias.filter(
        Q(estado_asistencia__icontains='justificad') |
        Q(estado_asistencia__icontains='justificado')
    ).count()
    
    pct_asistio = round((asistio / total) * 100, 2) if total else 0
    pct_inasistio = round((inasistio / total) * 100, 2) if total else 0
    pct_justificada = round((justificada / total) * 100, 2) if total else 0
    
    # Alertas por ficha
    alertas_ficha = obtener_alertas_por_ficha(asistencias)
    
    # Registros para el PDF
    registros = preparar_registros_pdf(asistencias)
    
    # Logo
    logo_data = obtener_logo_pdf()
    
    context = {
        'total': total,
        'asistio': asistio,
        'inasistio': inasistio,
        'justificada': justificada,
        'pct_asistio': pct_asistio,
        'pct_inasistio': pct_inasistio,
        'pct_justificada': pct_justificada,
        'registros': registros,
        'alertas_ficha': alertas_ficha,
        'logo_data': logo_data,
        'fecha_actual': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'filtros_display': obtener_filtros_display(request),
    }
    
    html_string = render_to_string('reporte_ambiente.html', context, request=request)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_asistencia_ambiente.pdf"'
    
    pdf_buffer = BytesIO()
    pisa.CreatePDF(html_string, dest=pdf_buffer, encoding='utf-8')
    response.write(pdf_buffer.getvalue())
    return response


@login_required
def exportar_asistencia_ambiente_csv(request):
    """Exporta asistencia ambiente a CSV"""
    
    asistencias = obtener_asistencias_ambiente_con_filtros(request)
    
    def data_extractor(asistencia):
        usuario = asistencia.id_usuario
        ficha = usuario.id_ficha if usuario else None
        jornada = ficha.id_jornada if ficha else None
        return [
            usuario.cedula if usuario else '',
            usuario.nombre if usuario else '',
            usuario.apellido if usuario else '',
            ficha.numero_ficha if ficha else '',
            jornada.nombre_jornada if jornada else '',
            asistencia.fecha.strftime('%Y-%m-%d') if asistencia.fecha else '',
            asistencia.estado_asistencia or '',
            asistencia.id_competencia.nombre_competencia if asistencia.id_competencia else '',
            f"{getattr(asistencia.id_instructor, 'nombre', '')} {getattr(asistencia.id_instructor, 'apellido', '')}".strip(),
        ]
    
    headers = ['Documento', 'Nombre', 'Apellido', 'Ficha', 'Jornada', 'Fecha', 'Estado', 'Competencia', 'Instructor']
    
    return exportar_csv(asistencias, headers, 'reporte_asistencia_ambiente', data_extractor)


@login_required
def exportar_asistencia_sede_pdf(request):
    """Exporta asistencia sede a PDF"""
    
    asistencias = obtener_asistencias_sede_con_filtros(request)
    
    # ✅ PRIMERO los filtros y conteos
    total = asistencias.count()
    con_salida = asistencias.filter(hora_salida__isnull=False).count()
    sin_salida = total - con_salida
    
    # ✅ DESPUÉS el slice para el PDF
    asistencias = asistencias[:800]
    
    logo_data = obtener_logo_pdf()
    
    # Preparar datos para el PDF
    registros = []
    for asistencia in asistencias:
        usuario = asistencia.id_usuario
        ficha = getattr(usuario, 'id_ficha', None)
        jornada = getattr(ficha, 'id_jornada', None)
        registros.append({
            'documento': getattr(usuario, 'cedula', '-'),
            'nombre': f"{getattr(usuario, 'nombre', '')} {getattr(usuario, 'apellido', '')}".strip() or '-',
            'ficha': getattr(ficha, 'numero_ficha', 'Sin ficha'),
            'jornada': getattr(jornada, 'nombre_jornada', 'No asignada'),
            'fecha': asistencia.fecha.strftime('%Y-%m-%d') if asistencia.fecha else '-',
            'entrada': asistencia.hora_entrada.strftime('%H:%M') if asistencia.hora_entrada else '-',
            'salida': asistencia.hora_salida.strftime('%H:%M') if asistencia.hora_salida else '-',
        })
    
    return generar_pdf_asistencia_sede(request, asistencias, registros, logo_data)
# ==================== ASISTENCIA SEDE ====================

@login_required
def asistencia_sede(request):
    """Vista para mostrar asistencias en sede con filtros"""
    
    asistencias = obtener_asistencias_sede_con_filtros(request)
    
    paginator = Paginator(asistencias, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'asistencias': page_obj,
        'fichas': obtener_fichas_activas(),
        'jornadas': obtener_jornadas(),
        'roles': obtener_roles(),
        'filtros': {
            'ficha': request.GET.get('ficha', ''),
            'documento': request.GET.get('documento', ''),
            'fecha': request.GET.get('fecha', ''),
            'jornada': request.GET.get('jornada', ''),
            'rol': request.GET.get('rol', ''),
        }
    }
    
    return render(request, 'asistencia_sede.html', context)


@login_required
def exportar_asistencia_sede_csv(request):
    """Exporta asistencia sede a CSV"""
    
    asistencias = obtener_asistencias_sede_con_filtros(request)
    
    def data_extractor(asistencia):
        usuario = asistencia.id_usuario
        ficha = getattr(usuario, 'id_ficha', None)
        jornada = getattr(ficha, 'id_jornada', None)
        return [
            getattr(usuario, 'cedula', ''),
            getattr(usuario, 'nombre', ''),
            getattr(usuario, 'apellido', ''),
            getattr(ficha, 'numero_ficha', ''),
            getattr(jornada, 'nombre_jornada', ''),
            asistencia.fecha.strftime('%Y-%m-%d') if asistencia.fecha else '',
            asistencia.hora_entrada.strftime('%H:%M') if asistencia.hora_entrada else '',
            asistencia.hora_salida.strftime('%H:%M') if asistencia.hora_salida else '',
        ]
    
    headers = ['Documento', 'Nombre', 'Apellido', 'Ficha', 'Jornada', 'Fecha', 'Hora entrada', 'Hora salida']
    
    return exportar_csv(asistencias, headers, 'reporte_asistencia_sede', data_extractor)



# ==================== JUSTIFICACIONES ====================

@login_required
def justificaciones(request):
    """Vista para listar justificaciones con filtros"""
    
    justificaciones = obtener_justificaciones_con_filtros(request)
    total, pendientes, aprobadas, rechazadas = obtener_estadisticas_justificaciones(justificaciones)
    
    paginator = Paginator(justificaciones, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'justificaciones': page_obj,
        'total': total,
        'pendientes': pendientes,
        'aprobadas': aprobadas,
        'rechazadas': rechazadas,
        'filtros': {
            'search': request.GET.get('search', ''),
            'estado': request.GET.get('estado', 'all'),
        }
    }
    
    return render(request, 'justificaciones.html', context)


