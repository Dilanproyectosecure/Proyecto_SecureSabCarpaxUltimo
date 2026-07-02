from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date
import os

from apps.reporte_monitoreo.coordinador.models import Competencia, PeticionJustificacion, AsistenciaAmbiente

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

        if inasistencia.peticiones:
            ultima_pet = inasistencia.peticiones[0]
            inasistencia.peticion_estado = ultima_pet.estado
            inasistencia.peticion_id = ultima_pet.id_peticion
            inasistencia.peticion_motivo = ultima_pet.motivo_extension
            inasistencia.peticion_observaciones = ultima_pet.observaciones_instructor
        else:
            inasistencia.peticion_estado = None
            inasistencia.peticion_id = None
            inasistencia.peticion_motivo = ""
            inasistencia.peticion_observaciones = ""

        inasistencia.expirada = inasistencia.dias_pasados > 3
        inasistencia.peticion_aprobada = inasistencia.peticion_estado == 'Aprobado'

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

        for aid in inasistencias_ids:
            try:
                asis = AsistenciaAmbiente.objects.get(id_asistencia_ambiente=aid, id_usuario=request.user)
                dias_pasados = (hoy - asis.fecha).days
                if dias_pasados > 3:
                    pet_ok = PeticionJustificacion.objects.filter(
                        id_asistencia_ambiente=asis,
                        id_aprendiz=request.user,
                        estado='Aprobado'
                    ).exists()
                    if not pet_ok:
                        messages.error(request, f'La inasistencia del {asis.fecha} supera los 3 días. Debe solicitar una petición al instructor.')
                        return render(request, 'radicar_justificacion.html', {
                            'usuario': request.user,
                            'competencias': competencias,
                            'inasistencias': inasistencias
                        })
            except AsistenciaAmbiente.DoesNotExist:
                continue

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

        ext = os.path.splitext(soporte.name)[1].lower()
        if ext not in ('.pdf', '.png'):
            messages.error(request, 'Solo se permiten archivos PDF o PNG')
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


@login_required
def solicitar_peticion(request):
    if request.method != 'POST':
        return redirect('aprendiz:radicar_justificacion')

    asistencia_id = request.POST.get('asistencia_id')
    motivo = request.POST.get('motivo_extension', '').strip()

    if not asistencia_id or not motivo:
        messages.error(request, 'Debe proporcionar un motivo')
        return redirect('aprendiz:radicar_justificacion')

    hoy = date.today()
    PeticionJustificacion.objects.create(
        id_asistencia_ambiente_id=asistencia_id,
        id_aprendiz=request.user,
        motivo_extension=motivo,
        fecha_creacion=hoy,
        estado='Pendiente'
    )

    registrar_actividad(
        usuario=request.user,
        tipo_accion='PETICION_JUSTIFICACION',
        actividad='Solicitud de petición para justificar',
        descripcion=f'El aprendiz {request.user.nombre} {request.user.apellido} solicitó permiso para justificar inasistencia #{asistencia_id}',
        request=request
    )

    messages.success(request, 'Petición enviada al instructor. Espera su aprobación.')
    return redirect('aprendiz:radicar_justificacion')