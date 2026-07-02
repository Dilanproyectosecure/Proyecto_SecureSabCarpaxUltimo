# ==================== DJANGO CORE ====================
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.conf import settings
from django.http import JsonResponse
from datetime import date, timedelta
from django.db.models import Q, Subquery, OuterRef
from apps.login.models import Usuarios
from apps.reporte_monitoreo.coordinador.models import ( Ficha, AsistenciaAmbiente, Competencia, Justificacion, PeticionJustificacion, FichaInstructor, Jornada, AsistenciaSede)
from .models import LlamadoAtencion
from .selectors.fichas_selector import obtener_fichas_con_estadisticas
from .selectors.fichas_selector import obtener_datos_ficha
from .selectors.asistencia_selector import ( obtener_ficha_con_asistencias, obtener_asistencias_base, buscar_aprendiz, obtener_competencias_programa)
from .selectors.justificacion_queries import ( obtener_justificaciones, filtrar_justificaciones, obtener_peticiones_pendientes)
from .services.inasistencias_service import calcular_inasistencias_aprendiz, calcular_retardos_aprendiz
from .services.asistencia_service import ( registrar_asistencia, generar_reporte, generar_totales)
from .services.aprendiz_service import actualizar_datos_aprendiz
from .services.justificacion_action_service import procesar_accion_justificacion, habilitar_carga_evidencia
from .services.llamado_service import verificar_y_procesar_aprendices, verificar_retardos_aprendices, obtener_llamados_recientes, reenviar_correo, notificar_aprendiz as servicio_notificar_aprendiz
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
            llamados_ret = verificar_retardos_aprendices(aprendices, request.user)
            llamados = (llamados or []) + (llamados_ret or [])
            if llamados:
                for ll in llamados:
                    nivel_nombre = dict(LlamadoAtencion.NIVEL_CHOICES).get(ll.nivel, f'Llamado nivel {ll.nivel}')
                    if ll.total_inasistencias < 0:
                        motivo = f'{abs(ll.total_inasistencias)} retardos consecutivos'
                    else:
                        motivo = f'{ll.total_inasistencias} inasistencias'
                    messages.warning(
                        request,
                        f'{nivel_nombre} generado para {ll.id_usuario.nombre} {ll.id_usuario.apellido} '
                        f'({motivo}) - Correo enviado.'
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

        aprendices_con_sede = [a for a in aprendices if not hasattr(a, 'tiene_asistencia_sede') or a.tiene_asistencia_sede]
        aprendices_sin_sede = [a for a in aprendices if hasattr(a, 'tiene_asistencia_sede') and not a.tiene_asistencia_sede]

        return render(request, 'gestionar_asistencia.html', {
            'ficha': ficha,
            'aprendices': aprendices,
            'aprendices_con_sede': aprendices_con_sede,
            'aprendices_sin_sede': aprendices_sin_sede,
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
            asistencias = asistencias.filter(estado_asistencia__iexact=estado)

        if aprendiz_encontrado:
            asistencias = asistencias.filter(id_usuario=aprendiz_encontrado)

        if reporte and reporte_desde and reporte_hasta:

            asistencias = asistencias.filter(
                fecha__range=[reporte_desde, reporte_hasta]
            )

            reporte_resumen = generar_reporte(asistencias)
            totales = generar_totales(asistencias)

            competencia_nombre = ''
            if competencia_id:
                try:
                    competencia_nombre = Competencia.objects.get(id_competencia=competencia_id).nombre_competencia
                except Competencia.DoesNotExist:
                    competencia_nombre = competencia_id

            context_pdf = {
                'reporte_resumen': reporte_resumen,
                'totales': totales,
                'desde': reporte_desde,
                'hasta': reporte_hasta,
                'ficha': ficha_seleccionada_obj,
                'jornada': ficha_seleccionada_obj.id_jornada,
                'aprendiz_filtro': aprendiz_busqueda or '',
                'competencia_filtro': competencia_nombre,
                'estado_filtro': estado or '',
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

        asistencias = asistencias.order_by('-fecha', 'id_usuario__apellido')

    total_asistio = asistencias.filter(estado_asistencia__iexact='Asistio').count()
    total_inasistio = asistencias.filter(estado_asistencia__iexact='Inasistio').count()
    total_retardo = asistencias.filter(estado_asistencia__iexact='Retardo').count()

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
        'aprendiz_busqueda': aprendiz_busqueda or '',
        'competencia_seleccionada': int(competencia_id) if competencia_id else None,
        'fecha_desde': fecha_desde or '',
        'fecha_hasta': fecha_hasta or '',
        'estado': estado or '',
        'llamado_activo': llamado_activo,
        'total_inasistencias': total_inasistencias,
        'total_asistio': total_asistio,
        'total_inasistio': total_inasistio,
        'total_retardo': total_retardo,
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
    justificaciones = obtener_justificaciones(instructor_id=request.user.id_usuario)

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

    # INASISTENCIAS EXPIRADAS SIN JUSTIFICACION (para habilitar carga)
    hoy = date.today()
    fecha_limite = hoy - timedelta(days=3)
    inasistencias_expiradas = AsistenciaAmbiente.objects.filter(
        estado_asistencia='Inasistio',
        id_instructor=request.user,
        fecha__lt=fecha_limite,
    ).exclude(
        id_asistencia_ambiente__in=Justificacion.objects.filter(
            estado__in=['Pendiente', 'Aprobado', 'Habilitado']
        ).values('id_asistencia_ambiente')
    ).select_related(
        'id_usuario',
        'id_usuario__id_ficha',
        'id_usuario__id_ficha__id_jornada',
        'id_competencia'
    ).distinct()

    inasistencias_habilitadas_ids = set(
        Justificacion.objects.filter(
            estado='Habilitado',
            id_asistencia_ambiente__in=inasistencias_expiradas
        ).values_list('id_asistencia_ambiente_id', flat=True)
    )

    # PETICIONES PENDIENTES
    peticiones_pendientes = obtener_peticiones_pendientes(instructor_id=request.user.id_usuario)

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
        'inasistencias_expiradas': inasistencias_expiradas,
        'inasistencias_habilitadas_ids': inasistencias_habilitadas_ids,
        'peticiones_pendientes': peticiones_pendientes,
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
        observaciones,
        instructor_id=request.user.id_usuario
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


# ==================== HABILITAR CARGA DE EVIDENCIA ====================
@login_required
def habilitar_carga(request):

    if request.method != 'POST':
        return redirect('instructor:gestionar_justificaciones')

    asistencia_id = request.POST.get('asistencia_id')
    observaciones = request.POST.get('observaciones', '')

    if not asistencia_id:
        messages.error(request, 'ID de inasistencia no proporcionado')
        return redirect('instructor:gestionar_justificaciones')

    success, mensaje = habilitar_carga_evidencia(
        asistencia_id=asistencia_id,
        instructor=request.user,
        observaciones=observaciones
    )

    if success:
        registrar_actividad(
            usuario=request.user,
            tipo_accion='JUSTIFICACION_HABILITAR',
            actividad='Habilitación de carga de evidencia',
            descripcion=f'Instructor {request.user.nombre} {request.user.apellido} habilitó la carga de evidencia para la inasistencia ID: {asistencia_id}',
            request=request
        )
        messages.success(request, mensaje)
    else:
        messages.error(request, mensaje)

    return redirect('instructor:gestionar_justificaciones')


# ==================== PROCESAR PETICIÓN DE JUSTIFICACIÓN (AJAX) ====================
@login_required
def procesar_peticion(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    import json
    peticion_id = request.POST.get('peticion_id')
    accion = request.POST.get('accion')
    observaciones = request.POST.get('observaciones', '')

    if not peticion_id or accion not in ('aprobar', 'rechazar'):
        return JsonResponse({'success': False, 'error': 'Datos inválidos'}, status=400)

    try:
        peticion = PeticionJustificacion.objects.select_related(
            'id_asistencia_ambiente',
            'id_asistencia_ambiente__id_competencia',
            'id_aprendiz'
        ).get(id_peticion=peticion_id)
    except PeticionJustificacion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Petición no encontrada'}, status=404)

    if peticion.id_asistencia_ambiente and peticion.id_asistencia_ambiente.id_competencia_id:
        competencia_id = peticion.id_asistencia_ambiente.id_competencia_id
        tiene_permiso = FichaInstructor.objects.filter(
            id_instructor=request.user.id_usuario,
            id_competencia=competencia_id
        ).exists()
        if not tiene_permiso:
            return JsonResponse({'success': False, 'error': 'No tiene permiso para procesar peticiones de esta competencia'}, status=403)

    if accion == 'aprobar':
        peticion.estado = 'Aprobado'
    else:
        peticion.estado = 'Rechazado'

    if observaciones:
        peticion.observaciones_instructor = observaciones

    peticion.save()

    registrar_actividad(
        usuario=request.user,
        tipo_accion='PETICION_JUSTIFICACION_' + accion.upper(),
        actividad='Petición de justificación ' + ('aprobada' if accion == 'aprobar' else 'rechazada'),
        descripcion=f'Instructor {request.user.nombre} {request.user.apellido} {accion}ó petición #{peticion_id} de {peticion.id_aprendiz.nombre} {peticion.id_aprendiz.apellido}',
        request=request
    )

    return JsonResponse({'success': True, 'message': f'Petición {accion}ada correctamente'})


# ==================== REENVIAR NOTIFICACIÓN LLAMADO (AJAX) ====================
@login_required
def reenviar_notificacion_llamado(request, llamado_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    enviado = reenviar_correo(llamado_id)
    if enviado:
        return JsonResponse({'success': True, 'message': 'Correo reenviado correctamente'})
    return JsonResponse({'success': False, 'error': 'No se pudo reenviar el correo'}, status=400)


# ==================== NOTIFICAR APRENDIZ (AJAX) ====================
@login_required
def notificar_aprendiz(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    aprendiz_id = request.POST.get('aprendiz_id')
    if not aprendiz_id:
        return JsonResponse({'success': False, 'error': 'aprendiz_id requerido'}, status=400)
    success, mensaje = servicio_notificar_aprendiz(aprendiz_id, request.user)
    if success:
        return JsonResponse({'success': True, 'message': mensaje})
    return JsonResponse({'success': False, 'error': mensaje}, status=400)


# ==================== DESCARTAR NOTIFICACION (AJAX) ====================
@login_required
def dismiss_llamado(request, llamado_id):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    try:
        llamado = LlamadoAtencion.objects.get(id_llamado=llamado_id, id_instructor=request.user)
        llamado.notificado = True
        llamado.save(update_fields=['notificado'])
        return JsonResponse({'success': True})
    except LlamadoAtencion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No encontrado'}, status=404)


# ==================== ENVIAR CORREOS INASISTENCIA (AJAX) ====================
@login_required
def enviar_correos_inasistencia_view(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    import json
    import logging
    logger = logging.getLogger('apps.gestion_asistencia_justificacion.instructor')

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    ids = data.get('aprendices_ids', [])
    ficha_id = data.get('ficha_id')
    fecha = data.get('fecha')
    competencia_id = data.get('competencia_id')

    if not ids or not ficha_id:
        return JsonResponse({'success': False, 'error': 'Faltan datos'}, status=400)

    try:
        from apps.reporte_monitoreo.coordinador.models import Ficha, Competencia
        from .services.email_service import enviar_correos_inasistencia
        from apps.gestor_sistema.services import registrar_actividad
        from apps.login.models import Usuarios

        ficha = Ficha.objects.get(id_ficha=ficha_id)
    except Ficha.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ficha no encontrada'}, status=404)

    competencia = Competencia.objects.filter(id_competencia=competencia_id).first() if competencia_id else None
    aprendices = Usuarios.objects.filter(id_usuario__in=ids)

    resultado = enviar_correos_inasistencia(list(aprendices), ficha, fecha, competencia)

    ids_enviados = [d['id'] for d in resultado['detalles'] if d['estado'] == 'enviado']
    if ids_enviados:
        registrar_actividad(
            usuario=request.user,
            tipo_accion='EMAIL_INASISTENCIA',
            actividad='Envío de correos de inasistencia',
            descripcion=f'Correos enviados a {len(ids_enviados)} aprendices - ficha {ficha.numero_ficha} - fecha {fecha} ids[{",".join(str(i) for i in ids_enviados)}]',
            request=request
        )

    fallidos = resultado.get('fallidos', 0)
    if fallidos > 0:
        logger.warning(
            f"Envío inasistencia: {fallidos} correos fallaron para ficha {ficha.numero_ficha} fecha {fecha}. "
            f"Detalles: {[d for d in resultado['detalles'] if d['estado'] == 'fallido']}"
        )

    return JsonResponse(resultado)


# ==================== ENVIAR CORREO RETARDO (AJAX) ====================
@login_required
def enviar_correo_retardo_view(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    import json
    import logging
    logger = logging.getLogger('apps.gestion_asistencia_justificacion.instructor')

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    aprendiz_id = data.get('aprendiz_id')
    retardos = data.get('retardos_consecutivos', 0)

    if not aprendiz_id:
        return JsonResponse({'success': False, 'error': 'aprendiz_id requerido'}, status=400)

    try:
        from apps.reporte_monitoreo.coordinador.models import Ficha
        from .services.email_service import enviar_correo_retardo
        from apps.login.models import Usuarios

        ficha_id = data.get('ficha_id')
        ficha = Ficha.objects.filter(id_ficha=ficha_id).first() if ficha_id else None
        aprendiz = Usuarios.objects.get(id_usuario=aprendiz_id)
    except Usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Aprendiz no encontrado'}, status=404)

    fecha = data.get('fecha', '')

    enviado = enviar_correo_retardo(aprendiz, retardos, ficha, fecha)
    if enviado:
        from apps.gestor_sistema.services import registrar_actividad
        registrar_actividad(
            usuario=request.user,
            tipo_accion='EMAIL_RETARDO',
            actividad='Envío de correo de retardo',
            descripcion=f'Correo de retardo enviado a {aprendiz.nombre} {aprendiz.apellido} ({retardos} retardos)',
            request=request
        )
        return JsonResponse({'enviado': True, 'mensaje': 'Correo de retardo enviado correctamente'})
    else:
        logger.warning(f"No se pudo enviar correo de retardo a {aprendiz.nombre} {aprendiz.apellido}")
    return JsonResponse({'enviado': False, 'mensaje': 'No se pudo enviar el correo'}, status=400)
