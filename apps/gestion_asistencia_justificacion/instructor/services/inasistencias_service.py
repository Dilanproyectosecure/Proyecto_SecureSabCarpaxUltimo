from collections import defaultdict
from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente, Justificacion
from django.db.models import Exists, OuterRef
from datetime import date, timedelta


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


def calcular_retardos_aprendiz(aprendiz):
    retardos = AsistenciaAmbiente.objects.filter(
        id_usuario=aprendiz,
        estado_asistencia='Retardo'
    ).order_by('-fecha')[:10]

    if not retardos.exists():
        return {
            "retardos_consecutivos": 0,
            "llamado_atencion": False,
        }

    fechas_retardos = [r.fecha for r in retardos]
    fechas_retardos.sort(reverse=True)

    retardos_consecutivos = 1
    for i in range(len(fechas_retardos) - 1):
        diff = (fechas_retardos[i] - fechas_retardos[i + 1]).days
        if diff == 1:
            retardos_consecutivos += 1
        else:
            break

    return {
        "retardos_consecutivos": retardos_consecutivos,
        "llamado_atencion": retardos_consecutivos >= 3,
    }