from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.reporte_monitoreo.coordinador.models import (
    AsistenciaAmbiente,
    Justificacion,
    Programa,
    Jornada,
    Competencia
)

from apps.gestion_asistencia_justificacion.aprendiz.selectors.asistencia_selector import (
    obtener_asistencias_usuario
)

User = get_user_model()


class AsistenciasExistsSelectorTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        # =========================
        # USUARIO
        # =========================
        cls.usuario = User.objects.create_user(
            cedula="123",
            correo="test@test.com",
            nombre="Test",
            apellido="User",
            telefono="123",
            estado="ACTIVO",
            password="123"
        )

        # =========================
        # DATOS BASE
        # =========================
        cls.programa = Programa.objects.create(
            nombre_programa="ADSO",
            tipo_programa="Tecnólogo"
        )

        cls.jornada = Jornada.objects.create(
            nombre_jornada="Mañana",
            hora_inicio="06:00",
            hora_fin="12:00"
        )

        cls.competencia = Competencia.objects.create(
            nombre_competencia="Python",
            descripcion="Programación",
            estado="ACTIVA",
            id_programa=cls.programa
        )

        # =========================
        # ASISTENCIA
        # =========================
        cls.asistencia = AsistenciaAmbiente.objects.create(
            id_usuario=cls.usuario,
            id_competencia=cls.competencia,
            estado_asistencia="INASISTENTE"
        )

    # ======================================================
    # TEST 1: sin justificación aprobada
    # ======================================================
    def test_sin_justificacion_aprobada(self):
        resultado = obtener_asistencias_usuario(self.usuario)
        asistencia = resultado.first()

        self.assertFalse(asistencia.tiene_justificacion_aprobada)

    # ======================================================
    # TEST 2: con justificación aprobada
    # ======================================================
    def test_con_justificacion_aprobada(self):

        Justificacion.objects.create(
            id_asistencia_ambiente=self.asistencia,
            estado="Aprobado"
        )

        resultado = obtener_asistencias_usuario(self.usuario)
        asistencia = resultado.first()

        self.assertTrue(asistencia.tiene_justificacion_aprobada)