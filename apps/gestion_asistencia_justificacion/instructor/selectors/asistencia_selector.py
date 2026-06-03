# selectors/asistencia_selector.py
from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente, Ficha, Competencia
from django.db.models import Q


def obtener_ficha_con_asistencias(ficha_id):
    return Ficha.objects.select_related(
        'id_programa', 'id_jornada'
    ).get(id_ficha=ficha_id)


def obtener_asistencias_base(ficha):
    return AsistenciaAmbiente.objects.filter(
        id_usuario__id_ficha=ficha
    ).select_related('id_usuario', 'id_competencia')


def buscar_aprendiz(ficha, texto):
    return ficha.usuarios_set.filter(
        Q(cedula=texto) |
        Q(nombre__icontains=texto) |
        Q(apellido__icontains=texto)
    ).first()


def obtener_competencias_programa(programa):
    return Competencia.objects.filter(id_programa=programa)