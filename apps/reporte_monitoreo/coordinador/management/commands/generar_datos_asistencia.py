import random
from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = 'Genera datos de asistencia ambiente y sede para aprendices de una ficha'

    def add_arguments(self, parser):
        parser.add_argument('--ficha', type=int, default=1, help='ID de la ficha (default: 1)')
        parser.add_argument('--dias', type=int, default=5, help='Dias habiles hacia atras (default: 5)')

    def handle(self, *args, **options):
        ficha_id = options['ficha']
        dias = options['dias']
        conn = connections['default']
        cursor = conn.cursor()

        cursor.execute(
            'SELECT id_usuario FROM usuarios WHERE id_ficha = %s AND id_usuario IS NOT NULL',
            [ficha_id]
        )
        aprendices = [row[0] for row in cursor.fetchall()]

        if not aprendices:
            self.stdout.write(self.style.ERROR(f'No hay aprendices en la ficha {ficha_id}'))
            return

        cursor.execute(
            'SELECT id_instructor FROM ficha_instructor WHERE id_ficha = %s',
            [ficha_id]
        )
        instructores = [row[0] for row in cursor.fetchall()]
        if not instructores:
            instructores = [14, 15]

        cursor.execute(
            'SELECT id_competencia FROM competencia WHERE nombre_competencia LIKE %s LIMIT 1',
            ['%DESARROLLAR%SOFTWARE%']
        )
        row = cursor.fetchone()
        competencia_id = row[0] if row else 17

        hoy = date.today()
        dias_habiles = []
        fecha = hoy
        while len(dias_habiles) < dias:
            if fecha.weekday() < 5:
                dias_habiles.append(fecha)
            fecha -= timedelta(days=1)
        dias_habiles.reverse()

        amb_creados = 0
        sede_creados = 0

        for dia in dias_habiles:
            instructor = random.choice(instructores)

            for aprendiz in aprendices:
                rand = random.random()
                if rand < 0.70:
                    estado_amb = 'Asistio'
                    estado_sede = 'Presente'
                elif rand < 0.85:
                    estado_amb = 'Inasistio'
                    estado_sede = 'Ausente'
                elif rand < 0.95:
                    estado_amb = 'Retardo'
                    estado_sede = 'Retardo'
                else:
                    estado_amb = 'Justificado'
                    estado_sede = 'Presente'

                if estado_sede == 'Presente':
                    hora_ent = time(6, 0, 0)
                elif estado_sede == 'Retardo':
                    hora_ent = time(random.choice([6, 7]), random.choice([5, 10, 15, 20]), 0)
                else:
                    hora_ent = None

                hora_sal = time(12, 0, 0) if hora_ent else None

                cursor.execute(
                    'INSERT INTO asistencia_ambiente (id_usuario, id_instructor, id_competencia, fecha, estado_asistencia) '
                    'VALUES (%s, %s, %s, %s, %s)',
                    [aprendiz, instructor, competencia_id, dia, estado_amb]
                )
                amb_creados += 1

                cursor.execute(
                    'INSERT INTO asistencia_sede (id_usuario, fecha, hora_entrada, hora_salida, estado_asistencia) '
                    'VALUES (%s, %s, %s, %s, %s)',
                    [aprendiz, dia, hora_ent, hora_sal, estado_sede]
                )
                sede_creados += 1

        conn.commit()

        self.stdout.write(self.style.SUCCESS(f'\n=== RESUMEN ==='))
        self.stdout.write(f'Aprendices: {len(aprendices)}')
        self.stdout.write(f'Dias: {dias} ({dias_habiles[0]} a {dias_habiles[-1]})')
        self.stdout.write(f'Instructores: {instructores}')
        self.stdout.write(f'Competencia: {competencia_id}')
        self.stdout.write(f'Registros asistencia_ambiente: {amb_creados}')
        self.stdout.write(f'Registros asistencia_sede: {sede_creados}')
