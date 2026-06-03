import datetime
from django.test import TestCase

# IMPORT CORRECTO (services)
from apps.gestion_asistencia_justificacion.aprendiz.services.asistencia_service import (
    analizar_inasistencias
)


class AnalisisInasistenciasTest(TestCase):

    # ======================================================
    # MOCK PARA SIMULAR ASISTENCIAS
    # ======================================================
    class MockAsistencia:
        def __init__(self, fecha, estado, justificada=False):
            self.fecha = fecha
            self.estado_asistencia = estado
            self.tiene_justificacion_aprobada = justificada

    # ======================================================
    # TEST 1: SIN DATOS
    # ======================================================
    def test_sin_inasistencias(self):

        datos = []

        tiene_3, tiene_5, total = analizar_inasistencias(datos)

        self.assertFalse(tiene_3)
        self.assertFalse(tiene_5)
        self.assertEqual(total, 0)

    # ======================================================
    # TEST 2: UN SOLO DÍA
    # ======================================================
    def test_un_dia_inasistencia(self):

        datos = [
            self.MockAsistencia(datetime.date(2026, 5, 1), "Inasistio")
        ]

        tiene_3, tiene_5, total = analizar_inasistencias(datos)

        self.assertFalse(tiene_3)
        self.assertFalse(tiene_5)
        self.assertEqual(total, 1)

    # ======================================================
    # TEST 3: 3 DÍAS CONSECUTIVOS
    # ======================================================
    def test_tres_dias_consecutivos(self):

        datos = [
            self.MockAsistencia(datetime.date(2026, 5, 3), "Inasistio"),
            self.MockAsistencia(datetime.date(2026, 5, 2), "Inasistio"),
            self.MockAsistencia(datetime.date(2026, 5, 1), "Inasistio"),
        ]

        tiene_3, tiene_5, total = analizar_inasistencias(datos)

        self.assertTrue(tiene_3)
        self.assertFalse(tiene_5)
        self.assertEqual(total, 3)

    # ======================================================
    # TEST 4: 5 DÍAS TOTALES
    # ======================================================
    def test_cinco_dias(self):

        datos = [
            self.MockAsistencia(datetime.date(2026, 5, 5), "Inasistio"),
            self.MockAsistencia(datetime.date(2026, 5, 4), "Inasistio"),
            self.MockAsistencia(datetime.date(2026, 5, 3), "Inasistio"),
            self.MockAsistencia(datetime.date(2026, 5, 2), "Inasistio"),
            self.MockAsistencia(datetime.date(2026, 5, 1), "Inasistio"),
        ]

        tiene_3, tiene_5, total = analizar_inasistencias(datos)

        self.assertTrue(tiene_3)
        self.assertTrue(tiene_5)
        self.assertEqual(total, 5)

    # ======================================================
    # TEST 5: INASISTENCIA JUSTIFICADA NO CUENTA
    # ======================================================
    def test_inasistencia_justificada(self):

        datos = [
            self.MockAsistencia(datetime.date(2026, 5, 1), "Inasistio", True),
            self.MockAsistencia(datetime.date(2026, 5, 2), "Inasistio", True),
            self.MockAsistencia(datetime.date(2026, 5, 3), "Inasistio", True),
        ]

        tiene_3, tiene_5, total = analizar_inasistencias(datos)

        self.assertFalse(tiene_3)
        self.assertFalse(tiene_5)
        self.assertEqual(total, 0)