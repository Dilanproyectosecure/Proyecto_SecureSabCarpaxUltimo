import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.login.models import Usuarios
from apps.reporte_monitoreo.coordinador.models import AsistenciaAmbiente, Competencia


class VistasAprendizTest(TestCase):

    def setUp(self):
        self.client = Client()

        self.usuario = Usuarios.objects.create(
            cedula="123",
            nombre="Test",
            apellido="User",
            correo="test@test.com",
            estado="Activo"
        )

        self.competencia = Competencia.objects.create(
            nombre_competencia="Python",
            descripcion="Test",
            estado="ACTIVO"
        )

        self.asistencia = AsistenciaAmbiente.objects.create(
            id_usuario=self.usuario,
            id_competencia=self.competencia,
            fecha=datetime.date.today(),
            estado_asistencia="Inasistio"
        )

    # --------------------------------------------------
    # CONSULTAR ASISTENCIA
    # --------------------------------------------------

    def test_consultar_asistencia_200(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse('aprendiz:consultar_asistencia')
        )

        self.assertEqual(response.status_code, 200)

    def test_consultar_contexto(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse('aprendiz:consultar_asistencia')
        )

        self.assertIn('asistencias', response.context)
        self.assertIn('competencias', response.context)

    # --------------------------------------------------
    # RADICAR JUSTIFICACION
    # --------------------------------------------------

    def test_get_radicar(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse('aprendiz:radicar_justificacion')
        )

        self.assertEqual(response.status_code, 200)

    def test_post_justificacion_exitosa(self):
        self.client.force_login(self.usuario)

        archivo = SimpleUploadedFile("soporte.pdf", b"test")

        response = self.client.post(
            reverse('aprendiz:radicar_justificacion'),
            {
                'inasistencias': [self.asistencia.id_asistencia_ambiente],
                'motivo': 'Prueba',
                'soporte': archivo
            }
        )

        self.assertEqual(response.status_code, 302)