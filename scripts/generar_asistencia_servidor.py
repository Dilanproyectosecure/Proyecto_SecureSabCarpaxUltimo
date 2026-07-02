import os, sys, django, random
from datetime import date, time, timedelta

sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
cursor = connection.cursor()

# Configuracion
fecha_inicio = date(2026, 4, 20)
fecha_fin = date(2026, 6, 26)
aprendices = [1, 23, 57, 58, 59, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98]
nelson_id = 15
marcela_id = 14

# Competencias por instructor
competencias_instructor = {
    nelson_id: [17, 27],
    marcela_id: [28],
}

# Festivos Colombia 2026 (Ley 51 de 1983)
festivos = {
    date(2026, 5, 1),
    date(2026, 5, 18),
    date(2026, 6, 8),
    date(2026, 6, 15),
}

# Generar dias habiles
dias_habiles = []
fecha = fecha_inicio
while fecha <= fecha_fin:
    if fecha.weekday() < 5 and fecha not in festivos:
        dias_habiles.append(fecha)
    fecha += timedelta(days=1)

print(f'Dias habiles: {len(dias_habiles)}')

# Semilla para reproducibilidad
random.seed(42)

# Pre-calcular patron de instructor por dia
instructores_por_dia = {}
for i, dia in enumerate(dias_habiles):
    if i % 2 == 0:
        instructores_por_dia[dia] = nelson_id
    else:
        instructores_por_dia[dia] = marcela_id

# ============================================
# GENERAR ASISTENCIA SEDE
# ============================================
print('Generando asistencia_sede...')
registros_sede = []
for aprendiz in aprendices:
    prob_presente = 0.40 + random.uniform(-0.05, 0.05)
    prob_retardo = 0.15 + random.uniform(-0.03, 0.03)

    for dia in dias_habiles:
        instructor = instructores_por_dia[dia]
        rand = random.random()

        if rand < prob_presente:
            estado = 'Presente'
            h = random.choice([6, 6, 6, 7])
            m = random.choice([0, 5, 10, 15, 20, 25, 30])
            hora_ent = time(h, m, 0)
            hora_sal = time(12, 0, 0)
        elif rand < prob_presente + prob_retardo:
            estado = 'Retardo'
            hora_ent = time(random.choice([7, 7, 8]), random.choice([0, 10, 15, 20, 30, 45]), 0)
            hora_sal = time(12, 0, 0)
        else:
            estado = 'Ausente'
            hora_ent = None
            hora_sal = None

        registros_sede.append((aprendiz, dia, hora_ent, hora_sal, estado, instructor))

print(f'Insertando {len(registros_sede)} registros en asistencia_sede...')
cursor.execute('DELETE FROM asistencia_sede')
for r in registros_sede:
    cursor.execute(
        'INSERT INTO asistencia_sede (id_usuario, fecha, hora_entrada, hora_salida, estado_asistencia, id_instructor) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        r
    )

# ============================================
# GENERAR ASISTENCIA AMBIENTE
# ============================================
print('Generando asistencia_ambiente...')
registros_amb = []
for aprendiz in aprendices:
    for dia in dias_habiles:
        instructor = instructores_por_dia[dia]

        # Buscar en sede el estado de este dia
        estado_sede = None
        for r in registros_sede:
            if r[0] == aprendiz and r[1] == dia:
                estado_sede = r[4]
                break

        if estado_sede == 'Presente':
            estado_amb = 'Asistio'
        elif estado_sede == 'Retardo':
            estado_amb = 'Retardo'
        else:
            estado_amb = 'Inasistio'

        comps = competencias_instructor.get(instructor, [17])
        competencia = random.choice(comps)

        registros_amb.append((aprendiz, instructor, competencia, dia, estado_amb))

print(f'Insertando {len(registros_amb)} registros en asistencia_ambiente...')
cursor.execute('DELETE FROM asistencia_ambiente')
for r in registros_amb:
    cursor.execute(
        'INSERT INTO asistencia_ambiente (id_usuario, id_instructor, id_competencia, fecha, estado_asistencia) '
        'VALUES (%s, %s, %s, %s, %s)',
        r
    )

connection.commit()

# Verificacion
cursor.execute('SELECT COUNT(*) FROM asistencia_sede')
sede_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM asistencia_ambiente')
amb_count = cursor.fetchone()[0]

print(f'\n=== RESUMEN ===')
print(f'asistencia_sede: {sede_count} registros')
print(f'asistencia_ambiente: {amb_count} registros')
print(f'Rango: {fecha_inicio} a {fecha_fin}')
print(f'Instructores alternos: Nelson (pares), Marcela (impares)')
print('Done!')
