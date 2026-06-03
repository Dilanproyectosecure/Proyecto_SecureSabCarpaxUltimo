from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.reporte_monitoreo.coordinador.models import (
    AsistenciaAmbiente,
    Justificacion,
    Programa,
    Jornada,
    Competencia
)

from apps.gestion_asistencia_justificacion.aprendiz.selectors.inasistencias_selector import (
    obtener_inasistencias_usuario
)

User = get_user_model()


class InasistenciasSelectorTest(TestCase):

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
    # TEST 1: trae asistencias
    # ======================================================
    def test_obtener_inasistencias(self):
        resultado = obtener_inasistencias_usuario(self.usuario)
        self.assertEqual(resultado.count(), 1)

    # ======================================================
    # TEST 2: existe prefetch de justificaciones
    # ======================================================
    def test_prefetch_justificaciones(self):
        resultado = obtener_inasistencias_usuario(self.usuario)
        asistencia = resultado.first()

        self.assertTrue(hasattr(asistencia, "justificaciones"))
        self.assertEqual(len(asistencia.justificaciones), 0)