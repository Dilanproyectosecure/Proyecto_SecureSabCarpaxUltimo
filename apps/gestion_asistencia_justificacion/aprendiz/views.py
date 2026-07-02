from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date

from apps.reporte_monitoreo.coordinador.models import Competencia

from .selectors.asistencia_selector import obtener_asistencias_usuario
from .selectors.inasistencias_selector import obtener_inasistencias_usuario

from .services.justificacion_service import crear_justificaciones
from .services.asistencia_service import analizar_inasistencias

from .utils.fechas import calcular_dias_entre
from apps.gestor_sistema.services import registrar_actividad

@login_required
def consultar_asistencia(request):
    """Vista para que el aprendiz consulte sus asistencias"""

    competencias = Competencia.objects.all()

    # SELECTOR
    todas_asistencias = obtener_asistencias_usuario(request.user)

    # SERVICE
    tiene_3_inasistencias, tiene_5_inasistencias, total_dias_inasistencia = analizar_inasistencias(
        todas_asistencias
    )

    # FILTROS
    asistencias_filtradas = todas_asistencias

    estado = request.GET.get('estado')
    competencia_id = request.GET.get('competencia')
    fecha = request.GET.get('fecha')

    if competencia_id and competencia_id.strip():
        asistencias_filtradas = asistencias_filtradas.filter(id_competencia_id=competencia_id)

    if fecha:
        asistencias_filtradas = asistencias_filtradas.filter(fecha=fecha)

    if estado and estado.strip():
        asistencias_filtradas = asistencias_filtradas.filter(
            estado_asistencia=estado
        )

    return render(request, 'consultar_asistencia.html', {
        'usuario': request.user,
        'asistencias': asistencias_filtradas,
        'competencias': competencias,
        'tiene_3_inasistencias': tiene_3_inasistencias,
        'tiene_5_inasistencias': tiene_5_inasistencias,
        'total_dias_inasistencia': total_dias_inasistencia
    })



@login_required
def radicar_justificacion(request):
    """
    Permite al aprendiz consultar inasistencias y radicar justificaciones.
    """

    competencias = Competencia.objects.all()

    # SELECTOR
    inasistencias = obtener_inasistencias_usuario(request.user)

    hoy = date.today()

    # SOLO PRESENTACIÓN (no lógica de negocio)
    for inasistencia in inasistencias:
        inasistencia.dias_pasados = calcular_dias_entre(inasistencia.fecha, hoy)

        if inasistencia.justificaciones:
            ultima = inasistencia.justificaciones[0]
            inasistencia.estado_justificacion = ultima.estado
            inasistencia.observacion_justificacion = ultima.observaciones
            inasistencia.tiene_habilitacion = any(
                j.estado == 'Habilitado' for j in inasistencia.justificaciones
            )
        else:
            inasistencia.estado_justificacion = None
            inasistencia.observacion_justificacion = ""
            inasistencia.tiene_habilitacion = False

    if request.method == 'POST':

        inasistencias_ids = request.POST.getlist('inasistencias')
        motivo = request.POST.get('motivo')
        soporte = request.FILES.get('soporte')

        if not inasistencias_ids:
            messages.error(request, 'Debe seleccionar al menos una inasistencia')
            return render(request, 'radicar_justificacion.html', {
                'usuario': request.user,
                'competencias': competencias,
                'inasistencias': inasistencias
            })

        if not motivo:
            messages.error(request, 'Debe seleccionar un motivo')
            return render(request, 'radicar_justificacion.html', {
                'usuario': request.user,
                'competencias': competencias,
                'inasistencias': inasistencias
            })

        if not soporte:
            messages.error(request, 'Debe adjuntar un archivo de soporte')
            return render(request, 'radicar_justificacion.html', {
                'usuario': request.user,
                'competencias': competencias,
                'inasistencias': inasistencias
            })

        extensiones_permitidas = ('.pdf', '.png')
        if not soporte.name.lower().endswith(extensiones_permitidas):
            messages.error(request, 'Solo se permiten archivos PDF o PNG')
            return render(request, 'radicar_justificacion.html', {
                'usuario': request.user,
                'competencias': competencias,
                'inasistencias': inasistencias
            })

        TAMANO_MAXIMO = 5 * 1024 * 1024
        if soporte.size > TAMANO_MAXIMO:
            messages.error(request, 'El archivo no debe superar los 5MB')
            return render(request, 'radicar_justificacion.html', {
                'usuario': request.user,
                'competencias': competencias,
                'inasistencias': inasistencias
            })

        # SERVICE
        cantidad_creadas = crear_justificaciones(
            usuario=request.user,
            inasistencias_ids=inasistencias_ids,
            motivo=motivo,
            soporte=soporte
        )

        # ✅ REGISTRAR ACTIVIDAD - ENVÍO DE JUSTIFICACIÓN
        registrar_actividad(
            usuario=request.user,
            tipo_accion='JUSTIFICACION_ENVIO',
            actividad='Envío de justificación',
            descripcion=f'El aprendiz {request.user.nombre} {request.user.apellido} envió {cantidad_creadas} justificación(es) por motivo: {motivo}',
            request=request
        )

        if cantidad_creadas > 0:
            messages.success(request, f'{cantidad_creadas} justificación(es) enviada(s)')
        else:
            messages.error(request, 'No se pudo enviar ninguna justificación')

        return redirect('aprendiz:consultar_asistencia')

    return render(request, 'radicar_justificacion.html', {
        'usuario': request.user,
        'competencias': competencias,
        'inasistencias': inasistencias
    })