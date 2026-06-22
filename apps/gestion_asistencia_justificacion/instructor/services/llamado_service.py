from datetime import timedelta
from django.utils import timezone
from apps.login.models import Usuarios
from ..models import LlamadoAtencion
from apps.email_service import enviar_correo_seguro
from .inasistencias_service import calcular_inasistencias_aprendiz


def _obtener_coordinadores():
    return Usuarios.objects.filter(
        roleuser__role__name='coordinador',
        estado__icontains='activo'
    ).exclude(correo__isnull=True).exclude(correo__exact='')


def _enviar_llamado_correo(llamado):
    aprendiz = llamado.id_usuario
    instructor = llamado.id_instructor

    if not aprendiz.correo:
        return False

    nivel = llamado.nivel
    total = llamado.total_inasistencias

    if nivel == 1:
        asunto = 'SecureSab - Primer llamado de atención por inasistencias'
        mensaje_texto = (
            f'Cordial saludo {aprendiz.nombre} {aprendiz.apellido},\n\n'
            f'Por medio del presente, se le informa que ha acumulado {total} inasistencias injustificadas '
            f'en el seguimiento académico del programa de formación.\n\n'
            f'De acuerdo con el reglamento del aprendiz SENA, esta situación constituye un '
            f'PRIMER LLAMADO DE ATENCIÓN.\n\n'
            f'Lo invitamos a justificar dichas inasistencias ante su instructor '
            f'{instructor.nombre} {instructor.apellido} y a regularizar su asistencia.\n\n'
            f'Atentamente,\n'
            f'Sistema SecureSab - SENA'
        )
        mensaje_html = (
            f'<h2>Primer Llamado de Atención</h2>'
            f'<p>Cordial saludo <strong>{aprendiz.nombre} {aprendiz.apellido}</strong>,</p>'
            f'<p>Se le informa que ha acumulado <strong>{total} inasistencias injustificadas</strong> '
            f'en el seguimiento académico del programa de formación.</p>'
            f'<p>De acuerdo con el reglamento del aprendiz SENA, esta situación constituye un '
            f'<strong>PRIMER LLAMADO DE ATENCIÓN</strong>.</p>'
            f'<p>Lo invitamos a justificar dichas inasistencias ante su instructor '
            f'<strong>{instructor.nombre} {instructor.apellido}</strong> y a regularizar su asistencia.</p>'
            f'<hr><p><em>Atentamente,<br>Sistema SecureSab - SENA</em></p>'
        )
        cc = None

    elif nivel == 2:
        asunto = 'SecureSab - Segundo llamado de atención por inasistencias'
        mensaje_texto = (
            f'Cordial saludo {aprendiz.nombre} {aprendiz.apellido},\n\n'
            f'Mediante la presente, se le NOTIFICA que ha acumulado {total} inasistencias injustificadas '
            f'en lo que va del trimestre.\n\n'
            f'Esta es la SEGUNDA NOTIFICACIÓN formal y constituye un '
            f'SEGUNDO LLAMADO DE ATENCIÓN según el reglamento del aprendiz SENA.\n\n'
            f'Le recordamos que la inasistencia reiterada puede acarrear sanciones disciplinarias '
            f'y académicas. Le solicitamos presentarse ante su instructor '
            f'{instructor.nombre} {instructor.apellido} para justificar y regularizar su situación.\n\n'
            f'Atentamente,\n'
            f'Sistema SecureSab - SENA'
        )
        mensaje_html = (
            f'<h2>Segundo Llamado de Atención</h2>'
            f'<p>Cordial saludo <strong>{aprendiz.nombre} {aprendiz.apellido}</strong>,</p>'
            f'<p>Se le NOTIFICA que ha acumulado <strong>{total} inasistencias injustificadas</strong> '
            f'en lo que va del trimestre.</p>'
            f'<p>Esta es la <strong>SEGUNDA NOTIFICACIÓN formal</strong> y constituye un '
            f'<strong>SEGUNDO LLAMADO DE ATENCIÓN</strong> según el reglamento del aprendiz SENA.</p>'
            f'<p>Le recordamos que la inasistencia reiterada puede acarrear sanciones disciplinarias '
            f'y académicas. Le solicitamos presentarse ante su instructor '
            f'<strong>{instructor.nombre} {instructor.apellido}</strong> para justificar y regularizar su situación.</p>'
            f'<hr><p><em>Atentamente,<br>Sistema SecureSab - SENA</em></p>'
        )
        cc = None

    else:
        asunto = 'SecureSab - Tercer llamado - Proceso de deserción'
        mensaje_texto = (
            f'Cordial saludo {aprendiz.nombre} {aprendiz.apellido},\n\n'
            f'Habiendo acumulado {total} inasistencias injustificadas en el trimestre, se supera el '
            f'límite reglamentario establecido por el SENA.\n\n'
            f'En consecuencia, se da inicio al PROCESO DE DESERCIÓN y se procede con el '
            f'TERCER LLAMADO DE ATENCIÓN, dando traslado a la coordinación académica.\n\n'
            f'Le solicitamos presentarse URGENTEMENTE ante la coordinación para conocer '
            f'el estado de su proceso formativo.\n\n'
            f'Atentamente,\n'
            f'Sistema SecureSab - SENA'
        )
        mensaje_html = (
            f'<h2>Tercer Llamado - Proceso de Deserción</h2>'
            f'<p>Cordial saludo <strong>{aprendiz.nombre} {aprendiz.apellido}</strong>,</p>'
            f'<p>Habiendo acumulado <strong>{total} inasistencias injustificadas</strong> en el trimestre, '
            f'se supera el límite reglamentario establecido por el SENA.</p>'
            f'<p>En consecuencia, se da inicio al <strong>PROCESO DE DESERCIÓN</strong> y se procede con el '
            f'<strong>TERCER LLAMADO DE ATENCIÓN</strong>, dando traslado a la coordinación académica.</p>'
            f'<p>Le solicitamos presentarse <strong>URGENTEMENTE</strong> ante la coordinación para conocer '
            f'el estado de su proceso formativo.</p>'
            f'<hr><p><em>Atentamente,<br>Sistema SecureSab - SENA</em></p>'
        )
        coordinadores = _obtener_coordinadores()
        cc = [c.correo for c in coordinadores if c.correo] if coordinadores else None

    return enviar_correo_seguro(asunto, aprendiz.correo, mensaje_texto, mensaje_html, cc=cc)


