from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente
from django.db.models import Count, Case, When, IntegerField



def registrar_asistencia(aprendices, request, fecha, competencia):

    registradas = 0

    for aprendiz in aprendices:
        estado = request.POST.get(f'asistencia_{aprendiz.id_usuario}')

        if estado:
            AsistenciaAmbiente.objects.update_or_create(
                id_usuario=aprendiz,
                fecha=fecha,
                id_competencia=competencia,
                defaults={
                    'estado_asistencia': estado,
                    'id_instructor': request.user,
                }
            )
            registradas += 1

    return registradas



def generar_reporte(asistencias):
    return asistencias.values(
        'id_usuario__nombre',
        'id_usuario__apellido'
    ).annotate(
        asistio=Count(Case(When(estado_asistencia__iexact='asistio', then=1), output_field=IntegerField())),
        inasistio=Count(Case(When(estado_asistencia__iexact='inasistio', then=1), output_field=IntegerField())),
        retardo=Count(Case(When(estado_asistencia__iexact='retardo', then=1), output_field=IntegerField())),
    )


def generar_totales(asistencias):
    return asistencias.aggregate(
        total_asistio=Count(Case(When(estado_asistencia__iexact='asistio', then=1), output_field=IntegerField())),
        total_inasistio=Count(Case(When(estado_asistencia__iexact='inasistio', then=1), output_field=IntegerField())),
        total_retardo=Count(Case(When(estado_asistencia__iexact='retardo', then=1), output_field=IntegerField())),
    )