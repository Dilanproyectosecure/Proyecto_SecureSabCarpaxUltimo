from django.db.models import Count, Exists, OuterRef
from django.db import connection
from apps.reporte_monitoreo.coordinador.models import Ficha, Competencia, AsistenciaSede
from apps.login.models import Usuarios


def obtener_fichas_con_estadisticas(instructor_id=None):
    """
    Retorna fichas con estadísticas.
    Si se proporciona instructor_id, solo retorna las fichas asignadas a ese instructor.
    """
    
    # Filtrar por instructor si se proporciona
    if instructor_id:
        fichas = Ficha.objects.filter(
            fichainstructor__id_instructor=instructor_id
        )
    else:
        fichas = Ficha.objects.all()
    
    # Calcular estadísticas para cada ficha
    for ficha in fichas:
        ficha.total_aprendices = Usuarios.objects.filter(
            id_ficha=ficha
        ).count()
        
        ficha.total_competencias = Competencia.objects.filter(
            id_programa=ficha.id_programa
        ).count()
    
    return fichas


def obtener_datos_ficha(ficha, fecha, instructor_id=None):
    """
    Retorna:
    - aprendices (listado de aprendices activos de la ficha)
    - competencias (solo las asignadas al instructor para esta ficha)
    - competencia principal (la primera de las asignadas)
    """
    
    # 1. Obtener aprendices activos de la ficha
    aprendices = Usuarios.objects.filter(
        id_ficha=ficha,
        estado__icontains='activo'
    ).order_by('apellido', 'nombre')
    
    # 2. Obtener competencias según el instructor
    if instructor_id:
        # Usar SQL crudo para evitar problemas de relaciones en Django
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT c.id_competencia, c.nombre_competencia, c.descripcion, 
                       c.estado, c.codigo_rap, c.asignatura_relacionada, c.trimestre
                FROM competencia c
                INNER JOIN ficha_instructor fi ON fi.id_competencia = c.id_competencia
                WHERE fi.id_ficha = %s AND fi.id_instructor = %s
            """, [ficha.id_ficha, instructor_id])
            
            competencias_ids = [row[0] for row in cursor.fetchall()]
            
            if competencias_ids:
                competencias = Competencia.objects.filter(id_competencia__in=competencias_ids)
            else:
                competencias = Competencia.objects.none()
    else:
        # Si no hay instructor, tomar todas las competencias del programa
        competencias = Competencia.objects.filter(id_programa=ficha.id_programa)
    
    # 3. Seleccionar la primera competencia como la activa
    competencia = competencias.first() if competencias.exists() else None
    
    # 4. Anotar si tienen asistencia en sede
    asistencia_sede_subquery = AsistenciaSede.objects.filter(
        id_usuario=OuterRef('id_usuario'),
        fecha=fecha,
        hora_entrada__isnull=False
    )
    
    aprendices = aprendices.annotate(
        tiene_asistencia_sede=Exists(asistencia_sede_subquery)
    )
    
    return aprendices, competencias, competencia