def verificar_y_procesar_aprendices(aprendices, instructor):
    llamados_creados = []

    for aprendiz in aprendices:
        datos = calcular_inasistencias_aprendiz(aprendiz)
        total = datos["total"]

        niveles_a_verificar = []

        if total >= 5:
            niveles_a_verificar.append((3, 5))
        if total >= 4:
            niveles_a_verificar.append((2, 4))
        if total >= 3:
            niveles_a_verificar.append((1, 3))

        for nivel, umbral in niveles_a_verificar:
            existe = LlamadoAtencion.objects.filter(
                id_usuario=aprendiz,
                nivel=nivel
            ).exists()

            if not existe:
                llamado = LlamadoAtencion.objects.create(
                    id_usuario=aprendiz,
                    id_instructor=instructor,
                    nivel=nivel,
                    total_inasistencias=total,
                )

                enviado = _enviar_llamado_correo(llamado)
                if enviado:
                    llamado.notificado = True
                    llamado.fecha_notificacion = timezone.now()
                    llamado.save(update_fields=['notificado', 'fecha_notificacion'])

                llamados_creados.append(llamado)

    return llamados_creados


def obtener_llamados_recientes(instructor, dias=7):
    return LlamadoAtencion.objects.filter(
        id_instructor=instructor,
        fecha_creacion__gte=timezone.now() - timedelta(days=dias)
    ).select_related('id_usuario').order_by('-fecha_creacion')


def reenviar_correo(llamado_id):
    try:
        llamado = LlamadoAtencion.objects.select_related('id_usuario', 'id_instructor').get(id_llamado=llamado_id)
        enviado = _enviar_llamado_correo(llamado)
        if enviado:
            llamado.notificado = True
            llamado.fecha_notificacion = timezone.now()
            llamado.save(update_fields=['notificado', 'fecha_notificacion'])
        return enviado
    except LlamadoAtencion.DoesNotExist:
        return False


def notificar_aprendiz(aprendiz_id, instructor):
    try:
        aprendiz = Usuarios.objects.get(id_usuario=aprendiz_id)
    except Usuarios.DoesNotExist:
        return False, 'Aprendiz no encontrado'

    creados = verificar_y_procesar_aprendices([aprendiz], instructor)
    if creados:
        return True, 'Notificación enviada correctamente'

    llamado = LlamadoAtencion.objects.filter(
        id_usuario=aprendiz,
        id_instructor=instructor
    ).order_by('-nivel').first()

    if llamado:
        enviado = reenviar_correo(llamado.id_llamado)
        if enviado:
            return True, 'Correo reenviado correctamente'
        return False, 'No se pudo enviar el correo'

    return False, 'No se encontraron inasistencias suficientes para generar un llamado'
