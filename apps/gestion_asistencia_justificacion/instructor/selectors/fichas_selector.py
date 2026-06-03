from django.db.models import Count
from apps.reporte_monitoreo.coordinador.models import Ficha
from apps.login.models import Usuarios
from apps.reporte_monitoreo.coordinador.models import Competencia, AsistenciaSede
from django.db.models import Exists, OuterRef


def obtener_fichas_con_estadisticas():
    fichas = Ficha.objects.all()

    for ficha in fichas:
        ficha.total_aprendices = Usuarios.objects.filter(
            id_ficha=ficha
        ).count()

        ficha.total_competencias = Competencia.objects.filter(
            id_programa=ficha.id_programa
        ).count()

    return fichas



def obtener_datos_ficha(ficha, fecha):
    """
    Retorna:
    - aprendices
    - competencias
    - competencia principal
    """

    aprendices = Usuarios.objects.filter(
        id_ficha=ficha,
        estado__icontains='activo'
    ).order_by('apellido', 'nombre')

    competencias = Competencia.objects.filter(
        id_programa=ficha.id_programa
    )

    competencia = competencias.first() if competencias.exists() else None

    asistencia_sede_subquery = AsistenciaSede.objects.filter(
        id_usuario=OuterRef('id_usuario'),
        fecha=fecha,
        hora_entrada__isnull=False
    )

    aprendices = aprendices.annotate(
        tiene_asistencia_sede=Exists(asistencia_sede_subquery)
    )

    return aprendices, competencias, competencia