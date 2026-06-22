# ==================== DJANGO CORE ====================
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.conf import settings
from django.http import JsonResponse
from datetime import date
import json
from apps.login.models import Usuarios
from apps.reporte_monitoreo.coordinador.models import ( Ficha, AsistenciaAmbiente, Competencia, Justificacion, Jornada, AsistenciaSede)
from .models import LlamadoAtencion
from .selectors.fichas_selector import obtener_fichas_con_estadisticas
from .selectors.fichas_selector import obtener_datos_ficha
from .selectors.asistencia_selector import ( obtener_ficha_con_asistencias, obtener_asistencias_base, buscar_aprendiz, obtener_competencias_programa)
from .selectors.justificacion_queries import ( obtener_justificaciones, filtrar_justificaciones)
from .services.inasistencias_service import calcular_inasistencias_aprendiz, calcular_retardos_aprendiz
from .services.asistencia_service import ( registrar_asistencia, generar_reporte, generar_totales)
from .services.aprendiz_service import actualizar_datos_aprendiz
from .services.justificacion_action_service import procesar_accion_justificacion
from .utils.pdf_utils import generate_pdf_response
from django.urls import reverse  
from apps.gestor_sistema.services import registrar_actividad



# ==================== FICHAS ====================
@login_required
def fichas_instructor(request):
    fichas = obtener_fichas_con_estadisticas(instructor_id=request.user.id_usuario)

    return render(request, 'fichas_instructor.html', {
        'fichas': fichas
    })




# ==================== GESTIONAR ASISTENCIA ====================
@login_required
def gestionar_asistencia(request):

    ficha_id = request.GET.get('ficha')
    fecha = request.GET.get('fecha', date.today().isoformat())
    competencia_id = request.GET.get('competencia')

    if not ficha_id:
        messages.error(request, 'Debe seleccionar una ficha')
        return redirect('instructor:fichas_instructor')

    try:
        ficha = Ficha.objects.select_related('id_programa', 'id_jornada').get(id_ficha=ficha_id)
        # SELECTOR
        aprendices, competencias, competencia = obtener_datos_ficha(ficha, fecha, instructor_id=request.user.id_usuario)

        # Seleccionar competencia específica si se proporciona
        if competencia_id and competencias.exists():
            try:
                competencia = competencias.get(id_competencia=competencia_id)
            except Competencia.DoesNotExist:
                competencia = competencias.first()

        for a in aprendices:
            datos = calcular_inasistencias_aprendiz(a)
            a.tiene_3_consecutivas = datos["tiene_3"]
            a.tiene_5_inasistencias = datos["tiene_5"]
            a.total_inasistencias = datos["total"]
            retardos = calcular_retardos_aprendiz(a)
            a.retardos_consecutivos = retardos["retardos_consecutivos"]
            a.tiene_retardos_consecutivos = retardos["llamado_atencion"]
            a.correo_ya_enviado = False

        from apps.gestor_sistema.models import registro_actividad
        from django.db.models import Q
        import re
        correos_enviados = registro_actividad.objects.filter(
            Q(tipo_accion='EMAIL_INASISTENCIA') & Q(descripcion__contains=f'ficha {ficha.numero_ficha}') & Q(descripcion__contains=f'fecha {fecha}'),
        )
        ids_enviados = set()
        for reg in correos_enviados:
            match = re.search(r'ids\[([^\]]+)\]', reg.descripcion)
            if match:
                for uid in match.group(1).split(','):
                    try:
                        ids_enviados.add(int(uid.strip()))
                    except ValueError:
                        pass
        for a in aprendices:
            if a.id_usuario in ids_enviados:
                a.correo_ya_enviado = True

        if request.method == 'POST':
            post_competencia_id = request.POST.get('competencia_id')
            if post_competencia_id and competencias.exists():
                try:
                    competencia = competencias.get(id_competencia=post_competencia_id)
                except Competencia.DoesNotExist:
                    pass

            registradas = registrar_asistencia(aprendices, request, fecha, competencia)

            llamados = verificar_y_procesar_aprendices(aprendices, request.user)
            if llamados:
                for ll in llamados:
                    nivel_nombre = dict(LlamadoAtencion.NIVEL_CHOICES).get(ll.nivel, f'Llamado nivel {ll.nivel}')
                    messages.warning(
                        request,
                        f'{nivel_nombre} generado para {ll.id_usuario.nombre} {ll.id_usuario.apellido} '
                        f'({ll.total_inasistencias} inasistencias) - Correo enviado.'
                    )

            registrar_actividad(
                usuario=request.user,
                tipo_accion='ASISTENCIA_REGISTRO',
                actividad='Registro de asistencia',
                descripcion=f'Instructor {request.user.nombre} {request.user.apellido} registró {registradas} asistencias para la ficha {ficha.numero_ficha} en fecha {fecha}',
                request=request
            )

            messages.success(request, f'{registradas} asistencias registradas')
            url = reverse('instructor:gestionar_asistencia')
            return redirect(f'{url}?ficha={ficha_id}&fecha={fecha}&competencia={competencia.id_competencia if competencia else ""}')

        return render(request, 'gestionar_asistencia.html', {
            'ficha': ficha,
            'aprendices': aprendices,
            'competencias': competencias,
            'competencia': competencia,
            'fecha_seleccionada': fecha,
            'llamados_recientes': obtener_llamados_recientes(request.user),
        })

    except Ficha.DoesNotExist:
        messages.error(request, 'La ficha no existe')
        return redirect('instructor:fichas_instructor')





