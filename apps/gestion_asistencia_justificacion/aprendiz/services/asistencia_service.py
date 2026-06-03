from collections import defaultdict

def analizar_inasistencias(todas_asistencias):
    # Agrupar por día
    asistencias_por_dia = defaultdict(list)

    for asistencia in todas_asistencias:
        asistencias_por_dia[asistencia.fecha].append(asistencia)

    dias_inasistencia_completa = []

    for fecha, asistencias_dia in asistencias_por_dia.items():

        tuvo_asistencia = any(
            a.estado_asistencia in ['Asistio', 'Retardo']
            for a in asistencias_dia
        )

        tiene_inasistencia_sin_justificar = any(
            a.estado_asistencia == 'Inasistio' and not a.tiene_justificacion_aprobada
            for a in asistencias_dia
        )

        if not tuvo_asistencia and tiene_inasistencia_sin_justificar:
            dias_inasistencia_completa.append(fecha)

    # ordenar
    dias_inasistencia_completa.sort(reverse=True)

    # 3 días consecutivos
    tiene_3 = False
    contador = 0
    fecha_anterior = None

    for fecha in dias_inasistencia_completa:
        if fecha_anterior is None:
            contador = 1
        else:
            if (fecha_anterior - fecha).days == 1:
                contador += 1
            else:
                break

        if contador >= 3:
            tiene_3 = True
            break

        fecha_anterior = fecha

    # 5 días total
    tiene_5 = len(dias_inasistencia_completa) >= 5

    return tiene_3, tiene_5, len(dias_inasistencia_completa)