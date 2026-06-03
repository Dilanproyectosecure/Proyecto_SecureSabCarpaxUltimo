import datetime
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.gestion_asistencia_justificacion.aprendiz.services.justificacion_service import (
    crear_justificaciones
)

from apps.reporte_monitoreo.coordinador.models import (
    AsistenciaAmbiente,
)

from apps.login.models import Usuarios


class JustificacionServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuarios.objects.create(
            cedula="123",
            nombre="Test",
            apellido="User",
            correo="test@test.com",
            estado="Activo"
        )

        cls.asistencia = AsistenciaAmbiente.objects.create(
            id_usuario=cls.usuario,
            fecha=datetime.date.today(),
            estado_asistencia="Inasistio"
        )

    # --------------------------------------------------
    # TEST 1: CREA JUSTIFICACION
    # --------------------------------------------------
    def test_crea_justificacion_valida(self):

        archivo = SimpleUploadedFile("soporte.pdf", b"dummy content")

        creadas = crear_justificaciones(
            self.usuario,
            [self.asistencia.id_asistencia_ambiente],
            "Motivo prueba",
            archivo
        )

        self.assertEqual(creadas, 1)

    # --------------------------------------------------
    # TEST 2: MAS DE 3 DIAS NO CREA
    # --------------------------------------------------
    def test_mas_de_3_dias_no_crea(self):

        self.asistencia.fecha = datetime.date.today() - datetime.timedelta(days=5)
        self.asistencia.save()

        archivo = SimpleUploadedFile("soporte.pdf", b"dummy content")

        creadas = crear_justificaciones(
            self.usuario,
            [self.asistencia.id_asistencia_ambiente],
            "Motivo",
            archivo
        )

        self.assertEqual(creadas, 0)

    # --------------------------------------------------
    # TEST 3: ASISTENCIA NO EXISTE
    # --------------------------------------------------
    def test_asistencia_no_existe(self):

        archivo = SimpleUploadedFile("soporte.pdf", b"dummy content")

        creadas = crear_justificaciones(
            self.usuario,
            [999999],
            "Motivo",
            archivo
        )

        self.assertEqual(creadas, 0)

    # --------------------------------------------------
    # TEST 4: MULTIPLES ASISTENCIAS
    # --------------------------------------------------
    def test_varias_asistencias(self):

        archivo = SimpleUploadedFile("soporte.pdf", b"dummy content")

        a2 = AsistenciaAmbiente.objects.create(
            id_usuario=self.usuario,
            fecha=datetime.date.today(),
            estado_asistencia="Inasistio"
        )

        creadas = crear_justificaciones(
            self.usuario,
            [
                self.asistencia.id_asistencia_ambiente,
                a2.id_asistencia_ambiente
            ],
            "Motivo",
            archivo
        )

        self.assertEqual(creadas, 2)