# ==================== ACTUALIZAR APRENDIZ ====================
@login_required
def actualizar_aprendiz(request):
    """Vista para actualizar datos de un aprendiz desde el modal"""

    if request.method == 'POST':

        user_id = request.POST.get('user_id')
        valor = request.POST.get('valor')
        campo = request.POST.get('campo')
        ficha_id = request.POST.get('ficha_id')
        fecha = request.POST.get('fecha')

        try:
            actualizar_datos_aprendiz(user_id, campo, valor)

            messages.success(
                request,
                f'{campo.capitalize()} actualizado correctamente'
            )

        except Usuarios.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect(
            f'/instructor/fichas/gestionar-asistencia/?ficha={ficha_id}&fecha={fecha}'
        )

    return redirect('instructor:fichas_instructor')




# ==================== CONSULTAR ASISTENCIAS ====================
@login_required
def consultar_asistenciaI(request):

    ficha_id = request.GET.get('ficha')
    aprendiz_busqueda = request.GET.get('aprendiz')
    competencia_id = request.GET.get('competencia')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    estado = request.GET.get('estado')
    reporte = request.GET.get('reporte')
    reporte_desde = request.GET.get('reporte_desde')
    reporte_hasta = request.GET.get('reporte_hasta')

    fichas = Ficha.objects.all().select_related('id_programa', 'id_jornada')

    ficha_seleccionada_obj = None
    aprendiz_encontrado = None
    asistencias = AsistenciaAmbiente.objects.none()
    llamado_activo = None
    total_inasistencias = 0

    if ficha_id:
        ficha_seleccionada_obj = obtener_ficha_con_asistencias(ficha_id)
        asistencias = obtener_asistencias_base(ficha_seleccionada_obj)

        if aprendiz_busqueda:
            aprendiz_encontrado = buscar_aprendiz(ficha_seleccionada_obj, aprendiz_busqueda)

        if competencia_id:
            asistencias = asistencias.filter(id_competencia_id=competencia_id)

        if estado:
            asistencias = asistencias.filter(estado_asistencia=estado)

        if reporte and reporte_desde and reporte_hasta:

            asistencias = asistencias.filter(
                fecha__range=[reporte_desde, reporte_hasta]
            )

            reporte_resumen = generar_reporte(asistencias)
            totales = generar_totales(asistencias)

            context_pdf = {
                'reporte_resumen': reporte_resumen,
                'totales': totales,
                'desde': reporte_desde,
                'hasta': reporte_hasta,
                'ficha': ficha_seleccionada_obj,
                'jornada': ficha_seleccionada_obj.id_jornada
            }

            return generate_pdf_response(
                'reportes/reporteGeneral_plantilla.html',
                context_pdf,
                filename=f"reporte_general_{ficha_id}.pdf"
            )

        if fecha_desde:
            asistencias = asistencias.filter(fecha__gte=fecha_desde)

        if fecha_hasta:
            asistencias = asistencias.filter(fecha__lte=fecha_hasta)

        if aprendiz_encontrado:
            asistencias = asistencias.filter(id_usuario=aprendiz_encontrado)

        asistencias = asistencias.order_by('-fecha', 'id_usuario__apellido')


    paginator = Paginator(asistencias, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    competencias = obtener_competencias_programa(
        ficha_seleccionada_obj.id_programa if ficha_seleccionada_obj else None
    ) if ficha_seleccionada_obj else Competencia.objects.none()

    if aprendiz_encontrado:
        llamado_activo = LlamadoAtencion.objects.filter(
            id_usuario=aprendiz_encontrado,
            id_instructor=request.user
        ).select_related('id_usuario').order_by('-nivel').first()

        datos_asis = calcular_inasistencias_aprendiz(aprendiz_encontrado)
        total_inasistencias = datos_asis["total"]

    return render(request, 'consultar_asistenciaI.html', {
        'asistencias': page_obj,
        'fichas': fichas,
        'competencias': competencias,
        'ficha_seleccionada': int(ficha_id) if ficha_id else None,
        'ficha_seleccionada_obj': ficha_seleccionada_obj,
        'aprendiz_encontrado': aprendiz_encontrado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estado': estado,
        'llamado_activo': llamado_activo,
        'total_inasistencias': total_inasistencias,
    })




# ==================== GESTIONAR JUSTIFICACIONES ====================
@login_required
def gestionar_justificaciones(request):

    ficha_id = request.GET.get('ficha')
    jornada_id = request.GET.get('jornada')
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    aprendiz = request.GET.get('aprendiz')

    fichas = Ficha.objects.all().select_related('id_programa')
    jornadas = Jornada.objects.all()

    # SELECTOR
    justificaciones = obtener_justificaciones()

    # FILTROS
    justificaciones = filtrar_justificaciones(
        justificaciones,
        ficha_id,
        jornada_id,
        estado,
        fecha_desde,
        fecha_hasta,
        aprendiz
    )

    # PAGINACIÓN
    paginator = Paginator(justificaciones, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'gestionar_justificaciones.html', {
        'justificaciones': page_obj,
        'fichas': fichas,
        'jornadas': jornadas,
        'ficha_seleccionada': int(ficha_id) if ficha_id else None,
        'jornada_seleccionada': int(jornada_id) if jornada_id else None,
        'estado': estado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'aprendiz_busqueda': aprendiz,
        'MEDIA_URL': settings.MEDIA_URL,
    })




# ==================== PROCESAR JUSTIFICACIÓN ====================
@login_required
def procesar_justificacion(request):

    if request.method != 'POST':
        return redirect('instructor:gestionar_justificaciones')

    justificacion_id = request.POST.get('justificacion_id')
    accion = request.POST.get('accion')
    observaciones = request.POST.get('observaciones', '')

    success, mensaje = procesar_accion_justificacion(
        justificacion_id,
        accion,
        observaciones
    )

    # ✅ REGISTRAR ACTIVIDAD - APROBACIÓN/RECHAZO DE JUSTIFICACIÓN
    if success:
        tipo_accion = 'JUSTIFICACION_APROBAR' if accion == 'aprobar' else 'JUSTIFICACION_RECHAZAR'
        actividad = 'Aprobación de justificación' if accion == 'aprobar' else 'Rechazo de justificación'
        
        registrar_actividad(
            usuario=request.user,
            tipo_accion=tipo_accion,
            actividad=actividad,
            descripcion=f'Instructor {request.user.nombre} {request.user.apellido} {actividad.lower()} (ID: {justificacion_id}) - Observaciones: {observaciones}',
            request=request
        )

    if success:
        messages.success(request, mensaje)
    else:
        messages.error(request, mensaje)

    return redirect('instructor:gestionar_justificaciones')



