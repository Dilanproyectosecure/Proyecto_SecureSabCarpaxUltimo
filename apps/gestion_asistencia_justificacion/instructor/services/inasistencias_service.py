from collections import defaultdict
from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente, Justificacion
from django.db.models import Exists, OuterRef


def calcular_inasistencias_aprendiz(aprendiz):

    asistencias = AsistenciaAmbiente.objects.filter(
        id_usuario=aprendiz
    ).annotate(
        tiene_justificacion_aprobada=Exists(
            Justificacion.objects.filter(
                id_asistencia_ambiente=OuterRef('id_asistencia_ambiente'),
                estado='Aprobado'
            )
        )
    )

    por_dia = defaultdict(list)

    for a in asistencias:
        por_dia[a.fecha].append(a)

    dias = []

    for fecha, items in por_dia.items():

        tuvo = any(x.estado_asistencia in ['Asistio', 'Retardo'] for x in items)

        injustificada = any(
            x.estado_asistencia == 'Inasistio' and not x.tiene_justificacion_aprobada
            for x in items
        )

        if not tuvo and injustificada:
            dias.append(fecha)

    dias.sort(reverse=True)

    # 3 consecutivos
    consecutivo = False
    contador = 0
    anterior = None

    for f in dias:
        if anterior and (anterior - f).days == 1:
            contador += 1
        else:
            contador = 1

        if contador >= 3:
            consecutivo = True
            break

        anterior = f

    return {
        "tiene_3": consecutivo,
        "tiene_5": len(dias) >= 5,
        "total": len(dias),
    }